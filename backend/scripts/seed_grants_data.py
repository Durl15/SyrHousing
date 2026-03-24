"""
Seed the grants, eligibility_criteria, and grant_applications tables with
real Syracuse/NYS grant programs.

Run from the backend package root:
    python -m backend.scripts.seed_grants_data

Or from C:\SyrHousing\backend:
    python -m scripts.seed_grants_data
"""
import json
import logging
import sys
import os
from datetime import datetime, date

# Allow running as a standalone script from the backend directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)


GRANT_SEED_DATA = [
    # ── 1. SHARP ─────────────────────────────────────────────────────────────
    {
        "grant": {
            "grant_name": "SHARP – Syracuse Home Assistance and Repair Program",
            "source": "City of Syracuse / Home HeadQuarters",
            "amount_min": 0,
            "amount_max": 15000,
            "deadline": "rolling",
            "income_limit": 56450.0,   # 80% AMI, Onondaga County 4-person household
            "age_min": None,
            "age_max": None,
            "property_types": ["single_family"],
            "repair_categories": ["structural", "emergency_repairs", "accessibility"],
            "application_url": "https://hhqinc.org/sharp",
            "status": "open",
            "description": (
                "Forgivable deferred loan for low-to-moderate income Syracuse homeowners. "
                "Covers structural, code, health and safety, and accessibility repairs. "
                "Loan is forgiven after a required owner-occupancy period."
            ),
            "agency_phone": "(315) 474-1939",
            "agency_email": "info@hhqinc.org",
        },
        "eligibility": {
            "requires_owner_occupied": True,
            "requires_primary_residence": True,
            "requires_us_citizen": False,
            "geographic_restriction": "City of Syracuse, NY",
            "credit_score_min": None,
            "first_time_buyer_required": False,
            "additional_notes": (
                "Property must be located within Syracuse city limits. "
                "Income limit is 80% of Area Median Income (AMI). "
                "1–4 unit owner-occupied residential properties eligible."
            ),
        },
    },
    # ── 2. RESTORE ───────────────────────────────────────────────────────────
    {
        "grant": {
            "grant_name": "RESTORE – Residential Emergency Services to Offer Repairs to the Elderly",
            "source": "NYS Office of Temporary and Disability Assistance (OTDA)",
            "amount_min": 0,
            "amount_max": 5000,
            "deadline": "rolling",
            "income_limit": 31800.0,   # Approximate 2024 threshold for single elderly
            "age_min": 60,
            "age_max": None,
            "property_types": ["single_family"],
            "repair_categories": ["emergency_repairs", "structural"],
            "application_url": "https://otda.ny.gov/programs/restore/",
            "status": "open",
            "description": (
                "State-funded emergency home repair grant for homeowners 60+ with limited income. "
                "Addresses critical health, safety, and structural repairs to prevent displacement. "
                "Administered locally through county offices and community action agencies."
            ),
            "agency_phone": "(315) 435-2700",
            "agency_email": "restore@onondagacounty.gov",
        },
        "eligibility": {
            "requires_owner_occupied": True,
            "requires_primary_residence": True,
            "requires_us_citizen": False,
            "geographic_restriction": "New York State (Onondaga County administered locally)",
            "credit_score_min": None,
            "first_time_buyer_required": False,
            "additional_notes": (
                "Applicant must be 60 or older. Income verification required. "
                "Repairs must pose an immediate health or safety risk. "
                "No repayment required — direct grant."
            ),
        },
    },
    # ── 3. T-HIP ─────────────────────────────────────────────────────────────
    {
        "grant": {
            "grant_name": "T-HIP – Targeted Home Improvement Program",
            "source": "Home HeadQuarters / HUD Community Development Block Grant",
            "amount_min": 0,
            "amount_max": 10000,
            "deadline": "rolling",
            "income_limit": 63400.0,   # 90% AMI — LMI threshold
            "age_min": None,
            "age_max": None,
            "property_types": ["single_family"],
            "repair_categories": ["structural", "energy_efficiency", "emergency_repairs"],
            "application_url": "https://hhqinc.org/t-hip",
            "status": "open",
            "description": (
                "Targeted grant for low-to-moderate income Syracuse homeowners in designated "
                "CDBG target areas. Covers structural repairs, code violations, and energy "
                "efficiency improvements. No repayment for qualified applicants."
            ),
            "agency_phone": "(315) 474-1939",
            "agency_email": "info@hhqinc.org",
        },
        "eligibility": {
            "requires_owner_occupied": True,
            "requires_primary_residence": True,
            "requires_us_citizen": False,
            "geographic_restriction": "HUD-designated CDBG target areas within Syracuse, NY",
            "credit_score_min": None,
            "first_time_buyer_required": False,
            "additional_notes": (
                "Property must be in a HUD-designated CDBG target area. "
                "Income at or below 90% AMI. Contact HHQ to verify eligibility by address."
            ),
        },
    },
    # ── 4. NYS Resilient Retrofits ───────────────────────────────────────────
    {
        "grant": {
            "grant_name": "NYS Resilient Retrofits",
            "source": "NYSERDA / NY Homes and Community Renewal",
            "amount_min": 10000,
            "amount_max": 50000,
            "deadline": "2026-12-31",
            "income_limit": 90000.0,
            "age_min": None,
            "age_max": None,
            "property_types": ["single_family", "multifamily", "townhouse"],
            "repair_categories": ["energy_efficiency", "structural"],
            "application_url": "https://www.nyserda.ny.gov/All-Programs/Resilient-Retrofits",
            "status": "open",
            "description": (
                "Substantial funding for climate resilience improvements: insulation, "
                "high-efficiency heating/cooling, air sealing, and structural fortification. "
                "Designed for LMI households to reduce energy burden and improve durability. "
                "Can be combined with other NYSERDA programs."
            ),
            "agency_phone": "1-866-NYSERDA",
            "agency_email": "info@nyserda.ny.gov",
        },
        "eligibility": {
            "requires_owner_occupied": True,
            "requires_primary_residence": True,
            "requires_us_citizen": False,
            "geographic_restriction": "New York State",
            "credit_score_min": None,
            "first_time_buyer_required": False,
            "additional_notes": (
                "Income must be at or below 80% AMI for maximum grant amounts. "
                "100–150% AMI eligible for reduced grant with financing. "
                "Must use NYSERDA-qualified contractor."
            ),
        },
    },
    # ── 5. Homebuyer Dream Program ───────────────────────────────────────────
    {
        "grant": {
            "grant_name": "Homebuyer Dream Program (HDP)",
            "source": "Federal Home Loan Bank of New York (FHLBNY)",
            "amount_min": 500,
            "amount_max": 9500,
            "deadline": "2026-04-15",   # Upcoming reservation window
            "income_limit": 84720.0,   # 80% AMI 4-person, NYC/NY 2024
            "age_min": None,
            "age_max": None,
            "property_types": ["single_family", "condo", "co_op", "townhouse"],
            "repair_categories": ["accessibility", "structural"],
            "application_url": "https://www.fhlbny.com/hdp",
            "status": "closing_soon",
            "description": (
                "Up to $9,500 in down payment and closing cost assistance for first-time "
                "homebuyers purchasing in New York or New Jersey. Funds are reserved through "
                "participating FHLBNY member banks — contact a participating lender to apply. "
                "Retention period of 5 years applies."
            ),
            "agency_phone": "(212) 441-6700",
            "agency_email": "hdp@fhlbny.com",
        },
        "eligibility": {
            "requires_owner_occupied": True,
            "requires_primary_residence": True,
            "requires_us_citizen": False,
            "geographic_restriction": "New York or New Jersey — must purchase in NY/NJ",
            "credit_score_min": 620,
            "first_time_buyer_required": True,
            "additional_notes": (
                "First-time homebuyer required (no ownership interest in primary residence "
                "in past 3 years). Must obtain mortgage through a participating FHLBNY member. "
                "Homebuyer education course required. Reservation windows open periodically."
            ),
        },
    },
    # ── 6. NYSERDA Green Jobs – Green NY ─────────────────────────────────────
    {
        "grant": {
            "grant_name": "NYSERDA Green Jobs – Green NY (GJGNY)",
            "source": "NYSERDA",
            "amount_min": 0,
            "amount_max": 14000,
            "deadline": "rolling",
            "income_limit": 107000.0,
            "age_min": None,
            "age_max": None,
            "property_types": ["single_family", "multifamily"],
            "repair_categories": ["energy_efficiency"],
            "application_url": "https://www.nyserda.ny.gov/All-Programs/Green-Jobs-Green-New-York",
            "status": "open",
            "description": (
                "On-bill financing and grants for energy efficiency improvements: insulation, "
                "air sealing, heating systems, windows, and more. LMI customers receive "
                "grants up to $14,000 with no repayment. Moderate income customers receive "
                "low-interest financing (as low as 0%). Includes free energy assessment."
            ),
            "agency_phone": "1-866-NYSERDA",
            "agency_email": "info@nyserda.ny.gov",
        },
        "eligibility": {
            "requires_owner_occupied": True,
            "requires_primary_residence": True,
            "requires_us_citizen": False,
            "geographic_restriction": "New York State",
            "credit_score_min": None,
            "first_time_buyer_required": False,
            "additional_notes": (
                "LMI definition: household income ≤80% State Median Income (SMI). "
                "Moderate income: 80–120% SMI — eligible for 0% on-bill financing. "
                "Must start with a free home energy assessment through NYSERDA portal."
            ),
        },
    },
    # ── 7. Home HeadQuarters Repair Program ─────────────────────────────────
    {
        "grant": {
            "grant_name": "Home HeadQuarters Comprehensive Home Repair",
            "source": "Home HeadQuarters, Inc. (HHQ)",
            "amount_min": 0,
            "amount_max": 25000,
            "deadline": "rolling",
            "income_limit": 70500.0,
            "age_min": None,
            "age_max": None,
            "property_types": ["single_family"],
            "repair_categories": [
                "structural",
                "emergency_repairs",
                "accessibility",
                "energy_efficiency",
            ],
            "application_url": "https://hhqinc.org/home-repair",
            "status": "open",
            "description": (
                "Comprehensive repair program for low-to-moderate income homeowners in "
                "Onondaga County and Central New York. Covers structural, code, health & "
                "safety, accessibility, and energy efficiency repairs. Multiple funding "
                "sources — grant amounts and terms vary by repair type and funding availability."
            ),
            "agency_phone": "(315) 474-1939",
            "agency_email": "info@hhqinc.org",
        },
        "eligibility": {
            "requires_owner_occupied": True,
            "requires_primary_residence": True,
            "requires_us_citizen": False,
            "geographic_restriction": "Onondaga County and Central New York",
            "credit_score_min": None,
            "first_time_buyer_required": False,
            "additional_notes": (
                "Income at or below 100% AMI. Properties must pass initial assessment. "
                "Priority given to elderly, disabled, and households with children. "
                "HHQ is a HUD-approved housing counseling agency."
            ),
        },
    },
]


def run_seed():
    """Insert seed grants if they do not already exist."""
    import sys
    import os

    # Add parent dirs so relative imports work when run as __main__
    here = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(here)
    project_dir = os.path.dirname(backend_dir)
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)

    try:
        from backend.database import SessionLocal, engine, Base
        from backend.models.grants_db import Grant, EligibilityCriteria
        # Ensure tables exist
        Base.metadata.create_all(bind=engine)
    except ImportError:
        # Try relative import path for in-package execution
        from ..database import SessionLocal, engine, Base
        from ..models.grants_db import Grant, EligibilityCriteria
        Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    inserted = 0
    skipped = 0
    errors = 0

    try:
        for entry in GRANT_SEED_DATA:
            g_data = entry["grant"]
            ec_data = entry["eligibility"]

            try:
                existing = (
                    db.query(Grant)
                    .filter(Grant.grant_name == g_data["grant_name"])
                    .first()
                )
                if existing:
                    logger.info("SKIP  (already exists): %s", g_data["grant_name"])
                    skipped += 1
                    continue

                prop_types = g_data.pop("property_types", None)
                repair_cats = g_data.pop("repair_categories", None)

                grant = Grant(
                    **g_data,
                    property_types=json.dumps(prop_types) if prop_types else None,
                    repair_categories=json.dumps(repair_cats) if repair_cats else None,
                    last_verified=datetime.utcnow(),
                )
                db.add(grant)
                db.flush()

                ec = EligibilityCriteria(grant_id=grant.id, **ec_data)
                db.add(ec)
                db.flush()

                db.commit()
                inserted += 1
                logger.info("INSERT: %s", grant.grant_name)

            except Exception:
                db.rollback()
                logger.exception("Failed to seed grant: %s", g_data.get("grant_name"))
                errors += 1

    finally:
        db.close()

    logger.info(
        "\nSeed complete — inserted: %d  skipped: %d  errors: %d",
        inserted, skipped, errors,
    )


if __name__ == "__main__":
    run_seed()
