"""
Formula Validator and Sync Checker

This utility validates that the Excel file formulas are in sync with the calculator implementation.
Run this whenever the Excel file is updated to detect:
- New attributes added
- Attributes removed
- Formula changes
- Missing calculator implementations
"""

import pandas as pd
import json
from typing import Dict, List, Tuple, Set
from pathlib import Path


class FormulaValidator:
    """Validates Excel formulas against calculator implementation"""

    def __init__(self, excel_path: str):
        """
        Initialize validator with Excel file path

        Args:
            excel_path: Path to LF-Layers_FULLY_ENRICHED_ALL_36.xlsx
        """
        self.excel_path = excel_path
        self.excel_formulas = {}
        self.excel_descriptions = {}
        self.excel_units = {}
        self.excel_layers = {}

    def load_excel_metadata(self) -> Tuple[int, int]:
        """
        Load all metadata from Excel file

        Returns:
            Tuple of (direct_extraction_count, calculated_count)
        """
        try:
            df = pd.read_excel(self.excel_path)

            # Count direct extraction vs calculated
            direct_count = 0
            calculated_count = 0

            for idx, row in df.iterrows():
                attr_name = row['Target Attribute']
                formula = row['Formula/Derivation']
                description = row.get('Description', '')
                unit = row.get('Unit', '')
                layer = row.get('Layer', '')

                # Store metadata
                self.excel_descriptions[attr_name] = description
                self.excel_units[attr_name] = unit
                self.excel_layers[attr_name] = layer

                if formula == 'Direct extraction':
                    direct_count += 1
                else:
                    calculated_count += 1
                    self.excel_formulas[attr_name] = formula

            print(f"✅ Loaded Excel metadata:")
            print(f"   - Direct extraction: {direct_count} attributes")
            print(f"   - Calculated: {calculated_count} attributes")
            print(f"   - Total: {direct_count + calculated_count} attributes")

            return direct_count, calculated_count

        except Exception as e:
            print(f"❌ Error loading Excel file: {e}")
            return 0, 0

    def validate_against_calculator(self) -> Dict[str, List[str]]:
        """
        Validate Excel formulas against calculator implementation

        Returns:
            Dictionary with validation results:
            - missing_in_calculator: Formulas in Excel but not in calculator
            - extra_in_calculator: Formulas in calculator but not in Excel
            - formula_changes: Formulas that differ between Excel and calculator
        """
        # Import calculator to check what it has loaded
        from app.services.derived_metrics_calculator import get_calculator

        calculator = get_calculator(self.excel_path)

        # Get sets of attribute names
        excel_attrs = set(self.excel_formulas.keys())
        calc_attrs = set(calculator.formulas.keys())

        # Find differences
        missing_in_calc = excel_attrs - calc_attrs
        extra_in_calc = calc_attrs - excel_attrs

        # Check for formula changes (both exist but differ)
        formula_changes = []
        for attr in excel_attrs & calc_attrs:
            excel_formula = self.excel_formulas[attr]
            calc_formula = calculator.formulas[attr]
            if excel_formula != calc_formula:
                formula_changes.append(f"{attr}: Excel='{excel_formula}' vs Calc='{calc_formula}'")

        results = {
            "missing_in_calculator": list(missing_in_calc),
            "extra_in_calculator": list(extra_in_calc),
            "formula_changes": formula_changes,
            "total_excel_formulas": len(excel_attrs),
            "total_calculator_formulas": len(calc_attrs)
        }

        return results

    def export_metadata_json(self, output_path: str = "/tmp/attributes_metadata.json"):
        """
        Export complete metadata to JSON for use by the adapter

        Args:
            output_path: Path to save JSON file
        """
        metadata = {
            "direct_extraction": [],
            "calculated": [],
            "formulas": {}
        }

        # Read Excel again to categorize
        df = pd.read_excel(self.excel_path)

        for idx, row in df.iterrows():
            attr_name = row['Target Attribute']
            formula = row['Formula/Derivation']
            description = row.get('Description', '')
            unit = row.get('Unit', '')
            layer = row.get('Layer', '')
            dimension = row.get('Dimension', '')

            attr_dict = {
                "name": attr_name,
                "layer": layer,
                "unit": unit,
                "dimension": dimension,
                "description": description
            }

            if formula == 'Direct extraction':
                metadata["direct_extraction"].append(attr_dict)
            else:
                attr_dict["formula"] = formula
                metadata["calculated"].append(attr_dict)
                metadata["formulas"][attr_name] = formula

        # Write to JSON
        with open(output_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"\n✅ Exported metadata to: {output_path}")
        print(f"   - {len(metadata['direct_extraction'])} direct extraction attributes")
        print(f"   - {len(metadata['calculated'])} calculated attributes")

        return metadata

    def print_validation_report(self):
        """Print comprehensive validation report"""
        print("\n" + "="*80)
        print("FORMULA VALIDATION REPORT")
        print("="*80)

        # Load Excel metadata
        direct_count, calc_count = self.load_excel_metadata()

        # Validate against calculator
        results = self.validate_against_calculator()

        # Print summary
        print(f"\n📊 SUMMARY:")
        print(f"   - Excel has {results['total_excel_formulas']} calculated formulas")
        print(f"   - Calculator loaded {results['total_calculator_formulas']} formulas")

        # Check for issues
        has_issues = False

        if results['missing_in_calculator']:
            has_issues = True
            print(f"\n⚠️  MISSING IN CALCULATOR ({len(results['missing_in_calculator'])}):")
            for attr in results['missing_in_calculator']:
                print(f"   - {attr}: {self.excel_formulas[attr]}")

        if results['extra_in_calculator']:
            has_issues = True
            print(f"\n⚠️  EXTRA IN CALCULATOR ({len(results['extra_in_calculator'])}):")
            for attr in results['extra_in_calculator']:
                print(f"   - {attr}")

        if results['formula_changes']:
            has_issues = True
            print(f"\n⚠️  FORMULA CHANGES ({len(results['formula_changes'])}):")
            for change in results['formula_changes']:
                print(f"   - {change}")

        if not has_issues:
            print("\n✅ ALL CHECKS PASSED - Excel and Calculator are in sync!")
        else:
            print("\n❌ SYNC ISSUES DETECTED - Please review and update calculator!")

        print("="*80)

        return not has_issues


def run_validation(
    excel_path: str = "/Users/tusharsikand/Documents/Projects/liases-foras/change-request/managed-rag/LF-Layers_FULLY_ENRICHED_ALL_36.xlsx",
    export_json: bool = True
):
    """
    Run full validation and optionally export metadata

    Args:
        excel_path: Path to Excel file
        export_json: Whether to export metadata JSON

    Returns:
        True if validation passed, False otherwise
    """
    validator = FormulaValidator(excel_path)

    # Print validation report
    passed = validator.print_validation_report()

    # Export metadata if requested
    if export_json:
        validator.export_metadata_json()

    return passed


if __name__ == "__main__":
    # Run validation when executed directly
    passed = run_validation(export_json=True)

    if not passed:
        print("\n⚠️  ACTION REQUIRED:")
        print("   1. Review the differences above")
        print("   2. Update the calculator or Excel file as needed")
        print("   3. Re-run this validation script")
    else:
        print("\n✅ System is ready - all formulas are in sync!")
