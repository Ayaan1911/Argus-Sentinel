"""
Test: processor correctly matches nuclei findings to Intelligence Library entries
via tag-based lookup — verifying the full chain:
  nuclei finding (tagged xss/sqli/ssrf) → processor → kb_entry → reasoning + audience guidance
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.scanners.processor import FindingProcessor

processor = FindingProcessor()

# --- XSS finding (tag: xss) ---
def test_xss_finding_matches_intelligence_library():
    raw = {
        "source": "nuclei",
        "type": "vulnerability",
        "title": "Reflected Cross-Site Scripting: http://juice-shop:3000/search?q=test",
        "raw_data": {
            "info": {
                "name": "Reflected Cross-Site Scripting",
                "severity": "medium",
                "tags": ["xss", "rxss", "dast", "vuln"],
            },
            "severity": "medium",
            "matched-at": "http://juice-shop:3000/search?q=test",
        }
    }
    result = processor.process(raw, scan_id="test-scan-1", audience="student")

    # Intelligence Library should have been matched
    assert result["technical_impact"] != "Unknown", (
        "Expected XSS Intelligence Library entry to populate technical_impact"
    )
    # Audience guidance should be populated
    assert result["audience_guidance"].get("student"), (
        f"Expected student audience guidance for XSS, got: {result['audience_guidance']}"
    )
    # Attack patterns from the library
    assert len(result["attack_patterns"]) > 0, "Expected XSS attack patterns from Intelligence Library"
    # Recommended actions
    assert len(result["recommended_actions"]) > 0, "Expected XSS recommended actions"
    # Reasoning breakdown should exist
    assert len(result["reasoning_breakdown"]) > 0

    print(f"  ✓ XSS matched: technical_impact='{result['technical_impact'][:60]}...'")
    print(f"  ✓ student guidance: '{result['audience_guidance']['student'][:80]}...'")
    print(f"  ✓ attack_patterns: {result['attack_patterns']}")
    print(f"  ✓ risk_score: {result['final_risk_score']} ({result['severity']})")
    print(f"  ✓ reasoning: {[s['label'] for s in result['reasoning_breakdown']]}")


# --- SQLi finding (tag: sqli) ---
def test_sqli_finding_matches_intelligence_library():
    raw = {
        "source": "nuclei",
        "type": "vulnerability",
        "title": "Error based SQL Injection: http://juice-shop:3000/'",
        "raw_data": {
            "info": {
                "name": "Error based SQL Injection",
                "severity": "critical",
                "tags": ["sqli", "error", "dast", "vuln"],
            },
            "severity": "critical",
            "matched-at": "http://juice-shop:3000/'",
        }
    }
    result = processor.process(raw, scan_id="test-scan-2", audience="bug_bounty_hunter")

    assert result["technical_impact"] != "Unknown", (
        "Expected SQL Injection Intelligence Library entry to populate technical_impact"
    )
    assert result["audience_guidance"].get("bug_bounty_hunter"), (
        f"Expected bug_bounty_hunter guidance for SQLi, got: {result['audience_guidance']}"
    )
    assert len(result["attack_patterns"]) > 0

    print(f"  ✓ SQLi matched: technical_impact='{result['technical_impact'][:60]}...'")
    print(f"  ✓ bug_bounty_hunter guidance: '{result['audience_guidance']['bug_bounty_hunter'][:80]}...'")
    print(f"  ✓ risk_score: {result['final_risk_score']} ({result['severity']})")


# --- SSRF finding (tag: ssrf) ---
def test_ssrf_finding_matches_intelligence_library():
    raw = {
        "source": "nuclei",
        "type": "vulnerability",
        "title": "Blind SSRF: http://juice-shop:3000/api/Products/1",
        "raw_data": {
            "info": {
                "name": "Blind SSRF",
                "severity": "high",
                "tags": ["ssrf", "dast", "oast", "vuln"],
            },
            "severity": "high",
            "matched-at": "http://juice-shop:3000/api/Products/1",
        }
    }
    result = processor.process(raw, scan_id="test-scan-3", audience="pentester")

    assert result["technical_impact"] != "Unknown", (
        "Expected SSRF Intelligence Library entry to populate technical_impact"
    )
    assert result["audience_guidance"].get("pentester"), (
        f"Expected pentester guidance for SSRF, got: {result['audience_guidance']}"
    )

    print(f"  ✓ SSRF matched: technical_impact='{result['technical_impact'][:60]}...'")
    print(f"  ✓ pentester guidance: '{result['audience_guidance']['pentester'][:80]}...'")
    print(f"  ✓ risk_score: {result['final_risk_score']} ({result['severity']})")


# --- Previously-orphaned entries (added nuclei_tags/title_keywords this
# session — before that, these entries had rich JSON but nothing in
# processor.py ever routed a real finding to them) ---
def test_missing_security_headers_now_matches():
    raw = {
        "source": "nuclei",
        "type": "vulnerability",
        "title": "HTTP Missing Security Headers: http://juice-shop:3000",
        "raw_data": {
            "info": {"name": "HTTP Missing Security Headers", "severity": "info",
                      "tags": ["misconfig", "headers", "generic"]},
            "severity": "info",
        }
    }
    result = processor.process(raw, scan_id="test-scan-headers", audience="developer")
    assert result["technical_impact"] != "Unknown"
    assert result["audience_guidance"].get("developer")


def test_exposed_api_docs_now_matches():
    raw = {
        "source": "nuclei",
        "type": "vulnerability",
        "title": "Public Swagger API - Detect: http://juice-shop:3000/api-docs/swagger.yaml",
        "raw_data": {
            "info": {"name": "Public Swagger API - Detect", "severity": "info",
                      "tags": ["swagger", "exposure"]},
            "severity": "info",
        }
    }
    result = processor.process(raw, scan_id="test-scan-swagger", audience="developer")
    assert result["technical_impact"] != "Unknown"
    assert "api" in result["technical_impact"].lower() or "swagger" in result["technical_impact"].lower() or "documentation" in result["technical_impact"].lower()


# --- New vulnerability entries added this session ---
def test_exposed_git_matches():
    raw = {
        "source": "nuclei",
        "type": "vulnerability",
        "title": "Git Config File - Detect: http://example.com/.git/config",
        "raw_data": {
            "info": {"name": "Git Config File", "severity": "medium", "tags": ["git", "exposure"]},
            "severity": "medium",
        }
    }
    result = processor.process(raw, scan_id="test-scan-git", audience="pentester")
    assert result["technical_impact"] != "Unknown"
    assert result["audience_guidance"].get("pentester")


def test_exposed_env_matches():
    raw = {
        "source": "nuclei",
        "type": "vulnerability",
        "title": "Environment File Exposure: http://example.com/.env",
        "raw_data": {
            "info": {"name": "Environment File Exposure", "severity": "critical", "tags": ["exposure", "env"]},
            "severity": "critical",
        }
    }
    result = processor.process(raw, scan_id="test-scan-env", audience="security_team")
    assert result["technical_impact"] != "Unknown"
    assert result["severity"] in ("critical", "high")  # severity comes from finding_data, not the KB entry


def test_default_credentials_matches():
    raw = {
        "source": "nuclei",
        "type": "vulnerability",
        "title": "Generic Default Login",
        "raw_data": {
            "info": {"name": "Generic Default Login", "severity": "critical", "tags": ["default-login"]},
            "severity": "critical",
        }
    }
    result = processor.process(raw, scan_id="test-scan-creds", audience="student")
    assert result["technical_impact"] != "Unknown"


def test_exposed_cicd_config_matches():
    raw = {
        "source": "nuclei",
        "type": "vulnerability",
        "title": "Exposed GitLab CI Config: http://example.com/.gitlab-ci.yml",
        "raw_data": {
            "info": {"name": "Exposed GitLab CI Config", "severity": "low", "tags": ["exposure", "ci"]},
            "severity": "low",
        }
    }
    result = processor.process(raw, scan_id="test-scan-cicd", audience="developer")
    assert result["technical_impact"] != "Unknown"


def test_ambiguous_generic_tag_prefers_more_specific_entry():
    # A finding tagged only with the generic "exposure" tag (shared by 7+
    # entries) should still resolve to the entry with the most specific
    # overlapping tag once a distinguishing tag is present.
    raw = {
        "source": "nuclei",
        "type": "vulnerability",
        "title": "Some Config Exposure",
        "raw_data": {
            "info": {"name": "Some Config Exposure", "severity": "low", "tags": ["exposure", "git", "config"]},
            "severity": "low",
        }
    }
    result = processor.process(raw, scan_id="test-scan-ambiguous", audience="student")
    assert "git" in result["technical_impact"].lower()


# --- Unmatched finding — should not crash ---
def test_unmatched_finding_returns_base_result():
    raw = {
        "source": "nuclei",
        "type": "vulnerability",
        "title": "FingerprintHub Technology Fingerprint: http://juice-shop:3000",
        "raw_data": {
            "info": {
                "name": "FingerprintHub Technology Fingerprint",
                "severity": "info",
                "tags": ["tech", "discovery"],
            },
            "severity": "info",
            "matched-at": "http://juice-shop:3000",
        }
    }
    result = processor.process(raw, scan_id="test-scan-4", audience="student")

    # Should not crash, should return informational base score
    assert result["final_risk_score"] >= 0
    assert result["severity"] == "informational"
    print(f"  ✓ Unmatched finding: severity={result['severity']}, risk={result['final_risk_score']}")


if __name__ == "__main__":
    print("\n=== Processor Intelligence Library Matching Tests ===\n")

    tests = [
        test_xss_finding_matches_intelligence_library,
        test_sqli_finding_matches_intelligence_library,
        test_ssrf_finding_matches_intelligence_library,
        test_unmatched_finding_returns_base_result,
    ]

    passed = 0
    failed = 0
    for test in tests:
        print(f"Running {test.__name__}:")
        try:
            test()
            print(f"  PASSED\n")
            passed += 1
        except AssertionError as e:
            print(f"  FAILED: {e}\n")
            failed += 1

    print(f"=== Results: {passed} passed, {failed} failed ===")
    sys.exit(0 if failed == 0 else 1)
