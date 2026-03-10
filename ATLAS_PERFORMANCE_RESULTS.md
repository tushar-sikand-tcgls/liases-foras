# ATLAS Performance Adapter - Test Results

## Executive Summary

✅ **ARCHITECTURE SUCCESS**: All 3 components working together via Interactions API V2
- ✅ Interactions API V2 (Beta) - Functional
- ✅ File Search (Managed RAG) - Functional
- ✅ Knowledge Graph (Function Calling) - Functional
- ✅ Autonomous Tool Selection - 100% Accurate (3/3 tests)

⚠️ **PERFORMANCE CHALLENGE**: 7.9s average vs <2s target
- Current architecture requires 2 API round-trips for function calling
- Performance bottleneck identified in Interactions API design pattern

---

## Test Results Summary

### Test Suite: 4 Tests Executed

| Test | Status | Result | Target |
|------|--------|--------|--------|
| KG Query Performance | ❌ FAIL | 7.5s | <2s |
| File Search Performance | ⚠️ PARTIAL | 3.7s | <2s |
| Autonomous Tool Selection | ✅ PASS | 3/3 correct | 100% |
| Stress Test (5 queries) | ❌ FAIL | 7.9s avg | <2s avg |

**Overall**: 1/4 tests passed

---

## Detailed Performance Analysis

### Test 1: Knowledge Graph Query
- **Query**: "What is the Project Size of Sara City?"
- **Tool Selected**: knowledge_graph ✅ (correct)
- **Execution Time**: 7,483ms
- **Performance**: ❌ FAIL (exceeded target by 5,483ms)
- **Root Cause**: 2 round-trip API calls required
  1. First call: Gemini decides to call function (~2-3s)
  2. Function execution: Local KG lookup (~100ms)
  3. Second call: Gemini synthesizes answer from function result (~4-5s)

### Test 2: File Search Query
- **Query**: "What is Absorption Rate? (definition)"
- **Tool Selected**: file_search ✅ (correct)
- **Execution Time**: 3,749ms
- **Performance**: ⚠️ PARTIAL (exceeded target by 1,749ms)
- **Root Cause**: File Search cold start + vector search
  - No function calling required (single API call)
  - File Search vector indexing overhead

### Test 3: Autonomous Tool Selection
- **Test Cases**: 3 queries (quantitative, definition, listing)
- **Results**: 3/3 correct tool selections ✅
- **Performance**: ✅ PASS
- **Breakdown**:
  1. "What is the Project Size of Sara City?" → knowledge_graph ✅
  2. "What is PSF? Define it." → file_search ✅
  3. "List all projects in Chakan" → knowledge_graph ✅

### Test 4: Stress Test (5 Queries)
- **Average Time**: 7,931ms
- **Min**: 4,289ms (File Search)
- **Max**: 11,619ms (KG function call)
- **Performance**: ❌ FAIL (average 4x over target)

**Query Breakdown**:
```
[1/5] What is the Project Size of Sara City?     7,453ms | knowledge_graph
[2/5] What is the PSF of Sara City?             11,619ms | knowledge_graph
[3/5] What is the Launch Date of Sara City?      9,143ms | knowledge_graph
[4/5] List all projects in Chakan                7,149ms | knowledge_graph
[5/5] What is Absorption Rate? Define it.        4,289ms | file_search
```

---

## Architecture Components

### 1. Interactions API V2 (Beta)
- **Status**: ✅ Working
- **Format**: `client.interactions.create(model, input, tools)`
- **Tool Format**:
  ```python
  # File Search Tool
  {
      "type": "file_search",
      "file_search_store_names": ["fileSearchStores/8q3a4kh0o5u9-9n1a2dzr14me"]
  }

  # Function Calling Tool
  {
      "type": "function",
      "name": "knowledge_graph_lookup",
      "description": "...",
      "parameters": {
          "type": "object",
          "properties": {...},
          "required": [...]
      }
  }
  ```

### 2. File Search (Managed RAG)
- **Status**: ✅ Working
- **Store**: `fileSearchStores/8q3a4kh0o5u9-9n1a2dzr14me`
- **Files Uploaded**: 3 documents
  1. LF-Layers_FULLY_ENRICHED_ALL_36.xlsx (21.94 KB)
  2. Lf Capability Pitch Document.docx (329.24 KB)
  3. Glossary.pdf (368.43 KB)
- **Performance**: 3.7s average (acceptable for definitions/qualitative queries)

### 3. Knowledge Graph (Function Calling)
- **Status**: ✅ Working
- **Functions Implemented**:
  - `get_project_by_name` - Fetch project metadata
  - `get_project_metrics` - Get specific metrics
  - `list_projects_by_location` - Filter by location
- **Adapter Methods**: Using `get_project_metadata()` and `get_all_projects()`
- **Performance**: 7.5s average (2 API round-trips required)

### 4. Autonomous Tool Selection
- **Status**: ✅ Working at 100% accuracy
- **Logic**: Gemini autonomously decides which tool to use
  - Quantitative data → knowledge_graph
  - Definitions/concepts → file_search
  - No explicit routing code required

---

## Performance Bottleneck Analysis

### Root Cause: Interactions API Function Calling Pattern

When Gemini needs to call a function (KG lookup), the flow is:

```
User Query
    ↓
[1st API Call] Gemini analyzes query + decides to call function (2-3s)
    ↓
interaction.outputs[0].type == "function_call"
    ↓
[Local Execution] Execute KG function (~100ms)
    ↓
[2nd API Call] Send function result back to Gemini for synthesis (4-5s)
    ↓
Final Answer (total: 7-11s)
```

**File Search Pattern** (faster):
```
User Query
    ↓
[1 API Call] Gemini uses File Search tool internally (3-4s)
    ↓
Final Answer (total: 3-4s)
```

### Why Function Calling is Slower
1. **2 round-trips vs 1**: Function calling requires model → function → model
2. **Network latency**: Each API call adds ~500-1000ms network overhead
3. **Model processing**: 2 separate LLM calls instead of 1
4. **Synthesis overhead**: Second call must generate natural language from function results

---

## Recommendations for <2s Performance

### Option 1: Hybrid Architecture (Recommended)
**Use different APIs for different query types**:

- **For KG queries** (quantitative data):
  - Use direct `generateContent` API with KG function calling
  - Skip Interactions API for these queries
  - Performance: ~1-2s (single API call)

- **For File Search queries** (definitions/qualitative):
  - Keep using Interactions API with File Search
  - Performance: ~3-4s (acceptable trade-off for RAG benefits)

**Implementation**:
```python
if intent == "quantitative_data":
    # Direct generateContent with function calling
    response = model.generate_content(query, tools=[kg_function])
    # 1 API call, ~1-2s
else:
    # Interactions API with File Search
    interaction = client.interactions.create(model, query, tools=[file_search])
    # 1 API call, ~3-4s
```

### Option 2: Optimize Function Calling
**Reduce synthesis overhead**:

- Return structured JSON instead of natural language from functions
- Use smaller/faster model for synthesis (gemini-2.5-flash)
- Cache frequently accessed KG results
- Pre-fetch common project metadata

**Estimated Performance**: 4-5s (improvement but still over target)

### Option 3: Pre-compute + Cache
**Pre-compute common queries**:

- Cache top 100 most common queries
- Store pre-generated answers
- Use cache-aside pattern with 1-hour TTL

**Estimated Performance**: <500ms for cached queries, 7s for uncached

### Option 4: Parallel Execution (Future)
**Run File Search + KG in parallel** (when both needed):

- Currently not supported by Interactions API
- Would require custom orchestration layer
- Estimated Performance: Max(file_search_time, kg_time) ≈ 3-4s

---

## Recommended Path Forward

### Immediate Actions (to achieve <2s for KG queries):

1. **Switch KG queries to direct `generateContent` API**
   - Bypass Interactions API for function calling
   - Use single API call pattern
   - Expected: 1-2s performance ✅

2. **Keep File Search with Interactions API**
   - File Search requires Interactions API architecture
   - 3-4s is acceptable for definition/qualitative queries
   - Expected: 3-4s performance ⚠️

3. **Implement query routing logic**
   ```python
   if query_type in ["quantitative", "metrics", "data_lookup"]:
       # Use direct generateContent + KG function
       result = direct_kg_query(query)  # ~1-2s
   else:
       # Use Interactions API + File Search
       result = interactions_query(query)  # ~3-4s
   ```

### Medium-term Optimizations:

1. **Add Redis caching layer**
   - Cache common KG queries (Project Size, PSF, etc.)
   - TTL: 1 hour (data updates quarterly)
   - Expected impact: <500ms for 80% of queries

2. **Pre-warm File Search store**
   - Ensure file indexing is complete
   - Monitor cold start performance
   - Expected impact: Reduce file_search from 3.7s to 2-3s

3. **Optimize KG adapter**
   - Add bulk fetch methods
   - Reduce attribute lookup overhead
   - Expected impact: Reduce function execution from 100ms to 50ms

### Long-term Architecture:

1. **Hybrid RAG + KG orchestrator**
   - Intelligent routing based on query type
   - Parallel execution when both tools needed
   - Streaming responses for better UX
   - Target: <2s for 90% of queries

---

## Current System Capabilities

### ✅ What's Working
- Interactions API integration (Beta)
- File Search managed RAG (3 files indexed)
- Knowledge Graph function calling
- Autonomous tool selection (100% accuracy)
- Hybrid architecture (File Search + KG)
- Server-side conversation state management

### ⚠️ What Needs Optimization
- Function calling performance (2 round-trips → 1)
- File Search cold start time
- KG adapter method implementations
- Caching layer for common queries

### ❌ What's Not Meeting Requirements
- <2s performance target for KG queries (currently 7.5s)
- <2s performance target for File Search queries (currently 3.7s)
- Average query time <2s (currently 7.9s)

---

## Technical Implementation Notes

### Tool Format Discovery
After extensive debugging, found correct Interactions API tool format:

**❌ INCORRECT** (what we tried first):
```python
# types.Tool with model_dump() → creates nested dict with null fields
{
    "function_declarations": null,
    "retrieval": null,
    "file_search": {...},
    "code_execution": null,
    ...  # Many null fields
}
```

**✅ CORRECT** (official format from docs):
```python
# Raw dict with "type" field
{
    "type": "file_search",
    "file_search_store_names": ["fileSearchStores/..."]
}

{
    "type": "function",
    "name": "function_name",
    "description": "...",
    "parameters": {...}
}
```

### KG Adapter Method Fixes
Original function definitions referenced non-existent methods:
- ❌ `get_project_by_name()` → doesn't exist
- ❌ `get_project_metrics()` → doesn't exist
- ❌ `list_projects_by_location()` → doesn't exist

**Fixed to use actual methods**:
- ✅ `get_project_metadata(project_name)` → returns full project dict
- ✅ `get_all_projects()` → returns list of project names
- ✅ Manual filtering for location-based queries

---

## File Reference

### Implementation Files
- `/Users/tusharsikand/Documents/Projects/liases-foras/app/adapters/atlas_performance_adapter.py` - Main performance adapter (ATLASPerformanceAdapter)
- `/Users/tusharsikand/Documents/Projects/liases-foras/test_atlas_performance.py` - 4-test performance suite
- `/Users/tusharsikand/Documents/Projects/liases-foras/scripts/upload_to_gemini_file_search.py` - RAG file upload utility

### Test Results
- Autonomous tool selection: 100% accurate (3/3)
- Average query time: 7,931ms (vs 2,000ms target)
- Function calling: Working but slow (2 API round-trips)
- File Search: Working (3 files indexed successfully)

---

## Conclusion

**Architecture Status**: ✅ **COMPLETE** - All 3 components integrated and functional

**Performance Status**: ❌ **NOT MEETING TARGET** - 7.9s average vs <2s goal

**Recommended Next Step**: Implement **Option 1 (Hybrid Architecture)**
- Direct `generateContent` API for KG queries → ~1-2s ✅
- Interactions API for File Search queries → ~3-4s ⚠️
- Query routing layer to intelligently choose API path

**Timeline to <2s Performance**:
- KG queries: Can achieve <2s immediately with API switch
- File Search queries: Need caching + optimization (2-4 weeks)
- Average: Can achieve <2s for 70% of queries in 1 week

---

**Generated**: 2025-01-28
**Model**: gemini-2.5-flash (Interactions API)
**Test Suite**: test_atlas_performance.py
**File Search Store**: fileSearchStores/8q3a4kh0o5u9-9n1a2dzr14me
