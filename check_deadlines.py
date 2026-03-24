"""
check_deadlines.py — SyrHousing Deadline Notifier

Scans the grants table for grants closing within 30 days, logs them to
Logs/notifications.log, and fires a desktop toast notification via plyer.

Intended to run as a Windows Scheduled Task (daily).

Setup (Windows Task Scheduler):
  Program : pythonw.exe   (or full path to venv python)
  Args    : C:\\SyrHousing\\check_deadlines.py
  Start in: C:\\SyrHousing
"""
import os
import sys
import sqlite3
import logging
import json
import traceback
from datetime import datetime, timedelta, date
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "backend" / "syrhousing.db"
LOG_DIR = BASE_DIR / "Logs"
LOG_PATH = LOG_DIR / "notifications.log"

LOG_DIR.mkdir(parents=True, exist_ok=True)

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("check_deadlines")

# ── Configuration ──────────────────────────────────────────────────────────
WARN_DAYS = 30          # flag grants closing within this many days
URGENT_DAYS = 7         # highlight as urgent below this many days


def _connect_db() -> sqlite3.Connection:
    """Open a read-only connection to the SQLite database."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _parse_deadline(deadline_str: str | None) -> date | None:
    """
    Attempt to parse a deadline string into a date object.
    Returns None for 'rolling', 'annual', None, or unparseable values.
    """
    if not deadline_str or deadline_str.lower() in ("rolling", "annual", "n/a", ""):
        return None
    # Try common ISO/US date formats
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(deadline_str.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _fetch_closing_grants(conn: sqlite3.Connection, today: date, warn_days: int) -> list[dict]:
    """Return grants whose parsed deadline falls within warn_days from today."""
    try:
        cursor = conn.execute(
            "SELECT id, grant_name, source, deadline, status, amount_max, "
            "       application_url, agency_phone "
            "FROM grants "
            "WHERE status != 'closed'"
        )
        rows = cursor.fetchall()
    except sqlite3.OperationalError as exc:
        logger.error("Could not query grants table: %s", exc)
        return []

    closing = []
    for row in rows:
        dl = _parse_deadline(row["deadline"])
        if dl is None:
            continue
        days_left = (dl - today).days
        if 0 <= days_left <= warn_days:
            closing.append({
                "id": row["id"],
                "grant_name": row["grant_name"],
                "source": row["source"],
                "deadline": str(dl),
                "days_left": days_left,
                "status": row["status"],
                "amount_max": row["amount_max"],
                "application_url": row["application_url"],
                "agency_phone": row["agency_phone"],
            })

    closing.sort(key=lambda x: x["days_left"])
    return closing


def _send_toast(title: str, message: str) -> None:
    """
    Send a Windows desktop notification via plyer.
    Fails silently if plyer is not installed or running headless.
    """
    try:
        from plyer import notification
        notification.notify(
            title=title,
            message=message,
            app_name="SyrHousing",
            timeout=12,
        )
        logger.debug("Toast sent: %s", title)
    except ImportError:
        logger.warning(
            "plyer not installed — desktop notifications disabled. "
            "Install with: pip install plyer"
        )
    except Exception as exc:
        logger.warning("Toast notification failed: %s", exc)


def main() -> int:
    today = date.today()
    logger.info("=" * 60)
    logger.info("SyrHousing deadline check  |  %s", today.isoformat())
    logger.info("=" * 60)

    # ── Connect ────────────────────────────────────────────────────────────
    try:
        conn = _connect_db()
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        logger.error("Make sure the backend has been started at least once to create the DB.")
        return 1
    except Exception:
        logger.exception("Unexpected error connecting to database")
        return 1

    # ── Query ──────────────────────────────────────────────────────────────
    try:
        closing = _fetch_closing_grants(conn, today, WARN_DAYS)
    except Exception:
        logger.exception("Failed to fetch closing grants")
        conn.close()
        return 1
    finally:
        conn.close()

    if not closing:
        logger.info("No grants closing within %d days. Nothing to report.", WARN_DAYS)
        return 0

    # ── Log each grant ─────────────────────────────────────────────────────
    urgent = [g for g in closing if g["days_left"] <= URGENT_DAYS]
    soon = [g for g in closing if g["days_left"] > URGENT_DAYS]

    for g in closing:
        urgency = "URGENT" if g["days_left"] <= URGENT_DAYS else "WARN "
        logger.warning(
            "[%s] %s — deadline %s (%d days left)  |  source: %s  |  URL: %s",
            urgency,
            g["grant_name"],
            g["deadline"],
            g["days_left"],
            g["source"] or "N/A",
            g["application_url"] or "N/A",
        )

    # ── Desktop notifications ──────────────────────────────────────────────
    if urgent:
        names = ", ".join(g["grant_name"][:40] for g in urgent[:3])
        suffix = f" (+{len(urgent) - 3} more)" if len(urgent) > 3 else ""
        _send_toast(
            title=f"⚠ URGENT: {len(urgent)} Grant Deadline(s) This Week",
            message=f"{names}{suffix}\nAct now — deadline within {URGENT_DAYS} days!",
        )

    if soon:
        names = ", ".join(g["grant_name"][:40] for g in soon[:2])
        suffix = f" (+{len(soon) - 2} more)" if len(soon) > 2 else ""
        _send_toast(
            title=f"📅 {len(soon)} Grant(s) Closing Within {WARN_DAYS} Days",
            message=f"{names}{suffix}",
        )

    # ── Summary ────────────────────────────────────────────────────────────
    logger.info(
        "Summary: %d grant(s) closing within %d days (%d urgent, %d soon)",
        len(closing), WARN_DAYS, len(urgent), len(soon),
    )

    # Write a machine-readable JSON summary alongside the log
    summary_path = LOG_DIR / "deadline_summary.json"
    try:
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "checked_at": datetime.now().isoformat(),
                    "warn_days": WARN_DAYS,
                    "urgent_count": len(urgent),
                    "soon_count": len(soon),
                    "grants": closing,
                },
                f,
                indent=2,
            )
        logger.info("JSON summary written to %s", summary_path)
    except Exception:
        logger.exception("Failed to write JSON summary")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        logger.critical("Unhandled exception in check_deadlines:\n%s", traceback.format_exc())
        sys.exit(2)
