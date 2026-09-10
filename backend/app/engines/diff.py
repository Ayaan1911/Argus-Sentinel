"""Compares the findings of two completed scans of the same target.

Findings don't have a stable identity across scans — every scan creates
fresh rows with fresh UUIDs — so matching is done on (type, title) as a
practical approximation, not a guaranteed-correct identity match. This
works well in practice because titles are built from stable scanner-
reported values (e.g. "Port 8080/tcp: tcpwrapped", "Subdomain:
mail.example.com") that don't change between runs unless the underlying
thing actually changed, but it's still a heuristic: it can produce a false
match/miss if a scanner's title format happens to embed a value that
legitimately varies scan-to-scan for what's really the same finding (e.g. a
nuclei template whose title embeds a timestamp), or a false "new"+"resolved"
pair if a title's wording changes between scanner tool versions.
"""


def _match_key(finding: dict) -> tuple:
    return ((finding.get("type") or "").lower(), finding.get("title") or "")


def _group_by_key(findings: list[dict]) -> dict[tuple, list[dict]]:
    grouped: dict[tuple, list[dict]] = {}
    for f in findings:
        grouped.setdefault(_match_key(f), []).append(f)
    return grouped


def _is_changed(current: dict, previous: dict) -> bool:
    return (
        current.get("final_risk_score") != previous.get("final_risk_score")
        or current.get("severity") != previous.get("severity")
        or current.get("confidence") != previous.get("confidence")
    )


def diff_findings(current: list[dict], previous: list[dict]) -> dict:
    """current/previous are lists of finding dicts (FindingRead-shaped) for
    the two scans being compared, current being the newer of the two.

    Findings sharing a (type, title) key are matched positionally within
    that key's group — the common case is at most one finding per key, so
    this only matters for scans with duplicate-title findings, where it's a
    best-effort pairing rather than a guaranteed-correct one."""
    current_by_key = _group_by_key(current)
    previous_by_key = _group_by_key(previous)

    new_findings, changed_findings, unchanged_findings, resolved_findings = [], [], [], []

    for key in current_by_key.keys() | previous_by_key.keys():
        cur_list = current_by_key.get(key, [])
        prev_list = previous_by_key.get(key, [])
        matched = min(len(cur_list), len(prev_list))

        for i in range(matched):
            cur, prev = cur_list[i], prev_list[i]
            if _is_changed(cur, prev):
                changed_findings.append({
                    "finding": cur,
                    "previous_risk_score": prev.get("final_risk_score"),
                    "previous_severity": prev.get("severity"),
                    "previous_confidence": prev.get("confidence"),
                })
            else:
                unchanged_findings.append(cur)

        new_findings.extend(cur_list[matched:])
        resolved_findings.extend(prev_list[matched:])

    return {
        "new_findings": new_findings,
        "resolved_findings": resolved_findings,
        "changed_findings": changed_findings,
        "unchanged_findings": unchanged_findings,
        "summary": {
            "new": len(new_findings),
            "resolved": len(resolved_findings),
            "changed": len(changed_findings),
            "unchanged": len(unchanged_findings),
        },
    }
