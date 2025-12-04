"""
ATLAS v4 Graph State Schema

Immutable state management for LangGraph with rich tracking
"""

from typing import TypedDict, List, Dict, Optional, Literal, Any
from typing_extensions import Annotated
import operator


class GraphState(TypedDict):
    """
    ATLAS v4 Graph State

    Tracks complete execution flow through LangGraph with immutable updates
    """

    # ============ INPUT ============
    query: str
    region: Optional[str]
    project_id: Optional[int]
    session_id: Optional[str]

    # ============ INTENT & PLANNING ============
    intent: Optional[Literal[
        "DATA_RETRIEVAL",
        "CALCULATION",
        "COMPARISON",
        "INSIGHT",
        "STRATEGIC",
        "CONTEXT_ENRICHMENT"
    ]]
    intent_confidence: float
    intent_reasoning: Optional[str]

    plan: List[str]  # Ordered tool names to execute
    plan_reasoning: Optional[str]

    # ============ EXECUTION TRACKING ============
    tool_calls: Annotated[List[Dict[str, Any]], operator.add]  # Append-only history
    current_tool: Optional[str]
    iteration: int

    # ============ DATA LAYERS ============
    layer0_data: Optional[Dict[str, Any]]      # Raw dimensions: U, C, T, L²
    layer1_metrics: Optional[Dict[str, Any]]   # Derived: PSF, AR, velocity
    layer2_insights: Optional[Dict[str, Any]]  # Calculated: NPV, IRR
    vector_insights: Optional[List[Dict[str, Any]]]  # VectorDB semantic search results
    location_context: Optional[Dict[str, Any]]  # Google APIs data

    # ============ SYNTHESIS ============
    analysis: Optional[str]          # Part 1: What data shows
    insights: Optional[str]          # Part 2: Why/how factors
    recommendations: Optional[Dict[str, Any]]   # Part 3: Strategic guidance

    # ============ METADATA & CONTROL ============
    confidence: float  # Overall confidence in response (0-1)
    completeness: float  # Data completeness (0-1)
    errors: Annotated[List[str], operator.add]  # Append-only error log
    warnings: Annotated[List[str], operator.add]  # Append-only warning log

    # ============ OUTPUT ============
    final_output: Optional[Dict[str, Any]]
    validation_passed: bool


def create_initial_state(
    query: str,
    region: Optional[str] = None,
    project_id: Optional[int] = None,
    session_id: Optional[str] = None
) -> GraphState:
    """
    Create initial state for graph execution

    Args:
        query: User query
        region: Optional region context
        project_id: Optional project ID
        session_id: Optional session ID for multi-turn

    Returns:
        Initial GraphState with defaults
    """
    return GraphState(
        # Input
        query=query,
        region=region,
        project_id=project_id,
        session_id=session_id,

        # Intent & Planning
        intent=None,
        intent_confidence=0.0,
        intent_reasoning=None,
        plan=[],
        plan_reasoning=None,

        # Execution
        tool_calls=[],
        current_tool=None,
        iteration=0,

        # Data Layers
        layer0_data=None,
        layer1_metrics=None,
        layer2_insights=None,
        vector_insights=None,
        location_context=None,

        # Synthesis
        analysis=None,
        insights=None,
        recommendations=None,

        # Metadata
        confidence=0.0,
        completeness=0.0,
        errors=[],
        warnings=[],

        # Output
        final_output=None,
        validation_passed=False
    )


def update_state(
    state: GraphState,
    **updates: Any
) -> GraphState:
    """
    Immutably update state

    For list fields with Annotated[..., operator.add], appends to existing list
    For other fields, replaces value

    Args:
        state: Current state
        **updates: Fields to update

    Returns:
        New state dict with updates applied
    """
    new_state = state.copy()

    for key, value in updates.items():
        if key in state:
            # For annotated list fields, append instead of replace
            if key in ["tool_calls", "errors", "warnings"]:
                if isinstance(value, list):
                    new_state[key] = state[key] + value
                else:
                    new_state[key] = state[key] + [value]
            else:
                new_state[key] = value
        else:
            # New field, just set it
            new_state[key] = value

    return new_state
