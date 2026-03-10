#!/usr/bin/env python3
"""Test PSF Gap proximity query"""

import requests
import json

# Test the query
url = "http://localhost:8000/api/atlas/hybrid/query"
payload = {
    "question": "List top 3 projects by PSF Gap within 2 KM of Sara city",
    "city": "Pune",
    "region": "Chakan"
}

print("="*80)
print("Testing PSF Gap Proximity Query")
print("="*80)
print(f"\nQuestion: {payload['question']}")
print(f"City: {payload['city']}")
print(f"Region: {payload['region']}")
print("\nSending request...")

try:
    response = requests.post(url, json=payload, timeout=30)

    print(f"\nStatus Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print("\n" + "="*80)
        print("RESPONSE:")
        print("="*80)
        print(json.dumps(data, indent=2))
    else:
        print(f"\nError: {response.text}")

except Exception as e:
    print(f"\nException: {e}")
