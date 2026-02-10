"""
Port of checklist_text() from agent_gui.py:289-331.
Returns checklist text string. PDF generation deferred to Phase 2.
"""

from datetime import datetime
from typing import List

from ..models.program import Program
from ..models.user_profile import UserProfile


def checklist_text(program: Program, profile: UserProfile) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    needs = ", ".join(profile.repair_needs or [])

    lines: List[str] = []
    lines.append("SYRHOUSING – PROGRAM CHECKLIST\n")
    lines.append("=" * 36 + "\n")
    lines.append(f"Generated: {now}\n\n")
    lines.append(f"Program: {program.name}\n")
    lines.append(f"Agency:  {program.agency or ''}\n")
    lines.append(f"Phone:   {program.phone or ''}\n")
    lines.append(f"Website: {program.website or ''}\n")
    lines.append(f"Benefit: {program.max_benefit or ''}\n")
    lines.append(f"Status:  {program.status_or_deadline or ''}\n")

    lines.append("\nYour home profile:\n")
    lines.append(f"- Senior: {profile.is_senior}\n")
    lines.append(f"- Fixed income: {profile.is_fixed_income}\n")
    lines.append(f"- Repairs needed: {needs}\n")

    lines.append("\nEligibility (database):\n")
    lines.append((program.eligibility_summary or "(blank)").strip() + "\n")

    lines.append("\nIncome guidance (database):\n")
    lines.append((program.income_guidance or "(blank)").strip() + "\n")

    lines.append("\nDocument checklist:\n")
    docs = (program.docs_checklist or "").strip()
    if docs:
        lines.append(docs + "\n")
    else:
        lines.append("- Photo ID\n")
        lines.append("- Proof of ownership / purchase contract\n")
        lines.append("- Proof of income (SSA award letter, pension)\n")
        lines.append("- Contractor estimates for roof/heating/structural\n")
        lines.append("- Photos of problem areas\n")

    lines.append("\nCall script (questions):\n")
    lines.append("1) Are applications open now? Next intake date?\n")
    lines.append("2) Do roof/heating/structural repairs qualify? Any caps?\n")
    lines.append("3) Grant vs deferred loan vs loan? Any lien/forgiveness?\n")
    lines.append("4) Income limit (AMI %, household size)?\n")
    lines.append("5) Timeline and emergency-track options?\n")
    return "".join(lines)
