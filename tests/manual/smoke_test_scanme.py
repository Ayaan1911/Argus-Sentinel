import httpx
import asyncio
import sys

TARGET = "scanme.nmap.org"

async def test_scan():
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            res = await client.post("http://localhost:8000/api/v1/scans/", json={"target": TARGET})
            scan = res.json()
            print(f"Started scan against {TARGET}:", scan)
            if "id" not in scan:
                print("Failed to start scan:", scan)
                sys.exit(1)
            scan_id = scan["id"]
        except Exception as e:
            print("Error connecting to API:", e)
            sys.exit(1)
            
        print("Waiting for scan to complete...")
        poll_count = 0
        while True:
            await asyncio.sleep(15)
            poll_count += 1
            try:
                s_res = await client.get(f"http://localhost:8000/api/v1/scans/{scan_id}")
                s_data = s_res.json()
                status = s_data.get('status', 'unknown')
                print(f"[{poll_count * 15}s] Scan status: {status}, Stage: {s_data.get('current_stage')}")
                if status in ["completed", "failed"]:
                    break
                if poll_count > 60:  # 15 min timeout
                    print("Timed out waiting for scan")
                    break
            except Exception as e:
                print("Polling error:", e)
        
        # Get findings
        f_res = await client.get(f"http://localhost:8000/api/v1/findings/scan/{scan_id}")
        findings = f_res.json()
        
        # Categorise by type
        by_type = {}
        for f in findings:
            t = f.get('type', 'unknown')
            by_type[t] = by_type.get(t, 0) + 1
        
        print(f"\n=== RESULTS for {TARGET} ===")
        print(f"Total findings: {len(findings)}")
        print(f"By type: {by_type}")
        
        vuln_findings = [f for f in findings if f.get('type') == 'vulnerability']
        print(f"\nVulnerability findings (nuclei): {len(vuln_findings)}")
        for f in vuln_findings[:5]:
            print(f"  - [{f['severity'].upper()}] {f['title']} (Risk: {f['final_risk_score']:.1f})")
            if f.get('reasoning_breakdown'):
                for step in f['reasoning_breakdown'][:2]:
                    print(f"    → {step.get('label')}: {step.get('modifier')}")
        
        if len(vuln_findings) == 0:
            print("\nWARNING: No nuclei findings. Check worker logs:")
            # Print raw findings for diagnosis
            for f in findings[:5]:
                print(f"  - {f['type']}: {f['title']}")

if __name__ == "__main__":
    asyncio.run(test_scan())
