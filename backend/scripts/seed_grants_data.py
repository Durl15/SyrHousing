"""
Seed the grants, eligibility_criteria, and grant_applications tables with
real Syracuse/NYS grant programs.

Run from the backend package root:
    python -m backend.scripts.seed_grants_data
"""
import json
import logging
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)


GRANT_SEED_DATA = [
    # ── 1. SHARP ─────────────────────────────────────────────────────────────
    {
        "grant": {
            "grant_name": "SHARP – Syracuse Home Assistance and Repair Program",
            "source": "City of Syracuse / Home HeadQuarters",
            "amount_min": 0, "amount_max": 15000,
            "deadline": "rolling",
            "income_limit": 56450.0,
            "age_min": None, "age_max": None,
            "property_types": ["single_family"],
            "repair_categories": ["structural", "emergency_repairs", "accessibility"],
            "application_url": "https://hhqinc.org/sharp",
            "status": "open",
            "description": "Forgivable deferred loan for low-to-moderate income Syracuse homeowners. Covers structural, code, health and safety, and accessibility repairs. Loan is forgiven after a required owner-occupancy period.",
            "agency_phone": "(315) 474-1939",
            "agency_email": "info@hhqinc.org",
        },
        "eligibility": {
            "requires_owner_occupied": True, "requires_primary_residence": True,
            "requires_us_citizen": False,
            "geographic_restriction": "City of Syracuse, NY",
            "credit_score_min": None, "first_time_buyer_required": False,
            "additional_notes": "Property must be within Syracuse city limits. Income limit is 80% AMI. 1–4 unit owner-occupied residential properties eligible.",
        },
    },
    # ── 2. RESTORE ───────────────────────────────────────────────────────────
    {
        "grant": {
            "grant_name": "RESTORE – Residential Emergency Services to Offer Repairs to the Elderly",
            "source": "NYS Office of Temporary and Disability Assistance (OTDA)",
            "amount_min": 0, "amount_max": 5000,
            "deadline": "rolling",
            "income_limit": 31800.0,
            "age_min": 60, "age_max": None,
            "property_types": ["single_family"],
            "repair_categories": ["emergency_repairs", "structural"],
            "application_url": "https://otda.ny.gov/programs/restore/",
            "status": "open",
            "description": "State-funded emergency home repair grant for homeowners 60+ with limited income. Addresses critical health, safety, and structural repairs to prevent displacement.",
            "agency_phone": "(315) 435-2700",
            "agency_email": "restore@onondagacounty.gov",
        },
        "eligibility": {
            "requires_owner_occupied": True, "requires_primary_residence": True,
            "requires_us_citizen": False,
            "geographic_restriction": "New York State (Onondaga County administered locally)",
            "credit_score_min": None, "first_time_buyer_required": False,
            "additional_notes": "Applicant must be 60 or older. Repairs must pose an immediate health or safety risk. No repayment required.",
        },
    },
    # ── 3. T-HIP ─────────────────────────────────────────────────────────────
    {
        "grant": {
            "grant_name": "T-HIP – Targeted Home Improvement Program",
            "source": "Home HeadQuarters / HUD Community Development Block Grant",
            "amount_min": 0, "amount_max": 10000,
            "deadline": "rolling",
            "income_limit": 63400.0,
            "age_min": None, "age_max": None,
            "property_types": ["single_family"],
            "repair_categories": ["structural", "energy_efficiency", "emergency_repairs"],
            "application_url": "https://hhqinc.org/t-hip",
            "status": "open",
            "description": "Targeted grant for LMI Syracuse homeowners in CDBG target areas. Covers structural repairs, code violations, and energy efficiency improvements.",
            "agency_phone": "(315) 474-1939",
            "agency_email": "info@hhqinc.org",
        },
        "eligibility": {
            "requires_owner_occupied": True, "requires_primary_residence": True,
            "requires_us_citizen": False,
            "geographic_restriction": "HUD-designated CDBG target areas within Syracuse, NY",
            "credit_score_min": None, "first_time_buyer_required": False,
            "additional_notes": "Property must be in a HUD-designated CDBG target area. Income at or below 90% AMI.",
        },
    },
    # ── 4. NYS Resilient Retrofits ───────────────────────────────────────────
    {
        "grant": {
            "grant_name": "NYS Resilient Retrofits",
            "source": "NYSERDA / NY Homes and Community Renewal",
            "amount_min": 10000, "amount_max": 50000,
            "deadline": "2026-12-31",
            "income_limit": 90000.0,
            "age_min": None, "age_max": None,
            "property_types": ["single_family", "multifamily", "townhouse"],
            "repair_categories": ["energy_efficiency", "structural"],
            "application_url": "https://www.nyserda.ny.gov/All-Programs/Resilient-Retrofits",
            "status": "open",
            "description": "Substantial funding for climate resilience: insulation, high-efficiency heating/cooling, air sealing, and structural fortification. Designed for LMI households.",
            "agency_phone": "1-866-697-3732",
            "agency_email": "info@nyserda.ny.gov",
        },
        "eligibility": {
            "requires_owner_occupied": True, "requires_primary_residence": True,
            "requires_us_citizen": False,
            "geographic_restriction": "New York State",
            "credit_score_min": None, "first_time_buyer_required": False,
            "additional_notes": "Income at or below 80% AMI for maximum grant amounts. Must use NYSERDA-qualified contractor.",
        },
    },
    # ── 5. Homebuyer Dream Program ───────────────────────────────────────────
    {
        "grant": {
            "grant_name": "Homebuyer Dream Program (HDP)",
            "source": "Federal Home Loan Bank of New York (FHLBNY)",
            "amount_min": 500, "amount_max": 9500,
            "deadline": "2026-04-15",
            "income_limit": 84720.0,
            "age_min": None, "age_max": None,
            "property_types": ["single_family", "condo", "co_op", "townhouse"],
            "repair_categories": ["accessibility", "structural"],
            "application_url": "https://www.fhlbny.com/hdp",
            "status": "closing_soon",
            "description": "Up to $9,500 in down payment and closing cost assistance for first-time homebuyers. Funds reserved through participating FHLBNY member banks.",
            "agency_phone": "(212) 441-6700",
            "agency_email": "hdp@fhlbny.com",
        },
        "eligibility": {
            "requires_owner_occupied": True, "requires_primary_residence": True,
            "requires_us_citizen": False,
            "geographic_restriction": "New York or New Jersey",
            "credit_score_min": 620, "first_time_buyer_required": True,
            "additional_notes": "First-time homebuyer required. Must obtain mortgage through a participating FHLBNY member. Homebuyer education course required.",
        },
    },
    # ── 6. NYSERDA Green Jobs – Green NY ─────────────────────────────────────
    {
        "grant": {
            "grant_name": "NYSERDA Green Jobs – Green NY (GJGNY)",
            "source": "NYSERDA",
            "amount_min": 0, "amount_max": 14000,
            "deadline": "rolling",
            "income_limit": 107000.0,
            "age_min": None, "age_max": None,
            "property_types": ["single_family", "multifamily"],
            "repair_categories": ["energy_efficiency"],
            "application_url": "https://www.nyserda.ny.gov/All-Programs/Green-Jobs-Green-New-York",
            "status": "open",
            "description": "On-bill financing and grants for energy efficiency: insulation, air sealing, heating systems, windows. LMI customers receive grants up to $14,000 with no repayment.",
            "agency_phone": "1-866-697-3732",
            "agency_email": "info@nyserda.ny.gov",
        },
        "eligibility": {
            "requires_owner_occupied": True, "requires_primary_residence": True,
            "requires_us_citizen": False,
            "geographic_restriction": "New York State",
            "credit_score_min": None, "first_time_buyer_required": False,
            "additional_notes": "LMI: household income ≤80% State Median Income. Must start with a free home energy assessment.",
        },
    },
    # ── 7. Home HeadQuarters ─────────────────────────────────────────────────
    {
        "grant": {
            "grant_name": "Home HeadQuarters Comprehensive Home Repair",
            "source": "Home HeadQuarters, Inc. (HHQ)",
            "amount_min": 0, "amount_max": 25000,
            "deadline": "rolling",
            "income_limit": 70500.0,
            "age_min": None, "age_max": None,
            "property_types": ["single_family"],
            "repair_categories": ["structural", "emergency_repairs", "accessibility", "energy_efficiency"],
            "application_url": "https://hhqinc.org/home-repair",
            "status": "open",
            "description": "Comprehensive repair program for LMI homeowners in Onondaga County and Central NY. Covers structural, code, health & safety, accessibility, and energy efficiency repairs.",
            "agency_phone": "(315) 474-1939",
            "agency_email": "info@hhqinc.org",
        },
        "eligibility": {
            "requires_owner_occupied": True, "requires_primary_residence": True,
            "requires_us_citizen": False,
            "geographic_restriction": "Onondaga County and Central New York",
            "credit_score_min": None, "first_time_buyer_required": False,
            "additional_notes": "Income at or below 100% AMI. Priority given to elderly, disabled, and households with children.",
        },
    },
    # ── 8. HEAP ──────────────────────────────────────────────────────────────
    {
        "grant": {
            "grant_name": "HEAP – Home Energy Assistance Program",
            "source": "NYS Office of Temporary and Disability Assistance (OTDA)",
            "amount_min": 0, "amount_max": 3000,
            "deadline": "2026-05-15",
            "income_limit": 42156.0,
            "age_min": None, "age_max": None,
            "property_types": ["single_family", "multifamily", "mobile_home"],
            "repair_categories": ["energy_efficiency", "emergency_repairs"],
            "application_url": "https://otda.ny.gov/programs/heap/",
            "status": "open",
            "description": "Federally funded program helping low-income households pay heating and cooling costs, and emergency energy-related repairs. Includes furnace repair/replacement.",
            "agency_phone": "(315) 435-2700",
            "agency_email": "heap@onondagacounty.gov",
        },
        "eligibility": {
            "requires_owner_occupied": False, "requires_primary_residence": True,
            "requires_us_citizen": False,
            "geographic_restriction": "New York State",
            "credit_score_min": None, "first_time_buyer_required": False,
            "additional_notes": "Available to renters and homeowners. Income at or below 60% State Median Income. Emergency component available year-round.",
        },
    },
    # ── 9. Weatherization Assistance Program ─────────────────────────────────
    {
        "grant": {
            "grant_name": "Weatherization Assistance Program (WAP)",
            "source": "NYS Homes and Community Renewal (HCR)",
            "amount_min": 0, "amount_max": 6500,
            "deadline": "rolling",
            "income_limit": 42156.0,
            "age_min": None, "age_max": None,
            "property_types": ["single_family", "multifamily", "mobile_home"],
            "repair_categories": ["energy_efficiency"],
            "application_url": "https://hcr.ny.gov/weatherization",
            "status": "open",
            "description": "Free weatherization services for income-eligible households: insulation, air sealing, window repair, heating system tune-ups. Reduces energy bills by an average of 35%.",
            "agency_phone": "(315) 476-7251",
            "agency_email": "weatherization@cnyca.org",
        },
        "eligibility": {
            "requires_owner_occupied": False, "requires_primary_residence": True,
            "requires_us_citizen": False,
            "geographic_restriction": "New York State (administered by CNY Community Action in Onondaga County)",
            "credit_score_min": None, "first_time_buyer_required": False,
            "additional_notes": "Available to renters and homeowners. Priority for elderly, disabled, and households with children under 6. No repayment required.",
        },
    },
    # ── 10. USDA Section 504 ─────────────────────────────────────────────────
    {
        "grant": {
            "grant_name": "USDA Section 504 Home Repair Grant",
            "source": "USDA Rural Development",
            "amount_min": 0, "amount_max": 10000,
            "deadline": "rolling",
            "income_limit": 26500.0,
            "age_min": 62, "age_max": None,
            "property_types": ["single_family", "mobile_home"],
            "repair_categories": ["structural", "emergency_repairs", "accessibility"],
            "application_url": "https://www.rd.usda.gov/programs-services/single-family-housing-programs/single-family-housing-repair-loans-grants",
            "status": "open",
            "description": "Federal grant for very low-income rural homeowners aged 62+ to remove health and safety hazards. Grants up to $10,000; loans up to $40,000 at 1% interest.",
            "agency_phone": "(315) 477-6400",
            "agency_email": "rd.syracuse@usda.gov",
        },
        "eligibility": {
            "requires_owner_occupied": True, "requires_primary_residence": True,
            "requires_us_citizen": True,
            "geographic_restriction": "Rural areas of New York State (check property eligibility at eligibility.sc.egov.usda.gov)",
            "credit_score_min": None, "first_time_buyer_required": False,
            "additional_notes": "Grant component requires age 62+. Very low income (50% AMI). Property must be in USDA-eligible rural area.",
        },
    },
    # ── 11. VA SAH Grant ─────────────────────────────────────────────────────
    {
        "grant": {
            "grant_name": "VA Specially Adapted Housing (SAH) Grant",
            "source": "U.S. Department of Veterans Affairs",
            "amount_min": 0, "amount_max": 109986,
            "deadline": "rolling",
            "income_limit": None,
            "age_min": None, "age_max": None,
            "property_types": ["single_family", "condo", "townhouse"],
            "repair_categories": ["accessibility"],
            "application_url": "https://www.va.gov/housing-assistance/disability-housing-grants/",
            "status": "open",
            "description": "Grants for veterans with service-connected disabilities to build, buy, or modify a home for independent living. SAH up to $109,986; SHA up to $22,036.",
            "agency_phone": "1-800-827-1000",
            "agency_email": "sahinfo.vbaco@va.gov",
        },
        "eligibility": {
            "requires_owner_occupied": True, "requires_primary_residence": True,
            "requires_us_citizen": True,
            "geographic_restriction": "United States",
            "credit_score_min": None, "first_time_buyer_required": False,
            "additional_notes": "Must be a veteran with qualifying service-connected disability. Contact local VA Regional Office for application.",
        },
    },
    # ── 12. Catholic Charities ───────────────────────────────────────────────
    {
        "grant": {
            "grant_name": "Catholic Charities Emergency Home Repair",
            "source": "Catholic Charities of Onondaga County",
            "amount_min": 0, "amount_max": 2500,
            "deadline": "rolling",
            "income_limit": 35000.0,
            "age_min": None, "age_max": None,
            "property_types": ["single_family"],
            "repair_categories": ["emergency_repairs"],
            "application_url": "https://www.ccoc.us/services/",
            "status": "open",
            "description": "Emergency home repair assistance for low-income Onondaga County residents regardless of religious affiliation. Addresses urgent health and safety issues.",
            "agency_phone": "(315) 424-1800",
            "agency_email": "info@ccoc.us",
        },
        "eligibility": {
            "requires_owner_occupied": True, "requires_primary_residence": True,
            "requires_us_citizen": False,
            "geographic_restriction": "Onondaga County, NY",
            "credit_score_min": None, "first_time_buyer_required": False,
            "additional_notes": "Open to all regardless of faith. Emergency repairs only. Call to schedule intake appointment.",
        },
    },
    # ── 13. Onondaga County HOME ─────────────────────────────────────────────
    {
        "grant": {
            "grant_name": "Onondaga County HOME Repair Program",
            "source": "Onondaga County / HUD HOME Investment Partnerships",
            "amount_min": 0, "amount_max": 20000,
            "deadline": "rolling",
            "income_limit": 63400.0,
            "age_min": None, "age_max": None,
            "property_types": ["single_family"],
            "repair_categories": ["structural", "accessibility", "emergency_repairs"],
            "application_url": "https://www.ongov.net/planning/housingprograms.html",
            "status": "open",
            "description": "HUD-funded repair program for LMI homeowners in Onondaga County (outside city of Syracuse). Covers structural repairs, code violations, and accessibility modifications.",
            "agency_phone": "(315) 435-3558",
            "agency_email": "planning@ongov.net",
        },
        "eligibility": {
            "requires_owner_occupied": True, "requires_primary_residence": True,
            "requires_us_citizen": False,
            "geographic_restriction": "Onondaga County (outside City of Syracuse)",
            "credit_score_min": None, "first_time_buyer_required": False,
            "additional_notes": "City of Syracuse residents should apply through SHARP. Income at or below 80% AMI.",
        },
    },
    # ── 14. Historic Preservation Grant ─────────────────────────────────────
    {
        "grant": {
            "grant_name": "NYS Historic Homeownership Rehabilitation Tax Credit",
            "source": "NY State Office of Parks, Recreation and Historic Preservation",
            "amount_min": 5000, "amount_max": 50000,
            "deadline": "rolling",
            "income_limit": None,
            "age_min": None, "age_max": None,
            "property_types": ["single_family", "multifamily"],
            "repair_categories": ["historic_preservation", "structural"],
            "application_url": "https://parks.ny.gov/shpo/tax-credits/",
            "status": "open",
            "description": "20% state tax credit for rehabilitation of certified historic owner-occupied residences. Can be combined with federal 20% historic tax credit for total 40% credit.",
            "agency_phone": "(518) 237-8643",
            "agency_email": "shpo@parks.ny.gov",
        },
        "eligibility": {
            "requires_owner_occupied": True, "requires_primary_residence": True,
            "requires_us_citizen": False,
            "geographic_restriction": "New York State",
            "credit_score_min": None, "first_time_buyer_required": False,
            "additional_notes": "Property must be a certified historic structure. Work must be pre-approved by SHPO before starting. No income limit.",
        },
    },
    # ── 15. CNY Community Action ─────────────────────────────────────────────
    {
        "grant": {
            "grant_name": "CNY Community Action – Emergency Home Repair",
            "source": "CNY Community Action Council",
            "amount_min": 0, "amount_max": 8000,
            "deadline": "rolling",
            "income_limit": 42156.0,
            "age_min": None, "age_max": None,
            "property_types": ["single_family", "mobile_home"],
            "repair_categories": ["emergency_repairs", "energy_efficiency", "accessibility"],
            "application_url": "https://www.cnyca.org/housing",
            "status": "open",
            "description": "Emergency home repair and weatherization services for low-income Onondaga County residents. Funded through Community Services Block Grant and other sources.",
            "agency_phone": "(315) 476-7251",
            "agency_email": "housing@cnyca.org",
        },
        "eligibility": {
            "requires_owner_occupied": True, "requires_primary_residence": True,
            "requires_us_citizen": False,
            "geographic_restriction": "Onondaga County, NY",
            "credit_score_min": None, "first_time_buyer_required": False,
            "additional_notes": "Income at or below 200% Federal Poverty Level. Call for intake appointment. Waitlist may apply.",
        },
    },
]


def run_seed():
    here = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(here)
    project_dir = os.path.dirname(backend_dir)
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)

    try:
        from backend.database import SessionLocal, engine, Base
        from backend.models.grants_db import Grant, EligibilityCriteria
        Base.metadata.create_all(bind=engine)
    except ImportError:
        from ..database import SessionLocal, engine, Base
        from ..models.grants_db import Grant, EligibilityCriteria
        Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    inserted = skipped = errors = 0

    try:
        for entry in GRANT_SEED_DATA:
            g_data = dict(entry["grant"])
            ec_data = entry["eligibility"]
            try:
                existing = db.query(Grant).filter(Grant.grant_name == g_data["grant_name"]).first()
                if existing:
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
                logger.exception("Failed to seed: %s", g_data.get("grant_name"))
                errors += 1
    finally:
        db.close()

    logger.info("Seed complete — inserted: %d  skipped: %d  errors: %d", inserted, skipped, errors)


if __name__ == "__main__":
    run_seed()
