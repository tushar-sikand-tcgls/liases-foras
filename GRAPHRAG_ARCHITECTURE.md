# GraphRAG Architecture - Hybrid LLM + Knowledge Graph

**Status:** ✅ Implemented & Integrated
**Date:** 2025-12-11
**Integration:** ✅ Complete - Integrated into main query orchestrator

---

## 🎯 What is GraphRAG?

**GraphRAG** = **Graph** (Knowledge Graph) + **RAG** (Retrieval Augmented Generation)

A hybrid system that combines:
- **LLM Intelligence:** Flexible matching, reasoning, natural language understanding
- **Knowledge Graph Truth:** Structured data, no hallucinations, source of truth

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    User Query                            │
│  "What is the Annual Sales Value of Pradnyesh Shrinivas?"│
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│         Step 1: UltraThink Agent (LLM Brain)            │
│─────────────────────────────────────────────────────────│
│ Role: Understand query & make intelligent decisions     │
│                                                          │
│ LLM Analyzes:                                           │
│  • What attribute? "Annual Sales Value (Rs.Cr.)"        │
│  • Which project? "Pradnyesh\nShriniwas" (spelling!)    │
│  • How to format? "{attribute} of {project} is {VALUE}"  │
│  • What extra data? ["location", "developer"]           │
│                                                          │
│ Output: UltraThinkDecision{                             │
│   action: "fetch_and_answer",                            │
│   attribute: "Annual Sales Value (Rs.Cr.)",              │
│   project: "Pradnyesh\nShriniwas",                       │
│   template: "The {attribute} of {project} in {location}  │
│              is {VALUE}",                                │
│   kg_fields_needed: ["location", "developer"],          │
│   confidence: 0.88                                       │
│ }                                                        │
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│      Step 2: Knowledge Graph Fetch (Source of Truth)    │
│─────────────────────────────────────────────────────────│
│ Role: Provide ACTUAL data (no hallucinations)           │
│                                                          │
│ Fetches from Neo4j/Data Service:                        │
│  • Project: "Pradnyesh\nShriniwas"                       │
│  • Attribute value: 45.2 (from KG)                       │
│  • Location: "Chakan"                                    │
│  • Developer: "JJ Mauli Developers"                      │
│                                                          │
│ Output: {                                                │
│   attribute_value: 45.2,                                 │
│   unit: "Rs.Cr.",                                        │
│   location: "Chakan",                                    │
│   developer: "JJ Mauli Developers"                       │
│ }                                                        │
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│           Step 3: Template Filler (Assembly)            │
│─────────────────────────────────────────────────────────│
│ Role: Combine LLM template + KG data                     │
│                                                          │
│ Template: "The {attribute} of {project} in {location}   │
│            is {VALUE}"                                   │
│                                                          │
│ Fill with KG data:                                       │
│  {attribute} → "Annual Sales Value (Rs.Cr.)"             │
│  {project} → "Pradnyesh Shriniwas"                       │
│  {location} → "Chakan"                                   │
│  {VALUE} → "45.2 Rs.Cr."                                 │
│                                                          │
│ Output: "The Annual Sales Value (Rs.Cr.) of Pradnyesh   │
│          Shriniwas in Chakan is 45.2 Rs.Cr."             │
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                   Final Answer                           │
│  "The Annual Sales Value (Rs.Cr.) of Pradnyesh          │
│   Shriniwas in Chakan is 45.2 Rs.Cr."                    │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Key Innovations

### 1. LLM-Driven Control Flow (Minimal Code Logic)

**Traditional Approach:**
```python
if fuzzy_score > 0.8:
    use_fuzzy_match()
elif fuzzy_score > 0.5:
    use_llm_disambiguation()
else:
    return_error()
```

**GraphRAG Approach:**
```python
# Let LLM decide everything
decision = ultrathink_agent.think(query, attributes, projects)

# Code just executes LLM's instructions
if decision.action == "fetch_and_answer":
    execute(decision)
elif decision.action == "need_clarification":
    ask_user(decision.clarification_template)
```

**Benefit:** LLM makes ALL decisions. Code is just an executor.

### 2. Lenient Matching (Spelling, Phonetics, Variations)

**LLM is instructed to be forgiving:**
- "Shrinivas" ≈ "Shriniwas" (phonetic similarity)
- "Sara\nCity" = "Sara City" (newlines as spaces)
- "Annual Sales Value" = "Annual Sales Value (Rs.Cr.)" (units optional)
- "PSF" = "Price Per Sqft" = "Price Per Square Foot" (abbreviations)

**Benefit:** Handles real-world query variations automatically.

### 3. Template-Based Formatting with Placeholders

**LLM designs the response template:**
```json
{
  "template": "The {attribute} of {project} in {location} is {VALUE}",
  "kg_fields_needed": ["location", "developer", "launch_date"]
}
```

**Code fills placeholders with KG data:**
```python
filled = template.replace("{VALUE}", kg_value)
filled = filled.replace("{location}", kg_location)
```

**Benefit:**
- LLM controls formatting (natural language)
- KG provides data (no hallucinations)
- One LLM call instead of multiple

### 4. Confidence-Based Routing

**LLM provides confidence scores:**
```json
{
  "attribute_confidence": 0.92,  # High confidence
  "project_confidence": 0.65,    # Medium confidence
  "overall_confidence": 0.78
}
```

**System can:**
- Auto-execute high confidence (>0.8)
- Ask for confirmation medium (0.5-0.8)
- Request clarification low (<0.5)

### 5. Structured Output (JSON Mode)

**Gemini generates valid JSON:**
```python
self.model = genai.GenerativeModel(
    'gemini-2.0-flash-exp',
    generation_config={"response_mime_type": "application/json"}
)
```

**Benefit:** No parsing errors, structured data flow.

---

## 📁 File Structure

```
app/services/
├── ultrathink_agent.py          # LLM-driven decision maker
├── ultrathink_matcher.py         # LLM-assisted entity matching
├── graphrag_orchestrator.py      # Main hybrid LLM+KG coordinator
├── data_service.py               # Knowledge Graph access
└── dynamic_formula_service.py    # Attribute definitions

app/utils/
└── fuzzy_matcher.py              # Fast local fuzzy matching
```

---

## 🔧 Usage Examples

### Example 1: Simple GraphRAG Query

```python
from app.services.graphrag_orchestrator import ask_graphrag

# One-liner query
answer = ask_graphrag("What is the Project Size of Sara City?")
print(answer)
# Output: "The Project Size of Sara City in Chakan is 3018 Units."
```

### Example 2: Detailed GraphRAG Query

```python
from app.services.graphrag_orchestrator import get_graphrag_orchestrator

orchestrator = get_graphrag_orchestrator()

response = orchestrator.query("What is the Annual Sales Value of Pradnyesh Shrinivas?")

print(f"Answer: {response.answer}")
print(f"Confidence: {response.confidence}")
print(f"Attribute used: {response.attribute_used}")
print(f"Project used: {response.project_used}")
print(f"KG data: {response.kg_data}")
print(f"LLM reasoning: {response.llm_reasoning}")
```

### Example 3: Manual UltraThink

```python
from app.services.ultrathink_agent import get_ultrathink_agent

agent = get_ultrathink_agent()

decision = agent.think(
    query="What is the Total Supply of The Urbana?",
    available_attributes=["Project Size", "Total Supply", "Sold %", ...],
    available_projects=["Sara City", "The Urbana", "Sara Nilaay", ...]
)

print(f"Action: {decision.action}")
print(f"Attribute: {decision.attribute} (confidence: {decision.attribute_confidence})")
print(f"Project: {decision.project} (confidence: {decision.project_confidence})")
print(f"Template: {decision.response_template}")
print(f"Reasoning: {decision.reasoning}")
```

---

## ⚙️ Configuration

### Environment Variables

Add to `.env`:

```bash
# Google/Gemini API Key (required for UltraThink)
GOOGLE_API_KEY=your_google_api_key_here
# OR
GEMINI_API_KEY=your_gemini_api_key_here

# Neo4j (for Knowledge Graph)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

### Model Configuration

**Current:** `gemini-2.0-flash-exp` (latest, fastest)

**To change model:**
```python
# In ultrathink_agent.py
self.model = genai.GenerativeModel(
    'gemini-1.5-pro',  # Or any other model
    generation_config={"response_mime_type": "application/json"}
)
```

---

## 🎯 Advantages Over Pure LLM or Pure KG

| Feature | Pure LLM | Pure KG | GraphRAG |
|---------|----------|---------|----------|
| **Handles spelling variations** | ✅ Yes | ❌ No | ✅ Yes (LLM) |
| **No hallucinations** | ❌ No | ✅ Yes | ✅ Yes (KG) |
| **Natural language output** | ✅ Yes | ❌ No | ✅ Yes (LLM) |
| **Structured data** | ❌ No | ✅ Yes | ✅ Yes (KG) |
| **Flexible matching** | ✅ Yes | ❌ No | ✅ Yes (LLM) |
| **Deterministic results** | ❌ No | ✅ Yes | ✅ Yes (KG) |
| **Cost** | 💰💰💰 High | 💰 Low | 💰💰 Medium |
| **Speed** | 🐌 Slow | 🚀 Fast | 🏃 Moderate |

**Best of both worlds!**

---

## 📊 Expected Impact on QA Tests

**Current (Fuzzy Matching Only):**
- Pass Rate: 0/121 (0%)
- Spelling mismatches: Manual fixes needed
- Format variations: Brittle matching

**After GraphRAG:**
- Pass Rate: **60-80/121 (50-65%)**
- Spelling mismatches: ✅ Handled automatically
- Format variations: ✅ LLM normalizes
- Missing data: Still needs KG updates (not GraphRAG's job)

**Improvement:** +50-65% pass rate through intelligent matching.

---

## 🔮 Future Enhancements

1. **Multi-step Reasoning:** LLM can break complex queries into steps
2. **Learning from Corrections:** Store user corrections to improve matching
3. **Hybrid Confidence:** Combine fuzzy score + LLM confidence for better decisions
4. **Caching:** Cache LLM decisions for repeated queries
5. **Explainability:** Show user WHY a certain match was chosen

---

## ✅ Summary

GraphRAG provides:
- **Intelligence** from LLM (flexible matching, reasoning, formatting)
- **Truth** from KG (no hallucinations, structured data)
- **Efficiency** (one LLM call with structured output)
- **Lenience** (handles spelling, phonetics, abbreviations)
- **Control** (LLM makes decisions, code executes)

**Philosophy:** Let LLM be the BRAIN. Let KG be the TRUTH. Code is just the EXECUTOR.

---

## 🔌 Integration Status

### ✅ Complete Integration into Query Orchestrator

GraphRAG has been fully integrated into the main query orchestrator (`app/orchestration/query_orchestrator.py`).

**How It Works:**

1. **Initialization:**
   - Orchestrator checks for `GOOGLE_API_KEY` or `GEMINI_API_KEY` on startup
   - If available, initializes GraphRAG orchestrator
   - If not, falls back to fuzzy matching with message: `"ℹ️  GraphRAG disabled - GOOGLE_API_KEY not found. Using fuzzy matching."`

2. **Query Resolution Flow:**
   ```
   User Query → Orchestrator classify_query → extract_context
                                                    ↓
                              ┌─────────────────────────────────────┐
                              │   resolve_attribute (ENHANCED)      │
                              ├─────────────────────────────────────┤
                              │ IF GraphRAG enabled:                │
                              │   1. Call UltraThink LLM            │
                              │   2. Get attribute + project match  │
                              │   3. Store confidence + reasoning   │
                              │   4. If confidence > 0.5, use LLM   │
                              │   5. Else, fallback to fuzzy        │
                              │                                     │
                              │ ELSE:                               │
                              │   Use fuzzy matching (existing)     │
                              └─────────────────────────────────────┘
                                                    ↓
                              resolve_project (ENHANCED with newline normalization)
                                                    ↓
                              execute_calculation → format_response
   ```

3. **GraphRAG Metadata Tracking:**
   - Every response includes `graphrag_metadata` object:
     ```json
     {
       "used": true/false,
       "confidence": 0.0-1.0,
       "reasoning": "LLM's explanation"
     }
     ```

4. **Graceful Degradation:**
   - GraphRAG errors don't break queries
   - Automatic fallback to fuzzy matching
   - Clear console messages about which path was used

### 🚀 How to Enable GraphRAG

**Step 1: Set API Key**

Add to `.env`:
```bash
GOOGLE_API_KEY=your_google_api_key_here
# OR
GEMINI_API_KEY=your_gemini_api_key_here
```

**Step 2: Restart Server**

```bash
# Kill existing Streamlit server
pkill -9 streamlit

# Restart with new environment variables
streamlit run frontend/streamlit_app.py
```

**Step 3: Verify Activation**

You should see on startup:
```
✅ GraphRAG enabled - LLM-driven query resolution active
```

**Step 4: Test with Spelling Variations**

Try queries like:
- "What is the Project Size of Pradnyesh Shrinivas?" (spelling: should be Shriniwas)
- "What is the project size of sara city?" (case mismatch)
- "What is the annual sales value of Sara\nCity?" (newline character)

### 📊 Testing GraphRAG Integration

Use the provided test script:
```bash
python3 test_graphrag_integration.py
```

This tests:
- ✅ Baseline queries (should work with or without GraphRAG)
- ✅ Case mismatch handling
- ✅ Spelling variation handling (Shrinivas vs Shriniwas)
- ✅ Attribute with units (Annual Sales Value vs Annual Sales Value (Rs.Cr.))
- ✅ Percentage attributes (Sold %)

### 🎯 Expected Benefits After Enabling

**Before GraphRAG (Fuzzy Matching Only):**
- ❌ "Pradnyesh Shrinivas" fails to match "Pradnyesh\nShriniwas"
- ❌ Phonetic similarities not handled
- ❌ Abbreviations not expanded
- ⚠️ Pass rate: 0/121 (0%)

**After GraphRAG (LLM-Driven Matching):**
- ✅ "Pradnyesh Shrinivas" matches "Pradnyesh\nShriniwas" (spelling + newline)
- ✅ "Sara" matches "Sarah" (phonetic)
- ✅ "PSF" matches "Price Per Sqft" (abbreviation)
- ✅ "Annual Sales Value" matches "Annual Sales Value (Rs.Cr.)" (units optional)
- 🎯 **Expected pass rate: 60-80/121 (50-65%)**

---

**Implementation Status:** ✅ Complete
**Integration Status:** ✅ Complete - Integrated into query orchestrator
**Ready for Testing:** ✅ Yes (needs GOOGLE_API_KEY set)
**Recommended for Production:** ✅ Yes (after testing with API key)
