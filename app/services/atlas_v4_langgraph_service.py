"""
ATLAS v4 - LangGraph Service

Main orchestration service connecting all 6 agents with conditional routing.
"""

from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from pydantic import ValidationError

from app.services.graph_state import GraphState
from app.services.agents import (
    intent_agent_node,
    planning_agent_node,
    data_agent_node,
    calculator_agent_node,
    insight_agent_node,
    synthesizer_agent_node
)
from app.models.atlas_v4_models import (
    AtlasV4Response,
    ResponseMetadata,
    Recommendations,
    validate_atlas_v4_response,
    create_error_response
)


# ============================================================================
# ROUTING FUNCTIONS
# ============================================================================

def route_after_intent(state: GraphState) -> str:
    """
    Route after intent classification.

    Always go to planning agent to create dynamic tool sequence.
    """
    return "planning_agent"


def route_after_planning(state: GraphState) -> str:
    """
    Route after planning to first tool in plan.

    Args:
        state: Current graph state

    Returns:
        Next node name based on first tool in plan
    """
    plan = state.get("plan", [])

    if not plan:
        # No plan, skip to synthesis
        return "synthesizer_agent"

    # Map tool names to agent nodes
    tool_to_agent = {
        "get_layer0_data": "data_agent",
        "calculate_layer1_metrics": "calculator_agent",
        "search_vector_insights": "insight_agent",
        "get_location_context": "insight_agent",  # Can be handled by insight agent
        "optimize_product_mix": "calculator_agent"  # Layer 3 optimization
    }

    first_tool = plan[0]
    return tool_to_agent.get(first_tool, "synthesizer_agent")


def route_after_data_agent(state: GraphState) -> str:
    """
    Route after data agent execution.

    Check if calculator is next in plan, otherwise go to next planned tool.
    """
    return route_to_next_planned_tool(state, current_tool="get_layer0_data")


def route_after_calculator_agent(state: GraphState) -> str:
    """
    Route after calculator agent execution.

    Check if insight agent is next in plan, otherwise go to next planned tool.
    """
    return route_to_next_planned_tool(state, current_tool="calculate_layer1_metrics")


def route_after_insight_agent(state: GraphState) -> str:
    """
    Route after insight agent execution.

    Check if more tools needed, otherwise go to synthesis.
    """
    return route_to_next_planned_tool(state, current_tool="search_vector_insights")


def route_to_next_planned_tool(state: GraphState, current_tool: str) -> str:
    """
    Generic router to find next tool in plan.

    Args:
        state: Current graph state
        current_tool: Tool that just executed

    Returns:
        Next agent node or synthesizer if plan complete
    """
    plan = state.get("plan", [])

    # Find current tool index
    try:
        current_index = plan.index(current_tool)
    except ValueError:
        # Tool not in plan, go to synthesis
        return "synthesizer_agent"

    # Check if there are more tools
    if current_index + 1 >= len(plan):
        # Plan complete, go to synthesis
        return "synthesizer_agent"

    # Get next tool
    next_tool = plan[current_index + 1]

    # Map to agent
    tool_to_agent = {
        "get_layer0_data": "data_agent",
        "calculate_layer1_metrics": "calculator_agent",
        "search_vector_insights": "insight_agent",
        "get_location_context": "insight_agent",
        "optimize_product_mix": "calculator_agent"
    }

    return tool_to_agent.get(next_tool, "synthesizer_agent")


def route_after_synthesis(state: GraphState) -> Literal["__end__"] | str:
    """
    Route after synthesis - check if refinement needed.

    Args:
        state: Current graph state

    Returns:
        END if done, otherwise loop back to planning for refinement
    """
    iteration = state.get("iteration", 0)
    confidence = state.get("confidence", 0.0)
    errors = state.get("errors", [])

    # Max iterations check
    if iteration >= 10:
        return END

    # If high confidence and no errors, end
    if confidence >= 0.7 and not errors:
        return END

    # If synthesis failed (no analysis/insights), retry once
    analysis = state.get("analysis", "")
    insights = state.get("insights", "")

    if not analysis or not insights:
        if iteration < 3:  # Allow up to 3 retries for synthesis
            # Loop back to planning to try different approach
            return "planning_agent"

    # Otherwise, end (even if incomplete)
    return END


# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================

def create_atlas_v4_graph() -> StateGraph:
    """
    Create the ATLAS v4 LangGraph workflow.

    Returns:
        Compiled StateGraph ready for execution
    """

    # Initialize graph with GraphState schema
    workflow = StateGraph(GraphState)

    # ========================================================================
    # ADD NODES (6 Agents)
    # ========================================================================

    workflow.add_node("intent_agent", intent_agent_node)
    workflow.add_node("planning_agent", planning_agent_node)
    workflow.add_node("data_agent", data_agent_node)
    workflow.add_node("calculator_agent", calculator_agent_node)
    workflow.add_node("insight_agent", insight_agent_node)
    workflow.add_node("synthesizer_agent", synthesizer_agent_node)

    # ========================================================================
    # SET ENTRY POINT
    # ========================================================================

    workflow.set_entry_point("intent_agent")

    # ========================================================================
    # ADD CONDITIONAL EDGES (Routing Logic)
    # ========================================================================

    # After Intent Agent → Always go to Planning Agent
    workflow.add_conditional_edges(
        "intent_agent",
        route_after_intent,
        {
            "planning_agent": "planning_agent"
        }
    )

    # After Planning Agent → Route to first tool in plan
    workflow.add_conditional_edges(
        "planning_agent",
        route_after_planning,
        {
            "data_agent": "data_agent",
            "calculator_agent": "calculator_agent",
            "insight_agent": "insight_agent",
            "synthesizer_agent": "synthesizer_agent"
        }
    )

    # After Data Agent → Route to next tool or synthesis
    workflow.add_conditional_edges(
        "data_agent",
        route_after_data_agent,
        {
            "calculator_agent": "calculator_agent",
            "insight_agent": "insight_agent",
            "synthesizer_agent": "synthesizer_agent"
        }
    )

    # After Calculator Agent → Route to next tool or synthesis
    workflow.add_conditional_edges(
        "calculator_agent",
        route_after_calculator_agent,
        {
            "insight_agent": "insight_agent",
            "synthesizer_agent": "synthesizer_agent"
        }
    )

    # After Insight Agent → Route to next tool or synthesis
    workflow.add_conditional_edges(
        "insight_agent",
        route_after_insight_agent,
        {
            "calculator_agent": "calculator_agent",
            "synthesizer_agent": "synthesizer_agent"
        }
    )

    # After Synthesizer Agent → Check if refinement needed (loop-back) or END
    workflow.add_conditional_edges(
        "synthesizer_agent",
        route_after_synthesis,
        {
            "planning_agent": "planning_agent",  # Loop back for refinement
            END: END
        }
    )

    # ========================================================================
    # COMPILE GRAPH
    # ========================================================================

    return workflow.compile()


# ============================================================================
# EXECUTION FUNCTION
# ============================================================================

async def execute_atlas_v4_query(
    query: str,
    region: str = None,
    project_id: int = None,
    session_id: str = None
) -> Dict[str, Any]:
    """
    Execute ATLAS v4 query using LangGraph.

    Args:
        query: User's natural language query
        region: Optional region filter
        project_id: Optional project ID filter
        session_id: Optional session ID for tracking

    Returns:
        Dict with analysis, insights, recommendations, and metadata
    """

    # Create graph
    graph = create_atlas_v4_graph()

    # Initialize state
    initial_state: GraphState = {
        # INPUT
        "query": query,
        "region": region,
        "project_id": project_id,
        "session_id": session_id,

        # INTENT & PLANNING
        "intent": None,
        "intent_confidence": 0.0,
        "intent_reasoning": None,
        "plan": [],
        "plan_reasoning": None,

        # EXECUTION TRACKING
        "tool_calls": [],
        "current_tool": None,
        "iteration": 0,

        # DATA LAYERS
        "layer0_data": None,
        "layer1_metrics": None,
        "layer2_insights": None,
        "vector_insights": None,
        "location_context": None,

        # SYNTHESIS
        "analysis": None,
        "insights": None,
        "recommendations": None,

        # METADATA & CONTROL
        "confidence": 0.0,
        "completeness": 0.0,
        "errors": [],
        "warnings": [],

        # OUTPUT
        "final_output": None,
        "validation_passed": False
    }

    # Execute graph
    try:
        final_state = await graph.ainvoke(initial_state)

        # Build response dict
        response_dict = {
            "status": "success",
            "query": query,
            "intent": final_state.get("intent"),
            "intent_confidence": final_state.get("intent_confidence", 0.0),
            "analysis": final_state.get("analysis", ""),
            "insights": final_state.get("insights", ""),
            "recommendations": final_state.get("recommendations", {}),
            "metadata": {
                "confidence": final_state.get("confidence", 0.0),
                "completeness": final_state.get("completeness", 0.0),
                "iterations": final_state.get("iteration", 0),
                "tool_calls": final_state.get("tool_calls", []),
                "plan": final_state.get("plan", []),
                "plan_reasoning": final_state.get("plan_reasoning", "")
            },
            "errors": final_state.get("errors", []),
            "warnings": final_state.get("warnings", [])
        }

        # Validate response with Pydantic
        try:
            validated_response = validate_atlas_v4_response(response_dict)
            return validated_response.model_dump()

        except ValidationError as ve:
            # Validation failed - return error response
            error_msg = f"Response validation failed: {str(ve)}"
            error_response = create_error_response(
                query=query,
                error=error_msg,
                intent=final_state.get("intent")
            )
            return error_response.model_dump()

    except Exception as e:
        # Graph execution error
        error_response = create_error_response(
            query=query,
            error=f"Graph execution error: {str(e)}",
            intent=None
        )
        return error_response.model_dump()


# Synchronous wrapper for backward compatibility
def execute_atlas_v4_query_sync(
    query: str,
    region: str = None,
    project_id: int = None,
    session_id: str = None
) -> Dict[str, Any]:
    """
    Synchronous wrapper for execute_atlas_v4_query.

    Args:
        query: User's natural language query
        region: Optional region filter
        project_id: Optional project ID filter
        session_id: Optional session ID for tracking

    Returns:
        Dict with analysis, insights, recommendations, and metadata
    """
    import asyncio

    try:
        # Get or create event loop
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # Create new event loop if none exists
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(
        execute_atlas_v4_query(query, region, project_id, session_id)
    )
