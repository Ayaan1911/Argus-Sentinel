import httpx
import asyncio
import sys

async def test_scan():
    async with httpx.AsyncClient(timeout=30) as client:
        # Create a scan
        try:
            res = await client.post("http://localhost:8000/api/v1/scans/", json={"target": "github.com"})
            scan = res.json()
            print("Started scan:", scan)
            if "id" not in scan:
                print("Failed to start scan")
                sys.exit(1)
            scan_id = scan["id"]
        except Exception as e:
            print("Error connecting to API:", e)
            sys.exit(1)
            
        print("Waiting for scan to complete...")
        while True:
            await asyncio.sleep(10)
            try:
                s_res = await client.get(f"http://localhost:8000/api/v1/scans/{scan_id}")
                s_data = s_res.json()
                status = s_data.get('status', 'unknown')
                print(f"Scan status: {status}, Stage: {s_data.get('current_stage')}")
                if status in ["completed", "failed"]:
                    break
            except Exception as e:
                print("Polling error:", e)
        
        # Get findings
        f_res = await client.get(f"http://localhost:8000/api/v1/findings/scan/{scan_id}")
        findings = f_res.json()
        print(f"Total findings: {len(findings)}")
        print("Top 10 findings:")
        for f in findings[:10]:
            print(f"- {f['type']}: {f['title']} (Risk: {f['final_risk_score']}) [Source: {f.get('raw_data', {}).get('source', 'unknown')}]")

if __name__ == "__main__":
    asyncio.run(test_scan())
