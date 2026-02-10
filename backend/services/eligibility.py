"""
AI-powered eligibility screening service.
Builds context from program database + user profile, sends to LLM
for natural-language eligibility analysis and grant matching.
Falls back to offline chatbot when no LLM is configured.
"""

from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from ..models.program import Program
from ..models.user_profile import UserProfile
from ..models.scan import ScanState
from .llm import is_llm_available, chat_completion
from .chatbot import chatbot_answer
from .ranking import compute_rank

SYSTEM_PROMPT = """You are the SyrHousing Grant Assistant, an AI advisor for DJ AI Business Consultant.
You help Syracuse-area seniors and homeowners find home repair grants and assistance programs.

Your role:
- Analyze the user's home profile and repair needs against available programs
- Explain eligibility requirements in plain, friendly language
- Recommend the best-fit programs with clear reasoning
- Provide actionable next steps (who to call, what documents to gather)
- Be honest when a program may not be a good fit

Important guidelines:
- Always be encouraging but honest about eligibility likelihood
- Mention specific phone numbers and agencies when available
- If unsure about eligibility, recommend the user call the agency to verify
- Focus on grants and free assistance before loans
- Remember this is for Syracuse/Onondaga County, NY area
- Keep responses concise and practical"""


def _build_programs_context(db: Session, profile: UserProfile, limit: int = 15) -> str:
    """Build a text summary of the most relevant programs for the LLM context."""
    programs = db.query(Program).filter(Program.is_active == True).all()

    # Rank and sort
    ranked = []
    for p in programs:
        score, why = compute_rank(p, profile)
        ranked.append((score, p, why))
    ranked.sort(key=lambda x: x[0], reverse=True)

    lines = []
    for score, p, why in ranked[:limit]:
        lines.append(f"[{p.name}] (score: {score}/100)")
        lines.append(f"  Key: {p.program_key}")
        lines.append(f"  Category: {p.menu_category}")
        if p.program_type:
            lines.append(f"  Type: {p.program_type}")
        if p.max_benefit:
            lines.append(f"  Benefit: {p.max_benefit}")
        if p.status_or_deadline:
            lines.append(f"  Status: {p.status_or_deadline}")
        if p.agency:
            lines.append(f"  Agency: {p.agency}")
        if p.phone:
            lines.append(f"  Phone: {p.phone}")
        if p.website:
            lines.append(f"  Website: {p.website}")
        if p.repair_tags:
            lines.append(f"  Repair Tags: {p.repair_tags}")
        if p.eligibility_summary:
            lines.append(f"  Eligibility: {p.eligibility_summary}")
        if p.income_guidance:
            lines.append(f"  Income Guidance: {p.income_guidance}")
        # Top 3 ranking reasons
        lines.append(f"  Ranking: {'; '.join(why[:3])}")
        lines.append("")

    return "\n".join(lines)


def _build_profile_context(profile: UserProfile) -> str:
    """Build a text summary of the user's profile."""
    needs = ", ".join(profile.repair_needs or [])
    severity_parts = []
    for tag, score in (profile.repair_severity or {}).items():
        severity_parts.append(f"{tag}={score}/10")
    severity = ", ".join(severity_parts) if severity_parts else "not specified"

    return (
        f"Location: {profile.city}, {profile.county} County, NY\n"
        f"Senior (60+): {'Yes' if profile.is_senior else 'No'}\n"
        f"Fixed Income: {'Yes' if profile.is_fixed_income else 'No'}\n"
        f"Repair Needs: {needs or 'not specified'}\n"
        f"Severity Scores: {severity}"
    )


def _build_scan_context(db: Session) -> str:
    """Build brief scan status context."""
    states = db.query(ScanState).all()
    if not states:
        return "No scan data available."

    open_count = sum(1 for s in states if s.status == "open/unknown")
    closed_count = sum(1 for s in states if s.status == "closed")

    lines = [f"Monitoring {len(states)} program websites: {open_count} appear open, {closed_count} appear closed."]
    for s in states:
        if s.status == "closed":
            lines.append(f"  NOTE: {s.name} appears CLOSED as of last scan.")
    return "\n".join(lines)


def ai_chat(
    question: str,
    db: Session,
    profile: UserProfile,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> Tuple[str, bool]:
    """
    Process a user question through the AI eligibility screening system.

    Returns: (answer_text, used_llm)
    - If LLM is available: sends full context + conversation to LLM
    - If not: falls back to offline chatbot
    """
    if not is_llm_available():
        answer, _ = chatbot_answer(question, db, profile)
        return answer, False

    # Build context for the LLM
    profile_ctx = _build_profile_context(profile)
    programs_ctx = _build_programs_context(db, profile)
    scan_ctx = _build_scan_context(db)

    context_message = (
        f"--- USER HOME PROFILE ---\n{profile_ctx}\n\n"
        f"--- AVAILABLE PROGRAMS (ranked by relevance) ---\n{programs_ctx}\n"
        f"--- SCAN STATUS ---\n{scan_ctx}\n\n"
        f"Use the above data to answer the user's question. "
        f"Reference specific programs by name, include phone numbers and websites when relevant. "
        f"If a program appears closed per scan status, mention that and suggest calling to confirm."
    )

    # Build message history
    messages = []

    # Include context as first user message if no history
    if conversation_history:
        # Inject context into the start of conversation
        messages.append({"role": "user", "content": context_message + "\n\n(This is background context, not a question.)"})
        messages.append({"role": "assistant", "content": "I have the program data and your profile. How can I help?"})
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": question})
    else:
        messages.append({"role": "user", "content": context_message + f"\n\nUser question: {question}"})

    answer = chat_completion(SYSTEM_PROMPT, messages)
    return answer, True


def screen_eligibility(
    program_key: str,
    db: Session,
    profile: UserProfile,
) -> Tuple[str, bool]:
    """
    Deep eligibility screening for a specific program.
    Returns: (screening_text, used_llm)
    """
    program = db.query(Program).filter(
        Program.program_key == program_key, Program.is_active == True
    ).first()

    if not program:
        return "Program not found.", False

    if not is_llm_available():
        # Offline fallback: use ranking explanation
        score, why = compute_rank(program, profile)
        lines = [
            f"Eligibility Screening: {program.name}",
            f"AI Score: {score}/100",
            "",
            "Ranking Factors:",
        ]
        lines.extend([f"- {w}" for w in why])
        lines.append("")
        lines.append("For detailed eligibility, call the agency directly:")
        if program.phone:
            lines.append(f"  Phone: {program.phone}")
        if program.website:
            lines.append(f"  Website: {program.website}")
        return "\n".join(lines), False

    profile_ctx = _build_profile_context(profile)
    score, why = compute_rank(program, profile)

    scan_state = db.query(ScanState).filter(ScanState.program_key == program_key).first()
    scan_note = ""
    if scan_state:
        scan_note = f"Last scan status: {scan_state.status} (checked: {scan_state.last_checked})"

    program_detail = (
        f"Program: {program.name}\n"
        f"Category: {program.menu_category}\n"
        f"Type: {program.program_type or 'Not specified'}\n"
        f"Benefit: {program.max_benefit or 'Varies'}\n"
        f"Status: {program.status_or_deadline or 'Unknown'}\n"
        f"Agency: {program.agency or 'Unknown'}\n"
        f"Phone: {program.phone or 'N/A'}\n"
        f"Website: {program.website or 'N/A'}\n"
        f"Repair Tags: {program.repair_tags or 'None'}\n"
        f"Eligibility Summary: {program.eligibility_summary or 'Not available'}\n"
        f"Income Guidance: {program.income_guidance or 'Not available'}\n"
        f"Docs Checklist: {program.docs_checklist or 'Not available'}\n"
        f"AI Score: {score}/100\n"
        f"Score Breakdown: {'; '.join(why)}\n"
        f"{scan_note}"
    )

    prompt = (
        f"--- USER HOME PROFILE ---\n{profile_ctx}\n\n"
        f"--- PROGRAM DETAILS ---\n{program_detail}\n\n"
        f"Please provide a detailed eligibility screening for this user and program. Include:\n"
        f"1. Likelihood assessment (Good fit / Possible fit / Unlikely fit)\n"
        f"2. Key eligibility factors that match or don't match\n"
        f"3. Specific documents the user should prepare\n"
        f"4. Recommended next steps with the specific phone number to call\n"
        f"5. Questions the user should ask when they call\n"
        f"Be practical and direct."
    )

    messages = [{"role": "user", "content": prompt}]
    answer = chat_completion(SYSTEM_PROMPT, messages, max_tokens=1500)
    return answer, True
