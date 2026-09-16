from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, noload
from sqlalchemy import func
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone

from redis.asyncio import Redis

from app.config import settings
from app.database import get_db
from app.models.scan import Scan
from app.models.finding import Finding
from app.rate_limit import limiter
from app.schemas.scan import ScanCreate, ScanRead
from app.schemas.finding import FindingRead
from app.scanners.utils import normalize_target
from app.engines.diff import diff_findings
from app.tasks.scan_tasks import run_scan

router = APIRouter()


def _scan_rate_limit() -> str:
    # Tighter in demo mode — this endpoint is open to anonymous public
    # traffic there, not just people who've set up their own API key.
    return "3/minute" if settings.DEMO_MODE else "5/minute"


async def _enforce_demo_scan_ceiling() -> None:
    """A rolling daily cap on total scans created in demo mode, independent
    of the per-IP rate limit above — protects against runaway compute cost
    from many distinct visitors each staying under the per-IP limit."""
    if not settings.DEMO_MODE:
        return

    redis = Redis.from_url(settings.REDIS_URL)
    try:
        day_key = f"demo:scan_count:{datetime.now(timezone.utc):%Y-%m-%d}"
        count = await redis.incr(day_key)
        if count == 1:
            await redis.expire(day_key, 60 * 60 * 26)  # a little over a day, covers TZ edges
        if count > settings.DEMO_SCAN_DAILY_LIMIT:
            raise HTTPException(
                status_code=429,
                detail=(
                    f"The public demo's daily scan limit ({settings.DEMO_SCAN_DAILY_LIMIT}/day) "
                    "has been reached. Self-host Argus Sentinel for unlimited scanning."
                ),
            )
    finally:
        await redis.aclose()

# How long a completed scan of the same (normalized) target is considered
# fresh enough to hand back instead of launching a new one.
RESCAN_WINDOW = timedelta(hours=24)

@router.get("/dashboard-stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    # Get all findings
    stmt = select(Finding)
    result = await db.execute(stmt)
    findings = result.scalars().all()
    
    # Severity Distribution
    by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    by_type = {"vulnerability": 0, "port": 0, "subdomain": 0, "technology": 0}
    
    for f in findings:
        sev = f.severity.lower() if f.severity else "info"
        if sev == "informational": sev = "info"
        if sev in by_severity:
            by_severity[sev] += 1
            
        t = f.type.lower() if f.type else "other"
        if t in by_type:
            by_type[t] += 1
        else:
            by_type[t] = 1
            
    # Scans over time (last 14 days)
    # Must be timezone-aware: Scan.created_at is DateTime(timezone=True), and
    # asyncpg interprets a *naive* datetime bound as a query parameter using
    # the server's local system timezone rather than UTC — a naive
    # datetime.utcnow() here would silently shift this cutoff on any host
    # whose local timezone isn't UTC.
    fourteen_days_ago = datetime.now(timezone.utc) - timedelta(days=14)
    stmt_scans = select(Scan.created_at).where(Scan.created_at >= fourteen_days_ago)
    res_scans = await db.execute(stmt_scans)
    scan_dates = [row[0] for row in res_scans.all()]
    
    scans_by_date = {}
    for i in range(14):
        d = (datetime.utcnow() - timedelta(days=13-i)).strftime("%Y-%m-%d")
        scans_by_date[d] = 0
        
    for d in scan_dates:
        date_str = d.strftime("%Y-%m-%d")
        if date_str in scans_by_date:
            scans_by_date[date_str] += 1
            
    scans_over_time = [{"date": k, "count": v} for k, v in scans_by_date.items()]
    
    return {
        "severity_distribution": by_severity,
        "type_breakdown": by_type,
        "scans_over_time": scans_over_time,
        "total_findings": len(findings)
    }


@router.post("/", response_model=ScanRead)
@limiter.limit(_scan_rate_limit)
async def create_scan(request: Request, scan_in: ScanCreate, db: AsyncSession = Depends(get_db)):
    # scan_in.target is already normalized by the ScanCreate validator, so this
    # is a plain equality check — no need to re-normalize here.

    # Check for an already in-flight scan of this target to avoid duplicating
    # active work, regardless of force_rescan.
    stmt = select(Scan).where(Scan.target == scan_in.target, Scan.status.in_(["pending", "running"]))
    result = await db.execute(stmt)
    existing_scan = result.scalars().first()

    if existing_scan:
        stmt = select(Scan).options(selectinload(Scan.findings)).where(Scan.id == existing_scan.id)
        res = await db.execute(stmt)
        return res.scalar_one()

    # Reuse a recent completed scan of the same target instead of silently
    # creating a duplicate — unless the caller explicitly wants a fresh one.
    if not scan_in.force_rescan:
        # Timezone-aware for the same reason as fourteen_days_ago above —
        # this is compared directly against Scan.created_at.
        recent_cutoff = datetime.now(timezone.utc) - RESCAN_WINDOW
        stmt = (
            select(Scan)
            .where(
                Scan.target == scan_in.target,
                Scan.status == "completed",
                Scan.created_at >= recent_cutoff,
            )
            .order_by(Scan.created_at.desc())
        )
        result = await db.execute(stmt)
        recent_completed = result.scalars().first()

        if recent_completed:
            stmt = select(Scan).options(selectinload(Scan.findings)).where(Scan.id == recent_completed.id)
            res = await db.execute(stmt)
            return res.scalar_one()

    # Only counts against the daily demo ceiling once we're actually about to
    # dispatch new scanner work — reused/deduped scans above don't cost anything.
    await _enforce_demo_scan_ceiling()

    db_scan = Scan(
        target=scan_in.target,
        audience=scan_in.audience,
        status="pending",
        is_demo=settings.DEMO_MODE,
    )
    db.add(db_scan)
    await db.commit()
    
    # Trigger celery task
    run_scan.delay(str(db_scan.id), db_scan.target, db_scan.audience)
    
    # Re-fetch with selectinload to prevent Greenlet async load errors during serialization
    stmt = select(Scan).options(selectinload(Scan.findings)).where(Scan.id == db_scan.id)
    result = await db.execute(stmt)
    loaded_scan = result.scalar_one()
    
    return loaded_scan

@router.get("/", response_model=List[Dict[str, Any]])
async def list_scans(db: AsyncSession = Depends(get_db)):
    stmt = select(Scan).options(selectinload(Scan.findings)).order_by(Scan.created_at.desc())
    result = await db.execute(stmt)
    scans = result.scalars().all()
    
    out = []
    for s in scans:
        out.append({
            "id": str(s.id),
            "target": s.target,
            "status": s.status,
            "audience": s.audience,
            "created_at": s.created_at,
            "finding_count": len(s.findings)
        })
    return out

@router.get("/target/{normalized_target}/history")
async def get_scan_history_for_target(normalized_target: str, db: AsyncSession = Depends(get_db)):
    # Normalize defensively even though callers are expected to already pass
    # a normalized value — same reasoning as every other target entry point.
    target = normalize_target(normalized_target)

    stmt = (
        select(Scan)
        .options(noload(Scan.findings))
        .where(Scan.target == target, Scan.status == "completed")
        .order_by(Scan.created_at.desc())
    )
    result = await db.execute(stmt)
    scans = result.scalars().all()

    if not scans:
        return []

    # One grouped query for all finding counts instead of one query per scan.
    scan_ids = [s.id for s in scans]
    count_stmt = (
        select(Finding.scan_id, func.count(Finding.id))
        .where(Finding.scan_id.in_(scan_ids))
        .group_by(Finding.scan_id)
    )
    count_result = await db.execute(count_stmt)
    counts_by_scan_id = {row[0]: row[1] for row in count_result.all()}

    return [
        {
            "id": str(s.id),
            "created_at": s.created_at,
            "status": s.status,
            "finding_count": counts_by_scan_id.get(s.id, 0),
        }
        for s in scans
    ]


@router.get("/{scan_id}", response_model=ScanRead)
async def get_scan(scan_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Scan).options(selectinload(Scan.findings)).where(Scan.id == scan_id)
    result = await db.execute(stmt)
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan

@router.get("/{scan_id}/status")
async def get_scan_status(scan_id: str, db: AsyncSession = Depends(get_db)):
    # Deliberately lightweight: no findings are loaded, just a count, so this
    # is cheap enough to poll every few seconds for the life of a scan.
    stmt = select(Scan).where(Scan.id == scan_id)
    result = await db.execute(stmt)
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    count_stmt = select(func.count(Finding.id)).where(Finding.scan_id == scan_id)
    count_result = await db.execute(count_stmt)
    finding_count = count_result.scalar_one()

    return {
        "scan_id": str(scan.id),
        "target": scan.target,
        "audience": scan.audience,
        "status": scan.status,
        "stage_status": scan.stage_status or {},
        "finding_count": finding_count
    }

@router.get("/{scan_id}/diff")
async def get_scan_diff(
    scan_id: str,
    compare_to: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Scan).where(Scan.id == scan_id)
    result = await db.execute(stmt)
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=400, detail="Scan not found")
    if scan.status != "completed":
        raise HTTPException(status_code=400, detail=f"Scan is not completed (status: {scan.status})")

    target = normalize_target(scan.target)

    if compare_to:
        stmt = select(Scan).where(Scan.id == compare_to)
        result = await db.execute(stmt)
        compare_scan = result.scalar_one_or_none()
        if not compare_scan:
            raise HTTPException(status_code=400, detail="Comparison scan not found")
        if normalize_target(compare_scan.target) != target:
            raise HTTPException(status_code=400, detail="Scans belong to different targets")
        if compare_scan.status != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Comparison scan is not completed (status: {compare_scan.status})",
            )
    else:
        # "prior" means chronologically before scan_id — not just "some other
        # scan, preferring the newest overall" — otherwise diffing an old
        # scan with no compare_to would pick a scan from after it in time.
        stmt = (
            select(Scan)
            .where(
                Scan.target == target,
                Scan.status == "completed",
                Scan.id != scan_id,
                Scan.created_at < scan.created_at,
            )
            .order_by(Scan.created_at.desc())
        )
        result = await db.execute(stmt)
        compare_scan = result.scalars().first()
        if not compare_scan:
            raise HTTPException(status_code=404, detail="No prior completed scan of this target to compare against")

    cur_stmt = select(Finding).where(Finding.scan_id == scan.id)
    cur_result = await db.execute(cur_stmt)
    current_findings = [FindingRead.model_validate(f).model_dump(mode="json") for f in cur_result.scalars().all()]

    prev_stmt = select(Finding).where(Finding.scan_id == compare_scan.id)
    prev_result = await db.execute(prev_stmt)
    previous_findings = [FindingRead.model_validate(f).model_dump(mode="json") for f in prev_result.scalars().all()]

    diff = diff_findings(current_findings, previous_findings)

    return {
        "scan_id": str(scan.id),
        "compared_to_scan_id": str(compare_scan.id),
        "target": target,
        "scan_date": scan.created_at,
        "compared_scan_date": compare_scan.created_at,
        "summary": diff["summary"],
        "new_findings": diff["new_findings"],
        "resolved_findings": diff["resolved_findings"],
        "changed_findings": diff["changed_findings"],
        "unchanged_findings": diff["unchanged_findings"],
    }


@router.delete("/{scan_id}")
async def delete_scan(scan_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Scan).options(noload(Scan.findings)).where(Scan.id == scan_id)
    result = await db.execute(stmt)
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    await db.delete(scan)
    await db.commit()
    return {"deleted": True}
