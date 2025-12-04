"""
Planning Agent - Dynamic Tool Sequencing

Creates execution plan based on intent and current state
"""

import os
from typing import List, Dict, Any
import google.generativeai as genai

from app.services.graph_state import GraphState


# Planning prompt
PLANNING_PROMPT = """You are a planning agent for ATLAS - a real estate analytics system.

Your task: Create an ordered execution plan (list of tools) to answer the user's query.

**Query:** {query}
**Intent:** {intent}
**Intent Reasoning:** {intent_reasoning}

**Available Tools:**

1. **get_layer0_data** - Retrieve raw dimensions (U, C, T, L²) from Knowledge Graph
   - Use when: Need project/region data
   - Returns: Project dimensions, metrics

2. **calculate_layer1_metrics** - Calculate derived metrics (PSF, AR, velocity) from Layer 0
   - Use when: Need calculated metrics
   - Requires: layer0_data in state
   - Returns: PSF, ASP, Absorption Rate, Sales Velocity, Density

3. **search_vector_insights** - Semantic search in VectorDB for market intelligence
   - Use when: Need market context, "why" questions, causal analysis
   - Returns: Market insights, trends, factors

4. **get_location_context** - Google APIs for location intelligence
   - Use when: Need maps, distances, weather, air quality, proximity
   - Returns: Geographic/environmental data

5. **optimize_product_mix** - Layer 3 optimization for strategic decisions
   - Use when: Need strategic recommendations, optimization
   - Requires: layer0_data, layer1_metrics
   - Returns: Optimized strategies

**Current State:**
- layer0_data: {has_layer0}
- layer1_metrics: {has_layer1}
- vector_insights: {has_vector}
- iteration: {iteration}

**Planning Guidelines:**

1. **DATA_RETRIEVAL Intent:**
   - Usually: ["get_layer0_data"]
   - May add: ["calculate_layer1_metrics"] if metrics needed

2. **CALCULATION Intent:**
   - Usually: ["get_layer0_data", "calculate_layer1_metrics"]

3. **COMPARISON Intent:**
   - Usually: ["get_layer0_data", "calculate_layer1_metrics"]
   - May add: ["search_vector_insights"] for context

4. **INSIGHT Intent:**
   - Usually: ["get_layer0_data", "calculate_layer1_metrics", "search_vector_insights"]
   - Full pipeline for causal analysis

5. **STRATEGIC Intent:**
   - Usually: ["get_layer0_data", "calculate_layer1_metrics", "search_vector_insights", "optimize_product_mix"]
   - Complete pipeline with optimization

6. **CONTEXT_ENRICHMENT Intent:**
   - Usually: ["get_location_context"]
   - May add: ["get_layer0_data"] for project context

**CRITICAL:**
- Skip tools if data already in state (e.g., don't call get_layer0_data if layer0_data exists)
- Order matters: get_layer0_data before calculate_layer1_metrics
- Adapt to available data: if layer0_data missing, can use search_vector_insights instead

**Your Response:**
Return JSON with:
{{
  "plan": ["tool1", "tool2", ...],
  "reasoning": "Brief explanation of why this sequence"
}}

Keep plan concise (2-4 tools typically).
"""


def create_plan(
    query: str,
    intent: str,
    intent_reasoning: str,
    state: GraphState
) -> Dict[str, Any]:
    """
    Create tool execution plan using Gemini

    Args:
        query: User query
        intent: Classified intent
        intent_reasoning: Why this intent
        state: Current graph state

    Returns:
        Dict with plan (list of tools) and reasoning
    """

    # Configure Gemini
    api_key = os.getenv('GOOGLE_API_KEY', 'AIzaSyAG33P0W7MaScsX7VJxBy-dPJiiIbZ_XhM')
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')

    # Check what data already exists
    has_layer0 = "Yes" if state.get("layer0_data") else "No"
    has_layer1 = "Yes" if state.get("layer1_metrics") else "No"
    has_vector = "Yes" if state.get("vector_insights") else "No"
    iteration = state.get("iteration", 0)

    # Generate prompt
    prompt = PLANNING_PROMPT.format(
        query=query,
        intent=intent,
        intent_reasoning=intent_reasoning,
        has_layer0=has_layer0,
        has_layer1=has_layer1,
        has_vector=has_vector,
        iteration=iteration
    )

    try:
        # Call Gemini
        response = model.generate_content(prompt)
        response_text = response.text

        # Parse JSON response
        import json
        import re

        # Extract JSON from markdown code blocks if present
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)

        result = json.loads(response_text)

        # Validate tools
        valid_tools = [
            "get_layer0_data",
            "calculate_layer1_metrics",
            "search_vector_insights",
            "get_location_context",
            "optimize_product_mix"
        ]

        plan = result.get("plan", [])
        invalid_tools = [t for t in plan if t not in valid_tools]

        if invalid_tools:
            # Remove invalid tools
            plan = [t for t in plan if t in valid_tools]
            result["reasoning"] += f" (Removed invalid tools: {invalid_tools})"

        # If plan is empty, add default based on intent
        if not plan:
            plan = get_default_plan(intent)
            result["reasoning"] = f"Empty plan, using default for {intent}"

        result["plan"] = plan
        return result

    except Exception as e:
        # Fallback to default plan
        return {
            "plan": get_default_plan(intent),
            "reasoning": f"Error in planning: {str(e)}, using default plan"
        }


def get_default_plan(intent: str) -> List[str]:
    """
    Get default tool sequence for intent

    Args:
        intent: Intent category

    Returns:
        List of tool names
    """
    defaults = {
        "DATA_RETRIEVAL": ["get_layer0_data"],
        "CALCULATION": ["get_layer0_data", "calculate_layer1_metrics"],
        "COMPARISON": ["get_layer0_data", "calculate_layer1_metrics"],
        "INSIGHT": ["get_layer0_data", "calculate_layer1_metrics", "search_vector_insights"],
        "STRATEGIC": ["get_layer0_data", "calculate_layer1_metrics", "search_vector_insights"],
        "CONTEXT_ENRICHMENT": ["get_location_context"]
    }

    return defaults.get(intent, ["get_layer0_data", "search_vector_insights"])


def planning_agent_node(state: GraphState) -> GraphState:
    """
    Planning Agent Node - LangGraph node function

    Creates dynamic tool execution plan based on intent and current state

    Args:
        state: Current graph state

    Returns:
        Updated state with plan and plan_reasoning
    """

    query = state["query"]
    intent = state.get("intent", "INSIGHT")
    intent_reasoning = state.get("intent_reasoning", "")

    # Create plan
    planning_result = create_plan(query, intent, intent_reasoning, state)

    # Update state
    return {
        **state,
        "plan": planning_result["plan"],
        "plan_reasoning": planning_result["reasoning"],
        "iteration": state["iteration"] + 1
    }
