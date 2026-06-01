import requests
import json
import sys

res = requests.get('http://localhost:8000/api/scans')
scans = res.json()
if 'data' in scans:
    scans = scans['data']

if not scans:
    print("No scans available.")
    sys.exit(0)

scan_id = scans[0]['id']
print(f"Testing PDF for scan {scan_id}...")

pdf_res = requests.get(f'http://localhost:8000/api/scan/{scan_id}/report/pdf')
if pdf_res.status_code == 200:
    print(f"Success! PDF size: {len(pdf_res.content)} bytes")
else:
    print(f"Failed: {pdf_res.status_code}")
    print(pdf_res.text)
