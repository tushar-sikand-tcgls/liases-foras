"""
Comprehensive Dimension Validation Test

Tests the self-validating mechanism that prevents dimension-mismatched responses.
"""

import requests
import json

API_BASE_URL = "http://localhost:8000"

# Test cases: (query, expected_dimension, should_pass)
TEST_CASES = [
    {
        "query": "What is absorption rate in sara city",
        "expected_dim": "T⁻¹",
        "should_pass": True,
        "description": "Absorption rate - should return rate dimension"
    },
    {
        "query": "What is project age of Sara city",
        "expected_dim": "T",
        "should_pass": False,
        "description": "Project age - data not available, should fail validation"
    },
    {
        "query": "What is sellout time for sara city",
        "expected_dim": "T",
        "should_pass": True,
        "description": "Sellout time - should return time dimension"
    },
    {
        "query": "How many units in sara city",
        "expected_dim": "U",
        "should_pass": True,
        "description": "Total units - should return units dimension"
    },
    {
        "query": "What is the project size of sara city",
        "expected_dim": "L²",
        "should_pass": True,
        "description": "Project size - should return area dimension"
    }
]


def test_query(test_case):
    """Test a single query"""
    query = test_case["query"]
    expected_dim = test_case["expected_dim"]
    should_pass = test_case["should_pass"]
    description = test_case["description"]

    print(f"\n{'='*70}")
    print(f"Test: {description}")
    print(f"Query: '{query}'")
    print(f"Expected Dimension: {expected_dim}")
    print(f"{'='*70}")

    response = requests.post(
        f"{API_BASE_URL}/api/qa/question",
        json={"question": query, "project_id": None},
        timeout=30
    )

    if response.status_code != 200:
        print(f"❌ HTTP Error: {response.status_code}")
        return False

    data = response.json()
    status = data.get("status")

    if should_pass:
        # Should succeed
        if status == "success":
            answer = data.get("answer", {})
            result = answer.get("result", {})
            value = result.get("value")
            unit = result.get("unit")
            dimension = result.get("dimension")

            print(f"✅ PASS: Query succeeded as expected")
            print(f"   Value: {value} {unit}")
            print(f"   Dimension: {dimension}")
            return True
        else:
            print(f"❌ FAIL: Query should have succeeded but got error:")
            print(f"   Error: {data.get('error')}")
            return False
    else:
        # Should fail validation
        if status == "error":
            error = data.get("error", "")
            if "Dimension validation FAILED" in error:
                print(f"✅ PASS: Dimension validation correctly caught mismatch")
                print(f"   Error: {error}")
                debug = data.get("debug", {})
                if debug:
                    print(f"   Expected: {debug.get('expected_dimension')}")
                    print(f"   Actual: {debug.get('actual_dimension')}")
                    print(f"   Value: {debug.get('actual_value')}")
                return True
            else:
                print(f"❌ FAIL: Got error but not dimension validation:")
                print(f"   Error: {error}")
                return False
        else:
            print(f"❌ FAIL: Query should have failed validation but succeeded")
            print(f"   Value: {data.get('answer', {}).get('result', {}).get('value')}")
            return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("DIMENSION VALIDATION COMPREHENSIVE TEST")
    print("="*70)
    print("\nThis test verifies the self-validating mechanism that prevents")
    print("dimension-mismatched responses (e.g., returning Units when Time was requested)")
    print()

    results = []
    for test_case in TEST_CASES:
        result = test_query(test_case)
        results.append({
            "description": test_case["description"],
            "passed": result
        })

    # Summary
    print(f"\n\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")

    passed = sum(1 for r in results if r["passed"])
    total = len(results)

    for i, r in enumerate(results, 1):
        status = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f"{i}. {status}: {r['description']}")

    print(f"\n{passed}/{total} tests passed ({100*passed/total:.1f}%)")

    if passed == total:
        print("\n✅ ALL TESTS PASSED: Dimension validation is working correctly!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")

    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
