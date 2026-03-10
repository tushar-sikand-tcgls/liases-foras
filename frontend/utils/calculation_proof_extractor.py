"""
Calculation Proof Extractor

Extracts calculation proof data from query responses for display in the frontend.
Detects derived attributes and financial metrics, retrieves formula and input data.
"""

from typing import Dict, List, Optional, Any
import json


def extract_calculation_proof_from_response(response_data: Dict) -> Optional[Dict]:
    """
    Extract calculation proof data from query response

    Args:
        response_data: Full response from v4_query_service.query()

    Returns:
        Dict with calculation proof data if available, None otherwise
        Format: {
            "calculation_type": str,
            "project_name": str,
            "formula": str,
            "inputs": Dict[str, Any],
            "result": Any,
            "unit": str,
            "steps": List[Dict]  # Optional
        }
    """
    # Check if response has kg_data
    kg_data = response_data.get('kg_data', {})
    if not kg_data:
        return None

    # Check resolved attributes for derived attributes (L1 layer)
    resolved_attributes = response_data.get('resolved_attributes', [])

    # Look for derived attributes (those with formulas)
    for attr_metadata in resolved_attributes:
        formula = attr_metadata.get('Formula/Derivation')
        if formula and formula != 'Direct extraction':
            # This is a derived attribute!
            attribute_name = attr_metadata.get('Target Attribute')
            unit = attr_metadata.get('Unit')

            # Extract project name from kg_data keys (format: "ProjectName.AttributeName")
            project_name = None
            result_value = None

            for key, value in kg_data.items():
                if '.' in key and attribute_name in key:
                    parts = key.split('.')
                    project_name = parts[0]
                    result_value = value
                    break

            if not project_name or result_value is None:
                continue  # Skip if we can't find the data

            # Extract inputs from kg_data based on formula
            # This is a simplified version - can be enhanced with formula parsing
            inputs = extract_inputs_from_formula(formula, kg_data, project_name)

            return {
                "calculation_type": attribute_name,
                "project_name": project_name,
                "formula": formula,
                "inputs": inputs,
                "result": result_value,
                "unit": unit,
                "steps": []  # Can be auto-generated from formula
            }

    # Check if this is a financial metric calculation
    computation_results = response_data.get('computation_results', {})
    if computation_results:
        # Financial calculation (IRR, NPV, etc.)
        if 'irr' in computation_results:
            return {
                "calculation_type": "IRR",
                "project_name": extract_project_name_from_kg(kg_data),
                "formula": "IRR = r such that NPV = 0",
                "inputs": {
                    "cash_flows": computation_results.get('cash_flows', []),
                    "initial_investment": computation_results.get('initial_investment')
                },
                "result": computation_results['irr'],
                "unit": "%",
                "steps": []
            }
        elif 'npv' in computation_results:
            return {
                "calculation_type": "NPV",
                "project_name": extract_project_name_from_kg(kg_data),
                "formula": "NPV = ∑[CF_t / (1+r)^t]",
                "inputs": {
                    "cash_flows": computation_results.get('cash_flows', []),
                    "discount_rate": computation_results.get('discount_rate')
                },
                "result": computation_results['npv'],
                "unit": "Rs Cr",
                "steps": []
            }

    return None


def extract_inputs_from_formula(formula: str, kg_data: Dict, project_name: str) -> Dict[str, Any]:
    """
    Extract input values from KG data based on formula variables

    Args:
        formula: Formula string (e.g., "(AnnualSales × 12) / Supply")
        kg_data: KG data dict
        project_name: Project name to look up values

    Returns:
        Dict of input variable names and values
    """
    import re

    # Extract variable names from formula (camelCase identifiers)
    # Pattern matches: annualSales, totalSupplyUnits, etc.
    variable_pattern = r'\b[a-z][a-zA-Z0-9]*\b'
    variables = re.findall(variable_pattern, formula)

    # Filter out common math words
    math_words = {'and', 'or', 'if', 'then', 'else', 'where', 'for', 'when'}
    variables = [v for v in variables if v not in math_words]

    inputs = {}

    # Map formula variables to KG keys
    # This mapping handles common variations
    variable_mapping = {
        'annualSales': 'Annual Sales (Units)',
        'supply': 'Total Supply (Units)',
        'unsoldPct': 'Unsold (%)',
        'soldPct': 'Sold (%)',
        'currentPSF': 'Current Price PSF',
        'launchPSF': 'Launch Price PSF',
        'unitSize': 'Unit Saleable Size (Sq.Ft.)',
        'annualValueCr': 'Annual Sales Value (Rs Cr)',
        'monthlySalesVelocity': 'Monthly Sales Velocity (%)'
    }

    for var in variables:
        # Try to find corresponding value in kg_data
        mapped_key = variable_mapping.get(var, var)

        # Look for keys like "ProjectName.AttributeName"
        full_key = f"{project_name}.{mapped_key}"
        if full_key in kg_data:
            inputs[var] = kg_data[full_key]
        else:
            # Try partial match
            for key, value in kg_data.items():
                if mapped_key in key and project_name in key:
                    inputs[var] = value
                    break

    return inputs


def extract_project_name_from_kg(kg_data: Dict) -> Optional[str]:
    """
    Extract project name from KG data keys

    Args:
        kg_data: KG data dict with keys like "ProjectName.Attribute"

    Returns:
        Project name or None
    """
    for key in kg_data.keys():
        if '.' in key:
            return key.split('.')[0]
    return None


def should_display_calculation_proof(response_data: Dict) -> bool:
    """
    Determine if calculation proof should be displayed for this response

    Args:
        response_data: Full response from v4_query_service.query()

    Returns:
        True if proof should be shown
    """
    proof_data = extract_calculation_proof_from_response(response_data)
    return proof_data is not None


def format_formula_for_display(formula: str) -> str:
    """
    Format formula string for nice display (convert symbols)

    Args:
        formula: Raw formula string (e.g., "(annualSales * 12) / supply")

    Returns:
        Formatted formula (e.g., "(Annual Sales × 12) / Supply")
    """
    # Replace multiplication/division symbols
    formula = formula.replace('*', '×')
    formula = formula.replace('/', '÷')

    # Convert camelCase to Title Case
    import re

    def camel_to_title(match):
        word = match.group(0)
        # Insert space before capital letters
        spaced = re.sub(r'([A-Z])', r' \1', word)
        return spaced.title().strip()

    # Replace camelCase words with Title Case
    formula = re.sub(r'\b[a-z][a-zA-Z0-9]*\b', camel_to_title, formula)

    return formula
