"""
Fuzzy Matching Utility - Smart Normalization for Attributes, Projects, Columns

This utility provides reusable fuzzy matching logic with intelligent normalization
for handling:
- Newlines in names/attributes
- Brackets and special characters
- Unit variations (%, Cr, Units, etc.)
- Case-insensitive matching
- Similarity-based scoring

Used for mapping:
- Test queries to knowledge graph attributes
- Project names with variations
- Excel column names to data fields
- Any other loosely-coupled matching needs
"""

import re
from typing import Optional, Tuple, List, Dict, Any
from difflib import SequenceMatcher


class FuzzyMatcher:
    """
    Smart fuzzy matching with normalization

    Features:
    - Newline handling: "Sara\nCity" matches "Sara City"
    - Bracket normalization: "(Rs.Cr.)" matches "(rs cr)"
    - Unit normalization: "units", "Units", "UNITS" all match
    - Position-based scoring: Matches early in query score higher
    - Similarity scoring: Uses SequenceMatcher for partial matches
    """

    @staticmethod
    def normalize(text: str) -> str:
        """
        Normalize text for fuzzy matching

        Steps:
        1. Replace newlines with spaces
        2. Normalize whitespace (collapse multiple spaces)
        3. Lowercase
        4. Strip leading/trailing spaces

        Args:
            text: Raw text to normalize

        Returns:
            Normalized text for matching

        Examples:
            >>> normalize("Sara\\nCity")
            "sara city"
            >>> normalize("Annual Sales Value\\n(Rs.Cr.)")
            "annual sales value (rs.cr.)"
        """
        if not text:
            return ""

        # Replace newlines with spaces
        normalized = text.replace('\n', ' ')

        # Normalize whitespace (collapse multiple spaces)
        normalized = ' '.join(normalized.split())

        # Lowercase
        normalized = normalized.lower()

        # Strip
        normalized = normalized.strip()

        return normalized

    @staticmethod
    def normalize_aggressive(text: str) -> str:
        """
        Aggressive normalization for very loose matching

        Additional steps:
        - Remove all punctuation (brackets, periods, commas)
        - Remove special characters

        Args:
            text: Raw text to normalize

        Returns:
            Aggressively normalized text

        Examples:
            >>> normalize_aggressive("Annual Sales Value (Rs.Cr.)")
            "annual sales value rscr"
        """
        # First do standard normalization
        normalized = FuzzyMatcher.normalize(text)

        # Remove punctuation and special characters
        # Keep only alphanumeric and spaces
        normalized = re.sub(r'[^a-z0-9\s]', '', normalized)

        # Collapse whitespace again
        normalized = ' '.join(normalized.split())

        return normalized

    @staticmethod
    def similarity_score(text1: str, text2: str, aggressive: bool = False) -> float:
        """
        Calculate similarity score between two texts

        Args:
            text1: First text
            text2: Second text
            aggressive: Use aggressive normalization

        Returns:
            Similarity score 0.0-1.0
        """
        if aggressive:
            norm1 = FuzzyMatcher.normalize_aggressive(text1)
            norm2 = FuzzyMatcher.normalize_aggressive(text2)
        else:
            norm1 = FuzzyMatcher.normalize(text1)
            norm2 = FuzzyMatcher.normalize(text2)

        if not norm1 or not norm2:
            return 0.0

        return SequenceMatcher(None, norm1, norm2).ratio()

    @staticmethod
    def match_with_score(
        query: str,
        target: str,
        variations: Optional[List[str]] = None,
        position_weight: float = 1.0
    ) -> Tuple[bool, float]:
        """
        Match query against target with scoring

        Args:
            query: Query string to match
            target: Target string to match against
            variations: Optional list of variations/aliases for target
            position_weight: Weight for position-based scoring (0-1)

        Returns:
            (matched: bool, score: float)

        Scoring:
            - Exact normalized match: 1.0
            - Containment: 0.5 + length_bonus + position_bonus
            - Variation match: 0.4
            - Partial similarity: 0.0-0.3 (based on difflib ratio)
        """
        query_norm = FuzzyMatcher.normalize(query)
        target_norm = FuzzyMatcher.normalize(target)

        # Exact match
        if query_norm == target_norm:
            return (True, 1.0)

        # Containment check
        if target_norm in query_norm:
            base_score = 0.5

            # Length bonus (longer matches are more specific)
            length_bonus = min(len(target_norm) / 100.0, 0.3)

            # Position bonus (earlier matches are more likely the subject)
            position = query_norm.find(target_norm)
            if position < 20:
                position_bonus = 0.2 * position_weight
            elif position < 40:
                position_bonus = 0.1 * position_weight
            else:
                position_bonus = 0.0

            score = base_score + length_bonus + position_bonus
            return (True, score)

        # Check variations
        if variations:
            for variation in variations:
                var_norm = FuzzyMatcher.normalize(variation)
                if var_norm in query_norm or query_norm in var_norm:
                    return (True, 0.4)

        # Partial similarity (fallback)
        similarity = FuzzyMatcher.similarity_score(query, target, aggressive=False)
        if similarity > 0.6:  # Threshold for "close enough"
            return (True, similarity * 0.5)  # Scale down to 0.0-0.5 range

        return (False, 0.0)

    @staticmethod
    def find_best_match(
        query: str,
        candidates: List[str],
        threshold: float = 0.2
    ) -> Optional[Tuple[str, float]]:
        """
        Find best matching candidate for a query

        Args:
            query: Query string
            candidates: List of candidate strings to match against
            threshold: Minimum score threshold (0.0-1.0)

        Returns:
            (best_match: str, score: float) or None if no match above threshold
        """
        best_match = None
        best_score = 0.0

        for candidate in candidates:
            matched, score = FuzzyMatcher.match_with_score(query, candidate)
            if matched and score > best_score:
                best_score = score
                best_match = candidate

        if best_match and best_score >= threshold:
            return (best_match, best_score)

        return None

    @staticmethod
    def match_dict_keys(
        query: str,
        data_dict: Dict[str, Any],
        threshold: float = 0.2
    ) -> Optional[Tuple[str, Any, float]]:
        """
        Match query to dictionary keys (useful for column mapping)

        Args:
            query: Query string (e.g., "Annual Sales Value")
            data_dict: Dictionary with keys to match against
            threshold: Minimum score threshold

        Returns:
            (matched_key: str, value: Any, score: float) or None

        Example:
            >>> data = {"annualSalesValueCr": 106.4, "totalSupply": 3018}
            >>> match_dict_keys("Annual Sales Value (Rs.Cr.)", data)
            ("annualSalesValueCr", 106.4, 0.85)
        """
        result = FuzzyMatcher.find_best_match(query, list(data_dict.keys()), threshold)

        if result:
            matched_key, score = result
            return (matched_key, data_dict[matched_key], score)

        return None


# Convenience functions for common use cases

def normalize_project_name(name: str) -> str:
    """Normalize project name for matching"""
    return FuzzyMatcher.normalize(name)


def normalize_attribute_name(name: str) -> str:
    """Normalize attribute name for matching"""
    return FuzzyMatcher.normalize(name)


def normalize_column_name(name: str) -> str:
    """Normalize column name for matching"""
    return FuzzyMatcher.normalize_aggressive(name)  # More aggressive for columns


def match_column_to_field(column_name: str, project_data: Dict[str, Any]) -> Optional[Tuple[str, Any]]:
    """
    Match an attribute/column name to a field in project data

    Args:
        column_name: Attribute name from query (e.g., "Annual Sales Value (Rs.Cr.)")
        project_data: Project data dictionary

    Returns:
        (field_name, value) or None
    """
    result = FuzzyMatcher.match_dict_keys(column_name, project_data, threshold=0.3)
    if result:
        field_name, value, score = result
        return (field_name, value)
    return None
