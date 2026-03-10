"""Test Price Growth Rate calculation"""

import requests

# Test price growth rate query
query = "What is the annual price growth rate for Sara City?"
print(f"Testing query: '{query}'")
print("=" * 60)

response = requests.post(
    "http://localhost:8000/api/qa/question",
    json={"question": query, "project_id": None}
)

if response.status_code == 200:
    result = response.json()

    print(f"Status: {result['status']}")

    if result['status'] == 'success' and 'answer' in result:
        answer = result['answer']

        # Check routing
        if 'understanding' in answer:
            understanding = answer['understanding']
            print(f"\nRouting:")
            print(f"  Layer: {understanding.get('layer')}")
            print(f"  Operation: {understanding.get('operation')}")
            print(f"  Confidence: {understanding.get('confidence')}")

        # Check result
        if 'result' in answer:
            res = answer['result']
            print(f"\nResult:")
            print(f"  Value: {res.get('value')} {res.get('unit')}")
            print(f"  Metric: {res.get('metric')}")
            print(f"  Dimension: {res.get('dimension')}")

        # Check calculation details
        if 'calculation' in answer:
            calc = answer['calculation']
            print(f"\nCalculation:")
            print(f"  Formula: {calc.get('formula')}")
            print(f"  Description: {calc.get('description')}")

        # Check provenance
        if 'provenance' in answer:
            prov = answer['provenance']
            print(f"\nProvenance:")
            print(f"  Source: {prov.get('source')}")
            print(f"  Attribute: {prov.get('attribute')}")

        # Validation
        if 'result' in answer:
            res = answer['result']
            value = res.get('value')
            dimension = res.get('dimension')

            print("\n" + "=" * 60)
            print("VALIDATION:")
            print("=" * 60)

            # Check dimension
            if dimension in ['C/L²/T', '%/Year', 'T⁻¹']:
                print(f"✅ PASS: Dimension is correct ({dimension})")
            else:
                print(f"❌ FAIL: Expected dimension C/L²/T or %/Year, got {dimension}")

            # Check value is reasonable (typically 5-15% per year)
            if value and 0 < value < 50:
                print(f"✅ PASS: Value is reasonable ({value:.2f}% per year)")
            else:
                print(f"⚠️  WARNING: Value seems unusual ({value})")

            # Check routing
            if understanding.get('layer') == 'LAYER_1':
                print(f"✅ PASS: Routed to Layer 1 (calculated metric)")
            else:
                print(f"❌ FAIL: Expected Layer 1, got {understanding.get('layer')}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
        print(f"Full response: {result}")
else:
    print(f"HTTP Error {response.status_code}")
    print(response.text)
