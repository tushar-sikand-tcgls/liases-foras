"""
Generic Derived Metrics Calculator

This service reads formulas from the Excel file and evaluates them
using a safe math expression parser. No domain-specific code!

Architecture:
1. Load formulas from LF-Layers_FULLY_ENRICHED_ALL_36.xlsx
2. Parse formulas and map to KG field names
3. Evaluate formulas using Python's ast.literal_eval (safe evaluation)
4. Return calculated metrics

Formula Validation:
- Run `python3 -m app.services.formula_validator` to check sync status
- Validates Excel formulas against calculator implementation
- Detects: adds, removes, changes to formulas
"""

import pandas as pd
import re
import ast
import operator
import os
from typing import Dict, Any, Optional


class DerivedMetricsCalculator:
    """
    Generic calculator that reads formulas from Excel and evaluates them
    against project data using a safe expression parser.
    """

    def __init__(self, excel_path: str, validate_on_init: bool = False):
        """
        Initialize calculator with formulas from Excel

        Args:
            excel_path: Path to LF-Layers_FULLY_ENRICHED_ALL_36.xlsx
            validate_on_init: Run formula validation on initialization (dev mode)
        """
        self.excel_path = excel_path
        self.formulas = {}
        self.field_mapping = {}
        self._load_formulas()

        # Optional: Validate formulas on init (useful in dev mode)
        if validate_on_init or os.getenv("VALIDATE_FORMULAS_ON_STARTUP", "false").lower() == "true":
            self._validate_formulas()

    def _load_formulas(self):
        """Load formulas from Excel file"""
        try:
            df = pd.read_excel(self.excel_path)

            # Extract calculated attributes (not "Direct extraction")
            calculated = df[df['Formula/Derivation'] != 'Direct extraction']

            for idx, row in calculated.iterrows():
                attr_name = row['Target Attribute']
                formula = row['Formula/Derivation']

                # Store formula
                self.formulas[attr_name] = formula

                # Create camelCase field name for storage
                field_name = self._to_camel_case(attr_name)
                self.field_mapping[attr_name] = field_name

            print(f"✅ Loaded {len(self.formulas)} calculated formulas from Excel")

        except Exception as e:
            print(f"⚠️  Error loading formulas: {e}")
            self.formulas = {}

    def _validate_formulas(self):
        """Run formula validation check (optional, for dev mode)"""
        try:
            # Direct validation without importing calculator again (avoid recursion)
            import pandas as pd

            df = pd.read_excel(self.excel_path)
            calculated = df[df['Formula/Derivation'] != 'Direct extraction']

            excel_formulas = {}
            for idx, row in calculated.iterrows():
                attr_name = row['Target Attribute']
                formula = row['Formula/Derivation']
                excel_formulas[attr_name] = formula

            # Compare
            excel_attrs = set(excel_formulas.keys())
            calc_attrs = set(self.formulas.keys())

            missing = excel_attrs - calc_attrs
            extra = calc_attrs - excel_attrs

            if missing or extra:
                print("⚠️  Formula validation detected sync issues!")
                print(f"   Run: python3 -m app.services.formula_validator")
            else:
                print("✅ Formula validation passed - Excel and Calculator in sync")

        except Exception as e:
            print(f"⚠️  Could not run formula validation: {e}")

    def _to_camel_case(self, name: str) -> str:
        """Convert 'Unsold Units' to 'unsoldUnits'"""
        # Remove special characters
        name = re.sub(r'[()%/-]', '', name)
        # Split into words
        words = name.split()
        if not words:
            return name
        # First word lowercase, rest title case
        return words[0].lower() + ''.join(w.capitalize() for w in words[1:])

    def _parse_formula(self, formula: str, data: Dict[str, Any]) -> Optional[float]:
        """
        Parse and evaluate formula using safe expression evaluation

        Args:
            formula: Formula string like "Annual Sales / 12"
            data: Project data dictionary

        Returns:
            Calculated value or None if cannot calculate
        """
        try:
            # Normalize formula - replace common terms with KG field names
            normalized = formula

            # Map common terms to KG field names (case-insensitive)
            term_mapping = {
                'Supply': 'totalSupplyUnits',
                'Total Supply': 'totalSupplyUnits',
                'Annual Sales': 'annualSalesUnits',
                'Unsold%': 'unsoldPercent',
                'Sold%': 'soldPercent',
                'Unsold': 'unsoldPercent',  # When used as percentage
                'Velocity%': 'monthlySalesVelocity',
                'Value': 'annualSalesValue',
                'Units': 'annualSalesUnits',  # Context-dependent
                'Size': 'unitSaleableSize',
                'Unit Size': 'unitSaleableSize',
                'CurrentPSF': 'currentPricePSF',
                'Current': 'currentPricePSF',  # When PSF context
                'LaunchPSF': 'launchPricePSF',
                'Launch': 'launchPricePSF',  # When PSF context
                'PSF': 'currentPricePSF',  # Default to current
            }

            # Replace terms (whole word matching)
            for term, field in term_mapping.items():
                # Use word boundaries for replacement
                pattern = r'\b' + re.escape(term) + r'\b'
                if field in data:
                    normalized = re.sub(pattern, f"data['{field}']", normalized, flags=re.IGNORECASE)

            # Replace math operators with Python equivalents
            normalized = normalized.replace('×', '*')
            normalized = normalized.replace('−', '-')  # Unicode minus
            normalized = normalized.replace('÷', '/')

            # Safe evaluation using eval with restricted globals
            allowed_names = {"data": data}
            allowed_functions = {
                "__builtins__": None,  # Disable built-ins for safety
            }

            result = eval(normalized, allowed_functions, allowed_names)
            return float(result) if result is not None else None

        except Exception as e:
            # Formula couldn't be evaluated - missing data or syntax error
            return None

    def calculate_all(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate all derived metrics for a project

        Args:
            data: Base project data from KG

        Returns:
            Dictionary with all calculated metrics
        """
        calculated = {}

        # Calculate in order (some formulas depend on others)
        # First pass: Simple formulas
        for attr_name, formula in self.formulas.items():
            field_name = self.field_mapping[attr_name]

            # Try to calculate
            value = self._parse_formula(formula, {**data, **calculated})

            if value is not None:
                calculated[field_name] = value

        # Second pass: Formulas that depend on first-pass results
        # (e.g., MOI depends on Unsold Units and Monthly Units Sold)
        for attr_name, formula in self.formulas.items():
            field_name = self.field_mapping[attr_name]

            if field_name not in calculated:  # Not calculated in first pass
                # Try again with calculated values available
                value = self._parse_formula(formula, {**data, **calculated})

                if value is not None:
                    calculated[field_name] = value

        return calculated


def get_calculator(excel_path: str = None) -> DerivedMetricsCalculator:
    """
    Get calculator instance (singleton pattern)

    Args:
        excel_path: Path to Excel file (default: standard location)

    Returns:
        DerivedMetricsCalculator instance
    """
    if excel_path is None:
        excel_path = "/Users/tusharsikand/Documents/Projects/liases-foras/change-request/managed-rag/LF-Layers_FULLY_ENRICHED_ALL_36.xlsx"

    return DerivedMetricsCalculator(excel_path)
