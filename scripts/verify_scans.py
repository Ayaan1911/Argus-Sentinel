import httpx
import asyncio

async def run_scan(target: str, wait_minutes: int = 8) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            res = await client.post("http://localhost:8000/api/v1/scans/", json={"target": target})
            scan = res.json()
        except Exception as e:
            return {"target": target, "error": str(e)}

        if "id" not in scan:
            return {"target": target, "error": scan}

        scan_id = scan["id"]
        print(f"[{target}] Scan started: {scan_id}")

        for i in range(wait_minutes * 4):
            await asyncio.sleep(15)
            try:
                s = (await client.get(f"http://localhost:8000/api/v1/scans/{scan_id}")).json()
                status = s.get("status", "?")
                print(f"[{target}] {(i+1)*15}s -> status={status}")
                if status in ["completed", "failed"]:
                    break
            except Exception as e:
                print(f"[{target}] poll error: {e}")

        try:
            findings = (await client.get(f"http://localhost:8000/api/v1/findings/scan/{scan_id}")).json()
        except Exception as e:
            return {"target": target, "scan_id": scan_id, "error": f"findings fetch: {e}"}

        by_type = {}
        for f in findings:
            t = f.get("type", "?")
            by_type[t] = by_type.get(t, 0) + 1

        vuln = [f for f in findings if f.get("type") == "vulnerability"]
        return {
            "target": target,
            "scan_id": scan_id,
            "total": len(findings),
            "by_type": by_type,
            "nuclei_count": len(vuln),
            "nuclei_samples": [
                {"title": f["title"], "severity": f.get("severity","?"), "risk": f.get("final_risk_score")}
                for f in vuln[:5]
            ],
        }

async def main():
    print("="*60)
    print("SCAN 1: github.com")
    print("="*60)
    r1 = await run_scan("github.com", wait_minutes=6)
    print(f"\n[github.com] total={r1.get('total')} by_type={r1.get('by_type')} nuclei={r1.get('nuclei_count')}")
    for s in r1.get("nuclei_samples", []):
        print(f"  -> [{s['severity'].upper()}] {s['title']} risk={s['risk']}")
    if r1.get("error"):
        print(f"  ERROR: {r1['error']}")

    print()
    print("="*60)
    print("SCAN 2: testphp.vulnweb.com")
    print("="*60)
    r2 = await run_scan("testphp.vulnweb.com", wait_minutes=3)
    print(f"\n[testphp.vulnweb.com] total={r2.get('total')} by_type={r2.get('by_type')} nuclei={r2.get('nuclei_count')}")
    for s in r2.get("nuclei_samples", []):
        print(f"  -> [{s['severity'].upper()}] {s['title']} risk={s['risk']}")
    if r2.get("error"):
        print(f"  ERROR: {r2['error']}")

if __name__ == "__main__":
    asyncio.run(main())
