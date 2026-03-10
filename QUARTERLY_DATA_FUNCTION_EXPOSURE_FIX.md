# Quarterly Data Function Exposure Fix

## Problem Statement

**User Query:** "What is supply units for FY 24-25?"

**Expected:** Return quarterly data directly from the table (6,894 units total)

**Actual Behavior:** Gemini was asking "which project?" even though the query was about market-level data, not project-specific data.

**Root Cause:** The quarterly market functions (`get_quarters_by_year_range`, `get_recent_quarters`, `get_all_quarterly_data`) were registered in the Function Registry but **NOT exposed to Gemini** via the ATLAS Hybrid endpoint.

---

## The Real Issue

The system had **two separate code paths**:

### Path 1: GeminiFunctionCallingService (Not Used by Streamlit)
- File: `app/services/gemini_function_calling_service.py`
- Had routing logic and system instructions
- **NOT used by the `/api/atlas/hybrid/query` endpoint**
- Changes made here had no effect on actual queries

### Path 2: ATLAS Performance Adapter (Used by Streamlit) ⚠️
- File: `app/adapters/atlas_performance_adapter.py`
- Used by `/api/atlas/hybrid/query` endpoint
- **Only exposed ONE function:** `liases_foras_lookup` (project-specific queries)
- **Missing:** Quarterly market functions

---

## The Fix

### Step 1: Added Quarterly Functions to ATLAS Adapter Tools

**File:** `app/adapters/atlas_performance_adapter.py`
**Location:** Lines 904-949

```python
# Add quarterly market functions for market-level queries (no specific project)
quarterly_functions = [
    {
        "type": "function",
        "name": "get_quarters_by_year_range",
        "description": "Get quarterly sales and supply data for the region within a specific year range. DEFAULT FUNCTION for queries about supply units, sales units, or market data when NO SPECIFIC PROJECT is mentioned. Examples: 'What is supply units for FY 24-25?', 'Show me sales in 2023', 'Market data for FY2022-2023'. Returns aggregated market data with location context.",
        "parameters": {
            "type": "object",
            "properties": {
                "start_year": {"type": "integer", "description": "Starting year (e.g., 2024 for FY 24-25)"},
                "end_year": {"type": "integer", "description": "Ending year (e.g., 2024 for FY 24-25)"}
            },
            "required": ["start_year", "end_year"]
        }
    },
    {
        "type": "function",
        "name": "get_recent_quarters",
        "description": "Get the N most recent quarters of sales and supply data. Perfect for queries like 'Show me recent market trends', 'Latest quarterly data', 'What's happening in the market recently?'. Default: 8 quarters (2 years).",
        "parameters": {
            "type": "object",
            "properties": {
                "n": {"type": "integer", "description": "Number of recent quarters to retrieve (default: 8)"}
            }
        }
    },
    {
        "type": "function",
        "name": "get_all_quarterly_data",
        "description": "Get all quarterly sales and marketable supply data from Q2 FY14-15 to Q2 FY25-26. Returns complete time-series data for comprehensive market trend analysis. Use when user asks for 'all data', 'complete history', 'full time series'.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
]
tools.extend(quarterly_functions)
```

### Step 2: Added Function Call Handler

**File:** `app/adapters/atlas_performance_adapter.py`
**Location:** Lines 988-993 (routing), Lines 1426-1449 (executor)

```python
# In function call routing (lines 988-993)
elif output.name in ["get_quarters_by_year_range", "get_recent_quarters", "get_all_quarterly_data"]:
    function_results = self._execute_quarterly_market_function(
        output.name,
        dict(output.arguments)
    )
    tool_used = "quarterly_market_data"

# Executor method (lines 1426-1449)
def _execute_quarterly_market_function(self, function_name: str, arguments: Dict) -> Dict:
    """
    Execute quarterly market data functions using FunctionRegistry

    Args:
        function_name: Name of quarterly function
        arguments: Function arguments (start_year, end_year, n, etc.)

    Returns:
        Quarterly market data with location context and aggregated metrics
    """
    try:
        from app.services.function_registry import get_function_registry

        registry = get_function_registry()
        result = registry.execute_function(function_name, arguments)

        return result
    except Exception as e:
        return {
            "error": str(e),
            "function_name": function_name,
            "arguments": arguments
        }
```

---

## Verification

### Test Query 1: FY 24-25 Supply Units

**Query:** "What is supply units for FY 24-25?"

**Response:**
```
The supply units for FY 24-25 are:

* Q1 24-25: 1741 units
* Q2 24-25: 1731 units
* Q3 24-25: 1699 units
* Q4 24-25: 1723 units

The total supply units for FY 24-25 (Q1 to Q4) are 6894 units.
```

**Metadata:**
- Execution Path: `interactions_api`
- Tool Used: `quarterly_market_data` ✅
- Function Called: `get_quarters_by_year_range(start_year=2024, end_year=2024)`

### Direct Function Test

```python
from app.services.function_registry import get_function_registry

registry = get_function_registry()
result = registry.execute_function('get_quarters_by_year_range', {'start_year': 2024, 'end_year': 2024})

# Output:
Location: {'region': 'Chakan', 'city': 'Pune', 'state': 'Maharashtra'}
Total Supply: 6,894 units
Message: Chakan, Pune: 4 quarters from FY 2024-24 (Total Supply: 6,894 units, Total Sales: 807 units)
```

---

## What Changed

### Before Fix

**Available Functions in ATLAS Adapter:**
1. `liases_foras_lookup` - Project-specific queries only
2. `getDistanceFromProject` - Distance calculations
3. `find_projects_within_radius` - Proximity search
4. `generate_location_map_with_poi` - Map visualization

**Total:** 4 functions

**Missing:** All quarterly market functions!

### After Fix

**Available Functions in ATLAS Adapter:**
1. `liases_foras_lookup` - Project-specific queries
2. `getDistanceFromProject` - Distance calculations
3. `find_projects_within_radius` - Proximity search
4. `generate_location_map_with_poi` - Map visualization
5. **`get_quarters_by_year_range`** - Quarterly data by year ✅ NEW
6. **`get_recent_quarters`** - Recent N quarters ✅ NEW
7. **`get_all_quarterly_data`** - All historical data ✅ NEW

**Total:** 7 functions

---

## Why This Matters

### The Knowledge Graph (KG) Was Always There

The quarterly data was:
- ✅ Loaded from `data/extracted/quarterly_sales_supply.json`
- ✅ Indexed in ChromaDB (48 documents)
- ✅ Registered in Function Registry (3 functions)
- ✅ Working when called directly via Python

**But Gemini couldn't see it!**

The ATLAS adapter is the "gatekeeper" between Gemini and the function registry. If a function isn't explicitly added to the `tools` array in the ATLAS adapter, Gemini has no idea it exists.

### Analogy

Think of it like having a library with thousands of books (Function Registry), but only showing the catalog for 4 books to visitors (ATLAS adapter). The other books exist, they're perfectly organized, but visitors can't check them out because they don't know about them.

---

## Testing Other Queries

### Query 2: Recent Market Trends
```
Q: "Show me recent market trends"
Expected Function: get_recent_quarters(n=8)
Status: ✅ Should work
```

### Query 3: Complete History
```
Q: "Show me all quarterly data"
Expected Function: get_all_quarterly_data()
Status: ✅ Should work
```

### Query 4: Specific Year Range
```
Q: "What was supply in 2023?"
Expected Function: get_quarters_by_year_range(start_year=2023, end_year=2023)
Status: ✅ Should work
```

---

## Deployment

**Status:** ✅ Complete

**Backend Restarted:** PID 88509

**Verification Command:**
```bash
curl -s http://localhost:8000/api/atlas/hybrid/query \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "What is supply units for FY 24-25?"}' \
  | python3 -m json.tool
```

**Expected Response:**
- `"tool_used": "quarterly_market_data"`
- `"answer"` contains 6,894 total units

---

## Key Learnings

1. **Function Registration ≠ Function Exposure**
   - Just because a function is in the Function Registry doesn't mean Gemini can use it
   - Must explicitly add to ATLAS adapter's `tools` array

2. **Multiple Code Paths**
   - `GeminiFunctionCallingService` is NOT used by Streamlit
   - ATLAS Hybrid adapter is the actual execution path
   - Always verify which adapter is being used by the endpoint

3. **Tool-Calling Architecture**
   - Gemini Interactions API requires tools to be passed in the `create()` call
   - Each tool needs a type, name, description, and parameters schema
   - Function results are sent back via `previous_interaction_id`

4. **Debugging Strategy**
   - Direct function test: Verify function works in isolation
   - Check endpoint routing: Which adapter is handling the query?
   - Verify tools list: Are functions exposed to Gemini?
   - Test end-to-end: Does Gemini call the right function?

---

**Date:** 2025-01-28
**Status:** ✅ Fixed and Verified
**Impact:** Critical - Core functionality now working as expected
**Files Modified:** `app/adapters/atlas_performance_adapter.py` (Lines 904-949, 988-993, 1426-1449)
