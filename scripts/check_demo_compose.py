"""Fail CI if the public demo loses its network isolation or private ports."""
import json
import sys


compose = json.load(sys.stdin)
services = compose["services"]
assert compose["networks"]["private"]["internal"] is True
assert set(services["worker"]["networks"]) == {"private"}
assert set(services["api"]["networks"]) == {"private", "web"}
assert services["caddy"]["networks"]["web"]["ipv4_address"] == "172.31.245.254"
assert "--forwarded-allow-ips 172.31.245.254" in " ".join(services["api"]["command"])
assert all(not services[name].get("ports") for name in (
    "api", "worker", "frontend", "db", "redis", "juice-shop"
))
assert services["api"]["environment"]["DEMO_MODE"] == "true"
assert services["worker"]["environment"]["DEMO_MODE"] == "true"
assert {p["published"] for p in services["caddy"]["ports"]} == {"80", "443"}
print("Demo Compose isolation verified")
