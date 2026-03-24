"""
Eligibility matching engine.

Inputs : age (int), income (float), property_type (str), repair_category (str)
Output : ranked list of grants with match_score 0-100

Scoring model (each dimension worth 25 pts, un-specified dimensions are free passes):
  - income   : applicant_income <= grant.income_limit
  - age      : age_min <= applicant_age <= age_max
  - property : applicant property_type in grant.property_types
  - repair   : applicant repair_category in grant.repair_categories

If a grant specifies no constraints at all, score = 100.
"""
import json
import logging
from typing import Optional

from sqlalchemy.orm import Session

from ..models.grants_db import Grant

logger = logging.getLogger(__name__)

# Valid filter values
VALID_PROPERTY_TYPES = {
    "single_family", "multifamily", "condo", "co_op", "mobile_home", "townhouse"
}

VALID_REPAIR_CATEGORIES = {
    "emergency_repairs",
    "energy_efficiency",
    "accessibility",
    "structural",
    "historic_preservation",
}


def _parse_json_field(value: Optional[str]) -> list:
    if not value:
        return []
    try:
        result = json.loads(value)
        return result if isinstance(result, list) else []
    except (ValueError, TypeError):
        return []


def calculate_match_score(
    grant: Grant,
    age: int,
    income: float,
    property_type: str,
    repair_category: str,
) -> int:
    """
    Return an integer 0-100 representing how well the applicant matches this grant.
    Dimensions with no constraint on the grant side are ignored (not penalised).
    """
    total_possible = 0
    total_earned = 0

    # ── Income ──────────────────────────────────────────────────────────────
    if grant.income_limit is not None:
        total_possible += 25
        if income <= grant.income_limit:
            total_earned += 25
        elif income <= grant.income_limit * 1.10:
            # Within 10% over limit — partial credit
            total_earned += 10

    # ── Age ─────────────────────────────────────────────────────────────────
    if grant.age_min is not None or grant.age_max is not None:
        total_possible += 25
        age_ok = True
        if grant.age_min is not None and age < grant.age_min:
            age_ok = False
        if grant.age_max is not None and age > grant.age_max:
            age_ok = False
        if age_ok:
            total_earned += 25

    # ── Property type ────────────────────────────────────────────────────────
    prop_types = _parse_json_field(grant.property_types)
    if prop_types:
        total_possible += 25
        if property_type in prop_types:
            total_earned += 25

    # ── Repair category ──────────────────────────────────────────────────────
    repair_cats = _parse_json_field(grant.repair_categories)
    if repair_cats:
        total_possible += 25
        if repair_category in repair_cats:
            total_earned += 25

    if total_possible == 0:
        return 100

    return min(100, int((total_earned / total_possible) * 100))


def match_grants(
    db: Session,
    age: int,
    income: float,
    property_type: str,
    repair_category: str,
    repair_filter: Optional[str] = None,
    min_score: int = 0,
    include_closed: bool = False,
) -> list[dict]:
    """
    Query all active grants, score them, apply optional filters, and return
    a sorted list (highest score first).

    Parameters
    ----------
    db              : SQLAlchemy session
    age             : Applicant age
    income          : Annual household income
    property_type   : One of VALID_PROPERTY_TYPES
    repair_category : One of VALID_REPAIR_CATEGORIES
    repair_filter   : Optional hard-filter to only grants that include this
                      repair category (independent of scoring)
    min_score       : Exclude grants below this threshold (default 0)
    include_closed  : Whether to include grants with status == "closed"

    Returns
    -------
    List of dicts with grant data + match_score, sorted descending by score.
    """
    try:
        query = db.query(Grant)
        if not include_closed:
            query = query.filter(Grant.status != "closed")

        grants = query.all()
    except Exception:
        logger.exception("Database error while fetching grants for matching")
        return []

    results = []
    for grant in grants:
        # Optional hard repair-category filter
        if repair_filter:
            cats = _parse_json_field(grant.repair_categories)
            if cats and repair_filter not in cats:
                continue

        try:
            score = calculate_match_score(grant, age, income, property_type, repair_category)
        except Exception:
            logger.exception("Score calculation failed for grant %s", grant.id)
            score = 0

        if score < min_score:
            continue

        row = grant.to_dict()
        row["match_score"] = score
        if grant.eligibility:
            row["eligibility_criteria"] = grant.eligibility.to_dict()
        else:
            row["eligibility_criteria"] = {}
        results.append(row)

    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results
