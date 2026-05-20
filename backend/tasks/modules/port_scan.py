import subprocess
import logging
import xml.etree.ElementTree as ET
from app.models import Subdomain, Port

logger = logging.getLogger(__name__)

# Limit port scanning to this many hosts per scan to avoid extremely long runs
MAX_HOSTS = 50

# Top ports to scan — balances coverage vs speed
TOP_PORTS = '1000'


def parse_nmap_xml(xml_output: str, subdomain_id: int) -> list:
    """Parse nmap XML output and return a list of Port ORM objects."""
    ports = []
    try:
        root = ET.fromstring(xml_output)
        for host in root.findall('host'):
            for port_elem in host.findall('./ports/port'):
                port_num = port_elem.get('portid')
                if not port_num:
                    continue
                port_num = int(port_num)
                protocol = port_elem.get('protocol', 'tcp')

                state_elem = port_elem.find('state')
                if state_elem is None or state_elem.get('state') != 'open':
                    continue

                service = ''
                version = ''
                service_elem = port_elem.find('service')
                if service_elem is not None:
                    service = service_elem.get('name', '')
                    product = service_elem.get('product', '')
                    ver = service_elem.get('version', '')
                    version = f'{product} {ver}'.strip()

                ports.append(Port(
                    subdomain_id=subdomain_id,
                    port=port_num,
                    protocol=protocol,
                    service=service,
                    version=version if version else None,
                ))
    except ET.ParseError as e:
        logger.error(f'nmap XML parse error: {e}')
    except Exception as e:
        logger.error(f'Unexpected error parsing nmap output: {e}')
    return ports


def run(scan_id: str, db) -> None:
    """
    Stage 3: Port Scanning.
    Runs nmap against each live host. Limits to MAX_HOSTS to control scan time.
    Stores open ports with service/version info in the database.
    """
    live_subs = (
        db.query(Subdomain)
        .filter(Subdomain.scan_id == scan_id, Subdomain.is_alive == True)
        .limit(MAX_HOSTS)
        .all()
    )

    if not live_subs:
        logger.info(f'[{scan_id}] No live hosts for port scanning')
        return

    logger.info(f'[{scan_id}] Port scanning {len(live_subs)} live hosts')
    nmap_available = True

    for sub in live_subs:
        if not nmap_available:
            break

        # Clear stale port data before re-scanning
        db.query(Port).filter(Port.subdomain_id == sub.id).delete()
        db.commit()

        try:
            proc = subprocess.run(
                [
                    'nmap',
                    '-T4',
                    '--top-ports', TOP_PORTS,
                    '-sV',
                    '--open',
                    '--host-timeout', '90s',
                    '-oX', '-',      # XML output to stdout
                    sub.subdomain,
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )

            ports = parse_nmap_xml(proc.stdout, sub.id)
            for p in ports:
                db.add(p)
            db.commit()

            logger.info(f'[{scan_id}] {sub.subdomain}: {len(ports)} open port(s)')

        except subprocess.TimeoutExpired:
            logger.warning(f'[{scan_id}] nmap timeout for {sub.subdomain}')
            db.commit()
        except FileNotFoundError:
            logger.warning('[port_scan] nmap binary not found — skipping port scan stage')
            nmap_available = False
        except Exception as e:
            logger.error(f'[{scan_id}] nmap error for {sub.subdomain}: {e}')
            db.commit()

    logger.info(f'[{scan_id}] Port scanning complete')
