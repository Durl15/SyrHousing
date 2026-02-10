"""
Grant deduplication logic using fuzzy matching.
Prevents creating duplicate programs from discovered grants.
"""

from typing import Tuple, Dict, List
from rapidfuzz import fuzz
from ...models.program import Program


def find_duplicates(
    new_grant: Dict,
    existing_programs: List[Program]
) -> Tuple[Program | None, float]:
    """
    Find duplicate program using multi-factor fuzzy matching.

    Matching priority:
    1. URL exact match (highest confidence)
    2. Name fuzzy match + agency similarity
    3. Phone/email exact match

    Args:
        new_grant: Dictionary with grant data (keys: name, website, agency, phone, email)
        existing_programs: List of existing Program objects to check against

    Returns:
        Tuple of (matching_program, similarity_score) where:
        - matching_program: Matching Program object or None if no match
        - similarity_score: 0.0-1.0 confidence score of the match

    Example:
        >>> program, score = find_duplicates(new_grant, all_programs)
        >>> if score > 0.85:
        >>>     print(f"Duplicate detected: {program.name} ({score:.0%} similar)")
    """

    # Priority 1: URL exact match (highest confidence)
    if new_grant.get("website"):
        new_url = new_grant["website"].strip().lower()
        for prog in existing_programs:
            if prog.website and prog.website.strip().lower() == new_url:
                return prog, 1.0  # Perfect match

    # Priority 2: Name fuzzy match + agency verification
    if not new_grant.get("name"):
        return None, 0.0

    new_name = new_grant["name"].strip()
    best_match = None
    best_score = 0.0

    for prog in existing_programs:
        if not prog.name:
            continue

        # Calculate name similarity using token set ratio (handles word order differences)
        name_score = fuzz.token_set_ratio(new_name, prog.name) / 100.0

        if name_score >= 0.85:  # Name threshold
            # Verify agency similarity if both have agency data
            if new_grant.get("agency") and prog.agency:
                agency_score = fuzz.ratio(new_grant["agency"], prog.agency) / 100.0
                if agency_score >= 0.70:  # Agency threshold
                    # Combined score: weighted average
                    combined_score = (name_score * 0.7) + (agency_score * 0.3)
                    if combined_score > best_score:
                        best_match = prog
                        best_score = combined_score
            else:
                # No agency to verify, use name score alone
                if name_score > best_score:
                    best_match = prog
                    best_score = name_score

    if best_match and best_score >= 0.85:
        return best_match, best_score

    # Priority 3: Phone/email exact match (secondary verification)
    if new_grant.get("phone"):
        new_phone = new_grant["phone"].strip()
        for prog in existing_programs:
            if prog.phone and prog.phone.strip() == new_phone:
                # Phone match found, verify with name similarity
                if prog.name:
                    name_score = fuzz.token_set_ratio(new_name, prog.name) / 100.0
                    if name_score >= 0.70:  # Lower threshold with phone confirmation
                        return prog, 0.90  # High confidence

    if new_grant.get("email"):
        new_email = new_grant["email"].strip().lower()
        for prog in existing_programs:
            if prog.email and prog.email.strip().lower() == new_email:
                # Email match found, verify with name similarity
                if prog.name:
                    name_score = fuzz.token_set_ratio(new_name, prog.name) / 100.0
                    if name_score >= 0.70:  # Lower threshold with email confirmation
                        return prog, 0.90  # High confidence

    # No match found
    return None, 0.0


def is_duplicate(new_grant: Dict, existing_programs: List[Program], threshold: float = 0.85) -> bool:
    """
    Check if a grant is a duplicate (convenience function).

    Args:
        new_grant: Grant data dictionary
        existing_programs: List of existing programs
        threshold: Similarity threshold (0.0-1.0), default 0.85

    Returns:
        bool: True if duplicate found above threshold
    """
    _, score = find_duplicates(new_grant, existing_programs)
    return score >= threshold
