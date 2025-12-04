#!/usr/bin/env python3
"""
Dimension Parser Utility
Parses dimensional formulas and creates Neo4j relationships to L0 dimensions

Handles:
- Simple dimensions: "U", "T", "L²", "C" → IS relationship
- Ratios: "C/L²", "L²/U", "C/T" → NUMERATOR and DENOMINATOR relationships
- Inverse: "1/T" → INVERSE_OF relationship
- Dimensionless: "None", "Dimensionless" → No relationships
- Complex: "U*T", "(C/L²)*T" → FACTOR relationships (future)

Author: Claude Code
Date: 2025-11-30
"""

from typing import Dict, List, Tuple
import re


class DimensionParser:
    """Parse dimensional formulas and generate Neo4j relationships"""

    # Layer 0 base dimensions
    BASE_DIMENSIONS = {"U", "L²", "T", "C"}

    # Dimensionless indicators
    DIMENSIONLESS = {"None", "Dimensionless", "", "String", "Text", "Boolean Flag", "Integer"}

    @staticmethod
    def parse_dimension(dimension: str) -> List[Dict]:
        """
        Parse a dimension string and return list of relationship definitions

        Args:
            dimension: Dimension formula (e.g., "C/L²", "U", "1/T", "None")

        Returns:
            List of relationship dictionaries with 'type' and 'target_dimension'

        Examples:
            parse_dimension("U") → [{"type": "IS", "target": "U"}]
            parse_dimension("C/L²") → [
                {"type": "NUMERATOR", "target": "C"},
                {"type": "DENOMINATOR", "target": "L²"}
            ]
            parse_dimension("1/T") → [{"type": "INVERSE_OF", "target": "T"}]
            parse_dimension("None") → []
        """
        if not dimension or dimension in DimensionParser.DIMENSIONLESS:
            return []

        relationships = []

        # Clean the dimension string
        dimension = dimension.strip()

        # Case 1: Simple dimension (U, T, L², C)
        if dimension in DimensionParser.BASE_DIMENSIONS:
            relationships.append({
                "type": "IS",
                "target": dimension
            })
            return relationships

        # Case 2: Inverse dimension (1/T, 1/L², etc.)
        inverse_match = re.match(r'^1/([UTLC²]+)$', dimension)
        if inverse_match:
            base_dim = inverse_match.group(1)
            if base_dim in DimensionParser.BASE_DIMENSIONS:
                relationships.append({
                    "type": "INVERSE_OF",
                    "target": base_dim
                })
                return relationships

        # Case 3: Ratio dimension (C/L², L²/U, C/T, etc.)
        ratio_match = re.match(r'^([UTLC²]+)/([UTLC²]+)$', dimension)
        if ratio_match:
            numerator = ratio_match.group(1)
            denominator = ratio_match.group(2)

            if numerator in DimensionParser.BASE_DIMENSIONS:
                relationships.append({
                    "type": "NUMERATOR",
                    "target": numerator
                })

            if denominator in DimensionParser.BASE_DIMENSIONS:
                relationships.append({
                    "type": "DENOMINATOR",
                    "target": denominator
                })

            return relationships

        # Case 4: Fraction with percentage (Fraction/T → 1/T)
        if dimension == "Fraction/T":
            relationships.append({
                "type": "INVERSE_OF",
                "target": "T"
            })
            return relationships

        # Case 5: Product dimensions (future support)
        # Examples: "U*T", "C*L²", etc.
        product_match = re.match(r'^([UTLC²]+)\*([UTLC²]+)$', dimension)
        if product_match:
            factor1 = product_match.group(1)
            factor2 = product_match.group(2)

            if factor1 in DimensionParser.BASE_DIMENSIONS:
                relationships.append({
                    "type": "FACTOR",
                    "target": factor1
                })

            if factor2 in DimensionParser.BASE_DIMENSIONS:
                relationships.append({
                    "type": "FACTOR",
                    "target": factor2
                })

            return relationships

        # Unknown dimension format - return empty
        return relationships

    @staticmethod
    def create_cypher_relationships(
        node_var: str,
        attr_name: str,
        dimension: str
    ) -> Tuple[str, Dict]:
        """
        Generate Cypher query fragment to create dimensional relationships

        Args:
            node_var: Node variable in Cypher (e.g., "p" for Project)
            attr_name: Attribute name (e.g., "totalSupplyUnits")
            dimension: Dimension formula (e.g., "U", "C/L²")

        Returns:
            Tuple of (cypher_query_fragment, parameters_dict)

        Example:
            create_cypher_relationships("p", "totalSupplyUnits", "U")
            →
            '''
            WITH p
            MATCH (dim_U:Dimension_L0 {name: "U"})
            CREATE (p)-[:HAS_DIMENSION {attribute: "totalSupplyUnits", relationship: "IS"}]->(dim_U)
            ''', {}
        """
        relationships = DimensionParser.parse_dimension(dimension)

        if not relationships:
            return "", {}

        cypher_parts = []
        params = {}

        for rel in relationships:
            rel_type = rel["type"]
            target_dim = rel["target"]

            cypher_parts.append(f"""
            WITH {node_var}
            MATCH (dim_{target_dim.replace('²', '2')}:Dimension_L0 {{name: "{target_dim}"}})
            CREATE ({node_var})-[:HAS_DIMENSION {{
                attribute: "{attr_name}",
                relationship: "{rel_type}"
            }}]->(dim_{target_dim.replace('²', '2')})
            """)

        return "\n".join(cypher_parts), params

    @staticmethod
    def get_dimension_summary(dimension: str) -> str:
        """
        Get human-readable summary of dimension relationships

        Example:
            get_dimension_summary("C/L²") → "C (Numerator) / L² (Denominator)"
            get_dimension_summary("U") → "U (Is)"
            get_dimension_summary("1/T") → "1 / T (Inverse)"
        """
        relationships = DimensionParser.parse_dimension(dimension)

        if not relationships:
            return "Dimensionless"

        if len(relationships) == 1:
            rel = relationships[0]
            if rel["type"] == "IS":
                return f"{rel['target']} (Is)"
            elif rel["type"] == "INVERSE_OF":
                return f"1 / {rel['target']} (Inverse)"

        if len(relationships) == 2:
            if relationships[0]["type"] == "NUMERATOR" and relationships[1]["type"] == "DENOMINATOR":
                return f"{relationships[0]['target']} (Numerator) / {relationships[1]['target']} (Denominator)"

        # Generic fallback
        parts = [f"{rel['target']} ({rel['type']})" for rel in relationships]
        return " & ".join(parts)


def test_dimension_parser():
    """Test the dimension parser with various cases"""
    print("="*70)
    print("DIMENSION PARSER TEST CASES")
    print("="*70)

    test_cases = [
        "U",           # Simple dimension
        "T",           # Simple dimension
        "L²",          # Simple dimension
        "C",           # Simple dimension
        "C/L²",        # Ratio (Price per sqft)
        "L²/U",        # Ratio (Area per unit)
        "C/T",         # Ratio (Cash flow per time)
        "1/T",         # Inverse (Frequency)
        "Fraction/T",  # Percentage per time
        "None",        # Dimensionless
        "Dimensionless", # Dimensionless
        "String",      # Text field
        "Boolean Flag" # Boolean
    ]

    parser = DimensionParser()

    for dimension in test_cases:
        relationships = parser.parse_dimension(dimension)
        summary = parser.get_dimension_summary(dimension)

        print(f"\nDimension: '{dimension}'")
        print(f"  Summary: {summary}")
        print(f"  Relationships: {relationships}")


if __name__ == "__main__":
    test_dimension_parser()
