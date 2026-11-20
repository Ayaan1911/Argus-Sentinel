"""The demo rate limit must use Caddy's client, never a forged peer header."""
import asyncio

from fastapi import Request
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.config import settings
from app.rate_limit import rate_limit_key


def test_demo_proxy_address_is_trusted_only_from_caddy(monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", True)

    async def key_for(peer):
        keys = []

        async def app(scope, receive, send):
            keys.append(rate_limit_key(Request(scope)))

        scope = {
            "type": "http", "client": (peer, 1234), "scheme": "http",
            "headers": [(b"x-forwarded-for", b"203.0.113.7")],
        }
        middleware = ProxyHeadersMiddleware(app, trusted_hosts="172.31.245.254")
        await middleware(scope, None, None)
        return keys[0]

    assert asyncio.run(key_for("172.31.245.254")) == "203.0.113.7"
    assert asyncio.run(key_for("172.31.245.9")) == "172.31.245.9"
