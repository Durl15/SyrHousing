"""
AI-powered grant writing service.
Generates professional grant application content (cover letters, eligibility statements,
project descriptions) using LLM or template fallbacks.
"""

from typing import Tuple
from sqlalchemy.orm import Session
import json

from ..models.application import Application
from ..models.program import Program
from ..models.user_profile import UserProfile
from .llm import is_llm_available, chat_completion

GRANT_WRITER_SYSTEM_PROMPT = """You are a professional grant writer specializing in housing assistance applications for Syracuse, NY area residents. Your role is to help homeowners craft compelling, honest, and professional application materials.

Guidelines:
- Write in first person from the applicant's perspective
- Be professional but personal - show genuine need
- Emphasize safety concerns and urgent repairs
- Highlight fixed income/financial constraints appropriately
- Reference specific program requirements
- Keep cover letters to 2-3 paragraphs
- Never exaggerate or fabricate information
- Use respectful, dignified language about financial need

Your output should be ready to use with minimal editing."""


def _build_profile_summary(profile: UserProfile) -> str:
    """Build a concise summary of user profile for LLM context."""
    parts = []
    parts.append(f"Location: {profile.city}, {profile.county} County, NY")

    if profile.is_senior:
        parts.append("Age: 60+ (Senior)")

    if profile.is_fixed_income:
        parts.append("Income Status: Fixed income")

    if profile.repair_needs:
        needs_list = ", ".join(profile.repair_needs[:5])
        parts.append(f"Repair Needs: {needs_list}")

        if profile.repair_severity:
            high_severity = [need for need, sev in profile.repair_severity.items() if sev >= 7]
            if high_severity:
                parts.append(f"Urgent Repairs: {', '.join(high_severity)}")

    return "\n".join(parts)


def _build_program_summary(program: Program) -> str:
    """Build a concise summary of program requirements for LLM context."""
    parts = []
    parts.append(f"Program: {program.name}")
    parts.append(f"Agency: {program.agency or 'N/A'}")
    parts.append(f"Type: {program.program_type or 'Housing assistance'}")
    parts.append(f"Max Benefit: {program.max_benefit or 'Varies'}")

    if program.eligibility_summary:
        parts.append(f"\nEligibility Requirements:\n{program.eligibility_summary}")

    if program.income_guidance:
        parts.append(f"\nIncome Requirements:\n{program.income_guidance}")

    if program.repair_tags:
        parts.append(f"\nCovered Repairs: {program.repair_tags}")

    if program.docs_checklist:
        parts.append(f"\nRequired Documents:\n{program.docs_checklist}")

    return "\n".join(parts)


def generate_cover_letter(
    db: Session,
    application_id: str,
    user_profile: UserProfile
) -> Tuple[str, bool]:
    """Generate a cover letter for the grant application."""
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise ValueError("Application not found")

    program = db.query(Program).filter(Program.program_key == app.program_key).first()
    if not program:
        raise ValueError("Program not found")

    # Check if LLM available
    if not is_llm_available():
        return _offline_cover_letter(user_profile, program), False

    # Build context
    profile_ctx = _build_profile_summary(user_profile)
    program_ctx = _build_program_summary(program)

    prompt = f"""Generate a professional cover letter for a grant application.

USER PROFILE:
{profile_ctx}

PROGRAM APPLYING TO:
{program_ctx}

REQUIREMENTS:
- Write in first person
- 2-3 paragraphs maximum
- Professional but warm tone
- Express genuine need without overstating
- Mention specific repair needs if relevant
- Reference fixed income if applicable
- Close with readiness to provide more information
- Do not use placeholders like [Your Name] or [Date] - write the letter content only

Format as ready-to-use letter content (no brackets or placeholders)."""

    messages = [{"role": "user", "content": prompt}]
    try:
        content = chat_completion(GRANT_WRITER_SYSTEM_PROMPT, messages, max_tokens=800)
        return content, True
    except Exception:
        # Fall back to template if LLM fails
        return _offline_cover_letter(user_profile, program), False


def generate_eligibility_statement(
    db: Session,
    application_id: str,
    user_profile: UserProfile
) -> Tuple[str, bool]:
    """Generate an eligibility statement matching profile to program requirements."""
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise ValueError("Application not found")

    program = db.query(Program).filter(Program.program_key == app.program_key).first()
    if not program:
        raise ValueError("Program not found")

    if not is_llm_available():
        return _offline_eligibility_statement(user_profile, program), False

    profile_ctx = _build_profile_summary(user_profile)

    prompt = f"""Generate a formal eligibility statement for a grant application.

USER PROFILE:
{profile_ctx}

PROGRAM ELIGIBILITY REQUIREMENTS:
{program.eligibility_summary or 'Requirements not specified'}

INCOME REQUIREMENTS:
{program.income_guidance or 'Income guidelines not specified'}

REPAIR ALIGNMENT:
Program covers: {program.repair_tags or 'Various repairs'}
User needs: {', '.join(user_profile.repair_needs or [])}

Create a point-by-point statement showing how the applicant meets requirements:
1. Location/jurisdiction eligibility
2. Age/senior status (if applicable)
3. Income level (fixed income status)
4. Property ownership/residence
5. Repair needs alignment with program scope

Use formal but clear language. Be factual and direct. Each point should be 1-2 sentences."""

    messages = [{"role": "user", "content": prompt}]
    try:
        content = chat_completion(GRANT_WRITER_SYSTEM_PROMPT, messages, max_tokens=1000)
        return content, True
    except Exception:
        return _offline_eligibility_statement(user_profile, program), False


def generate_project_description(
    db: Session,
    application_id: str,
    user_profile: UserProfile
) -> Tuple[str, bool]:
    """Generate a detailed project description of repair needs."""
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise ValueError("Application not found")

    program = db.query(Program).filter(Program.program_key == app.program_key).first()
    if not program:
        raise ValueError("Program not found")

    if not is_llm_available():
        return _offline_project_description(user_profile, program), False

    repair_needs = user_profile.repair_needs or []
    severity = user_profile.repair_severity or {}

    # Build detailed repair context
    repair_details = []
    for need in repair_needs:
        sev = severity.get(need, 5)
        repair_details.append(f"- {need}: Severity {sev}/10")

    repair_ctx = "\n".join(repair_details) if repair_details else "- General home repairs needed"

    prompt = f"""Generate a detailed project description for a home repair grant application.

USER INFORMATION:
Location: {user_profile.city}, {user_profile.county} County, NY
Senior: {'Yes (60+)' if user_profile.is_senior else 'No'}
Fixed Income: {'Yes' if user_profile.is_fixed_income else 'No'}

REPAIR NEEDS AND SEVERITY:
{repair_ctx}

PROGRAM SCOPE:
{program.repair_tags or 'Various home repairs'}

Write a narrative (3-4 paragraphs) that:
1. Describes current condition of home/systems needing repair
2. Explains safety concerns and why repairs are urgent
3. Details how issues impact daily life, health, or safety
4. Aligns with program's repair scope
5. Provides realistic scope of work needed

Use vivid but factual language. Focus on necessity and safety. Don't exaggerate."""

    messages = [{"role": "user", "content": prompt}]
    try:
        content = chat_completion(GRANT_WRITER_SYSTEM_PROMPT, messages, max_tokens=1500)
        return content, True
    except Exception:
        return _offline_project_description(user_profile, program), False


def generate_needs_justification(
    db: Session,
    application_id: str,
    user_profile: UserProfile
) -> Tuple[str, bool]:
    """Generate a needs justification explaining why assistance is needed."""
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise ValueError("Application not found")

    program = db.query(Program).filter(Program.program_key == app.program_key).first()
    if not program:
        raise ValueError("Program not found")

    if not is_llm_available():
        return _offline_needs_justification(user_profile, program), False

    profile_ctx = _build_profile_summary(user_profile)

    prompt = f"""Generate a needs justification statement for a grant application.

USER PROFILE:
{profile_ctx}

PROGRAM:
{program.name}
Max Benefit: {program.max_benefit or 'Varies'}

Write a 2-3 paragraph statement that:
1. Explains the applicant's financial situation and why they cannot afford repairs on their own
2. Describes the impact of delaying these repairs
3. Expresses how this grant would help them maintain their home safely
4. Uses respectful, dignified language about financial need

Be honest and factual. Emphasize the genuine need without exaggeration."""

    messages = [{"role": "user", "content": prompt}]
    try:
        content = chat_completion(GRANT_WRITER_SYSTEM_PROMPT, messages, max_tokens=1000)
        return content, True
    except Exception:
        return _offline_needs_justification(user_profile, program), False


# Offline fallback templates

def _offline_cover_letter(profile: UserProfile, program: Program) -> str:
    """Template-based cover letter when LLM unavailable."""
    senior_status = "senior (60+) " if profile.is_senior else ""
    income_status = "on a fixed income" if profile.is_fixed_income else "with limited financial resources"

    repair_needs = ", ".join(profile.repair_needs[:3]) if profile.repair_needs else "home maintenance"

    return f"""Dear {program.agency or 'Sir/Madam'},

I am writing to apply for the {program.name}. As a {senior_status}homeowner in {profile.city}, {profile.county} County, I am {income_status} and need assistance with critical home repairs including {repair_needs}.

These repairs are becoming increasingly urgent and affect the safety and livability of my home. Given my financial situation, I am unable to afford these necessary repairs without assistance. This program would provide vital support to help me maintain my home safely.

Thank you for considering my application. I am prepared to provide any additional documentation needed and look forward to hearing from you.

Sincerely,
[Your signature]"""


def _offline_eligibility_statement(profile: UserProfile, program: Program) -> str:
    """Template-based eligibility statement when LLM unavailable."""
    points = []

    points.append(f"1. Location: I am a homeowner residing in {profile.city}, {profile.county} County, which is within the program's service area.")

    if profile.is_senior:
        points.append("2. Age: I am 60 years of age or older, meeting the senior eligibility requirement.")

    if profile.is_fixed_income:
        income_point = "3. Income: I am on a fixed income, which qualifies me under the program's income guidelines."
        points.append(income_point)
    else:
        points.append("3. Income: My household income falls within the program's income limits.")

    points.append("4. Property: I own and occupy this property as my primary residence.")

    if profile.repair_needs:
        repair_list = ", ".join(profile.repair_needs[:3])
        points.append(f"5. Repair Needs: My home requires repairs in the following areas: {repair_list}, which align with the program's scope of covered repairs.")

    return "\n\n".join(points)


def _offline_project_description(profile: UserProfile, program: Program) -> str:
    """Template-based project description when LLM unavailable."""
    repair_needs = ", ".join(profile.repair_needs) if profile.repair_needs else "various home systems"

    severity_note = ""
    if profile.repair_severity:
        high_severity = [need for need, sev in profile.repair_severity.items() if sev >= 7]
        if high_severity:
            severity_note = f" The most urgent issues are {', '.join(high_severity)}."

    return f"""My home in {profile.city} requires critical repairs to {repair_needs}.{severity_note} These issues have developed over time and now present safety concerns that I cannot ignore.

The current condition of these systems affects my daily life and wellbeing. Without proper repairs, the situation will continue to deteriorate, potentially leading to more serious and costly problems. As a homeowner {' on a fixed income' if profile.is_fixed_income else ''}, I lack the financial resources to address these repairs on my own.

The scope of work needed includes assessment and repair of the affected systems to restore them to safe, functional condition. This will ensure my home remains livable and safe for years to come.

I am committed to working with qualified contractors and following all program requirements to ensure the repairs are completed properly and in compliance with local building codes."""


def _offline_needs_justification(profile: UserProfile, program: Program) -> str:
    """Template-based needs justification when LLM unavailable."""
    income_explanation = "As someone on a fixed income, " if profile.is_fixed_income else "With limited financial resources, "
    senior_note = " As a senior, maintaining a safe home environment is especially important for my health and independence." if profile.is_senior else ""

    return f"""{income_explanation}I do not have the financial means to pay for these necessary home repairs out of pocket. The costs of these repairs exceed my available savings and monthly budget, making it impossible to address them without assistance.

Delaying these repairs poses risks to my safety, health, and the long-term integrity of my home. What starts as a manageable issue can quickly become a more serious and expensive problem if left unaddressed.{senior_note}

The {program.name} would provide the critical financial assistance I need to make my home safe and livable. This support would not only address immediate safety concerns but also help me maintain my home and remain in my community for years to come. I am deeply grateful for programs like this that help homeowners in need."""
