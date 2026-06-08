import pytest
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
