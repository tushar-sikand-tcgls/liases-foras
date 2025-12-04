# ATLAS v4 - LangGraph Architecture

## Vision: Fine-Grained Agents + Coarse-Grained MCP Server

```
┌─────────────────────────────────────────────────────────────────┐
│ MCP SERVER (Coarse-Grained Agent)                                │
│ - Overall orchestration across all fine-grained agents          │
│ - Cross-agent state management                                  │
│ - High-level decision making                                    │
│ - TODO: To be implemented after fine-grained agents complete    │
└─────────────────────────────────────────────────────────────────┘
                          ↓ coordinates
┌─────────────────────────────────────────────────────────────────┐
│ FINE-GRAINED AGENTS (Tools/Capabilities)                         │
│                                                                  │
│ 1. Intent Agent      - Semantic intent classification           │
│ 2. Planning Agent    - Dynamic tool sequencing                  │
│ 3. Data Agent        - Knowledge Graph L0 access                │
│ 4. Calculator Agent  - Python functions L1/L2                   │
│ 5. Insight Agent     - VectorDB + GraphRAG synthesis            │
│ 6. Synthesizer Agent - ANALYSIS + INSIGHTS + RECOMMENDATIONS    │
└─────────────────────────────────────────────────────────────────┘
```

---

## LangGraph Structure (Branching with Loop-Back)

```
                    ┌─────────────────┐
                    │  START          │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Intent Agent    │
                    │ (Semantic)      │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Planning Agent  │
                    │ (Tool Sequence) │
                    └────────┬────────┘
                             ↓
                  ┌──────────┴──────────┐
                  │  Route by Intent    │
                  └──────────┬──────────┘
                             ↓
        ┌────────────────────┼────────────────────┐
        ↓                    ↓                    ↓
┌───────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Data Path     │  │ Calculation Path │  │ Insight Path     │
│ (L0 KG)       │  │ (L0 + L1/L2)     │  │ (L0+L1+Vector)   │
└───────┬───────┘  └────────┬─────────┘  └────────┬─────────┘
        │                   │                      │
        └────────────────┬──┴──────────────────────┘
                         ↓
                ┌─────────────────┐
                │ Check Complete? │◄─────┐
                └────────┬────────┘      │
                         ↓               │ loop back if
                    Yes  │  No           │ confidence < 0.8
                         ↓               │ or iteration < 10
                ┌─────────────────┐      │
                │ Synthesizer     │──────┘
                │ Agent (3-part)  │
                └────────┬────────┘
                         ↓
                ┌─────────────────┐
                │ Validate Output │
                └────────┬────────┘
                         ↓
                    ┌────────┐
                    │  END   │
                    └────────┘
```

---

## State Schema (Rich State - Immutable Updates)

```python
from typing import TypedDict, List, Dict, Optional, Literal
from typing_extensions import Annotated

class GraphState(TypedDict):
    """
    ATLAS v4 Graph State

    Immutable updates via langgraph.graph.add_messages pattern
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

    plan: List[str]  # Ordered tool names: ["get_layer0", "calculate_layer1", ...]
    plan_reasoning: Optional[str]

    # ============ EXECUTION TRACKING ============
    tool_calls: Annotated[List[Dict], "append"]  # History of all tool executions
    current_tool: Optional[str]
    iteration: int

    # ============ DATA LAYERS ============
    layer0_data: Optional[Dict]      # Raw dimensions: U, C, T, L²
    layer1_metrics: Optional[Dict]   # Derived: PSF, AR, velocity
    layer2_insights: Optional[Dict]  # Calculated: NPV, IRR
    vector_insights: Optional[List[Dict]]  # VectorDB semantic search results
    location_context: Optional[Dict]  # Google APIs data

    # ============ SYNTHESIS ============
    analysis: Optional[str]          # Part 1: What data shows
    insights: Optional[str]          # Part 2: Why/how factors
    recommendations: Optional[str]   # Part 3: Strategic guidance

    # ============ METADATA & CONTROL ============
    confidence: float  # Overall confidence in response (0-1)
    completeness: float  # Data completeness (0-1)
    errors: Annotated[List[str], "append"]  # Error log
    warnings: Annotated[List[str], "append"]  # Warning log

    # ============ OUTPUT ============
    final_output: Optional[Dict]
    validation_passed: bool
```

---

## Agent Definitions (Fine-Grained)

### 1. Intent Agent
**Purpose:** Semantic intent classification (NO keyword matching)

**Input:** `query`, `region`, `project_id`
**Output:** `intent`, `intent_confidence`, `intent_reasoning`

**Logic:**
- Uses LLM with classification prompt
- Analyzes semantic meaning of entire query
- Returns one of 6 intent categories
- Provides reasoning for transparency

**Example:**
```python
Input: "Why is PSF low in Chakan?"
Output: {
    "intent": "INSIGHT",
    "intent_confidence": 0.95,
    "intent_reasoning": "Query seeks causal explanation (why), not just PSF value. Requires market intelligence from VectorDB."
}
```

---

### 2. Planning Agent
**Purpose:** Dynamic tool sequencing based on intent

**Input:** `intent`, `query`, current `state`
**Output:** `plan`, `plan_reasoning`

**Logic:**
- Creates ordered list of tools to execute
- Adapts based on what data is already in state
- Handles missing data gracefully

**Example:**
```python
Intent: "INSIGHT"
Output: {
    "plan": [
        "get_layer0_data",
        "calculate_layer1_metrics",
        "search_vector_insights"
    ],
    "plan_reasoning": "Need L0 data first, calculate metrics, then explain with market context"
}
```

---

### 3. Data Agent (Knowledge Graph L0)
**Purpose:** Retrieve raw dimensions from Knowledge Graph

**Input:** `region`, `project_id`
**Output:** Updates `layer0_data` in state

**Tools:**
- `data_service.get_projects_by_location(region)`
- `data_service.get_project_by_id(project_id)`

**Error Handling:**
- If no data found → Add warning, continue
- If partial data → Log completeness score

---

### 4. Calculator Agent (Python Functions L1/L2)
**Purpose:** Execute deterministic calculations

**Input:** `layer0_data`
**Output:** Updates `layer1_metrics`, `layer2_insights`

**Tools:**
- Layer 1: PSF, ASP, Absorption Rate, Sales Velocity, Density
- Layer 2: NPV, IRR, Payback Period, Profitability Index

**Error Handling:**
- If missing L0 data → Calculate what's possible, log gaps
- Validate dimensional consistency (PSF = C/L²)

---

### 5. Insight Agent (VectorDB + GraphRAG)
**Purpose:** Semantic search + causal analysis

**Input:** `query`, `region`, `layer1_metrics`
**Output:** Updates `vector_insights`

**Tools:**
- ChromaDB semantic search
- Combines structured (KG) + unstructured (VectorDB) data

**Logic:**
- Search VectorDB with semantic query
- Connect VectorDB insights to calculated metrics
- Explain causality

---

### 6. Synthesizer Agent (3-Part Output)
**Purpose:** Generate ANALYSIS + INSIGHTS + RECOMMENDATIONS

**Input:** All state data (L0, L1, L2, vector, etc.)
**Output:** `analysis`, `insights`, `recommendations`, `final_output`

**Structure (Mandatory):**
```json
{
  "analysis": "What data shows (with metrics + benchmarks)",
  "insights": "Why/how factors drive outcomes",
  "recommendations": {
    "for_developers": "...",
    "for_investors": "...",
    "timing": "...",
    "risks": [...]
  }
}
```

**Error Handling:**
- Validate all 3 parts present
- Minimum length requirements
- Retry if incomplete

---

## Conditional Routing Logic

### Route by Intent:
```python
def route_by_intent(state: GraphState) -> str:
    """Route to appropriate path based on intent"""
    intent = state["intent"]

    if intent == "DATA_RETRIEVAL":
        return "data_agent"

    elif intent == "CALCULATION":
        return "data_agent"  # Need L0 first, then calculator

    elif intent == "COMPARISON":
        return "data_agent"  # Multi-entity, then calculator

    elif intent in ["INSIGHT", "STRATEGIC"]:
        return "data_agent"  # Full pipeline: L0 → L1 → Vector

    elif intent == "CONTEXT_ENRICHMENT":
        return "location_context_agent"

    else:
        return "data_agent"  # Default fallback
```

### Check Completeness:
```python
def check_completeness(state: GraphState) -> str:
    """Decide if we have enough data or need more"""

    # Check confidence and completeness
    if state["confidence"] >= 0.8 and state["completeness"] >= 0.7:
        return "synthesizer"  # Enough data

    # Check iteration limit
    if state["iteration"] >= 10:
        return "synthesizer"  # Max iterations reached

    # Check if plan has remaining tools
    if state["plan"]:
        return "executor"  # Execute next tool in plan

    # Edge case: Low confidence but no more tools
    if state["confidence"] < 0.8:
        state["warnings"].append("Low confidence but no more tools available")
        return "synthesizer"

    return "synthesizer"
```

---

## Error Handling Strategy

### 1. Retry with Exponential Backoff
```python
async def execute_tool_with_retry(tool_name: str, args: Dict, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            result = await execute_tool(tool_name, args)
            return result
        except Exception as e:
            if attempt == max_retries - 1:
                raise  # Final attempt failed
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### 2. Fallback Strategies
```python
def execute_with_fallback(state: GraphState, primary_tool: str, fallback_tool: str):
    try:
        result = execute_tool(primary_tool)
        return result
    except Exception as e:
        state["warnings"].append(f"{primary_tool} failed: {e}. Using fallback {fallback_tool}")
        return execute_tool(fallback_tool)
```

### 3. Continue with Partial Data
```python
def handle_missing_data(state: GraphState):
    """Continue execution even with incomplete data"""
    if not state["layer0_data"]:
        state["warnings"].append("Layer 0 data unavailable. Using VectorDB only.")
        state["plan"] = ["search_vector_insights"]  # Adjust plan
```

---

## Output Validation (Pydantic)

```python
from pydantic import BaseModel, Field, field_validator

class ATLASOutput(BaseModel):
    """Validated ATLAS output structure"""

    analysis: str = Field(
        ...,
        min_length=100,
        description="What the data shows (metrics + benchmarks)"
    )

    insights: str = Field(
        ...,
        min_length=100,
        description="Why/how factors drive outcomes"
    )

    recommendations: Dict[str, Any] = Field(
        ...,
        description="Strategic guidance (developers, investors, timing, risks)"
    )

    metadata: Dict = Field(
        default_factory=dict,
        description="Execution metadata (tools used, confidence, warnings)"
    )

    @field_validator('recommendations')
    def validate_recommendations(cls, v):
        required_keys = ['for_developers', 'for_investors', 'timing', 'risks']
        missing = [k for k in required_keys if k not in v]
        if missing:
            raise ValueError(f"Missing recommendation keys: {missing}")
        return v

def validate_output(state: GraphState) -> str:
    """Validate final output structure"""
    try:
        validated = ATLASOutput(
            analysis=state["analysis"],
            insights=state["insights"],
            recommendations=state["recommendations"],
            metadata={
                "tool_calls": state["tool_calls"],
                "confidence": state["confidence"],
                "warnings": state["warnings"]
            }
        )
        state["validation_passed"] = True
        state["final_output"] = validated.model_dump()
        return "success"

    except Exception as e:
        state["errors"].append(f"Validation failed: {e}")

        # Retry synthesis if validation fails and iteration < 3
        if state["iteration"] < 3:
            return "retry_synthesis"
        else:
            # Max retries, return partial output
            state["validation_passed"] = False
            return "partial_success"
```

---

## Graph Construction (LangGraph Code Structure)

```python
from langgraph.graph import StateGraph, END

# Initialize graph
workflow = StateGraph(GraphState)

# Add nodes (agents)
workflow.add_node("intent_agent", intent_agent_node)
workflow.add_node("planning_agent", planning_agent_node)
workflow.add_node("data_agent", data_agent_node)
workflow.add_node("calculator_agent", calculator_agent_node)
workflow.add_node("insight_agent", insight_agent_node)
workflow.add_node("synthesizer_agent", synthesizer_agent_node)
workflow.add_node("validator", validator_node)

# Set entry point
workflow.set_entry_point("intent_agent")

# Add edges
workflow.add_edge("intent_agent", "planning_agent")
workflow.add_conditional_edges(
    "planning_agent",
    route_by_intent,
    {
        "data_agent": "data_agent",
        "location_context_agent": "location_context_agent"
    }
)

# Conditional loop-back
workflow.add_conditional_edges(
    "calculator_agent",
    check_completeness,
    {
        "synthesizer": "synthesizer_agent",
        "executor": "data_agent",  # Loop back for more data
    }
)

workflow.add_edge("synthesizer_agent", "validator")
workflow.add_conditional_edges(
    "validator",
    lambda state: "success" if state["validation_passed"] else "partial",
    {
        "success": END,
        "partial": END
    }
)

# Compile graph
app = workflow.compile()
```

---

## Advantages Over v3 (LangChain)

### 1. Advanced State Management
- **v3:** Messages-based, implicit state
- **v4:** Explicit TypedDict state with clear structure
- **Benefit:** Know exactly what data is available at each step

### 2. Enhanced Control Flow
- **v3:** Linear tool calling loop
- **v4:** Branching paths by intent, conditional loop-back
- **Benefit:** Different workflows for different query types

### 3. Transparency & Debugging
- **v3:** Black box agent execution
- **v4:** Visual graph, state snapshots at each node
- **Benefit:** Debug failures, optimize workflows

### 4. Error Recovery
- **v3:** Try-catch in single loop
- **v4:** Retry at node level, fallback routing, graceful degradation
- **Benefit:** Robust execution even with failures

### 5. Modularity
- **v3:** Single orchestrator with tools
- **v4:** 6 fine-grained agents, composable
- **Benefit:** Easy to add/modify individual agents

---

## Testing Strategy

### 1. Unit Tests (Per Agent)
- Test each agent node independently
- Mock state input/output
- Validate state mutations

### 2. Integration Tests (Full Graph)
- Test complete graph execution
- Validate state flow between nodes
- Check routing logic

### 3. Error Scenario Tests
- Test with missing data
- Test with tool failures
- Test retry/fallback mechanisms

### 4. Comparison Tests (v3 vs v4)
- Same queries to both versions
- Compare output quality
- Measure latency difference

---

## Migration Plan

### Phase 1: Build v4 Core (Current)
1. ✅ Architecture design
2. 🔄 Implement GraphState
3. 🔄 Implement 6 agents
4. 🔄 Build graph structure
5. 🔄 Add validation

### Phase 2: Testing & Refinement
1. Port v3 test queries
2. Add graph-specific tests
3. Optimize performance
4. Add visualization

### Phase 3: Deployment
1. Create `/api/qa/question/v4` endpoint
2. Run v3 and v4 side by side
3. Compare outputs
4. Gradual migration

### Phase 4: MCP Server (Future)
1. Design coarse-grained MCP agent
2. Coordinate across fine-grained agents
3. Cross-session state management
4. Multi-user orchestration

---

## File Structure

```
app/
├── services/
│   ├── atlas_v4_langgraph_service.py  # Main graph implementation
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── intent_agent.py            # Agent 1
│   │   ├── planning_agent.py          # Agent 2
│   │   ├── data_agent.py              # Agent 3
│   │   ├── calculator_agent.py        # Agent 4
│   │   ├── insight_agent.py           # Agent 5
│   │   └── synthesizer_agent.py       # Agent 6
│   └── graph_state.py                 # State schema
│
├── api/
│   └── atlas_v4_routes.py             # v4 endpoints
│
tests/
├── test_atlas_v4_agents.py            # Unit tests per agent
├── test_atlas_v4_graph.py             # Integration tests
└── test_atlas_v3_vs_v4.py             # Comparison tests
```

---

## Next Steps

1. Implement `GraphState` schema
2. Implement Intent Agent
3. Implement Planning Agent
4. Implement Data Agent
5. Implement Calculator Agent
6. Implement Insight Agent
7. Implement Synthesizer Agent
8. Build graph structure
9. Add validation
10. Create v4 endpoint
11. Test & refine
12. Document MCP Server architecture

Ready to start implementation! 🚀
