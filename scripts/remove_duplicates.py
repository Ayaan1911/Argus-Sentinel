# One-time cleanup tool for duplicate Scan rows created before the target
# normalization + recent-completed-scan reuse fix in routers/scans.py
# create_scan(). New scans no longer produce these duplicates — this script
# is kept only to clean up rows from before that fix.
import asyncio
import os
import sys

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.models.scan import Scan
from app.config import settings

async def main():
    print("Connecting to DB...")
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Fetch all scans
        stmt = select(Scan).order_by(Scan.created_at.desc()).options(selectinload(Scan.findings))
        result = await session.execute(stmt)
        all_scans = result.scalars().all()
        
        target_groups = {}
        for s in all_scans:
            if s.target not in target_groups:
                target_groups[s.target] = []
            target_groups[s.target].append(s)

        total_removed = 0
        for target, scans in target_groups.items():
            if len(scans) > 1:
                # Keep the one with the most findings or the most recent completed one
                scans.sort(key=lambda x: (len(x.findings), 1 if x.status == 'completed' else 0, x.created_at), reverse=True)
                keep_scan = scans[0]
                scans_to_delete = scans[1:]
                
                print(f"Target {target}: Keeping {keep_scan.id} (findings: {len(keep_scan.findings)}), deleting {len(scans_to_delete)} duplicates")
                
                for scan_to_delete in scans_to_delete:
                    await session.delete(scan_to_delete)
                    total_removed += 1
        
        await session.commit()
        print(f"Total duplicate scans removed: {total_removed}")

if __name__ == "__main__":
    asyncio.run(main())
