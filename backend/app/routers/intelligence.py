from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any

from app.intelligence.loader import get_intelligence_loader

router = APIRouter()

@router.get("/services")
async def list_services():
    loader = get_intelligence_loader()
    return loader._cache.get("services", {})

@router.get("/services/{name}")
async def get_service(name: str):
    loader = get_intelligence_loader()
    entry = loader.get_service(name)
    if not entry:
        raise HTTPException(status_code=404, detail="Service not found")
    return entry

@router.get("/technologies")
async def list_technologies():
    loader = get_intelligence_loader()
    return loader._cache.get("technologies", {})

@router.get("/technologies/{name}")
async def get_technology(name: str):
    loader = get_intelligence_loader()
    entry = loader.get_technology(name)
    if not entry:
        raise HTTPException(status_code=404, detail="Technology not found")
    return entry

@router.get("/vulnerabilities")
async def list_vulnerabilities():
    loader = get_intelligence_loader()
    return loader._cache.get("vulnerabilities", {})

@router.get("/vulnerabilities/{name}")
async def get_vulnerability(name: str):
    loader = get_intelligence_loader()
    entry = loader.get_vulnerability(name)
    if not entry:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    return entry

@router.get("/search")
async def search_intelligence(q: str = Query(..., min_length=1)):
    loader = get_intelligence_loader()
    results = []
    query = q.lower()
    
    for category in ["services", "technologies", "vulnerabilities"]:
        items = loader._cache.get(category, {})
        for name, data in items.items():
            if query in name.lower() or query in str(data.get("description", "")).lower() or query in str(data.get("service", "")).lower() or query in str(data.get("technology", "")).lower():
                results.append({
                    "type": category.rstrip("ies").rstrip("s") if category != "technologies" else "technology",
                    "entry": data
                })
    return results
