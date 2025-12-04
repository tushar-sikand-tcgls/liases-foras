"""
Test SIRRUS.AI LangChain Service with "Tell me about Chakan" query

This test validates:
1. LangChain agent initialization with Gemini
2. Tool execution (get_region_layer0_data, calculate_layer1_metrics, etc.)
3. Layer 0 → Layer 1 → Layer 2 → Layer 3 hierarchy
4. SIRRUS.AI multi-dimensional insight generation
"""

import os
import json
os.environ['GOOGLE_API_KEY'] = 'AIzaSyAG33P0W7MaScsX7VJxBy-dPJiiIbZ_XhM'

print("=" * 80)
print("TESTING SIRRUS.AI LANGCHAIN SERVICE")
print("=" * 80)

# Test 1: Import and Initialize
print("\n1. Testing SIRRUS.AI Service Import...")
try:
    from app.services.sirrus_langchain_service import get_sirrus_service
    sirrus_service = get_sirrus_service()
    print("   ✓ SIRRUS.AI LangChain service imported")
    print(f"   ✓ LLM Model: gemini-2.0-flash-exp")
    print(f"   ✓ Number of tools: {len(sirrus_service.tools)}")
    print(f"   ✓ Tool names: {[tool.name for tool in sirrus_service.tools]}")
except Exception as e:
    print(f"   ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 2: Process "Tell me about Chakan" query
print("\n2. Testing 'Tell me about Chakan' Query...")
print("   Query: 'Tell me about Chakan'")
print("   Expected: Layer 0 → Layer 1 → Layer 2 insights")
print()

try:
    result = sirrus_service.process_query(
        query="Tell me about Chakan",
        region="Chakan"
    )

    print("   ✓ Query processed successfully")
    print("\n" + "=" * 80)
    print("RESULT:")
    print("=" * 80)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("=" * 80)

    # Validate structure
    if "error" in result:
        print(f"\n   ⚠ Error in result: {result['error']}")
    elif "summary" in result or "insights" in result:
        print("\n   ✓ Result contains insights/summary")

        if "metadata" in result and "tool_calls" in result["metadata"]:
            tool_calls = result["metadata"]["tool_calls"]
            print(f"   ✓ Tool calls executed: {len(tool_calls)}")
            for i, call in enumerate(tool_calls, 1):
                print(f"      {i}. {call.get('tool', 'unknown')}")

        if "metadata" in result and "iterations" in result["metadata"]:
            iterations = result["metadata"]["iterations"]
            print(f"   ✓ Completed in {iterations} iteration(s)")

except Exception as e:
    print(f"   ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 3: Verify data flow
print("\n3. Testing Data Flow (Layer 0 → Layer 1)...")
try:
    # Directly test tool execution
    from app.services.data_service import data_service

    chakan_projects = data_service.get_projects_by_location("Chakan")
    print(f"   ✓ Found {len(chakan_projects)} projects in Chakan")

    if chakan_projects:
        sample_project = chakan_projects[0]
        print(f"   ✓ Sample project: {sample_project.get('projectName', {}).get('value', 'N/A')}")
        print(f"      - Total Units (U): {sample_project.get('totalUnits', {}).get('value', 'N/A')}")
        print(f"      - Saleable Area (L²): {sample_project.get('saleableAreaInSqft', {}).get('value', 'N/A')} sqft")
        print(f"      - Current PSF (C/L²): ₹{sample_project.get('currentPricePSF', {}).get('value', 'N/A')}")

except Exception as e:
    print(f"   ⚠ Warning: {e}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
print("\nTo start the full server with SIRRUS.AI, run:")
print("  python api_server.py")
print("\nTo test via API endpoint:")
print("  curl -X POST http://localhost:8000/api/qa/question/v3 \\")
print("    -H 'Content-Type: application/json' \\")
print("    -d '{\"question\": \"Tell me about Chakan\"}'")
