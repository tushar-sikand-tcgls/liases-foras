"""
Test Intent Recognition in SIRRUS.AI v3

Validates that the LLM correctly identifies user intent and routes to appropriate tools:
1. DATA_RETRIEVAL → Knowledge Graph
2. CALCULATION → Python Calculators
3. COMPARISON → KG + Calculators
4. INSIGHT → GraphRAG (KG + VectorDB)
5. STRATEGIC → Layer 3 Optimization
6. CONTEXT_ENRICHMENT → Google APIs
"""

import os
import json
os.environ['GOOGLE_API_KEY'] = 'AIzaSyAG33P0W7MaScsX7VJxBy-dPJiiIbZ_XhM'

from app.services.sirrus_langchain_service import get_sirrus_service

# Test cases organized by intent category
TEST_CASES = [
    # Category 1: DATA_RETRIEVAL
    {
        "category": "DATA_RETRIEVAL",
        "query": "Tell me about Hinjewadi",
        "region": "Hinjewadi",
        "expected_tools": ["get_region_layer0_data"],
        "description": "Should fetch Layer 0 data from Knowledge Graph"
    },
    {
        "category": "DATA_RETRIEVAL",
        "query": "Show me all projects in Wakad",
        "region": "Wakad",
        "expected_tools": ["get_region_layer0_data"],
        "description": "Should query KG for projects list"
    },

    # Category 2: CALCULATION
    {
        "category": "CALCULATION",
        "query": "What's the average PSF in Chakan?",
        "region": "Chakan",
        "expected_tools": ["get_region_layer0_data", "calculate_layer1_metrics"],
        "description": "Should fetch data + calculate Layer 1 metric"
    },
    {
        "category": "CALCULATION",
        "query": "Calculate absorption rate for Chakan projects",
        "region": "Chakan",
        "expected_tools": ["get_region_layer0_data", "calculate_layer1_metrics"],
        "description": "Should use calculator for derived metric"
    },

    # Category 3: COMPARISON
    {
        "category": "COMPARISON",
        "query": "Compare Chakan vs Hinjewadi by PSF",
        "region": None,
        "expected_tools": ["get_region_layer0_data", "calculate_layer1_metrics"],
        "description": "Should fetch data for both regions + compare metrics"
    },
    {
        "category": "COMPARISON",
        "query": "Top 3 projects in Chakan by price",
        "region": "Chakan",
        "expected_tools": ["get_region_layer0_data", "calculate_layer1_metrics"],
        "description": "Should rank projects by Layer 1 metric"
    },

    # Category 4: INSIGHT
    {
        "category": "INSIGHT",
        "query": "Why is absorption low in Chakan?",
        "region": "Chakan",
        "expected_tools": ["get_region_layer0_data", "search_market_insights"],
        "description": "Should use GraphRAG: KG data + VectorDB insights"
    },
    {
        "category": "INSIGHT",
        "query": "What factors affect pricing in Hinjewadi?",
        "region": "Hinjewadi",
        "expected_tools": ["get_region_layer0_data", "search_market_insights"],
        "description": "Should query VectorDB for market intelligence"
    },

    # Category 5: STRATEGIC
    {
        "category": "STRATEGIC",
        "query": "Should I invest in Chakan?",
        "region": "Chakan",
        "expected_tools": ["get_region_layer0_data", "search_market_insights"],  # optimize_product_mix if available
        "description": "Should provide Layer 3 strategic recommendation"
    },
    {
        "category": "STRATEGIC",
        "query": "Best product mix for 100 units in Chakan",
        "region": "Chakan",
        "expected_tools": ["get_region_layer0_data", "optimize_product_mix"],  # If optimize tool available
        "description": "Should run Layer 3 optimization"
    },

    # Category 6: CONTEXT_ENRICHMENT
    {
        "category": "CONTEXT_ENRICHMENT",
        "query": "Show me map of Chakan",
        "region": "Chakan",
        "expected_tools": ["get_location_context"],
        "description": "Should use Google Maps API"
    },
    {
        "category": "CONTEXT_ENRICHMENT",
        "query": "What's nearby Chakan?",
        "region": "Chakan",
        "expected_tools": ["get_location_context"],
        "description": "Should query Google Places API"
    },
]

def analyze_tool_calls(tool_calls):
    """Extract tool names from tool_calls metadata"""
    if not tool_calls:
        return []
    return [call.get("tool") for call in tool_calls]

def test_intent_recognition():
    """Test all intent categories"""

    print("=" * 80)
    print("TESTING INTENT RECOGNITION IN SIRRUS.AI")
    print("=" * 80)

    sirrus_service = get_sirrus_service()

    results = {
        "total": len(TEST_CASES),
        "passed": 0,
        "failed": 0,
        "details": []
    }

    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}/{len(TEST_CASES)}: {test_case['category']}")
        print(f"{'='*80}")
        print(f"Query: \"{test_case['query']}\"")
        print(f"Expected Tools: {', '.join(test_case['expected_tools'])}")
        print(f"Description: {test_case['description']}")
        print()

        try:
            # Execute query
            result = sirrus_service.process_query(
                query=test_case['query'],
                region=test_case['region']
            )

            # Extract actual tools used
            actual_tools = []
            if "metadata" in result and "tool_calls" in result["metadata"]:
                actual_tools = analyze_tool_calls(result["metadata"]["tool_calls"])

            print(f"Actual Tools Used: {', '.join(actual_tools) if actual_tools else 'None'}")

            # Verify tool match
            expected_set = set(test_case['expected_tools'])
            actual_set = set(actual_tools)

            # Check if at least one expected tool was called
            if expected_set & actual_set:  # Intersection
                print("✅ PASS - Correct intent routing")
                results["passed"] += 1
                test_result = "PASS"
            else:
                print(f"❌ FAIL - Expected {test_case['expected_tools']}, got {actual_tools}")
                results["failed"] += 1
                test_result = "FAIL"

            # Show summary from response
            summary = result.get("summary", "")
            if summary:
                # Truncate long summaries
                if len(summary) > 200:
                    summary = summary[:200] + "..."
                print(f"\nSummary: {summary}")

            results["details"].append({
                "test": i,
                "category": test_case['category'],
                "query": test_case['query'],
                "expected_tools": test_case['expected_tools'],
                "actual_tools": actual_tools,
                "result": test_result
            })

        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            results["failed"] += 1
            results["details"].append({
                "test": i,
                "category": test_case['category'],
                "query": test_case['query'],
                "result": "ERROR",
                "error": str(e)
            })

    # Final summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {results['total']}")
    print(f"Passed: {results['passed']} ✅")
    print(f"Failed: {results['failed']} ❌")
    print(f"Success Rate: {(results['passed']/results['total']*100):.1f}%")

    # Breakdown by category
    print("\nBreakdown by Intent Category:")
    categories = {}
    for detail in results["details"]:
        cat = detail["category"]
        if cat not in categories:
            categories[cat] = {"passed": 0, "failed": 0}
        if detail["result"] == "PASS":
            categories[cat]["passed"] += 1
        else:
            categories[cat]["failed"] += 1

    for cat, stats in categories.items():
        total = stats["passed"] + stats["failed"]
        success_rate = (stats["passed"]/total*100) if total > 0 else 0
        print(f"  {cat}: {stats['passed']}/{total} ({success_rate:.0f}%)")

    print("\n" + "=" * 80)

    # Save detailed results
    with open("intent_recognition_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Detailed results saved to: intent_recognition_test_results.json")

if __name__ == "__main__":
    test_intent_recognition()
