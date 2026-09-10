from app.engines.diff import diff_findings


def _finding(type_="port", title="Port 22/tcp: ssh", severity="low", risk=3.0, confidence=0.9):
    return {
        "type": type_,
        "title": title,
        "severity": severity,
        "final_risk_score": risk,
        "confidence": confidence,
    }


def test_finding_only_in_current_is_new():
    current = [_finding(title="Port 22/tcp: ssh")]
    previous = []

    result = diff_findings(current, previous)

    assert result["summary"] == {"new": 1, "resolved": 0, "changed": 0, "unchanged": 0}
    assert result["new_findings"] == current
    assert result["resolved_findings"] == []
    assert result["changed_findings"] == []


def test_finding_only_in_previous_is_resolved():
    current = []
    previous = [_finding(title="Port 8080/tcp: tcpwrapped")]

    result = diff_findings(current, previous)

    assert result["summary"] == {"new": 0, "resolved": 1, "changed": 0, "unchanged": 0}
    assert result["resolved_findings"] == previous


def test_matching_finding_with_same_score_severity_confidence_is_unchanged():
    current = [_finding(title="Port 22/tcp: ssh", severity="low", risk=3.0, confidence=0.9)]
    previous = [_finding(title="Port 22/tcp: ssh", severity="low", risk=3.0, confidence=0.9)]

    result = diff_findings(current, previous)

    assert result["summary"] == {"new": 0, "resolved": 0, "changed": 0, "unchanged": 1}
    assert result["unchanged_findings"] == current


def test_matching_finding_with_different_risk_score_is_changed():
    current = [_finding(title="Port 22/tcp: ssh", risk=7.5)]
    previous = [_finding(title="Port 22/tcp: ssh", risk=4.0)]

    result = diff_findings(current, previous)

    assert result["summary"]["changed"] == 1
    changed = result["changed_findings"][0]
    assert changed["finding"]["final_risk_score"] == 7.5
    assert changed["previous_risk_score"] == 4.0
    assert changed["previous_severity"] == "low"
    assert changed["previous_confidence"] == 0.9


def test_matching_finding_with_different_severity_only_is_changed():
    current = [_finding(title="Port 22/tcp: ssh", severity="high", risk=3.0)]
    previous = [_finding(title="Port 22/tcp: ssh", severity="low", risk=3.0)]

    result = diff_findings(current, previous)

    assert result["summary"]["changed"] == 1


def test_matching_finding_with_different_confidence_only_is_changed():
    current = [_finding(title="Port 22/tcp: ssh", confidence=0.95)]
    previous = [_finding(title="Port 22/tcp: ssh", confidence=0.5)]

    result = diff_findings(current, previous)

    assert result["summary"]["changed"] == 1


def test_match_key_is_case_insensitive_on_type_but_not_title():
    current = [_finding(type_="PORT", title="Port 22/tcp: ssh")]
    previous = [_finding(type_="port", title="Port 22/tcp: ssh")]

    result = diff_findings(current, previous)

    assert result["summary"]["unchanged"] == 1


def test_mixed_scan_buckets_all_computed_together():
    current = [
        _finding(title="Port 22/tcp: ssh", risk=3.0),       # unchanged
        _finding(title="Port 3306/tcp: mysql", risk=8.0),   # changed (was 4.0)
        _finding(title="Subdomain: new.example.com"),        # new
    ]
    previous = [
        _finding(title="Port 22/tcp: ssh", risk=3.0),
        _finding(title="Port 3306/tcp: mysql", risk=4.0),
        _finding(title="Subdomain: old.example.com"),        # resolved
    ]

    result = diff_findings(current, previous)

    assert result["summary"] == {"new": 1, "resolved": 1, "changed": 1, "unchanged": 1}


def test_duplicate_title_matches_positionally():
    # Two findings sharing the same (type, title) key — best-effort
    # positional pairing rather than a guaranteed-correct identity match.
    current = [
        _finding(title="Missing Header", risk=1.0),
        _finding(title="Missing Header", risk=9.0),
    ]
    previous = [
        _finding(title="Missing Header", risk=1.0),
    ]

    result = diff_findings(current, previous)

    # First pairs up (unchanged), second has no previous counterpart (new).
    assert result["summary"] == {"new": 1, "resolved": 0, "changed": 0, "unchanged": 1}
