#!/usr/bin/env python3
"""
Standalone script to run grant discovery manually or via cron.

Usage:
    python -m backend.scripts.run_discovery [--sources rss_feed,grants_gov_api] [--no-notify]

Options:
    --sources: Comma-separated list of sources to check (default: all)
    --no-notify: Skip sending email notification to admins

Examples:
    # Run with all sources
    python -m backend.scripts.run_discovery

    # Run with specific sources
    python -m backend.scripts.run_discovery --sources rss_feed

    # Run without notification
    python -m backend.scripts.run_discovery --no-notify

Cron setup (run daily at 2 AM):
    0 2 * * * cd /path/to/SyrHousing && /usr/bin/python3 -m backend.scripts.run_discovery >> /var/log/syrhousing/discovery.log 2>&1
"""

import sys
import argparse
import logging
from datetime import datetime

# Setup path for imports
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database import SessionLocal
from backend.services.discovery.discovery_service import run_discovery
from backend.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('discovery_runs.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)


def main():
    """
    Main entry point for standalone discovery script.
    """
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Run automated grant discovery',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--sources',
        type=str,
        help='Comma-separated list of sources (e.g., rss_feed,grants_gov_api)',
        default=None
    )
    parser.add_argument(
        '--no-notify',
        action='store_true',
        help='Skip sending admin notification email'
    )

    args = parser.parse_args()

    # Parse sources
    if args.sources:
        sources = [s.strip() for s in args.sources.split(',')]
    else:
        # Use config default
        sources_str = settings.DISCOVERY_SOURCES.strip()
        sources = [s.strip() for s in sources_str.split(',')] if sources_str else None

    send_notification = not args.no_notify

    logger.info("=" * 70)
    logger.info("STARTING GRANT DISCOVERY RUN")
    logger.info("=" * 70)
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Sources: {sources or 'all available'}")
    logger.info(f"Send notification: {send_notification}")
    logger.info("")

    # Create database session
    db = SessionLocal()

    try:
        # Run discovery
        run = run_discovery(
            db=db,
            sources=sources,
            send_notification=send_notification
        )

        # Log results
        logger.info("=" * 70)
        logger.info("DISCOVERY RUN COMPLETED")
        logger.info("=" * 70)
        logger.info(f"Run ID: {run.id}")
        logger.info(f"Status: {run.status}")
        logger.info(f"Sources checked: {run.sources_checked}")
        logger.info(f"Grants discovered: {run.grants_discovered}")
        logger.info(f"Duplicates found: {run.duplicates_found}")
        logger.info(f"Errors: {run.errors}")
        logger.info(f"Started at: {run.started_at}")
        logger.info(f"Completed at: {run.completed_at}")
        logger.info("")

        if run.errors > 0:
            logger.warning(f"Discovery completed with {run.errors} error(s)")
            logger.warning(f"Check error log for details: {run.error_log}")
            sys.exit(1)
        else:
            logger.info("✅ Discovery completed successfully!")
            sys.exit(0)

    except Exception as e:
        logger.error(f"❌ Discovery failed: {e}", exc_info=True)
        sys.exit(2)

    finally:
        db.close()


if __name__ == "__main__":
    main()
