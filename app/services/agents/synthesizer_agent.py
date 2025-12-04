"""
Synthesizer Agent - 3-Part Output Generation

Generates ANALYSIS + INSIGHTS + RECOMMENDATIONS from all collected data
"""

import os
from typing import Dict, Any
import google.generativeai as genai
import json

from app.services.graph_state import GraphState


# ATLAS Synthesis Prompt
ATLAS_SYNTHESIS_PROMPT = """You are ATLAS - Analytical Tool built around real estate strategy.

## YOUR TASK
Generate a comprehensive analytical response with MANDATORY 3-part structure:

**Part 1: ANALYSIS** (What the data shows)
**Part 2: INSIGHTS** (Why things are the way they are)
**Part 3: RECOMMENDATIONS** (What to do about it)

---

## INPUT DATA

**User Query:** {query}
**Intent:** {intent}
**Region:** {region}

**Layer 0 Data (Raw Dimensions):**
{layer0_summary}

**Layer 1 Metrics (Calculated):**
{layer1_summary}

**Market Intelligence (VectorDB):**
{vector_summary}

---

## MANDATORY OUTPUT STRUCTURE

You MUST generate all 3 parts:

### PART 1: ANALYSIS
- Synthesize Layer 0/1 data into meaningful patterns
- Quantify with metrics and benchmarks
- Compare against market averages
- Identify trends, anomalies, correlations
- Example: "Chakan's average PSF of ₹3,645 is 49% below Pune average (₹7,200), indicating value positioning in industrial belt"

### PART 2: INSIGHTS
- Explain root causes using market intelligence (VectorDB)
- Connect Layer 1 metrics to real-world factors
- Reference infrastructure, demographics, developer strategy
- Example: "Low PSF driven by: (1) Industrial focus (workforce housing), (2) Distance from IT hubs (15km), (3) Limited current metro access"

### PART 3: RECOMMENDATIONS
- Provide actionable strategic guidance
- Include timing, target segments, pricing strategy
- Suggest alternatives and risk mitigation
- Segment by stakeholder:
  - **For Developers:** Product strategy, pricing, launch timing
  - **For Investors:** Entry/exit timing, expected returns, risks
  - **Timing:** When to act
  - **Risks:** What could go wrong

---

## CRITICAL RULES

1. **Never Just List Data** - Always interpret and contextualize
2. **Use Numbers with Context** - "₹3,645 PSF (49% below market)" not just "₹3,645"
3. **Connect Dots** - Link calculated metrics to market intelligence
4. **Be Specific** - "Target 2BHK at ₹3,200-3,800 PSF" not "Consider affordable housing"
5. **Segment Recommendations** - Different advice for developers vs investors
6. **Include Timing** - "Hold until 2026-2027" not just "Hold"

---

## RESPONSE FORMAT

Return JSON:
{{
  "analysis": "What data shows (200+ words)",
  "insights": "Why/how factors (200+ words)",
  "recommendations": {{
    "for_developers": "Strategic guidance for developers",
    "for_investors": "Strategic guidance for investors",
    "timing": "When to act and market inflection points",
    "risks": ["Risk 1", "Risk 2", "Risk 3"]
  }}
}}

**If data is incomplete:** Still provide analysis based on available data + VectorDB insights. Acknowledge gaps.

Generate response now:
"""


def format_layer0_summary(layer0_data: Dict[str, Any]) -> str:
    """Format Layer 0 data for prompt"""
    if not layer0_data or not layer0_data.get("projects"):
        return "No Layer 0 data available"

    total_projects = layer0_data.get("total_projects", 0)
    projects = layer0_data.get("projects", [])

    # Sample first 3 projects
    sample = projects[:3]

    summary = f"Total Projects: {total_projects}\n\nSample Projects:\n"
    for p in sample:
        summary += f"- {p.get('project_name', 'Unknown')}: "
        summary += f"PSF ₹{p.get('current_price_psf', 'N/A')}, "
        summary += f"Units {p.get('total_units', 'N/A')}\n"

    return summary


def format_layer1_summary(layer1_metrics: Dict[str, Any]) -> str:
    """Format Layer 1 metrics for prompt"""
    if not layer1_metrics or layer1_metrics.get("error"):
        return "No Layer 1 metrics available"

    aggregates = layer1_metrics.get("aggregates", {})

    summary = "Aggregated Metrics:\n"
    if "avg_psf" in aggregates:
        summary += f"- Average PSF: ₹{aggregates['avg_psf']:.0f}\n"
        summary += f"  Range: ₹{aggregates.get('min_psf', 0):.0f} - ₹{aggregates.get('max_psf', 0):.0f}\n"

    if "avg_absorption_rate" in aggregates:
        summary += f"- Average Absorption Rate: {aggregates['avg_absorption_rate']:.2f}%/month\n"

    if "avg_sales_velocity" in aggregates:
        summary += f"- Average Sales Velocity: {aggregates['avg_sales_velocity']:.1f} units/month\n"

    if "avg_density" in aggregates:
        summary += f"- Average Density: {aggregates['avg_density']:.1f} units/acre\n"

    return summary if summary != "Aggregated Metrics:\n" else "No calculated metrics"


def format_vector_summary(vector_insights: list) -> str:
    """Format VectorDB insights for prompt"""
    if not vector_insights:
        return "No market intelligence available from VectorDB"

    summary = "Market Intelligence Insights:\n"
    for insight in vector_insights[:3]:  # Top 3
        text = insight.get("text", "")
        # Truncate long texts
        if len(text) > 300:
            text = text[:300] + "..."
        summary += f"- {text}\n"

    return summary


def synthesizer_agent_node(state: GraphState) -> GraphState:
    """
    Synthesizer Agent Node - LangGraph node function

    Generates ANALYSIS + INSIGHTS + RECOMMENDATIONS from all collected data

    Args:
        state: Current graph state with all data layers

    Returns:
        Updated state with analysis, insights, recommendations
    """

    # Configure Gemini
    api_key = os.getenv('GOOGLE_API_KEY', 'AIzaSyAG33P0W7MaScsX7VJxBy-dPJiiIbZ_XhM')
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')

    # Prepare summaries
    layer0_summary = format_layer0_summary(state.get("layer0_data"))
    layer1_summary = format_layer1_summary(state.get("layer1_metrics"))
    vector_summary = format_vector_summary(state.get("vector_insights"))

    # Generate prompt
    prompt = ATLAS_SYNTHESIS_PROMPT.format(
        query=state["query"],
        intent=state.get("intent", "INSIGHT"),
        region=state.get("region", "Not specified"),
        layer0_summary=layer0_summary,
        layer1_summary=layer1_summary,
        vector_summary=vector_summary
    )

    errors = []
    warnings = []

    try:
        # Call Gemini
        response = model.generate_content(prompt)
        response_text = response.text

        # Parse JSON response
        import re

        # Extract JSON from markdown code blocks if present
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)

        result = json.loads(response_text)

        # Extract parts
        analysis = result.get("analysis", "")
        insights = result.get("insights", "")
        recommendations = result.get("recommendations", {})

        # Validate minimum content
        if len(analysis) < 50:
            warnings.append("Analysis is too short (< 50 chars)")
        if len(insights) < 50:
            warnings.append("Insights are too short (< 50 chars)")
        if not recommendations:
            warnings.append("Recommendations are missing")

        # Update confidence
        confidence = state.get("confidence", 0.0)
        if analysis and insights and recommendations:
            confidence = min(confidence + 0.3, 1.0)

    except Exception as e:
        errors.append(f"Error in synthesis: {str(e)}")
        # Fallback to partial output
        analysis = "Error generating analysis. See raw data above."
        insights = "Error generating insights."
        recommendations = {
            "for_developers": "Consult with real estate advisor",
            "for_investors": "Consult with real estate advisor",
            "timing": "Unknown",
            "risks": ["Incomplete analysis due to error"]
        }
        confidence = 0.3

    # Update state
    updated_state = {
        **state,
        "analysis": analysis,
        "insights": insights,
        "recommendations": recommendations,
        "confidence": confidence,
        "iteration": state["iteration"] + 1
    }

    # Add errors and warnings
    if errors:
        updated_state["errors"] = errors
    if warnings:
        updated_state["warnings"] = warnings

    # Log tool call
    tool_call = {
        "tool": "synthesize_output",
        "args": {"intent": state.get("intent")},
        "result_summary": f"Generated {len(analysis)} chars analysis, {len(insights)} chars insights",
        "confidence": confidence
    }
    updated_state["tool_calls"] = [tool_call]

    return updated_state
