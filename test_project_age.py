"""Test project age query to debug dimension mismatch"""
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

            value = result.get("value")
            unit = result.get("unit")
            dimension = result.get("dimension")

            print(f"\n{'='*70}")
            print("DIMENSION CHECK:")
            print(f"{'='*70}")
            print(f"Query asks for: Project Age (expected dimension: T - Time)")
            print(f"Response value: {value} {unit}")
            print(f"Response dimension: {dimension}")

            # VALIDATION CHECK
            if dimension == "T":
                print(f"\n✅ PASS: Dimension matches (Time)")
            elif dimension == "U":
                print(f"\n❌ FAIL: Dimension mismatch!")
                print(f"   Expected: T (Time)")
                print(f"   Got: U (Units)")
                print(f"   This is likely the hardcoded project size (3018 units)")
            else:
                print(f"\n⚠️  WARNING: Unexpected dimension '{dimension}'")

        else:
            print(f"Error: {data.get('error', 'Unknown')}")
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_project_age()
