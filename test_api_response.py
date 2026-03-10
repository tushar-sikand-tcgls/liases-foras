import requests
import json

response = requests.post(
    'http://localhost:8000/api/atlas/hybrid/query',
    json={"question": "Show me total demand for years 2020-2023"},
    timeout=30
)

if response.status_code == 200:
    data = response.json()
    print(f"Has answer: {'answer' in data}")
    print(f"Answer length: {len(data.get('answer', ''))}")
    print(f"\nFirst 1000 characters:")
    print(data.get('answer', '')[:1000])
    print("\n\n=== Looking for Chakan link ===")
    answer = data.get('answer', '')
    if 'Chakan' in answer:
        # Find Chakan and show 200 chars around it
        idx = answer.find('Chakan')
        print(answer[max(0, idx-50):idx+200])
else:
    print(f"Error: {response.status_code}")
    print(response.text)
