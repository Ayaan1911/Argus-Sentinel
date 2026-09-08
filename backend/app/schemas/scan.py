import ipaddress
import socket
import urllib.parse

from pydantic import BaseModel, UUID4, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from .finding import FindingRead
from app.scanners.utils import is_internal_ip

# The bundled juice-shop container is the intended default authorized local
# test target (see docker-compose.yml) and is explicitly exempt from the
# private/internal IP block below even though it resolves to an internal
# Docker network address.
ALLOWED_INTERNAL_HOSTNAMES = {"juice-shop"}


def _extract_hostname(raw_target: str) -> str:
    host = raw_target.strip()
    if "//" in host:
        host = urllib.parse.urlparse(host).hostname or host
    # Strip a trailing path and/or port so "example.com:8080/x" -> "example.com"
    host = host.split("/", 1)[0]
    if not host.startswith("["):  # not a bracketed IPv6 literal
        host = host.split(":", 1)[0]
    return host


def validate_scan_target(raw_target: str) -> str:
    hostname = _extract_hostname(raw_target)
    if not hostname:
        raise ValueError("target is required")

    if hostname.lower() in ALLOWED_INTERNAL_HOSTNAMES:
        return raw_target.strip()

    try:
        resolved_ips = [hostname]
        ipaddress.ip_address(hostname)  # raises ValueError if not a literal IP
    except ValueError:
        # ponytail: DNS-resolve-time check only, vulnerable to DNS rebinding
        # between this validation and actual scanner dispatch — add
        # resolved-IP pinning at scanner dispatch time if that threat matters.
        try:
            infos = socket.getaddrinfo(hostname, None)
        except socket.gaierror as e:
            raise ValueError(f"Could not resolve target hostname: {hostname}") from e
        resolved_ips = [info[4][0] for info in infos]

    for ip_str in resolved_ips:
        if is_internal_ip(ip_str):
            raise ValueError(
                f"Target '{hostname}' resolves to a disallowed address ({ip_str}); "
                "loopback, link-local, private, and multicast ranges are not permitted"
            )

    return raw_target.strip()


class ScanBase(BaseModel):
    target: str
    audience: str = "student"

    @field_validator("target")
    @classmethod
    def _validate_target(cls, v: str) -> str:
        try:
            return validate_scan_target(v)
        except ValueError as e:
            raise ValueError(str(e)) from e

class ScanCreate(ScanBase):
    pass

class ScanStatusUpdate(BaseModel):
    status: str

class ScanRead(ScanBase):
    id: UUID4
    status: str
    stage_status: Dict[str, Any] = {}
    created_at: datetime
    updated_at: Optional[datetime] = None
    findings: List[FindingRead] = []

    class Config:
        from_attributes = True
