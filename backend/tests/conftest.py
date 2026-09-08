"""
Shared fixtures for DB-backed tests (test_routes.py, test_scan_tasks.py).

Spins up a throwaway Postgres container via `docker run` (not docker-compose,
so it never touches the project's real db/redis services or any other
container on the machine) and repoints the app's already-imported async/sync
engines at it. app.config.Settings() and the module-level engines in
app.database / app.tasks.scan_tasks are bound to DATABASE_URL at *import*
time, so instead of fighting test-file import order, the `postgres_engines`
fixture patches those already-created engine objects in place — every
consumer (app.database.get_db, app.tasks.scan_tasks.run_scan) looks up
`engine`/`SessionLocal`/`AsyncSessionLocal` as a module-level name at call
time, so the patch takes effect regardless of when a test module imported them.

If Docker isn't available, every test that depends (directly or transitively)
on `postgres_engines` is skipped — the existing pure-Python unit tests
(test_reasoning.py, test_correlation.py, etc.) are untouched by any of this
and never trigger it, since they don't request these fixtures.
"""
import asyncio
import os
import socket
import subprocess
import time

import pytest
from sqlalchemy import create_engine as create_sync_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

os.environ.setdefault("API_KEY", "test-api-key")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

TEST_CONTAINER_NAME = "argus-test-postgres"
TEST_API_KEY = os.environ["API_KEY"]


def _docker_available() -> bool:
    try:
        subprocess.run(["docker", "info"], capture_output=True, timeout=10, check=True)
        return True
    except Exception:
        return False


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def postgres_engines():
    if not _docker_available():
        pytest.skip("Docker is not available in this environment — skipping DB-backed tests")

    port = _find_free_port()
    subprocess.run(["docker", "rm", "-f", TEST_CONTAINER_NAME], capture_output=True)
    subprocess.run(
        [
            "docker", "run", "-d", "--rm",
            "--name", TEST_CONTAINER_NAME,
            "-e", "POSTGRES_USER=test",
            "-e", "POSTGRES_PASSWORD=test",
            "-e", "POSTGRES_DB=argus_test",
            "-p", f"{port}:5432",
            "postgres:15-alpine",
        ],
        check=True, capture_output=True,
    )

    try:
        ready = False
        for _ in range(60):
            result = subprocess.run(
                ["docker", "exec", TEST_CONTAINER_NAME, "pg_isready", "-U", "test"],
                capture_output=True,
            )
            if result.returncode == 0:
                ready = True
                break
            time.sleep(0.5)
        if not ready:
            pytest.skip("Postgres test container did not become ready in time")

        async_url = f"postgresql+asyncpg://test:test@localhost:{port}/argus_test"
        sync_url = f"postgresql://test:test@localhost:{port}/argus_test"

        import app.database as database_module
        import app.tasks.scan_tasks as scan_tasks_module
        from app.models.base import Base

        # NullPool: every operation gets a fresh connection instead of reusing
        # a pooled one across the different event loops each asyncio.run()
        # call (and each TestClient request) creates — asyncpg connections
        # aren't safe to reuse across event loops.
        async_engine = create_async_engine(async_url, poolclass=NullPool)
        database_module.engine = async_engine
        database_module.AsyncSessionLocal = sessionmaker(
            async_engine, class_=AsyncSession, expire_on_commit=False
        )

        sync_engine = create_sync_engine(sync_url)
        scan_tasks_module.engine = sync_engine
        scan_tasks_module.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

        async def _create_all():
            async with async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        asyncio.run(_create_all())

        yield {"async_engine": async_engine, "sync_engine": sync_engine}
    finally:
        subprocess.run(["docker", "rm", "-f", TEST_CONTAINER_NAME], capture_output=True)


@pytest.fixture()
def clean_db(postgres_engines):
    """Truncates scans/findings before each test so DB-backed tests don't see
    rows left behind by a previous test."""
    from app.models.finding import Finding
    from app.models.scan import Scan

    async def _truncate():
        async with postgres_engines["async_engine"].begin() as conn:
            await conn.execute(Finding.__table__.delete())
            await conn.execute(Scan.__table__.delete())

    asyncio.run(_truncate())
    yield postgres_engines


@pytest.fixture()
def client(clean_db):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.rate_limit import limiter

    # All route tests share one API key, so without this every test after the
    # 5th POST /scans/ in the whole session would spuriously 429.
    limiter.reset()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers():
    return {"x-api-key": TEST_API_KEY}
