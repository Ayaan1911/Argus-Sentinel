import httpx
import asyncio
import sys

TARGET = "http://juice-shop:3000"

async def main():
    async with httpx.AsyncClient(timeout=30) as client:
        # Create a scan
        print(f"Creating scan for target: {TARGET}")
        try:
            res = await client.post("http://localhost:8000/api/v1/scans/", json={"target": TARGET, "audience": "student"})
            if res.status_code != 200:
                print(f"Failed to create scan, status code: {res.status_code}, response: {res.text}")
                sys.exit(1)
            scan = res.json()
            print("Scan created response:", scan)
            scan_id = scan.get("id")
            if not scan_id:
                print("No scan ID returned!")
                sys.exit(1)
        except Exception as e:
            print("Error connecting to API:", e)
            sys.exit(1)

        print(f"Waiting for scan {scan_id} to complete...")
        poll_count = 0
        while True:
            await asyncio.sleep(10)
            poll_count += 1
            try:
                s_res = await client.get(f"http://localhost:8000/api/v1/scans/{scan_id}")
                s_data = s_res.json()
                status = s_data.get('status', 'unknown')
                print(f"[{poll_count * 10}s] Status: {status}")
                if status in ["completed", "failed"]:
                    break
                if poll_count > 60:
                    print("Timeout waiting for scan")
                    break
            except Exception as e:
                print("Polling error:", e)

        # Retrieve findings
        try:
            f_res = await client.get(f"http://localhost:8000/api/v1/findings/scan/{scan_id}")
            findings = f_res.json()
        except Exception as e:
            print("Error fetching findings:", e)
            sys.exit(1)

        print("\n" + "="*60)
        print(f"SCAN RESULTS FOR {TARGET}")
        print("="*60)
        print(f"Total Findings: {len(findings)}")
        
        # Breakdown by source/type
        sources = {}
        severities = {}
        for f in findings:
            src = f.get("raw_data", {}).get("source", "unknown")
            sources[src] = sources.get(src, 0) + 1
            
            sev = f.get("severity", "info")
            severities[sev] = severities.get(sev, 0) + 1

        print(f"Sources: {sources}")
        print(f"Severities: {severities}")

        print("\nDetailed Findings Sample:")
        for f in findings:
            # Check for nuclei finding
            src = f.get("raw_data", {}).get("source", "unknown")
            print(f"- [{f.get('severity').upper()}] {f.get('title')} (Risk Score: {f.get('final_risk_score')}) [Source: {src}]")
            
            # Print audience guidance and reasoning breakdown
            print(f"  Reasoning:")
            for step in f.get("reasoning_breakdown", []):
                print(f"    * {step.get('label')}: {step.get('modifier')}")
            
            guidance = f.get("audience_guidance", {})
            print(f"  Guidance (Audience student): {guidance.get('student')}")
            print(f"  Guidance (Audience developer): {guidance.get('developer')}")
            print("-" * 40)

if __name__ == "__main__":
    asyncio.run(main())
