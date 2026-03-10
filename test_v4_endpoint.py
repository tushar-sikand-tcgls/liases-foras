"""Test v4 endpoint response format"""
import requests
import json

API_BASE_URL = "http://localhost:8000"

def test_v4_endpoint():
    """Test the /api/qa/question/v4 endpoint"""

    query = "what is absorption rate in sara city"

    print(f"\n{'='*70}")
    print(f"Testing v4 Endpoint: '{query}'")
    print(f"{'='*70}\n")

    response = requests.post(
        f"{API_BASE_URL}/api/qa/question/v4",
        json={
            "question": query,
            "project_id": None,
            "region": None,
            "session_id": None
        },
        timeout=30
    )

    print(f"Status Code: {response.status_code}\n")

    if response.status_code == 200:
        data = response.json()

        print("Response Structure:")
        print(json.dumps(data, indent=2))
        print()

        # Check what fields are present
        print(f"\n{'='*70}")
        print("Response Fields:")
        print(f"{'='*70}")
        for key in data.keys():
            print(f"  - {key}: {type(data[key]).__name__}")
        print()

        return data
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        print(response.text)
        return None

if __name__ == "__main__":
    test_v4_endpoint()
