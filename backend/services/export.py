"""
Export service for generating PDF and CSV reports of grants and applications.
Provides downloadable reports with matching grants, eligibility details, and application checklists.
"""

import csv
import io
from datetime import datetime
from typing import List, Dict, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

from ..models.program import Program
from ..models.user_profile import UserProfile
from .ranking import compute_rank


def generate_csv_export(programs: List[Program], profile: Optional[UserProfile] = None) -> str:
    """
    Generate CSV export of programs.
    If profile provided, includes match score.
    Returns CSV as string.
    """
    output = io.StringIO()

    # Define CSV columns
    fieldnames = [
        'Grant Name',
        'Program Type',
        'Category',
        'Maximum Benefit',
        'Status/Deadline',
        'Agency',
        'Phone',
        'Email',
        'Website',
        'Eligibility Summary',
        'Income Guidance',
        'Repair Tags',
    ]

    if profile:
        fieldnames.insert(1, 'Match Score')

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for program in programs:
        row = {
            'Grant Name': program.name,
            'Program Type': program.program_type or '',
            'Category': program.menu_category,
            'Maximum Benefit': program.max_benefit or '',
            'Status/Deadline': program.status_or_deadline or '',
            'Agency': program.agency or '',
            'Phone': program.phone or '',
            'Email': program.email or '',
            'Website': program.website or '',
            'Eligibility Summary': program.eligibility_summary or '',
            'Income Guidance': program.income_guidance or '',
            'Repair Tags': program.repair_tags or '',
        }

        if profile:
            score, _ = compute_rank(program, profile)
            row['Match Score'] = f"{score}/100"

        writer.writerow(row)

    return output.getvalue()


def generate_pdf_report(
    programs: List[Program],
    profile: Optional[UserProfile] = None,
    title: str = "Syracuse Housing Grant Report"
) -> bytes:
    """
    Generate comprehensive PDF report of matching grants.
    Returns PDF as bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch,
    )

    # Container for the 'Flowable' objects
    elements = []

    # Define styles
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=12,
        alignment=TA_CENTER,
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=6,
        spaceBefore=12,
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_LEFT,
    )

    # Add title
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 0.2*inch))

    # Add generation date
    date_text = f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
    elements.append(Paragraph(date_text, normal_style))
    elements.append(Spacer(1, 0.3*inch))

    # Add profile summary if provided
    if profile:
        elements.append(Paragraph("Your Profile", heading_style))

        profile_data = [
            ['Location:', f"{profile.city}, {profile.county} County, NY"],
            ['Senior (60+):', 'Yes' if profile.is_senior else 'No'],
            ['Fixed Income:', 'Yes' if profile.is_fixed_income else 'No'],
        ]

        if profile.repair_needs:
            repair_needs_str = ', '.join(profile.repair_needs)
            profile_data.append(['Repair Needs:', repair_needs_str])

        profile_table = Table(profile_data, colWidths=[1.5*inch, 5*inch])
        profile_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e5e7eb')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))

        elements.append(profile_table)
        elements.append(Spacer(1, 0.3*inch))

    # Add summary
    elements.append(Paragraph(f"Matching Grants: {len(programs)}", heading_style))
    elements.append(Spacer(1, 0.1*inch))

    # Sort programs by match score if profile provided
    if profile:
        programs_with_scores = []
        for program in programs:
            score, why = compute_rank(program, profile)
            programs_with_scores.append((score, program, why))
        programs_with_scores.sort(key=lambda x: x[0], reverse=True)
    else:
        programs_with_scores = [(0, program, []) for program in programs]

    # Add each program
    for idx, (score, program, why) in enumerate(programs_with_scores, 1):
        # Program header
        if profile:
            header_text = f"{idx}. {program.name} - Match: {score}/100"
        else:
            header_text = f"{idx}. {program.name}"

        elements.append(Paragraph(header_text, heading_style))

        # Program details table
        details_data = []

        if program.program_type:
            details_data.append(['Type:', program.program_type])

        if program.max_benefit:
            details_data.append(['Maximum Benefit:', program.max_benefit])

        if program.status_or_deadline:
            details_data.append(['Status/Deadline:', program.status_or_deadline])

        if program.agency:
            details_data.append(['Agency:', program.agency])

        if program.phone:
            details_data.append(['Phone:', program.phone])

        if program.email:
            details_data.append(['Email:', program.email])

        if program.website:
            details_data.append(['Website:', program.website])

        if details_data:
            details_table = Table(details_data, colWidths=[1.5*inch, 5*inch])
            details_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(details_table)
            elements.append(Spacer(1, 0.1*inch))

        # Eligibility summary
        if program.eligibility_summary:
            elements.append(Paragraph("<b>Eligibility:</b>", normal_style))
            elements.append(Paragraph(program.eligibility_summary, normal_style))
            elements.append(Spacer(1, 0.05*inch))

        # Income guidance
        if program.income_guidance:
            elements.append(Paragraph("<b>Income Requirements:</b>", normal_style))
            elements.append(Paragraph(program.income_guidance, normal_style))
            elements.append(Spacer(1, 0.05*inch))

        # Application checklist
        if program.docs_checklist:
            elements.append(Paragraph("<b>Documents Needed:</b>", normal_style))

            # Parse checklist items
            checklist_items = program.docs_checklist.split(';')
            for item in checklist_items:
                item = item.strip()
                if item:
                    elements.append(Paragraph(f"☐ {item}", normal_style))
            elements.append(Spacer(1, 0.05*inch))

        # Match reasoning if profile provided
        if profile and why:
            elements.append(Paragraph("<b>Why this matches your needs:</b>", normal_style))
            for reason in why[:5]:  # Top 5 reasons
                elements.append(Paragraph(f"• {reason}", normal_style))

        # Add space between programs
        elements.append(Spacer(1, 0.2*inch))

        # Page break after every 2 programs for better readability
        if idx % 2 == 0 and idx < len(programs_with_scores):
            elements.append(PageBreak())

    # Add footer
    elements.append(Spacer(1, 0.3*inch))
    footer_text = (
        "<i>This report is generated by SyrHousing Grant Agent. "
        "Information is current as of the generation date. "
        "Please contact agencies directly to confirm program availability and requirements.</i>"
    )
    elements.append(Paragraph(footer_text, normal_style))

    # Build PDF
    doc.build(elements)

    # Get PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes


def generate_application_checklist_pdf(program: Program, profile: Optional[UserProfile] = None) -> bytes:
    """
    Generate a detailed application checklist PDF for a specific grant program.
    Returns PDF as bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch,
    )

    elements = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=12,
        alignment=TA_CENTER,
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=6,
        spaceBefore=12,
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_LEFT,
    )

    # Add title
    title_text = f"Application Checklist: {program.name}"
    elements.append(Paragraph(title_text, title_style))
    elements.append(Spacer(1, 0.2*inch))

    # Add date
    date_text = f"Prepared: {datetime.now().strftime('%B %d, %Y')}"
    elements.append(Paragraph(date_text, normal_style))
    elements.append(Spacer(1, 0.3*inch))

    # Program overview
    elements.append(Paragraph("Program Overview", heading_style))

    overview_data = [
        ['Agency:', program.agency or 'N/A'],
        ['Phone:', program.phone or 'N/A'],
        ['Email:', program.email or 'N/A'],
        ['Website:', program.website or 'N/A'],
        ['Maximum Benefit:', program.max_benefit or 'Varies'],
        ['Deadline:', program.status_or_deadline or 'Check with agency'],
    ]

    overview_table = Table(overview_data, colWidths=[1.5*inch, 5*inch])
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e5e7eb')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(overview_table)
    elements.append(Spacer(1, 0.3*inch))

    # Eligibility
    if program.eligibility_summary:
        elements.append(Paragraph("Eligibility Requirements", heading_style))
        elements.append(Paragraph(program.eligibility_summary, normal_style))
        elements.append(Spacer(1, 0.2*inch))

    # Income requirements
    if program.income_guidance:
        elements.append(Paragraph("Income Requirements", heading_style))
        elements.append(Paragraph(program.income_guidance, normal_style))
        elements.append(Spacer(1, 0.2*inch))

    # Document checklist
    elements.append(Paragraph("Required Documents Checklist", heading_style))
    elements.append(Paragraph("Gather the following documents before applying:", normal_style))
    elements.append(Spacer(1, 0.1*inch))

    if program.docs_checklist:
        checklist_items = program.docs_checklist.split(';')
        for item in checklist_items:
            item = item.strip()
            if item:
                elements.append(Paragraph(f"☐ {item}", normal_style))
                elements.append(Spacer(1, 0.05*inch))
    else:
        # Default checklist
        default_docs = [
            "Proof of ownership (property deed)",
            "Photo identification (driver's license or state ID)",
            "Proof of income (pay stubs, tax returns, Social Security statements)",
            "Recent utility bills",
            "Repair estimates or contractor bids",
            "Proof of homeowner's insurance (if applicable)",
        ]
        for doc in default_docs:
            elements.append(Paragraph(f"☐ {doc}", normal_style))
            elements.append(Spacer(1, 0.05*inch))

    elements.append(Spacer(1, 0.3*inch))

    # Application steps
    elements.append(Paragraph("Application Steps", heading_style))

    steps = [
        "1. Review all eligibility requirements carefully",
        "2. Gather all required documents listed above",
        "3. Contact the agency to confirm program availability",
        "4. Schedule an intake appointment if required",
        "5. Complete the application form",
        "6. Submit application with all supporting documents",
        "7. Follow up on application status",
    ]

    for step in steps:
        elements.append(Paragraph(step, normal_style))
        elements.append(Spacer(1, 0.05*inch))

    elements.append(Spacer(1, 0.3*inch))

    # Important notes
    elements.append(Paragraph("Important Notes", heading_style))
    notes = [
        "• Call the agency before applying to confirm program is currently accepting applications",
        "• Ask about current funding availability and estimated wait times",
        "• Keep copies of all documents you submit",
        "• Note the name of the person you speak with and date of contact",
        "• Ask for a confirmation number or receipt when submitting your application",
    ]

    for note in notes:
        elements.append(Paragraph(note, normal_style))
        elements.append(Spacer(1, 0.05*inch))

    # Match information if profile provided
    if profile:
        score, why = compute_rank(program, profile)
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph(f"Your Match Score: {score}/100", heading_style))
        if why:
            for reason in why[:5]:
                elements.append(Paragraph(f"• {reason}", normal_style))

    # Build PDF
    doc.build(elements)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes
