"""
Test ATLAS Future State Architecture
File Search (Managed RAG) + Knowledge Graph Function Calling

This test demonstrates the hybrid architecture where:
1. Gemini File Search provides managed RAG over documents
2. Knowledge Graph functions provide structured data access
3. Gemini autonomously decides which tool to use

Test Cases:
- File Search only (definitions, concepts, general knowledge)
- KG only (specific project data, metrics, calculations)
- Hybrid (requires both RAG and structured data)
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.adapters.gemini_unified_adapter import get_gemini_unified_adapter
from app.adapters.data_service_kg_adapter import get_data_service_kg_adapter


def test_file_search_only():
    """
    Test File Search (managed RAG) for document-based queries

    Expected: Gemini uses File Search tool to answer from uploaded documents
    """
    print(f"\n{'#'*80}")
    print(f"# TEST 1: FILE SEARCH ONLY (Definitions & Concepts)")
    print(f"{'#'*80}\n")

    # Get adapters
    kg_adapter = get_data_service_kg_adapter()
    unified_adapter = get_gemini_unified_adapter(kg_adapter=kg_adapter)

    # Test queries that should use File Search
    test_queries = [
        "What is Absorption Rate?",
        "Define Price Per Square Foot (PSF)",
        "What are the different layers in the Liases Foras framework?",
        "Explain the concept of Months of Inventory"
    ]

    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print(f"{'─'*80}")

        result = unified_adapter.query(query)

        print(f"\n✅ Response:")
        print(f"{result.text_response}\n")
        print(f"🔍 Tool Usage:")
        print(f"   File Search: {result.file_search_used}")
        print(f"   KG Function: {result.kg_function_called}")

        # Assert File Search was used
        assert result.file_search_used, f"Expected File Search to be used for: {query}"
        print(f"\n{'─'*80}")


def test_kg_function_only():
    """
    Test Knowledge Graph function calling for structured data queries

    Expected: Gemini calls knowledge_graph_lookup function
    """
    print(f"\n{'#'*80}")
    print(f"# TEST 2: KNOWLEDGE GRAPH ONLY (Structured Data)")
    print(f"{'#'*80}\n")

    # Get adapters
    kg_adapter = get_data_service_kg_adapter()
    unified_adapter = get_gemini_unified_adapter(kg_adapter=kg_adapter)

    # Test queries that should use KG function
    test_queries = [
        "What is the Project Size of Sara City?",
        "How many units does VTP Pegasus have?",
        "What is the Saleable Area of Megapolis Smart Homes 1?",
        "Calculate PSF for Sara City"
    ]

    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        print(f"{'─'*80}")

        result = unified_adapter.query(query)

        print(f"\n✅ Response:")
        print(f"{result.text_response}\n")
        print(f"🔧 Tool Usage:")
        print(f"   File Search: {result.file_search_used}")
        print(f"   KG Function: {result.kg_function_called}")

        if result.kg_results:
            print(f"\n📊 KG Results:")
            print(f"   Success: {result.kg_results.get('success')}")
            print(f"   Data: {result.kg_results.get('data')}")

        # Assert KG function was called
        assert result.kg_function_called, f"Expected KG function call for: {query}"
        print(f"\n{'─'*80}")


def test_hybrid_rag_and_kg():
    """
    Test hybrid queries requiring both File Search and KG

    Expected: Gemini uses both tools in sequence
    """
    print(f"\n{'#'*80}")
    print(f"# TEST 3: HYBRID (File Search + KG)")
    print(f"{'#'*80}\n")

    # Get adapters
    kg_adapter = get_data_service_kg_adapter()
    unified_adapter = get_gemini_unified_adapter(kg_adapter=kg_adapter)

    # Test queries that require both RAG and structured data
    test_queries = [
        "What is the absorption rate of Sara City and how does it compare to the definition in the glossary?",
        "Calculate the PSF for VTP Pegasus and explain what PSF means",
        "Show me the project size of Megapolis and explain the Layer 0 dimensional model"
    ]

    for query in test_queries:
        print(f"\n🔄 Query: {query}")
        print(f"{'─'*80}")

        result = unified_adapter.query(query)

        print(f"\n✅ Response:")
        print(f"{result.text_response}\n")
        print(f"🔍🔧 Tool Usage:")
        print(f"   File Search: {result.file_search_used}")
        print(f"   KG Function: {result.kg_function_called}")

        if result.kg_results:
            print(f"\n📊 KG Results:")
            print(f"   {result.kg_results}")

        print(f"\n{'─'*80}")


def test_multi_turn_conversation():
    """
    Test multi-turn conversation with context retention

    Expected: Uses Interactions API for server-side state management
    """
    print(f"\n{'#'*80}")
    print(f"# TEST 4: MULTI-TURN CONVERSATION (State Management)")
    print(f"{'#'*80}\n")

    # Get adapters
    kg_adapter = get_data_service_kg_adapter()
    unified_adapter = get_gemini_unified_adapter(kg_adapter=kg_adapter)

    # Conversation flow
    conversation = [
        ("Tell me about Sara City project", None),
        ("What is its absorption rate?", "previous_interaction_id_here"),  # Refers to Sara City
        ("How does that compare to the market average?", "previous_interaction_id_here")
    ]

    print("⚠️  Note: Multi-turn with Interactions API requires additional implementation")
    print("This test demonstrates the intended workflow.\n")

    for turn, (query, prev_id) in enumerate(conversation, 1):
        print(f"\n💬 Turn {turn}: {query}")
        print(f"   Previous Interaction ID: {prev_id or 'None (first turn)'}")
        print(f"{'─'*80}")

        # In future implementation, pass previous_interaction_id
        result = unified_adapter.query(query)

        print(f"\n✅ Response:")
        print(f"{result.text_response}\n")

        # In future, extract and store interaction_id for next turn
        # interaction_id = result.metadata.get("interaction_id")

        print(f"{'─'*80}")


def test_performance_benchmarks():
    """
    Test performance: File Search vs KG vs Hybrid

    Expected latencies:
    - File Search: <500ms (vs 1-2s for ChromaDB)
    - KG: <200ms
    - Hybrid: <1s
    """
    print(f"\n{'#'*80}")
    print(f"# TEST 5: PERFORMANCE BENCHMARKS")
    print(f"{'#'*80}\n")

    import time

    # Get adapters
    kg_adapter = get_data_service_kg_adapter()
    unified_adapter = get_gemini_unified_adapter(kg_adapter=kg_adapter)

    # Benchmark queries
    benchmarks = [
        ("File Search", "What is Absorption Rate?"),
        ("KG", "What is the Project Size of Sara City?"),
        ("Hybrid", "Calculate PSF for Sara City and explain what it means")
    ]

    results = []

    for query_type, query in benchmarks:
        print(f"\n⏱️  Benchmarking: {query_type}")
        print(f"   Query: {query}")

        start_time = time.time()
        result = unified_adapter.query(query)
        latency_ms = (time.time() - start_time) * 1000

        results.append({
            "type": query_type,
            "latency_ms": latency_ms,
            "file_search": result.file_search_used,
            "kg": result.kg_function_called
        })

        print(f"   ✅ Latency: {latency_ms:.2f}ms")
        print(f"   Tools: File Search={result.file_search_used}, KG={result.kg_function_called}")

    # Summary
    print(f"\n{'─'*80}")
    print(f"BENCHMARK SUMMARY:")
    print(f"{'─'*80}")
    for r in results:
        print(f"{r['type']:12} {r['latency_ms']:8.2f}ms  (File Search: {r['file_search']}, KG: {r['kg']})")

    print(f"\n🎯 Target Latencies:")
    print(f"   File Search:  <500ms   (vs 1-2s for ChromaDB)")
    print(f"   KG:          <200ms")
    print(f"   Hybrid:       <1s")


def main():
    """Run all tests"""
    print(f"\n{'#'*80}")
    print(f"# ATLAS FUTURE STATE ARCHITECTURE TESTS")
    print(f"# File Search (Managed RAG) + Knowledge Graph Function Calling")
    print(f"{'#'*80}\n")

    print("Prerequisites:")
    print("1. ✅ GOOGLE_API_KEY or GEMINI_API_KEY set in .env")
    print("2. ✅ FILE_SEARCH_STORE_NAME set in .env (run scripts/upload_to_gemini_file_search.py)")
    print("3. ✅ 3 managed RAG files uploaded (LF-Layers, Pitch Doc, Glossary)")
    print("4. ✅ Knowledge Graph adapter configured (DataServiceKGAdapter)")

    try:
        # Run tests
        test_file_search_only()
        test_kg_function_only()
        test_hybrid_rag_and_kg()
        test_multi_turn_conversation()
        test_performance_benchmarks()

        print(f"\n{'#'*80}")
        print(f"# ALL TESTS COMPLETE ✅")
        print(f"{'#'*80}\n")

        print("Next Steps:")
        print("1. Integrate unified adapter into LangGraph orchestrator")
        print("2. Add Interactions API for multi-turn state management")
        print("3. Implement streaming response capability")
        print("4. Deploy to production")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
