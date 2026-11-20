# Upgrading an older Argus database

The normal startup runs `alembic upgrade head`. A known older installation may instead contain manually created `scans` and `findings` tables with **no Alembic version marker**. The first migration now creates those tables, so running it directly against such a database fails with `relation "scans" already exists`.

The procedure below is for the original table layout represented by [`5da69c924778_initial_tables.py`](../backend/alembic/versions/5da69c924778_initial_tables.py). It was rehearsed against a disposable PostgreSQL database containing a scan and finding; the rows survived the upgrade and the final-severity backfill ran. It has **not** been run on an unknown production volume.

1. Stop API and worker traffic. Back up the database, copy the dump off the host, and verify it with `pg_restore -l` or a test restore. Do not run a schema migration without a usable backup. For the standard Compose database, PowerShell commands are:

   ```powershell
   docker compose stop api worker
   docker compose exec -T db pg_dump -U postgres -d argus -Fc -f /tmp/argus-before-upgrade.dump
   docker compose exec -T db pg_restore -l /tmp/argus-before-upgrade.dump
   $dbContainer = docker compose ps -q db
   docker cp "${dbContainer}:/tmp/argus-before-upgrade.dump" ..\argus-before-upgrade.dump
   ```
2. Inspect the database before stamping anything:

   ```powershell
   docker compose exec -T db psql -U postgres -d argus -c "SELECT to_regclass('public.alembic_version')"
   docker compose exec -T db psql -U postgres -d argus -c "SELECT table_name, column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema='public' AND table_name IN ('scans','findings') ORDER BY table_name, ordinal_position"
   docker compose exec -T db psql -U postgres -d argus -c "SELECT indexname, tablename FROM pg_indexes WHERE schemaname='public' AND tablename IN ('scans','findings') ORDER BY tablename, indexname"
   ```

3. If `alembic_version` contains a revision, use the normal `alembic upgrade head`; **do not stamp again**. If it is absent or empty, compare every column, nullability, primary key, foreign key, and index against the initial migration. The original `scans` table has `id`, `target`, `status`, `audience`, `created_at`, and `updated_at`, with no `stage_status` or `is_demo`. If anything differs, stop and review the schema; stamping the wrong revision skips needed changes.
4. Only after the original layout is confirmed, stamp the existing tables as the first revision, then apply later revisions:

   ```powershell
   docker compose run --rm --no-deps api alembic stamp 5da69c924778
   docker compose run --rm --no-deps api alembic upgrade head
   docker compose exec -T db psql -U postgres -d argus -c "SELECT version_num FROM alembic_version"
   ```

5. Confirm the version is `84b71c2e0f66`, the scan and finding counts match the backup, and sample findings have severity consistent with `final_risk_score`. Then restart the API and worker.

The test for this path is [`test_legacy_upgrade.py`](../backend/tests/test_legacy_upgrade.py). It does not justify stamping a database with extra columns or a different schema. Keep the application stopped until such a database is reviewed and migrated separately.
