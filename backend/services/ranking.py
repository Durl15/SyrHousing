"""
Port of compute_rank() from agent_gui.py:145-220.
Same algorithm, same weights. Does NOT mutate program data.
Enhancement: if repair_severity present, weight tag matches by severity score.
"""

import re
from typing import List, Tuple, Set, Optional, Dict

from ..models.program import Program
from ..models.user_profile import UserProfile


def normalize_tags(s: Optional[str]) -> Set[str]:
    if not s:
        return set()
    return {p.strip().lower() for p in s.split(";") if p.strip()}


def compute_rank(
    program: Program,
    profile: UserProfile,
) -> Tuple[int, List[str]]:
    score = 0
    why: List[str] = []

    # --- ProgramType scoring ---
    ptype = (program.program_type or "").strip().lower()
    if "grant" in ptype:
        score += 35
        why.append("+35: ProgramType indicates GRANT (preferred vs loans).")
    elif "deferred" in ptype or "forg" in ptype:
        score += 25
        why.append("+25: Deferred/forgivable assistance.")
    elif "loan" in ptype:
        score += 10
        why.append("+10: Loan product (less favorable than grants).")
    else:
        score += 12
        why.append("+12: ProgramType unspecified; treated as general assistance.")

    # --- MenuCategory scoring ---
    cat = (program.menu_category or "").strip().lower()
    if "urgent" in cat or "safety" in cat:
        score += 20
        why.append("+20: URGENT SAFETY category aligns with critical repairs.")
    elif "health" in cat:
        score += 12
        why.append("+12: HEALTH HAZARDS category.")
    elif "aging" in cat or "access" in cat:
        score += 10
        why.append("+10: AGING IN PLACE/accessibility category.")
    elif "energy" in cat:
        score += 10
        why.append("+10: ENERGY & BILLS category.")
    else:
        score += 6
        why.append("+6: General category.")

    # --- Repair tag matching ---
    repair_needs_list: List[str] = profile.repair_needs or []
    need = {str(n).strip().lower() for n in repair_needs_list if str(n).strip()}
    tags = normalize_tags(program.repair_tags)
    hits = sorted(need.intersection(tags))

    if hits:
        severity: Dict[str, int] = profile.repair_severity or {}
        if severity:
            pts = 0
            for h in hits:
                sev = severity.get(h, 1)
                pts += min(10, max(1, sev)) * 3
            pts = min(30, pts)
        else:
            pts = min(30, 10 * len(hits))
        score += pts
        why.append(f"+{pts}: Matches repair needs: {', '.join(hits)}.")
    else:
        score += 4
        why.append("+4: No explicit repair-tag match; verify scope.")

    # --- Jurisdiction scoring ---
    jur = (program.jurisdiction or "").strip().lower()
    agency = (program.agency or "").strip().lower()
    if "syracuse" in jur or "syracuse" in agency:
        score += 10
        why.append("+10: Syracuse/local administration.")
    elif "onondaga" in jur or "onondaga" in agency:
        score += 8
        why.append("+8: Onondaga County/local administration.")
    elif "nys" in jur or "new york" in jur or "hcr" in agency or "nyserda" in agency:
        score += 6
        why.append("+6: NY State program (often available locally).")
    else:
        score += 3
        why.append("+3: Non-local jurisdiction; verify local availability.")

    # --- Senior / Fixed-income keyword scan ---
    blob = " ".join([
        program.name or "",
        program.eligibility_summary or "",
        program.income_guidance or "",
        program.docs_checklist or "",
    ]).lower()

    if profile.is_senior:
        if "60" in blob or "62" in blob or "senior" in blob or "elderly" in blob:
            score += 8
            why.append("+8: Senior/age wording detected.")
        else:
            score += 2
            why.append("+2: Senior wording not detected; verify eligibility by phone.")

    if profile.is_fixed_income:
        if "income" in blob or "ami" in blob or "low income" in blob or "very-low" in blob:
            score += 6
            why.append("+6: Income-based wording detected.")
        else:
            score += 2
            why.append("+2: Income rules not stated; verify by phone.")

    # --- PriorityRank bump ---
    pr = program.priority_rank or 0.0
    if pr > 0:
        bump = int(min(10, pr / 10))
        if bump > 0:
            score += bump
            why.append(f"+{bump}: Incorporates existing PriorityRank ({pr}).")

    score = max(0, min(100, int(score)))
    why.append(f"Final Score: {score}/100 (heuristic triage).")
    return score, why
