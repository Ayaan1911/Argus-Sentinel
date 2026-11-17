"""Compares two completed scans of the same target.

New port findings match by address, port, and protocol. Historical rows
without an address keep the former (type, title) matching heuristic.
Other finding types still match by (type, title).
"""


def _match_key(finding: dict, host_aware: bool) -> tuple:
    type_ = (finding.get("type") or "").lower()
    if type_ == "port" and host_aware:
        raw = finding["raw_data"]
        return (type_, raw["host"], raw["port"], raw["protocol"])
    return (type_, finding.get("title") or "")


def _group_by_key(findings: list[dict], host_aware: bool) -> dict[tuple, list[dict]]:
    grouped: dict[tuple, list[dict]] = {}
    for f in findings:
        grouped.setdefault(_match_key(f, host_aware), []).append(f)
    return grouped


def _is_changed(current: dict, previous: dict) -> bool:
    return (
        current.get("title") != previous.get("title")
        or current.get("final_risk_score") != previous.get("final_risk_score")
        or current.get("severity") != previous.get("severity")
        or current.get("confidence") != previous.get("confidence")
    )


def diff_findings(current: list[dict], previous: list[dict]) -> dict:
    """current/previous are lists of finding dicts (FindingRead-shaped) for
    the two scans being compared, current being the newer of the two.

    Duplicate keys are paired positionally. Older port findings with no
    host identity remain a best-effort comparison."""
    # shortcut: old port rows lack host data; retire title matching after old histories are removed.
    ports = [f for f in current + previous if (f.get("type") or "").lower() == "port"]
    host_aware = all(
        (raw := f.get("raw_data") or {}).get("host")
        and raw.get("port") is not None
        and raw.get("protocol")
        for f in ports
    )
    current_by_key = _group_by_key(current, host_aware)
    previous_by_key = _group_by_key(previous, host_aware)

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
