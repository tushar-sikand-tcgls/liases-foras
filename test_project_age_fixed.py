"""Test project age query after fix"""
import requests
import json

API_BASE_URL = "http://localhost:8000"

def test_project_age():
    """Test project age query"""

    query = "What is project age of Sara city"

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

        print("Full Response:")
        print(json.dumps(data, indent=2))
        print()

        if data.get("status") == "success" and "answer" in data:
            answer = data["answer"]
            result = answer.get("result", {})
            understanding = answer.get("understanding", {})

            value = result.get("value")
            unit = result.get("unit")
            dimension = result.get("dimension")
            layer = understanding.get("layer")

            print(f"\n{'='*70}")
            print("RESULT SUMMARY:")
            print(f"{'='*70}")
            print(f"Value:     {value} {unit}")
            print(f"Dimension: {dimension}")
            print(f"Layer:     {layer}")
            print()

            # VALIDATION
            if dimension == "T":
                print(f"✅ PASS: Dimension is correct (T - Time)")
            else:
                print(f"❌ FAIL: Dimension should be T, got {dimension}")

            if value and value > 0:
                print(f"✅ PASS: Got a calculated value ({value} {unit})")
            else:
                print(f"❌ FAIL: Value is {value}")

            # Check if value is reasonable (Sara City launched Nov 2007)
            # Current date is Dec 2025, so ~217 months
            if value and 210 <= value <= 225:
                print(f"✅ PASS: Value is reasonable (~18 years = ~217 months)")
            elif value:
                print(f"⚠️  WARNING: Value {value} months seems off (expected ~217)")

        elif data.get("status") == "error":
            print(f"❌ ERROR: {data.get('error')}")
            if "debug" in data:
                print(f"\nDebug Info:")
                print(json.dumps(data["debug"], indent=2))
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        print(response.text)


def test_time_to_possession():
    """Test time to possession query"""

    query = "How many months until possession for Sara city?"

    print(f"\n\n{'='*70}")
    print(f"Testing Query: '{query}'")
    print(f"{'='*70}\n")

    response = requests.post(
        f"{API_BASE_URL}/api/qa/question",
        json={"question": query, "project_id": None},
        timeout=30
    )

    if response.status_code == 200:
        data = response.json()

        if data.get("status") == "success" and "answer" in data:
            result = data["answer"].get("result", {})
            value = result.get("value")
            unit = result.get("unit")
            dimension = result.get("dimension")

            print(f"✅ SUCCESS: {value} {unit} (dimension: {dimension})")

            # Sara City possession is Dec 2027, so ~24 months from Dec 2025
            if value and 20 <= value <= 30:
                print(f"✅ PASS: Value is reasonable (~2 years until possession)")
        else:
            print(f"❌ ERROR: {data.get('error')}")


if __name__ == "__main__":
    test_project_age()
    test_time_to_possession()

    print(f"\n{'='*70}")
    print("TEST COMPLETE")
    print(f"{'='*70}\n")
