"""
Semantic Query Matcher - Vector-based query understanding
Uses string similarity and embeddings to match queries flexibly
"""

from typing import Dict, Optional, List
from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass
class QueryPattern:
    """Query pattern with semantic examples"""
    pattern_type: str
    examples: List[str]
    handler: str
    min_similarity: float = 0.6


class SemanticQueryMatcher:
    """
    Semantic query matcher using string similarity instead of exact matching

    Handles variations like:
    - "Calculate average" → "Compute average", "Provide average", "Generate average", "Derive average"
    - "What is PSF" → "Tell me PSF", "Show PSF", "Display PSF", "Get PSF"
    """

    def __init__(self):
        self.patterns = self._define_patterns()

    def _define_patterns(self) -> List[QueryPattern]:
        """Define query patterns with semantic examples (not hardcoded keywords!)"""
        return [
            # Specific project query patterns (HIGHEST PRIORITY - must come before averages)
            # Matches queries with "of [project name]" or "[project name] project size"
            QueryPattern(
                pattern_type="specific_project",
                examples=[
                    "what is the project size of project x",
                    "project size of project x",
                    "project x project size",
                    "get project size for project x",
                    "show me project x size",
                    "how big is project x",
                    "what is the size of project x",
                    "project x total units",
                    "how many units in project x",
                    "project x units",
                    "get data for project x",
                    "project x details",
                    "project x information",
                    "project x size",  # Added for "[name] size" pattern
                    "size of project x",
                    "project x data",
                    "what is project x",
                    "tell me about project x",
                    "show project x",
                    "show me project x",
                    "show me project x data",
                    "show me project x project data",
                    "display project x",
                    "display project x data",
                    "project x dimensions",
                    "project x project",  # Added to match "[name] project [dimension]"
                    "the project x project size",
                    "the size of the project x project"
                ],
                handler="get_specific_project",
                min_similarity=0.35  # Lower threshold because project names vary
            ),

            # Total/Sum patterns (MUST come before average patterns to avoid misrouting!)
            QueryPattern(
                pattern_type="total",
                examples=[
                    # "What is the total" variations (HIGH PRIORITY)
                    "what is the total",
                    "what is the total project size",
                    "what is the total size",
                    "what is total project size",
                    "total project size",
                    "sum of project sizes",
                    "sum of all project sizes",
                    "total of project sizes",
                    "aggregate project size",

                    # Revenue patterns
                    "total revenue",
                    "sum of revenue",
                    "calculate total revenue",
                    "compute total revenue",
                    "provide total revenue",
                    "generate sum of revenue",
                    "what is total revenue",
                    "show me total revenue",
                    "get total revenue",
                    "aggregate revenue",
                    "sum of all revenue",

                    # Annual sales patterns
                    "sum of all annual sales",
                    "total annual sales",
                    "what is the sum of annual sales",
                    "what is the sum of all annual sales",
                    "calculate sum of annual sales",
                    "aggregate annual sales",
                    "sum of all sales",
                    "total of all sales",
                    "what is total sales",
                    "sum annual sales",
                    "total sales",

                    # Units patterns
                    "sum of all units",
                    "total units",
                    "sum of units sold",
                    "total units sold",
                    "aggregate units",
                    "total of all units"
                ],
                handler="calculate_total",
                min_similarity=0.35  # Lower threshold to catch variations
            ),

            # Average project size patterns
            QueryPattern(
                pattern_type="average_project_size",
                examples=[
                    "calculate average of project sizes",
                    "compute average project size",
                    "provide average project size",
                    "generate mean project size",
                    "derive average units",
                    "what is the average project size",
                    "show me average project size",
                    "get average project size",
                    "find mean project size",
                    "tell me average project size",
                    "give me average project size",
                    "average number of units",
                    "mean units per project"
                ],
                handler="calculate_average_project_size",
                min_similarity=0.5
            ),

            # PSF patterns
            QueryPattern(
                pattern_type="psf",
                examples=[
                    "what is the psf",
                    "calculate psf",
                    "compute price per sqft",
                    "provide price per square foot",
                    "generate psf",
                    "derive price per area",
                    "show me psf",
                    "get psf",
                    "tell me psf",
                    "give me price per sqft",
                    "display psf",
                    "find psf"
                ],
                handler="calculate_psf",
                min_similarity=0.5
            ),

            # ASP patterns
            QueryPattern(
                pattern_type="asp",
                examples=[
                    "what is the asp",
                    "calculate asp",
                    "compute average selling price",
                    "provide asp",
                    "generate asp",
                    "derive price per unit",
                    "show me asp",
                    "get asp",
                    "tell me asp",
                    "average selling price",
                    "price per unit"
                ],
                handler="calculate_asp",
                min_similarity=0.5
            ),

            # Top N patterns
            QueryPattern(
                pattern_type="top_n",
                examples=[
                    "top 5 projects by revenue",
                    "show me top 10 by units",
                    "give me top 3 by area",
                    "provide top projects by revenue",
                    "compute top 5 projects",
                    "generate top 10 by size",
                    "find largest projects",
                    "highest revenue projects",
                    "biggest projects by units"
                ],
                handler="get_top_n",
                min_similarity=0.4
            ),

            # Standard Deviation patterns
            QueryPattern(
                pattern_type="standard_deviation",
                examples=[
                    "find the standard deviation in project size",
                    "calculate standard deviation of project sizes",
                    "compute standard deviation in project size",
                    "what is the standard deviation of project sizes",
                    "standard deviation of units",
                    "std dev of project size",
                    "standard deviation in size",
                    "find std dev of project sizes",
                    "calculate standard deviation",
                    "compute std dev",
                    "standard deviation of sizes",
                    "std deviation of project size"
                ],
                handler="calculate_standard_deviation",
                min_similarity=0.5
            )
        ]

    def string_similarity(self, a: str, b: str) -> float:
        """
        Calculate string similarity using SequenceMatcher

        Returns: Similarity score 0.0 to 1.0
        """
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    def best_match(self, query: str) -> Optional[Dict]:
        """
        Find best matching pattern using semantic similarity

        Args:
            query: User query (any variation like "calculate", "compute", "provide", etc.)

        Returns:
            Dict with pattern_type, handler, similarity score, or None
        """
        query_lower = query.lower().strip()

        best_score = 0.0
        best_pattern = None
        best_handler = None

        # Check all patterns
        for pattern in self.patterns:
            # Compare query against all examples in this pattern
            for example in pattern.examples:
                similarity = self.string_similarity(query_lower, example)

                if similarity > best_score and similarity >= pattern.min_similarity:
                    best_score = similarity
                    best_pattern = pattern.pattern_type
                    best_handler = pattern.handler

        if best_pattern:
            return {
                "pattern_type": best_pattern,
                "handler": best_handler,
                "similarity": best_score
            }

        return None

    def extract_number_from_top_n(self, query: str) -> Optional[int]:
        """Extract number from 'top N' queries"""
        import re
        match = re.search(r'top\s+(\d+)', query.lower())
        if match:
            return int(match.group(1))
        return None

    def extract_field_from_top_n(self, query: str) -> Optional[str]:
        """Extract field name from 'top N by X' queries"""
        import re
        # Try "by revenue", "by units", "by project size", etc.
        # Capture multiple words after "by" (up to 3 words)
        match = re.search(r'by\s+([\w\s]+?)(?:\s*$|,)', query.lower())
        if match:
            field_phrase = match.group(1).strip()

            # Map common variations to standard fields
            field_mapping = {
                'revenue': 'totalSupplyUnits',
                'sales': 'totalRevenueCr',
                'income': 'totalRevenueCr',
                'units': 'totalSupplyUnits',
                'size': 'totalSupplyUnits',
                'sizes': 'totalSupplyUnits',
                'project size': 'totalSupplyUnits',
                'project sizes': 'totalSupplyUnits',
                'area': 'projectSizeAcres',
                'land': 'projectSizeAcres',
                'land area': 'projectSizeAcres'
            }
            return field_mapping.get(field_phrase, 'totalSupplyUnits')
        return 'totalSupplyUnits'  # Default to units if no match

    def extract_field_from_total_query(self, query: str) -> str:
        """
        Extract field name from total/sum queries

        Examples:
            "sum of all annual sales" → "annualSalesUnits"
            "total revenue" → "totalRevenueCr"
            "sum of units" → "totalSupplyUnits"

        Returns:
            Field name to sum (defaults to 'totalSupplyUnits')
        """
        query_lower = query.lower()

        # Field mapping with priority order (check most specific first)
        field_checks = [
            # Annual metrics (most specific)
            (['annual sales', 'annual sale'], 'annualSalesUnits'),
            (['annual revenue', 'annual income'], 'annualSalesValueCr'),

            # Revenue metrics
            (['revenue', 'income', 'sales value'], 'totalRevenueCr'),

            # Unit metrics
            (['units sold', 'sold units'], 'totalSupplyUnits'),
            (['units', 'unit count'], 'totalSupplyUnits'),

            # Area metrics
            (['area', 'square feet', 'sqft'], 'projectSizeAcres'),
        ]

        # Try to match patterns in order
        for patterns, field_name in field_checks:
            for pattern in patterns:
                if pattern in query_lower:
                    return field_name

        # Default to units
        return 'totalSupplyUnits'


# Example usage
if __name__ == "__main__":
    matcher = SemanticQueryMatcher()

    # Test with variations
    test_queries = [
        "Calculate the average of all project sizes",  # Original
        "Compute the average of all project sizes",    # Variation 1
        "Provide the average of all project sizes",    # Variation 2
        "Generate the mean of all project sizes",      # Variation 3
        "Derive the average project size",             # Variation 4
        "What is the PSF?",
        "Show me the price per sqft",
        "Compute PSF",
        "Top 5 projects by revenue",
        "Give me top 10 by units"
    ]

    for query in test_queries:
        match = matcher.best_match(query)
        if match:
            print(f"✓ '{query}' → {match['handler']} (similarity: {match['similarity']:.2f})")
        else:
            print(f"✗ '{query}' → No match")
