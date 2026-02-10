"""
Comprehensive Syracuse Housing Grants Seed Data
Auto-populate with all known Syracuse housing grants with complete details.
This creates a well-structured grant database with deadlines, income limits, and requirements.
"""

import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, Base, engine
from backend.models.program import Program
from backend.models.watchlist import WatchlistEntry

# Syracuse Housing Grants - Comprehensive Database
SYRACUSE_GRANTS = [
    {
        "name": "SHARP Grant (Syracuse Homeowner Assistance & Repair Program)",
        "program_key": "sharp_syracuse",
        "jurisdiction": "City of Syracuse",
        "program_type": "Grant",
        "menu_category": "URGENT SAFETY",
        "repair_tags": "roof;heating;structural;electrical;plumbing;windows;doors;exterior;steps;railings",
        "priority_rank": 100.0,
        "max_benefit": "Up to $3,000 (grant)",
        "status_or_deadline": "Seasonal - Often closes when funding depleted, reopens annually",
        "agency": "Home HeadQuarters / City of Syracuse CDBG",
        "phone": "(315) 474-1939",
        "email": "info@homehq.org",
        "website": "https://www.homehq.org/homeowner-loans-grants",
        "eligibility_summary": "Owner-occupied homes in Syracuse. Income limits apply (typically 80% AMI or below). First-come, first-served.",
        "income_guidance": "Income limits: ~$48,000 for 1 person, ~$55,000 for 2 people, ~$62,000 for 3 people, ~$68,500 for 4+ (2024 estimates, varies by year)",
        "docs_checklist": "Proof of ownership (deed); Photo ID; Proof of income (pay stubs, tax returns, Social Security); Utility bills; Repair estimates/bids",
        "last_verified": datetime.now(timezone.utc),
    },
    {
        "name": "NYS RESTORE Program (Senior 60+ Emergency Repairs)",
        "program_key": "nys_restore",
        "jurisdiction": "New York State",
        "program_type": "Grant",
        "menu_category": "URGENT SAFETY",
        "repair_tags": "roof;heating;structural;emergency;health-safety;electrical;plumbing;accessibility",
        "priority_rank": 100.0,
        "max_benefit": "$10,000-$20,000 depending on administrator and funding",
        "status_or_deadline": "Rolling basis - Check with local administrator for current funding",
        "agency": "NYS Homes & Community Renewal (HCR) - via local administrators",
        "phone": "(315) 474-1939 (Home HeadQuarters) or (315) 435-3558 (Onondaga County)",
        "email": "",
        "website": "https://hcr.ny.gov/restore-program",
        "eligibility_summary": "Homeowner 60+ years old. Emergency repairs only (health/safety hazards). Income limits apply. Must be owner-occupied.",
        "income_guidance": "Income limits vary by administrator. Generally 50-80% AMI. Contact local administrator for current limits.",
        "docs_checklist": "Proof of age (60+); Proof of ownership; Photo ID; Income documentation; Proof of emergency repair need",
        "last_verified": datetime.now(timezone.utc),
    },
    {
        "name": "Home HeadQuarters Urgent Care Program",
        "program_key": "hhq_urgent_care",
        "jurisdiction": "City of Syracuse",
        "program_type": "Loan/Deferred Loan Mix",
        "menu_category": "URGENT SAFETY",
        "repair_tags": "roof;heating;structural;electrical;plumbing;emergency;health-safety",
        "priority_rank": 95.0,
        "max_benefit": "Up to $20,000 (combination of loan and deferred loan)",
        "status_or_deadline": "Rolling - Emergency repairs prioritized",
        "agency": "Home HeadQuarters",
        "phone": "(315) 474-1939",
        "email": "info@homehq.org",
        "website": "https://www.homehq.org/homeowner-loans-grants",
        "eligibility_summary": "Owner-occupied homes in Syracuse area. Emergency/urgent repairs that affect health and safety. Income limits apply.",
        "income_guidance": "Flexible income limits. Deferred loan portion may be forgivable after staying in home for specified period.",
        "docs_checklist": "Proof of ownership; Photo ID; Income proof; Emergency repair documentation/estimates; Homeowner's insurance (if required)",
        "last_verified": datetime.now(timezone.utc),
    },
    {
        "name": "T-HIP (Targeted Home Improvement Program)",
        "program_key": "t_hip_onondaga",
        "jurisdiction": "Onondaga County",
        "program_type": "Grant/Deferred Loan",
        "menu_category": "URGENT SAFETY",
        "repair_tags": "roof;heating;structural;windows;doors;electrical;plumbing;accessibility",
        "priority_rank": 90.0,
        "max_benefit": "Varies - Often up to $15,000-$25,000",
        "status_or_deadline": "Funding cycles - Call for current availability",
        "agency": "Onondaga County Community Development",
        "phone": "(315) 435-3558",
        "email": "",
        "website": "https://ongov.net/planning/cdbg.html",
        "eligibility_summary": "Low-to-moderate income homeowners in Onondaga County. Priority for seniors and disabled residents. Urgent repairs focus.",
        "income_guidance": "Income limits typically 50-80% Area Median Income. Varies by household size.",
        "docs_checklist": "Proof of ownership; Income documentation; Photo ID; Age verification (if senior); Disability documentation (if applicable); Repair estimates",
        "last_verified": datetime.now(timezone.utc),
    },
    {
        "name": "NYS Resilient Retrofits for At-Risk Housing",
        "program_key": "nys_resilient_retrofits",
        "jurisdiction": "New York State",
        "program_type": "Grant",
        "menu_category": "URGENT SAFETY",
        "repair_tags": "flood-mitigation;structural;foundation;drainage;waterproofing;resilience",
        "priority_rank": 75.0,
        "max_benefit": "Varies by project scope",
        "status_or_deadline": "Project-based funding - Check for current RFPs and availability",
        "agency": "NYS Division of Homeland Security and Emergency Services / HCR",
        "phone": "Check local administrator",
        "email": "",
        "website": "https://hcr.ny.gov/",
        "eligibility_summary": "Properties in flood-prone or disaster-prone areas. Focused on climate resilience and disaster mitigation retrofits.",
        "income_guidance": "May have income requirements depending on funding source. Check with administrator.",
        "docs_checklist": "Proof of ownership; Property assessment; Flood maps; Resilience retrofit plan; Income documentation (if required)",
        "last_verified": datetime.now(timezone.utc),
    },
    {
        "name": "NYS Homebuyer Dream Program",
        "program_key": "nys_homebuyer_dream",
        "jurisdiction": "New York State",
        "program_type": "Grant",
        "menu_category": "BUYING HELP",
        "repair_tags": "down-payment;closing-costs",
        "priority_rank": 70.0,
        "max_benefit": "Up to $15,000 down payment assistance",
        "status_or_deadline": "Active program - Check with participating lenders",
        "agency": "NYS Homes & Community Renewal",
        "phone": "",
        "email": "",
        "website": "https://hcr.ny.gov/homebuyer-dream-program",
        "eligibility_summary": "First-time homebuyers in New York State. Income and purchase price limits apply. Must complete homebuyer education.",
        "income_guidance": "Income limits vary by county. Generally 80% AMI or below. Check website for current limits.",
        "docs_checklist": "Pre-approval letter; Income documentation; Asset statements; Homebuyer education certificate; Purchase agreement",
        "last_verified": datetime.now(timezone.utc),
    },
    {
        "name": "NYSERDA EmPower+ (Income-Eligible Energy Efficiency)",
        "program_key": "nyserda_empower_plus",
        "jurisdiction": "New York State",
        "program_type": "Grant (No-cost services)",
        "menu_category": "ENERGY & BILLS",
        "repair_tags": "insulation;air-sealing;heating;appliances;energy;windows;doors;drafts",
        "priority_rank": 75.0,
        "max_benefit": "100% covered for eligible households - No cost energy upgrades",
        "status_or_deadline": "Rolling - Year-round program",
        "agency": "NYSERDA via approved contractors (PEACE Inc. locally)",
        "phone": "(315) 470-3315 (PEACE Inc.)",
        "email": "",
        "website": "https://www.nyserda.ny.gov/All-Programs/EmPower-New-York",
        "eligibility_summary": "Income-eligible homeowners and renters. Free energy efficiency upgrades including insulation, air sealing, lighting, appliances.",
        "income_guidance": "60% of State Median Income or below, OR enrolled in qualifying assistance programs (SNAP, HEAP, Medicaid, etc.)",
        "docs_checklist": "Proof of income OR proof of enrollment in qualifying assistance program; Utility bill; Photo ID",
        "last_verified": datetime.now(timezone.utc),
    },
    {
        "name": "PEACE Inc. Weatherization Assistance Program",
        "program_key": "peace_weatherization",
        "jurisdiction": "Onondaga County",
        "program_type": "Grant (No-cost services)",
        "menu_category": "ENERGY & BILLS",
        "repair_tags": "insulation;air-sealing;heating;windows;doors;energy;ventilation",
        "priority_rank": 75.0,
        "max_benefit": "100% covered for eligible households - Average $7,000-$9,000 in improvements",
        "status_or_deadline": "Rolling - Year-round, may have waitlist",
        "agency": "PEACE Inc. Energy & Housing",
        "phone": "(315) 470-3315",
        "email": "",
        "website": "https://www.peace-caa.org/programs/energyhousing/",
        "eligibility_summary": "Low-income homeowners and renters. Priority for elderly, disabled, and families with children.",
        "income_guidance": "At or below 60% State Median Income. Priority for HEAP recipients.",
        "docs_checklist": "Proof of income; Utility bills (12 months if available); Proof of ownership or landlord permission; Photo ID",
        "last_verified": datetime.now(timezone.utc),
    },
    {
        "name": "Home HeadQuarters FlexFund Loan Program",
        "program_key": "hhq_flexfund",
        "jurisdiction": "Central New York",
        "program_type": "Loan",
        "menu_category": "GENERAL",
        "repair_tags": "roof;heating;structural;windows;doors;exterior;energy;renovation",
        "priority_rank": 60.0,
        "max_benefit": "Loan amounts vary - Statewide program",
        "status_or_deadline": "Rolling - Year-round",
        "agency": "Home HeadQuarters",
        "phone": "(315) 474-1939",
        "email": "info@homehq.org",
        "website": "https://www.homehq.org/homeowner-loans-grants",
        "eligibility_summary": "Flexible underwriting for home improvement loans. Credit-challenged borrowers may qualify.",
        "income_guidance": "No strict income limits. Credit and ability to repay assessed.",
        "docs_checklist": "Proof of ownership; Photo ID; Income documentation; Credit report; Repair estimates; Homeowner's insurance",
        "last_verified": datetime.now(timezone.utc),
    },
    {
        "name": "NYS Access to Home Program (Accessibility Modifications)",
        "program_key": "nys_access_to_home",
        "jurisdiction": "New York State",
        "program_type": "Grant",
        "menu_category": "AGING IN PLACE",
        "repair_tags": "accessibility;ramps;grab-bars;stairs;bathroom;lift;doorways;mobility",
        "priority_rank": 85.0,
        "max_benefit": "Up to $50,000 (typically $10,000-$30,000)",
        "status_or_deadline": "Rolling - Administered through local providers",
        "agency": "NYS HCR via AccessCNY and other providers",
        "phone": "(315) 455-7591 (AccessCNY)",
        "email": "",
        "website": "https://hcr.ny.gov/access-home-program",
        "eligibility_summary": "Homeowners or renters with disabilities. Modifications must be medically necessary. Income limits apply.",
        "income_guidance": "80% Area Median Income or below. Varies by household size.",
        "docs_checklist": "Medical documentation of disability; Income proof; Proof of ownership or landlord approval; Occupational therapy assessment; Modification estimates",
        "last_verified": datetime.now(timezone.utc),
    },
    {
        "name": "AccessCNY Environmental Modifications (E-Mods)",
        "program_key": "accesscny_emods",
        "jurisdiction": "Central New York",
        "program_type": "Grant",
        "menu_category": "AGING IN PLACE",
        "repair_tags": "accessibility;ramps;grab-bars;bathroom;stairs;mobility;doorways",
        "priority_rank": 80.0,
        "max_benefit": "Varies by need and funding source",
        "status_or_deadline": "Rolling - Year-round",
        "agency": "AccessCNY",
        "phone": "(315) 455-7591",
        "email": "",
        "website": "https://www.accesscny.org/services/emods/",
        "eligibility_summary": "Individuals with disabilities requiring home modifications. Multiple funding sources available.",
        "income_guidance": "Varies by funding source. Some programs income-based, others not.",
        "docs_checklist": "Disability documentation; Income proof (if required); Assessment by occupational therapist; Contractor estimates",
        "last_verified": datetime.now(timezone.utc),
    },
    {
        "name": "City of Syracuse Lead Hazard Control Program",
        "program_key": "syracuse_lead_program",
        "jurisdiction": "City of Syracuse",
        "program_type": "Grant",
        "menu_category": "HEALTH HAZARDS",
        "repair_tags": "lead;windows;doors;siding;paint;healthy-homes",
        "priority_rank": 85.0,
        "max_benefit": "Varies - Covers lead hazard remediation",
        "status_or_deadline": "Funding cycles - Often closed, call for next opening",
        "agency": "City of Syracuse Neighborhood & Business Development",
        "phone": "(315) 448-8710",
        "email": "",
        "website": "https://www.syr.gov/Departments/NBD/Neighborhood-Development/Syracuse-Lead-Grant-Program",
        "eligibility_summary": "Homes with lead hazards. Priority for homes with children under 6. Income limits apply.",
        "income_guidance": "80% Area Median Income or below. Priority for lower incomes.",
        "docs_checklist": "Lead inspection report; Proof of ownership; Income documentation; Household composition; Child ages",
        "last_verified": datetime.now(timezone.utc),
    },
    {
        "name": "Onondaga County Lead Hazard Reduction Program",
        "program_key": "onondaga_lead_program",
        "jurisdiction": "Onondaga County",
        "program_type": "Grant",
        "menu_category": "HEALTH HAZARDS",
        "repair_tags": "lead;windows;doors;siding;paint;healthy-homes",
        "priority_rank": 80.0,
        "max_benefit": "Varies - Covers lead hazard remediation",
        "status_or_deadline": "Availability varies - HUD-funded program",
        "agency": "Onondaga County Community Development",
        "phone": "(315) 435-3558",
        "email": "",
        "website": "https://ongov.net/planning/cdbg.html",
        "eligibility_summary": "Homes with lead hazards in Onondaga County. Often requires child under 6 with elevated blood lead level.",
        "income_guidance": "Income limits apply. Check with program for current requirements.",
        "docs_checklist": "Lead test results; Blood lead level (if applicable); Income proof; Proof of ownership; Household composition",
        "last_verified": datetime.now(timezone.utc),
    },
    {
        "name": "Onondaga County HEAP (Home Energy Assistance Program)",
        "program_key": "onondaga_heap",
        "jurisdiction": "Onondaga County",
        "program_type": "Grant",
        "menu_category": "URGENT SAFETY",
        "repair_tags": "heating;utilities;emergency;energy",
        "priority_rank": 90.0,
        "max_benefit": "Benefit amount varies - Paid directly to utility/fuel vendor",
        "status_or_deadline": "Seasonal: November through mid-March (Emergency HEAP year-round)",
        "agency": "Onondaga County Department of Social Services",
        "phone": "(315) 435-8295 or Dial 211",
        "email": "",
        "website": "https://onondaga.gov/dss/heap/apply/",
        "eligibility_summary": "Low-income households struggling with heating costs. Emergency HEAP for heat-related emergencies.",
        "income_guidance": "60% State Median Income or below. Higher limits for elderly.",
        "docs_checklist": "Proof of income (all household members); Heating bills; Photo ID; Proof of address; Social Security cards",
        "last_verified": datetime.now(timezone.utc),
    },
    {
        "name": "Historic Preservation Programs (City/County)",
        "program_key": "historic_preservation",
        "jurisdiction": "City of Syracuse / Onondaga County",
        "program_type": "Grant/Tax Credit",
        "menu_category": "HISTORIC RESTORATION",
        "repair_tags": "facade;porch;exterior;windows;historic;preservation",
        "priority_rank": 55.0,
        "max_benefit": "Varies by program and district",
        "status_or_deadline": "Program-specific - Check with local preservation office",
        "agency": "Syracuse Landmark Preservation Board / County Planning",
        "phone": "(315) 448-8108",
        "email": "",
        "website": "https://www.syr.gov/",
        "eligibility_summary": "Properties in historic districts or designated landmarks. Must follow preservation standards.",
        "income_guidance": "Varies by program. Some programs income-based, others not.",
        "docs_checklist": "Historic significance documentation; Proof of ownership; Restoration plans; Preservation board approval; Contractor estimates",
        "last_verified": datetime.now(timezone.utc),
    },
    {
        "name": "USDA Section 504 Home Repair Program",
        "program_key": "usda_504_repair",
        "jurisdiction": "Rural areas (typically outside Syracuse city limits)",
        "program_type": "Grant/Loan",
        "menu_category": "URGENT SAFETY",
        "repair_tags": "roof;heating;structural;health-safety;accessibility",
        "priority_rank": 70.0,
        "max_benefit": "Grants up to $10,000 (age 62+, very low income); Loans up to $40,000",
        "status_or_deadline": "Rolling - Year-round (rural eligibility only)",
        "agency": "USDA Rural Development",
        "phone": "Check local USDA RD office",
        "email": "",
        "website": "https://www.rd.usda.gov/programs-services/single-family-housing-programs/single-family-housing-repair-loans-grants",
        "eligibility_summary": "Age 62+ for grants. Very low income. Must be in USDA-designated rural area. Remove health/safety hazards.",
        "income_guidance": "Grants: Very low income (50% AMI). Loans: Low income (80% AMI). Must be unable to get credit elsewhere.",
        "docs_checklist": "Proof of age (62+ for grant); Income documentation; Proof of ownership; Rural area verification; Repair estimates; Unable to secure credit (for loans)",
        "last_verified": datetime.now(timezone.utc),
    },
]

# Watchlist entries for grant monitoring
WATCHLIST_ENTRIES = [
    {
        "program_key": "sharp_syracuse",
        "name": "SHARP Grant",
        "url": "https://www.homehq.org/homeowner-loans-grants",
        "open_keywords": "applications;apply;accepting;available;funding available",
        "closed_keywords": "closed;not accepting;funding depleted;waitlist only",
    },
    {
        "program_key": "nys_restore",
        "name": "NYS RESTORE",
        "url": "https://hcr.ny.gov/restore-program",
        "open_keywords": "available;accepting;apply",
        "closed_keywords": "closed;suspended;not available",
    },
    {
        "program_key": "hhq_urgent_care",
        "name": "HHQ Urgent Care",
        "url": "https://www.homehq.org/homeowner-loans-grants",
        "open_keywords": "emergency;urgent;available",
        "closed_keywords": "not accepting;closed",
    },
    {
        "program_key": "nyserda_empower_plus",
        "name": "NYSERDA EmPower+",
        "url": "https://www.nyserda.ny.gov/All-Programs/EmPower-New-York",
        "open_keywords": "available;enroll;apply;accepting",
        "closed_keywords": "closed;suspended",
    },
    {
        "program_key": "peace_weatherization",
        "name": "PEACE Weatherization",
        "url": "https://www.peace-caa.org/programs/energyhousing/",
        "open_keywords": "available;apply;weatherization",
        "closed_keywords": "closed;not accepting;waitlist closed",
    },
    {
        "program_key": "nys_access_to_home",
        "name": "NYS Access to Home",
        "url": "https://hcr.ny.gov/access-home-program",
        "open_keywords": "available;accepting;apply",
        "closed_keywords": "closed;suspended",
    },
    {
        "program_key": "syracuse_lead_program",
        "name": "Syracuse Lead Program",
        "url": "https://www.syr.gov/Departments/NBD/Neighborhood-Development/Syracuse-Lead-Grant-Program",
        "open_keywords": "accepting;applications;apply;available",
        "closed_keywords": "closed;not accepting;2025 applications closed",
    },
    {
        "program_key": "onondaga_heap",
        "name": "HEAP",
        "url": "https://onondaga.gov/dss/heap/apply/",
        "open_keywords": "accepting;apply;available;open",
        "closed_keywords": "closed;season ended",
    },
]


def seed_grants():
    """Seed the database with comprehensive Syracuse grant data."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print("=" * 60)
        print("SYRACUSE HOUSING GRANTS DATABASE SEED")
        print("=" * 60)
        print()

        # Check if already seeded
        existing_count = db.query(Program).count()
        if existing_count > 0:
            print(f"[!] Database already contains {existing_count} programs.")
            response = input("Do you want to add/update grants? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("Seed cancelled.")
                return

        # Add/Update grants
        print("[*] Adding Syracuse housing grants...")
        added = 0
        updated = 0

        for grant_data in SYRACUSE_GRANTS:
            program_key = grant_data["program_key"]
            existing = db.query(Program).filter(Program.program_key == program_key).first()

            if existing:
                # Update existing program
                for key, value in grant_data.items():
                    if key != "program_key":  # Don't update the key itself
                        setattr(existing, key, value)
                existing.updated_at = datetime.now(timezone.utc)
                updated += 1
                print(f"  [+] Updated: {grant_data['name']}")
            else:
                # Add new program
                program = Program(**grant_data, is_active=True)
                db.add(program)
                added += 1
                print(f"  [+] Added: {grant_data['name']}")

        db.commit()
        print()
        print(f"[OK] Programs: {added} added, {updated} updated")

        # Add/Update watchlist entries
        print()
        print("[*] Adding watchlist monitoring entries...")
        watchlist_added = 0
        watchlist_updated = 0

        for watch_data in WATCHLIST_ENTRIES:
            program_key = watch_data["program_key"]
            existing = db.query(WatchlistEntry).filter(
                WatchlistEntry.program_key == program_key
            ).first()

            if existing:
                # Update existing entry
                for key, value in watch_data.items():
                    if key != "program_key":
                        setattr(existing, key, value)
                watchlist_updated += 1
                print(f"  [+] Updated: {watch_data['name']}")
            else:
                # Add new entry
                entry = WatchlistEntry(**watch_data, is_active=True)
                db.add(entry)
                watchlist_added += 1
                print(f"  [+] Added: {watch_data['name']}")

        db.commit()
        print()
        print(f"[OK] Watchlist: {watchlist_added} added, {watchlist_updated} updated")

        # Print summary
        print()
        print("=" * 60)
        print("DATABASE SUMMARY")
        print("=" * 60)
        total_programs = db.query(Program).filter(Program.is_active == True).count()
        total_watchlist = db.query(WatchlistEntry).filter(WatchlistEntry.is_active == True).count()

        print(f"Total Active Programs: {total_programs}")
        print(f"Total Watchlist Entries: {total_watchlist}")
        print()

        # Show programs by category
        print("Programs by Category:")
        categories = db.query(Program.menu_category).filter(Program.is_active == True).distinct()
        for (cat,) in categories:
            count = db.query(Program).filter(
                Program.is_active == True,
                Program.menu_category == cat
            ).count()
            print(f"  - {cat}: {count}")

        print()
        print("[OK] Seed completed successfully!")
        print()

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error during seed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_grants()
