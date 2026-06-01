import logging
from datetime import datetime
from .celery_app import celery_app
from app.database import SessionLocal
from app.models import Scan

logger = logging.getLogger(__name__)

STAGES = [
    ('subdomain_enum',    'Subdomain Enumeration'),
    ('live_host_check',   'Live Host Detection'),
    ('screenshot_capture','Screenshots'),
    ('port_scan',         'Port Scanning'),
    ('js_extractor',      'JS File Extraction'),
    ('secret_detector',   'Secret Detection'),
    ('endpoint_miner',    'Endpoint Mining'),
    ('takeover_check',    'Takeover Check'),
    ('nuclei_scan',       'Nuclei Scan'),
    ('ai_summary',        'AI Summary'),
]


@celery_app.task(bind=True, name='tasks.pipeline.run_scan')
def run_scan(self, scan_id: str):
    """
    Main pipeline task. Executes each recon stage sequentially.
    Failures in individual stages are caught and logged but do not abort the pipeline.
    """
    db = SessionLocal()
    try:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            logger.error(f'Scan {scan_id} not found')
            return

        scan.status = 'running'
        db.commit()

        # Import all stage modules
        from tasks.modules import (
            subdomain_enum,
            live_host_check,
            screenshot_capture,
            port_scan,
            js_extractor,
            secret_detector,
            endpoint_miner,
            takeover_check,
            nuclei_scan,
            ai_summary,
        )

        module_map = {
            'subdomain_enum':     subdomain_enum.run,
            'live_host_check':    live_host_check.run,
            'screenshot_capture': screenshot_capture.run,
            'port_scan':          port_scan.run,
            'js_extractor':       js_extractor.run,
            'secret_detector':    secret_detector.run,
            'endpoint_miner':     endpoint_miner.run,
            'takeover_check':     takeover_check.run,
            'nuclei_scan':        nuclei_scan.run,
            'ai_summary':         ai_summary.run,
        }

        for stage_key, stage_name in STAGES:
            # Re-fetch scan to get latest state and avoid stale reads
            scan = db.query(Scan).filter(Scan.id == scan_id).first()
            if not scan:
                logger.error(f'Scan {scan_id} disappeared mid-pipeline')
                return

            scan.current_stage = stage_name
            db.commit()
            logger.info(f'[{scan_id}] Starting stage: {stage_name}')

            try:
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(module_map[stage_key], scan_id, db)
                    future.result(timeout=300)  # 5 minutes max per stage
                logger.info(f'[{scan_id}] Completed stage: {stage_name}')
            except concurrent.futures.TimeoutError:
                logger.warning(f'[{scan_id}] Stage "{stage_name}" timed out after 5 minutes. Continuing to next stage.')
                continue
            except Exception as e:
                logger.error(
                    f'[{scan_id}] Stage "{stage_name}" failed: {e}',
                    exc_info=True,
                )
                # Continue to next stage — partial results are better than none
                continue

        # Mark scan complete
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if scan:
            scan.status = 'complete'
            scan.completed_at = datetime.utcnow()
            scan.current_stage = 'Complete'
            db.commit()
            logger.info(f'[{scan_id}] Scan complete')

    except Exception as e:
        logger.error(f'[{scan_id}] Pipeline fatal error: {e}', exc_info=True)
        try:
            scan = db.query(Scan).filter(Scan.id == scan_id).first()
            if scan:
                scan.status = 'failed'
                scan.error_message = str(e)
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
