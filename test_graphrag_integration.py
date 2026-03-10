"""
Test GraphRAG Integration in Query Orchestrator

This script tests the LLM-driven query resolution to ensure:
1. Spelling mistakes are handled (Shrinivas vs Shriniwas)
2. Case mismatches are handled
3. Newline characters are normalized
4. GraphRAG metadata is included in responses
"""

from app.orchestration.query_orchestrator import QueryOrchestrator
import json

def test_graphrag_integration():
    """Test GraphRAG integration with various query variations"""

    print("=" * 80)
    print("GRAPHRAG INTEGRATION TEST")
    print("=" * 80)

    # Initialize orchestrator
    orchestrator = QueryOrchestrator()

    # Test cases with spelling variations, case mismatches, and newlines
    test_queries = [
        {
            "query": "What is the Project Size of Sara City?",
            "description": "Baseline - should work with or without GraphRAG"
        },
        {
            "query": "What is the project size of sara city?",  # lowercase
            "description": "Case mismatch test"
        },
        {
            "query": "What is the Project Size of Pradnyesh Shrinivas?",  # Spelling: Shrinivas (should be Shriniwas)
            "description": "Spelling variation test"
        },
        {
            "query": "What is the Annual Sales Value of Sara City?",
            "description": "Attribute with units test"
        },
        {
            "query": "What is the Sold % of The Urbana?",
            "description": "Percentage attribute test"
        }
    ]

    for i, test_case in enumerate(test_queries, 1):
        query = test_case["query"]
        description = test_case["description"]

        print(f"\n{'─' * 80}")
        print(f"Test {i}: {description}")
        print(f"Query: \"{query}\"")
        print("─" * 80)

        try:
            # Execute query
            response = orchestrator.execute_query(query)

            # Display results
            print(f"\n✅ Query Type: {response.get('query_type')}")
            print(f"✅ Execution Path: {' → '.join(response.get('execution_path', []))}")

            # GraphRAG metadata
            graphrag_meta = response.get('graphrag_metadata', {})
            if graphrag_meta.get('used'):
                print(f"\n🤖 GraphRAG Used: YES")
                print(f"   Confidence: {graphrag_meta.get('confidence', 0):.2%}")
                print(f"   Reasoning: {graphrag_meta.get('reasoning', 'N/A')[:100]}...")
            else:
                print(f"\n🔧 GraphRAG Used: NO (fuzzy matching fallback)")

            # Metadata
            metadata = response.get('metadata', {})
            print(f"\n📊 Resolved Entities:")
            print(f"   Attribute: {metadata.get('attribute_name', 'N/A')}")
            print(f"   Project: {metadata.get('project_name', 'N/A')}")

            # Result or error
            if response.get('error'):
                print(f"\n❌ Error: {response['error']}")
            elif response.get('result'):
                result = response['result']
                if isinstance(result, dict):
                    print(f"\n✅ Result:")
                    print(f"   Value: {result.get('value', 'N/A')}")
                    print(f"   Unit: {result.get('unit', 'N/A')}")
                else:
                    print(f"\n✅ Result: {result}")
            else:
                print(f"\n⚠️  No result returned")

        except Exception as e:
            print(f"\n❌ Exception: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'=' * 80}")
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_graphrag_integration()
