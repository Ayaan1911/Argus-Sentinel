from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class CorrelationMatch:
    rule_name: str
    matched_findings: List[str]
    modifier: float
    explanation: str

@dataclass
class CorrelationResult:
    correlations_found: List[CorrelationMatch] = field(default_factory=list)
    amplified_findings: List[str] = field(default_factory=list)
    mitigated_findings: List[str] = field(default_factory=list)
    combined_risk_level: str = "informational"
    summary: str = ""

class CorrelationEngine:
    def _get_risk_level(self, score: float) -> str:
        if score <= 2.0: return "informational"
        if score <= 4.0: return "low"
        if score <= 6.0: return "medium"
        if score <= 8.0: return "high"
        return "critical"

    def correlate(self, findings: List[Dict[str, Any]]) -> CorrelationResult:
        result = CorrelationResult()
        
        db_findings = []
        ssh_findings = []
        high_sev_count = 0
        tech_outdated_findings = []
        vuln_findings = []

        for f in findings:
            raw = f.get("raw_data", {})
            f_type = f.get("type", "").lower()
            title = f.get("title", "")
            risk_score = f.get("risk_score", 0.0)

            if risk_score >= 6.1:
                high_sev_count += 1
            
            # The database finding itself must be unauthenticated — not just
            # any finding anywhere in the scan (an anonymous FTP server says
            # nothing about whether Redis next to it wants a password).
            port = raw.get("port")
            is_db = port in [3306, 6379] or "mysql" in title.lower() or "redis" in title.lower()
            if is_db and raw.get("no_authentication"):
                db_findings.append(f)
                
            if port == 22 or "ssh" in title.lower():
                ssh_findings.append(f)

            # outdated_version is set by nmap.py (server products, on type
            # "port" findings) and by httpx.py (client-side libraries like
            # jQuery/Bootstrap detected via tech-detect, on type "technology"
            # findings) — both compare a detected version against that
            # product's min_secure_version on file.
            if f_type in ("port", "technology") and raw.get("outdated_version"):
                tech_outdated_findings.append(f)
                
            if f_type == "vulnerability":
                vuln_findings.append(f)

        # Rule 1
        if db_findings:
            result.correlations_found.append(CorrelationMatch(
                rule_name="open_database_no_auth",
                matched_findings=[f["title"] for f in db_findings],
                modifier=3.0,
                explanation="An exposed database with no authentication is directly exploitable with zero effort."
            ))

        # Rule 2
        for f in ssh_findings:
            raw = f.get("raw_data", {})
            if raw.get("internet_facing") and (raw.get("password_auth_enabled") or raw.get("no_authentication")):
                result.correlations_found.append(CorrelationMatch(
                    rule_name="internet_facing_ssh_weak_auth",
                    matched_findings=[f["title"]],
                    modifier=2.5,
                    explanation="Internet-facing SSH with weak authentication is one of the most common initial access vectors."
                ))

        # Rule 3
        combined_risk_modifier = 0.0
        if high_sev_count >= 3:
            combined_risk_modifier += 1.5
            result.correlations_found.append(CorrelationMatch(
                rule_name="multiple_high_severity",
                matched_findings=[],
                modifier=1.5,
                explanation="Multiple high-severity findings indicate a broadly exposed attack surface."
            ))

        # Rule 4
        if tech_outdated_findings and vuln_findings:
            result.correlations_found.append(CorrelationMatch(
                rule_name="outdated_stack_with_vuln",
                matched_findings=[f["title"] for f in vuln_findings],
                modifier=2.0,
                explanation="Outdated technology with known vulnerabilities significantly increases exploitation likelihood."
            ))

        # Rules 5, 6
        for f in findings:
            raw = f.get("raw_data", {})
            if raw.get("admin_panel_exposed"):
                result.correlations_found.append(CorrelationMatch(
                    rule_name="admin_panel_exposed",
                    matched_findings=[f["title"]],
                    modifier=1.5,
                    explanation="Exposed admin panels are high-value targets for brute force and authentication bypass attacks."
                ))
            if f.get("type", "").lower() == "subdomain" and raw.get("takeover_possible"):
                result.correlations_found.append(CorrelationMatch(
                    rule_name="subdomain_takeover_critical",
                    matched_findings=[f["title"]],
                    modifier=3.0,
                    explanation="Subdomain takeover allows an attacker to serve malicious content under your trusted domain."
                ))

        # Determine amplified/mitigated findings
        amplified = set()
        mitigated = set()
        for corr in result.correlations_found:
            if corr.modifier > 0 and corr.rule_name != "multiple_high_severity":
                amplified.update(corr.matched_findings)
            elif corr.modifier < 0:
                mitigated.update(corr.matched_findings)
                
        result.amplified_findings = list(amplified)
        result.mitigated_findings = list(mitigated)

        # Combined risk = the highest per-finding score after each finding's own
        # correlation modifiers are applied, plus the scan-wide bonus from rules
        # like "multiple_high_severity" that apply_modifiers deliberately excludes
        # from any single finding's own final_risk_score.
        simulated_findings = self.apply_modifiers(findings, result, mutate=False)
        max_final = max([f.get("final_risk_score", 0.0) for f in simulated_findings], default=0.0)
        
        combined_score = max_final + combined_risk_modifier
        combined_score = max(0.0, min(10.0, combined_score))
        
        result.combined_risk_level = self._get_risk_level(combined_score)
        
        if result.correlations_found:
            result.summary = f"Detected {len(result.correlations_found)} correlation(s) affecting overall risk. Combined risk is evaluated at {result.combined_risk_level.upper()}."
        else:
            result.summary = "No complex correlations detected. Findings evaluated individually."
            
        return result

    def apply_modifiers(self, findings: List[Dict[str, Any]], correlation_result: CorrelationResult, mutate: bool = True) -> List[Dict[str, Any]]:
        out_findings = []
        for f in findings:
            if mutate:
                nf = f
            else:
                nf = f.copy()
                nf["reasoning_breakdown"] = list(f.get("reasoning_breakdown", []))
            
            modifier_sum = 0.0
            
            for corr in correlation_result.correlations_found:
                if corr.rule_name == "multiple_high_severity":
                    continue
                if nf.get("title") in corr.matched_findings:
                    modifier_sum += corr.modifier
                    nf.get("reasoning_breakdown", []).append({
                        "label": "Correlation: " + corr.rule_name,
                        "modifier": corr.modifier,
                        "reason": corr.explanation
                    })
            
            nf["correlation_modifier"] = nf.get("correlation_modifier", 0.0) + modifier_sum
            final_risk = nf.get("risk_score", 0.0) + nf["correlation_modifier"]
            nf["final_risk_score"] = max(0.0, min(10.0, final_risk))
            out_findings.append(nf)
            
        return out_findings
