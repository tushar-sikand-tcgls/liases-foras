"""
Test Frontend Integration - Verify Both Bugs Fixed
Tests that both Sellout Time and Months of Inventory work correctly through the API
"""
import requests

API_BASE_URL = "http://localhost:8000"

def test_frontend_api():
    """Test both queries through the /api/qa/question endpoint"""

    print("=" * 80)
    print("FRONTEND INTEGRATION TEST: Both Queries via /api/qa/question")
    print("=" * 80)

    test_cases = [
        {
            "name": "Sellout Time",
            "query": "What is sellout time for sara city",
            "expected_value_range": (2.0, 2.2),
            "expected_unit": "Years",
            "description": "Should return ~2.1 years (NOT 3018 Units)"
        },
        {
            "name": "Months of Inventory",
            "query": "How long to sell remaining units in sara city?",
            "expected_value_range": (2.7, 2.9),
            "expected_unit": "Months",
            "description": "Should return ~2.79 months (NOT 3018 Units)"
        }
    ]

    all_passed = True

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}: {test_case['name']}")
        print(f"{'='*80}")
        print(f"Query: '{test_case['query']}'")
        print(f"Expected: {test_case['expected_value_range']} {test_case['expected_unit']}")
        print(f"Description: {test_case['description']}\n")

        try:
            # Make API request
            response = requests.post(
                f"{API_BASE_URL}/api/qa/question",
                json={
                    "question": test_case["query"],
                    "project_id": "sara city",
                    "location_context": None,
                    "admin_mode": False
                },
                timeout=10
            )

            if response.status_code != 200:
                print(f"✗ FAIL: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                all_passed = False
                continue

            data = response.json()

            # Check status
            if data.get("status") != "success":
                print(f"✗ FAIL: Status = {data.get('status')}")
                print(f"Error: {data.get('error', 'Unknown error')}")
                all_passed = False
                continue

            # Extract result
            answer = data.get("answer", {})
            result = answer.get("result", {})
            value = result.get("value")
            unit = result.get("unit")
            metric = result.get("metric")

            print(f"Response Details:")
            print(f"  Status: {data.get('status')}")
            print(f"  Metric: {metric}")
            print(f"  Value: {value}")
            print(f"  Unit: {unit}")

            # Validate value
            if value is None:
                print(f"✗ FAIL: No value returned")
                all_passed = False
                continue

            # Check if value is in expected range
            min_val, max_val = test_case["expected_value_range"]
            if not (min_val <= value <= max_val):
                print(f"✗ FAIL: Value {value} not in expected range {test_case['expected_value_range']}")
                all_passed = False
                continue

            # Check unit
            if unit != test_case["expected_unit"]:
                print(f"✗ FAIL: Unit '{unit}' does not match expected '{test_case['expected_unit']}'")
                all_passed = False
                continue

            # SUCCESS
            print(f"\n✓ PASS: {test_case['name']} = {value} {unit}")
            print(f"  Formula: {answer.get('calculation', {}).get('formula', 'N/A')}")
            print(f"  Source: {answer.get('provenance', {}).get('source', 'N/A')}")

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

    if all_passed:
        print("✓ ALL TESTS PASSED")
        print("\nFrontend Integration Status:")
        print("  1. ✅ Sellout Time: Returns 2.1 years (FIXED)")
        print("  2. ✅ Months of Inventory: Returns 2.79 months (FIXED)")
        print("\nBoth bugs are now fixed on the frontend! 🎉")
        return True
    else:
        print("✗ SOME TESTS FAILED")
        print("\nPlease check the error messages above.")
        return False


if __name__ == "__main__":
    import sys
    success = test_frontend_api()
    sys.exit(0 if success else 1)
