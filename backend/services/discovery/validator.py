"""
Confidence scoring for discovered grants.
Calculates data quality and completeness scores to help admins prioritize review.
"""

from typing import Dict


def calculate_confidence(grant_data: Dict, source_type: str) -> float:
    """
    Calculate confidence score for a discovered grant.

    The score (0.0-1.0) indicates data quality and completeness.
    Higher scores mean more complete and reliable grant information.

    Scoring factors:
    - Has name: +0.2 (required)
    - Has agency: +0.15
    - Has website: +0.15
    - Has contact info (phone/email): +0.1
    - Has deadline: +0.1
    - Has benefit amount: +0.1
    - Has eligibility info: +0.1
    - Source reliability: +0.1 (varies by source)

    Args:
        grant_data: Dictionary with grant fields
        source_type: Source identifier ("rss_feed", "grants_gov_api", "web_scrape")

    Returns:
        float: Confidence score from 0.0 to 1.0

    Example:
        >>> data = {"name": "SHARP Grant", "website": "https://...", "agency": "HHQ"}
        >>> score = calculate_confidence(data, "grants_gov_api")
        >>> print(f"Confidence: {score:.0%}")
        Confidence: 65%
    """
    score = 0.0

    # Required field: name
    if grant_data.get("name"):
        score += 0.2

    # Agency information
    if grant_data.get("agency"):
        score += 0.15

    # Website URL
    if grant_data.get("website"):
        score += 0.15

    # Contact information (phone or email)
    has_phone = bool(grant_data.get("phone"))
    has_email = bool(grant_data.get("email"))
    if has_phone or has_email:
        score += 0.1

    # Deadline information
    if grant_data.get("status_or_deadline"):
        score += 0.1

    # Benefit amount
    if grant_data.get("max_benefit"):
        score += 0.1

    # Eligibility information
    if grant_data.get("eligibility_summary"):
        score += 0.1

    # Source reliability factor
    source_scores = {
        "grants_gov_api": 0.1,      # Highest reliability - structured API data
        "rss_feed": 0.08,            # Good reliability - standardized format
        "web_scrape": 0.05,          # Lower reliability - unstructured HTML
    }
    score += source_scores.get(source_type, 0.05)

    # Ensure score stays within 0.0-1.0 range
    return min(1.0, max(0.0, score))


def get_confidence_label(score: float) -> str:
    """
    Get human-readable label for confidence score.

    Args:
        score: Confidence score (0.0-1.0)

    Returns:
        str: Label ("High", "Medium", "Low")
    """
    if score >= 0.8:
        return "High"
    elif score >= 0.5:
        return "Medium"
    else:
        return "Low"


def should_auto_approve(score: float, threshold: float = 0.9) -> bool:
    """
    Determine if grant should be auto-approved (very high confidence).

    Args:
        score: Confidence score
        threshold: Minimum score for auto-approval (default 0.9)

    Returns:
        bool: True if score meets auto-approval threshold
    """
    return score >= threshold
