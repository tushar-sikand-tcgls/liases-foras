"""
Comprehensive Excel Attribute Validation

Parses LF-Layers_ENRICHED_v3.xlsx and validates all Layer0 (40) and Layer1 (25) attributes
by testing formulas against sample values and expected answers.
"""

import pandas as pd
import re
import sys
from typing import Dict, Any, Optional, Tuple


# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


class ExcelAttributeValidator:
    """Validates enriched layer attributes from Excel file"""

    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.layer0_df = None
        self.layer1_df = None
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.results = []

    def load_excel(self):
        """Load Excel file and read both sheets"""
        print(f"{Colors.BOLD}Loading Excel file: {self.excel_path}{Colors.END}")
        try:
            self.layer0_df = pd.read_excel(self.excel_path, sheet_name='Layer0')
            self.layer1_df = pd.read_excel(self.excel_path, sheet_name='Layer1')
            print(f"{Colors.GREEN}✓ Loaded Layer0: {len(self.layer0_df)} rows{Colors.END}")
            print(f"{Colors.GREEN}✓ Loaded Layer1: {len(self.layer1_df)} rows{Colors.END}")
            return True
        except Exception as e:
            print(f"{Colors.RED}✗ Error loading Excel: {e}{Colors.END}")
            return False

    def parse_formula(self, formula_str: str) -> Optional[str]:
        """Parse formula string and extract calculation logic"""
        if pd.isna(formula_str):
            return None

        # Direct extraction formula
        if formula_str.lower().strip() in ['direct extraction', 'extraction', 'extract']:
            return 'DIRECT_EXTRACTION'

        return formula_str.strip()

    def evaluate_formula(self, formula: str, sample_values: str, expected_answer: Any) -> Tuple[bool, Any, str]:
        """
        Evaluate formula with sample values

        Returns:
            Tuple of (success, calculated_value, error_message)
        """
        if formula == 'DIRECT_EXTRACTION':
            # For direct extraction, sample value should equal expected answer
            try:
                # Clean up sample values
                sample = str(sample_values).strip()
                expected = str(expected_answer).strip()

                if sample == expected:
                    return True, sample, ""
                else:
                    return False, sample, f"Direct extraction: sample != expected"
            except Exception as e:
                return False, None, f"Error: {str(e)}"

        # For calculation formulas
        try:
            # Parse sample values (e.g., "1109 × 11%" or "106Cr,527 units,411 sqft")
            variables = self._parse_sample_values(sample_values)

            # Evaluate formula
            result = self._evaluate_expression(formula, variables)

            # Compare with expected answer
            expected_num = self._parse_number(expected_answer)
            result_num = self._parse_number(result)

            if expected_num is not None and result_num is not None:
                # Allow 2% tolerance
                tolerance = abs(expected_num * 0.02)
                if abs(result_num - expected_num) <= tolerance:
                    return True, result_num, ""
                else:
                    diff_pct = abs(result_num - expected_num) / expected_num * 100 if expected_num != 0 else 999
                    return False, result_num, f"Difference: {diff_pct:.2f}%"
            else:
                return False, result, "Could not parse numbers for comparison"

        except Exception as e:
            return False, None, f"Evaluation error: {str(e)}"

    def _parse_sample_values(self, sample_str: str) -> Dict[str, float]:
        """Parse sample values string into variable dictionary"""
        variables = {}

        # Pattern 1: "1109 × 11%" → supply=1109, percent=11
        # Pattern 2: "106Cr,527 units,411 sqft" → value=106, units=527, size=411
        # Pattern 3: "3996−2200" → current=3996, launch=2200

        # Remove extra spaces
        sample_str = ' '.join(sample_str.split())

        # Split by common delimiters
        parts = re.split(r'[,;/]', sample_str)

        for part in parts:
            # Extract number and unit/label
            # Example: "1109 × 11%" → [1109, 11]
            numbers = re.findall(r'[-+]?\d*\.?\d+', part)

            if 'Cr' in part or 'cr' in part:
                if numbers:
                    variables['value_cr'] = float(numbers[0])
            elif 'unit' in part.lower():
                if numbers:
                    variables['units'] = float(numbers[0])
            elif 'sqft' in part.lower() or 'sq' in part.lower():
                if numbers:
                    variables['size'] = float(numbers[0])
            elif '%' in part:
                if numbers:
                    variables['percent'] = float(numbers[0])
            elif '×' in part or '*' in part:
                if len(numbers) >= 2:
                    variables['value1'] = float(numbers[0])
                    variables['value2'] = float(numbers[1])
            elif '−' in part or '-' in part:
                if len(numbers) >= 2:
                    variables['current'] = float(numbers[0])
                    variables['launch'] = float(numbers[1])

        return variables

    def _evaluate_expression(self, formula: str, variables: Dict[str, float]) -> float:
        """Evaluate mathematical expression with variables"""
        # Replace formula placeholders with actual values
        # This is a simplified evaluator - extend as needed

        # Common formula patterns:
        # "Supply × Unsold%" → value1 × value2
        # "(Current−Launch)/Launch" → (current - launch) / launch
        # "Value×1e7/(Units×Size)" → value_cr * 1e7 / (units * size)

        expression = formula.lower()

        # Substitute common patterns
        substitutions = {
            'supply': 'value1',
            'units': 'units',
            'size': 'size',
            'current': 'current',
            'launch': 'launch',
            'value': 'value_cr',
            'annual sales': 'value1',
            '12': '12'
        }

        # Build eval-safe expression
        for key, var in substitutions.items():
            expression = expression.replace(key, str(variables.get(var, 0)))

        # Handle common operators
        expression = expression.replace('×', '*').replace('÷', '/')

        try:
            # Safe eval with limited scope
            result = eval(expression, {"__builtins__": {}}, variables)
            return float(result)
        except:
            raise ValueError(f"Cannot evaluate: {formula}")

    def _parse_number(self, value: Any) -> Optional[float]:
        """Parse number from string (handles formats like '122', '2.78', '~4860', '20.02 Cr')"""
        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            # Remove common non-numeric characters
            cleaned = value.replace(',', '').replace('~', '').replace('Avg.', '').strip()

            # Extract first number
            match = re.search(r'[-+]?\d*\.?\d+', cleaned)
            if match:
                return float(match.group())

        return None

    def validate_layer(self, df: pd.DataFrame, layer_name: str):
        """Validate all attributes in a layer"""
        print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}Validating {layer_name} ({len(df)} attributes){Colors.END}")
        print(f"{Colors.BOLD}{'='*80}{Colors.END}\n")

        for idx, row in df.iterrows():
            target_attr = row.get('Target Attribute', 'Unknown')
            formula_str = row.get('Formula/Derivation', '')
            sample_values = row.get('Sample Values', '')
            expected_answer = row.get('Expected Answer', '')

            # Parse formula
            formula = self.parse_formula(formula_str)

            if formula is None:
                print(f"{Colors.YELLOW}⚠ {target_attr}: No formula (SKIPPED){Colors.END}")
                self.skipped += 1
                self.results.append({
                    "layer": layer_name,
                    "attribute": target_attr,
                    "status": "SKIPPED",
                    "reason": "No formula"
                })
                continue

            # Skip if no sample values or expected answer
            if pd.isna(sample_values) or pd.isna(expected_answer):
                print(f"{Colors.YELLOW}⚠ {target_attr}: Missing test data (SKIPPED){Colors.END}")
                self.skipped += 1
                self.results.append({
                    "layer": layer_name,
                    "attribute": target_attr,
                    "status": "SKIPPED",
                    "reason": "Missing test data"
                })
                continue

            # Evaluate formula
            success, calculated, error_msg = self.evaluate_formula(formula, sample_values, expected_answer)

            if success:
                print(f"{Colors.GREEN}✓ {target_attr}: {calculated} (PASSED){Colors.END}")
                self.passed += 1
                self.results.append({
                    "layer": layer_name,
                    "attribute": target_attr,
                    "status": "PASSED",
                    "expected": expected_answer,
                    "calculated": calculated
                })
            else:
                print(f"{Colors.RED}✗ {target_attr}: {error_msg} (FAILED){Colors.END}")
                print(f"   Formula: {formula}")
                print(f"   Sample: {sample_values}")
                print(f"   Expected: {expected_answer}, Got: {calculated}")
                self.failed += 1
                self.results.append({
                    "layer": layer_name,
                    "attribute": target_attr,
                    "status": "FAILED",
                    "formula": formula,
                    "expected": expected_answer,
                    "calculated": calculated,
                    "error": error_msg
                })

    def print_summary(self):
        """Print validation summary"""
        total = self.passed + self.failed + self.skipped
        pass_rate = (self.passed / (self.passed + self.failed) * 100) if (self.passed + self.failed) > 0 else 0

        print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}VALIDATION SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{'='*80}{Colors.END}")
        print(f"Total Attributes: {total}")
        print(f"{Colors.GREEN}Passed: {self.passed}{Colors.END}")
        print(f"{Colors.RED}Failed: {self.failed}{Colors.END}")
        print(f"{Colors.YELLOW}Skipped: {self.skipped}{Colors.END}")
        print(f"Pass Rate: {pass_rate:.1f}%")

        if self.failed > 0:
            print(f"\n{Colors.BOLD}FAILED ATTRIBUTES:{Colors.END}")
            for result in self.results:
                if result["status"] == "FAILED":
                    print(f"  {Colors.RED}✗{Colors.END} {result['layer']}: {result['attribute']}")
                    print(f"      Error: {result.get('error', 'Unknown')}")

        print(f"{Colors.BOLD}{'='*80}{Colors.END}\n")

        if self.failed > 0:
            sys.exit(1)

    def run_validation(self):
        """Run complete validation"""
        if not self.load_excel():
            sys.exit(1)

        # Validate Layer0
        self.validate_layer(self.layer0_df, "Layer0")

        # Validate Layer1
        self.validate_layer(self.layer1_df, "Layer1")

        # Print summary
        self.print_summary()


if __name__ == "__main__":
    validator = ExcelAttributeValidator("change-request/enriched-layers/LF-Layers_ENRICHED_v3.xlsx")
    validator.run_validation()
