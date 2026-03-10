"""
ATLAS Hybrid Router - Comprehensive Performance Test

Tests the hybrid router achieves <2s average performance with all 3 components:
1. Interactions API
2. File Search (managed RAG)
3. Knowledge Graph (function calling)

Target: <2000ms average with intelligent routing
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from app.adapters.atlas_hybrid_router import get_hybrid_router
    from app.adapters.data_service_kg_adapter import get_data_service_kg_adapter
except ImportError as e:
    print(f"❌ ERROR: Failed to import: {e}")
    sys.exit(1)


def test_hybrid_router_performance():
    """
    Test Hybrid Router performance with mixed queries

    Expected Results:
    - Quantitative queries: <2000ms (Direct API path)
    - Qualitative queries: <3500ms (Interactions API path)
    - Average: <2000ms
    """
    print(f"\n{'#'*80}")
    print(f"# ATLAS HYBRID ROUTER PERFORMANCE TEST")
    print(f"# Target: <2000ms average (mixed queries)")
    print(f"{'#'*80}\n")

    print("Architecture:")
    print("  1. Interactions API V2 (for File Search)")
    print("  2. Direct API (for Knowledge Graph)")
    print("  3. File Search (managed RAG - 3 files)")
    print("  4. Knowledge Graph (function calling)")
    print("  5. Intelligent query routing\n")

    # Initialize
    kg_adapter = get_data_service_kg_adapter()
    router = get_hybrid_router(kg_adapter=kg_adapter)

    # Test queries (mixed quantitative and qualitative)
    test_cases = [
        # Quantitative queries (should use Direct API - fast)
        ("What is the Project Size of Sara City?", "quantitative", 2000),
        ("What is the PSF of Sara City?", "quantitative", 2000),
        ("What is the Launch Date of Sara City?", "quantitative", 2000),
        ("How many units does Sara City have?", "quantitative", 2000),
        ("List all projects in Chakan", "quantitative", 2000),
        ("Show me the location of Sara City", "quantitative", 2000),
        ("Get me the developer of Sara City", "quantitative", 2000),

        # Qualitative queries (should use Interactions API - slower but acceptable)
        ("What is Absorption Rate? Define it.", "qualitative", 3500),
        ("Explain PSF formula", "qualitative", 3500),
        ("What does Sales Velocity mean?", "qualitative", 3500),
    ]

    print(f"{'='*80}")
    print(f"RUNNING {len(test_cases)} TEST QUERIES")
    print(f"{'='*80}\n")

    results = []
    quantitative_times = []
    qualitative_times = []

    for i, (query, expected_intent, time_limit) in enumerate(test_cases, 1):
        print(f"[{i}/{len(test_cases)}] {query}")
        print(f"    Expected Intent: {expected_intent}")

        try:
            result = router.query(query)

            print(f"    Actual Intent: {result.query_intent}")
            print(f"    Execution Path: {result.execution_path}")
            print(f"    Tool Used: {result.tool_used}")
            print(f"    Classification Time: {result.classification_time_ms:.2f}ms")
            print(f"    Query Time: {result.query_time_ms:.2f}ms")
            print(f"    Total Time: {result.execution_time_ms:.2f}ms")

            # Check if intent classification is correct
            intent_correct = result.query_intent == expected_intent
            if intent_correct:
                print(f"    Intent Classification: ✅ CORRECT")
            else:
                print(f"    Intent Classification: ⚠️  MISMATCH (expected {expected_intent}, got {result.query_intent})")

            # Check if time is within limit
            if result.execution_time_ms < time_limit:
                print(f"    Performance: ✅ PASS (<{time_limit}ms)\n")
                status = "PASS"
            else:
                print(f"    Performance: ⚠️  Over limit by {result.execution_time_ms - time_limit:.2f}ms\n")
                status = "PARTIAL"

            results.append({
                "query": query,
                "expected_intent": expected_intent,
                "actual_intent": result.query_intent,
                "time_ms": result.execution_time_ms,
                "time_limit": time_limit,
                "status": status
            })

            # Track times by intent
            if result.query_intent == "quantitative":
                quantitative_times.append(result.execution_time_ms)
            else:
                qualitative_times.append(result.execution_time_ms)

        except Exception as e:
            print(f"    ❌ ERROR: {e}\n")
            results.append({
                "query": query,
                "expected_intent": expected_intent,
                "actual_intent": "error",
                "time_ms": 0,
                "time_limit": time_limit,
                "status": "FAIL"
            })

    # Calculate statistics
    print(f"\n{'='*80}")
    print(f"PERFORMANCE SUMMARY")
    print(f"{'='*80}\n")

    total_queries = len(results)
    passed_queries = sum(1 for r in results if r["status"] == "PASS")

    all_times = [r["time_ms"] for r in results if r["time_ms"] > 0]
    if all_times:
        avg_time = sum(all_times) / len(all_times)
        min_time = min(all_times)
        max_time = max(all_times)

        print(f"Overall Performance:")
        print(f"  • Total Queries: {total_queries}")
        print(f"  • Passed: {passed_queries}/{total_queries}")
        print(f"  • Average Time: {avg_time:.2f}ms")
        print(f"  • Min Time: {min_time:.2f}ms")
        print(f"  • Max Time: {max_time:.2f}ms")

        if quantitative_times:
            avg_quant = sum(quantitative_times) / len(quantitative_times)
            print(f"\nQuantitative Queries (Direct API):")
            print(f"  • Count: {len(quantitative_times)}")
            print(f"  • Average: {avg_quant:.2f}ms")
            print(f"  • Target: <2000ms")
            if avg_quant < 2000:
                print(f"  • Status: ✅ MEETS TARGET")
            else:
                print(f"  • Status: ❌ Over by {avg_quant - 2000:.2f}ms")

        if qualitative_times:
            avg_qual = sum(qualitative_times) / len(qualitative_times)
            print(f"\nQualitative Queries (Interactions API):")
            print(f"  • Count: {len(qualitative_times)}")
            print(f"  • Average: {avg_qual:.2f}ms")
            print(f"  • Target: <3500ms")
            if avg_qual < 3500:
                print(f"  • Status: ✅ ACCEPTABLE")
            else:
                print(f"  • Status: ⚠️  Over by {avg_qual - 3500:.2f}ms")

        print(f"\n{'='*80}")
        print(f"TARGET ACHIEVEMENT")
        print(f"{'='*80}")

        if avg_time < 2000:
            print(f"🎉 SUCCESS: Average {avg_time:.2f}ms < 2000ms target!")
            print(f"   Hybrid Router Architecture Validated ✅")
            router.print_stats()
            return 0
        else:
            print(f"⚠️  PARTIAL: Average {avg_time:.2f}ms")
            print(f"   Still significant improvement over pure Interactions API (7900ms)")
            router.print_stats()
            return 1
    else:
        print("❌ No successful queries")
        return 1


if __name__ == "__main__":
    sys.exit(test_hybrid_router_performance())
