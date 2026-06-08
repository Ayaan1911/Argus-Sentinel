import os

files = {
    "backend/app/engines/reasoning.py": """from dataclasses import dataclass
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
""",
    "backend/app/engines/confidence.py": """from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class ConfidenceResult:
    scanner_reliability: float
    evidence_score: float
    kb_match_score: float
    final_confidence: float
    confidence_label: str

class ConfidenceEngine:
    def _get_confidence_label(self, score: float) -> str:
        if score >= 0.85: return "confirmed"
        if score >= 0.70: return "likely"
        if score >= 0.50: return "possible"
        return "uncertain"

    def calculate_confidence(self, source: str, evidence: dict, intelligence_entry: Optional[dict]) -> ConfidenceResult:
        source = source.lower()
        rel_map = {
            "nmap": 0.95,
            "nuclei": 0.90,
            "httpx": 0.85,
            "subfinder": 0.80,
            "manual": 0.70,
            "heuristic": 0.50
        }
        scanner_reliability = rel_map.get(source, 0.60)

        evidence_score = 0.0
        
        corroborating_items = evidence.get("corroborating_items", [])
        evidence_score += min(0.30, len(corroborating_items) * 0.10)
        
        if evidence.get("banner_confirmed"):
            evidence_score += 0.10
        if evidence.get("version_confirmed"):
            evidence_score += 0.10
        if evidence.get("multiple_probes"):
            evidence_score += 0.05

        kb_match_score = 0.0
        if intelligence_entry is not None:
            kb_match_score += 0.10
            
            attack_patterns = intelligence_entry.get("attack_patterns", [])
            finding_pattern = evidence.get("attack_pattern")
            if finding_pattern and finding_pattern in attack_patterns:
                kb_match_score += 0.05

        final_confidence = scanner_reliability + evidence_score + kb_match_score
        final_confidence = max(0.0, min(1.0, final_confidence))

        return ConfidenceResult(
            scanner_reliability=scanner_reliability,
            evidence_score=evidence_score,
            kb_match_score=kb_match_score,
            final_confidence=final_confidence,
            confidence_label=self._get_confidence_label(final_confidence)
        )
""",
    "backend/app/engines/__init__.py": """from .reasoning import ReasoningEngine
from .confidence import ConfidenceEngine

reasoning_engine = ReasoningEngine()
confidence_engine = ConfidenceEngine()
""",
    "backend/tests/__init__.py": "",
    "backend/tests/test_reasoning.py": """import pytest
from app.engines.reasoning import ReasoningEngine

def test_ssh_high_risk():
    engine = ReasoningEngine()
    finding_data = {
        "internet_facing": True,
        "password_auth_enabled": True
    }
    intelligence_entry = {"risk_weight": 7.0}
    result = engine.calculate_risk("service", finding_data, intelligence_entry)
    
    assert result.total_score == 10.0  # 7.0 + 2.0 + 2.0 = 11.0, capped at 10.0
    assert result.risk_level == "critical"

def test_ssh_low_risk():
    engine = ReasoningEngine()
    finding_data = {
        "key_based_auth": True,
        "firewall_restricted": True
    }
    intelligence_entry = {"risk_weight": 5.0}  # Base 5.0
    result = engine.calculate_risk("service", finding_data, intelligence_entry)
    
    assert result.total_score == 2.5  # 5.0 - 1.0 - 1.5 = 2.5
    assert result.risk_level == "low"

def test_vulnerability_critical():
    engine = ReasoningEngine()
    finding_data = {
        "severity": "high",
        "publicly_exploitable": True,
        "authentication_required": False
    }
    result = engine.calculate_risk("vulnerability", finding_data, None)
    
    assert result.total_score == 9.5  # Base 7.0 + 1.5 + 1.0 = 9.5
    assert result.risk_level == "critical"

def test_reasoning_breakdown_not_empty():
    engine = ReasoningEngine()
    result = engine.calculate_risk("technology", {}, None)
    assert len(result.reasoning_breakdown) >= 1
    assert result.reasoning_breakdown[0]["label"] == "Base Score"

def test_score_capped_at_10():
    engine = ReasoningEngine()
    finding_data = {
        "internet_facing": True,
        "password_auth_enabled": True,
        "no_authentication": True,
        "default_port": True,
        "outdated_version": True
    }
    intelligence_entry = {"risk_weight": 10.0}
    result = engine.calculate_risk("service", finding_data, intelligence_entry)
    
    assert result.total_score == 10.0
""",
    "backend/tests/test_confidence.py": """import pytest
from app.engines.confidence import ConfidenceEngine

def test_nmap_high_confidence():
    engine = ConfidenceEngine()
    evidence = {"banner_confirmed": True}
    result = engine.calculate_confidence("nmap", evidence, None)
    
    assert result.final_confidence == 1.0  # 0.95 + 0.10 = 1.05 capped at 1.0
    assert result.confidence_label == "confirmed"

def test_heuristic_low_confidence():
    engine = ConfidenceEngine()
    result = engine.calculate_confidence("heuristic", {}, None)
    
    assert result.final_confidence == 0.50
    assert result.confidence_label == "possible"

def test_confidence_capped_at_1():
    engine = ConfidenceEngine()
    evidence = {"corroborating_items": [1, 2, 3, 4], "banner_confirmed": True, "version_confirmed": True}
    result = engine.calculate_confidence("nmap", evidence, {"attack_patterns": []})
    
    assert result.final_confidence == 1.0

def test_kb_match_boosts_confidence():
    engine = ConfidenceEngine()
    result_no_kb = engine.calculate_confidence("manual", {}, None)
    result_with_kb = engine.calculate_confidence("manual", {}, {"attack_patterns": []})
    
    assert result_with_kb.final_confidence > result_no_kb.final_confidence
    assert result_with_kb.kb_match_score == 0.10
"""
}

for filepath, content in files.items():
    dirpath = os.path.dirname(filepath)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Engines building complete.")
