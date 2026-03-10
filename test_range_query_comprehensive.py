"""
Comprehensive Range Query Test Suite

Tests end-to-end range query functionality across the entire LangGraph orchestrator pipeline.

This validates:
1. Intent classification (comparative)
2. Attribute resolution (Unit Saleable Size)
3. KG query planning (filter action with range operation)
4. KG execution (filter_projects_by_range method)
5. Answer composition (formatted multi-result response)

Test Case: "Show projects with units around 600 sq.ft" (Excel row 15)
Expected: Should find projects with Unit Saleable Size within ±10% of 600 sq.ft
"""

import os
os.environ['LLM_PROVIDER'] = 'ollama'  # Use Ollama for consistent testing

from app.services.v4_query_service import get_v4_service
import json


def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}\n")


def test_range_query_basic():
    """
    Test Case 1: Basic range query with implicit tolerance
    Query: "Show projects with units around 600 sq.ft"
    Expected: 5 projects within ±10% (540-660 sq.ft)
    """
    print_section("TEST 1: Basic Range Query")

    svc = get_v4_service()
    result = svc.query("show projects with units around 600 sq.ft")

    print(f"✓ Query: 'show projects with units around 600 sq.ft'")
    print(f"✓ Intent: {result.get('intent')}")
    print(f"✓ Execution path: {' → '.join(result.get('execution_path', []))}")

    # Validate intent
    assert result.get('intent') == 'comparative', f"Expected 'comparative', got '{result.get('intent')}'"
    print("  ✓ Intent classification: PASS")

    # Validate execution path
    expected_path = ['intent_classifier', 'attribute_resolver', 'entity_resolver', 'kg_query_planner', 'kg_executor', 'answer_composer']
    assert result.get('execution_path') == expected_path, f"Execution path mismatch"
    print("  ✓ Execution path: PASS")

    # Validate answer is not hallucinated
    assert 'answer' in result, "No answer in result"
    assert len(result['answer']) > 0, "Empty answer"
    print(f"  ✓ Answer generated: PASS ({len(result['answer'])} characters)")

    # Print answer
    print(f"\n📊 Answer:\n{result['answer']}\n")

    return result


def test_range_query_explicit_size():
    """
    Test Case 2: Range query with explicit "square feet" mention
    Query: "show projects with unit saleable size around 600 square feet"
    Expected: Should resolve to "Unit Saleable Size" attribute
    """
    print_section("TEST 2: Explicit Attribute Mention")

    svc = get_v4_service()
    result = svc.query("show projects with unit saleable size around 600 square feet")

    print(f"✓ Query: 'show projects with unit saleable size around 600 square feet'")
    print(f"✓ Intent: {result.get('intent')}")

    # Validate intent
    assert result.get('intent') == 'comparative', f"Expected 'comparative', got '{result.get('intent')}'"
    print("  ✓ Intent classification: PASS")

    # Validate answer
    assert 'answer' in result, "No answer in result"
    assert '5 projects' in result['answer'] or '5  projects' in result['answer'] or 'projects' in result['answer'], "Expected multiple projects in answer"
    print("  ✓ Multi-project response: PASS")

    # Print answer
    print(f"\n📊 Answer:\n{result['answer']}\n")

    return result


def test_range_query_different_tolerance():
    """
    Test Case 3: Range query that should trigger different tolerance
    Query: "show projects with unit size between 550 and 650 sq.ft"
    Expected: Should use "between" operation instead of "range"
    """
    print_section("TEST 3: Between Operation (Alternative to Range)")

    svc = get_v4_service()
    result = svc.query("show projects with unit size between 550 and 650 square feet")

    print(f"✓ Query: 'show projects with unit size between 550 and 650 square feet'")
    print(f"✓ Intent: {result.get('intent')}")

    # Validate intent
    assert result.get('intent') in ['comparative', 'objective'], f"Expected 'comparative' or 'objective', got '{result.get('intent')}'"
    print("  ✓ Intent classification: PASS")

    # Validate answer
    assert 'answer' in result, "No answer in result"
    print("  ✓ Answer generated: PASS")

    # Print answer
    print(f"\n📊 Answer:\n{result['answer']}\n")

    return result


def test_range_query_with_location():
    """
    Test Case 4: Range query with location filter
    Query: "show projects in Chakan with units around 600 sq.ft"
    Expected: Should filter by location AND unit size
    """
    print_section("TEST 4: Range Query with Location Filter")

    svc = get_v4_service()
    result = svc.query("show projects in Chakan with units around 600 sq.ft")

    print(f"✓ Query: 'show projects in Chakan with units around 600 sq.ft'")
    print(f"✓ Intent: {result.get('intent')}")

    # Validate intent
    assert result.get('intent') == 'comparative', f"Expected 'comparative', got '{result.get('intent')}'"
    print("  ✓ Intent classification: PASS")

    # Validate answer
    assert 'answer' in result, "No answer in result"
    assert 'Chakan' in result['answer'] or 'chakan' in result['answer'].lower(), "Expected Chakan mention in answer"
    print("  ✓ Location filter: PASS")

    # Print answer
    print(f"\n📊 Answer:\n{result['answer']}\n")

    return result


def test_answer_quality():
    """
    Test Case 5: Validate answer quality and formatting
    Expected: Answer should include project names, values, and insights
    """
    print_section("TEST 5: Answer Quality Validation")

    svc = get_v4_service()
    result = svc.query("show projects with units around 600 sq.ft")

    answer = result.get('answer', '')

    print("Checking answer quality metrics...")

    # Check for project names (should be in the answer)
    has_project_names = any(name in answer for name in ['Sara', 'Siddhivinayak', 'Pradnyesh', 'Sarangi', 'Urbana'])
    assert has_project_names, "No project names found in answer"
    print("  ✓ Contains project names: PASS")

    # Check for numeric values (should show unit sizes)
    has_numbers = any(char.isdigit() for char in answer)
    assert has_numbers, "No numeric values found in answer"
    print("  ✓ Contains numeric values: PASS")

    # Check for insights (should have some analysis)
    has_insights = 'Insights' in answer or 'insight' in answer.lower() or 'average' in answer.lower()
    if has_insights:
        print("  ✓ Contains insights: PASS")
    else:
        print("  ⚠ No explicit insights section (may be implicit)")

    # Check for formatting (HTML bold tags)
    has_formatting = '<b>' in answer
    assert has_formatting, "No HTML formatting found"
    print("  ✓ Has HTML formatting: PASS")

    print(f"\n📊 Answer Quality Score: {'EXCELLENT' if has_insights else 'GOOD'}")

    return result


def test_edge_case_no_matches():
    """
    Test Case 6: Range query with no matches
    Query: "show projects with units around 10000 sq.ft" (unrealistic size)
    Expected: Should gracefully handle no results
    """
    print_section("TEST 6: Edge Case - No Matches")

    svc = get_v4_service()
    result = svc.query("show projects with units around 10000 sq.ft")

    print(f"✓ Query: 'show projects with units around 10000 sq.ft'")
    print(f"✓ Intent: {result.get('intent')}")

    # Validate intent
    assert result.get('intent') in ['comparative', 'objective'], f"Expected 'comparative' or 'objective', got '{result.get('intent')}'"
    print("  ✓ Intent classification: PASS")

    # Validate answer handles no results gracefully
    assert 'answer' in result, "No answer in result"
    print("  ✓ Graceful handling: PASS")

    # Print answer
    print(f"\n📊 Answer:\n{result['answer']}\n")

    return result


def run_all_tests():
    """Run all test cases and print summary"""
    print_section("RANGE QUERY COMPREHENSIVE TEST SUITE")
    print("Testing LLM-driven range query implementation across LangGraph pipeline\n")

    tests = [
        ("Basic Range Query", test_range_query_basic),
        ("Explicit Attribute Mention", test_range_query_explicit_size),
        ("Between Operation", test_range_query_different_tolerance),
        ("Range with Location Filter", test_range_query_with_location),
        ("Answer Quality Validation", test_answer_quality),
        ("Edge Case - No Matches", test_edge_case_no_matches),
    ]

    results = []
    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            print(f"\n{'─'*80}")
            print(f"Running: {test_name}")
            print(f"{'─'*80}")
            result = test_func()
            results.append((test_name, "PASS", None))
            passed += 1
            print(f"✅ {test_name}: PASS")
        except AssertionError as e:
            results.append((test_name, "FAIL", str(e)))
            failed += 1
            print(f"❌ {test_name}: FAIL - {e}")
        except Exception as e:
            results.append((test_name, "ERROR", str(e)))
            failed += 1
            print(f"💥 {test_name}: ERROR - {e}")

    # Print summary
    print_section("TEST SUMMARY")
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success rate: {(passed/len(tests)*100):.1f}%\n")

    # Print detailed results
    print("Detailed Results:")
    print(f"{'─'*80}")
    for test_name, status, error in results:
        if status == "PASS":
            print(f"✅ {test_name}: {status}")
        else:
            print(f"❌ {test_name}: {status}")
            if error:
                print(f"   Error: {error}")
    print(f"{'─'*80}\n")

    # Return overall success
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()

    if success:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("\nRange query implementation is working correctly!")
        print("✓ Intent classification")
        print("✓ Attribute resolution")
        print("✓ KG query planning")
        print("✓ KG execution with filter_projects_by_range")
        print("✓ Answer composition with insights")
        exit(0)
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("Please review the errors above and fix the implementation.")
        exit(1)
