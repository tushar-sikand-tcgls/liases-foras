"""Test BHK Mix query routing and response"""

import requests

query = "BHK mix of sara city"
print(f"Testing query: '{query}'")
print("=" * 60)

response = requests.post(
    "http://localhost:8000/api/qa/question",
    json={"question": query, "project_id": None}
)

if response.status_code == 200:
    result = response.json()

    print(f"Status: {result.get('status')}")
    print(f"\nFull Response:")
    import json
    print(json.dumps(result, indent=2))

    # Check routing
    if 'answer' in result and 'understanding' in result['answer']:
        understanding = result['answer']['understanding']
        print(f"\n{'='*60}")
        print("ROUTING ANALYSIS:")
        print(f"{'='*60}")
        print(f"Layer: {understanding.get('layer')}")
        print(f"Operation: {understanding.get('operation')}")
        print(f"Confidence: {understanding.get('confidence')}")
        print(f"Routing: {understanding.get('routing')}")
else:
    print(f"HTTP Error {response.status_code}")
    print(response.text)
