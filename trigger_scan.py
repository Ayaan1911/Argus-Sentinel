import requests
import json
import time

url = "http://localhost:8000/api/scan"
payload = {"domain": "hackthebox.com"}
headers = {"Content-Type": "application/json"}

print("Starting scan for hackthebox.com...")
response = requests.post(url, json=payload, headers=headers)
data = response.json()
scan_id = data.get("data", {}).get("id")

if scan_id:
    print(f"Scan started successfully! ID: {scan_id}")
else:
    print("Failed to start scan:", data)
    exit(1)

print(f"Tracking scan {scan_id}...")
status_url = f"http://localhost:8000/api/scan/{scan_id}"
while True:
    res = requests.get(status_url)
    scan_data = res.json().get("data", {})
    status = scan_data.get("status")
    stage = scan_data.get("current_stage")
    print(f"Status: {status} | Stage: {stage}")
    
    if status in ["complete", "failed"]:
        print(f"Scan finished with status: {status}")
        
        # Diagnostics
        subdomains = scan_data.get("subdomains", [])
        live_hosts = [s for s in subdomains if s.get("is_alive")]
        screenshots = [s for s in subdomains if s.get("screenshot_path")]
        
        print("\n--- RESULTS ---")
        print(f"Total Subdomains: {len(subdomains)}")
        print(f"Live Hosts: {len(live_hosts)}")
        print(f"Screenshots returned by API: {len(screenshots)}")
        break
    
    time.sleep(10)
