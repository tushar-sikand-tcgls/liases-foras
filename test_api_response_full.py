import requests
import json

response = requests.post(
    'http://localhost:8000/api/atlas/hybrid/query',
    json={"question": "Show me total demand for years 2020-2023"},
    timeout=30
)

if response.status_code == 200:
    data = response.json()
    print("=== FULL RESPONSE ===")
    print(json.dumps(data, indent=2))
else:
    print(f"Error: {response.status_code}")
    print(response.text)
