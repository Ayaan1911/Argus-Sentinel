from dataclasses import dataclass
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
