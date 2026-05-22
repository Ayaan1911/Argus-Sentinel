"""
PDF Report Generator for Argus-Sentinel.

Generates a professional penetration testing style PDF report for a completed scan.
Uses Jinja2 for HTML templating and WeasyPrint for HTML→PDF conversion.
"""
import os
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.models import Scan, Subdomain, Secret, Endpoint, TakeoverRisk, AISummary, VulnerabilityFinding

TEMPLATES_DIR = Path(__file__).parent


SEVERITY_ORDER = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}


def generate_pdf(scan_id: str, db) -> bytes:
    """
    Query all scan data, render the Jinja2 HTML template, and convert to PDF bytes.
    Returns raw PDF bytes.
    """
    from weasyprint import HTML, CSS

    # ── Fetch all data ─────────────────────────────────────────────────────────
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise ValueError(f'Scan {scan_id} not found')

    subdomains   = db.query(Subdomain).filter(Subdomain.scan_id == scan_id).all()
    secrets      = db.query(Secret).filter(Secret.scan_id == scan_id).order_by(Secret.severity).all()
    endpoints    = db.query(Endpoint).filter(Endpoint.scan_id == scan_id).all()
    takeovers    = db.query(TakeoverRisk).filter(TakeoverRisk.scan_id == scan_id).all()
    ai_summary   = db.query(AISummary).filter(AISummary.scan_id == scan_id).first()
    vulns        = (
        db.query(VulnerabilityFinding)
        .filter(VulnerabilityFinding.scan_id == scan_id)
        .all()
    )

    # Sort vulnerabilities by severity
    vulns_sorted = sorted(vulns, key=lambda v: SEVERITY_ORDER.get(v.severity.lower(), 9))

    # ── Compute stats ──────────────────────────────────────────────────────────
    live_hosts   = [s for s in subdomains if s.is_alive]
    all_ports    = [p for s in subdomains for p in (s.ports or [])]
    all_techs    = sorted({t for s in subdomains for t in (s.technologies or []) if isinstance(t, str)})

    vuln_critical = [v for v in vulns if v.severity == 'critical']
    vuln_high     = [v for v in vulns if v.severity == 'high']
    vuln_medium   = [v for v in vulns if v.severity == 'medium']
    vuln_low      = [v for v in vulns if v.severity == 'low']
    vuln_info     = [v for v in vulns if v.severity == 'info']

    secret_critical = [s for s in secrets if (s.severity or 'medium') == 'critical']
    secret_high     = [s for s in secrets if (s.severity or 'medium') == 'high']
    secret_medium   = [s for s in secrets if (s.severity or 'medium') == 'medium']

    # ── Render template ────────────────────────────────────────────────────────
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template('template.html')

    html_content = template.render(
        scan=scan,
        subdomains=subdomains,
        live_hosts=live_hosts,
        all_ports=all_ports,
        all_techs=all_techs,
        secrets=secrets,
        endpoints=endpoints,
        takeovers=takeovers,
        ai_summary=ai_summary,
        vulns=vulns_sorted,
        vuln_critical=vuln_critical,
        vuln_high=vuln_high,
        vuln_medium=vuln_medium,
        vuln_low=vuln_low,
        vuln_info=vuln_info,
        secret_critical=secret_critical,
        secret_high=secret_high,
        secret_medium=secret_medium,
        generated_at=datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
    )

    # ── Convert to PDF ─────────────────────────────────────────────────────────
    pdf_bytes = HTML(string=html_content, base_url=str(TEMPLATES_DIR)).write_pdf()
    return pdf_bytes
