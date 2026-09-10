import asyncio
import ipaddress
import re
import urllib.parse

def strip_ansi(text: str) -> str:
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def normalize_target(raw: str) -> str:
    """Normalize a target to a bare lowercase hostname/IP — strips scheme,
    port, path, and a trailing dot — so "example.com", "EXAMPLE.com:8080",
    "example.com/path", and "example.com." all resolve to the same literal
    value across every scanner instead of being treated as different targets."""
    raw = raw.strip()
    parsed = urllib.parse.urlparse(raw if "//" in raw else f"http://{raw}")
    host = parsed.hostname or raw.split("/", 1)[0].split(":", 1)[0]
    return host.rstrip(".").lower()


def is_internal_ip(ip_str: str) -> bool:
    """True if the given IP is loopback, link-local, private, multicast,
    reserved, or unspecified — i.e. not a routable public address."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    return (
        ip.is_loopback
        or ip.is_link_local  # covers the 169.254.169.254 cloud metadata address
        or ip.is_private
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def parse_version_tuple(v: str):
    """Parses a leading "N", "N.N", or "N.N.N" from a version string into a
    comparable tuple. Returns None if nothing numeric could be parsed."""
    if not v:
        return None
    m = re.match(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?", v)
    if not m:
        return None
    return tuple(int(g) for g in m.groups() if g is not None)


def is_outdated(version: str, min_secure_version: str) -> bool | None:
    """True/False when both versions could be parsed and compared, None when
    there's not enough information — never guessed."""
    if not version or not min_secure_version:
        return None
    observed = parse_version_tuple(version)
    floor = parse_version_tuple(min_secure_version)
    if observed is None or floor is None:
        return None
    return observed < floor


async def run_subprocess(command: list[str], timeout: int = 300, input_bytes: bytes | None = None):
    """Run a subprocess and classify the outcome so callers can distinguish
    binary-not-found, timeout, non-zero exit, and success as separate cases
    instead of collapsing them all into an empty result list.

    Returns (stdout: str, stderr: str, status: dict) where status is
    {"status": "success" | "failed" | "timeout" | "no_binary", "detail": str | None}.
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE if input_bytes is not None else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError:
        return "", "", {"status": "no_binary", "detail": f"{command[0]} not found"}

    try:
        stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(input=input_bytes), timeout=timeout)
    except asyncio.TimeoutError:
        try:
            proc.kill()
        except ProcessLookupError:
            pass
        return "", "", {"status": "timeout", "detail": f"exceeded {timeout}s"}

    stdout = strip_ansi(stdout_b.decode('utf-8', errors='replace'))
    stderr = strip_ansi(stderr_b.decode('utf-8', errors='replace'))

    if proc.returncode != 0:
        detail = stderr.strip()[:500] or f"exit code {proc.returncode}"
        return stdout, stderr, {"status": "failed", "detail": detail}

    return stdout, stderr, {"status": "success", "detail": None}
