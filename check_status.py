#!/usr/bin/env python3
from backend.database import SessionLocal
from backend.models.discovered_grant import DiscoveryRun, DiscoveredGrant
from backend.models.program import Program
from sqlalchemy import func

db = SessionLocal()

# Count discovery runs
total_runs = db.query(func.count(DiscoveryRun.id)).scalar()
print(f'Discovery Runs: {total_runs}')

# Get latest run
latest = db.query(DiscoveryRun).order_by(DiscoveryRun.started_at.desc()).first()
if latest:
    print(f'\nLatest Run:')
    print(f'  - ID: {latest.id[:8]}...')
    print(f'  - Status: {latest.status}')
    print(f'  - Started: {latest.started_at}')
    print(f'  - Sources: {latest.sources_checked}')
    print(f'  - Discovered: {latest.grants_discovered}')
    print(f'  - Duplicates: {latest.duplicates_found}')

# Count discovered grants by status
pending = db.query(func.count(DiscoveredGrant.id)).filter(DiscoveredGrant.review_status == 'pending').scalar()
approved = db.query(func.count(DiscoveredGrant.id)).filter(DiscoveredGrant.review_status == 'approved').scalar()
rejected = db.query(func.count(DiscoveredGrant.id)).filter(DiscoveredGrant.review_status == 'rejected').scalar()
duplicates = db.query(func.count(DiscoveredGrant.id)).filter(DiscoveredGrant.review_status == 'duplicate').scalar()

print(f'\nDiscovered Grants:')
print(f'  - Pending Review: {pending}')
print(f'  - Approved: {approved}')
print(f'  - Rejected: {rejected}')
print(f'  - Duplicates: {duplicates}')

# Count active programs
active_programs = db.query(func.count(Program.id)).filter(Program.is_active == True).scalar()
print(f'\nActive Programs: {active_programs}')

db.close()
