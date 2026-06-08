import pytest
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
