import logging
import xml.etree.ElementTree as ET

from app.intelligence.loader import get_intelligence_loader
from app.scanners.utils import is_internal_ip, is_outdated, normalize_target, run_subprocess

logger = logging.getLogger(__name__)

# Conventional default port for each service name nmap commonly reports.
DEFAULT_PORTS = {
    "ftp": 21, "ssh": 22, "telnet": 23, "smtp": 25, "http": 80,
    "pop3": 110, "rpcbind": 111, "https": 443, "mysql": 3306,
    "ms-wbt-server": 3389, "postgresql": 5432, "vnc": 5900,
    "redis": 6379, "mongodb": 27017, "elasticsearch": 9200,
}

# nmap "product" substring -> (intelligence category, KB key) so a detected
# version can be compared against argus-intelligence/{category}/{key}.json's
# "min_secure_version" field, instead of a separate hardcoded vuln-version list.
PRODUCT_KB_MAP = {
    "openssh": ("services", "ssh"),
    "apache": ("technologies", "apache"),
    "nginx": ("technologies", "nginx"),
    "mysql": ("services", "mysql"),
    "postgresql": ("services", "postgresql"),
    "redis": ("services", "redis"),
    "mongodb": ("services", "mongodb"),
}


def _is_outdated(product: str, version: str) -> bool | None:
    """Returns True/False when a comparison could be made, None when there's
    not enough information (unknown product, unparseable version, or no
    min_secure_version on file for this product) — never guessed."""
    if not product or not version:
        return None
    product_l = product.lower()
    loader = get_intelligence_loader()
    for needle, (category, kb_key) in PRODUCT_KB_MAP.items():
        if needle not in product_l:
            continue
        entry = loader.data.get(category, {}).get(kb_key)
        min_secure = entry.get("min_secure_version") if entry else None
        return is_outdated(version, min_secure)
    return None


def _parse_auth_signals(scripts: dict) -> dict:
    """Only sets keys the relevant nmap script actually ran and reported on;
    leaves them absent (not False) otherwise."""
    signals = {}

    ssh_auth_output = scripts.get("ssh-auth-methods")
    if ssh_auth_output:
        lowered = ssh_auth_output.lower()
        signals["password_auth_enabled"] = "password" in lowered
        signals["key_based_auth"] = "publickey" in lowered

    ftp_anon_output = scripts.get("ftp-anon")
    if ftp_anon_output and "anonymous ftp login allowed" in ftp_anon_output.lower():
        signals["no_authentication"] = True

    # redis-info only gets a "Version:" line back if Redis answered INFO
    # without auth; against a requirepass instance the script prints nothing
    # (checked live against both kinds of Redis).
    redis_info_output = scripts.get("redis-info")
    if redis_info_output and "version:" in redis_info_output.lower():
        signals["no_authentication"] = True

    return signals


async def run(targets: list[str]) -> tuple[list[dict], dict]:
    hostnames = [normalize_target(t) for t in targets]
    logger.info(f"Starting nmap scan for {len(hostnames)} target(s)")
    command = [
        "/usr/bin/nmap", "-sV", "--script=default,ssh-auth-methods,banner,redis-info",
        "-T4", "--open", "-oX", "-", *hostnames,
    ]
    findings = []

    stdout, stderr, status = await run_subprocess(command, timeout=300)
    if status["status"] != "success":
        logger.warning(f"nmap {status['status']}: {status['detail']}")
        return findings, status

    if not stdout:
        return findings, status

    try:
        root = ET.fromstring(stdout)
        for host_el in root.findall('host'):
            addr_el = host_el.find('address')
            host_ip = addr_el.get('addr') if addr_el is not None else None
            internet_facing = (not is_internal_ip(host_ip)) if host_ip else None

            for port in host_el.findall('.//port'):
                portid = port.get('portid')
                protocol = port.get('protocol')
                state_el = port.find('state')
                state = state_el.get('state') if state_el is not None else ''
                service_el = port.find('service')
                service = service_el.get('name') if service_el is not None else ''
                version = service_el.get('version') if service_el is not None else ''
                product = service_el.get('product') if service_el is not None else ''

                scripts = {}
                for script in port.findall('script'):
                    scripts[script.get('id')] = script.get('output')

                port_num = int(portid) if portid else 0
                raw_data = {
                    "port": port_num,
                    "protocol": protocol,
                    "state": state,
                    "service": service,
                    "version": version,
                    "product": product,
                    "scripts": scripts,
                    "firewall_restricted": state == "filtered",
                    "default_port": DEFAULT_PORTS.get((service or "").lower()) == port_num,
                }
                if internet_facing is not None:
                    raw_data["internet_facing"] = internet_facing

                outdated = _is_outdated(product, version)
                if outdated is not None:
                    raw_data["outdated_version"] = outdated

                raw_data.update(_parse_auth_signals(scripts))

                findings.append({
                    "source": "nmap",
                    "type": "port",
                    "title": f"Port {portid}/{protocol}: {service}",
                    "raw_data": raw_data,
                })
    except ET.ParseError as e:
        logger.warning(f"Failed to parse Nmap XML: {e}")
        return findings, {"status": "failed", "detail": f"failed to parse XML output: {e}"}

    logger.info(f"nmap found {len(findings)} results")
    if not findings:
        logger.warning(f"nmap returned 0 results. stdout: {stdout[:200]}")

    return findings, status
