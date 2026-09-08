from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def rate_limit_key(request: Request) -> str:
    api_key = request.headers.get("x-api-key")
    return api_key if api_key else get_remote_address(request)


limiter = Limiter(key_func=rate_limit_key)
