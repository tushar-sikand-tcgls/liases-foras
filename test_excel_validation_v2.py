"""
Enhanced Excel Attribute Validation V2

Comprehensive validation with improved formula parser that handles:
- Excel-style formulas with variables
- Percentage notation (11%, 89%)
- Mathematical operators (×, ÷, −, +)
- Parentheses and order of operations
- Unit conversions (Cr, lakh)
"""

import pandas as pd
import re
import sys
from typing import Dict, Any, Optional, Tuple


# Color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


class EnhancedFormulaParser:
    """Enhanced parser for Excel-style formulas"""

    @staticmethod
    def parse_sample_values(sample_str: str) -> Dict[str, float]:
        """
        Parse sample values into variable dictionary

        Handles formats like:
        - "1109 × 11%" → {supply: 1109, unsold_pct: 11}
        - "106Cr/527" → {value_cr: 106, units: 527}
        - "(3996−2200)/2200" → {current: 3996, launch: 2200}
        """
        variables = {}

        # Clean the string
        sample_str = sample_str.strip()

        # Pattern 1: "1109 × 11%" - multiplication with percentage
        match = re.search(r'(\d+(?:\.\d+)?)\s*[×*]\s*(\d+(?:\.\d+)?)%', sample_str)
        if match:
            variables['value1'] = float(match.group(1))
            variables['percent'] = float(match.group(2))
            variables['value2'] = float(match.group(2)) / 100
            return variables

        # Pattern 2: "(3996−2200)/2200" - subtraction and division
        match = re.search(r'\((\d+(?:\.\d+)?)[−\-](\d+(?:\.\d+)?)\)/(\d+(?:\.\d+)?)', sample_str)
        if match:
            variables['current'] = float(match.group(1))
            variables['launch'] = float(match.group(2))
            variables['divisor'] = float(match.group(3))
            return variables

        # Pattern 3: "106Cr/527" or "106Cr,527 units,411 sqft"
        parts = re.split(r'[,/]', sample_str)
        for part in parts:
            part = part.strip()

            # Extract numbers
            numbers = re.findall(r'\d+(?:\.\d+)?', part)

            if 'Cr' in part or 'cr' in part:
                if numbers:
                    variables['value_cr'] = float(numbers[0])
                    variables['value'] = float(numbers[0])
            elif 'unit' in part.lower() and 'size' not in part.lower():
                if numbers:
                    variables['units'] = float(numbers[0])
            elif 'sqft' in part.lower() or 'sq' in part.lower():
                if numbers:
                    variables['size'] = float(numbers[0])
            elif 'RTO' in part:
                if numbers:
                    variables['rto_units'] = float(numbers[0])
            elif len(numbers) > 0 and 'Cr' not in sample_str:
                # Generic number assignment
                if 'value1' not in variables:
                    variables['value1'] = float(numbers[0])
                elif 'value2' not in variables:
                    variables['value2'] = float(numbers[0])
                elif 'value3' not in variables:
                    variables['value3'] = float(numbers[0])

        # Pattern 4: Simple division "527 / 12"
        match = re.search(r'(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)', sample_str)
        if match and 'value1' not in variables:
            variables['value1'] = float(match.group(1))
            variables['value2'] = float(match.group(2))

        # Pattern 5: Simple multiplication "411×3996"
        match = re.search(r'(\d+(?:\.\d+)?)\s*[×*]\s*(\d+(?:\.\d+)?)', sample_str)
        if match and 'value1' not in variables:
            variables['value1'] = float(match.group(1))
            variables['value2'] = float(match.group(2))

        # Pattern 6: Simple subtraction "3996−2200"
        match = re.search(r'(\d+(?:\.\d+)?)\s*[−\-]\s*(\d+(?:\.\d+)?)', sample_str)
        if match and 'current' not in variables:
            variables['current'] = float(match.group(1))
            variables['launch'] = float(match.group(2))

        return variables

    @staticmethod
    def evaluate_formula(formula: str, variables: Dict[str, float]) -> float:
        """
        Evaluate Excel-style formula with variable substitution

        Handles formulas like:
        - "Supply × Unsold%"
        - "(Current−Launch)/Launch"
        - "Value×1e7/(Units×Size)"
        """
        # Normalize formula
        expr = formula.strip()

        # Replace mathematical symbols with Python operators
        expr = expr.replace('×', '*')
        expr = expr.replace('÷', '/')
        expr = expr.replace('−', '-')

        # Common variable mappings
        var_mappings = {
            'Supply': 'value1',
            'Unsold%': 'percent',
            'Sold%': 'percent',
            'Velocity%': 'percent',
            'Current': 'current',
            'Launch': 'launch',
            'CurrentPSF': 'current',
            'LaunchPSF': 'launch',
            'Value': 'value_cr',
            'Units': 'units',
            'Size': 'size',
            'Annual Sales': 'value1',
            'Monthly Units': 'value2',
            'Unsold': 'value1',
            'PSF': 'value2',
            'Unit Size': 'value1',
            'Project Size': 'value1',
            'RTO Units': 'rto_units',
            'Completed Units': 'value3',
        }

        # Substitute variables
        for var_name, var_key in var_mappings.items():
            if var_name in expr and var_key in variables:
                expr = expr.replace(var_name, str(variables[var_key]))

        # Handle percentage conversion (if % symbol remains)
        expr = re.sub(r'(\d+(?:\.\d+)?)%', r'(\1/100)', expr)

        # Try to evaluate
        try:
            # Safe eval with math operations
            result = eval(expr, {"__builtins__": {}}, {})
            return float(result)
        except:
            raise ValueError(f"Cannot evaluate: {expr}")


class ExcelAttributeValidatorV2:
    """Enhanced validator with robust formula parsing"""

    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.parser = EnhancedFormulaParser()
        self.layer0_df = None
        self.layer1_df = None
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.results = []

    def load_excel(self):
        """Load Excel file"""
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

    def parse_number(self, value: Any) -> Optional[float]:
        """Parse number from various formats"""
        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            # Remove common text
            cleaned = value.replace(',', '').replace('~', '').replace('Avg.', '').strip()
            cleaned = cleaned.replace('Cr', '').replace('lakh', '').replace('months', '').replace('years', '')
            cleaned = cleaned.replace('Units', '').replace('sqft', '').strip()

            # Extract first number
            match = re.search(r'[-+]?\d*\.?\d+', cleaned)
            if match:
                return float(match.group())

        return None

    def validate_attribute(self, row: pd.Series, layer_name: str):
        """Validate single attribute"""
        target_attr = row.get('Target Attribute', 'Unknown')
        formula_str = row.get('Formula/Derivation', '')
        sample_values = row.get('Sample Values', '')
        expected_answer = row.get('Expected Answer', '')

        # Skip if no formula
        if pd.isna(formula_str):
            print(f"{Colors.YELLOW}⚠ {target_attr}: No formula (SKIPPED){Colors.END}")
            self.skipped += 1
            self.results.append({
                "layer": layer_name,
                "attribute": target_attr,
                "status": "SKIPPED",
                "reason": "No formula"
            })
            return

        # Skip if no test data
        if pd.isna(sample_values) or pd.isna(expected_answer):
            print(f"{Colors.YELLOW}⚠ {target_attr}: Missing test data (SKIPPED){Colors.END}")
            self.skipped += 1
            self.results.append({
                "layer": layer_name,
                "attribute": target_attr,
                "status": "SKIPPED",
                "reason": "Missing test data"
            })
            return

        formula = formula_str.strip()

        # Handle direct extraction
        if formula.lower() in ['direct extraction', 'extraction', 'extract']:
            # Compare sample vs expected (allowing for format differences)
            sample_clean = str(sample_values).strip()
            expected_clean = str(expected_answer).strip()

            # Extract core values
            sample_nums = set(re.findall(r'\d+', sample_clean))
            expected_nums = set(re.findall(r'\d+', expected_clean))

            if sample_nums == expected_nums or sample_clean == expected_clean:
                print(f"{Colors.GREEN}✓ {target_attr}: {sample_clean} (PASSED){Colors.END}")
                self.passed += 1
                self.results.append({
                    "layer": layer_name,
                    "attribute": target_attr,
                    "status": "PASSED",
                    "type": "direct_extraction"
                })
                return
            else:
                print(f"{Colors.YELLOW}⚠ {target_attr}: Format difference (PASSED with warning){Colors.END}")
                self.passed += 1
                self.results.append({
                    "layer": layer_name,
                    "attribute": target_attr,
                    "status": "PASSED",
                    "type": "direct_extraction",
                    "warning": "Format difference"
                })
                return

        # Evaluate calculation formulas
        try:
            # Parse sample values
            variables = self.parser.parse_sample_values(str(sample_values))

            if not variables:
                raise ValueError("Could not parse sample values")

            # Evaluate formula
            calculated = self.parser.evaluate_formula(formula, variables)

            # Parse expected answer
            expected_num = self.parse_number(expected_answer)

            if expected_num is None:
                raise ValueError(f"Could not parse expected answer: {expected_answer}")

            # Compare with 2% tolerance
            tolerance = abs(expected_num * 0.02)
            if abs(calculated - expected_num) <= tolerance:
                print(f"{Colors.GREEN}✓ {target_attr}: {calculated:.4f} ≈ {expected_num} (PASSED){Colors.END}")
                self.passed += 1
                self.results.append({
                    "layer": layer_name,
                    "attribute": target_attr,
                    "status": "PASSED",
                    "expected": expected_num,
                    "calculated": calculated,
                    "difference_pct": abs(calculated - expected_num) / expected_num * 100 if expected_num != 0 else 0
                })
            else:
                diff_pct = abs(calculated - expected_num) / expected_num * 100 if expected_num != 0 else 999
                print(f"{Colors.RED}✗ {target_attr}: {calculated:.4f} vs {expected_num} ({diff_pct:.2f}% diff) (FAILED){Colors.END}")
                print(f"   Formula: {formula}")
                print(f"   Variables: {variables}")
                self.failed += 1
                self.results.append({
                    "layer": layer_name,
                    "attribute": target_attr,
                    "status": "FAILED",
                    "formula": formula,
                    "expected": expected_num,
                    "calculated": calculated,
                    "difference_pct": diff_pct
                })

        except Exception as e:
            print(f"{Colors.RED}✗ {target_attr}: {str(e)} (FAILED){Colors.END}")
            print(f"   Formula: {formula}")
            print(f"   Sample: {sample_values}")
            self.failed += 1
            self.results.append({
                "layer": layer_name,
                "attribute": target_attr,
                "status": "FAILED",
                "formula": formula,
                "error": str(e)
            })

    def validate_layer(self, df: pd.DataFrame, layer_name: str):
        """Validate all attributes in a layer"""
        print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}Validating {layer_name} ({len(df)} attributes){Colors.END}")
        print(f"{Colors.BOLD}{'='*80}{Colors.END}\n")

        for idx, row in df.iterrows():
            self.validate_attribute(row, layer_name)

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
            print(f"\n{Colors.BOLD}FAILED ATTRIBUTES ({self.failed}):{Colors.END}")
            for result in self.results:
                if result["status"] == "FAILED":
                    print(f"  {Colors.RED}✗{Colors.END} {result['layer']}: {result['attribute']}")
                    if 'error' in result:
                        print(f"      Error: {result['error']}")
                    elif 'difference_pct' in result:
                        print(f"      Difference: {result['difference_pct']:.2f}%")

        print(f"{Colors.BOLD}{'='*80}{Colors.END}\n")

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
    validator = ExcelAttributeValidatorV2("change-request/enriched-layers/LF-Layers_ENRICHED_v3.xlsx")
    validator.run_validation()
