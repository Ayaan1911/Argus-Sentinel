import ipaddress
import socket

from pydantic import BaseModel, UUID4, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from .finding import FindingRead
from app.config import settings
from app.scanners.utils import is_internal_ip, normalize_target

# The bundled juice-shop container is the intended default authorized local
# test target (see docker-compose.yml) and is explicitly exempt from the
# private/internal IP block below even though it resolves to an internal
# Docker network address.
ALLOWED_INTERNAL_HOSTNAMES = {"juice-shop"}

# Targets a public demo deployment (DEMO_MODE=true) is locked to — a
# different, broader concept than ALLOWED_INTERNAL_HOSTNAMES above, which is
# specifically about exempting an internal Docker hostname from the
# private-IP block. scanme.nmap.org is a real public domain (no internal-IP
# exemption needed) but is the Nmap project's own dedicated, explicitly
# authorized public scan target, so it's safe to allow here the same way.
DEMO_ALLOWED_TARGETS = ALLOWED_INTERNAL_HOSTNAMES | {"scanme.nmap.org"}


def validate_scan_target(raw_target: str) -> str:
    hostname = normalize_target(raw_target)
    if not hostname:
        raise ValueError("target is required")

    if settings.DEMO_MODE:
        # Inverted from the normal allowlist-exception below: in a public
        # demo deployment, the bundled/authorized targets aren't just exempt
        # from the private-IP block, they're the ONLY valid targets, full
        # stop — including domains that would otherwise pass every check below.
        if hostname not in DEMO_ALLOWED_TARGETS:
            raise ValueError(
                "This is a public demo deployment — scans are locked to the authorized "
                f"demo targets ({', '.join(sorted(DEMO_ALLOWED_TARGETS))}). "
                "Self-host Argus Sentinel to scan your own targets."
            )
        return hostname

    if hostname in ALLOWED_INTERNAL_HOSTNAMES:
        return hostname

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

    # Store (and dedup against) the normalized form so "example.com",
    # "EXAMPLE.com:8080", and "example.com/path" are all the same target
    # across the DB, the dedup check, and every scanner.
    return hostname


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
    # Bypasses reuse of a recent completed scan for the same target
    # (see routers/scans.py's create_scan) and forces a fresh one.
    force_rescan: bool = False

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
