from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings


def rate_limit_key(request: Request) -> str:
    # In demo mode every visitor sends the same public DEMO_API_KEY, so
    # keying by that would put all demo traffic in one shared bucket — key
    # by remote address instead so the per-visitor limit actually applies.
    if settings.DEMO_MODE:
        return get_remote_address(request)
    api_key = request.headers.get("x-api-key")
    return api_key if api_key else get_remote_address(request)


limiter = Limiter(key_func=rate_limit_key)
