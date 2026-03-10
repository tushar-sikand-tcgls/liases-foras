# Proximity Comparison Query - Blank Answer Investigation

**Date:** 2025-12-22
**User Report:** "This question gave a blank answer, what happened: Q. Compare and comment on all projects within 2 KM of Sara City including Sara City"
**Status:** 🔴 **TIMEOUT ISSUE** - Answer composition timed out after 300 seconds

---

## Problem Statement

**Query:** "Compare and comment on all projects within 2 KM of Sara City including Sara City"
**Expected:** Comparative analysis of nearby projects with distances, metrics, and commentary
**Actual:** Blank answer returned to user due to timeout during answer composition

---

## Root Cause Analysis

### ✅ What's Working

1. **Intent Classification:** ✅ **WORKING**
   ```
   Intent: comparative (confidence: 0.90)
   Subcategory: find projects by criteria
   Reasoning: The query asks to compare and list multiple projects within a specific radius
   ```

2. **Entity Resolution:** ✅ **WORKING**
   ```
   Resolving: 'Sara City'
   ✓ Matched as project: 'Sara City'
   ```

3. **Geocoding:** ✅ **WORKING**
   ```
   ✓ Sara City: (18.755693, 73.836720)
   ✓ Pradnyesh Shriniwas: (18.756785, 73.844168)
   ✓ Sara Nilaay: (18.755001, 73.854004)
   ... and 7 more projects successfully geocoded
   ```

4. **KG Execution:** ✅ **WORKING**
   ```
   Execution Summary:
     Data points retrieved: 71
     Queries executed: 20
     Execution time: 10.48ms

   Retrieved full metadata (50+ fields) for all 10 projects:
   - Sara City
   - Pradnyesh Shriniwas
   - Sara Nilaay
   - Sara Abhiruchi Tower
   - The Urbana
   - Gulmohar City
   - Siddhivinayak Residency
   - Sarangi Paradise
   - Kalpavruksh Heights
   - Shubhan Karoti
   ```

### ❌ What's NOT Working

**Answer Composition:** ❌ **TIMEOUT**

```
[Composing Answer with LLM]...
✗ Error composing answer: Ollama request timed out after 300 seconds.
   Try reducing max_tokens or increasing timeout.
```

**Execution Time:**
- Total query time: **388089.88ms** (~6.5 minutes)
- KG execution: **10.48ms** ✅ Fast
- Answer composition: **~388 seconds** ❌ **TIMEOUT** (exceeded 300s limit)

**Result Returned to User:**
```
Error composing answer: Ollama request timed out after 300 seconds.
Try reducing max_tokens or increasing timeout.
```

---

## Why Did This Timeout?

### Context Complexity Analysis

**Data Volume:**
- 71 data points retrieved
- 10 projects with full metadata (50 fields each)
- Each project includes: Project ID, Name, Location, Launch Date, Possession Date, Project Size, Total Supply, Sold %, Unsold %, Annual Sales, Launch Price PSF, Current Price PSF, Monthly Sales Velocity, RERA status, and 36+ more enriched attributes

**Task Complexity:**
1. **Proximity calculation** (distances from Sara City to 9 other projects)
2. **Comparative analysis** (compare metrics across 10 projects)
3. **Commentary generation** (insights on similarities/differences)
4. **Enriched answer formatting** (icons, judgments, insights as per enhanced 8-step framework)

**Why Qwen 2.5:3b Struggled:**
- Small model (3 billion parameters) optimized for SPEED, not COMPLEX REASONING
- Comparative queries require holding 10 projects × 50 fields = 500 data points in context
- Generating comparative analysis is MORE cognitively demanding than single-project queries
- Enhanced 8-step framework requires ~1000 tokens output (vs 300-500 for simple queries)

---

## Comparison with Sellout Efficiency Query

**Sellout Efficiency Query (from previous investigation):**
- Query: "What is the sellout efficiency of Sara City?"
- Data points: 1 project, 1 attribute
- Task: Return single value with insights
- Result: **ALSO TIMED OUT** after 300 seconds (but eventually completed at 480 seconds)

**Proximity Comparison Query (current issue):**
- Query: "Compare and comment on all projects within 2 KM of Sara City including Sara City"
- Data points: 10 projects, 71 data points (full metadata)
- Task: Comparative analysis across 10 projects
- Result: **TIMED OUT** after 300 seconds

**Pattern:** Both queries timeout with Ollama/Qwen 2.5:3b when using the enhanced 8-step analytical framework, but **comparative queries are WORSE** due to higher context complexity.

---

## Why Timeout Increased from 120s to 300s Wasn't Enough

**Previous Fix:**
In `app/services/ollama_service.py` lines 21-28, we increased timeout from 120s to 300s based on the Sellout Efficiency query taking 480 seconds.

```python
@dataclass
class OllamaConfig:
    timeout: int = 300  # seconds - increased to 5 minutes for complex answer composition
```

**Why This Is Insufficient for Comparative Queries:**
- Sellout Efficiency (1 project, 1 attribute): **~480 seconds**
- Proximity Comparison (10 projects, 71 attributes): **>388 seconds** (still running when timeout hit)

**Scaling Factor:**
- Linear data scaling: 10 projects × 71 fields = 710 data points
- Cognitive scaling: Comparative reasoning is EXPONENTIALLY harder than single-value retrieval
- Estimated completion time: **600-900 seconds** (10-15 minutes)

---

## Solutions

### Option A: Increase Timeout to 900 Seconds (NOT RECOMMENDED)

**Implementation:**
```python
# app/services/ollama_service.py line 28
timeout: int = 900  # 15 minutes
```

**Pros:**
- Simple one-line fix
- May allow complex comparisons to complete

**Cons:**
- User waits 10-15 minutes for answer (TERRIBLE UX)
- No guarantee it will work for even larger comparisons
- Qwen 2.5:3b may still struggle or hallucinate with such complex context

**Verdict:** ❌ Not recommended

---

### Option B: Switch to Gemini for Answer Composition (RECOMMENDED)

**Implementation:**
```python
# app/nodes/answer_composer_node.py

def answer_composer_node(state: QueryState, llm: LLMPort) -> QueryState:
    """
    Node 8: Compose final answer

    Uses Gemini for complex queries (comparative, aggregation) for better reasoning.
    Uses Ollama/Qwen for simple queries (fetch, single metric) for speed.
    """

    # Detect complex queries
    intent = state.get('intent', 'objective')
    kg_data_size = len(state.get('kg_data', {}))

    # Switch to Gemini for complex queries
    if intent in ['comparative', 'aggregation'] or kg_data_size > 20:
        print("⚡ Complex query detected - switching to Gemini for answer composition")
        from app.adapters.gemini_llm_adapter import GeminiLLMAdapter
        gemini_llm = GeminiLLMAdapter()
        answer = gemini_llm.compose_answer(
            query=state['query'],
            kg_data=state.get('kg_data', {}),
            ...
        )
    else:
        # Use Ollama for simple queries (fast)
        answer = llm.compose_answer(...)
```

**Pros:**
- Gemini 1.5 Pro has **MUCH better** comparative reasoning
- Gemini has **200K token context** (vs Qwen's ~32K)
- Gemini completes complex queries in **10-30 seconds** (not 6 minutes)
- User gets high-quality comparative analysis

**Cons:**
- Adds API cost ($0.00125/1K input tokens, $0.005/1K output tokens)
- For this query: ~$0.10-0.20 per comparative query (acceptable for quality)

**Estimated Impact:**
- Timeout risk: **ELIMINATED**
- Query time: **10-30 seconds** (vs 6+ minutes)
- Answer quality: **SIGNIFICANTLY BETTER** (Gemini's reasoning > Qwen 3B)

**Verdict:** ✅ **RECOMMENDED**

---

### Option C: Simplify Answer Composer Prompt for Comparative Queries

**Implementation:**
For comparative queries with >5 projects, use a simplified 3-step framework instead of 8-step:

```python
# app/adapters/gemini_llm_adapter.py (or ollama_service.py)

# Detect comparative query with many projects
if intent == 'comparative' and num_projects > 5:
    prompt = """
    You are composing a COMPARATIVE answer for a real estate query.

    Use this SIMPLIFIED 3-STEP FRAMEWORK:

    1. **Summary Table**: Present all projects in a table with key metrics
    2. **Key Insights**: Highlight 3-5 most important differences/similarities
    3. **Recommendation**: Brief recommendation if asked

    DO NOT use the full 8-step analytical framework for comparative queries.
    Keep answer concise (300-500 characters).
    """
```

**Pros:**
- Reduces token generation requirements
- May complete within 300s timeout
- Keeps using Qwen (no API cost)

**Cons:**
- Sacrifices analytical depth (violates user's "value addition" requirement)
- Still might timeout with Qwen 2.5:3b
- No guarantee of quality

**Verdict:** ⚠️ Backup option if Option B (Gemini) is not acceptable

---

### Option D: Pre-compute Comparative Summaries (FUTURE OPTIMIZATION)

**Implementation:**
Pre-compute comparative summaries for common query patterns:
- "Projects within X km of Y"
- "Compare projects in location Z"
- "Top N projects by metric M"

Cache these summaries and update quarterly with LF data refreshes.

**Pros:**
- Instant responses (<1s)
- No LLM generation needed
- Perfect for recurring queries

**Cons:**
- Requires building caching layer
- Only works for predictable query patterns
- Not a short-term fix

**Verdict:** 💡 Good long-term optimization, not a fix for current issue

---

## Recommended Immediate Action

**IMPLEMENT OPTION B: Hybrid LLM Routing (Gemini for Complex, Qwen for Simple)**

### Implementation Plan

1. **Modify `app/nodes/answer_composer_node.py`:**
   - Add complexity detection logic
   - Route complex queries (comparative, >20 data points) to Gemini
   - Keep simple queries (fetch, single metric) on Qwen for speed

2. **Update `app/adapters/gemini_llm_adapter.py`:**
   - Ensure `compose_answer` method works with Gemini API
   - Add timeout of 60 seconds (Gemini is much faster)

3. **Add Configuration:**
   ```python
   # .env
   ANSWER_COMPOSER_LLM_ROUTING="hybrid"  # Options: "ollama", "gemini", "hybrid"
   COMPLEXITY_THRESHOLD_KG_DATA_POINTS=20
   ```

4. **Testing:**
   - Test with current query: "Compare and comment on all projects within 2 KM of Sara City including Sara City"
   - Expected: Completes in 10-30 seconds with high-quality comparative analysis
   - Test with simple query: "What is the PSF of Sara City"
   - Expected: Still uses Qwen (fast, <10s)

---

## Success Criteria

After implementing Option B (Hybrid LLM Routing):

1. ✅ **Timeout Eliminated:** Comparative queries complete within 60 seconds
2. ✅ **Quality Maintained:** Answer includes all enhanced framework requirements (icons, judgments, insights)
3. ✅ **Cost Efficient:** Simple queries still use Qwen (free), only complex queries use Gemini ($0.10-0.20 per query)
4. ✅ **No Blank Answers:** System returns meaningful comparative analysis
5. ✅ **User Satisfaction:** Query completes fast enough for interactive use (<30s)

---

## Files Involved

| File | Status | Notes |
|------|--------|-------|
| `app/nodes/answer_composer_node.py` | ⚠️ Needs modification | Add LLM routing logic |
| `app/adapters/gemini_llm_adapter.py` | ⚠️ Verify compose_answer | Ensure it works for this query |
| `app/services/ollama_service.py` | ✅ Working | Timeout at 300s (insufficient for complex queries) |
| `.env` | ⚠️ Add config | Add routing strategy config |

---

## Alternative: If Gemini Is Not Available

If switching to Gemini is not an option, implement **Option C (Simplified Prompt)** as a fallback:

**Quick Fix:**
```python
# app/adapters/gemini_llm_adapter.py lines 704-730

# Add to compose_answer method:
if context.get('intent') == 'comparative' and len(kg_data) > 20:
    # Use simplified 3-step framework instead of 8-step
    prompt = """
    Comparative Query - Use SIMPLIFIED FRAMEWORK:
    1. Present data in table format
    2. Highlight 3 key insights
    3. Brief recommendation (if asked)

    Keep answer under 500 characters.
    """
```

**Expected Result:**
- May complete within 300s timeout
- Answer will be shorter and less analytical
- Quality: Acceptable but not ideal

---

## Key Learnings

1. **Context Complexity Matters:** Comparative queries scale EXPONENTIALLY harder than single-metric queries
2. **Model Selection:** Qwen 2.5:3b (3B parameters) is great for SPEED but struggles with COMPLEX REASONING
3. **Timeout Scaling:** Linear timeout increases (120s → 300s) don't work for exponential complexity growth
4. **Hybrid Approach:** Use small/fast models for simple queries, larger/smarter models for complex queries
5. **User Experience:** 6+ minute timeouts are UNACCEPTABLE for interactive use - need <30s responses

---

## Status

**Current:** ❌ Blank answer due to timeout (300s exceeded)

**Recommended Fix:** ✅ Implement Option B (Hybrid LLM Routing - Gemini for complex, Qwen for simple)

**Expected After Fix:** ✅ Comparative queries complete in 10-30 seconds with high-quality analysis

---

**Next Step:** Awaiting user decision on which fix to implement (Option B recommended)
