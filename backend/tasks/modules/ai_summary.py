import os
import logging
import requests
from datetime import datetime
from app.database import SessionLocal
from app.models import Scan, Subdomain, Secret, Endpoint, TakeoverRisk, AISummary, VulnerabilityFinding

logger = logging.getLogger(__name__)

OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions'
DEFAULT_MODEL = 'openai/gpt-4o-mini'
MAX_TOKENS = 2000
API_TIMEOUT = 90  # seconds


def build_prompt(
    scan: Scan,
    subdomains: list,
    secrets: list,
    endpoints: list,
    takeover_risks: list,
    vuln_findings: list = None,
) -> str:
    """Build a detailed recon summary prompt for the AI model."""
    alive_count = sum(1 for s in subdomains if s.is_alive)

    # Collect open ports with host context
    all_ports = []
    for s in subdomains:
        for p in s.ports:
            all_ports.append(
                f'{s.subdomain}:{p.port}/{p.protocol} ({p.service or "unknown"})'
            )

    # Collect unique technologies
    all_techs: set[str] = set()
    for s in subdomains:
        for t in (s.technologies or []):
            if isinstance(t, str) and t.strip():
                all_techs.add(t.strip())

    # Format samples (limit length to stay within token budget)
    ports_sample = '\n'.join(all_ports[:25]) if all_ports else 'None detected'
    secrets_sample = '\n'.join([
        f'  - [{s.secret_type}] in {s.file_url} at line {s.line_number}: {s.matched_value}...'
        for s in secrets[:20]
    ]) if secrets else 'None detected'
    takeovers_sample = '\n'.join([
        f'  - {r.subdomain} → {r.cname or "N/A"} ({r.provider})'
        for r in takeover_risks
    ]) if takeover_risks else 'None detected'
    endpoints_sample = '\n'.join([e.url for e in endpoints[:25]]) if endpoints else 'None detected'
    techs_sample = ', '.join(sorted(all_techs)[:30]) if all_techs else 'Unknown'

    # Vulnerability findings summary
    vuln_findings = vuln_findings or []
    vuln_critical = [v for v in vuln_findings if v.severity == 'critical']
    vuln_high     = [v for v in vuln_findings if v.severity == 'high']
    vuln_medium   = [v for v in vuln_findings if v.severity == 'medium']
    vulns_sample  = '\n'.join([
        f'  [{v.severity.upper()}] {v.template_name} @ {v.matched_at}'
        for v in vuln_findings[:20]
    ]) if vuln_findings else 'None detected'

    return f"""You are a senior bug bounty hunter and penetration tester analyzing automated reconnaissance results.

TARGET DOMAIN: {scan.domain}

═══ RECON STATISTICS ═══
• Total Subdomains Found   : {len(subdomains)}
• Live Hosts               : {alive_count}
• Open Ports Detected      : {len(all_ports)}
• Secrets/Credentials      : {len(secrets)}
• API Endpoints Found      : {len(endpoints)}
• Subdomain Takeover Risks : {len(takeover_risks)}
• Vulnerabilities (Nuclei) : {len(vuln_findings)} total — {len(vuln_critical)} critical, {len(vuln_high)} high, {len(vuln_medium)} medium

═══ TECHNOLOGIES DETECTED ═══
{techs_sample}

═══ OPEN PORTS (sample of up to 25) ═══
{ports_sample}

═══ SECRETS FOUND (sample of up to 20) ═══
{secrets_sample}

═══ TAKEOVER RISKS ═══
{takeovers_sample}

═══ NUCLEI VULNERABILITY FINDINGS (sample of up to 20) ═══
{vulns_sample}

═══ API ENDPOINTS (sample of up to 25) ═══
{endpoints_sample}

─────────────────────────────────────────────────────────────────────────────
Based on this reconnaissance data, provide a professional security assessment:

## 🎯 Top 5 Most Critical Findings
Identify and explain the 5 most interesting, dangerous, or exploitable findings. Be specific about why each is significant.

## 🔬 Recommended Next Steps
Provide 6–8 specific, actionable next steps for further testing and exploitation. Include tool suggestions where relevant (e.g., nuclei, ghauri, sqlmap, burpsuite).

## ⚠️ Severity Assessment
Overall severity rating: **Critical / High / Medium / Low / Informational**
Justification: (2–3 sentences explaining the rating based on the findings)

## 📋 Quick Summary
A 3–4 sentence executive summary suitable for a bug bounty report introduction.

Format everything in clean Markdown. Be direct and technical — this is for a security professional.
"""


def run(scan_id: str, db=None) -> None:
    """
    Stage 8: AI Summary Generation.
    Calls OpenRouter API with recon data to generate a professional security assessment.
    If no API key is configured, stores a placeholder explaining how to enable it.
    Can be called directly (from regenerate endpoint) or as part of the pipeline.
    """
    close_db = db is None
    if close_db:
        db = SessionLocal()

    try:
        api_key = os.getenv('OPENROUTER_API_KEY', '').strip()

        if not api_key:
            logger.warning(f'[{scan_id}] No OPENROUTER_API_KEY configured — storing placeholder')
            _store_summary(db, scan_id, (
                '## AI Summary Unavailable\n\n'
                'No `OPENROUTER_API_KEY` has been configured.\n\n'
                'To enable AI-powered analysis:\n'
                '1. Get a free API key at [openrouter.ai](https://openrouter.ai)\n'
                '2. Add `OPENROUTER_API_KEY=your_key_here` to your `.env` file\n'
                '3. Restart the backend, then click **Regenerate Summary** on this scan\n\n'
                '*The AI summary uses GPT-4o mini via OpenRouter — '
                'cost is typically under $0.01 per scan.*'
            ))
            return

        # Load all scan data
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            logger.error(f'[{scan_id}] Scan not found for AI summary')
            return

        subdomains = db.query(Subdomain).filter(Subdomain.scan_id == scan_id).all()
        secrets = db.query(Secret).filter(Secret.scan_id == scan_id).all()
        endpoints = db.query(Endpoint).filter(Endpoint.scan_id == scan_id).all()
        takeover_risks = db.query(TakeoverRisk).filter(TakeoverRisk.scan_id == scan_id).all()
        vuln_findings = db.query(VulnerabilityFinding).filter(VulnerabilityFinding.scan_id == scan_id).all()

        prompt = build_prompt(scan, subdomains, secrets, endpoints, takeover_risks, vuln_findings)

        logger.info(f'[{scan_id}] Sending prompt to OpenRouter ({DEFAULT_MODEL})')

        response = requests.post(
            OPENROUTER_API_URL,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://github.com/Ayaan1911/Argus-Sentinel',
                'X-Title': 'Argus-Sentinel Recon Tool',
            },
            json={
                'model': DEFAULT_MODEL,
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': MAX_TOKENS,
                'temperature': 0.3,
            },
            timeout=API_TIMEOUT,
        )

        if response.status_code == 200:
            result = response.json()
            summary_text = result['choices'][0]['message']['content']
            logger.info(f'[{scan_id}] AI summary received ({len(summary_text)} chars)')
        else:
            error_body = response.text[:300]
            summary_text = (
                f'## AI Summary Failed\n\n'
                f'OpenRouter API returned HTTP {response.status_code}.\n\n'
                f'```\n{error_body}\n```\n\n'
                f'Please check your API key and try regenerating the summary.'
            )
            logger.error(f'[{scan_id}] OpenRouter error {response.status_code}: {error_body}')

        _store_summary(db, scan_id, summary_text)

    except requests.Timeout:
        logger.error(f'[{scan_id}] OpenRouter request timed out')
        _store_summary(db, scan_id, '## AI Summary Failed\n\nThe request to OpenRouter timed out. Please try regenerating the summary.')
    except Exception as e:
        logger.error(f'[{scan_id}] AI summary error: {e}', exc_info=True)
    finally:
        if close_db:
            db.close()


def _store_summary(db, scan_id: str, text: str) -> None:
    """Upsert an AISummary record."""
    try:
        existing = db.query(AISummary).filter(AISummary.scan_id == scan_id).first()
        if existing:
            existing.summary_text = text
            existing.created_at = datetime.utcnow()
        else:
            db.add(AISummary(
                scan_id=scan_id,
                summary_text=text,
                created_at=datetime.utcnow(),
            ))
        db.commit()
    except Exception as e:
        logger.error(f'[{scan_id}] Failed to store AI summary: {e}')
        db.rollback()


# Alias used by the regenerate-summary API endpoint
run_ai_summary = run
