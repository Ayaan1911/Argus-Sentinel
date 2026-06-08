from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class ReasoningStep:
    label: str
    modifier: float
    reason: str

@dataclass
class ReasoningResult:
    base_score: float
    modifiers: List[ReasoningStep]
    total_score: float
    risk_level: str
    reasoning_breakdown: List[Dict[str, Any]]

class ReasoningEngine:
    def _get_risk_level(self, score: float) -> str:
        if score <= 2.0: return "informational"
        if score <= 4.0: return "low"
        if score <= 6.0: return "medium"
        if score <= 8.0: return "high"
        return "critical"

    def calculate_risk(self, finding_type: str, finding_data: dict, intelligence_entry: dict) -> ReasoningResult:
        base_score = 0.0
        modifiers = []

        finding_type = finding_type.lower()

        if finding_type in ["port", "service"]:
            base_score = float(intelligence_entry.get("risk_weight", 0.0)) if intelligence_entry else 0.0
            if finding_data.get("internet_facing"):
                modifiers.append(ReasoningStep("Internet Facing", 2.0, "Service is exposed to the public internet."))
            if finding_data.get("password_auth_enabled"):
                modifiers.append(ReasoningStep("Password Auth", 2.0, "Password authentication is enabled, increasing brute-force risk."))
            if finding_data.get("outdated_version"):
                modifiers.append(ReasoningStep("Outdated Version", 1.5, "Service is running an outdated version with potential CVEs."))
            if finding_data.get("default_port"):
                modifiers.append(ReasoningStep("Default Port", 1.5, "Running on default port makes it easier for automated scanners to find."))
            if finding_data.get("no_authentication"):
                modifiers.append(ReasoningStep("No Authentication", 2.0, "Service is accessible without any authentication."))
            if finding_data.get("firewall_restricted"):
                modifiers.append(ReasoningStep("Firewall Restricted", -1.5, "Service access is restricted by a firewall."))
            if finding_data.get("key_based_auth"):
                modifiers.append(ReasoningStep("Key-Based Auth", -1.0, "Strong key-based authentication is enforced."))

        elif finding_type == "vulnerability":
            severity = finding_data.get("severity", "informational").lower()
            sev_map = {"critical": 9.0, "high": 7.0, "medium": 5.0, "low": 3.0, "informational": 1.0}
            base_score = sev_map.get(severity, 1.0)
            
            if finding_data.get("publicly_exploitable"):
                modifiers.append(ReasoningStep("Publicly Exploitable", 1.5, "Vulnerability can be exploited over the public internet."))
            if finding_data.get("authentication_required") is False:
                modifiers.append(ReasoningStep("No Authentication Required", 1.0, "Exploitation does not require prior authentication."))
            if finding_data.get("affects_multiple_targets"):
                modifiers.append(ReasoningStep("Broad Impact", 1.0, "Vulnerability affects multiple targets or systems."))
            if finding_data.get("mitigating_control_present"):
                modifiers.append(ReasoningStep("Mitigated", -1.0, "A mitigating control reduces the likelihood of exploitation."))

        elif finding_type == "technology":
            base_score = 3.0
            if finding_data.get("outdated_version"):
                modifiers.append(ReasoningStep("Outdated Version", 2.0, "Technology is outdated and may contain vulnerabilities."))
            if finding_data.get("known_vulnerabilities"):
                modifiers.append(ReasoningStep("Known Vulnerabilities", 1.5, "Public exploits or CVEs exist for this technology."))
            if finding_data.get("admin_panel_exposed"):
                modifiers.append(ReasoningStep("Exposed Admin Panel", 1.0, "Administrative interface is exposed."))
            if finding_data.get("waf_detected"):
                modifiers.append(ReasoningStep("WAF Detected", -1.0, "A Web Application Firewall provides active defense."))

        elif finding_type == "subdomain":
            base_score = 2.0
            if finding_data.get("resolves_to_internal_ip"):
                modifiers.append(ReasoningStep("Internal Resolution", 1.5, "Subdomain resolves to an internal IP address, potential SSRF target."))
            if finding_data.get("wildcard_subdomain"):
                modifiers.append(ReasoningStep("Wildcard Subdomain", 2.0, "Wildcard DNS record increases attack surface."))
            if finding_data.get("takeover_possible"):
                modifiers.append(ReasoningStep("Subdomain Takeover", 1.0, "Subdomain points to an unclaimed external resource."))

        total_score = base_score + sum(m.modifier for m in modifiers)
        total_score = max(0.0, min(10.0, total_score))
        
        reasoning_breakdown = [{"label": "Base Score", "modifier": base_score, "reason": "Initial base score derived from finding type and intelligence data."}]
        for m in modifiers:
            reasoning_breakdown.append({"label": m.label, "modifier": m.modifier, "reason": m.reason})

        return ReasoningResult(
            base_score=base_score,
            modifiers=modifiers,
            total_score=total_score,
            risk_level=self._get_risk_level(total_score),
            reasoning_breakdown=reasoning_breakdown
        )
