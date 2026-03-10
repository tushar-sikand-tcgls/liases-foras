"""
Test Kolkata data loading with location_context
"""

import requests
import json

# API endpoint
API_URL = "http://localhost:8000/api/atlas/hybrid/query"

# Test 1: Query with Pune (Chakan) location_context
print("=" * 80)
print("TEST 1: Pune (Chakan) Query")
print("=" * 80)

pune_request = {
    "question": "Show me all projects",
    "location_context": {
        "state": "Maharashtra",
        "city": "Pune",
        "region": "Chakan"
    }
}

print(f"\n📍 Sending request with location_context: {pune_request['location_context']}")
response = requests.post(API_URL, json=pune_request, timeout=30)

if response.status_code == 200:
    result = response.json()
    print(f"\n✅ Response received:")
    print(f"   Status: {result.get('status')}")
    print(f"   Execution Time: {result.get('execution_time_ms', 0):.2f}ms")
    print(f"\n   Answer Preview (first 500 chars):")
    answer = result.get('answer', '')
    print(f"   {answer[:500]}...")
else:
    print(f"\n❌ Error: Status {response.status_code}")
    print(f"   {response.text}")

# Test 2: Query with Kolkata location_context
print("\n\n" + "=" * 80)
print("TEST 2: Kolkata Query")
print("=" * 80)

kolkata_request = {
    "question": "Show me all projects",
    "location_context": {
        "state": "West Bengal",
        "city": "Kolkata",
        "region": "0-2 KM"
    }
}

print(f"\n📍 Sending request with location_context: {kolkata_request['location_context']}")
response = requests.post(API_URL, json=kolkata_request, timeout=30)

if response.status_code == 200:
    result = response.json()
    print(f"\n✅ Response received:")
    print(f"   Status: {result.get('status')}")
    print(f"   Execution Time: {result.get('execution_time_ms', 0):.2f}ms")
    print(f"\n   Answer Preview (first 500 chars):")
    answer = result.get('answer', '')
    print(f"   {answer[:500]}...")
else:
    print(f"\n❌ Error: Status {response.status_code}")
    print(f"   {response.text}")

# Test 3: Verify different data is returned
print("\n\n" + "=" * 80)
print("TEST 3: Verify Location Switching Works")
print("=" * 80)

print("\n📊 Expected Results:")
print("   - Pune should return: Sara City, Gulmohar City, The Urbana, etc. (10 projects)")
print("   - Kolkata should return: Siddha Galaxia, Merlin Verve, PS Panache, Srijan Eternis, Ambuja Utalika (5 projects)")
print("\n✅ Check the answers above to verify different projects are returned for each city!")

print("\n" + "=" * 80)
print("Testing Complete!")
print("=" * 80)
