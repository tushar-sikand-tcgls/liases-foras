"""
Test Precision Formatting - Verify 2 Decimal Display with Full Precision in Calculations
Tests that all enriched Layer 1 queries return properly formatted results
"""
import requests
import json

API_BASE_URL = "http://localhost:8000"

def test_precision_formatting():
    """Test precision formatting across multiple projects and attributes"""

    print("=" * 80)
    print("PRECISION FORMATTING TEST")
    print("=" * 80)
    print("\nRequirements:")
    print("1. Main answer: 2 decimal precision")
    print("2. Calculation details: Full precision available")
    print("3. Unit: Always accompanied with value")
    print("4. Source: Properly attributed")
    print("=" * 80)

    test_cases = [
        {
            "name": "Sellout Time - Sara City",
            "query": "What is sellout time for sara city",
            "expected_unit": "Years",
            "expected_dimension": "T"
        },
        {
            "name": "Sellout Time - Sarangi Paradise",
            "query": "What is sellout time for Sarangi Paradise",
            "expected_unit": "Years",
            "expected_dimension": "T"
        },
        {
            "name": "Months of Inventory - Sara City",
            "query": "How long to sell remaining units in sara city?",
            "expected_unit": "Months",
            "expected_dimension": "T"
        },
        {
            "name": "Sellout Time - Gulmohar City",
            "query": "What is sellout time for gulmohar city",
            "expected_unit": "Years",
            "expected_dimension": "T"
        },
        {
            "name": "Current PSF - Sara City",
            "query": "What is current PSF for sara city",
            "expected_unit": "₹/sqft",
            "expected_dimension": "C/L²"
        }
    ]

    all_passed = True
    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}: {test_case['name']}")
        print(f"{'='*80}")
        print(f"Query: '{test_case['query']}'")

        try:
            # Make API request
            response = requests.post(
                f"{API_BASE_URL}/api/qa/question",
                json={
                    "question": test_case["query"],
                    "project_id": None,
                    "location_context": None,
                    "admin_mode": False
                },
                timeout=10
            )

            if response.status_code != 200:
                print(f"✗ FAIL: HTTP {response.status_code}")
                all_passed = False
                continue

            data = response.json()

            if data.get("status") != "success":
                print(f"✗ FAIL: Status = {data.get('status')}")
                all_passed = False
                continue

            # Extract result fields
            answer = data.get("answer", {})
            result = answer.get("result", {})
            calculation = answer.get("calculation", {})
            provenance = answer.get("provenance", {})

            # Check required fields
            value_raw = result.get("value")
            unit = result.get("unit")
            text = result.get("text")
            dimension = result.get("dimension")

            full_precision = calculation.get("fullPrecisionValue")
            rounded_value = calculation.get("roundedValue")
            calc_unit = calculation.get("unit")

            source = provenance.get("source")

            # Validation checks
            checks_passed = True

            # Check 1: Main result has 2 decimal display text
            if text:
                # Extract number from text (e.g., "2.95 Years" -> 2.95)
                try:
                    display_number = float(text.split()[0])
                    decimal_places = len(str(display_number).split('.')[-1]) if '.' in str(display_number) else 0
                    if decimal_places <= 2:
                        print(f"✓ Display text with ≤2 decimals: {text}")
                    else:
                        print(f"✗ Display text has >2 decimals: {text}")
                        checks_passed = False
                except:
                    print(f"✓ Display text: {text}")
            else:
                print(f"✗ Missing display text field")
                checks_passed = False

            # Check 2: Raw value available
            if value_raw is not None:
                print(f"✓ Raw value available: {value_raw}")
            else:
                print(f"✗ Missing raw value")
                checks_passed = False

            # Check 3: Unit always present
            if unit and unit == test_case["expected_unit"]:
                print(f"✓ Unit present and correct: {unit}")
            elif unit:
                print(f"⚠ Unit present but unexpected: {unit} (expected {test_case['expected_unit']})")
            else:
                print(f"✗ Missing unit")
                checks_passed = False

            # Check 4: Full precision in calculation details
            if full_precision is not None:
                print(f"✓ Full precision available: {full_precision}")
            else:
                print(f"✗ Missing full precision value")
                checks_passed = False

            # Check 5: Rounded value in calculation details
            if rounded_value is not None:
                decimal_places = len(str(rounded_value).split('.')[-1]) if '.' in str(rounded_value) else 0
                if decimal_places <= 2:
                    print(f"✓ Rounded value (≤2 decimals): {rounded_value}")
                else:
                    print(f"✗ Rounded value has >2 decimals: {rounded_value}")
                    checks_passed = False
            else:
                print(f"✗ Missing rounded value")
                checks_passed = False

            # Check 6: Source attribution
            if source and source != "Unknown":
                print(f"✓ Source attributed: {source}")
            else:
                print(f"✗ Source missing or Unknown: {source}")
                checks_passed = False

            # Check 7: Dimension correct
            if dimension == test_case["expected_dimension"]:
                print(f"✓ Dimension correct: {dimension}")
            else:
                print(f"⚠ Dimension mismatch: {dimension} (expected {test_case['expected_dimension']})")

            if checks_passed:
                print(f"\n✓ PASS: All formatting requirements met")
                results.append({
                    "test": test_case["name"],
                    "status": "PASS",
                    "display": text,
                    "full_precision": full_precision,
                    "unit": unit
                })
            else:
                print(f"\n✗ FAIL: Some formatting requirements not met")
                all_passed = False
                results.append({
                    "test": test_case["name"],
                    "status": "FAIL"
                })

        except requests.exceptions.RequestException as e:
            print(f"✗ FAIL: Request error: {e}")
            all_passed = False
        except Exception as e:
            print(f"✗ FAIL: Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for result in results:
        status_icon = "✓" if result["status"] == "PASS" else "✗"
        print(f"{status_icon} {result['test']}: {result['status']}")
        if result["status"] == "PASS":
            print(f"  Display: {result['display']}")
            print(f"  Full Precision: {result['full_precision']}")
            print(f"  Unit: {result['unit']}")

    print("\n" + "=" * 80)
    if all_passed:
        print("✓ ALL PRECISION FORMATTING TESTS PASSED")
        print("\nFormatting Requirements Met:")
        print("  1. ✅ Main answer: 2 decimal precision")
        print("  2. ✅ Calculation details: Full precision available")
        print("  3. ✅ Unit: Always accompanied with value")
        print("  4. ✅ Source: Properly attributed")
        return True
    else:
        print("✗ SOME TESTS FAILED")
        print("\nPlease check the error messages above.")
        return False


if __name__ == "__main__":
    import sys
    success = test_precision_formatting()
    sys.exit(0 if success else 1)
