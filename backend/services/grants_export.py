"""
Export engine for grants.

PDF  – reportlab, one card per grant with application checklist
CSV  – stdlib csv, all fields as flat rows
"""
import csv
import io
import logging
import traceback
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# ── Application checklist items per repair category ──────────────────────────
CHECKLIST_BY_CATEGORY = {
    "emergency_repairs": [
        "Proof of homeownership (deed or mortgage statement)",
        "Government-issued photo ID",
        "Most recent federal tax return",
        "Proof of income (pay stubs / Social Security / pension letters)",
        "Written description of emergency repair needed",
        "Two contractor estimates (if required by program)",
        "Proof of homeowners insurance",
        "Utility bills (last 3 months) – if relevant to repair",
    ],
    "energy_efficiency": [
        "Proof of homeownership",
        "Government-issued photo ID",
        "Most recent federal tax return",
        "Proof of income for all household members",
        "Recent utility bills (electric, gas – last 12 months)",
        "Completed energy audit report (if pre-required)",
        "Contractor/installer NYSERDA certification number",
        "Property tax bill (current year)",
    ],
    "accessibility": [
        "Proof of homeownership",
        "Government-issued photo ID",
        "Most recent federal tax return",
        "Proof of income for all household members",
        "Letter from physician or OT documenting disability/mobility need",
        "Written scope of accessibility modifications",
        "Two contractor estimates",
        "Property tax bill (current year)",
    ],
    "structural": [
        "Proof of homeownership",
        "Government-issued photo ID",
        "Most recent federal tax return",
        "Proof of income for all household members",
        "Property inspection report or code violation notice",
        "Two licensed contractor estimates",
        "Proof of homeowners insurance",
        "Property tax bill (current year)",
        "Mortgage statement (if applicable)",
    ],
    "historic_preservation": [
        "Proof of homeownership",
        "Government-issued photo ID",
        "Most recent federal tax return",
        "Proof of income for all household members",
        "Historic property designation certificate",
        "Pre-approved scope of work from SHPO (State Historic Preservation Office)",
        "Two contractor estimates from historically qualified contractors",
        "Photographs of current property condition",
        "Property tax bill (current year)",
    ],
}

DEFAULT_CHECKLIST = [
    "Proof of homeownership (deed or mortgage statement)",
    "Government-issued photo ID",
    "Most recent federal tax return",
    "Proof of income for all household members",
    "Property tax bill (current year)",
    "Homeowners insurance documentation",
    "Completed program application form",
]

STATUS_COLORS = {
    "open": (0.08, 0.53, 0.27),         # green
    "closing_soon": (0.87, 0.45, 0.04), # orange
    "closed": (0.75, 0.10, 0.10),       # red
}


def _get_checklist(repair_categories: list) -> list:
    if not repair_categories:
        return DEFAULT_CHECKLIST
    items = []
    seen = set()
    for cat in repair_categories:
        for item in CHECKLIST_BY_CATEGORY.get(cat, DEFAULT_CHECKLIST):
            if item not in seen:
                items.append(item)
                seen.add(item)
    return items or DEFAULT_CHECKLIST


def export_grants_csv(grants: list[dict]) -> io.StringIO:
    """
    Build an in-memory CSV from a list of grant dicts (as returned by
    match_grants or a plain to_dict() call).

    Returns a StringIO object ready to be read/streamed.
    """
    output = io.StringIO()
    if not grants:
        return output

    fieldnames = [
        "grant_name", "source", "status", "match_score",
        "amount_min", "amount_max", "deadline",
        "income_limit", "age_min", "age_max",
        "property_types", "repair_categories",
        "application_url", "last_verified",
        "agency_phone", "agency_email",
        "description",
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()

    for g in grants:
        row = dict(g)
        # Flatten list fields to semicolon-separated strings
        if isinstance(row.get("property_types"), list):
            row["property_types"] = "; ".join(row["property_types"])
        if isinstance(row.get("repair_categories"), list):
            row["repair_categories"] = "; ".join(row["repair_categories"])
        writer.writerow(row)

    output.seek(0)
    return output


def export_grants_pdf(grants: list[dict]) -> io.BytesIO:
    """
    Build a PDF report with one card per grant and a per-grant application
    checklist.  Returns a BytesIO buffer.

    Raises ImportError if reportlab is not installed.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            HRFlowable, PageBreak,
        )
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
    except ImportError as exc:
        raise ImportError(
            "reportlab is required for PDF export. Install it with: pip install reportlab"
        ) from exc

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    NAVY = colors.HexColor("#1a2744")
    TEAL = colors.HexColor("#0d9488")
    LIGHT_BG = colors.HexColor("#f0f4f8")
    WHITE = colors.white

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        textColor=NAVY,
        fontSize=22,
        spaceAfter=4,
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        textColor=TEAL,
        fontSize=10,
        spaceAfter=12,
        alignment=TA_CENTER,
    )
    grant_title_style = ParagraphStyle(
        "GrantTitle",
        parent=styles["Heading2"],
        textColor=NAVY,
        fontSize=14,
        spaceBefore=8,
        spaceAfter=4,
    )
    label_style = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        textColor=colors.HexColor("#6b7280"),
        fontSize=8,
        spaceAfter=1,
    )
    value_style = ParagraphStyle(
        "Value",
        parent=styles["Normal"],
        textColor=NAVY,
        fontSize=10,
        spaceAfter=6,
    )
    checklist_header_style = ParagraphStyle(
        "ChecklistHeader",
        parent=styles["Heading3"],
        textColor=TEAL,
        fontSize=11,
        spaceBefore=10,
        spaceAfter=4,
    )
    checklist_item_style = ParagraphStyle(
        "ChecklistItem",
        parent=styles["Normal"],
        fontSize=9,
        textColor=NAVY,
        leftIndent=12,
        spaceAfter=3,
    )
    url_style = ParagraphStyle(
        "URL",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#0369a1"),
        spaceAfter=6,
    )

    story = []

    # ── Cover page ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("SyrHousing Grant Report", title_style))
    story.append(
        Paragraph(
            f"Generated {datetime.now().strftime('%B %d, %Y')} · {len(grants)} grant(s) matched",
            subtitle_style,
        )
    )
    story.append(HRFlowable(width="100%", thickness=2, color=TEAL, spaceAfter=16))

    for idx, g in enumerate(grants):
        try:
            _build_grant_card(
                story, g, idx,
                grant_title_style, label_style, value_style,
                checklist_header_style, checklist_item_style, url_style,
                NAVY, TEAL, LIGHT_BG, WHITE,
                HRFlowable, Paragraph, Spacer, Table, TableStyle, PageBreak,
                inch, colors,
            )
        except Exception:
            logger.exception("Failed to render PDF card for grant %s", g.get("grant_name"))
            story.append(
                Paragraph(f"[Error rendering card for: {g.get('grant_name', 'Unknown')}]", value_style)
            )

    try:
        doc.build(story)
    except Exception:
        logger.exception("reportlab doc.build() failed")
        raise

    buffer.seek(0)
    return buffer


def _build_grant_card(
    story, g, idx,
    grant_title_style, label_style, value_style,
    checklist_header_style, checklist_item_style, url_style,
    NAVY, TEAL, LIGHT_BG, WHITE,
    HRFlowable, Paragraph, Spacer, Table, TableStyle, PageBreak,
    inch, colors,
):
    if idx > 0:
        story.append(PageBreak())

    # Grant title + score badge
    score = g.get("match_score")
    score_text = f" — Match: {score}%" if score is not None else ""
    story.append(
        Paragraph(f"{g.get('grant_name', 'Unknown Grant')}{score_text}", grant_title_style)
    )

    # Status badge via table
    status = g.get("status", "open")
    status_rgb = STATUS_COLORS.get(status, STATUS_COLORS["open"])
    badge_color = colors.Color(*status_rgb)
    badge_table = Table([[status.upper().replace("_", " ")]], colWidths=[1.2 * inch])
    badge_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), badge_color),
            ("TEXTCOLOR", (0, 0), (-1, -1), WHITE),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("ROUNDEDCORNERS", [4]),
        ])
    )
    story.append(badge_table)
    story.append(Spacer(1, 6))

    # Details grid
    def fmt_currency(v):
        if v is None:
            return "N/A"
        return f"${v:,.0f}"

    def fmt_list(v):
        if not v:
            return "Any"
        if isinstance(v, list):
            return ", ".join(v).replace("_", " ").title()
        return str(v)

    details = [
        ("Source / Agency", g.get("source") or "N/A"),
        (
            "Funding Amount",
            f"{fmt_currency(g.get('amount_min'))} – {fmt_currency(g.get('amount_max'))}",
        ),
        ("Deadline", g.get("deadline") or "Rolling / Contact agency"),
        ("Income Limit", fmt_currency(g.get("income_limit"))),
        (
            "Age Requirement",
            f"{g.get('age_min') or 'Any'} – {g.get('age_max') or 'Any'}",
        ),
        ("Eligible Property Types", fmt_list(g.get("property_types"))),
        ("Repair Categories", fmt_list(g.get("repair_categories"))),
        ("Phone", g.get("agency_phone") or "N/A"),
        ("Email", g.get("agency_email") or "N/A"),
        ("Last Verified", str(g.get("last_verified") or "N/A")[:10]),
    ]

    grid_data = []
    for label, val in details:
        grid_data.append(
            [
                Paragraph(label, label_style),
                Paragraph(str(val), value_style),
            ]
        )

    grid = Table(grid_data, colWidths=[1.8 * inch, 5.0 * inch])
    grid.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, LIGHT_BG]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.append(grid)
    story.append(Spacer(1, 8))

    # Description
    if g.get("description"):
        story.append(Paragraph(g["description"], value_style))
        story.append(Spacer(1, 6))

    # Eligibility notes
    ec = g.get("eligibility_criteria", {})
    if ec:
        notes_parts = []
        if ec.get("requires_owner_occupied"):
            notes_parts.append("Owner-occupied property required")
        if ec.get("requires_primary_residence"):
            notes_parts.append("Primary residence required")
        if ec.get("geographic_restriction"):
            notes_parts.append(f"Geographic restriction: {ec['geographic_restriction']}")
        if ec.get("first_time_buyer_required"):
            notes_parts.append("First-time homebuyer required")
        if ec.get("additional_notes"):
            notes_parts.append(ec["additional_notes"])
        if notes_parts:
            story.append(
                Paragraph("Eligibility Notes: " + " · ".join(notes_parts), value_style)
            )
            story.append(Spacer(1, 6))

    # Application URL
    url = g.get("application_url")
    if url:
        story.append(Paragraph(f"Apply at: {url}", url_style))

    # Application checklist
    repair_cats = g.get("repair_categories") or []
    checklist = _get_checklist(repair_cats)

    story.append(HRFlowable(width="100%", thickness=1, color=TEAL, spaceAfter=4))
    story.append(Paragraph("Application Checklist", checklist_header_style))
    for item in checklist:
        story.append(Paragraph(f"☐  {item}", checklist_item_style))
