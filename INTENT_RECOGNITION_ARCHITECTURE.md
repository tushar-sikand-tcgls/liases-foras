# Intent Recognition Architecture

## Overview

The SIRRUS.AI v3 system now includes **AI-driven intent recognition** that automatically classifies user queries and routes to appropriate tools:

1. **Knowledge Graph** (data retrieval)
2. **Python Calculators** (deterministic calculations)
3. **GraphRAG** (market insights from VectorDB)
4. **Layer 3 Optimization** (strategic recommendations)
5. **Google APIs** (location intelligence)

## Architecture Flow

```
┌──────────────────────────────────────────────────────────────┐
│ User Query: "Why is absorption low in Chakan?"               │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│ Step 1: INTENT RECOGNITION (LLM Classification)              │
│                                                               │
│ SIRRUS.AI analyzes query signals:                            │
│ - "Why" → INSIGHT intent (Category 4)                        │
│ - "absorption" → Layer 1 metric                              │
│ - "Chakan" → Region context                                  │
│                                                               │
│ Classification: INTENT = INSIGHT (Why/How question)          │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│ Step 2: TOOL SELECTION (Intent-Driven Routing)               │
│                                                               │
│ INSIGHT intent → Route to:                                   │
│ 1. get_region_layer0_data("Chakan")  [Knowledge Graph]       │
│ 2. calculate_layer1_metrics(...)     [Calculator]            │
│ 3. search_market_insights("Chakan absorption factors")       │
│                                      [VectorDB - GraphRAG]   │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│ Step 3: TOOL EXECUTION (Sequential Function Calling)         │
│                                                               │
│ Tool 1: get_region_layer0_data                               │
│ → Returns: 8 projects with U, C, T, L² dimensions            │
│                                                               │
│ Tool 2: calculate_layer1_metrics                             │
│ → Calculates: PSF, Absorption Rate, Sales Velocity           │
│                                                               │
│ Tool 3: search_market_insights                               │
│ → Returns: VectorDB insights on Chakan market factors        │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│ Step 4: LLM SYNTHESIS (Layer 2 Insight Generation)           │
│                                                               │
│ SIRRUS.AI analyzes:                                          │
│ - Layer 0 data (raw dimensions)                              │
│ - Layer 1 metrics (calculated absorption rates)              │
│ - Market context (VectorDB insights)                         │
│                                                               │
│ Generates Layer 2 Insight:                                   │
│ "Absorption is low because: (1) Distance to amenities,       │
│  (2) No metro connectivity, (3) Industrial-focused area"     │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│ Response: Structured JSON with insights, reasoning, data     │
└──────────────────────────────────────────────────────────────┘
```

## 6 Intent Categories

### Category 1: DATA_RETRIEVAL
**What:** Fetching raw data from Knowledge Graph (Layer 0)

**Signals:**
- "tell me about"
- "show me"
- "list"
- "what is"
- "get"
- "fetch"
- "find projects"

**Tool Routing:** `get_region_layer0_data` → Knowledge Graph query

**Example Queries:**
| Query | Tools Used | Output |
|-------|------------|--------|
| "Tell me about Chakan" | get_region_layer0_data | 8 projects with Layer 0 dimensions |
| "Show me projects in Hinjewadi" | get_region_layer0_data | List of all Hinjewadi projects |
| "What is the total units in Sara City?" | get_region_layer0_data | U dimension for specific project |

---

### Category 2: CALCULATION
**What:** Deterministic calculations using Python functions (Layer 1)

**Signals:**
- "calculate"
- "compute"
- "what's the"
- "average"
- "sum"
- "PSF"
- "IRR"
- "NPV"
- "absorption rate"

**Tool Routing:** `get_region_layer0_data` + `calculate_layer1_metrics` → Python calculators

**Example Queries:**
| Query | Tools Used | Output |
|-------|------------|--------|
| "Calculate average PSF in Chakan" | get_region_layer0_data + calculate_layer1_metrics | ₹3645/sqft (average) |
| "What's the IRR for project 1?" | get_region_layer0_data + calculate_irr | 24.5% IRR |
| "Compute absorption rate" | get_region_layer0_data + calculate_layer1_metrics | 2.8%/month |

---

### Category 3: COMPARISON
**What:** Multi-entity comparison (Layer 0 + Layer 1)

**Signals:**
- "compare"
- "versus"
- "vs"
- "better"
- "top"
- "rank"
- "which"
- "best"

**Tool Routing:** `get_region_layer0_data` (multiple) + `calculate_layer1_metrics` → Comparative analysis

**Example Queries:**
| Query | Tools Used | Output |
|-------|------------|--------|
| "Compare Chakan vs Hinjewadi" | get_region_layer0_data (both) + calculate_layer1_metrics | PSF: Chakan ₹3645, Hinjewadi ₹7200 |
| "Top 3 projects by PSF in Chakan" | get_region_layer0_data + calculate_layer1_metrics | Ranked list with PSF values |
| "Which is better: Sara City or Gulmohar?" | get_region_layer0_data + calculate_layer1_metrics | Comparative table of metrics |

---

### Category 4: INSIGHT (GraphRAG)
**What:** Analytical insights combining KG data + VectorDB market intelligence (Layer 2)

**Signals:**
- "why"
- "how come"
- "reasons"
- "factors"
- "explain"
- "analyze"
- "what causes"

**Tool Routing:** `get_region_layer0_data` + `search_market_insights` → GraphRAG (KG + VectorDB)

**Example Queries:**
| Query | Tools Used | Output |
|-------|------------|--------|
| "Why is absorption low in Sara City?" | get_region_layer0_data + search_market_insights | Layer 2 insight: Poor amenity proximity + no metro |
| "What factors affect PSF in Chakan?" | get_region_layer0_data + search_market_insights | Industrial focus, infrastructure plans, demographics |
| "Explain pricing trends in Hinjewadi" | get_region_layer0_data + search_market_insights | IT hub premium, metro impact, demand drivers |

---

### Category 5: STRATEGIC (Layer 3 Optimization)
**What:** Strategic recommendations using algorithms (Layer 3)

**Signals:**
- "should I"
- "recommend"
- "optimize"
- "best strategy"
- "what to do"
- "advice"
- "product mix"

**Tool Routing:** `optimize_product_mix` + full data pipeline → scipy optimization / OPPS scoring

**Example Queries:**
| Query | Tools Used | Output |
|-------|------------|--------|
| "Should I invest in Chakan?" | get_region_layer0_data + search_market_insights + market_opportunity_scoring | Layer 3 OPPS score + recommendation |
| "Optimize product mix for 100 units" | get_region_layer0_data + optimize_product_mix | Optimal 1BHK/2BHK/3BHK mix with IRR |
| "Best launch strategy for Sara City Phase 2" | Full pipeline + Layer 3 tools | Strategic roadmap with timing |

---

### Category 6: CONTEXT_ENRICHMENT (Location Intelligence)
**What:** Enriching with Google APIs data (maps, weather, distances, POIs)

**Signals:**
- "location"
- "nearby"
- "distance"
- "map"
- "weather"
- "air quality"
- "proximity"
- "how far"

**Tool Routing:** `get_location_context` → Google Maps, Places, Distance Matrix, Air Quality APIs

**Example Queries:**
| Query | Tools Used | Output |
|-------|------------|--------|
| "Show me map of Chakan" | get_location_context | Google Maps static image |
| "Distance to nearest school in Chakan?" | get_location_context | 12 km via Distance Matrix API |
| "What's nearby Chakan?" | get_location_context | List of POIs from Places API |

---

## Intent Recognition System Prompt (Embedded in SIRRUS.AI)

The intent recognition logic is embedded in the SIRRUS.AI system prompt:

```python
## INTENT RECOGNITION (CRITICAL - DO THIS FIRST!)

Before selecting tools, classify the user's query intent:

### Intent Category 1: DATA_RETRIEVAL (Knowledge Graph)
**Signals:** "tell me about", "show me", "list", "what is", ...
**Route to:** `get_region_layer0_data` → Knowledge Graph query

### Intent Category 2: CALCULATION (Python Calculators)
**Signals:** "calculate", "compute", "what's the", "average", ...
**Route to:** `calculate_layer1_metrics` → Deterministic calculations

### Intent Category 3: COMPARISON (KG + Calculators)
**Signals:** "compare", "versus", "vs", "better", "top", "rank", ...
**Route to:** Multi-project analysis with KG + calculators

### Intent Category 4: INSIGHT (Why/How - LLM Analysis)
**Signals:** "why", "how come", "reasons", "factors", ...
**Route to:** `search_market_insights` → GraphRAG (KG + VectorDB)

### Intent Category 5: STRATEGIC (Recommendations)
**Signals:** "should I", "recommend", "optimize", ...
**Route to:** `optimize_product_mix` + full pipeline → Layer 3

### Intent Category 6: CONTEXT_ENRICHMENT (Location Intelligence)
**Signals:** "location", "nearby", "distance", "map", ...
**Route to:** `get_location_context` → Google APIs
```

## How LLM Makes Intent Decisions

### Example 1: "Tell me about Chakan"
```
Intent Analysis:
- Signal: "tell me about" → DATA_RETRIEVAL (Category 1)
- Entity: "Chakan" → Region identifier
- No calculation signals → No CALCULATION intent
- No comparison signals → No COMPARISON intent

Decision: DATA_RETRIEVAL
Tools: get_region_layer0_data("Chakan")
```

### Example 2: "Why is absorption low in Sara City?"
```
Intent Analysis:
- Signal: "why" → INSIGHT (Category 4)
- Signal: "absorption" → Layer 1 metric (needs calculation)
- Entity: "Sara City" → Project identifier
- Requires explanation → VectorDB market context needed

Decision: INSIGHT (GraphRAG)
Tools:
  1. get_region_layer0_data (for Sara City project)
  2. calculate_layer1_metrics (absorption rate)
  3. search_market_insights ("Sara City absorption factors")
```

### Example 3: "Compare Chakan vs Hinjewadi by PSF"
```
Intent Analysis:
- Signal: "compare" → COMPARISON (Category 3)
- Signal: "PSF" → Layer 1 metric (needs calculation)
- Entities: "Chakan", "Hinjewadi" → Multiple regions
- No "why" signal → No deep insight needed (yet)

Decision: COMPARISON
Tools:
  1. get_region_layer0_data("Chakan")
  2. get_region_layer0_data("Hinjewadi")
  3. calculate_layer1_metrics (for both regions)
  4. (Optional) search_market_insights if comparison needs context
```

### Example 4: "Should I invest in Chakan?"
```
Intent Analysis:
- Signal: "should I" → STRATEGIC (Category 5)
- Signal: "invest" → Investment decision (Layer 3)
- Entity: "Chakan" → Region
- Requires recommendation → Layer 3 optimization needed

Decision: STRATEGIC
Tools:
  1. get_region_layer0_data("Chakan")
  2. calculate_layer1_metrics (all metrics)
  3. search_market_insights ("Chakan investment opportunity")
  4. market_opportunity_scoring (OPPS score)
```

## Multi-Intent Queries (Complex Scenarios)

Some queries may have **multiple intents**. SIRRUS.AI handles these by sequencing tools:

### Example: "Compare Chakan vs Hinjewadi and explain why Hinjewadi is more expensive"

**Intent Breakdown:**
1. **Primary: COMPARISON** → Compare two regions
2. **Secondary: INSIGHT** → Explain pricing difference

**Tool Sequence:**
```
1. get_region_layer0_data("Chakan")
2. get_region_layer0_data("Hinjewadi")
3. calculate_layer1_metrics (both regions)
4. search_market_insights("Hinjewadi Chakan pricing factors")
```

**Response Structure:**
```json
{
  "insights": [
    {
      "insight_id": "CHAKAN_HINJEWADI_COMPARISON",
      "insight_layer": 2,
      "insight_type": "Comparison",
      "summary": "Hinjewadi PSF (₹7200) is 97% higher than Chakan (₹3645)"
    },
    {
      "insight_id": "HINJEWADI_PREMIUM_DRIVERS",
      "insight_layer": 2,
      "insight_type": "Pricing_Factors",
      "summary": "Hinjewadi premium driven by: IT hub, metro connectivity, higher demand"
    }
  ]
}
```

## Testing Intent Recognition

Run the intent recognition test suite:

```bash
python test_intent_recognition.py
```

**Expected Output:**
```
TEST SUMMARY
════════════════════════════════════════════════════════════════
Total Tests: 12
Passed: 10 ✅
Failed: 2 ❌
Success Rate: 83.3%

Breakdown by Intent Category:
  DATA_RETRIEVAL: 2/2 (100%)
  CALCULATION: 2/2 (100%)
  COMPARISON: 2/2 (100%)
  INSIGHT: 2/2 (100%)
  STRATEGIC: 1/2 (50%)  # May fail if optimize_product_mix tool not available
  CONTEXT_ENRICHMENT: 1/2 (50%)  # May fail if get_location_context needs API keys
```

## Benefits of Intent-Driven Architecture

### 1. **Intelligent Routing**
- LLM automatically selects appropriate tools based on query intent
- No manual routing rules needed
- Handles natural language variations ("calculate" vs "compute" vs "what's the")

### 2. **GraphRAG for Insights**
- "Why" questions automatically trigger VectorDB search
- Combines structured data (KG) with unstructured insights (VectorDB)
- Provides context-rich explanations

### 3. **Deterministic Calculations**
- Calculator tools ensure accuracy for financial metrics
- PSF, IRR, NPV use Python functions (not LLM estimation)
- Traceable provenance (Layer 0 → Layer 1 formula)

### 4. **Strategic Recommendations**
- "Should I invest?" questions route to Layer 3 optimization
- Uses scipy algorithms for product mix optimization
- OPPS scoring for market opportunity analysis

### 5. **Location Intelligence**
- Automatically enriches with Google APIs when location context is needed
- Distance to schools, hospitals, transport hubs
- Maps, weather, air quality data

### 6. **Transparency**
- All tool calls logged in metadata
- Response includes which tools were used and why
- User can see the reasoning chain

---

## Future Enhancements

### 1. **Intent Confidence Scores**
Add explicit confidence scoring for intent classification:
```json
{
  "intent": {
    "primary": "INSIGHT",
    "confidence": 0.95,
    "secondary": "COMPARISON",
    "confidence": 0.30
  }
}
```

### 2. **Intent Clarification**
Ask user for clarification when intent is ambiguous:
```
User: "Show me Chakan"
SIRRUS.AI: "What would you like to know about Chakan?
  (1) List of projects [DATA_RETRIEVAL]
  (2) Market analysis [INSIGHT]
  (3) Investment recommendation [STRATEGIC]"
```

### 3. **Intent History**
Track common intents per user/session:
```json
{
  "session_intent_profile": {
    "CALCULATION": 45%,  // User prefers calculations
    "INSIGHT": 30%,
    "COMPARISON": 25%
  }
}
```

### 4. **Multi-Turn Intent Continuity**
Remember intent across conversation turns:
```
Turn 1: "Tell me about Chakan" → DATA_RETRIEVAL
Turn 2: "Why is absorption low?" → INSIGHT (infers context: Chakan from Turn 1)
Turn 3: "Compare with Hinjewadi" → COMPARISON (compares Chakan vs Hinjewadi)
```

---

## Summary

✅ **Intent recognition is now AI-driven** - LLM classifies queries before tool selection
✅ **6 intent categories** cover all query types (data, calculation, comparison, insight, strategic, context)
✅ **GraphRAG for insights** - Combines Knowledge Graph + VectorDB for "why" questions
✅ **Deterministic calculations** - Python functions for accuracy (not LLM estimation)
✅ **Strategic optimization** - Layer 3 tools for investment recommendations
✅ **Location intelligence** - Google APIs for proximity, maps, weather
✅ **Transparent tool routing** - All tool calls logged with reasoning

**Architecture:** LLM Intent Recognition → Tool Selection → Sequential Execution → LLM Synthesis
