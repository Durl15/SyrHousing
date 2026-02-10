"""
Data extraction and normalization for discovered grants.
Extracts structured information from raw grant data.
"""

import re
from typing import Dict
from datetime import datetime


def extract_grant_data(raw_grant: Dict, source_type: str) -> Dict:
    """
    Extract and normalize grant data from raw source data.

    Args:
        raw_grant: Raw grant data from source adapter
        source_type: Source identifier ("rss_feed", "grants_gov_api", "web_scrape")

    Returns:
        Dict: Normalized grant data with standardized fields

    Example:
        >>> raw = {"name": "Housing Grant - Up to $5,000", "source_url": "..."}
        >>> extracted = extract_grant_data(raw, "rss_feed")
        >>> print(extracted["max_benefit"])
        "$5,000"
    """
    extracted = {
        "source_type": source_type,
        "source_url": raw.get("source_url", ""),
        "source_id": raw.get("source_id"),
        "name": raw.get("name", "").strip(),
        "raw_data": str(raw),
    }

    # Extract from description/summary if available
    description = raw.get("description", "")

    # Extract benefit amount
    extracted["max_benefit"] = extract_benefit_amount(
        raw.get("name", "") + " " + description
    )

    # Extract deadline
    extracted["status_or_deadline"] = extract_deadline(
        description + " " + raw.get("name", "")
    )

    # Extract contact information
    phone = extract_phone(description)
    email = extract_email(description)
    if phone:
        extracted["phone"] = phone
    if email:
        extracted["email"] = email

    # Extract agency (from name or description)
    extracted["agency"] = extract_agency(raw.get("name", ""), description)

    # Classify jurisdiction
    extracted["jurisdiction"] = classify_jurisdiction(
        raw.get("name", "") + " " + description
    )

    # Assign menu category
    extracted["menu_category"] = classify_category(
        raw.get("name", "") + " " + description
    )

    # Use description as eligibility summary if substantial
    if description and len(description) > 100:
        extracted["eligibility_summary"] = description[:500]  # Truncate if too long

    return extracted


def extract_benefit_amount(text: str) -> str | None:
    """
    Extract benefit amount from text.

    Patterns: "$5,000", "up to $10,000", "$1,000-$5,000"

    Args:
        text: Text to search

    Returns:
        str or None: Extracted benefit amount
    """
    if not text:
        return None

    # Pattern: dollar amounts with optional "up to", "maximum", etc.
    patterns = [
        r'(?:up to|maximum of|max|grant of)\s*\$\s*([\d,]+)',
        r'\$\s*([\d,]+)\s*(?:grant|assistance|benefit)',
        r'\$\s*([\d,]+(?:\s*-\s*\$?\s*[\d,]+)?)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount = match.group(1)
            # Clean up formatting
            return f"${amount}"

    return None


def extract_deadline(text: str) -> str | None:
    """
    Extract deadline from text.

    Formats: MM/DD/YYYY, Month DD, YYYY, "December 31, 2025"

    Args:
        text: Text to search

    Returns:
        str or None: Extracted deadline
    """
    if not text:
        return None

    # Pattern 1: MM/DD/YYYY or MM-DD-YYYY
    match = re.search(r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b', text)
    if match:
        return match.group(1)

    # Pattern 2: Month DD, YYYY
    months = '|'.join([
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December',
        'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ])
    match = re.search(
        rf'\b({months})\s+(\d{{1,2}}),?\s+(\d{{4}})\b',
        text,
        re.IGNORECASE
    )
    if match:
        return f"{match.group(1)} {match.group(2)}, {match.group(3)}"

    # Pattern 3: Keywords like "deadline", "due", "closes"
    deadline_pattern = r'(?:deadline|due|closes|close date|application period ends):\s*([^\n\.]+)'
    match = re.search(deadline_pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()[:100]  # Limit length

    return None


def extract_phone(text: str) -> str | None:
    """
    Extract phone number from text.

    Formats: (315) 555-1234, 315-555-1234, 315.555.1234

    Args:
        text: Text to search

    Returns:
        str or None: Extracted phone number
    """
    if not text:
        return None

    # Pattern: various phone formats
    patterns = [
        r'\((\d{3})\)\s*(\d{3})-(\d{4})',  # (315) 555-1234
        r'(\d{3})-(\d{3})-(\d{4})',         # 315-555-1234
        r'(\d{3})\.(\d{3})\.(\d{4})',       # 315.555.1234
        r'(\d{3})\s+(\d{3})\s+(\d{4})',     # 315 555 1234
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return f"({match.group(1)}) {match.group(2)}-{match.group(3)}"

    return None


def extract_email(text: str) -> str | None:
    """
    Extract email address from text.

    Args:
        text: Text to search

    Returns:
        str or None: Extracted email address
    """
    if not text:
        return None

    # Pattern: email addresses
    match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    if match:
        return match.group(0).lower()

    return None


def extract_agency(name: str, description: str) -> str | None:
    """
    Extract agency name from grant name or description.

    Args:
        name: Grant name
        description: Grant description

    Returns:
        str or None: Extracted agency name
    """
    text = name + " " + description

    # Common agency patterns
    agency_patterns = [
        r'(?:administered by|offered by|provided by)\s+([^\.]+?)(?:\.|$)',
        r'(?:Department of|Office of)\s+([^\.]+?)(?:\.|$)',
        r'(?:HUD|USDA|NYS|State of New York)\s+([^\.]+?)(?:\.|$)',
    ]

    for pattern in agency_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            agency = match.group(1).strip()
            if len(agency) < 100:  # Reasonable length
                return agency

    return None


def classify_jurisdiction(text: str) -> str | None:
    """
    Classify jurisdiction based on keywords.

    Args:
        text: Text to analyze

    Returns:
        str or None: Jurisdiction classification
    """
    text_lower = text.lower()

    # Check for specific jurisdictions (most specific first)
    if 'syracuse' in text_lower:
        return "City of Syracuse"
    elif 'onondaga' in text_lower:
        return "Onondaga County"
    elif any(keyword in text_lower for keyword in ['new york state', 'nys', 'ny state']):
        return "New York State"
    elif any(keyword in text_lower for keyword in ['federal', 'hud', 'usda', 'national']):
        return "Federal"

    return None


def classify_category(text: str) -> str:
    """
    Classify grant into menu category based on keywords.

    Args:
        text: Text to analyze

    Returns:
        str: Menu category
    """
    text_lower = text.lower()

    # Category keyword mapping
    category_keywords = {
        "URGENT SAFETY": ["emergency", "urgent", "safety", "structural", "hazard", "dangerous"],
        "HEALTH HAZARDS": ["lead", "asbestos", "mold", "health", "toxic", "contamination"],
        "AGING IN PLACE": ["senior", "elderly", "aging", "accessibility", "ada", "disabled", "mobility"],
        "ENERGY & BILLS": ["energy", "weatherization", "efficiency", "insulation", "heating", "utility", "bills", "hvac"],
        "HISTORIC RESTORATION": ["historic", "heritage", "preservation", "restoration", "landmark"],
        "BUYING HELP": ["purchase", "down payment", "first-time", "homebuyer", "acquisition", "ownership"],
    }

    # Check each category
    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                return category

    # Default category
    return "GENERAL"
