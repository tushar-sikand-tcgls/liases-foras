"""
Intent Agent - Semantic Intent Classification

NO keyword matching - uses LLM semantic understanding
"""

import os
from typing import Dict, Any
import google.generativeai as genai

from app.services.graph_state import GraphState


# Intent classification prompt
INTENT_CLASSIFICATION_PROMPT = """You are an intent classifier for ATLAS - a real estate analytics system.

Classify the user's query into ONE of these intents using SEMANTIC UNDERSTANDING (NOT keyword matching):

**Intent Categories:**

1. DATA_RETRIEVAL - User wants factual information about entities (regions, projects, developers)
   - Seeks information ABOUT something
   - Not asking WHY or SHOULD
   - Example: "Tell me about Chakan", "Show me projects in Hinjewadi"

2. CALCULATION - User wants a computed metric or mathematical result
   - Requires quantitative analysis
   - Formula application needed
   - Example: "What's the average PSF?", "Calculate IRR"

3. COMPARISON - User wants to evaluate options or rank alternatives
   - Relative assessment between entities
   - Ranking or ordering by criteria
   - Example: "Compare Chakan vs Hinjewadi", "Top 3 projects by PSF"

4. INSIGHT - User seeks understanding of causality or mechanisms
   - Explanation of WHY/HOW
   - Root cause analysis
   - Example: "Why is absorption low?", "What factors affect pricing?"

5. STRATEGIC - User needs decision support or guidance
   - Advice or recommendation
   - Strategic direction
   - Example: "Should I invest?", "Optimize product mix"

6. CONTEXT_ENRICHMENT - User wants location-specific environmental/geographic data
   - Physical location attributes
   - Not market metrics
   - Example: "Show me map", "Distance to school", "What's nearby?"

**CRITICAL:** Understand the SEMANTIC INTENT of the ENTIRE query, not just keywords.

**Example:**
- "Why is PSF calculated this way?" → CALCULATION (wants formula explanation)
- "Why is PSF low in Chakan?" → INSIGHT (wants causal analysis)

Both have "why" but different intents!

**Your Task:**
Classify this query: "{query}"
{context}

Respond in JSON format:
{{
  "intent": "INTENT_NAME",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation of why this intent"
}}
"""


def classify_intent(query: str, region: str = None, project_id: int = None) -> Dict[str, Any]:
    """
    Classify intent using Gemini LLM

    Args:
        query: User query
        region: Optional region context
        project_id: Optional project ID

    Returns:
        Dict with intent, confidence, reasoning
    """

    # Configure Gemini
    api_key = os.getenv('GOOGLE_API_KEY', 'AIzaSyAG33P0W7MaScsX7VJxBy-dPJiiIbZ_XhM')
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')

    # Build context string
    context_parts = []
    if region:
        context_parts.append(f"Region context: {region}")
    if project_id:
        context_parts.append(f"Project ID context: {project_id}")

    context = "\nContext: " + ", ".join(context_parts) if context_parts else ""

    # Generate prompt
    prompt = INTENT_CLASSIFICATION_PROMPT.format(query=query, context=context)

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

        # Validate intent
        valid_intents = [
            "DATA_RETRIEVAL",
            "CALCULATION",
            "COMPARISON",
            "INSIGHT",
            "STRATEGIC",
            "CONTEXT_ENRICHMENT"
        ]

        if result.get("intent") not in valid_intents:
            # Fallback to INSIGHT as safest default
            return {
                "intent": "INSIGHT",
                "confidence": 0.5,
                "reasoning": f"Invalid intent '{result.get('intent')}', defaulting to INSIGHT"
            }

        return result

    except Exception as e:
        # Fallback on error
        return {
            "intent": "INSIGHT",
            "confidence": 0.3,
            "reasoning": f"Error in classification: {str(e)}, defaulting to INSIGHT"
        }


def intent_agent_node(state: GraphState) -> GraphState:
    """
    Intent Agent Node - LangGraph node function

    Classifies user query intent using semantic understanding

    Args:
        state: Current graph state

    Returns:
        Updated state with intent, intent_confidence, intent_reasoning
    """

    query = state["query"]
    region = state.get("region")
    project_id = state.get("project_id")

    # Classify intent
    classification = classify_intent(query, region, project_id)

    # Update state
    return {
        **state,
        "intent": classification["intent"],
        "intent_confidence": classification["confidence"],
        "intent_reasoning": classification["reasoning"],
        "iteration": state["iteration"] + 1
    }
