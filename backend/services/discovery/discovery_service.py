"""
Main discovery service orchestrator.
Coordinates grant discovery across multiple sources.
"""

import uuid
import json
import logging
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from ...models.discovered_grant import DiscoveredGrant, DiscoveryRun
from ...models.program import Program
from .sources.rss_feed import RSSFeedAdapter
from .extractors.data_extractor import extract_grant_data
from .deduplicator import find_duplicates
from .validator import calculate_confidence

logger = logging.getLogger(__name__)


def get_source_adapters(sources: Optional[List[str]] = None):
    """
    Get configured source adapters.

    Args:
        sources: List of source types to use, or None for all available

    Returns:
        List of source adapter instances
    """
    # Available sources
    available = {
        "rss_feed": RSSFeedAdapter(),
        # "grants_gov_api": GrantsGovAPIAdapter(),  # Phase 3
        # "web_scrape": WebScraperAdapter(),         # Phase 3
    }

    if sources is None:
        # Use all available sources
        return list(available.values())

    # Filter requested sources
    adapters = []
    for source in sources:
        if source in available:
            adapters.append(available[source])
        else:
            logger.warning(f"Unknown source type: {source}")

    return adapters


def run_discovery(
    db: Session,
    sources: Optional[List[str]] = None,
    send_notification: bool = True
) -> DiscoveryRun:
    """
    Run grant discovery from specified sources.

    This is the main entry point for grant discovery. It:
    1. Creates a DiscoveryRun record to track execution
    2. Fetches grants from configured sources
    3. Extracts and normalizes data
    4. Checks for duplicates against existing programs
    5. Calculates confidence scores
    6. Saves discovered grants to database
    7. Sends admin notification (if enabled)

    Args:
        db: Database session
        sources: List of source types to use (None = all)
        send_notification: Whether to send admin notification (default True)

    Returns:
        DiscoveryRun: Completed discovery run with statistics

    Example:
        >>> from backend.database import SessionLocal
        >>> db = SessionLocal()
        >>> run = run_discovery(db, sources=["rss_feed"])
        >>> print(f"Discovered {run.grants_discovered} grants, {run.duplicates_found} duplicates")
    """
    # Create discovery run record
    run = DiscoveryRun(
        id=str(uuid.uuid4()),
        started_at=datetime.now(timezone.utc),
        status="running",
        sources_checked=0,
        grants_discovered=0,
        duplicates_found=0,
        errors=0,
        error_log=json.dumps([])
    )
    db.add(run)
    db.commit()

    logger.info(f"Starting discovery run {run.id}")

    # Track errors
    errors = []

    # Get source adapters
    try:
        adapters = get_source_adapters(sources)
        logger.info(f"Using {len(adapters)} source adapter(s)")
    except Exception as e:
        logger.error(f"Failed to initialize source adapters: {e}")
        run.status = "failed"
        run.completed_at = datetime.now(timezone.utc)
        run.errors += 1
        run.error_log = json.dumps([{"error": str(e), "stage": "initialization"}])
        db.commit()
        return run

    # Get existing programs for deduplication
    existing_programs = db.query(Program).filter(Program.is_active == True).all()
    logger.info(f"Loaded {len(existing_programs)} existing programs for deduplication")

    # Process each source
    for adapter in adapters:
        run.sources_checked += 1
        source_type = adapter.get_source_type()

        try:
            logger.info(f"Fetching grants from {source_type}...")
            raw_grants = adapter.fetch_grants()
            logger.info(f"Fetched {len(raw_grants)} grants from {source_type}")

            for raw_grant in raw_grants:
                try:
                    # Extract structured data
                    extracted = extract_grant_data(raw_grant, source_type)

                    # Skip if no name
                    if not extracted.get("name"):
                        logger.warning(f"Skipping grant with no name from {source_type}")
                        continue

                    # Check for duplicates
                    duplicate_program, similarity = find_duplicates(extracted, existing_programs)

                    if duplicate_program and similarity >= 0.85:
                        # Duplicate found
                        run.duplicates_found += 1
                        logger.info(
                            f"Duplicate detected: '{extracted['name']}' matches "
                            f"'{duplicate_program.name}' ({similarity:.0%} similar)"
                        )

                        # Still save as discovered grant but mark as duplicate
                        discovered = DiscoveredGrant(
                            id=str(uuid.uuid4()),
                            source_type=source_type,
                            source_url=extracted.get("source_url", ""),
                            source_id=extracted.get("source_id"),
                            name=extracted["name"],
                            jurisdiction=extracted.get("jurisdiction"),
                            program_type=extracted.get("program_type"),
                            max_benefit=extracted.get("max_benefit"),
                            status_or_deadline=extracted.get("status_or_deadline"),
                            agency=extracted.get("agency"),
                            phone=extracted.get("phone"),
                            email=extracted.get("email"),
                            website=extracted.get("website"),
                            eligibility_summary=extracted.get("eligibility_summary"),
                            docs_checklist=extracted.get("docs_checklist"),
                            discovered_at=datetime.now(timezone.utc),
                            confidence_score=calculate_confidence(extracted, source_type),
                            raw_data=extracted.get("raw_data"),
                            review_status="duplicate",
                            matched_program_key=duplicate_program.program_key,
                            similarity_score=similarity,
                        )
                        db.add(discovered)
                        continue

                    # Not a duplicate - calculate confidence
                    confidence = calculate_confidence(extracted, source_type)

                    # Save as new discovered grant
                    discovered = DiscoveredGrant(
                        id=str(uuid.uuid4()),
                        source_type=source_type,
                        source_url=extracted.get("source_url", ""),
                        source_id=extracted.get("source_id"),
                        name=extracted["name"],
                        jurisdiction=extracted.get("jurisdiction"),
                        program_type=extracted.get("program_type"),
                        max_benefit=extracted.get("max_benefit"),
                        status_or_deadline=extracted.get("status_or_deadline"),
                        agency=extracted.get("agency"),
                        phone=extracted.get("phone"),
                        email=extracted.get("email"),
                        website=extracted.get("website"),
                        eligibility_summary=extracted.get("eligibility_summary"),
                        docs_checklist=extracted.get("docs_checklist"),
                        discovered_at=datetime.now(timezone.utc),
                        confidence_score=confidence,
                        raw_data=extracted.get("raw_data"),
                        review_status="pending",
                    )
                    db.add(discovered)
                    run.grants_discovered += 1

                    logger.info(
                        f"New grant discovered: '{extracted['name']}' "
                        f"(confidence: {confidence:.0%})"
                    )

                except Exception as e:
                    run.errors += 1
                    error_msg = f"Error processing grant from {source_type}: {str(e)}"
                    logger.error(error_msg)
                    errors.append({"source": source_type, "error": str(e), "grant": str(raw_grant)[:200]})

            # Commit after each source
            db.commit()

        except Exception as e:
            run.errors += 1
            error_msg = f"Error fetching from {source_type}: {str(e)}"
            logger.error(error_msg)
            errors.append({"source": source_type, "error": str(e), "stage": "fetch"})

    # Update run status
    run.completed_at = datetime.now(timezone.utc)
    run.status = "completed" if run.errors == 0 else "completed_with_errors"
    run.error_log = json.dumps(errors)
    db.commit()

    logger.info(
        f"Discovery run {run.id} completed: "
        f"{run.grants_discovered} discovered, "
        f"{run.duplicates_found} duplicates, "
        f"{run.errors} errors"
    )

    # Send notification to admins
    if send_notification and run.grants_discovered > 0:
        try:
            from ..notifications import send_discovery_notification
            send_discovery_notification(db, run)
        except Exception as e:
            logger.error(f"Failed to send discovery notification: {e}")

    return run


def get_high_confidence_grants(db: Session, min_confidence: float = 0.8) -> List[DiscoveredGrant]:
    """
    Get discovered grants with high confidence scores.

    Args:
        db: Database session
        min_confidence: Minimum confidence score (default 0.8)

    Returns:
        List of high-confidence discovered grants pending review
    """
    return db.query(DiscoveredGrant).filter(
        DiscoveredGrant.review_status == "pending",
        DiscoveredGrant.confidence_score >= min_confidence
    ).order_by(DiscoveredGrant.confidence_score.desc()).all()


def approve_discovered_grant(
    db: Session,
    grant_id: str,
    admin_user_id: str,
    create_program: bool = True,
    program_key: Optional[str] = None
) -> Optional[Program]:
    """
    Approve a discovered grant and optionally create a Program record.

    Args:
        db: Database session
        grant_id: DiscoveredGrant ID
        admin_user_id: Admin user ID for audit trail
        create_program: Whether to create Program record (default True)
        program_key: Custom program_key (auto-generated if None)

    Returns:
        Program: Created program if create_program=True, else None
    """
    grant = db.query(DiscoveredGrant).filter(DiscoveredGrant.id == grant_id).first()
    if not grant:
        raise ValueError(f"Discovered grant {grant_id} not found")

    # Update review status
    grant.review_status = "approved"
    grant.reviewed_by = admin_user_id
    grant.reviewed_at = datetime.now(timezone.utc)

    if create_program:
        # Generate program_key if not provided
        if not program_key:
            program_key = _generate_program_key(grant.name, db)

        # Create Program record
        program = Program(
            id=str(uuid.uuid4()),
            program_key=program_key,
            name=grant.name,
            jurisdiction=grant.jurisdiction,
            program_type=grant.program_type,
            max_benefit=grant.max_benefit,
            status_or_deadline=grant.status_or_deadline,
            agency=grant.agency,
            phone=grant.phone,
            email=grant.email,
            website=grant.website,
            eligibility_summary=grant.eligibility_summary,
            docs_checklist=grant.docs_checklist,
            menu_category=_infer_category(grant),
            priority_rank=50.0,  # Default middle priority
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(program)

        # Link back to program
        grant.created_program_key = program_key

        db.commit()
        logger.info(f"Approved grant '{grant.name}' and created program '{program_key}'")
        return program

    db.commit()
    logger.info(f"Approved grant '{grant.name}' (no program created)")
    return None


def _generate_program_key(name: str, db: Session) -> str:
    """Generate unique program_key from grant name."""
    # Slugify name
    base_key = name.lower()
    base_key = base_key.replace("'", "").replace('"', "")
    base_key = "".join(c if c.isalnum() else "_" for c in base_key)
    base_key = "_".join(base_key.split())  # Collapse multiple underscores
    base_key = base_key[:100]  # Limit length

    # Ensure uniqueness
    key = base_key
    suffix = 2
    while db.query(Program).filter(Program.program_key == key).first():
        key = f"{base_key}_{suffix}"
        suffix += 1

    return key


def _infer_category(grant: DiscoveredGrant) -> str:
    """Infer menu_category from discovered grant data."""
    # Use extracted category from data_extractor if available
    if hasattr(grant, 'menu_category') and grant.menu_category:
        return grant.menu_category

    # Default
    return "GENERAL"
