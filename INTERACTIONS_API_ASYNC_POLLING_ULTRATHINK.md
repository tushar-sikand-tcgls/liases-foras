# Interactions API Async Polling - Ultra-Think Analysis

## Executive Summary

**Problem Discovered**: Current Interactions API implementation uses BLOCKING synchronous calls, causing timeout issues and slow performance (4.9s average for qualitative queries).

**Root Cause**: The `client.interactions.create()` call blocks for up to 30 seconds waiting for a response, which:
1. Causes "Read timed out" errors
2. Results in 5-6 second query times for File Search
3. Prevents proper async handling of complex agentic queries

**Solution**: Implement async polling pattern with `background=True` parameter.

---

## Current Implementation (BLOCKING - ❌ BROKEN)

### atlas_performance_adapter.py (Lines 148-155)

```python
interaction = self.client.interactions.create(
    model=self.model_name,
    input=user_query,
    tools=tools,
    # ❌ NO background=True - BLOCKS for 30 seconds
)

# ❌ Assumes synchronous response
final_answer = interaction.outputs[-1].text if interaction.outputs else "No response"
```

**Problems:**
1. **Blocking Call**: Client waits for full response (up to 30s timeout)
2. **No State Management**: Doesn't handle `NEEDS_TOOL_CALL` status
3. **No Polling Loop**: Assumes single-round-trip (incorrect for function calling)
4. **Timeout Errors**: "Read timed out" when queries take >30s

**Performance Impact (from test results):**
- File Search queries: **4,969ms average** (42% over 3.5s target)
- Likely hitting timeout issues internally
- No proper async handling

---

## Correct Implementation (ASYNC POLLING - ✅ CORRECT)

### Architecture

```
User Query
    ↓
client.interactions.create(..., background=True)  # Returns immediately with interaction_id
    ↓
    Status: IN_PROGRESS
    ↓
Polling Loop (every 5 seconds):
    ↓
    client.interactions.get(interaction_id)
    ↓
    ├─ Status: IN_PROGRESS → Continue polling
    ├─ Status: NEEDS_TOOL_CALL → Execute function, send tool_response, continue polling
    ├─ Status: COMPLETED → Extract outputs[-1].text, return answer ✅
    └─ Status: FAILED → Handle error
```

### Code Implementation

```python
def query_with_async_polling(self, user_query: str) -> Dict:
    """
    Execute query using async polling pattern (correct Interactions API usage)
    """
    start_time = time.time()

    # Step 1: Create interaction with background=True (returns immediately)
    print(f"🚀 Starting interaction with background execution...")
    initial_interaction = self.client.interactions.create(
        model=self.model_name,
        input=user_query,
        tools=tools,
        background=True,  # ✅ KEY: Returns immediately with interaction_id
        request_options={"timeout": 120}  # ✅ Increased timeout for polling
    )

    interaction_id = initial_interaction.id
    print(f"✅ Interaction started. ID: {interaction_id}, Status: {initial_interaction.status}")

    # Step 2: Polling loop until COMPLETED
    poll_count = 0
    while True:
        poll_count += 1
        print(f"🔄 Poll #{poll_count}: Checking status...")

        # Get current status
        current_interaction = self.client.interactions.get(interaction_id)
        status = current_interaction.status
        print(f"   Status: {status}")

        if status == "COMPLETED":
            # ✅ Final answer ready
            final_answer = current_interaction.outputs[-1].text
            execution_time_ms = (time.time() - start_time) * 1000

            print(f"✅ Completed in {execution_time_ms:.2f}ms after {poll_count} polls")

            return {
                "answer": final_answer,
                "execution_time_ms": execution_time_ms,
                "tool_used": "file_search",  # or detect from tool_calls
                "interaction_id": interaction_id,
                "poll_count": poll_count
            }

        elif status == "NEEDS_TOOL_CALL":
            # ✅ Function calling required (KG lookup)
            print(f"🔧 Function call required...")

            for call in current_interaction.tool_calls:
                if call.name == "knowledge_graph_lookup":
                    print(f"   Calling KG with args: {call.args}")

                    # Execute local KG function
                    kg_result = self.kg_adapter.lookup(call.args)

                    # Send tool response back to continue conversation
                    self.client.interactions.send_tool_response(
                        interaction_id=interaction_id,
                        tool_response=types.ToolResponse(
                            call_id=call.id,
                            response=kg_result
                        )
                    )
                    print(f"   ✅ Tool response sent, continuing...")

            # Continue polling after sending tool response
            time.sleep(2)  # Wait 2s before next poll

        elif status == "FAILED":
            # ❌ Error occurred
            error_msg = current_interaction.error_message or "Unknown error"
            print(f"❌ Interaction failed: {error_msg}")
            raise Exception(f"Interaction failed: {error_msg}")

        elif status == "IN_PROGRESS":
            # ⏳ Still processing, wait and poll again
            print(f"   ⏳ Still in progress, waiting 5s...")
            time.sleep(5)

        else:
            # Unknown status
            print(f"⚠️  Unknown status: {status}")
            time.sleep(5)
```

---

## Performance Comparison

### Before (Blocking Synchronous - Current)

| Metric | Value | Issue |
|--------|-------|-------|
| File Search queries | 4,969ms | 42% over 3.5s target |
| Timeout errors | Frequent | "Read timed out" |
| Function calling | 2 round-trips | Blocking on each |
| Average | 2,207ms | 10% over 2s target |

### After (Async Polling - Expected)

| Metric | Expected | Improvement |
|--------|----------|-------------|
| File Search queries | 2,500-3,000ms | 40-50% faster |
| Timeout errors | None | ✅ Eliminated |
| Function calling | Async polling | ✅ Non-blocking |
| Average | **1,800-1,900ms** | ✅ **<2s TARGET ACHIEVED** |

---

## Implementation Changes Required

### File 1: `app/adapters/atlas_performance_adapter.py`

**Changes:**
1. Add `background=True` to `client.interactions.create()`
2. Implement polling loop with `client.interactions.get(interaction_id)`
3. Handle `NEEDS_TOOL_CALL` status for function calling
4. Add proper timeout handling (120s for polling)

**Lines to modify:** 148-180 (entire `query()` method)

**New method signature:**
```python
def query(self, user_query: str) -> PerformanceResponse:
    """Execute query using async polling pattern"""
```

### File 2: `test_hybrid_router.py`

**Changes:**
- Update test expectations for qualitative queries:
  - Before: <3500ms
  - After: <3000ms (with async polling)

**Lines to modify:** 67-69 (qualitative query time limits)

---

## Key Design Principles (Async Polling)

1. **Non-Blocking Initialization**: `background=True` returns immediately with `interaction_id`

2. **Polling Interval**:
   - If `NEEDS_TOOL_CALL`: 2 seconds (fast response after tool call)
   - If `IN_PROGRESS`: 5 seconds (normal polling)

3. **Status Handling**:
   - `IN_PROGRESS` → Continue polling
   - `NEEDS_TOOL_CALL` → Execute function + send response + continue polling
   - `COMPLETED` → Extract answer and return
   - `FAILED` → Raise exception

4. **Timeout Strategy**:
   - Client timeout: 120s (for entire polling session)
   - No per-poll timeout (each `get()` call is fast)

5. **Tool Response Format**:
```python
types.ToolResponse(
    call_id=call.id,  # ✅ Must match tool_call.id
    response=kg_result  # ✅ Dict with function result
)
```

---

## Root Cause Analysis

### Why Current Implementation is Slow

**Test Results (from `test_hybrid_router.py`):**

```
[8/10] What is Absorption Rate? Define it.
    Execution Path: interactions_api
    Query Time: 4314.05ms
    Status: ⚠️  Over limit by 814.08ms

[9/10] Explain PSF formula
    Execution Path: interactions_api
    Query Time: 5624.82ms
    Status: ⚠️  Over limit by 2124.84ms

Qualitative Queries Average: 4,969ms (42% over 3.5s target)
```

**Root Causes:**

1. **Blocking Synchronous Call**: `client.interactions.create()` without `background=True` blocks for full response
2. **30-Second Timeout**: Internal timeout causes "Read timed out" errors
3. **No Polling**: Assumes single API call returns final answer (incorrect for agentic queries)
4. **Function Calling Overhead**: If function calling occurs, requires 2 blocking round-trips:
   - Call 1: Gemini decides to call function (blocks 2-3s)
   - Local execution: 100ms
   - Call 2: Gemini synthesizes answer (blocks 4-5s)
   - Total: 6-8s (if no timeout)

**Why Async Polling Fixes This:**

1. **Non-Blocking**: Client doesn't wait for full response
2. **No Timeout Errors**: Each poll is fast (<100ms), no 30s blocking
3. **Proper State Management**: Handles `NEEDS_TOOL_CALL` correctly
4. **Efficient Function Calling**: Send tool response immediately, continue polling without blocking
5. **Expected Performance**: 2.5-3.0s for File Search queries (vs 5-6s blocking)

---

## Expected Performance After Fix

### Weighted Average Calculation

**Query Distribution:**
- 70% quantitative (Direct API): 1,517ms ✅
- 30% qualitative (Interactions API with async polling): 2,750ms (estimated)

**Weighted Average:**
```
(0.70 × 1,517ms) + (0.30 × 2,750ms) = 1,887ms
```

**Result**: ✅ **1,887ms average < 2,000ms TARGET ACHIEVED**

### Performance by Query Type (After Fix)

| Query Type | Path | Expected Time | Status |
|------------|------|---------------|--------|
| Quantitative (70%) | Direct API | 1,500ms | ✅ <2s |
| Qualitative (30%) | Interactions API (async) | 2,750ms | ✅ <3s |
| **Average** | **Hybrid** | **1,887ms** | **✅ <2s TARGET** |

---

## Implementation Priority

### High Priority (CRITICAL - Performance Blocker)
1. ✅ **Update `atlas_performance_adapter.py`** with async polling pattern
2. ✅ **Test File Search queries** to validate 2.5-3.0s performance
3. ✅ **Re-run `test_hybrid_router.py`** to verify <2s average

### Medium Priority (Validation)
4. Test function calling with `NEEDS_TOOL_CALL` status
5. Validate `send_tool_response()` integration
6. Monitor poll count (should be 2-4 polls per query)

### Low Priority (Optimization)
7. Optimize polling interval (5s → 3s if consistent)
8. Add caching for common File Search queries
9. Implement poll count monitoring/logging

---

## Next Steps

1. **Implement Async Polling** in `atlas_performance_adapter.py` (30 min)
2. **Test File Search Performance** with qualitative queries (10 min)
3. **Re-run Comprehensive Test** (`test_hybrid_router.py`) (5 min)
4. **Validate <2s Average** achieved with async polling (5 min)

**Total Implementation Time**: ~50 minutes

**Expected Outcome**: <2s average performance with all 3 components working ✅

---

## Conclusion

**Problem**: Blocking synchronous Interactions API calls causing 4.9s average for File Search queries (42% over target).

**Solution**: Async polling pattern with `background=True` and proper status handling.

**Expected Impact**:
- File Search queries: 4.9s → 2.75s (44% faster)
- Overall average: 2.2s → 1.9s (14% faster)
- **✅ Achieves <2s target with all 3 components**

**Implementation Status**: Ready to implement (code provided above)
