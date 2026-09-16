import asyncio
import logging
import urllib.parse
from datetime import datetime, timedelta, timezone

from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.scan import Scan
from app.models.finding import Finding

from app.scanners import subfinder, httpx, nmap, nuclei
from app.scanners.processor import FindingProcessor
from app.engines import correlation_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup sync database for celery
sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
engine = create_engine(sync_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

celery_app = Celery("argus", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

# ponytail: embedded beat (see docker-compose.yml's worker `-B` flag) runs in
# the same process as the worker, which double-schedules this task if the
# worker is ever scaled to multiple replicas — move to a dedicated `beat`
# service first if that happens. Hourly is plenty of margin for a 24h window.
celery_app.conf.beat_schedule = {
    "prune-demo-scans-hourly": {
        "task": "prune_demo_scans",
        "schedule": 3600.0,
    },
}

DEMO_SCAN_RETENTION = timedelta(hours=24)


def _live_hostnames(httpx_results: list[dict]) -> set:
    hosts = set()
    for f in httpx_results:
        url = f.get("raw_data", {}).get("url", "")
        host = urllib.parse.urlparse(url).hostname
        if host:
            hosts.add(host)
    return hosts


def _live_urls_by_host(httpx_results: list[dict]) -> dict:
    """host -> the full URL (with real port) httpx confirmed live on it, so
    downstream stages hit the actual working endpoint instead of re-guessing
    default ports 80/443."""
    urls = {}
    for f in httpx_results:
        url = f.get("raw_data", {}).get("url", "")
        host = urllib.parse.urlparse(url).hostname
        if host:
            urls.setdefault(host, url)
    return urls


async def _run_pipeline(target: str):
    """Sequential recon pipeline: subfinder discovers subdomains -> httpx
    confirms which of (target + discovered subdomains) are actually live ->
    nmap/nuclei only scan the target plus confirmed-live discovered
    subdomains, not the full unfiltered subdomain list."""
    stage_status = {}

    subfinder_results, subfinder_status = await subfinder.run(target)
    stage_status["subfinder"] = subfinder_status

    discovered = [
        f["raw_data"]["host"] for f in subfinder_results
        if f.get("raw_data", {}).get("host")
    ]

    httpx_results, httpx_status = await httpx.run([target] + discovered)
    stage_status["httpx"] = httpx_status

    live_hosts = _live_hostnames(httpx_results)
    live_discovered = [h for h in discovered if h in live_hosts]
    # The original target is always in scope regardless of its own httpx
    # result — only the *discovered* subdomains get filtered by liveness.
    scan_targets = [target] + live_discovered

    nmap_results, nmap_status = await nmap.run(scan_targets)
    stage_status["nmap"] = nmap_status

    live_urls = _live_urls_by_host(httpx_results)
    nuclei_targets = [live_urls.get(t, t) for t in scan_targets]
    nuclei_results, nuclei_status = await nuclei.run(nuclei_targets)
    stage_status["nuclei"] = nuclei_status

    all_findings = subfinder_results + httpx_results + nmap_results + nuclei_results
    return all_findings, stage_status


@celery_app.task(name="run_scan")
def run_scan(scan_id: str, target: str, audience: str):
    db = SessionLocal()
    try:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            logger.error(f"Scan {scan_id} not found")
            return

        scan.status = "running"
        db.commit()

        logger.info(f"Running scan pipeline for {target}")
        raw_findings, stage_status = asyncio.run(_run_pipeline(target))

        scan.stage_status = stage_status
        db.commit()

        logger.info(f"Total raw findings: {len(raw_findings)}")

        processor = FindingProcessor()
        db_findings = []

        for raw_f in raw_findings:
            processed = processor.process(raw_f, scan_id, audience)
            db_finding = Finding(**processed)
            db_findings.append(db_finding)

        if db_findings:
            db.add_all(db_findings)
            db.flush()

            # Convert to dicts for correlation engine
            findings_dicts = []
            for f in db_findings:
                findings_dicts.append({
                    "id": str(f.id),
                    "type": f.type,
                    "title": f.title,
                    "raw_data": f.raw_data,
                    "risk_score": f.risk_score,
                    "severity": f.severity,
                    "reasoning_breakdown": f.reasoning_breakdown,
                    "final_risk_score": f.final_risk_score,
                    "correlation_modifier": f.correlation_modifier
                })

            correlation_result = correlation_engine.correlate(findings_dicts)
            updated_dicts = correlation_engine.apply_modifiers(findings_dicts, correlation_result)
            # Zero correlations is often the correct answer (this scan's findings
            # genuinely don't match any rule), but logged explicitly so it's never
            # silently indistinguishable from a rule/data-shape mismatch bug.
            if correlation_result.correlations_found:
                rule_names = [c.rule_name for c in correlation_result.correlations_found]
                logger.info(f"Correlation engine: {len(rule_names)} rule(s) matched: {rule_names}")
            else:
                logger.info("Correlation engine: no rules matched this scan's findings — all correlation_modifier values are 0.0")

            # Update DB with final scores
            for ud in updated_dicts:
                f_obj = next((x for x in db_findings if str(x.id) == ud["id"]), None)
                if f_obj:
                    f_obj.final_risk_score = ud["final_risk_score"]
                    f_obj.correlation_modifier = ud["correlation_modifier"]
                    f_obj.reasoning_breakdown = ud["reasoning_breakdown"]

        scan.status = "completed"
        db.commit()
        logger.info(f"Scan {scan_id} completed successfully")

    except Exception as e:
        logger.exception(f"Scan {scan_id} failed: {e}")
        db.rollback()
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if scan:
            scan.status = "failed"
            db.commit()
    finally:
        db.close()


@celery_app.task(name="prune_demo_scans")
def prune_demo_scans():
    """Deletes demo-mode scan records (and their findings) once older than
    DEMO_SCAN_RETENTION. Only ever touches rows with is_demo=True — a
    self-hosted deployment's real scan history is never marked is_demo (see
    routers/scans.py::create_scan), so running this unconditionally is a
    harmless no-op there rather than something that needs its own on/off
    switch."""
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - DEMO_SCAN_RETENTION
        expired_ids = [
            row[0] for row in
            db.query(Scan.id).filter(Scan.is_demo.is_(True), Scan.created_at < cutoff).all()
        ]
        if not expired_ids:
            logger.info("prune_demo_scans: nothing expired")
            return {"pruned": 0}

        # No DB-level ON DELETE CASCADE on findings.scan_id, so findings are
        # deleted explicitly first, in the same transaction as the scans.
        db.query(Finding).filter(Finding.scan_id.in_(expired_ids)).delete(synchronize_session=False)
        db.query(Scan).filter(Scan.id.in_(expired_ids)).delete(synchronize_session=False)
        db.commit()
        logger.info(f"prune_demo_scans: pruned {len(expired_ids)} expired demo scan(s)")
        return {"pruned": len(expired_ids)}
    finally:
        db.close()
