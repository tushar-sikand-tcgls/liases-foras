# ATLAS Orchestration Architecture

## Core Principle

**Intent Recognition → Workflow Selection → LangChain Orchestration → LLM-Guided Tool Stitching**

The LLM doesn't just generate the final answer - it **actively participates in orchestration**, deciding which tools to call, interpreting intermediate results, and determining the next step.

---

## Architecture Flow

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. USER QUERY                                                     │
│ "Why is absorption low in Chakan?"                                │
└──────────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────────┐
│ 2. INTENT RECOGNITION (LLM Classifier)                            │
│                                                                    │
│ LLM analyzes signals:                                             │
│ - "Why" → INSIGHT intent (needs GraphRAG)                         │
│ - "absorption" → Layer 1 metric                                   │
│ - "Chakan" → Region context                                       │
│                                                                    │
│ Classification: INTENT = INSIGHT                                  │
│ Workflow Selected: GraphRAG_Insight_Workflow                      │
└──────────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────────┐
│ 3. WORKFLOW EXECUTION (LangChain + LLM Orchestration)             │
│                                                                    │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ Step 1: LLM decides first tool                                │ │
│ │ "I need Layer 0 data for Chakan to calculate absorption"     │ │
│ │ Tool Call: get_region_layer0_data("Chakan")                  │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                          ↓                                         │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ Tool Result: 8 projects with U, C, T, L² dimensions          │ │
│ │ LLM interprets: "8 projects found, need to calculate AR"     │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                          ↓                                         │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ Step 2: LLM decides next tool                                 │ │
│ │ "Now calculate Layer 1 metrics from Layer 0 data"            │ │
│ │ Tool Call: calculate_layer1_metrics(layer0_json)             │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                          ↓                                         │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ Tool Result: PSF, AR, velocity for all 8 projects            │ │
│ │ LLM interprets: "AR is 2.8%/month, need market context"      │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                          ↓                                         │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ Step 3: LLM decides next tool                                 │ │
│ │ "Search VectorDB for factors affecting Chakan absorption"    │ │
│ │ Tool Call: search_market_insights("Chakan absorption")       │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                          ↓                                         │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ Tool Result: VectorDB insights on infrastructure, distance   │ │
│ │ LLM interprets: "Now I have all data to generate insight"    │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                          ↓                                         │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ Step 4: LLM synthesizes (NO MORE TOOLS)                       │ │
│ │ Generates: ANALYSIS + INSIGHTS + RECOMMENDATIONS             │ │
│ └──────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────────┐
│ 4. STRUCTURED OUTPUT                                              │
│ - Part 1: ANALYSIS (What data shows: AR 2.8% vs 3.2% market)     │
│ - Part 2: INSIGHTS (Why: Distance, no metro, industrial focus)   │
│ - Part 3: RECOMMENDATIONS (What to do: Hold until 2027 metro)    │
└──────────────────────────────────────────────────────────────────┘
```

---

## Key Components

### 1. Intent Recognition (LLM-Powered)

**Not rule-based pattern matching - LLM actively classifies intent:**

```python
# Embedded in ATLAS system prompt:
"Before selecting tools, classify the user's query intent:
- DATA_RETRIEVAL → Knowledge Graph
- CALCULATION → Python Calculators
- COMPARISON → KG + Calculators
- INSIGHT → GraphRAG (KG + VectorDB + LLM synthesis)
- STRATEGIC → Layer 3 Optimization
- CONTEXT_ENRICHMENT → Google APIs"
```

**LLM considers:**
- Query signals ("why", "calculate", "compare", "should I")
- Entity context (region, project, metric)
- User's underlying question (not just keywords)

**Example:**
- Query: "Tell me about Chakan"
- Simple pattern matcher: DATA_RETRIEVAL
- **ATLAS LLM**: DATA_RETRIEVAL + INSIGHT (user wants analysis, not just data)

### 2. Workflow Selection

**Each intent has a workflow pattern:**

| Intent | Workflow Pattern | Tools Used | LLM Role |
|--------|------------------|------------|----------|
| **DATA_RETRIEVAL** | Single-tool → KG query | get_region_layer0_data | Interpret + contextualize data |
| **CALCULATION** | KG → Calculator → Interpret | get_region_layer0_data + calculate_layer1_metrics | Validate + explain calculation |
| **COMPARISON** | KG (multi) → Calculator → Compare | get_region_layer0_data (multiple) + calculate_layer1_metrics | Synthesize comparison + insights |
| **INSIGHT (GraphRAG)** | KG → Calculator → VectorDB → Synthesize | get_region_layer0_data + calculate_layer1_metrics + search_market_insights | Root cause analysis + recommendations |
| **STRATEGIC** | Full pipeline + Optimization | All tools + optimize_product_mix | Strategic guidance + risk analysis |
| **CONTEXT_ENRICHMENT** | Google APIs | get_location_context | Enrich with location intelligence |

### 3. LangChain Orchestration

**LangChain provides the framework, LLM provides the intelligence:**

```python
# LangChain's role:
1. Tool binding: llm_with_tools = llm.bind_tools(tools)
2. Message management: Maintains conversation history
3. Tool execution: Invokes Python functions when LLM requests
4. Result formatting: Converts tool output to ToolMessage

# LLM's role:
1. Decides which tool to call next
2. Interprets tool results
3. Determines if more tools needed
4. Synthesizes final answer when done
```

**Iterative Loop:**
```python
while iteration < max_iterations:
    # LLM decides what to do next
    response = llm_with_tools.invoke(messages)

    if response.tool_calls:
        # LLM wants to use a tool
        results = execute_tool_calls(response.tool_calls)
        messages.append(tool_results)  # Feed back to LLM
        continue  # LLM interprets and decides next step
    else:
        # LLM has enough info, generates final answer
        return response.content
```

### 4. LLM Assistance Throughout

**LLM is NOT just final synthesizer - helps at every step:**

#### A. Tool Selection
```
LLM: "I need Layer 0 data first to understand project dimensions"
Action: Calls get_region_layer0_data("Chakan")
```

#### B. Result Interpretation
```
Tool Result: {"projects": [{"total_units": null, "current_price_psf": 3996}, ...]}
LLM: "I see 8 projects, but many have null values for total_units.
      I'll focus on PSF data which is complete."
```

#### C. Next Step Decision
```
LLM: "I have PSF data but need to understand absorption.
      However, sold_units is null for most projects.
      Let me search VectorDB for absorption insights instead."
Action: Calls search_market_insights("Chakan absorption trends")
```

#### D. Data Stitching
```
Tool 1 Result: PSF average ₹3,645
Tool 2 Result: VectorDB says "Industrial area, workforce housing"
Tool 3 Result: VectorDB says "Metro planned 2027"

LLM Stitches Together:
"Low PSF (₹3,645) is consistent with industrial/workforce market.
 Current constraints: no metro. Future catalyst: 2027 metro extension.
 RECOMMENDATION: Hold until infrastructure matures."
```

#### E. Final Synthesis
```
LLM generates mandatory 3-part output:
1. ANALYSIS: What data shows (with numbers + benchmarks)
2. INSIGHTS: Why (root causes from VectorDB + logic)
3. RECOMMENDATIONS: What to do (strategic guidance)
```

---

## Workflow Examples

### Workflow 1: INSIGHT (GraphRAG) - "Why is absorption low?"

**Intent Classification:**
```
Signal: "why" → INSIGHT intent
Workflow: GraphRAG_Insight_Workflow
```

**Orchestration Steps:**
```
Step 1: LLM → "Need project data"
        Tool: get_region_layer0_data("Chakan")
        Result: 8 projects with dimensions

Step 2: LLM → "Calculate absorption from Layer 0"
        Tool: calculate_layer1_metrics(layer0_json)
        Result: AR = 2.8%/month

Step 3: LLM → "Need market context to explain why"
        Tool: search_market_insights("Chakan absorption factors")
        Result: "Distance to amenities, no metro, industrial focus"

Step 4: LLM → "I have enough data to answer"
        Action: Synthesize ANALYSIS + INSIGHTS + RECOMMENDATIONS
        Output: Structured JSON with 3-part response
```

**LLM's Stitching Logic:**
- Connects AR=2.8% (calculated) with "no metro" (VectorDB)
- Explains causality: "Low absorption DUE TO infrastructure gaps"
- Projects future: "Metro 2027 will improve absorption"
- Recommends timing: "Hold until 2026-2027"

---

### Workflow 2: COMPARISON - "Compare Chakan vs Hinjewadi"

**Intent Classification:**
```
Signal: "compare" → COMPARISON intent
Workflow: Multi_Region_Comparison_Workflow
```

**Orchestration Steps:**
```
Step 1: LLM → "Need data for both regions"
        Tool: get_region_layer0_data("Chakan")
        Tool: get_region_layer0_data("Hinjewadi")
        Result: Data for both regions

Step 2: LLM → "Calculate metrics for comparison"
        Tool: calculate_layer1_metrics(chakan_data)
        Tool: calculate_layer1_metrics(hinjewadi_data)
        Result: PSF Chakan ₹3,645, PSF Hinjewadi ₹7,200

Step 3: LLM → "Need context for WHY difference exists"
        Tool: search_market_insights("Chakan vs Hinjewadi pricing")
        Result: "IT hub premium, metro access, demographics"

Step 4: LLM → "Generate comparative analysis"
        Action: Synthesize with comparative framing
        Output:
        - ANALYSIS: "Hinjewadi 97% premium over Chakan"
        - INSIGHTS: "IT hub vs industrial, metro vs no metro"
        - RECOMMENDATIONS: "Chakan for value, Hinjewadi for appreciation"
```

**LLM's Stitching Logic:**
- Quantifies difference: 97% premium
- Explains root causes: IT hub, metro, demographics
- Segments recommendations: Developer vs investor perspective

---

### Workflow 3: STRATEGIC - "Should I invest in Chakan?"

**Intent Classification:**
```
Signal: "should I" → STRATEGIC intent
Workflow: Strategic_Recommendation_Workflow
```

**Orchestration Steps:**
```
Step 1: LLM → "Need comprehensive market data"
        Tool: get_region_layer0_data("Chakan")
        Result: 8 projects, various metrics

Step 2: LLM → "Calculate all relevant metrics"
        Tool: calculate_layer1_metrics(layer0_json)
        Result: PSF, AR, velocity, density

Step 3: LLM → "Need market opportunity analysis"
        Tool: search_market_insights("Chakan investment opportunity")
        Result: Infrastructure plans, demographics, growth projections

Step 4: LLM → "Need location context for risks"
        Tool: get_location_context("Chakan, Pune")
        Result: Distance to amenities, connectivity

Step 5: LLM → "Calculate market opportunity score" (if available)
        Tool: market_opportunity_scoring("Chakan")
        Result: OPPS score + breakdown

Step 6: LLM → "Generate strategic recommendation"
        Action: Synthesize investment thesis
        Output:
        - ANALYSIS: Current market state (metrics + benchmarks)
        - INSIGHTS: Growth drivers + risk factors
        - RECOMMENDATIONS: Investment decision + timing + risk mitigation
```

**LLM's Stitching Logic:**
- Risk-Reward: "Low entry price + future infrastructure = opportunity"
- Timing: "2-3 year hold until metro completion"
- Segmentation: "Right for patient investors, not flippers"
- Risk Mitigation: "Diversify across multiple projects, max 30% allocation"

---

## LLM's Multi-Step Reasoning

**Example: "Why is absorption low in Sara City?"**

### Iteration 1: Data Gathering
```
LLM Thought: "I need to know Sara City's absorption rate first"
Tool Call: get_region_layer0_data("Chakan") with filter for Sara City
Result: Sara City: sold_units=null, total_units=null
LLM Interprets: "Sold units data is incomplete, can't calculate AR directly"
```

### Iteration 2: Alternative Approach
```
LLM Thought: "Since I can't calculate AR, I'll search for absorption insights"
Tool Call: search_market_insights("Sara City absorption")
Result: VectorDB has general Chakan insights, not project-specific
LLM Interprets: "Need to provide general Chakan absorption context instead"
```

### Iteration 3: Broader Context
```
LLM Thought: "Get broader Chakan market data for comparison"
Tool Call: get_region_layer0_data("Chakan") [all projects]
Result: 8 projects in Chakan
LLM Interprets: "Can compare Sara City against Chakan average"
```

### Iteration 4: Market Intelligence
```
LLM Thought: "Need market factors affecting Chakan absorption"
Tool Call: search_market_insights("Chakan market factors")
Result: "Industrial area, no metro, distance to IT hubs"
LLM Interprets: "These factors likely affect Sara City too"
```

### Iteration 5: Final Synthesis
```
LLM Thought: "I have enough context to answer, even without exact AR"
Action: Generate response:
- ANALYSIS: "Sara City is in Chakan, which averages 2.8%/month absorption"
- INSIGHTS: "Low absorption driven by: (1) Industrial location, (2) No metro"
- RECOMMENDATIONS: "Monitor post-2027 metro extension for improvement"
```

**Key Point:** LLM **adapts workflow** when data is incomplete, finding alternative paths to answer the question.

---

## Benefits of LLM-Guided Orchestration

### 1. **Intelligent Tool Selection**
- Not hardcoded rules: "IF 'why' THEN search_market_insights"
- LLM understands context: "User wants root causes, need VectorDB"

### 2. **Dynamic Workflow Adaptation**
- Can skip tools if data insufficient
- Can add extra tools if more context needed
- Handles incomplete data gracefully

### 3. **Result Interpretation**
- Tool returns JSON → LLM extracts meaning
- "8 projects found" → "Enough for statistical analysis"
- "sold_units=null" → "Can't calculate AR, use VectorDB instead"

### 4. **Data Stitching**
- Connects dots across multiple tool results
- PSF (Calculator) + "Industrial area" (VectorDB) = "Value market positioning"

### 5. **Contextual Synthesis**
- Not just concatenating tool outputs
- Weaves narrative: "Because X (VectorDB), we see Y (Calculator), therefore Z (Recommendation)"

### 6. **Mandatory Analytical Output**
- ATLAS enforces 3-part structure
- LLM can't just list data - must analyze, explain, recommend

---

## Comparison: Traditional vs ATLAS

### Traditional Agent (ReAct Pattern):
```
1. Thought: "I need to get project data"
2. Action: get_project_data(project_id)
3. Observation: Returns JSON
4. Thought: "Now I'll calculate PSF"
5. Action: calculate_psf(revenue, area)
6. Observation: Returns PSF value
7. Final Answer: "PSF is ₹4,200"  ← Just the number!
```

### ATLAS (Intent-Driven + Analytical):
```
1. Intent Classification: INSIGHT (user wants WHY, not just WHAT)
2. Workflow Selection: GraphRAG_Insight_Workflow
3. Tool Sequence (LLM-guided):
   - get_region_layer0_data → 8 projects
   - calculate_layer1_metrics → PSF ₹3,645 avg
   - search_market_insights → "Industrial belt, no metro"
4. LLM Synthesis:
   - ANALYSIS: "PSF ₹3,645 is 49% below Pune avg (₹7,200)"
   - INSIGHTS: "Low PSF due to industrial focus + lack of metro"
   - RECOMMENDATIONS: "Value opportunity for patient investors,
                        wait until 2027 metro for price appreciation"
```

**Key Difference:** ATLAS provides **strategic intelligence**, not just data.

---

## Future Enhancements

### 1. Multi-Turn Workflows
```
Turn 1: "Tell me about Chakan"
ATLAS: [Provides analysis + insights]

Turn 2: "Compare with Hinjewadi"
ATLAS: [Remembers Chakan from Turn 1, fetches Hinjewadi, compares]

Turn 3: "Should I invest in Chakan or Hinjewadi?"
ATLAS: [Uses previous analysis, generates investment thesis]
```

### 2. Workflow Learning
Track which workflows work best for which query types:
```
Query: "Why is absorption low?"
Successful Workflow: KG → Calculator → VectorDB (87% user satisfaction)
Failed Workflow: KG → VectorDB (skipped calculator, incomplete answer)
```

### 3. Dynamic Tool Discovery
LLM queries available tools at runtime:
```
LLM: "I need to calculate ROI but don't see a calculate_roi tool"
System: "Available: calculate_irr, calculate_npv"
LLM: "I'll use calculate_npv and explain ROI conceptually"
```

### 4. Parallel Tool Execution
When tools are independent:
```
LLM: "I need data for 3 regions"
System: Executes get_region_layer0_data for all 3 in parallel
LLM: Receives results simultaneously, compares
```

---

## Summary

✅ **Intent Recognition** → LLM classifies query, selects workflow
✅ **Workflow** → Defines tool sequence pattern (not rigid)
✅ **LangChain** → Framework for tool binding + message management
✅ **LLM Orchestration** → Decides tool calls, interprets results, stitches data
✅ **Mandatory Analytical Output** → ANALYSIS + INSIGHTS + RECOMMENDATIONS

**ATLAS is not a chatbot - it's an analytical advisor powered by LLM-guided orchestration.**
