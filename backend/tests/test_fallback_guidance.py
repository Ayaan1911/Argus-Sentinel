"""
Test: fallback intelligence entries populate guidance for unmatched finding types,
while specific matches (SSH, Apache, XSS) still use their real library entries.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.scanners.processor import FindingProcessor
p = FindingProcessor()

def test_live_host_gets_fallback_guidance():
    r = p.process({
        "source": "httpx", "type": "technology",
        "title": "Live Host: http://scanme.nmap.org",
        "raw_data": {"url": "http://scanme.nmap.org"}
    }, "test", "student")
    assert r["technical_impact"] != "Unknown", "Live Host should hit live_host.json"
    assert r["audience_guidance"].get("student"), "student guidance must be populated"
    assert r["audience_guidance"].get("developer"), "developer guidance must be populated"
    assert r["audience_guidance"].get("bug_bounty_hunter"), "bug_bounty_hunter must be populated"
    assert r["audience_guidance"].get("pentester"), "pentester must be populated"
    assert r["audience_guidance"].get("security_team"), "security_team must be populated"
    print(f"  PASS  Live Host - student: {r['audience_guidance']['student'][:80]}...")
    print(f"        all personas: {list(r['audience_guidance'].keys())}")

def test_tcpwrapped_port_gets_fallback_guidance():
    r = p.process({
        "source": "nmap", "type": "port",
        "title": "Port 21/tcp: tcpwrapped",
        "raw_data": {"service": "tcpwrapped", "port": 21, "protocol": "tcp",
                     "state": "open", "version": "", "scripts": {}}
    }, "test", "bug_bounty_hunter")
    assert r["technical_impact"] != "Unknown", "tcpwrapped should hit generic_port.json"
    assert r["audience_guidance"].get("bug_bounty_hunter"), "bug_bounty_hunter guidance must be populated"
    print(f"  PASS  tcpwrapped - bug_bounty_hunter: {r['audience_guidance']['bug_bounty_hunter'][:80]}...")

def test_ssh_still_uses_specific_entry():
    r = p.process({
        "source": "nmap", "type": "port",
        "title": "Port 22/tcp: ssh",
        "raw_data": {"service": "ssh", "port": 22, "protocol": "tcp",
                     "state": "open", "version": "OpenSSH 6.6.1p1", "scripts": {}}
    }, "test", "pentester")
    # Must use specific ssh.json, not generic_port.json
    assert "ssh" in r["technical_impact"].lower() or "secure shell" in r["technical_impact"].lower(), \
        f"SSH should use ssh.json, got: {r['technical_impact']}"
    assert r["audience_guidance"].get("pentester"), "pentester guidance must be populated"
    print(f"  PASS  SSH uses specific entry: {r['technical_impact'][:60]}...")
    print(f"        pentester: {r['audience_guidance']['pentester'][:80]}...")

def test_subdomain_gets_guidance():
    r = p.process({
        "source": "subfinder", "type": "subdomain",
        "title": "Subdomain: nmap.scanme.nmap.org",
        "raw_data": {"host": "nmap.scanme.nmap.org"}
    }, "test", "student")
    assert r["technical_impact"] != "Unknown", "Subdomain should hit subdomain.json"
    assert r["audience_guidance"].get("student"), "student guidance must be populated"
    print(f"  PASS  Subdomain - student: {r['audience_guidance']['student'][:80]}...")

def test_xss_still_uses_specific_vuln_entry():
    r = p.process({
        "source": "nuclei", "type": "vulnerability",
        "title": "Reflected Cross-Site Scripting: http://target.com/search?q=test",
        "raw_data": {
            "info": {"name": "Reflected XSS", "severity": "medium", "tags": ["xss", "rxss"]},
            "severity": "medium"
        }
    }, "test", "developer")
    assert "xss" in r["technical_impact"].lower() or "script" in r["technical_impact"].lower(), \
        f"XSS should use xss.json, got: {r['technical_impact']}"
    assert r["audience_guidance"].get("developer"), "developer guidance must be populated"
    print(f"  PASS  XSS uses specific vuln entry: {r['technical_impact'][:60]}...")

if __name__ == "__main__":
    print("\n=== Fallback Guidance Tests ===\n")
    tests = [
        test_live_host_gets_fallback_guidance,
        test_tcpwrapped_port_gets_fallback_guidance,
        test_ssh_still_uses_specific_entry,
        test_subdomain_gets_guidance,
        test_xss_still_uses_specific_vuln_entry,
    ]
    passed = failed = 0
    for t in tests:
        print(f"Running {t.__name__}:")
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {e}")
            failed += 1
        print()
    print(f"=== {passed} passed, {failed} failed ===")
    sys.exit(0 if failed == 0 else 1)
