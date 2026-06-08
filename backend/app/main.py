import time
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
from redis.asyncio import Redis

from app.config import settings
from app.database import init_db, get_db
from app.tasks import celery_app

from app.routers import scans, findings, intelligence
from app.intelligence.loader import get_intelligence_loader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # Initialize intelligence loader cache
    get_intelligence_loader()
    yield

app = FastAPI(
    title="Argus Sentinel API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time_ms = (time.time() - start_time) * 1000
    logger.info(
        f"{request.method} {request.url.path} "
        f"status_code={response.status_code} "
        f"response_time_ms={process_time_ms:.2f}"
    )
    return response

@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "not_found", "message": str(exc.detail)}
    )

from fastapi.exceptions import RequestValidationError
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": "validation_error", "detail": exc.errors()}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error")
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "message": "An unexpected error occurred"}
    )

app.include_router(scans.router, prefix="/api/v1/scans", tags=["scans"])
app.include_router(findings.router, prefix="/api/v1/findings", tags=["findings"])
app.include_router(intelligence.router, prefix="/api/v1/intelligence", tags=["intelligence"])

@app.get("/health")
async def health_check():
    # Check DB
    db_status = "disconnected"
    try:
        from app.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"DB health check failed: {e}")

    # Check Redis
    redis_status = "disconnected"
    try:
        r = Redis.from_url(settings.REDIS_URL)
        await r.ping()
        redis_status = "connected"
        await r.close()
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")

    # Intelligence info
    loader = get_intelligence_loader()
    
    return {
        "status": "ok",
        "service": "Argus Sentinel",
        "version": "1.0.0",
        "database": db_status,
        "redis": redis_status,
        "intelligence_library": {
            "services": len(loader.data.get("services", {})),
            "technologies": len(loader.data.get("technologies", {})),
            "vulnerabilities": len(loader.data.get("vulnerabilities", {}))
        }
    }
