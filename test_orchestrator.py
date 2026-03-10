"""
Test script for QueryOrchestrator

Tests the LangGraph state machine with sample queries
"""

from app.orchestration import QueryOrchestrator
import json


def test_orchestrator():
    """Test the query orchestrator with different query types"""

    orchestrator = QueryOrchestrator()

    # Test queries
    test_queries = [
        # Calculation query
        "What is the PSF Gap of Sara City?",

        # Statistical query
        "What is the average Launch PSF across all projects in Pune?",

        # Project search query
        "Show all projects in Chakan",
    ]

    print("=" * 80)
    print("Testing Query Orchestrator with LangGraph")
    print("=" * 80)

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 80}")
        print(f"Test {i}: {query}")
        print(f"{'=' * 80}")

        try:
            result = orchestrator.execute_query(query)

            print(f"\nQuery Type: {result['query_type']}")
            print(f"Execution Path: {' → '.join(result['execution_path'])}")

            if result['error']:
                print(f"\n❌ Error: {result['error']}")
            else:
                print(f"\n✅ Result:")
                print(json.dumps(result['result'], indent=2))

            print(f"\nMetadata:")
            print(json.dumps(result['metadata'], indent=2))

        except Exception as e:
            print(f"\n❌ Exception: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'=' * 80}")
    print("Testing Complete")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    test_orchestrator()
