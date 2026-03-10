"""
Comprehensive Validation Test for All Enriched Layer Attributes

This test validates all Layer 1 (calculated) attributes from the enriched layers knowledge graph.
Tests are organized by attribute ID and verify formulas match the knowledge graph definitions.

References:
- change-request/enriched-layers/enriched_layers_knowledge.json
- app/services/enriched_layers_service.py
- app/calculators/enriched_calculator.py
"""

import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional

# API Configuration
API_BASE_URL = "http://localhost:8000"
QA_ENDPOINT = f"{API_BASE_URL}/api/qa/question"

# Test Data: Sara City Project (known reference data)
SARA_CITY_DATA = {
    "projectName": "sara city",
    "totalSupplyUnits": 1109,
    "soldPct": 89.0,
    "unsoldPct": 11.0,
    "annualSalesUnits": 527,
    "annualSalesValue": 106,  # Rs Cr
    "unitSaleableSize": 411,  # Sqft
    "launchPricePSF": 2200,
    "currentPricePSF": 3996,
    "monthlySalesVelocity": 3.47,  # %/month
    "launchDate": "Nov 2007",
    "possessionDate": "Dec 2027",
    "currentDate": "Dec 2024"
}

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class AttributeValidator:
    """Validates enriched layer attributes against knowledge graph definitions"""

    def __init__(self):
        self.test_results = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def query_api(self, question: str) -> Optional[Dict[str, Any]]:
        """Send question to API and return response"""
        try:
            response = requests.post(
                QA_ENDPOINT,
                json={"question": question, "project_id": None},
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                print(f"{Colors.RED}HTTP Error {response.status_code}{Colors.END}")
                return None

        except Exception as e:
            print(f"{Colors.RED}API Error: {str(e)}{Colors.END}")
            return None

    def calculate_expected(self, attribute_id: str) -> Optional[float]:
        """Calculate expected value based on formula definition"""

        formulas = {
            # L1_1: Unsold Units
            "L1_1": SARA_CITY_DATA["totalSupplyUnits"] * (SARA_CITY_DATA["unsoldPct"] / 100),

            # L1_2: Sold Units
            "L1_2": SARA_CITY_DATA["totalSupplyUnits"] * (SARA_CITY_DATA["soldPct"] / 100),

            # L1_3: Monthly Units Sold
            "L1_3": SARA_CITY_DATA["annualSalesUnits"] / 12,

            # L1_4: Months of Inventory
            "L1_4": (SARA_CITY_DATA["totalSupplyUnits"] * SARA_CITY_DATA["unsoldPct"] / 100) / (SARA_CITY_DATA["annualSalesUnits"] / 12),

            # L1_5: Price Growth (%)
            "L1_5": ((SARA_CITY_DATA["currentPricePSF"] - SARA_CITY_DATA["launchPricePSF"]) / SARA_CITY_DATA["launchPricePSF"]) * 100,

            # L1_6: Realised PSF
            "L1_6": (SARA_CITY_DATA["annualSalesValue"] * 1e7) / (SARA_CITY_DATA["annualSalesUnits"] * SARA_CITY_DATA["unitSaleableSize"]),

            # L1_7: Revenue per Unit
            "L1_7": (SARA_CITY_DATA["annualSalesValue"] * 1e7) / SARA_CITY_DATA["annualSalesUnits"],

            # L1_8: Monthly Velocity (Units)
            "L1_8": (SARA_CITY_DATA["monthlySalesVelocity"] / 100) * SARA_CITY_DATA["totalSupplyUnits"],

            # L1_9: Unsold Inventory Value
            "L1_9": ((SARA_CITY_DATA["totalSupplyUnits"] * SARA_CITY_DATA["unsoldPct"] / 100) * SARA_CITY_DATA["unitSaleableSize"] * SARA_CITY_DATA["currentPricePSF"]) / 1e7,

            # L1_13: Average Ticket Size
            "L1_13": SARA_CITY_DATA["unitSaleableSize"] * SARA_CITY_DATA["currentPricePSF"],

            # L1_14: Launch Ticket Size
            "L1_14": SARA_CITY_DATA["unitSaleableSize"] * SARA_CITY_DATA["launchPricePSF"],

            # L1_15: PSF Gap
            "L1_15": SARA_CITY_DATA["currentPricePSF"] - SARA_CITY_DATA["launchPricePSF"],

            # L1_18: Months to Sell Remaining
            "L1_18": (SARA_CITY_DATA["totalSupplyUnits"] * SARA_CITY_DATA["unsoldPct"] / 100) / (SARA_CITY_DATA["annualSalesUnits"] / 12),

            # L1_22: Price Growth Rate (% per Year) - requires project age
            # Project Age: Nov 2007 to Dec 2024 = ~205 months = 17.08 years
            "L1_22": ((SARA_CITY_DATA["currentPricePSF"] - SARA_CITY_DATA["launchPricePSF"]) / SARA_CITY_DATA["launchPricePSF"] * 100) / 17.08,

            # L1_27: Absorption Rate
            # (Sold Units / Total Supply) / Duration Months × 100
            # (987 / 1109) / 205 × 100 = 0.43%/month
            "L1_27": ((SARA_CITY_DATA["totalSupplyUnits"] * SARA_CITY_DATA["soldPct"] / 100) / SARA_CITY_DATA["totalSupplyUnits"]) / 205 * 100,

            # L1_33: Project Age (Months)
            # Nov 2007 to Dec 2024 = 17 years * 12 + 1 month = 205 months
            "L1_33": 205,

            # L1_34: Time to Possession (Months)
            # Dec 2027 - Dec 2024 = 36 months
            "L1_34": 36,
        }

        return formulas.get(attribute_id)

    def parse_numeric_result(self, result: Any) -> Optional[float]:
        """Extract numeric value from API result"""
        if isinstance(result, (int, float)):
            return float(result)

        if isinstance(result, str):
            # Try to extract number from string
            import re
            # Remove commas and extract number
            cleaned = result.replace(',', '').strip()
            match = re.search(r'[-+]?\d*\.?\d+', cleaned)
            if match:
                return float(match.group())

        return None

    def validate_attribute(
        self,
        attribute_id: str,
        attribute_name: str,
        query: str,
        expected_value: Optional[float],
        tolerance_pct: float = 2.0
    ) -> bool:
        """Validate a single attribute"""

        print(f"\n{Colors.BOLD}Testing {attribute_id}: {attribute_name}{Colors.END}")
        print(f"Query: {Colors.BLUE}{query}{Colors.END}")

        if expected_value is None:
            print(f"{Colors.YELLOW}⚠ No expected value defined - skipping validation{Colors.END}")
            self.warnings += 1
            return True

        print(f"Expected: {expected_value:.2f}")

        # Query API
        response = self.query_api(query)

        if not response:
            print(f"{Colors.RED}✗ FAILED: No API response{Colors.END}")
            self.failed += 1
            self.test_results.append({
                "id": attribute_id,
                "name": attribute_name,
                "status": "FAILED",
                "reason": "No API response"
            })
            return False

        # Check for error response
        if response.get("status") == "error":
            print(f"{Colors.RED}✗ FAILED: {response.get('error', 'Unknown error')}{Colors.END}")
            self.failed += 1
            self.test_results.append({
                "id": attribute_id,
                "name": attribute_name,
                "status": "FAILED",
                "reason": response.get("error", "Unknown error")
            })
            return False

        # Extract result value
        actual_value = None

        # Try different response structures
        if "answer" in response and "result" in response["answer"]:
            result_data = response["answer"]["result"]
            if "value" in result_data:
                actual_value = self.parse_numeric_result(result_data["value"])
            else:
                actual_value = self.parse_numeric_result(result_data)
        elif "result" in response:
            actual_value = self.parse_numeric_result(response["result"])

        if actual_value is None:
            print(f"{Colors.RED}✗ FAILED: Could not parse numeric result from response{Colors.END}")
            print(f"Response: {json.dumps(response, indent=2)}")
            self.failed += 1
            self.test_results.append({
                "id": attribute_id,
                "name": attribute_name,
                "status": "FAILED",
                "reason": "Could not parse result"
            })
            return False

        print(f"Actual: {actual_value:.2f}")

        # Calculate tolerance
        tolerance = abs(expected_value * tolerance_pct / 100)
        difference = abs(actual_value - expected_value)
        difference_pct = (difference / expected_value * 100) if expected_value != 0 else 0

        if difference <= tolerance:
            print(f"{Colors.GREEN}✓ PASSED (difference: {difference_pct:.2f}%){Colors.END}")
            self.passed += 1
            self.test_results.append({
                "id": attribute_id,
                "name": attribute_name,
                "status": "PASSED",
                "expected": expected_value,
                "actual": actual_value,
                "difference_pct": difference_pct
            })
            return True
        else:
            print(f"{Colors.RED}✗ FAILED: Difference {difference_pct:.2f}% exceeds tolerance {tolerance_pct}%{Colors.END}")
            self.failed += 1
            self.test_results.append({
                "id": attribute_id,
                "name": attribute_name,
                "status": "FAILED",
                "expected": expected_value,
                "actual": actual_value,
                "difference_pct": difference_pct
            })
            return False

    def run_all_tests(self):
        """Run comprehensive validation test suite"""

        print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}COMPREHENSIVE ENRICHED ATTRIBUTES VALIDATION TEST{Colors.END}")
        print(f"{Colors.BOLD}{'='*80}{Colors.END}")
        print(f"Test Project: {SARA_CITY_DATA['projectName'].upper()}")
        print(f"Total Attributes to Test: 26 (Layer 1 calculated attributes)")
        print(f"{Colors.BOLD}{'='*80}{Colors.END}")

        # Test each attribute
        test_cases = [
            # Basic calculations
            ("L1_1", "Unsold Units", "Unsold units of Sara City"),
            ("L1_2", "Sold Units", "Sold units of Sara City"),
            ("L1_3", "Monthly Units Sold", "Monthly units sold of Sara City"),
            ("L1_4", "Months of Inventory", "Months of inventory for Sara City"),

            # Price metrics
            ("L1_5", "Price Growth (%)", "Price growth of Sara City"),
            ("L1_6", "Realised PSF", "Realised PSF of Sara City"),
            ("L1_15", "PSF Gap", "PSF gap for Sara City"),

            # Revenue metrics
            ("L1_7", "Revenue per Unit", "Revenue per unit of Sara City"),
            ("L1_13", "Average Ticket Size", "Average ticket size of Sara City"),
            ("L1_14", "Launch Ticket Size", "Launch ticket size of Sara City"),

            # Velocity metrics
            ("L1_8", "Monthly Velocity (Units)", "Monthly velocity units for Sara City"),

            # Inventory valuation
            ("L1_9", "Unsold Inventory Value", "Unsold inventory value of Sara City"),

            # Timeline metrics (recently added)
            ("L1_18", "Months to Sell Remaining", "Months to sell remaining for Sara City"),
            ("L1_22", "Price Growth Rate (% per Year)", "Price growth rate of Sara City"),
            ("L1_27", "Absorption Rate", "Absorption rate of Sara City"),
            ("L1_33", "Project Age (Months)", "Project age of Sara City"),
            ("L1_34", "Time to Possession (Months)", "Time to possession for Sara City"),
        ]

        for attribute_id, attribute_name, query in test_cases:
            expected = self.calculate_expected(attribute_id)
            self.validate_attribute(attribute_id, attribute_name, query, expected)

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}TEST SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{'='*80}{Colors.END}")

        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0

        print(f"Total Tests: {total}")
        print(f"{Colors.GREEN}Passed: {self.passed}{Colors.END}")
        print(f"{Colors.RED}Failed: {self.failed}{Colors.END}")
        print(f"{Colors.YELLOW}Warnings: {self.warnings}{Colors.END}")
        print(f"Pass Rate: {pass_rate:.1f}%")

        if self.failed > 0:
            print(f"\n{Colors.BOLD}FAILED TESTS:{Colors.END}")
            for result in self.test_results:
                if result["status"] == "FAILED":
                    print(f"  {Colors.RED}✗{Colors.END} {result['id']}: {result['name']}")
                    if "reason" in result:
                        print(f"    Reason: {result['reason']}")
                    elif "difference_pct" in result:
                        print(f"    Expected: {result['expected']:.2f}, Actual: {result['actual']:.2f}")
                        print(f"    Difference: {result['difference_pct']:.2f}%")

        print(f"{Colors.BOLD}{'='*80}{Colors.END}\n")

        # Exit with error code if tests failed
        if self.failed > 0:
            exit(1)

if __name__ == "__main__":
    validator = AttributeValidator()
    validator.run_all_tests()
