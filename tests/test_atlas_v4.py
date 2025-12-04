"""
ATLAS v4 - End-to-End Tests

Tests for the LangGraph-based ATLAS v4 implementation.
"""

import pytest
import asyncio
from app.services.atlas_v4_langgraph_service import (
    execute_atlas_v4_query,
    execute_atlas_v4_query_sync,
    create_atlas_v4_graph
)
from app.models.atlas_v4_models import AtlasV4Response, validate_atlas_v4_response
from pydantic import ValidationError


# ============================================================================
# GRAPH CONSTRUCTION TESTS
# ============================================================================

def test_graph_construction():
    """Test that the LangGraph can be constructed without errors."""
    graph = create_atlas_v4_graph()
    assert graph is not None
    print("✓ Graph constructed successfully")


# ============================================================================
# QUERY EXECUTION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_simple_data_retrieval_query():
    """Test DATA_RETRIEVAL intent query."""
    response = await execute_atlas_v4_query(
        query="Show me all projects in Chakan",
        region="Chakan"
    )

    assert response["status"] == "success"
    assert response["intent"] in ["DATA_RETRIEVAL", "INSIGHT"]
    assert len(response["analysis"]) >= 100
    assert len(response["insights"]) >= 100
    assert "for_developers" in response["recommendations"]
    print("✓ Simple data retrieval query successful")


@pytest.mark.asyncio
async def test_calculation_intent_query():
    """Test CALCULATION intent query."""
    response = await execute_atlas_v4_query(
        query="Calculate average PSF in Chakan",
        region="Chakan"
    )

    assert response["status"] == "success"
    assert response["intent"] in ["CALCULATION", "DATA_RETRIEVAL"]
    assert len(response["analysis"]) >= 100
    assert "recommendations" in response
    print("✓ Calculation intent query successful")


@pytest.mark.asyncio
async def test_insight_intent_query():
    """Test INSIGHT intent query (most complex)."""
    response = await execute_atlas_v4_query(
        query="Why is absorption rate low in Chakan compared to Pune?",
        region="Chakan"
    )

    assert response["status"] == "success"
    assert response["intent"] == "INSIGHT"
    assert len(response["analysis"]) >= 100
    assert len(response["insights"]) >= 100
    assert len(response["recommendations"]["risks"]) >= 1
    print("✓ Insight intent query successful")


@pytest.mark.asyncio
async def test_strategic_intent_query():
    """Test STRATEGIC intent query."""
    response = await execute_atlas_v4_query(
        query="Should I invest in residential projects in Chakan?",
        region="Chakan"
    )

    assert response["status"] == "success"
    assert response["intent"] in ["STRATEGIC", "INSIGHT"]
    assert len(response["analysis"]) >= 100
    assert "timing" in response["recommendations"]
    print("✓ Strategic intent query successful")


# ============================================================================
# VALIDATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_response_validation():
    """Test that response passes Pydantic validation."""
    response = await execute_atlas_v4_query(
        query="What is the average PSF in Chakan?",
        region="Chakan"
    )

    # Should not raise ValidationError
    validated = validate_atlas_v4_response(response)
    assert isinstance(validated, AtlasV4Response)
    assert validated.status == "success"
    print("✓ Response validation successful")


def test_validation_fails_on_short_analysis():
    """Test that validation fails if analysis is too short."""
    invalid_response = {
        "status": "success",
        "query": "Test query",
        "intent": "INSIGHT",
        "intent_confidence": 0.9,
        "analysis": "Short",  # Too short
        "insights": "Also short",  # Too short
        "recommendations": {
            "for_developers": "Do something with real estate development strategy",
            "for_investors": "Consider investing in this market with careful analysis",
            "timing": "Act within next 6 months",
            "risks": ["Market volatility"]
        },
        "metadata": {
            "confidence": 0.8,
            "completeness": 0.7,
            "iterations": 2,
            "tool_calls": [],
            "plan": [],
            "plan_reasoning": None
        },
        "errors": [],
        "warnings": []
    }

    with pytest.raises(ValidationError):
        validate_atlas_v4_response(invalid_response)

    print("✓ Validation correctly rejects short analysis")


# ============================================================================
# METADATA TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_metadata_tracking():
    """Test that metadata is properly tracked."""
    response = await execute_atlas_v4_query(
        query="Show me projects in Chakan with absorption analysis",
        region="Chakan"
    )

    metadata = response["metadata"]

    # Check metadata structure
    assert "confidence" in metadata
    assert "completeness" in metadata
    assert "iterations" in metadata
    assert "tool_calls" in metadata
    assert "plan" in metadata

    # Check metadata values
    assert 0.0 <= metadata["confidence"] <= 1.0
    assert 0.0 <= metadata["completeness"] <= 1.0
    assert metadata["iterations"] >= 1
    assert len(metadata["tool_calls"]) >= 1
    assert len(metadata["plan"]) >= 1

    print(f"✓ Metadata tracking successful")
    print(f"  - Confidence: {metadata['confidence']:.2f}")
    print(f"  - Completeness: {metadata['completeness']:.2f}")
    print(f"  - Iterations: {metadata['iterations']}")
    print(f"  - Tool calls: {len(metadata['tool_calls'])}")
    print(f"  - Plan: {metadata['plan']}")


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_invalid_region_handling():
    """Test handling of invalid region."""
    response = await execute_atlas_v4_query(
        query="Show me projects",
        region="InvalidRegionXYZ123"
    )

    # Should still return success (with warnings)
    assert response["status"] == "success"
    # May have warnings about no data
    assert "warnings" in response

    print("✓ Invalid region handled gracefully")


@pytest.mark.asyncio
async def test_empty_query_handling():
    """Test handling of empty/minimal query."""
    response = await execute_atlas_v4_query(
        query="PSF",
        region="Chakan"
    )

    # Should still work (planning agent will interpret)
    assert response["status"] == "success"
    assert len(response["analysis"]) > 0

    print("✓ Minimal query handled successfully")


# ============================================================================
# SYNCHRONOUS WRAPPER TEST
# ============================================================================

def test_synchronous_wrapper():
    """Test that synchronous wrapper works."""
    response = execute_atlas_v4_query_sync(
        query="What is average PSF in Chakan?",
        region="Chakan"
    )

    assert response["status"] == "success"
    assert len(response["analysis"]) >= 100
    print("✓ Synchronous wrapper successful")


# ============================================================================
# AGENT EXECUTION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_all_agents_execute():
    """Test that all agents are executed for an INSIGHT query."""
    response = await execute_atlas_v4_query(
        query="Why is Chakan's pricing below Pune average and what should developers do?",
        region="Chakan"
    )

    tool_calls = response["metadata"]["tool_calls"]

    # For INSIGHT intent, expect multiple tools
    tool_names = [tc.get("tool") for tc in tool_calls]

    # Should have at least data retrieval and synthesis
    assert len(tool_names) >= 2

    print(f"✓ All agents executed for INSIGHT query")
    print(f"  - Tools used: {tool_names}")


# ============================================================================
# PLAN EXECUTION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_plan_follows_intent():
    """Test that plan is generated based on intent."""
    response = await execute_atlas_v4_query(
        query="Why is absorption rate low in Chakan?",
        region="Chakan"
    )

    plan = response["metadata"]["plan"]
    intent = response["intent"]

    # INSIGHT intent should have comprehensive plan
    if intent == "INSIGHT":
        assert len(plan) >= 2  # At least data + insights
        assert any("layer0" in tool.lower() or "data" in tool.lower() for tool in plan)

    print(f"✓ Plan generated correctly for {intent} intent")
    print(f"  - Plan: {plan}")


# ============================================================================
# RUNNER
# ============================================================================

if __name__ == "__main__":
    """Run tests manually."""
    print("\n" + "="*80)
    print("ATLAS v4 - End-to-End Tests")
    print("="*80 + "\n")

    # Test 1: Graph Construction
    print("TEST 1: Graph Construction")
    test_graph_construction()
    print()

    # Test 2: Simple Query
    print("TEST 2: Simple Data Retrieval Query")
    asyncio.run(test_simple_data_retrieval_query())
    print()

    # Test 3: Calculation Query
    print("TEST 3: Calculation Intent Query")
    asyncio.run(test_calculation_intent_query())
    print()

    # Test 4: Insight Query
    print("TEST 4: Insight Intent Query (Complex)")
    asyncio.run(test_insight_intent_query())
    print()

    # Test 5: Strategic Query
    print("TEST 5: Strategic Intent Query")
    asyncio.run(test_strategic_intent_query())
    print()

    # Test 6: Validation
    print("TEST 6: Response Validation")
    asyncio.run(test_response_validation())
    print()

    # Test 7: Validation Failure
    print("TEST 7: Validation Failure on Short Content")
    test_validation_fails_on_short_analysis()
    print()

    # Test 8: Metadata
    print("TEST 8: Metadata Tracking")
    asyncio.run(test_metadata_tracking())
    print()

    # Test 9: Error Handling
    print("TEST 9: Invalid Region Handling")
    asyncio.run(test_invalid_region_handling())
    print()

    # Test 10: Empty Query
    print("TEST 10: Empty Query Handling")
    asyncio.run(test_empty_query_handling())
    print()

    # Test 11: Sync Wrapper
    print("TEST 11: Synchronous Wrapper")
    test_synchronous_wrapper()
    print()

    # Test 12: Agent Execution
    print("TEST 12: All Agents Execute")
    asyncio.run(test_all_agents_execute())
    print()

    # Test 13: Plan Follows Intent
    print("TEST 13: Plan Follows Intent")
    asyncio.run(test_plan_follows_intent())
    print()

    print("="*80)
    print("All tests passed! ✓")
    print("="*80)
