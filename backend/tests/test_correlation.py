import pytest
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

def test_outdated_stack_with_vuln_triggers():
    # outdated_version is set by nmap.py on type="port" findings (server
    # products) — this reflects real scanner output shape.
    engine = CorrelationEngine()
    findings = [
        {
            "type": "port",
            "title": "Port 22/tcp: ssh",
            "raw_data": {"port": 22, "outdated_version": True},
            "risk_score": 3.0,
            "reasoning_breakdown": []
        },
        {
            "type": "vulnerability",
            "title": "CVE-2023-1234",
            "raw_data": {},
            "risk_score": 5.0,
            "reasoning_breakdown": []
        }
    ]
    result = engine.correlate(findings)
    assert any(c.rule_name == "outdated_stack_with_vuln" for c in result.correlations_found)


def test_outdated_stack_with_vuln_triggers_for_technology_findings_too():
    # outdated_version is also set by httpx.py on type="technology" findings
    # (client-side libraries like jQuery detected via tech-detect) — the
    # rule must catch this source too, not just nmap's.
    engine = CorrelationEngine()
    findings = [
        {
            "type": "technology",
            "title": "Live Host: http://example.com",
            "raw_data": {"outdated_version": True},
            "risk_score": 3.0,
            "reasoning_breakdown": []
        },
        {
            "type": "vulnerability",
            "title": "CVE-2023-1234",
            "raw_data": {},
            "risk_score": 5.0,
            "reasoning_breakdown": []
        }
    ]
    result = engine.correlate(findings)
    assert any(c.rule_name == "outdated_stack_with_vuln" for c in result.correlations_found)


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
