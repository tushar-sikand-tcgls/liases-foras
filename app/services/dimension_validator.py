"""
Dimension Validator - Self-Validating Mechanism

Ensures that query responses match expected dimensions.
Prevents returning dimension-mismatched data (e.g., returning Units when Time was requested).
"""

from typing import Dict, Optional, Tuple
import re


# Dimension keywords mapping
DIMENSION_KEYWORDS = {
    "U": [
        "units", "unit", "supply", "inventory", "total units", "sold units",
        "unsold units", "remaining units", "how many units", "number of units"
    ],
    "L²": [
        "area", "size", "sqft", "square feet", "acres", "land", "carpet area",
        "saleable area", "built-up area", "project size"
    ],
    "T": [
        "time", "duration", "age", "months", "years", "period", "sellout time",
        "months of inventory", "project age", "how long", "when", "date",
        "launch date", "possession date"
    ],
    "CF": [
        "price", "cost", "revenue", "investment", "cash flow", "money", "rupees",
        "inr", "crore", "lakh", "amount"
    ],
    "CF/L²": [
        "psf", "price per sqft", "cost per sqft", "per square feet"
    ],
    "CF/U": [
        "asp", "average selling price", "price per unit", "unit price"
    ],
    "T⁻¹": [
        "rate", "velocity", "absorption rate", "sales velocity", "per month",
        "per year", "monthly", "annual"
    ]
}


class DimensionValidator:
    """Validates that query responses match expected dimensions"""

    def __init__(self):
        self.dimension_keywords = DIMENSION_KEYWORDS

    def extract_expected_dimension(self, query: str) -> Optional[str]:
        """
        Extract expected dimension from query text

        Args:
            query: User's natural language query

        Returns:
            Expected dimension code (U, L², T, CF, etc.) or None if ambiguous
        """
        query_lower = query.lower()

        # SPECIAL CASE: "growth" or "appreciation" with "price" indicates dimensionless percentage
        # "Price growth", "price appreciation" → dimensionless (%), not CF
        if ('growth' in query_lower or 'appreciation' in query_lower) and 'price' in query_lower:
            # This is a percentage metric (dimensionless), don't enforce CF dimension
            return None

        # SPECIAL CASE: "gap" with "price" or "psf" indicates CF/L² or absolute difference
        # "PSF gap", "price gap" → could be dimensionless difference
        if 'gap' in query_lower and ('price' in query_lower or 'psf' in query_lower):
            return None

        # Score each dimension based on keyword matches
        scores = {}
        for dimension, keywords in self.dimension_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in query_lower:
                    score += 1
            if score > 0:
                scores[dimension] = score

        # Return dimension with highest score, or None if tied
        if not scores:
            return None

        max_score = max(scores.values())
        candidates = [dim for dim, score in scores.items() if score == max_score]

        if len(candidates) == 1:
            return candidates[0]
        else:
            # Ambiguous - multiple dimensions match equally
            return None

    def validate_response(
        self,
        query: str,
        response_value: any,
        response_unit: str,
        response_dimension: Optional[str]
    ) -> Tuple[bool, str]:
        """
        Validate that response dimension matches query expectation

        Args:
            query: User's query
            response_value: Value in response
            response_unit: Unit of measurement
            response_dimension: Dimension in response

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if dimension matches or validation not applicable
            - error_message: Description if invalid, empty string if valid
        """
        expected_dim = self.extract_expected_dimension(query)

        # If we can't determine expected dimension, allow it
        if expected_dim is None:
            return True, ""

        # If response doesn't have dimension, that's a problem
        if response_dimension is None:
            return False, (
                f"Dimension validation FAILED: "
                f"Query expects dimension '{expected_dim}' but response has no dimension. "
                f"Got: {response_value} {response_unit}"
            )

        # Check if dimensions match
        if expected_dim == response_dimension:
            return True, ""
        else:
            return False, (
                f"Dimension validation FAILED: "
                f"Query expects dimension '{expected_dim}' (based on keywords: {self._get_matched_keywords(query, expected_dim)}), "
                f"but response has dimension '{response_dimension}'. "
                f"Got: {response_value} {response_unit}. "
                f"This indicates the system returned irrelevant data."
            )

    def _get_matched_keywords(self, query: str, dimension: str) -> list:
        """Get list of keywords that matched for this dimension"""
        query_lower = query.lower()
        matched = []
        for keyword in self.dimension_keywords.get(dimension, []):
            if keyword in query_lower:
                matched.append(f"'{keyword}'")
        return matched[:3]  # Return first 3 matches

    def get_dimension_name(self, dimension_code: str) -> str:
        """Get human-readable name for dimension code"""
        dimension_names = {
            "U": "Units (Count)",
            "L²": "Area (sqft/acres)",
            "T": "Time (months/years/dates)",
            "CF": "Cash Flow (₹)",
            "CF/L²": "Price per Area (₹/sqft)",
            "CF/U": "Price per Unit (₹)",
            "T⁻¹": "Rate (per month/year)"
        }
        return dimension_names.get(dimension_code, dimension_code)


# Global instance
_validator = None


def get_dimension_validator() -> DimensionValidator:
    """Get global dimension validator instance"""
    global _validator
    if _validator is None:
        _validator = DimensionValidator()
    return _validator
