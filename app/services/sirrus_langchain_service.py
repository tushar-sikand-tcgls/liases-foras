"""
SIRRUS.AI LangChain Service: Multi-Dimensional Insight Engine

Implements the SIRRUS.AI system prompt with LangChain agent orchestration:
- Layer 0: Raw dimensions (U, C, T, L²) from Knowledge Graph
- Layer 1: Derived metrics (PSF, AR, velocity) using calculators
- Layer 2: Insights (analysis of Layer 1) using LLM
- Layer 3: Strategic insights (optimization) using algorithms

Architecture:
    User Query → LangChain Agent → Tools (KG, Calculators, VectorDB) → LLM Synthesis → Insights
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

# Import existing services
from app.services.data_service import data_service
from app.services.vector_db_service import VectorDBService
from app.services.context_service import ContextService
from app.calculators.layer1 import Layer1Calculator
from app.calculators.layer2 import Layer2Calculator
from app.calculators.layer3 import Layer3Optimizer


# ATLAS System Prompt (Analytical Tool built around real estate strategy)
SIRRUS_SYSTEM_PROMPT = """You are ATLAS - Analytical Tool built around real estate strategy.

## CRITICAL: YOU ARE AN ANALYTICAL ADVISOR, NOT A DATA RETRIEVAL BOT

**Your Purpose:**
- Generate **ANALYSIS** of market trends and project performance
- Provide **INSIGHTS** into "why" and "how" factors drive outcomes
- Deliver **RECOMMENDATIONS** for strategic decision-making

**You are NOT:**
- ❌ A data dump service ("Here are 8 projects in Chakan" is WRONG)
- ❌ A calculator bot ("PSF is ₹3645" without context is WRONG)
- ❌ A list generator (raw tables without interpretation is WRONG)

**You ARE:**
- ✅ A strategic advisor that interprets data
- ✅ An insight engine that explains "why" behind numbers
- ✅ A recommendation system that guides investment decisions

## YOUR ROLE

You generate insights following a 4-layer hierarchy:
- **Layer 0**: Raw dimensions (U=Units, C=Cashflow, T=Time, L²=Area) [INPUT - from Knowledge Graph]
- **Layer 1**: Derived metrics (PSF, Absorption Rate, Sales Velocity) [CALCULATED - using tools]
- **Layer 2**: Analytical Insights (comparisons, patterns, risks) [YOU GENERATE - by analyzing Layer 1]
- **Layer 3**: Strategic Insights (optimization, recommendations) [YOU GENERATE - using algorithms]

## INTENT RECOGNITION (CRITICAL - DO THIS FIRST!)

Classify the user's query intent using **semantic understanding**, NOT keyword matching.

Think about:
- **What is the user ultimately trying to achieve?**
- **What type of answer would satisfy their need?**
- **What tools would provide the necessary information?**

### Intent Category 1: DATA_RETRIEVAL (Knowledge Graph)
**Purpose:** User wants to know about entities (regions, projects, developers)
**Semantic Meaning:** Query seeks information ABOUT something, not WHY or SHOULD
**Tool Routing:** `get_region_layer0_data` → Knowledge Graph query
**Example Semantic Patterns:**
- Informational query about a place/project
- Request for factual data
- Exploratory discovery ("what exists here?")

### Intent Category 2: CALCULATION (Python Calculators)
**Purpose:** User wants a computed metric or mathematical result
**Semantic Meaning:** Query requires quantitative analysis or formula application
**Tool Routing:** `get_region_layer0_data` + `calculate_layer1_metrics` → Deterministic calculations
**Example Semantic Patterns:**
- Request for a specific numerical metric
- Mathematical operation needed
- Derived quantity from raw dimensions

### Intent Category 3: COMPARISON (KG + Calculators)
**Purpose:** User wants to evaluate options or rank alternatives
**Semantic Meaning:** Query involves relative assessment between multiple entities
**Tool Routing:** `get_region_layer0_data` (multiple) + `calculate_layer1_metrics` → Multi-entity analysis
**Example Semantic Patterns:**
- Evaluating multiple options
- Ranking or ordering by criteria
- Relative performance assessment

### Intent Category 4: INSIGHT (Why/How - LLM Analysis)
**Purpose:** User seeks understanding of causality or mechanisms
**Semantic Meaning:** Query asks for explanation, root causes, or factors driving outcomes
**Tool Routing:** `get_region_layer0_data` + `search_market_insights` → GraphRAG analysis
**Example Semantic Patterns:**
- Causal inquiry (why/how something happens)
- Request for explanation of a phenomenon
- Understanding factors or drivers

### Intent Category 5: STRATEGIC (Recommendations)
**Purpose:** User needs decision support or guidance
**Semantic Meaning:** Query seeks advice, recommendation, or strategic direction
**Tool Routing:** `optimize_product_mix` + full data pipeline → Layer 3 optimization
**Example Semantic Patterns:**
- Decision-making query (should I...)
- Request for strategic guidance
- Optimization or best course of action

### Intent Category 6: CONTEXT_ENRICHMENT (Location Intelligence)
**Purpose:** User wants location-specific environmental/geographic data
**Semantic Meaning:** Query relates to physical location attributes, not market metrics
**Tool Routing:** `get_location_context` → Google APIs integration
**Example Semantic Patterns:**
- Geographic/spatial information
- Environmental factors
- Physical infrastructure and proximity

---

**CRITICAL:** Do NOT use keyword matching like "if query contains 'why' then INSIGHT".
Instead, understand the **semantic intent** of the entire query.

**Example:**
- "Why is PSF calculated this way?" → CALCULATION (user wants formula explanation)
- "Why is PSF low in Chakan?" → INSIGHT (user wants causal analysis)
- Both have "why", but different intents based on context!

## CRITICAL RULES (ATLAS OUTPUT REQUIREMENTS)

### 1. **MANDATORY 3-PART RESPONSE STRUCTURE**

Every response MUST contain:

**PART 1: ANALYSIS** (What the data shows)
- Synthesize Layer 0/1 data into meaningful patterns
- Identify trends, anomalies, correlations
- Compare against benchmarks (market average, peer projects)
- Example: "Chakan's average PSF of ₹3,645 is 49% below Pune average (₹7,200), indicating value positioning in industrial belt"

**PART 2: INSIGHTS** (Why things are the way they are)
- Explain root causes using market intelligence (VectorDB)
- Connect Layer 1 metrics to real-world factors
- Reference infrastructure, demographics, developer strategy
- Example: "Low PSF driven by: (1) Industrial focus (workforce housing), (2) Distance from IT hubs (15km), (3) Limited current metro access"

**PART 3: RECOMMENDATIONS** (What to do about it)
- Provide actionable strategic guidance
- Include timing, target segments, pricing strategy
- Suggest alternatives and risk mitigation
- Example: "For developers: Target 2BHK workforce housing at ₹3,200-3,800 PSF. Launch Phase 2 post-2027 metro extension. For investors: Hold until infrastructure matures (2026-2027)"

### 2. **NEVER Output Raw Data Without Context**
❌ WRONG: "There are 8 projects in Chakan with PSF ranging from ₹2,808 to ₹4,330"
✅ RIGHT: "Chakan market shows 53% PSF variance (₹2,808-₹4,330), indicating fragmented positioning. This presents opportunity for mid-range differentiation at ₹3,500 PSF targeting value-conscious buyers."

### 3. **Other Critical Rules**
3. **Intent-First Approach**: ALWAYS classify intent BEFORE selecting tools
4. **Never Invent Data**: All numbers come from tools (Knowledge Graph, Calculators, Vector DB)
5. **Always Trace Back**: Every insight must reference Layer 1 metrics → Layer 0 dimensions
6. **Use Tools First**: Before answering, gather data using available tools
7. **Dimensional Consistency**: Validate formulas (e.g., PSF = C/L² [INR/sqft] ✓)
8. **Market Context**: Compare project metrics against market benchmarks
9. **Confidence Scores**: Rate confidence (Layer 0: 100%, Layer 1: 95%, Layer 2: 80-90%, Layer 3: 60-75%)
10. **Structured Output**: Return insights in JSON format with analysis, insights, and recommendations

## AVAILABLE TOOLS

- `get_region_layer0_data`: Fetch Layer 0 raw dimensions for a region (U, C, T, L²)
- `calculate_layer1_metrics`: Calculate derived metrics (PSF, AR, velocity) from Layer 0
- `search_market_insights`: Semantic search in vector DB for market intelligence
- `get_location_context`: Get Google APIs context (maps, weather, distances)
- `optimize_product_mix`: Run Layer 3 optimization for strategic recommendations

## ATLAS WORKFLOW (Flexible & Dynamic)

### Core Philosophy:
✅ **FLEXIBLE:** Adapt workflow to ANY query, even unforeseen requests
✅ **DYNAMIC:** Tools selected based on semantic understanding, not hardcoded rules
✅ **STRUCTURED:** Always maintain professional 3-part output structure

---

### Workflow Pattern (Adaptive)

**Step 1: SEMANTIC INTENT CLASSIFICATION**
- Understand user's underlying goal (NOT keyword matching)
- Identify information needed to answer
- Determine tool sequence dynamically

**Step 2: DYNAMIC TOOL SELECTION**
- Select tools based on what query requires, not predefined patterns
- Iterate as needed - add/skip tools based on intermediate results
- Gracefully handle missing data or incomplete information

**Step 3: ADAPTIVE EXECUTION**
- Execute tools in optimal sequence
- Interpret each result before deciding next step
- Can pivot strategy if initial approach doesn't yield sufficient info

**Step 4: STRUCTURED SYNTHESIS**
- **ALWAYS** return 3-part structured output (mandatory):
  1. **ANALYSIS:** What the data shows (with metrics + benchmarks)
  2. **INSIGHTS:** Why things are the way they are (causality + factors)
  3. **RECOMMENDATIONS:** What to do about it (strategic guidance)
- This structure ensures professional, actionable output

---

### Example: Standard Query ("Tell me about Chakan")

**Tool Sequence:**
```
1. get_region_layer0_data("Chakan")
2. calculate_layer1_metrics(...)
3. search_market_insights("Chakan market trends")
→ Synthesize into 3-part structure
```

---

### Example: Unforeseen Query ("What's the carbon footprint of Chakan projects?")

**Adaptive Workflow:**
```
LLM Thought: "I don't have a carbon footprint tool, but I can adapt..."

Step 1: get_region_layer0_data("Chakan")
   → Get project dimensions

Step 2: calculate_layer1_metrics(...)
   → Get total area, units (proxy for building size)

Step 3: search_market_insights("Chakan construction sustainability")
   → Search VectorDB for any sustainability/environmental data

Step 4: get_location_context("Chakan, Pune")
   → Get environmental data (air quality, etc.)

Synthesis (3-part structure):
- ANALYSIS: "8 projects totaling X sqft built area. No direct carbon data available."
- INSIGHTS: "Industrial area with AQI 156 (Moderate). Construction materials/methods not documented."
- RECOMMENDATIONS: "For carbon assessment: (1) Request builder green certifications (2) Use sqft × regional carbon intensity as proxy (3) Focus on operational emissions (HVAC, water) rather than embodied carbon"
```

**Key:** Even for unexpected query, maintains professional structure!

---

### Example: Ambiguous Query ("Is Chakan good?")

**Adaptive Workflow:**
```
LLM Thought: "'Good' is subjective - need to clarify perspective"

Step 1: get_region_layer0_data("Chakan")
Step 2: calculate_layer1_metrics(...)
Step 3: search_market_insights("Chakan market opportunity")

Synthesis (Multi-perspective):
- ANALYSIS: "Chakan shows ₹3,645 PSF (49% below Pune avg), 2.8%/month absorption"
- INSIGHTS: "Trade-off: Value pricing + workforce demand vs limited amenities + no current metro"
- RECOMMENDATIONS:
  → For value-seeking homebuyers: "GOOD - affordable entry point"
  → For luxury buyers: "NOT IDEAL - limited premium positioning"
  → For investors: "GOOD with patience - 2027 metro inflection"
  → For flippers: "NOT GOOD - slow absorption limits quick exits"
```

**Key:** Adapts to ambiguity by providing multi-faceted analysis!

---

### Professional Output Structure (MANDATORY)

**Every response, regardless of query type, MUST follow this format:**

```json
{
  "insights": [
    {
      "section": "ANALYSIS",
      "content": "What the data objectively shows...",
      "metrics": [...],
      "benchmarks": {...}
    },
    {
      "section": "INSIGHTS",
      "content": "Why/how factors drive these outcomes...",
      "root_causes": [...],
      "market_context": {...}
    },
    {
      "section": "RECOMMENDATIONS",
      "content": "Strategic guidance for action...",
      "for_developers": "...",
      "for_investors": "...",
      "timing": "...",
      "risks": [...]
    }
  ]
}
```

This structure works for ANY query - flexible workflow, structured output!

## EXAMPLE OUTPUT FORMAT

```json
{
  "insights": [
    {
      "insight_metadata": {
        "insight_id": "CHAKAN_ABSORPTION_STATUS",
        "insight_layer": 2,
        "insight_type": "Absorption_Status",
        "context_entity": "region",
        "generated_at": "2025-12-02T12:00:00Z"
      },
      "insight_content": {
        "summary": "Chakan region absorbs at 2.8%/month (market average: 3.2%/month). Current pace indicates 24-month clearance for existing inventory.",
        "reasoning": "Aggregated Layer 1 metric Absorption_Rate across 3 projects in Chakan (Sara City: 2.5%, VTP Pegasus: 3.0%, Megapolis: 2.9%) averages 2.8%/month. Compared to Pune market average of 3.2%/month (12.5% slower).",
        "dimensional_analysis": "AR = [U_sold] ÷ ([U_total] × [T_elapsed]) = [1/month] ✓ Valid"
      },
      "layer_1_data_used": [
        {
          "metric": "Absorption_Rate_Chakan_Avg",
          "value": 0.028,
          "unit": "1/month",
          "derived_from": "Aggregated from 3 projects' Layer_0 data"
        }
      ],
      "market_context": {
        "pune_avg_absorption_rate": 0.032,
        "deviation_from_market": -0.125,
        "percentile_rank": 42
      },
      "confidence": {
        "score": 85,
        "drivers": ["Complete Layer 0 data for 3 projects", "Market benchmark from Q3 data"],
        "limitations": "Only 3 projects in Chakan; small sample size may not represent full market"
      },
      "recommendation": {
        "action": "Focus on absorption acceleration strategies for Chakan projects",
        "rationale": "Below-market absorption (12.5% slower) indicates either pricing issues or marketing gaps",
        "alternatives": ["Investigate pricing sensitivity", "Enhance marketing reach", "Evaluate competitive positioning"]
      }
    }
  ],
  "summary": "Chakan is a developing micro-market in Pune with 3 active projects totaling 550 units. Absorption is slightly below Pune average but improving. Key opportunity: 2BHK segment shows strongest demand.",
  "metadata": {
    "query": "Tell me about Chakan",
    "region": "Chakan",
    "total_insights_generated": 1,
    "layers_analyzed": [0, 1, 2],
    "timestamp": "2025-12-02T12:00:00Z"
  }
}
```

## KEY PRINCIPLES

- **Data Integrity**: Never fabricate metrics. All numbers trace to Layer 0.
- **Transparency**: Show calculation methods and data sources.
- **Business Value**: Focus on actionable insights, not just data regurgitation.
- **Dimensional Rigor**: Validate all formulas using dimensional analysis.
- **Confidence Honesty**: State limitations clearly; don't oversell certainty.

Now, process the user's query using tools and generate insights following this framework.
"""


class SirrusLangChainService:
    """
    LangChain-based SIRRUS.AI service with multi-layered insight generation
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize SIRRUS.AI LangChain service"""
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or "AIzaSyAG33P0W7MaScsX7VJxBy-dPJiiIbZ_XhM"

        # Initialize LLM (Gemini 2.5 Flash)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=self.api_key,
            temperature=0.2,  # Lower temperature for more deterministic insights
            convert_system_message_to_human=True
        )

        # Initialize services
        self.data_service = data_service
        self.vector_db = VectorDBService()
        self.context_service = ContextService()

        # Create tools (using decorator pattern)
        self.tools = self._create_tools()

        # Bind tools to LLM (Gemini's native function calling)
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        print("✓ SIRRUS.AI LangChain Service initialized")

    def _create_tools(self) -> List:
        """Create LangChain tools using @tool decorator"""

        # Define tools using decorator pattern for better type hints
        @tool
        def get_region_layer0_data(region: str) -> str:
            """Get Layer 0 raw dimensions (U, C, T, L²) for all projects in a region.

            Args:
                region: region name (e.g., 'Chakan', 'Hinjewadi')

            Returns:
                JSON with all projects' Layer 0 data (units, area, revenue, time, sold/unsold)
            """
            return self._tool_get_region_layer0_data(region)

        @tool
        def calculate_layer1_metrics(layer0_json: str) -> str:
            """Calculate Layer 1 derived metrics (PSF, AR, velocity) from Layer 0 data.

            Args:
                layer0_json: Layer 0 data JSON (from get_region_layer0_data)

            Returns:
                JSON with calculated PSF, Absorption Rate, Sales Velocity, MOI, etc.
            """
            return self._tool_calculate_layer1_metrics(layer0_json)

        @tool
        def search_market_insights(query: str) -> str:
            """Search vector database for market intelligence and insights.

            Args:
                query: search query (e.g., 'Chakan infrastructure development', 'Hinjewadi growth trends')

            Returns:
                Relevant market insights from city reports
            """
            return self._tool_search_market_insights(query)

        @tool
        def get_location_context(location_and_city: str) -> str:
            """Get location context using Google APIs (maps, weather, distances, air quality).

            Args:
                location_and_city: location name and city (e.g., "Chakan, Pune")

            Returns:
                Comprehensive location context
            """
            return self._tool_get_location_context(location_and_city)

        return [
            get_region_layer0_data,
            calculate_layer1_metrics,
            search_market_insights,
            get_location_context
        ]

    def _tool_get_region_layer0_data(self, region: str) -> str:
        """Tool: Get Layer 0 raw dimensions for a region"""
        try:
            # Get all projects in the region
            projects = self.data_service.get_projects_by_location(region)

            if not projects:
                return json.dumps({"error": f"No projects found in region: {region}"})

            # Extract Layer 0 data (U, C, T, L²)
            layer0_data = []
            for project in projects:
                project_l0 = {
                    "project_id": project.get("projectId", {}).get("value"),
                    "project_name": project.get("projectName", {}).get("value"),
                    "developer": project.get("developerName", {}).get("value"),
                    "location": project.get("location", {}).get("value"),
                    "region": project.get("region", {}).get("value"),
                    "micromarket": project.get("microMarket", {}).get("value"),
                    # U - Units
                    "total_units": project.get("totalUnits", {}).get("value"),
                    "sold_units": project.get("soldUnits", {}).get("value"),
                    "unsold_units": project.get("unsoldUnits", {}).get("value"),
                    # L² - Area
                    "total_saleable_area_sqft": project.get("saleableAreaSqft", {}).get("value"),
                    "land_area_acres": project.get("landAreaAcres", {}).get("value"),
                    # T - Time
                    "launch_date": project.get("launchDate", {}).get("value"),
                    "possession_date": project.get("possessionDate", {}).get("value"),
                    # C - Cashflow
                    "current_price_psf": project.get("currentPricePSF", {}).get("value"),
                    "launch_price_psf": project.get("launchPricePSF", {}).get("value"),
                }
                layer0_data.append(project_l0)

            result = {
                "region": region,
                "total_projects": len(layer0_data),
                "projects": layer0_data
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps({"error": f"Error fetching Layer 0 data: {str(e)}"})

    def _tool_calculate_layer1_metrics(self, layer0_json: str) -> str:
        """Tool: Calculate Layer 1 derived metrics from Layer 0"""
        try:
            layer0_data = json.loads(layer0_json) if isinstance(layer0_json, str) else layer0_json

            projects = layer0_data.get("projects", [])
            layer1_results = []

            for project in projects:
                project_l1 = {
                    "project_id": project["project_id"],
                    "project_name": project["project_name"],
                    "layer1_metrics": {}
                }

                # Calculate PSF (already in Layer 0, but validate)
                if project.get("current_price_psf"):
                    project_l1["layer1_metrics"]["PSF"] = {
                        "value": project["current_price_psf"],
                        "unit": "INR/sqft",
                        "dimension": "C/L²",
                        "note": "From Layer 0 data"
                    }

                # Calculate Absorption Rate (if we have time data)
                # For now, use monthly velocity as proxy
                if project.get("sold_units") and project.get("total_units"):
                    # Assume 12 months elapsed (simplified)
                    months_elapsed = 12
                    ar = Layer1Calculator.calculate_absorption_rate(
                        units_sold=project["sold_units"],
                        total_units=project["total_units"],
                        months_elapsed=months_elapsed
                    )
                    project_l1["layer1_metrics"]["AbsorptionRate"] = ar

                # Calculate Sales Velocity
                if project.get("sold_units"):
                    months_elapsed = 12
                    sv = Layer1Calculator.calculate_sales_velocity(
                        units_sold=project["sold_units"],
                        months_elapsed=months_elapsed
                    )
                    project_l1["layer1_metrics"]["SalesVelocity"] = sv

                # Calculate Months of Inventory
                if project.get("unsold_units") and project.get("sold_units"):
                    months_elapsed = 12
                    velocity = project["sold_units"] / months_elapsed
                    if velocity > 0:
                        moi = project["unsold_units"] / velocity
                        project_l1["layer1_metrics"]["MonthsOfInventory"] = {
                            "value": round(moi, 2),
                            "unit": "months",
                            "dimension": "T",
                            "formula": "U_unsold / (U_sold / T_elapsed)"
                        }

                layer1_results.append(project_l1)

            result = {
                "region": layer0_data.get("region"),
                "total_projects": len(layer1_results),
                "layer1_metrics": layer1_results
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps({"error": f"Error calculating Layer 1 metrics: {str(e)}"})

    def _tool_search_market_insights(self, query: str) -> str:
        """Tool: Search vector DB for market insights"""
        try:
            results = self.vector_db.semantic_search(
                query=query,
                n_results=5
            )
            return json.dumps({"query": query, "insights": results}, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Error searching market insights: {str(e)}"})

    def _tool_get_location_context(self, location_and_city: str) -> str:
        """Tool: Get location context from Google APIs"""
        try:
            # Parse input (format: "Chakan, Pune")
            parts = location_and_city.split(",")
            location = parts[0].strip() if len(parts) > 0 else location_and_city
            city = parts[1].strip() if len(parts) > 1 else None

            context = self.context_service.get_location_context(
                location_name=location,
                city=city
            )
            return json.dumps(context, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Error getting location context: {str(e)}"})

    def _tool_optimize_product_mix(self, optimization_params_json: str) -> str:
        """Tool: Run Layer 3 product mix optimization"""
        try:
            params = json.loads(optimization_params_json) if isinstance(optimization_params_json, str) else optimization_params_json

            result = Layer3Optimizer.optimize_product_mix(
                total_units=params["total_units"],
                total_land_area_sqft=params["total_land_area_sqft"],
                total_project_cost=params["total_project_cost"],
                project_duration_months=params["project_duration_months"],
                market_data=params["market_data"]
            )

            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Error optimizing product mix: {str(e)}"})

    def _execute_tool_calls(self, tool_calls: list) -> list:
        """Execute tool calls and return results"""
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})

            # Find matching tool
            for tool in self.tools:
                if tool.name == tool_name:
                    try:
                        result = tool.invoke(tool_args)
                        results.append({
                            "tool": tool_name,
                            "args": tool_args,
                            "result": result
                        })
                    except Exception as e:
                        results.append({
                            "tool": tool_name,
                            "args": tool_args,
                            "error": str(e)
                        })
                    break
        return results

    def process_query(
        self,
        query: str,
        region: Optional[str] = None,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process user query using SIRRUS.AI framework with native function calling

        Args:
            query: User query (e.g., "Tell me about Chakan")
            region: Selected region context (optional)
            project_id: Selected project ID (optional)

        Returns:
            Dict with insights following SIRRUS.AI format
        """

        # Build context-aware query
        context_parts = []
        if region:
            context_parts.append(f"[Context: User has selected region '{region}']")
        if project_id:
            context_parts.append(f"[Context: User is viewing Project ID {project_id}]")

        full_query = " ".join(context_parts + [query]) if context_parts else query

        # Initialize conversation messages
        messages = [
            SystemMessage(content=SIRRUS_SYSTEM_PROMPT),
            HumanMessage(content=full_query)
        ]

        all_tool_calls = []
        max_iterations = 10
        iteration = 0

        try:
            # Iterative function calling loop
            while iteration < max_iterations:
                iteration += 1

                # Invoke LLM with tools
                response = self.llm_with_tools.invoke(messages)

                # Check if LLM wants to call tools
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    # Execute tool calls
                    tool_results = self._execute_tool_calls(response.tool_calls)
                    all_tool_calls.extend(tool_results)

                    # Add AI response with tool calls to messages
                    messages.append(response)

                    # Add tool results as ToolMessage for each tool call
                    for i, tool_call in enumerate(response.tool_calls):
                        tool_result = tool_results[i] if i < len(tool_results) else {"error": "No result"}
                        result_content = tool_result.get('result', tool_result.get('error', 'Unknown error'))

                        messages.append(
                            ToolMessage(
                                content=str(result_content),
                                tool_call_id=tool_call.get('id', f"call_{i}")
                            )
                        )

                    # Continue loop for next iteration
                    continue
                else:
                    # No more tool calls, extract final answer
                    final_response = response.content

                    # Try to parse as JSON for structured SIRRUS.AI format
                    try:
                        insights = json.loads(final_response)
                    except:
                        # If not JSON, wrap in structured format
                        insights = {
                            "insights": [],
                            "summary": final_response,
                            "metadata": {
                                "query": query,
                                "region": region,
                                "timestamp": datetime.utcnow().isoformat() + "Z",
                                "tool_calls": all_tool_calls,
                                "iterations": iteration
                            }
                        }

                    return insights

            # Max iterations reached
            return {
                "error": f"Max iterations ({max_iterations}) reached",
                "query": query,
                "tool_calls": all_tool_calls
            }

        except Exception as e:
            return {
                "error": f"Error processing query: {str(e)}",
                "query": query,
                "region": region,
                "tool_calls": all_tool_calls
            }


# Global singleton
_sirrus_service_instance = None

def get_sirrus_service() -> SirrusLangChainService:
    """Get or create SIRRUS.AI LangChain service singleton"""
    global _sirrus_service_instance
    if _sirrus_service_instance is None:
        _sirrus_service_instance = SirrusLangChainService()
    return _sirrus_service_instance
