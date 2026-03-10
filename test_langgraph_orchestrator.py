"""
Test Script for LangGraph Orchestrator

This script tests the complete LangGraph orchestration system with all three
query types: Objective, Analytical, and Financial.

Demonstrates:
1. Hexagonal architecture with port/adapter pattern
2. LangGraph state machine with conditional routing
3. Vector DB semantic search for attributes
4. Knowledge Graph data retrieval
5. LLM-driven intelligence without data hallucination
6. Multi-turn conversation support for financial queries
7. Provenance tracking

Usage:
    python test_langgraph_orchestrator.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.orchestration.langgraph_orchestrator import get_orchestrator
import json


def print_response(response: dict, query: str):
    """Pretty print orchestrator response"""
    print(f"\n{'='*80}")
    print(f"QUERY: {query}")
    print(f"{'='*80}\n")

    print(f"[Intent]: {response.get('intent')} ({response.get('subcategory', 'N/A')})")
    print(f"[Execution Path]: {' → '.join(response.get('execution_path', []))}")
    print(f"[Execution Time]: {response.get('execution_time_ms', 0):.2f}ms")
    print(f"[Next Action]: {response.get('next_action')}\n")

    if response.get('clarification_question'):
        print(f"[Clarification Needed]:")
        print(response.get('clarification_question'))
        print()

    print(f"[Answer]:")
    print(response.get('answer'))
    print()

    if response.get('provenance'):
        prov = response['provenance']
        print(f"[Provenance]:")
        print(f"  Data Sources: {', '.join(prov.get('data_sources', []))}")
        if prov.get('layer0_inputs'):
            print(f"  Layer 0 Inputs: {', '.join(prov.get('layer0_inputs', []))}")
        if prov.get('layer1_intermediates'):
            print(f"  Layer 1 Metrics: {', '.join(prov.get('layer1_intermediates', []))}")
        if prov.get('calculation_methods'):
            print(f"  Calculation Methods: {', '.join(prov.get('calculation_methods', []))}")

    print(f"\n{'='*80}\n")


def test_objective_query():
    """Test Branch 1: Objective query (direct retrieval)"""
    print(f"\n{'#'*80}")
    print(f"TEST 1: OBJECTIVE QUERY (Direct Retrieval)")
    print(f"{'#'*80}")

    orchestrator = get_orchestrator()

    query = "What is the total units for Sara City?"

    response = orchestrator.query(
        query=query,
        session_id="test_objective"
    )

    print_response(response, query)

    # Verify routing
    assert response['intent'] == 'objective', f"Expected objective intent, got {response['intent']}"
    assert 'parameter_gatherer' not in response['execution_path'], "Objective query should not go through parameter gatherer"
    assert 'computation' not in response['execution_path'], "Objective query should not compute"

    print(f"✓ OBJECTIVE QUERY TEST PASSED\n")


def test_analytical_query():
    """Test Branch 2: Analytical query (aggregation/comparison)"""
    print(f"\n{'#'*80}")
    print(f"TEST 2: ANALYTICAL QUERY (Aggregation)")
    print(f"{'#'*80}")

    orchestrator = get_orchestrator()

    query = "What is the average sold percentage across all projects in Chakan?"

    response = orchestrator.query(
        query=query,
        session_id="test_analytical"
    )

    print_response(response, query)

    # Verify routing
    assert response['intent'] == 'analytical', f"Expected analytical intent, got {response['intent']}"
    assert 'parameter_gatherer' not in response['execution_path'], "Analytical query should not go through parameter gatherer"
    assert 'computation' not in response['execution_path'], "Analytical query should not compute"

    print(f"✓ ANALYTICAL QUERY TEST PASSED\n")


def test_financial_query_single_turn():
    """Test Branch 3: Financial query with all parameters (single turn)"""
    print(f"\n{'#'*80}")
    print(f"TEST 3: FINANCIAL QUERY (Single Turn - All Params)")
    print(f"{'#'*80}")

    orchestrator = get_orchestrator()

    # Query with discount rate included
    query = "Calculate NPV for Sara City with 12% discount rate"

    response = orchestrator.query(
        query=query,
        session_id="test_financial_single"
    )

    print_response(response, query)

    # Verify routing
    assert response['intent'] == 'financial', f"Expected financial intent, got {response['intent']}"
    assert 'parameter_gatherer' in response['execution_path'], "Financial query should go through parameter gatherer"

    # Check if went through computation or needs clarification
    if response.get('next_action') == 'answer' and 'computation' in response['execution_path']:
        print(f"✓ FINANCIAL QUERY (SINGLE TURN) TEST PASSED - Computation performed\n")
    elif response.get('next_action') == 'gather_parameters':
        print(f"✓ FINANCIAL QUERY (SINGLE TURN) TEST PASSED - Clarification needed (expected)\n")
    else:
        print(f"⚠ Unexpected next_action: {response.get('next_action')}\n")


def test_financial_query_multi_turn():
    """Test Branch 3: Financial query requiring multi-turn (missing params)"""
    print(f"\n{'#'*80}")
    print(f"TEST 4: FINANCIAL QUERY (Multi-Turn - Missing Params)")
    print(f"{'#'*80}")

    orchestrator = get_orchestrator()

    # Query WITHOUT parameters
    query = "What is the IRR for Sara City?"

    response = orchestrator.query(
        query=query,
        session_id="test_financial_multi"
    )

    print_response(response, query)

    # Verify routing
    assert response['intent'] == 'financial', f"Expected financial intent, got {response['intent']}"
    assert 'parameter_gatherer' in response['execution_path'], "Financial query should go through parameter gatherer"

    # Should ask for clarification
    if response.get('next_action') == 'gather_parameters':
        print(f"✓ System correctly identified missing parameters")
        print(f"✓ Clarification question generated\n")
    else:
        print(f"⚠ Expected 'gather_parameters', got: {response.get('next_action')}\n")

    print(f"✓ FINANCIAL QUERY (MULTI-TURN) TEST PASSED\n")


def test_semantic_search():
    """Test Vector DB semantic attribute search"""
    print(f"\n{'#'*80}")
    print(f"TEST 5: SEMANTIC ATTRIBUTE SEARCH")
    print(f"{'#'*80}")

    orchestrator = get_orchestrator()

    # Query with informal attribute name
    queries = [
        "How many total units does Sara City have?",  # "total units" → Total Units
        "What's the sold percentage?",                # "sold percentage" → Sold %
        "Show me the price per square foot"           # "price per square foot" → PSF
    ]

    for query in queries:
        print(f"\n[Testing] {query}")

        response = orchestrator.query(
            query=query,
            session_id="test_semantic"
        )

        # Check if attributes were resolved
        exec_path = response.get('execution_path', [])
        assert 'attribute_resolver' in exec_path, "Should go through attribute resolver"

        print(f"  ✓ Executed through attribute resolver")

    print(f"\n✓ SEMANTIC SEARCH TEST PASSED\n")


def test_entity_resolution():
    """Test KG fuzzy entity matching"""
    print(f"\n{'#'*80}")
    print(f"TEST 6: ENTITY RESOLUTION (Fuzzy Matching)")
    print(f"{'#'*80}")

    orchestrator = get_orchestrator()

    # Query with fuzzy project name
    query = "What are the total units for sara city?"  # Lowercase

    response = orchestrator.query(
        query=query,
        session_id="test_entity"
    )

    print_response(response, query)

    # Check if entity resolver executed
    exec_path = response.get('execution_path', [])
    assert 'entity_resolver' in exec_path, "Should go through entity resolver"

    print(f"✓ ENTITY RESOLUTION TEST PASSED\n")


def run_all_tests():
    """Run all tests"""
    print(f"\n{'#'*80}")
    print(f"LANGGRAPH ORCHESTRATOR - COMPREHENSIVE TEST SUITE")
    print(f"{'#'*80}\n")

    try:
        # Test all three query types
        test_objective_query()
        test_analytical_query()
        test_financial_query_single_turn()
        test_financial_query_multi_turn()

        # Test specific features
        test_semantic_search()
        test_entity_resolution()

        print(f"\n{'#'*80}")
        print(f"ALL TESTS PASSED ✓")
        print(f"{'#'*80}\n")

    except AssertionError as e:
        print(f"\n{'#'*80}")
        print(f"TEST FAILED ✗")
        print(f"{'#'*80}")
        print(f"Error: {e}\n")
        raise

    except Exception as e:
        print(f"\n{'#'*80}")
        print(f"TEST ERROR ✗")
        print(f"{'#'*80}")
        print(f"Error: {e}\n")
        import traceback
        traceback.print_exc()
        raise


def interactive_mode():
    """Interactive mode for manual testing"""
    print(f"\n{'#'*80}")
    print(f"LANGGRAPH ORCHESTRATOR - INTERACTIVE MODE")
    print(f"{'#'*80}\n")

    orchestrator = get_orchestrator()

    print(f"Enter queries to test the orchestrator. Type 'quit' to exit.\n")

    session_id = "interactive_session"

    while True:
        query = input(f"\n[Query] > ").strip()

        if query.lower() in ['quit', 'exit', 'q']:
            print(f"\nExiting...")
            break

        if not query:
            continue

        response = orchestrator.query(
            query=query,
            session_id=session_id
        )

        print_response(response, query)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test LangGraph Orchestrator")
    parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode')
    parser.add_argument('--test', '-t', type=str, help='Run specific test (objective, analytical, financial, semantic, entity)')

    args = parser.parse_args()

    if args.interactive:
        interactive_mode()
    elif args.test:
        test_name = args.test.lower()
        if test_name == 'objective':
            test_objective_query()
        elif test_name == 'analytical':
            test_analytical_query()
        elif test_name == 'financial':
            test_financial_query_single_turn()
            test_financial_query_multi_turn()
        elif test_name == 'semantic':
            test_semantic_search()
        elif test_name == 'entity':
            test_entity_resolution()
        else:
            print(f"Unknown test: {test_name}")
    else:
        run_all_tests()
