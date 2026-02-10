"""
Port of chatbot_answer() from agent_gui.py:225-284.
Same rapidfuzz / token-overlap matching.
Searches ALL programs, not just filtered subset (fixes agent_gui.py:796 bug).
Gets latest scan info from DB instead of file.
"""

import re
from typing import List, Tuple, Set, Optional

from sqlalchemy.orm import Session

from ..models.program import Program
from ..models.user_profile import UserProfile
from .ranking import compute_rank
from .scanner import build_latest_report

try:
    from rapidfuzz import fuzz, process  # type: ignore
    HAS_RAPIDFUZZ = True
except Exception:
    HAS_RAPIDFUZZ = False


def program_text(p: Program) -> str:
    parts = [
        p.name, p.menu_category, p.program_type, p.repair_tags, p.max_benefit,
        p.status_or_deadline, p.agency, p.eligibility_summary, p.income_guidance,
        p.docs_checklist, p.website,
    ]
    return " ".join([str(x) for x in parts if x])


def tokenize(text: str) -> Set[str]:
    text = (text or "").lower()
    return set(re.findall(r"[a-z0-9']{3,}", text))


def best_program_matches(
    question: str,
    programs: List[Program],
    limit: int = 5,
) -> List[Tuple[int, Program]]:
    q = question.strip()
    if not q:
        return []

    if HAS_RAPIDFUZZ:
        choices = {p.program_key: program_text(p) for p in programs}
        key_to_prog = {p.program_key: p for p in programs}
        res = process.extract(q, choices, scorer=fuzz.WRatio, limit=limit)
        out: List[Tuple[int, Program]] = []
        for (_text, score, key) in res:
            prog = key_to_prog.get(key)
            if prog:
                out.append((int(score), prog))
        return out

    qtok = tokenize(q)
    scored: List[Tuple[int, Program]] = []
    for p in programs:
        ptok = tokenize(program_text(p))
        inter = len(qtok.intersection(ptok))
        denom = max(1, len(qtok))
        score = int(100 * (inter / denom))
        scored.append((score, p))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:limit]


def chatbot_answer(
    question: str,
    db: Session,
    profile: UserProfile,
) -> Tuple[str, List[dict]]:
    q = question.strip()
    if not q:
        return (
            "Ask about roof/heating/structural programs, lead, accessibility, weatherization, or how to apply.",
            [],
        )

    programs = db.query(Program).filter(Program.is_active == True).all()
    matches = best_program_matches(q, programs, limit=5)
    scan_text = build_latest_report(db)

    lines: List[str] = []
    lines.append("Local Grant Agent (offline mode)\n")

    repair_needs = profile.repair_needs or []
    lines.append(
        f"Profile: senior={profile.is_senior}, fixed_income={profile.is_fixed_income}, "
        f"repairs={repair_needs}\n"
    )
    lines.append("\nTop matches:\n")

    matched_programs: List[dict] = []

    if not matches:
        lines.append("- No strong matches. Try: roof, furnace, heating, structural, lead, ramps, weatherization.\n")
    else:
        for match_score, p in matches:
            rank, why = compute_rank(p, profile)
            lines.append(f"\n[{p.name}]")
            lines.append(f"\n  MatchScore: {match_score}/100 | Rank: {rank}/100")
            lines.append(f"\n  Category: {p.menu_category} | Type: {p.program_type or ''}")
            lines.append(f"\n  Benefit: {p.max_benefit or ''} | Status: {p.status_or_deadline or ''}")
            lines.append(f"\n  Agency: {p.agency or ''} | Phone: {p.phone or ''}")
            lines.append(f"\n  Website: {p.website or ''}")
            lines.append("\n  Why: " + "; ".join(why[:4]) + "\n")

            matched_programs.append({
                "program_key": p.program_key,
                "name": p.name,
                "match_score": match_score,
                "rank_score": rank,
                "category": p.menu_category,
                "program_type": p.program_type,
                "max_benefit": p.max_benefit,
                "status": p.status_or_deadline,
                "agency": p.agency,
                "phone": p.phone,
                "website": p.website,
                "rank_explanation": why,
            })

    if scan_text:
        snippet = scan_text[:800].strip()
        lines.append("\nLatest scan context (snippet):\n")
        lines.append(snippet + ("\n...\n" if len(scan_text) > 800 else "\n"))

    lines.append("\nNext step:\n- If you share household size + approximate income, I can guide what to ask agencies to confirm eligibility.\n")
    return "".join(lines), matched_programs
