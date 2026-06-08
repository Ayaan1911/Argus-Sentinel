import os

files = {
    "backend/app/engines/correlation.py": """from dataclasses import dataclass, field
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
        any_no_auth = False
        ssh_findings = []
        high_sev_count = 0
        tech_outdated_findings = []
        vuln_findings = []
        web_vuln_findings = []
        any_waf = False

        for f in findings:
            raw = f.get("raw_data", {})
            f_type = f.get("type", "").lower()
            title = f.get("title", "")
            risk_score = f.get("risk_score", 0.0)

            if risk_score >= 6.1:
                high_sev_count += 1
            
            if raw.get("no_authentication"):
                any_no_auth = True
            
            if raw.get("waf_detected"):
                any_waf = True
                
            port = raw.get("port")
            if port in [3306, 6379] or "mysql" in title.lower() or "redis" in title.lower():
                db_findings.append(f)
                
            if port == 22 or "ssh" in title.lower():
                ssh_findings.append(f)

            if f_type == "technology" and raw.get("outdated_version"):
                tech_outdated_findings.append(f)
                
            if f_type == "vulnerability":
                vuln_findings.append(f)
                if "xss" in title.lower() or "sql injection" in title.lower() or "sqli" in title.lower():
                    web_vuln_findings.append(f)

        # Rule 1
        if db_findings and any_no_auth:
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

        # Rules 5, 6, 8
        for f in findings:
            raw = f.get("raw_data", {})
            if raw.get("admin_panel_exposed"):
                result.correlations_found.append(CorrelationMatch(
                    rule_name="admin_panel_exposed",
                    matched_findings=[f["title"]],
                    modifier=1.5,
                    explanation="Exposed admin panels are high-value targets for brute force and authentication bypass attacks."
                ))
            if raw.get("firewall_restricted") and raw.get("internet_facing"):
                result.correlations_found.append(CorrelationMatch(
                    rule_name="firewall_mitigates_exposure",
                    matched_findings=[f["title"]],
                    modifier=-1.5,
                    explanation="Firewall restrictions reduce the exploitability of internet-facing services."
                ))
            if f.get("type", "").lower() == "subdomain" and raw.get("takeover_possible"):
                result.correlations_found.append(CorrelationMatch(
                    rule_name="subdomain_takeover_critical",
                    matched_findings=[f["title"]],
                    modifier=3.0,
                    explanation="Subdomain takeover allows an attacker to serve malicious content under your trusted domain."
                ))

        # Rule 7
        if any_waf and web_vuln_findings:
            result.correlations_found.append(CorrelationMatch(
                rule_name="waf_mitigates_web_vulns",
                matched_findings=[f["title"] for f in web_vuln_findings],
                modifier=-1.0,
                explanation="A WAF provides partial mitigation for common web vulnerabilities."
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

        # Calc combined risk
        max_base = max([f.get("risk_score", 0.0) for f in findings], default=0.0)
        # However, to be fully accurate on max_base, we should see what the max final_risk_score is AFTER modifiers.
        # The prompt says: "Take the highest individual final_risk_score across all findings after modifiers... Apply any combined risk modifiers... Map to risk level"
        # We will do this carefully by simulating apply_modifiers logic.
        
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
""",
    "backend/app/engines/__init__.py": """from .reasoning import ReasoningEngine
from .confidence import ConfidenceEngine
from .correlation import CorrelationEngine

reasoning_engine = ReasoningEngine()
confidence_engine = ConfidenceEngine()
correlation_engine = CorrelationEngine()
""",
    "backend/tests/test_correlation.py": """import pytest
from app.engines.correlation import CorrelationEngine

def test_open_database_no_auth_triggers():
    engine = CorrelationEngine()
    findings = [
        {
            "type": "service",
            "title": "Redis Server",
            "raw_data": {"port": 6379, "no_authentication": True},
            "risk_score": 5.0,
            "reasoning_breakdown": []
        }
    ]
    result = engine.correlate(findings)
    assert len(result.correlations_found) == 1
    assert result.correlations_found[0].rule_name == "open_database_no_auth"
    assert "Redis Server" in result.amplified_findings
    
    updated = engine.apply_modifiers(findings, result)
    assert updated[0]["final_risk_score"] == 8.0
    assert updated[0]["correlation_modifier"] == 3.0

def test_ssh_weak_auth_triggers():
    engine = CorrelationEngine()
    findings = [
        {
            "type": "service",
            "title": "SSH Server",
            "raw_data": {"port": 22, "internet_facing": True, "password_auth_enabled": True},
            "risk_score": 4.0,
            "reasoning_breakdown": []
        }
    ]
    result = engine.correlate(findings)
    assert any(c.rule_name == "internet_facing_ssh_weak_auth" for c in result.correlations_found)
    
    updated = engine.apply_modifiers(findings, result)
    assert updated[0]["final_risk_score"] == 6.5

def test_multiple_high_severity_triggers():
    engine = CorrelationEngine()
    findings = [
        {"type": "vuln", "title": "Vuln 1", "risk_score": 7.0, "raw_data": {}, "reasoning_breakdown": []},
        {"type": "vuln", "title": "Vuln 2", "risk_score": 8.0, "raw_data": {}, "reasoning_breakdown": []},
        {"type": "vuln", "title": "Vuln 3", "risk_score": 6.5, "raw_data": {}, "reasoning_breakdown": []}
    ]
    result = engine.correlate(findings)
    assert any(c.rule_name == "multiple_high_severity" for c in result.correlations_found)
    assert result.combined_risk_level == "critical"  # Max is 8.0 + 1.5 = 9.5 -> critical

def test_firewall_mitigates():
    engine = CorrelationEngine()
    findings = [
        {
            "type": "service",
            "title": "Internal App",
            "raw_data": {"internet_facing": True, "firewall_restricted": True},
            "risk_score": 6.0,
            "reasoning_breakdown": []
        }
    ]
    result = engine.correlate(findings)
    assert any(c.rule_name == "firewall_mitigates_exposure" for c in result.correlations_found)
    assert "Internal App" in result.mitigated_findings
    
    updated = engine.apply_modifiers(findings, result)
    assert updated[0]["final_risk_score"] == 4.5

def test_subdomain_takeover_critical():
    engine = CorrelationEngine()
    findings = [
        {
            "type": "subdomain",
            "title": "dev.example.com",
            "raw_data": {"takeover_possible": True},
            "risk_score": 5.0,
            "reasoning_breakdown": []
        }
    ]
    result = engine.correlate(findings)
    assert any(c.rule_name == "subdomain_takeover_critical" for c in result.correlations_found)
    
    updated = engine.apply_modifiers(findings, result)
    assert updated[0]["final_risk_score"] == 8.0

def test_no_false_correlations():
    engine = CorrelationEngine()
    findings = [
        {
            "type": "service",
            "title": "Safe Service",
            "raw_data": {"port": 443},
            "risk_score": 2.0,
            "reasoning_breakdown": []
        }
    ]
    result = engine.correlate(findings)
    assert len(result.correlations_found) == 0
    assert result.combined_risk_level == "informational"
"""
}

for filepath, content in files.items():
    dirpath = os.path.dirname(filepath)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Correlation Engine building complete.")
