"""
Port of scan_grants.py — same logic: fetch, clean, hash, detect status, check changes.
Reads/writes DB instead of JSON/CSV files.
Removes winotify dependency.
Fix: check "open" keywords before "closed" (fixes scan_grants.py:101-107 bug).
"""

import re
import hashlib
from datetime import datetime, timezone
from typing import List, Tuple, Optional

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from ..models.watchlist import WatchlistEntry
from ..models.scan import ScanResult, ScanState

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SyrHousingScanner/2.0"
TIMEOUT = 25

RELEVANT_KEYWORDS = [
    "apply", "applications open", "accepting applications",
    "deadline", "due by", "funding available",
    "application period", "now accepting",
    ".pdf",
]


def clean_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


def fetch_text(url: str) -> Tuple[str, str]:
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
        r.raise_for_status()
        return clean_text(r.text), ""
    except Exception as e:
        return "", f"{type(e).__name__}: {e}"


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def split_keywords(s: Optional[str]) -> List[str]:
    if not s:
        return []
    return [k.strip().lower() for k in s.split(";") if k.strip()]


def detect_status(text: str, open_k: List[str], closed_k: List[str]) -> str:
    """Fixed: check open keywords first, then closed."""
    t = text.lower()
    if any(k in t for k in open_k):
        return "open/unknown"
    if any(k in t for k in closed_k):
        return "closed"
    return "unknown"


def is_relevant_change(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in RELEVANT_KEYWORDS)


def run_scan(db: Session) -> dict:
    entries = db.query(WatchlistEntry).filter(WatchlistEntry.is_active == True).all()
    ts = datetime.now(timezone.utc)

    results: List[ScanResult] = []
    changes = 0
    errors = 0

    for entry in entries:
        open_k = split_keywords(entry.open_keywords)
        closed_k = split_keywords(entry.closed_keywords)

        text, err = fetch_text(entry.url)

        if err:
            status = "error"
            h = ""
            changed = False
            note = f"Fetch failed: {err}"
            errors += 1
        else:
            status = detect_status(text, open_k, closed_k)
            h = hash_text(text)

            prev = db.query(ScanState).filter(ScanState.program_key == entry.program_key).first()
            prev_hash = prev.content_hash if prev else None
            prev_status = prev.status if prev else None

            changed = (prev_hash is not None and prev_hash != h) or (prev_status is not None and prev_status != status)
            note = "OK"

            if changed:
                changes += 1

            # Upsert scan_state
            if prev:
                prev.name = entry.name
                prev.url = entry.url
                prev.status = status
                prev.content_hash = h
                prev.last_checked = ts
            else:
                db.add(ScanState(
                    program_key=entry.program_key,
                    name=entry.name,
                    url=entry.url,
                    status=status,
                    content_hash=h,
                    last_checked=ts,
                ))

        result = ScanResult(
            timestamp=ts,
            watchlist_program_key=entry.program_key,
            name=entry.name,
            url=entry.url,
            status=status,
            changed=changed,
            notes=note,
        )
        db.add(result)
        results.append(result)

    db.commit()
    for r in results:
        db.refresh(r)

    return {
        "message": f"Scan complete: {len(entries)} programs checked",
        "scanned": len(entries),
        "changes": changes,
        "errors": errors,
        "results": results,
    }


def build_latest_report(db: Session) -> str:
    """Build a text report from the most recent scan batch."""
    latest = db.query(ScanResult).order_by(ScanResult.timestamp.desc()).first()
    if not latest:
        return "No scan results found."

    batch_ts = latest.timestamp
    batch = db.query(ScanResult).filter(ScanResult.timestamp == batch_ts).all()

    lines = [
        "SYRACUSE HOUSING GRANT SCAN REPORT",
        "=" * 46,
        f"Scan Time: {batch_ts.isoformat(timespec='seconds')}",
        "",
        "SUMMARY",
        "-" * 14,
    ]

    counts = {"open/unknown": 0, "closed": 0, "unknown": 0, "error": 0}
    change_items = []
    error_items = []

    for r in batch:
        counts[r.status] = counts.get(r.status, 0) + 1
        if r.changed:
            change_items.append(r)
        if r.status == "error":
            error_items.append(r)

    lines.append(f"Total programs: {len(batch)}")
    for k, v in counts.items():
        lines.append(f"{k}: {v}")
    lines.append("")

    lines.append("CHANGES")
    lines.append("-" * 30)
    if not change_items:
        lines.append("No changes detected.")
    else:
        for r in change_items:
            lines.append(f"- {r.name}")
            lines.append(f"  Status: {r.status}")
            lines.append(f"  Link: {r.url}")
            lines.append("")

    lines.append("")
    lines.append("ERRORS / BROKEN LINKS")
    lines.append("-" * 20)
    if not error_items:
        lines.append("No errors.")
    else:
        for r in error_items:
            lines.append(f"- {r.name}")
            lines.append(f"  Link: {r.url}")
            lines.append(f"  Error: {r.notes}")
            lines.append("")

    return "\n".join(lines)
