"""
ATLAS Performance Test - <2 Second Target

Tests the performance-optimized ATLAS adapter with:
1. Interactions API V2 (working)
2. File Search (managed RAG)
3. Knowledge Graph (function calling)

Target: <2 seconds end-to-end
"""

import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from app.adapters.atlas_performance_adapter import get_atlas_performance_adapter
    from app.adapters.data_service_kg_adapter import get_data_service_kg_adapter
except ImportError as e:
    print(f"❌ ERROR: Failed to import: {e}")
    print("Make sure google-genai is installed: pip install google-genai")
    sys.exit(1)


def test_kg_query_performance():
    """
    Test 1: KG query performance (Project Size)
    Target: <2 seconds
    """
    print(f"\n{'='*80}")
    print(f"TEST 1: Knowledge Graph Query (Quantitative Data)")
    print(f"{'='*80}\n")

    print("Query: What is the Project Size of Sara City?")
    print("Expected tool: Knowledge Graph")
    print(f"Target: <2000ms\n")

    # Initialize adapters
    kg_adapter = get_data_service_kg_adapter()
    atlas_adapter = get_atlas_performance_adapter(kg_adapter=kg_adapter)

    # Execute query
    start = time.time()
    result = atlas_adapter.query("What is the Project Size of Sara City?")
    elapsed = time.time() - start

    # Display results
    print(f"\n⏱️  PERFORMANCE:")
    print(f"   Execution Time: {result.execution_time_ms:.2f}ms")
    print(f"   Actual Time: {elapsed*1000:.2f}ms")
    print(f"   Tool Used: {result.tool_used}")
    print(f"   Interaction ID: {result.interaction_id}")

    print(f"\n📝 ANSWER:")
    print(f"   {result.answer[:200]}...")

    if result.function_results:
        print(f"\n📊 FUNCTION RESULTS:")
        print(f"   {result.function_results}")

    # Check performance
    print(f"\n✅ TARGET: <2000ms")
    if result.execution_time_ms < 2000:
        print(f"✅ PASS: {result.execution_time_ms:.2f}ms (under target)")
        return True
    else:
        print(f"❌ FAIL: {result.execution_time_ms:.2f}ms (exceeded target by {result.execution_time_ms - 2000:.2f}ms)")
        return False


def test_file_search_query_performance():
    """
    Test 2: File Search query performance (Qualitative/Definition)
    Target: <2 seconds
    """
    print(f"\n{'='*80}")
    print(f"TEST 2: File Search Query (Qualitative/Definition)")
    print(f"{'='*80}\n")

    print("Query: What is Absorption Rate? (definition)")
    print("Expected tool: File Search")
    print(f"Target: <2000ms\n")

    # Initialize adapter
    atlas_adapter = get_atlas_performance_adapter()

    # Execute query
    start = time.time()
    result = atlas_adapter.query("What is Absorption Rate? Provide the definition from the glossary.")
    elapsed = time.time() - start

    # Display results
    print(f"\n⏱️  PERFORMANCE:")
    print(f"   Execution Time: {result.execution_time_ms:.2f}ms")
    print(f"   Actual Time: {elapsed*1000:.2f}ms")
    print(f"   Tool Used: {result.tool_used}")

    print(f"\n📝 ANSWER:")
    print(f"   {result.answer[:300]}...")

    # Check performance
    print(f"\n✅ TARGET: <2000ms")
    if result.execution_time_ms < 2000:
        print(f"✅ PASS: {result.execution_time_ms:.2f}ms (under target)")
        return True
    else:
        print(f"❌ FAIL: {result.execution_time_ms:.2f}ms (exceeded target by {result.execution_time_ms - 2000:.2f}ms)")
        return False


def test_autonomous_tool_selection():
    """
    Test 3: Gemini autonomously selects correct tool
    """
    print(f"\n{'='*80}")
    print(f"TEST 3: Autonomous Tool Selection")
    print(f"{'='*80}\n")

    # Initialize adapters
    kg_adapter = get_data_service_kg_adapter()
    atlas_adapter = get_atlas_performance_adapter(kg_adapter=kg_adapter)

    test_cases = [
        ("What is the Project Size of Sara City?", "knowledge_graph", "Quantitative data query"),
        ("What is PSF? Define it.", "file_search", "Definition query"),
        ("List all projects in Chakan", "knowledge_graph", "Data listing query"),
    ]

    results = []
    for query, expected_tool, description in test_cases:
        print(f"\n📋 Test Case: {description}")
        print(f"   Query: {query}")
        print(f"   Expected Tool: {expected_tool}")

        result = atlas_adapter.query(query)

        print(f"   Actual Tool: {result.tool_used}")
        print(f"   Time: {result.execution_time_ms:.2f}ms")

        correct = result.tool_used == expected_tool or (
            expected_tool == "knowledge_graph" and result.tool_used == "knowledge_graph"
        )
        results.append(correct)

        if correct:
            print(f"   ✅ Correct tool selected")
        else:
            print(f"   ⚠️  Different tool selected (may still be valid)")

    passed = sum(results)
    total = len(results)

    print(f"\n✅ TOOL SELECTION: {passed}/{total} correct")
    return passed == total


def run_stress_test(num_queries=5):
    """
    Test 4: Stress test with multiple queries
    Target: Average <2 seconds
    """
    print(f"\n{'='*80}")
    print(f"TEST 4: Stress Test ({num_queries} queries)")
    print(f"{'='*80}\n")

    # Initialize adapters
    kg_adapter = get_data_service_kg_adapter()
    atlas_adapter = get_atlas_performance_adapter(kg_adapter=kg_adapter)

    queries = [
        "What is the Project Size of Sara City?",
        "What is the PSF of Sara City?",
        "What is the Launch Date of Sara City?",
        "List all projects in Chakan",
        "What is Absorption Rate? Define it."
    ]

    times = []
    for i, query in enumerate(queries[:num_queries], 1):
        print(f"\n[{i}/{num_queries}] {query}")
        result = atlas_adapter.query(query)
        times.append(result.execution_time_ms)
        print(f"         Time: {result.execution_time_ms:.2f}ms | Tool: {result.tool_used}")

    avg_time = sum(times) / len(times)
    max_time = max(times)
    min_time = min(times)

    print(f"\n📊 STATISTICS:")
    print(f"   Average: {avg_time:.2f}ms")
    print(f"   Min: {min_time:.2f}ms")
    print(f"   Max: {max_time:.2f}ms")
    print(f"   Target: <2000ms average")

    if avg_time < 2000:
        print(f"✅ PASS: Average {avg_time:.2f}ms < 2000ms")
        return True
    else:
        print(f"❌ FAIL: Average {avg_time:.2f}ms >= 2000ms")
        return False


def main():
    """Run all performance tests"""
    print(f"\n{'#'*80}")
    print(f"# ATLAS PERFORMANCE TEST SUITE")
    print(f"# Target: <2 seconds per query")
    print(f"{'#'*80}\n")

    print("Testing performance-optimized architecture:")
    print("  1. Interactions API V2 (no fallback overhead)")
    print("  2. File Search (managed RAG)")
    print("  3. Knowledge Graph (function calling)")
    print("  4. Single LLM call (no orchestration)")
    print("  5. Autonomous tool selection\n")

    results = []

    # Run tests
    try:
        results.append(("KG Query Performance", test_kg_query_performance()))
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        results.append(("KG Query Performance", False))

    try:
        results.append(("File Search Performance", test_file_search_query_performance()))
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        results.append(("File Search Performance", False))

    try:
        results.append(("Autonomous Tool Selection", test_autonomous_tool_selection()))
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        results.append(("Autonomous Tool Selection", False))

    try:
        results.append(("Stress Test", run_stress_test(5)))
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        results.append(("Stress Test", False))

    # Summary
    print(f"\n{'#'*80}")
    print(f"# TEST SUMMARY")
    print(f"{'#'*80}\n")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}  {test_name}")

    print(f"\n{'─'*80}")
    print(f"Total: {passed}/{total} tests passed")
    print(f"{'─'*80}\n")

    if passed == total:
        print("🎉 All tests passed! ATLAS performance target achieved (<2s)")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed. Performance optimization needed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
