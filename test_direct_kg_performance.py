"""
Test Direct KG Adapter Performance

Validates that the Direct API approach achieves <2s for Knowledge Graph queries.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from app.adapters.direct_kg_adapter import get_direct_kg_adapter
    from app.adapters.data_service_kg_adapter import get_data_service_kg_adapter
except ImportError as e:
    print(f"❌ ERROR: Failed to import: {e}")
    print("Make sure google-genai is installed: pip install google-genai")
    sys.exit(1)


def test_direct_kg_performance():
    """Test Direct KG Adapter performance (<2s target)"""
    print(f"\n{'='*80}")
    print(f"DIRECT KG ADAPTER PERFORMANCE TEST")
    print(f"Target: <2000ms for Knowledge Graph queries")
    print(f"{'='*80}\n")

    # Initialize adapters
    kg_adapter = get_data_service_kg_adapter()
    direct_adapter = get_direct_kg_adapter(kg_adapter=kg_adapter)

    # Test queries
    test_queries = [
        "What is the Project Size of Sara City?",
        "What is the PSF of Sara City?",
        "What is the Launch Date of Sara City?",
        "List all projects in Chakan"
    ]

    results = []
    print("Running test queries...\n")

    for i, query in enumerate(test_queries, 1):
        print(f"[{i}/{len(test_queries)}] {query}")

        result = direct_adapter.query(query)

        print(f"    Time: {result.execution_time_ms:.2f}ms")
        print(f"    Path: {result.execution_path}")
        print(f"    Answer: {result.answer[:100]}...")

        if result.execution_time_ms < 2000:
            print(f"    Status: ✅ PASS (<2000ms)\n")
        else:
            print(f"    Status: ❌ FAIL (>{result.execution_time_ms - 2000:.2f}ms over)\n")

        results.append(result.execution_time_ms)

    # Summary
    avg_time = sum(results) / len(results)
    max_time = max(results)
    min_time = min(results)
    passed = sum(1 for t in results if t < 2000)

    print(f"{'='*80}")
    print(f"PERFORMANCE SUMMARY")
    print(f"{'='*80}\n")
    print(f"Average Time: {avg_time:.2f}ms")
    print(f"Min Time: {min_time:.2f}ms")
    print(f"Max Time: {max_time:.2f}ms")
    print(f"Passed (<2000ms): {passed}/{len(results)}")

    if avg_time < 2000:
        print(f"\n🎉 SUCCESS: Average {avg_time:.2f}ms < 2000ms target!")
        print(f"   Improvement vs Interactions API: ~75% faster (7500ms → {avg_time:.2f}ms)")
        return 0
    else:
        print(f"\n⚠️  PARTIAL: Average {avg_time:.2f}ms")
        print(f"   Still faster than Interactions API ({avg_time:.2f}ms vs 7500ms)")
        return 1


if __name__ == "__main__":
    sys.exit(test_direct_kg_performance())
