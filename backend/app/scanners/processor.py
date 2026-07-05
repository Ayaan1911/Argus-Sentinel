from app.intelligence.loader import get_intelligence_loader
from app.engines import reasoning_engine, confidence_engine

class FindingProcessor:
    def __init__(self):
        self.loader = get_intelligence_loader()

    # Map nuclei template tags → Intelligence Library vulnerability filenames
    TAG_TO_VULN_KEY = {
        "sqli": "sql_injection",
        "sql": "sql_injection",
        "time-based-sqli": "sql_injection",
        "xss": "xss",
        "rxss": "xss",
        "ssrf": "ssrf",
        "rce": "rce",
        "idor": "idor",
    }

    def _match_vuln_entry(self, raw_data: dict, title: str):
        """Match a nuclei finding to an Intelligence Library vulnerability entry.

        Strategy:
        1. Tag-based match — nuclei tags are normalized (xss, sqli, ssrf, rce, idor)
        2. Title keyword fallback
        3. Returns None if no match found
        """
        info = raw_data.get("info", {})
        tags = {str(tag).lower() for tag in info.get("tags", [])}
        title_l = title.lower()

        for tag in tags:
            key = self.TAG_TO_VULN_KEY.get(tag)
            if key:
                entry = self.loader.get_vulnerability(key)
                if entry:
                    return entry

        keyword_map = {
            "sql injection": "sql_injection",
            "sqli": "sql_injection",
            "xss": "xss",
            "cross-site scripting": "xss",
            "ssrf": "ssrf",
            "server-side request forgery": "ssrf",
            "rce": "rce",
            "remote code execution": "rce",
            "idor": "idor",
            "insecure direct object": "idor",
        }
        for keyword, key in keyword_map.items():
            if keyword in title_l:
                entry = self.loader.get_vulnerability(key)
                if entry:
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
        elif f_type == "technology":
            tech_name = raw_data.get("title", "")
            kb_entry = self.loader.get_technology(tech_name)
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
        guidance = {audience: audience_data.get(audience, "")} if audience_data else {}

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
