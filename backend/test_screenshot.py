import os
from sqlalchemy.orm import Session
from app.database import engine
from tasks.modules.screenshot_capture import run

scan_id = 'c55ecb3d-2a6a-4c9a-ab84-7fbfd3a2b7bb'

print(f"Testing screenshot capture for scan {scan_id}...")
with Session(engine) as db:
    run(scan_id, db)
    print("Done!")
