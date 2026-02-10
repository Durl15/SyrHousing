"""
One-shot migration from CSV/JSON legacy files to SQLite database.

Usage:
    cd backend
    python -m scripts.seed_data
"""

import csv
import json
import os
import re
import sys
from datetime import datetime, timezone

# Add parent to path so we can import backend modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine, SessionLocal, Base
from backend.models import Program, UserProfile, WatchlistEntry, ScanResult, ScanState

BASE_DIR = r"C:\SyrHousing"
GRANTS_CSV = os.path.join(BASE_DIR, "Data", "grants_db.csv")
PROFILE_JSON = os.path.join(BASE_DIR, "Data", "my_home_profile.json")
WATCHLIST_CSV = os.path.join(BASE_DIR, "Data", "program_watchlist.csv")
SCAN_STATE_JSON = os.path.join(BASE_DIR, "Data", "scan_state.json")
SCAN_LOG_CSV = os.path.join(BASE_DIR, "Logs", "scan_log.csv")


def slugify(name: str) -> str:
    """Generate a unique program_key slug from the program name."""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = s.strip("_")
    return s[:120]


def strip_quad_quotes(val: str) -> str:
    """Strip quadruple-quote corruption from CSV values."""
    if val.startswith('"""') and val.endswith('"""'):
        return val[3:-3]
    if val.startswith('""') and val.endswith('""'):
        return val[2:-2]
    return val


def clean_field(val: str) -> str:
    """Clean a CSV field of corruption."""
    v = strip_quad_quotes(val.strip())
    v = v.replace('""""', '').replace('"""', '').replace('""', '"')
    # Strip stray leading/trailing double-quotes left by CSV parser
    v = v.strip('"').strip()
    return v


def empty_to_none(val: str):
    return val if val else None


def seed_programs(db):
    print("Seeding programs from grants_db.csv ...")
    with open(GRANTS_CSV, newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        seen_keys = set()
        count = 0
        for row in reader:
            name = clean_field(row.get("Name", ""))
            if not name:
                continue

            base_key = slugify(name)
            key = base_key
            suffix = 2
            while key in seen_keys:
                key = f"{base_key}_{suffix}"
                suffix += 1
            seen_keys.add(key)

            repair_tags = clean_field(row.get("RepairTags", ""))
            # Normalize: strip trailing quotes/junk from tags
            repair_tags = re.sub(r'["\s]+$', '', repair_tags)
            repair_tags = re.sub(r'^["\s]+', '', repair_tags)

            try:
                pr = float(clean_field(row.get("PriorityRank", "0")) or "0")
            except ValueError:
                pr = 0.0

            p = Program(
                program_key=key,
                name=name,
                jurisdiction=empty_to_none(clean_field(row.get("Jurisdiction", ""))),
                program_type=empty_to_none(clean_field(row.get("ProgramType", ""))),
                menu_category=clean_field(row.get("MenuCategory", "")) or "GENERAL",
                repair_tags=empty_to_none(repair_tags),
                priority_rank=pr,
                max_benefit=empty_to_none(clean_field(row.get("MaxBenefit", ""))),
                status_or_deadline=empty_to_none(clean_field(row.get("StatusOrDeadline", ""))),
                agency=empty_to_none(clean_field(row.get("Agency", ""))),
                phone=empty_to_none(clean_field(row.get("Phone", ""))),
                email=empty_to_none(clean_field(row.get("Email", ""))),
                website=empty_to_none(clean_field(row.get("Website", ""))),
                eligibility_summary=empty_to_none(clean_field(row.get("EligibilitySummary", ""))),
                income_guidance=empty_to_none(clean_field(row.get("IncomeGuidance", ""))),
                docs_checklist=empty_to_none(clean_field(row.get("DocsChecklist", ""))),
                is_active=True,
            )
            db.add(p)
            count += 1
    db.commit()
    print(f"  -> {count} programs imported")


def seed_profile(db):
    print("Seeding user profile from my_home_profile.json ...")
    with open(PROFILE_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    # The legacy file is {tag: severity_score} — convert to new format
    repair_severity = {}
    repair_needs = []
    for key, val in data.items():
        if isinstance(val, (int, float)) and val > 0:
            repair_needs.append(key)
            repair_severity[key] = int(val)

    profile = UserProfile(
        profile_name="default",
        city="Syracuse",
        county="Onondaga",
        is_senior=True,
        is_fixed_income=True,
        repair_needs=repair_needs,
        repair_severity=repair_severity,
    )
    db.add(profile)
    db.commit()
    print(f"  -> Default profile created with {len(repair_needs)} repair needs")


# Key remapping: old watchlist keys -> new deduplicated keys
KEY_REMAP = {
    "hhq_hub": "hhq_homeowner",
    "restore": "hcr_restore",
    "access_to_home": "hcr_access_to_home",
    "peace_weatherization": "peace_energyhousing",
    "hud_title1": "hud_title",
}


def seed_watchlist(db):
    print("Seeding watchlist from program_watchlist.csv ...")
    with open(WATCHLIST_CSV, newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        seen_urls = {}  # url -> WatchlistEntry (for dedup)
        count = 0

        for row in reader:
            pid = (row.get("ProgramId") or "").strip().strip('"')
            name = (row.get("Name") or "").strip().strip('"')
            url = (row.get("URL") or "").strip().strip('"')
            open_kw = (row.get("OpenKeywords") or "").strip().strip('"')
            closed_kw = (row.get("ClosedKeywords") or "").strip().strip('"')
            notes = (row.get("Notes") or "").strip().strip('"')

            if not pid or not url:
                continue

            # Remap old keys to new keys
            new_key = KEY_REMAP.get(pid, pid)

            if url in seen_urls:
                # Merge keywords into existing entry
                existing = seen_urls[url]
                existing_open = set(k.strip() for k in (existing.open_keywords or "").split(";") if k.strip())
                new_open = set(k.strip() for k in open_kw.split(";") if k.strip())
                merged_open = ";".join(sorted(existing_open | new_open))

                existing_closed = set(k.strip() for k in (existing.closed_keywords or "").split(";") if k.strip())
                new_closed = set(k.strip() for k in closed_kw.split(";") if k.strip())
                merged_closed = ";".join(sorted(existing_closed | new_closed))

                existing.open_keywords = merged_open
                existing.closed_keywords = merged_closed
                if notes and notes not in (existing.notes or ""):
                    existing.notes = f"{existing.notes or ''}; {notes}".strip("; ")
                continue

            # Check if key already exists in DB (from an earlier row)
            existing_by_key = db.query(WatchlistEntry).filter(WatchlistEntry.program_key == new_key).first()
            if existing_by_key:
                # Merge into existing
                existing_open = set(k.strip() for k in (existing_by_key.open_keywords or "").split(";") if k.strip())
                new_open = set(k.strip() for k in open_kw.split(";") if k.strip())
                existing_by_key.open_keywords = ";".join(sorted(existing_open | new_open))

                existing_closed = set(k.strip() for k in (existing_by_key.closed_keywords or "").split(";") if k.strip())
                new_closed = set(k.strip() for k in closed_kw.split(";") if k.strip())
                existing_by_key.closed_keywords = ";".join(sorted(existing_closed | new_closed))

                seen_urls[url] = existing_by_key
                continue

            entry = WatchlistEntry(
                program_key=new_key,
                name=name,
                url=url,
                open_keywords=open_kw or None,
                closed_keywords=closed_kw or None,
                notes=notes or None,
                is_active=True,
            )
            db.add(entry)
            db.flush()  # so subsequent dedup checks work
            seen_urls[url] = entry
            count += 1

    db.commit()
    print(f"  -> {count} watchlist entries imported (deduplicated)")


def seed_scan_state(db):
    print("Seeding scan state from scan_state.json ...")
    with open(SCAN_STATE_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    seen = {}  # new_key -> ScanState
    for old_key, info in data.items():
        new_key = KEY_REMAP.get(old_key, old_key)

        last_checked = None
        if info.get("last_checked"):
            try:
                last_checked = datetime.fromisoformat(info["last_checked"])
            except Exception:
                pass

        if new_key in seen:
            # Keep the one with the most recent last_checked
            existing_lc = seen[new_key].last_checked
            if last_checked and (not existing_lc or last_checked > existing_lc):
                seen[new_key].status = info.get("status", "unknown")
                seen[new_key].content_hash = info.get("hash")
                seen[new_key].last_checked = last_checked
            continue

        state = ScanState(
            program_key=new_key,
            name=info.get("name", ""),
            url=info.get("url", ""),
            status=info.get("status", "unknown"),
            content_hash=info.get("hash"),
            last_checked=last_checked,
        )
        db.add(state)
        seen[new_key] = state

    db.commit()
    print(f"  -> {len(seen)} scan states imported")


def seed_scan_log(db):
    print("Seeding scan log from scan_log.csv ...")
    with open(SCAN_LOG_CSV, newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            old_key = (row.get("program_id") or "").strip()
            new_key = KEY_REMAP.get(old_key, old_key)

            ts_str = (row.get("timestamp") or "").strip()
            try:
                ts = datetime.fromisoformat(ts_str)
            except Exception:
                continue

            changed_str = (row.get("changed") or "").strip().upper()
            changed = changed_str == "YES"

            result = ScanResult(
                timestamp=ts,
                watchlist_program_key=new_key,
                name=(row.get("name") or "").strip(),
                url=(row.get("url") or "").strip(),
                status=(row.get("status") or "unknown").strip(),
                changed=changed,
                notes=(row.get("notes") or "").strip() or None,
            )
            db.add(result)
            count += 1

    db.commit()
    print(f"  -> {count} scan log entries imported")


def main():
    print("Creating database tables ...")
    Base.metadata.create_all(bind=engine)
    print("  -> Tables created\n")

    db = SessionLocal()
    try:
        # Check if already seeded
        existing = db.query(Program).count()
        if existing > 0:
            print(f"Database already has {existing} programs. Skipping seed.")
            print("To re-seed, delete syrhousing.db and run again.")
            return

        seed_programs(db)
        seed_profile(db)
        seed_watchlist(db)
        seed_scan_state(db)
        seed_scan_log(db)

        print("\nSeed complete!")
        print(f"  Programs:   {db.query(Program).count()}")
        print(f"  Profiles:   {db.query(UserProfile).count()}")
        print(f"  Watchlist:  {db.query(WatchlistEntry).count()}")
        print(f"  ScanStates: {db.query(ScanState).count()}")
        print(f"  ScanLog:    {db.query(ScanResult).count()}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
