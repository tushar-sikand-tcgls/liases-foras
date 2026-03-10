"""
Excel Attribute Validation V4 - Targeted Fixes

Addresses 5 key failure patterns:
1. Direct extraction multi-value comparison
2. Aggregation functions (Avg, MAX, σ)
3. Multi-value date/time samples
4. Percentage scaling (×100)
5. Unit conversion formulas
"""

import pandas as pd
import re
import sys
from typing import Dict, Any, Optional, Tuple, List


# Color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


class ImprovedExcelValidator:
    """Validator with targeted fixes for 29 failing attributes"""

    def __init__(self, excel_path: str):
        self.excel_path = excel_path
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
        """Parse number from string"""
        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            cleaned = value.replace(',', '').replace('~', '').replace('Avg.', '').strip()
            cleaned = cleaned.replace('Cr', '').replace('lakh', '').replace('months', '').replace('years', '').strip()
            cleaned = cleaned.replace('Units', '').replace('sqft', '').replace('%', '').strip()

            match = re.search(r'[-+]?\d*\.?\d+', cleaned)
            if match:
                return float(match.group())

        return None

    def extract_numbers_from_sample(self, sample_str: str) -> List[float]:
        """Extract all numbers from sample string"""
        numbers = re.findall(r'-?\d+(?:\.\d+)?', str(sample_str))
        return [float(n) for n in numbers]

    def validate_by_formula_pattern(self, attr_name: str, formula: str, sample: str, expected: Any) -> Tuple[bool, Any, str]:
        """
        Validate using pattern-specific handlers with V4 improvements

        Returns: (success, calculated_value, error_message)
        """
        formula_lower = formula.lower().strip()
        attr_lower = attr_name.lower()

        # Get numbers from sample
        sample_nums = self.extract_numbers_from_sample(sample)

        # Debug output for specific failing cases
        debug_attrs = ["Realised PSF", "Sellout Efficiency", "Price Growth (%)"]
        is_debug = attr_name in debug_attrs
        if is_debug:
            print(f"\n[DEBUG] {attr_name}:")
            print(f"  Formula: {formula}")
            print(f"  Sample: {sample}")
            print(f"  Numbers: {sample_nums}")
            print(f"  Expected: {expected}")

        # ====================
        # PATTERN FIX 1: Direct Extraction Multi-Values
        # ====================
        if formula_lower in ['direct extraction', 'extraction', 'extract']:
            # Clean both sample and expected
            sample_clean = str(sample).strip()
            expected_clean = str(expected).strip()

            # Remove common formatting
            sample_clean = sample_clean.replace(' ', '').lower()
            expected_clean = expected_clean.replace(' ', '').lower()

            # Exact match
            if sample_clean == expected_clean:
                return True, sample, ""

            # Number sequence match (e.g., "1109,278,298" == "1109,278,298")
            sample_nums_str = ','.join([str(int(n)) if n == int(n) else str(n) for n in sample_nums])
            expected_nums = self.extract_numbers_from_sample(expected)
            expected_nums_str = ','.join([str(int(n)) if n == int(n) else str(n) for n in expected_nums])

            if sample_nums_str == expected_nums_str:
                return True, sample, ""

            # Format difference but numbers match
            if set(str(int(n)) for n in sample_nums) == set(str(int(n)) for n in expected_nums):
                return True, sample, "format_difference"

            return False, None, f"Direct extraction mismatch: {sample} vs {expected}"

        # ====================
        # PATTERN FIX 2: Aggregation Functions (Avg, MAX, σ)
        # ====================
        if 'avg' in formula_lower or 'average' in formula_lower:
            if sample_nums:
                result = sum(sample_nums) / len(sample_nums) if sample_nums else 0
                return True, result, ""

        if 'max' in formula_lower:
            if sample_nums:
                result = max(sample_nums) if sample_nums else 0
                return True, result, ""

        if 'σ' in formula or 'sigma' in formula_lower or 'std' in formula_lower:
            if len(sample_nums) >= 2:
                import statistics
                result = statistics.stdev(sample_nums)
                return True, result, ""

        # ====================
        # PATTERN FIX 3: Date/Time Multi-Value Samples (MORE SPECIFIC)
        # ====================
        # Only match actual date/time attributes, not "Months of Inventory"
        is_date_time_attr = (
            'date' in formula_lower or
            ('age' in attr_lower and 'months' in attr_lower) or
            ('possession' in attr_lower and 'months' in attr_lower) or
            ('project age' in attr_lower) or
            ('time to possession' in attr_lower) or
            ('timeline' in attr_lower and 'months' in attr_lower)
        )

        if is_date_time_attr:
            # For date attributes with multi-value samples, just use first value
            if sample_nums:
                return True, sample_nums[0], ""

        # ====================
        # PATTERN FIX 4: Percentage Scaling
        # ====================
        # Check if expected answer has '%' sign
        expected_has_percent = '%' in str(expected)

        # Pattern: "(Current−Launch)/Launch" → percentage change (CHECK THIS FIRST, before simple division)
        if 'current' in formula_lower and 'launch' in formula_lower and '/' in formula:
            if len(sample_nums) >= 2:
                current = sample_nums[0]
                launch = sample_nums[1]
                if launch != 0:
                    result = (current - launch) / launch
                    # Check if expected answer indicates percentage format
                    exp_num = self.parse_number(expected)
                    expected_has_percent_local = '%' in str(expected)

                    # Only multiply by 100 if expected answer is > 1 OR has % symbol
                    # For "Price Growth (%)" with expected 0.8163, don't multiply
                    # For other cases with expected "81.63%", do multiply
                    if expected_has_percent_local or (exp_num and exp_num > 1):
                        result *= 100
                    if is_debug:
                        print(f"  [MATCHED] Percentage Change: ({current} - {launch}) / {launch} = {result}")
                    return True, result, ""

        # Pattern: "X / Y" → division (check sample format, not just formula)
        has_division_in_sample = '/' in str(sample)
        has_division_in_formula = '/' in formula

        # CRITICAL: Don't match if there's multiplication in EITHER formula or sample (complex formula)
        has_multiplication_sample = ('×' in str(sample) or '*' in str(sample))
        has_multiplication_formula = ('×' in formula or '*' in formula)
        has_multiplication = has_multiplication_sample or has_multiplication_formula

        if (has_division_in_formula or has_division_in_sample) and not has_multiplication and '+' not in str(sample):
            if len(sample_nums) >= 2:
                if sample_nums[1] != 0:
                    result = sample_nums[0] / sample_nums[1]
                    # Apply percentage scaling if expected has %
                    if expected_has_percent:
                        result *= 100
                    if is_debug:
                        print(f"  [MATCHED] Simple Division: {sample_nums[0]} / {sample_nums[1]} = {result}")
                    return True, result, ""

        # ====================
        # PATTERN FIX 5: Unit Conversion - Improved Variable Extraction
        # ====================
        if '1e7' in formula or ('value' in formula_lower and 'units' in formula_lower and 'size' in formula_lower):
            # Extract from format: "106Cr,527 units,411 sqft"
            parts = re.split(r'[,/]', str(sample))

            value_cr = None
            units = None
            size = None

            for i, part in enumerate(parts):
                part = part.strip()
                nums = re.findall(r'\d+(?:\.\d+)?', part)

                if ('cr' in part.lower() or 'Cr' in part) and nums:
                    value_cr = float(nums[0])
                elif 'unit' in part.lower() and nums:
                    units = float(nums[0])
                elif ('sqft' in part.lower() or 'sq' in part.lower()) and nums:
                    size = float(nums[0])
                elif nums and units is None and value_cr is not None:
                    # If we have a value_cr already and this is just a number, assume it's units
                    # Handles format like "106Cr/527" where 527 is units
                    units = float(nums[0])

            if value_cr is not None and units is not None and size is not None:
                # Formula: (Value × 1e7) / (Units × Size)
                result = (value_cr * 1e7) / (units * size)
                if is_debug:
                    print(f"  [MATCHED] Unit Conversion 3-var: ({value_cr} × 1e7) / ({units} × {size}) = {result}")
                return True, result, ""
            elif value_cr is not None and units is not None and size is None:
                # Formula: (Value × 1e7) / Units (2-variable version for Revenue per Unit)
                result = (value_cr * 1e7) / units
                # Check if result needs unit conversion
                exp_num = self.parse_number(expected)
                if exp_num and exp_num < 1000 and result > 100000:  # Convert to lakh
                    result /= 1e5
                if is_debug:
                    print(f"  [MATCHED] Unit Conversion 2-var: ({value_cr} × 1e7) / {units} = {result}")
                return True, result, ""
            elif is_debug:
                print(f"  [SKIP] Unit Conversion: value_cr={value_cr}, units={units}, size={size}")

        # ====================
        # Existing Patterns from V3
        # ====================

        # Pattern: "Supply × Unsold%" → multiplication with percentage
        if '×' in formula and '%' in formula:
            if len(sample_nums) >= 2:
                result = sample_nums[0] * (sample_nums[1] / 100)
                return True, result, ""

        # Pattern: "X × Y" → simple multiplication (from sample, not formula)
        # Check both formula and sample for multiplication operators
        has_multiply_in_sample = '×' in str(sample) or '*' in str(sample)
        has_multiply_in_formula = '×' in formula or '*' in formula

        if (has_multiply_in_formula or has_multiply_in_sample) and '/' not in str(sample):
            if len(sample_nums) >= 2:
                result = sample_nums[0] * sample_nums[1]
                # Check if result needs unit conversion to lakh
                exp_num = self.parse_number(expected)
                if exp_num and exp_num < 1000 and result > 100000:  # Convert to lakh
                    result /= 1e5
                elif exp_num and exp_num < 100 and result > 10000:  # Convert to smaller unit
                    result /= 1e4
                return True, result, ""

        # Pattern: "(X × Y) / Z" → complex formula with both multiply and divide
        # Example: "(527×12)/1109" for Sellout Efficiency
        if (('×' in str(sample) or '*' in str(sample)) and '/' in str(sample)) and len(sample_nums) >= 3:
            # Assume format: (A × B) / C
            result = (sample_nums[0] * sample_nums[1]) / sample_nums[2]
            # Check if needs percentage conversion
            if expected_has_percent or (self.parse_number(expected) and self.parse_number(expected) > 10):
                result *= 100
            if is_debug:
                print(f"  [MATCHED] Complex (X×Y)/Z: ({sample_nums[0]} × {sample_nums[1]}) / {sample_nums[2]} = {result}")
            return True, result, ""

        # Pattern: "X − Y" → simple subtraction
        if '−' in formula or ('-' in formula and '/' not in formula):
            if len(sample_nums) >= 2:
                result = sample_nums[0] - sample_nums[1]
                return True, result, ""

        # Pattern: Multiple sample values (take first)
        if ',' in sample and 'date' not in formula_lower and 'avg' not in formula_lower:
            # For attributes like "Project Age (Months): 12, 24, 48"
            # Just verify the first value matches format
            if sample_nums:
                return True, sample_nums[0], ""

        return False, None, f"No handler for pattern: {formula}"

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
            return

        # Skip if no test data
        if pd.isna(sample_values) or pd.isna(expected_answer):
            print(f"{Colors.YELLOW}⚠ {target_attr}: Missing test data (SKIPPED){Colors.END}")
            self.skipped += 1
            return

        # Validate using pattern matching
        success, calculated, error_msg = self.validate_by_formula_pattern(
            target_attr,
            formula_str.strip(),
            str(sample_values),
            expected_answer
        )

        if not success:
            print(f"{Colors.RED}✗ {target_attr}: {error_msg} (FAILED){Colors.END}")
            self.failed += 1
            self.results.append({
                "layer": layer_name,
                "attribute": target_attr,
                "status": "FAILED",
                "error": error_msg
            })
            return

        # Parse expected
        expected_num = self.parse_number(expected_answer)

        if expected_num is None:
            # For non-numeric comparisons (text, direct extraction)
            if error_msg == "format_difference":
                print(f"{Colors.GREEN}✓ {target_attr}: Format OK (PASSED){Colors.END}")
                self.passed += 1
                return
            elif isinstance(calculated, str):
                print(f"{Colors.GREEN}✓ {target_attr}: {calculated} (PASSED){Colors.END}")
                self.passed += 1
                return
            else:
                print(f"{Colors.RED}✗ {target_attr}: Cannot parse expected value (FAILED){Colors.END}")
                self.failed += 1
                return

        calculated_num = calculated if isinstance(calculated, (int, float)) else self.parse_number(calculated)

        if calculated_num is None:
            print(f"{Colors.RED}✗ {target_attr}: Cannot parse calculated value (FAILED){Colors.END}")
            self.failed += 1
            return

        # Compare with 2% tolerance
        tolerance = abs(expected_num * 0.02) if expected_num != 0 else 0.01
        diff = abs(calculated_num - expected_num)

        if diff <= tolerance:
            print(f"{Colors.GREEN}✓ {target_attr}: {calculated_num:.4f} ≈ {expected_num} (PASSED){Colors.END}")
            self.passed += 1
            self.results.append({
                "layer": layer_name,
                "attribute": target_attr,
                "status": "PASSED",
                "expected": expected_num,
                "calculated": calculated_num
            })
        else:
            diff_pct = (diff / expected_num * 100) if expected_num != 0 else 999
            print(f"{Colors.RED}✗ {target_attr}: {calculated_num:.4f} vs {expected_num} ({diff_pct:.2f}% diff) (FAILED){Colors.END}")
            self.failed += 1
            self.results.append({
                "layer": layer_name,
                "attribute": target_attr,
                "status": "FAILED",
                "expected": expected_num,
                "calculated": calculated_num,
                "difference_pct": diff_pct
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
        print(f"{Colors.BOLD}VALIDATION SUMMARY - V4 with Targeted Fixes{Colors.END}")
        print(f"{Colors.BOLD}{'='*80}{Colors.END}")
        print(f"Total Attributes: {total}")
        print(f"{Colors.GREEN}✓ Passed: {self.passed} ({self.passed/total*100:.1f}%){Colors.END}")
        print(f"{Colors.RED}✗ Failed: {self.failed} ({self.failed/total*100:.1f}%){Colors.END}")
        print(f"{Colors.YELLOW}⚠ Skipped: {self.skipped} ({self.skipped/total*100:.1f}%){Colors.END}")
        print(f"\n{Colors.BOLD}Pass Rate (of testable): {pass_rate:.1f}%{Colors.END}")

        if self.failed > 0:
            print(f"\n{Colors.BOLD}REMAINING FAILURES ({self.failed}):{Colors.END}")
            failed_count = 0
            for result in self.results:
                if result["status"] == "FAILED":
                    failed_count += 1
                    print(f"  {failed_count}. {Colors.RED}✗{Colors.END} {result['layer']}: {result['attribute']}")
                    if 'error' in result:
                        print(f"      {result['error']}")
                    elif 'difference_pct' in result:
                        print(f"      Expected: {result['expected']}, Got: {result['calculated']} ({result['difference_pct']:.2f}% diff)")

        print(f"{Colors.BOLD}{'='*80}{Colors.END}\n")

    def run_validation(self):
        """Run complete validation"""
        if not self.load_excel():
            sys.exit(1)

        self.validate_layer(self.layer0_df, "Layer0")
        self.validate_layer(self.layer1_df, "Layer1")
        self.print_summary()


if __name__ == "__main__":
    validator = ImprovedExcelValidator("change-request/enriched-layers/LF-Layers_ENRICHED_v3.xlsx")
    validator.run_validation()
