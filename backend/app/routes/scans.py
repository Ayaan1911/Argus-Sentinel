import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from ..database import get_db
from ..models import Scan, Subdomain, Secret, Endpoint, TakeoverRisk, AISummary
from ..schemas import ScanSchema, ScanListSchema, envelope
from tasks.celery_app import celery_app
from tasks import pipeline

router = APIRouter()


@router.post('/scan')
def create_scan(payload: dict, db: Session = Depends(get_db)):
    """
    Initiate a new reconnaissance scan for a given domain.
    Accepts: {"domain": "example.com"}
    """
    domain = payload.get('domain', '').strip().lower()
    if not domain:
        raise HTTPException(status_code=400, detail='Domain is required')

    # Strip protocol prefix and path if provided
    domain = domain.replace('https://', '').replace('http://', '').split('/')[0].strip()

    if not domain:
        raise HTTPException(status_code=400, detail='Invalid domain format')

    scan = Scan(domain=domain, status='queued')
    db.add(scan)
    db.commit()
    db.refresh(scan)

    # Queue Celery task
    pipeline.run_scan.delay(scan.id)

    return envelope({
        'scan_id': scan.id,
        'domain': scan.domain,
        'status': scan.status,
        'created_at': scan.created_at.isoformat(),
    })


@router.get('/scans')
def list_scans(db: Session = Depends(get_db)):
    """
    List all scans with basic stats (subdomain count).
    """
    scans = db.query(Scan).order_by(Scan.created_at.desc()).all()
    result = []
    for s in scans:
        count = db.query(func.count(Subdomain.id)).filter(Subdomain.scan_id == s.id).scalar()
        result.append({
            'id': s.id,
            'domain': s.domain,
            'status': s.status,
            'created_at': s.created_at.isoformat() if s.created_at else None,
            'completed_at': s.completed_at.isoformat() if s.completed_at else None,
            'current_stage': s.current_stage,
            'subdomain_count': count or 0,
        })
    return envelope(result)


@router.get('/scan/{scan_id}')
def get_scan(scan_id: str, db: Session = Depends(get_db)):
    """
    Get full scan details including all findings.
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail='Scan not found')
    data = ScanSchema.from_orm(scan)
    return envelope(data.model_dump())


@router.delete('/scan/{scan_id}')
def delete_scan(scan_id: str, db: Session = Depends(get_db)):
    """
    Delete a scan and all associated data (cascading).
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail='Scan not found')
    db.delete(scan)
    db.commit()
    return envelope({'deleted': scan_id})


@router.get('/scan/{scan_id}/export')
def export_scan(scan_id: str, db: Session = Depends(get_db)):
    """
    Export complete scan data as JSON (same as get_scan, for explicit export use cases).
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail='Scan not found')
    data = ScanSchema.from_orm(scan)
    return envelope(data.model_dump())


@router.post('/scan/{scan_id}/regenerate-summary')
def regenerate_summary(scan_id: str, db: Session = Depends(get_db)):
    """
    Trigger AI summary regeneration for an existing scan.
    Useful when API key is added after the scan was run.
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail='Scan not found')

    from tasks.modules.ai_summary import run_ai_summary
    run_ai_summary(scan_id)
    db.refresh(scan)

    # Return updated summary if available
    summary = db.query(AISummary).filter(AISummary.scan_id == scan_id).first()
    return envelope({
        'regenerated': True,
        'summary': summary.summary_text if summary else None,
    })


@router.get('/scan/{scan_id}/status')
def get_scan_status(scan_id: str, db: Session = Depends(get_db)):
    """
    Lightweight status poll endpoint for frontend progress tracking.
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail='Scan not found')
    return envelope({
        'id': scan.id,
        'status': scan.status,
        'current_stage': scan.current_stage,
        'completed_at': scan.completed_at.isoformat() if scan.completed_at else None,
        'error_message': scan.error_message,
    })
