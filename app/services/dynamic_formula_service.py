"""
Dynamic Formula Service - Runtime Formula Evaluation from Excel

Loads the Excel sheet with all formulas and executes them dynamically at runtime.
NO HARDCODED CALCULATORS - everything is driven by the Excel sheet.
"""

import pandas as pd
import re
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass


@dataclass
class AttributeDefinition:
    """Attribute loaded from Excel"""
    layer: str
    target_attribute: str
    unit: str
    dimension: str
    description: str
    sample_prompt: str
    variation_in_prompt: str
    assumption_in_prompt: str
    formula_derivation: str
    sample_values: str
    expected_answer: str

    @property
    def requires_calculation(self) -> bool:
        """Check if this attribute needs calculation"""
        return self.formula_derivation and self.formula_derivation.strip().lower() != "direct extraction"


class DynamicFormulaService:
    """Service that loads Excel and executes formulas dynamically at runtime"""

    def __init__(self, excel_path: str = "/Users/tusharsikand/Documents/Projects/liases-foras/change-request/enriched-layers/LF-Layers_FULLY_ENRICHED_ALL_36.xlsx"):
        self.excel_path = excel_path
        self.attributes: Dict[str, AttributeDefinition] = {}
        self._load_excel()
        self._build_variable_mapping()

    def _load_excel(self):
        """Load all attributes from Excel sheet"""
        df = pd.read_excel(self.excel_path, sheet_name='All_Attributes')

        for _, row in df.iterrows():
            attr = AttributeDefinition(
                layer=str(row.get('Layer', '')),
                target_attribute=str(row.get('Target Attribute', '')),
                unit=str(row.get('Unit', '')),
                dimension=str(row.get('Dimension', '')),
                description=str(row.get('Description', '')),
                sample_prompt=str(row.get('Sample Prompt', '')),
                variation_in_prompt=str(row.get('Variation in Prompt', '')),
                assumption_in_prompt=str(row.get('Assumption in Prompt', '')),
                formula_derivation=str(row.get('Formula/Derivation', '')),
                sample_values=str(row.get('Sample Values', '')),
                expected_answer=str(row.get('Expected Answer', ''))
            )

            # Store by target attribute name (normalized)
            key = attr.target_attribute.lower().strip()
            self.attributes[key] = attr

        print(f"✓ Loaded {len(self.attributes)} attributes from Excel")

    def _build_variable_mapping(self):
        """Build mapping from formula variables to data field names"""
        self.variable_mapping = {
            # Basic dimensions
            'Supply': ['supply', 'totalSupplyUnits', 'totalUnits'],
            'Units': ['units', 'totalSupplyUnits', 'soldUnits'],
            'Sold': ['sold', 'soldUnits', 'sold_percent'],
            'Unsold': ['unsold', 'unsoldUnits', 'unsold_percent'],
            'Size': ['size', 'unitSaleableSizeSqft', 'avgUnitSize'],
            'Value': ['value', 'annualSalesValueCr', 'totalRevenue'],
            'Annual Sales': ['annual_sales', 'annualSalesUnits'],
            'AnnualSales': ['annualSalesUnits', 'annual_sales'],

            # Price fields
            'CurrentPSF': ['current_psf', 'currentPricePSF'],
            'LaunchPSF': ['launch_psf', 'launchPricePSF'],
            'Current PSF': ['currentPricePSF', 'current_psf'],
            'Launch PSF': ['launchPricePSF', 'launch_psf'],

            # Velocity
            'Velocity': ['velocity_percent', 'monthlySalesVelocity'],
            'Velocity%': ['monthlySalesVelocity', 'velocity_percent'],

            # Derived
            'Unit Size': ['unitSaleableSizeSqft', 'size', 'avgUnitSize'],
            'Monthly Sold': ['monthly_sold', 'monthly_units_sold'],
        }

    def get_attribute(self, attr_name: str) -> Optional[AttributeDefinition]:
        """Get attribute by name (case-insensitive)"""
        key = attr_name.lower().strip()
        return self.attributes.get(key)

    def search_attribute(self, query: str) -> Optional[Tuple[AttributeDefinition, float]]:
        """Fuzzy search for attribute with smart normalization for newlines, brackets, and units"""
        # Normalize query: remove newlines, normalize whitespace, lowercase
        query_normalized = ' '.join(query.replace('\n', ' ').split()).lower()

        best_match = None
        best_score = 0.0

        for attr in self.attributes.values():
            score = 0.0

            # Normalize attribute name: remove newlines, normalize whitespace
            attr_normalized = ' '.join(attr.target_attribute.replace('\n', ' ').split()).lower()

            # Check target attribute name (FIX: reversed containment check)
            if attr_normalized in query_normalized:
                # Base score for match
                base_score = 0.5
                # Bonus for longer matches (more specific)
                length_bonus = len(attr_normalized) / 100.0  # Up to +0.5 for long attributes
                # Bonus for word boundary match (not substring)
                import re
                if re.search(r'\b' + re.escape(attr_normalized) + r'\b', query_normalized):
                    boundary_bonus = 0.3
                else:
                    boundary_bonus = 0.0

                # Position bonus - prefer matches earlier in the query
                # Especially in "What is the X" patterns
                # STRONG bonus to override length bonuses
                position = query_normalized.find(attr_normalized)
                if position < 20:  # Appears in first 20 chars (likely the main subject)
                    position_bonus = 1.0  # Strong bonus for early position
                elif position < 40:  # Appears in first 40 chars
                    position_bonus = 0.2  # Small bonus
                else:
                    position_bonus = -0.3  # Penalty for appearing later (likely context)

                score += base_score + length_bonus + boundary_bonus + position_bonus

            # Check sample prompts (also normalize)
            if attr.sample_prompt:
                sample_normalized = ' '.join(attr.sample_prompt.replace('\n', ' ').split()).lower()
                if query_normalized in sample_normalized:
                    score += 0.3

            # Check variations (also normalize)
            if attr.variation_in_prompt:
                for variation in attr.variation_in_prompt.split('|'):
                    variation_normalized = ' '.join(variation.replace('\n', ' ').split()).lower().strip()
                    if variation_normalized and variation_normalized in query_normalized:
                        score += 0.2
                        break

            if score > best_score:
                best_score = score
                best_match = attr

        if best_match and best_score > 0.2:
            return (best_match, best_score)

        return None

    def execute_formula(self, attr: AttributeDefinition, project_data: Dict) -> Optional[Dict]:
        """
        Execute formula dynamically at runtime

        Args:
            attr: Attribute definition with formula
            project_data: Project data dictionary

        Returns:
            Result dictionary with value, unit, formula, etc.
        """
        if not attr.requires_calculation:
            return None

        try:
            # Parse formula and extract variables
            formula = attr.formula_derivation

            # Substitute variables with actual values
            substituted_formula = self._substitute_variables(formula, project_data)

            # Evaluate the expression safely
            result = self._safe_eval(substituted_formula)

            return {
                'attribute': attr.target_attribute,
                'value': result,
                'unit': attr.unit,
                'dimension': attr.dimension,
                'formula': formula,
                'substituted_formula': substituted_formula,
                'layer': attr.layer
            }

        except Exception as e:
            print(f"Error executing formula for {attr.target_attribute}: {e}")
            print(f"  Formula: {formula}")
            print(f"  Available data keys: {list(project_data.keys())}")
            return None

    def _substitute_variables(self, formula: str, data: Dict) -> str:
        """
        Substitute formula variables with actual data values

        Example:
          "Annual Sales / 12" with data={'annual_sales': 527}
          → "527 / 12"

          "Velocity% × Supply" with data={'velocity': 3.47}
          → "(3.47/100) * Supply"  # Divide by 100 for percentage
        """
        substituted = formula

        # Find all variable names in formula (words, possibly with spaces)
        # Pattern: words starting with capital letter, including multi-word like "Annual Sales"
        variable_pattern = r'\b([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*)\b'

        matches = re.findall(variable_pattern, formula)

        for var_name in set(matches):  # Use set to avoid duplicate substitutions
            # Find value in data using variable mapping
            value = self._find_variable_value(var_name, data)

            if value is not None:
                # Handle percentage symbols (e.g., "Velocity%" → divide by 100)
                if f"{var_name}%" in formula:
                    # Percentage: divide by 100
                    substituted = substituted.replace(f"{var_name}%", f"({value}/100)")
                else:
                    substituted = substituted.replace(var_name, str(value))

        # Clean up formula: replace × with *, − with -
        substituted = substituted.replace('×', '*')
        substituted = substituted.replace('−', '-')

        return substituted

    def _find_variable_value(self, var_name: str, data: Dict) -> Optional[float]:
        """
        Find variable value in data using mapping

        Example: "Annual Sales" → looks for 'annual_sales' or 'annualSalesUnits' in data
        """
        # Try direct lookup first
        if var_name in data:
            return self._extract_value(data[var_name])

        # Try variable mapping
        if var_name in self.variable_mapping:
            for field_name in self.variable_mapping[var_name]:
                if field_name in data:
                    return self._extract_value(data[field_name])

        # Try lowercase/camelCase variations
        var_lower = var_name.lower().replace(' ', '')
        if var_lower in data:
            return self._extract_value(data[var_lower])

        return None

    def _extract_value(self, field_value) -> Optional[float]:
        """Extract numeric value from field (handles dict and direct values)"""
        if isinstance(field_value, dict):
            return field_value.get('value')
        elif isinstance(field_value, (int, float)):
            return field_value
        return None

    def _safe_eval(self, expression: str) -> float:
        """
        Safely evaluate mathematical expression

        Uses only safe mathematical operations, no code execution
        """
        # Remove any whitespace
        expression = expression.strip()

        # Only allow numbers, operators, parentheses, and dots
        if not re.match(r'^[\d\s\+\-\*\/\(\)\.e]+$', expression):
            raise ValueError(f"Unsafe expression: {expression}")

        # Use eval with restricted globals/locals (only math operations)
        try:
            result = eval(expression, {"__builtins__": {}}, {})
            return float(result)
        except Exception as e:
            raise ValueError(f"Failed to evaluate: {expression}. Error: {e}")

    def list_all_attributes(self) -> List[Dict]:
        """List all attributes with their metadata"""
        return [
            {
                'name': attr.target_attribute,
                'layer': attr.layer,
                'unit': attr.unit,
                'dimension': attr.dimension,
                'requires_calculation': attr.requires_calculation,
                'formula': attr.formula_derivation if attr.requires_calculation else 'Direct extraction'
            }
            for attr in self.attributes.values()
        ]


# Global singleton
_service = None


def get_dynamic_formula_service() -> DynamicFormulaService:
    """Get global dynamic formula service instance"""
    global _service
    if _service is None:
        _service = DynamicFormulaService()
    return _service
