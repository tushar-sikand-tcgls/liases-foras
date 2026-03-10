"""
QueryState Schema - State definition for LangGraph orchestrator

This module defines the state structure that flows through all nodes in the
LangGraph state machine. It includes all information needed for query execution,
from initial input through to final answer composition.

Key Design Principles:
1. All state updates are additive (nodes add to state, never remove)
2. State is fully serializable for conversation persistence
3. Provenance tracked at every step
4. Multi-turn support via conversation_history
"""

from typing import TypedDict, List, Dict, Optional, Any, Literal


class QueryState(TypedDict, total=False):
    """
    State structure for LangGraph query orchestration

    This state flows through all 8 nodes in the state machine,
    accumulating information at each step.
    """

    # ============================================================================
    # INPUT SECTION - Initial query information
    # ============================================================================

    query: str
    """User's natural language query"""

    session_id: str
    """Unique session identifier for multi-turn conversations"""

    conversation_history: List[Dict[str, str]]
    """
    Previous turns in this session
    Format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    """

    # ============================================================================
    # INTENT CLASSIFICATION - Node 1 output
    # ============================================================================

    intent: Literal["objective", "analytical", "financial"]
    """
    Query intent classification:
    - objective: Direct retrieval of specific values
    - analytical: Aggregation, comparison, or multi-project analysis
    - financial: Financial calculations requiring formulas (IRR, NPV, etc.)
    """

    subcategory: Optional[str]
    """Specific type within intent (e.g., "IRR_calculation", "comparison", "direct_retrieval")"""

    confidence: float
    """LLM confidence in intent classification (0.0-1.0)"""

    classification_reasoning: Optional[str]
    """LLM's explanation of why this intent was chosen"""

    # ============================================================================
    # ENTITY EXTRACTION - Node 1 output
    # ============================================================================

    raw_entities: Dict[str, List[str]]
    """
    Raw entities extracted by LLM before resolution
    Format: {
        "projects": ["sara city", "the urbana"],
        "developers": ["sara builders"],
        "locations": ["chakan"],
        "attributes": ["sold %", "total units"]
    }
    """

    # ============================================================================
    # ATTRIBUTE RESOLUTION - Node 2 output
    # ============================================================================

    resolved_attributes: List[Dict[str, Any]]
    """
    Attributes resolved via Vector DB semantic search
    Each dict contains:
    - Target Attribute: Canonical name
    - Unit: Measurement unit
    - Dimension: Dimensional formula (CF/L^2, U/T, etc.)
    - Description: What this attribute means
    - Formula/Derivation: How it's calculated
    - Layer: L0, L1, L2, or L3
    - Sample Prompt: Example questions
    """

    attribute_search_results: Optional[List[Dict]]
    """Raw Vector DB search results with similarity scores"""

    # ============================================================================
    # ENTITY RESOLUTION - Node 3 output
    # ============================================================================

    resolved_projects: List[str]
    """Canonical project names resolved from raw entities"""

    resolved_developers: List[str]
    """Canonical developer names resolved from raw entities"""

    resolved_locations: List[str]
    """Canonical location names resolved from raw entities"""

    entity_resolution_details: Optional[Dict[str, Dict]]
    """
    Details about entity resolution process
    Format: {
        "projects": {"sara city": "Sara City", "urbana": "The Urbana"},
        "fuzzy_matches": [{"input": "sara", "match": "Sara City", "score": 0.95}]
    }
    """

    # ============================================================================
    # KG QUERY PLANNING - Node 4 output
    # ============================================================================

    kg_query_plan: List[Dict[str, Any]]
    """
    Structured query plan for KG execution
    Format: [
        {
            "action": "fetch|aggregate|compare",
            "projects": ["Sara City"],
            "attributes": ["Total Units"],
            "filters": {"location": "Chakan"},
            "aggregation": null|"sum|avg|max|min|count"
        }
    ]
    """

    # ============================================================================
    # KG EXECUTION - Node 5 output
    # ============================================================================

    kg_data: Dict[str, Any]
    """
    Data retrieved from Knowledge Graph (SINGLE SOURCE OF TRUTH)
    Format varies by query type:
    - Objective: {"Sara City.totalUnits": 3018}
    - Analytical: {"max_sold_pct": 96, "projects": [...]}
    - Financial: {"Sara City.annual_sales": 45.2, "Sara City.total_investment": 350.0}
    """

    kg_execution_details: Optional[Dict[str, Any]]
    """
    Metadata about KG query execution
    - query_count: Number of queries executed
    - execution_time_ms: Time taken
    - data_sources: Which LF pillars were used
    """

    # ============================================================================
    # PARAMETER CHECKING - Node 6 output
    # ============================================================================

    missing_parameters: Optional[List[str]]
    """
    List of parameters needed but not provided (for financial queries)
    Examples: ["discount_rate", "holding_period", "exit_value"]
    """

    has_all_parameters: bool
    """Whether all required parameters are available"""

    # ============================================================================
    # COMPUTATION - Node 7 output
    # ============================================================================

    computation_results: Optional[Dict[str, Any]]
    """
    Results from financial calculations (deterministic, not from LLM)
    Format: {
        "irr": 18.7,
        "npv": 125.5,
        "payback_period": 4.2,
        "calculation_method": "scipy.optimize.newton",
        "assumptions": [...],
        "sensitivity": {
            "base_case": {"irr": 18.7, "npv": 125.5},
            "optimistic": {"irr": 22.3, "npv": 156.2},
            "conservative": {"irr": 15.1, "npv": 98.3}
        }
    }
    """

    # ============================================================================
    # ANSWER COMPOSITION - Node 8 output
    # ============================================================================

    answer: str
    """
    Final natural language answer composed by LLM
    Includes provenance markers:
    - [DIRECT - KG] for values retrieved directly from KG
    - [COMPUTED] for calculated values
    - [ASSUMED] for assumption-based values
    """

    provenance: Dict[str, Any]
    """
    Full provenance trail for answer
    Format: {
        "data_sources": ["KG", "VectorDB"],
        "lf_pillars": ["1.2", "2.1"],
        "lf_data_version": "Q3_FY25",
        "calculation_methods": ["scipy.optimize.newton"],
        "timestamp": "2024-01-15T10:30:00Z",
        "layer0_inputs": ["Total Units", "Saleable Area"],
        "layer1_intermediates": ["PSF", "Absorption Rate"],
        "assumptions": [...]
    }
    """

    # ============================================================================
    # ROUTING & CONTROL FLOW
    # ============================================================================

    next_action: Literal["answer", "ask_clarification", "gather_parameters", "error"]
    """
    Determines next step in state machine:
    - answer: All done, return answer to user
    - ask_clarification: Need to ask user for missing information
    - gather_parameters: Need to collect additional parameters for financial calc
    - error: Something went wrong, return error message
    """

    clarification_question: Optional[str]
    """Question to ask user if next_action is ask_clarification"""

    # ============================================================================
    # ERROR HANDLING
    # ============================================================================

    error: Optional[str]
    """Error message if something went wrong"""

    error_details: Optional[Dict[str, Any]]
    """Additional error context for debugging"""

    # ============================================================================
    # EXECUTION METADATA
    # ============================================================================

    execution_path: List[str]
    """
    List of nodes executed in this query
    Example: ["intent_classifier", "attribute_resolver", "kg_executor", "answer_composer"]
    """

    total_execution_time_ms: Optional[float]
    """Total time from query to answer"""

    node_timings: Optional[Dict[str, float]]
    """Individual node execution times for performance monitoring"""


# ============================================================================
# HELPER TYPES
# ============================================================================

class ConversationMessage(TypedDict):
    """Structure for conversation history entries"""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: Optional[str]


class AttributeMetadata(TypedDict):
    """Structure for resolved attribute metadata from Vector DB"""
    target_attribute: str
    unit: str
    dimension: str
    description: str
    formula_derivation: str
    layer: str
    sample_prompt: str
    variation_in_prompt: str
    assumption_in_prompt: str
    sample_values: str
    expected_answer: str


class KGQueryPlan(TypedDict):
    """Structure for a single KG query in the plan"""
    action: Literal["fetch", "aggregate", "compare"]
    projects: Optional[List[str]]
    attributes: List[str]
    filters: Optional[Dict[str, Any]]
    aggregation: Optional[Literal["sum", "avg", "max", "min", "count"]]


class ProvenanceInfo(TypedDict):
    """Structure for provenance tracking"""
    data_sources: List[str]
    lf_pillars: List[str]
    lf_data_version: str
    calculation_methods: List[str]
    timestamp: str
    layer0_inputs: List[str]
    layer1_intermediates: List[str]
    layer2_dependencies: Optional[List[str]]
    assumptions: List[str]


# ============================================================================
# STATE INITIALIZATION
# ============================================================================

def create_initial_state(
    query: str,
    session_id: str,
    conversation_history: Optional[List[ConversationMessage]] = None
) -> QueryState:
    """
    Create initial state for a new query

    Args:
        query: User's natural language query
        session_id: Session identifier for multi-turn conversations
        conversation_history: Previous conversation turns (if any)

    Returns:
        Initial QueryState with required fields populated
    """
    return QueryState(
        query=query,
        session_id=session_id,
        conversation_history=conversation_history or [],
        has_all_parameters=True,  # Assume true until proven otherwise
        execution_path=[],
        raw_entities={},
        resolved_projects=[],
        resolved_developers=[],
        resolved_locations=[],
        resolved_attributes=[],
        kg_query_plan=[],
        kg_data={},
        next_action="answer"  # Will be updated by nodes
    )


# ============================================================================
# STATE VALIDATION
# ============================================================================

def validate_state_for_answer(state: QueryState) -> bool:
    """
    Check if state has all required fields for answer composition

    Args:
        state: Current query state

    Returns:
        True if state is ready for answer composition, False otherwise
    """
    required_fields = [
        "query",
        "intent",
        "resolved_attributes",
        "kg_data"
    ]

    for field in required_fields:
        if field not in state or state[field] is None:
            return False

    # For financial queries, also check computation_results
    if state.get("intent") == "financial":
        if "computation_results" not in state or state["computation_results"] is None:
            return False

    return True
