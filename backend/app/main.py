from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(
    title="Argus Sentinel API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api/v1")
app.include_router(api_router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "Argus Sentinel"}
