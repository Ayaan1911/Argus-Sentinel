from app.intelligence.loader import get_intelligence_loader
from app.engines import reasoning_engine, confidence_engine

class FindingProcessor:
    def __init__(self):
        self.loader = get_intelligence_loader()

    def _match_vuln_entry(self, raw_data: dict, title: str):
        """Match a nuclei finding to an Intelligence Library vulnerability entry.

        Data-driven — reads each vulnerabilities/*.json entry's own
        "nuclei_tags"/"title_keywords" fields rather than a hardcoded
        tag->entry map, so a new vulnerability entry becomes matchable just
        by adding the JSON file (see argus-intelligence/CONTRIBUTING.md) —
        no code change needed here.

        Strategy:
        1. Tag-based match — the entry with the MOST overlapping tags wins,
           so a finding carrying both a generic tag (e.g. "exposure") and a
           specific one (e.g. "git") doesn't ambiguously match every entry
           that happens to also share the generic tag.
        2. Title keyword fallback.
        3. Returns None if no match found.
        """
        info = raw_data.get("info", {})
        tags = {str(tag).lower() for tag in info.get("tags", [])}
        title_l = title.lower()
        vulns = self.loader.data.get("vulnerabilities", {})

        best_entry, best_score = None, 0
        for entry in vulns.values():
            entry_tags = {str(t).lower() for t in entry.get("nuclei_tags", [])}
            score = len(tags & entry_tags)
            if score > best_score:
                best_entry, best_score = entry, score
        if best_entry:
            return best_entry

        for entry in vulns.values():
            keywords = entry.get("title_keywords", [])
            if any(str(kw).lower() in title_l for kw in keywords):
                return entry

        return None

    def _fallback_service_entry(self, raw_data: dict, title: str):
        """For vuln findings that didn't match a vuln class, try matching a service/tech entry."""
        info = raw_data.get("info", {})
        tags = {str(tag).lower() for tag in info.get("tags", [])}
        title_l = title.lower()
        response = str(raw_data.get("response", "")).lower()

        if "ssh" in tags or "ssh" in title_l or "ssh-" in response:
            return self.loader.get_service("ssh")
        if "apache" in tags or "apache" in title_l or "server: apache" in response:
            return self.loader.get_technology("apache")

        return None

    def process(self, raw_finding: dict, scan_id: str, audience: str) -> dict:
        f_type = raw_finding.get("type", "").lower()
        title = raw_finding.get("title", "")
        raw_data = raw_finding.get("raw_data", {})
        source = raw_finding.get("source", "unknown")

        kb_entry = None
        if f_type in ["port", "service"]:
            service_name = raw_data.get("service", "")
            kb_entry = self.loader.get_service(service_name)
            # Fallback: unidentified/tcpwrapped ports get generic port guidance
            if kb_entry is None:
                kb_entry = self.loader.get_service("generic_port")
        elif f_type == "technology":
            kb_entry = None
            # httpx's tech-detect list (e.g. "jQuery:3.4.1") is a more
            # reliable signal for known frameworks/libraries than the page's
            # own <title>, which is usually the site's own branding rather
            # than the software name.
            for t in raw_data.get("tech", []) or []:
                tech_name = str(t).split(":")[0].strip()
                kb_entry = self.loader.get_technology(tech_name)
                if kb_entry:
                    break
            if kb_entry is None:
                kb_entry = self.loader.get_technology(raw_data.get("title", ""))
            # Fallback: unmatched tech findings (e.g. Live Host) get generic live_host guidance
            if kb_entry is None:
                kb_entry = self.loader.get_technology("live_host")
        elif f_type == "subdomain":
            kb_entry = self.loader.get_service("subdomain")
        elif f_type == "vulnerability":
            # Primary: tag+keyword based vuln class match
            kb_entry = self._match_vuln_entry(raw_data, title)
            # Fallback: service/tech match (e.g. SSH-related nuclei findings)
            if kb_entry is None:
                kb_entry = self._fallback_service_entry(raw_data, title)

        if kb_entry is None:
            kb_entry = {}

        reasoning_res = reasoning_engine.calculate_risk(f_type, raw_data, kb_entry)
        confidence_res = confidence_engine.calculate_confidence(source, raw_data, kb_entry)

        risk_level = reasoning_res.risk_level

        if risk_level in ["critical", "high"]:
            biz_impact = "Significant business risk"
        elif risk_level == "medium":
            biz_impact = "Moderate business risk"
        else:
            biz_impact = "Minimal business risk"

        audience_data = kb_entry.get("audience_guidance", {})
        # Return the full guidance map so the UI can switch personas freely.
        # Also include the scan-time audience as a convenience key.
        guidance = dict(audience_data) if audience_data else {}

        return {
            "scan_id": scan_id,
            "type": f_type,
            "title": title,
            "raw_data": raw_data,
            "severity": risk_level,
            "confidence": confidence_res.final_confidence,
            "risk_score": reasoning_res.total_score,
            "technical_impact": kb_entry.get("description", "Unknown"),
            "business_impact": biz_impact,
            "audience_guidance": guidance,
            "recommended_actions": kb_entry.get("recommended_actions", []),
            "learning_resources": kb_entry.get("learning_resources", []),
            "reasoning_breakdown": reasoning_res.reasoning_breakdown,
            "attack_patterns": kb_entry.get("attack_patterns", []),
            "related_findings": kb_entry.get("related_findings", []),
            "correlation_modifier": 0.0,
            "final_risk_score": reasoning_res.total_score
        }
