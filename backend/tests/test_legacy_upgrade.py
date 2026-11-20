"""A database created before Alembic had tables but no version marker."""
import uuid
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text


def test_known_legacy_schema_can_be_stamped_and_upgraded_without_losing_rows(clean_db, monkeypatch):
    engine = clean_db["sync_engine"]
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "alembic"))
    monkeypatch.setenv(
        "DATABASE_URL",
        engine.url.render_as_string(hide_password=False).replace("postgresql://", "postgresql+asyncpg://"),
    )
    scan_id, finding_id = str(uuid.uuid4()), str(uuid.uuid4())

    command.downgrade(config, "base")
    try:
        # The first revision reproduces the original manually created schema.
        command.upgrade(config, "5da69c924778")
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM alembic_version"))
            conn.execute(text(
                "INSERT INTO scans (id, target, status, audience) "
                "VALUES (:id, 'juice-shop', 'completed', 'student')"
            ), {"id": scan_id})
            conn.execute(text(
                "INSERT INTO findings (id, scan_id, type, title, severity, confidence, risk_score, "
                "final_risk_score, correlation_modifier) "
                "VALUES (:id, :scan_id, 'port', 'Port 3000/tcp', 'low', 0.9, 3.0, 7.9, 0.0)"
            ), {"id": finding_id, "scan_id": scan_id})

        assert "stage_status" not in {c["name"] for c in inspect(engine).get_columns("scans")}
        command.stamp(config, "5da69c924778")
        command.upgrade(config, "head")

        with engine.begin() as conn:
            scan = conn.execute(text(
                "SELECT target, status, stage_status, is_demo FROM scans WHERE id = :id"
            ), {"id": scan_id}).one()
            finding = conn.execute(text(
                "SELECT title, severity, final_risk_score FROM findings WHERE id = :id"
            ), {"id": finding_id}).one()
            version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert scan == ("juice-shop", "completed", {}, False)
        assert finding == ("Port 3000/tcp", "high", 7.9)
        assert version == "84b71c2e0f66"
    finally:
        command.upgrade(config, "head")
