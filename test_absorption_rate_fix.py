"""
Test script to verify absorption rate query fix

Tests that "what is absorption rate in sara city" returns
calculated value (0.44 %/month) NOT hardcoded value (3018 Units)
"""

import requests
import json

API_BASE_URL = "http://localhost:8000"

def test_absorption_rate_query():
    """Test absorption rate query returns calculation, not hardcoded value"""

    query = "what is absorption rate in sara city"

    print(f"\n{'='*70}")
    print(f"Testing Query: '{query}'")
    print(f"{'='*70}\n")

    response = requests.post(
        f"{API_BASE_URL}/api/qa/question",
        json={"question": query, "project_id": None},
        timeout=30
    )

    print(f"Status Code: {response.status_code}\n")

    if response.status_code == 200:
        data = response.json()

        # Pretty print response
        print("Full Response:")
        print(json.dumps(data, indent=2))
        print()

        # Check for success
        if data.get("status") == "success":
            answer = data.get("answer", {})
            result = answer.get("result", {})
            calculation = answer.get("calculation", {})
            understanding = answer.get("understanding", {})

            # Extract key values
            value = result.get("value")
            unit = result.get("unit")
            text = result.get("text")
            formula = calculation.get("formula")
            layer = understanding.get("layer")

            print(f"{'='*70}")
            print("RESULT SUMMARY:")
            print(f"{'='*70}")
            print(f"Value:   {value} {unit}")
            print(f"Text:    {text}")
            print(f"Formula: {formula}")
            print(f"Layer:   {layer}")
            print()

            # Verify fix worked
            if value == 3018 and unit == "Units":
                print("❌ FAILED: Still returning hardcoded value (3018 Units)")
                print("   Expected: ~0.44 %/month (calculated absorption rate)")
                return False
            elif "Direct retrieval from Knowledge Graph" in str(formula):
                print("❌ FAILED: Still showing 'Direct retrieval' formula")
                print("   Expected: Formula with calculation")
                return False
            elif unit in ["%/month", "%/year", "Pct/Year"]:
                print("✅ SUCCESS: Returning calculated absorption rate!")
                print(f"   Value: {value} {unit}")
                print(f"   Formula: {formula}")
                return True
            else:
                print(f"⚠️  UNEXPECTED: Got value={value} {unit}")
                print(f"   Expected absorption rate in %/month or %/year")
                return False

        elif data.get("status") == "error":
            error = data.get("error", "Unknown error")
            debug = data.get("debug", {})

            print(f"{'='*70}")
            print("ERROR RESPONSE:")
            print(f"{'='*70}")
            print(f"Error: {error}")
            if debug:
                print(f"\nDebug Info:")
                print(json.dumps(debug, indent=2))

            # Check if it's the expected error (enriched calculator issue)
            if "Layer 1 calculated metric" in error or "enriched calculator" in error.lower():
                print("\n✓ Query correctly identified as Layer 1 calculation")
                print("  (Error indicates enriched calculator needs fixing)")
                return None  # Partial success - routing is correct
            else:
                print("\n❌ Unexpected error")
                return False
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        print(response.text)
        return False

if __name__ == "__main__":
    result = test_absorption_rate_query()

    print(f"\n{'='*70}")
    if result == True:
        print("✅ TEST PASSED: Fix is working correctly!")
    elif result == None:
        print("⚠️  TEST PARTIAL: Routing fixed, but enriched calculator needs work")
    else:
        print("❌ TEST FAILED: Fix did not work")
    print(f"{'='*70}\n")
