import requests
scan_id = 'c55ecb3d-2a6a-4c9a-ab84-7fbfd3a2b7bb'
url = f"http://localhost:8000/api/scan/{scan_id}"
res = requests.get(url)
data = res.json().get("data", {})
subdomains = data.get("subdomains", [])
with_ss = [s for s in subdomains if s.get("screenshot_path")]
print(f"Screenshots in API response: {len(with_ss)}")
