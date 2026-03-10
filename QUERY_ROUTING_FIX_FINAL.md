# Query Routing Fix - Dual-Layered Approach

## Problem Statement

**User queries fiscal year data without mentioning a project:**
- ❌ "What is supply units for FY 24-25?" → Gemini asks for project name
- ❌ "Show me sales in 2023" → Gemini asks for project name

**Expected behavior:**
- ✅ Should automatically route to quarterly market data for Chakan
- ✅ Should NOT ask for clarification

---

## Solution: Dual-Layered Routing

Implemented TWO layers of routing instructions to ensure Gemini correctly routes fiscal year queries:

### Layer 1: System Instruction (Model-Level)
**File:** `app/services/gemini_function_calling_service.py`
**Function:** `_initialize_model_with_functions()`

Added permanent routing rules to the model's system instruction:

```python
system_instruction = """...

CRITICAL ROUTING RULES:

1. QUARTERLY MARKET DATA QUERIES (Default for market-level queries):
   When user asks about "supply units", "sales units", "market data",
   or mentions a FISCAL YEAR (e.g., "FY 24-25", "FY 2023-24")
   WITHOUT specifying a specific project name:

   → ALWAYS use: get_quarters_by_year_range

   Examples:
   - "What is supply units for FY 24-25?"
     → get_quarters_by_year_range(start_year=2024, end_year=2024)
   - "Show me sales in 2023"
     → get_quarters_by_year_range(start_year=2023, end_year=2023)

2. PROJECT-SPECIFIC QUERIES:
   When user mentions a SPECIFIC PROJECT NAME:
   → Use: get_project_by_name

REMEMBER: "FY 24-25" or "fiscal year" queries WITHOUT a project name
= quarterly market data for Chakan."""
```

### Layer 2: Query-Level Routing Hint (Per-Query)
**File:** `app/services/gemini_function_calling_service.py`
**Function:** `_build_initial_prompt()`

Added dynamic routing hint that gets injected **with each query** when fiscal year patterns are detected:

```python
def _build_initial_prompt(self, query, chat_history, system_prompt):
    # Detect fiscal year patterns
    has_fy_pattern = any(pattern in query_lower
                         for pattern in ['fy ', 'fiscal year', 'financial year'])
    has_year_number = any(str(year) in query for year in range(2014, 2027))
    has_market_keyword = any(kw in query_lower
                             for kw in ['supply units', 'sales units', 'market data'])

    # Check if project name mentioned
    known_projects = ['sara city', 'gulmohar city', 'vtp pegasus', ...]
    has_project_name = any(project in query_lower for project in known_projects)

    # Add routing instruction if needed
    if (has_fy_pattern or (has_year_number and has_market_keyword)) and not has_project_name:
        prompt = """
<ROUTING_INSTRUCTION>
This query is about MARKET-LEVEL data (no specific project mentioned).
Use get_quarters_by_year_range or get_recent_quarters function.
DO NOT ask for project name - return Chakan quarterly market data.
</ROUTING_INSTRUCTION>

""" + query
```

---

## How It Works

### Example: "What is supply units for FY 24-25?"

**Step 1: Pattern Detection**
```
has_fy_pattern = True (contains "fy ")
has_year_number = True (contains "24")
has_market_keyword = True (contains "supply units")
has_project_name = False (no known project names found)
```

**Step 2: Routing Hint Injection**
The query is transformed before being sent to Gemini:

```
Original: "What is supply units for FY 24-25?"

Sent to Gemini:
"""
<ROUTING_INSTRUCTION>
This query is about MARKET-LEVEL data (no specific project mentioned).
Use get_quarters_by_year_range or get_recent_quarters function.
DO NOT ask for project name - return Chakan quarterly market data.
</ROUTING_INSTRUCTION>

What is supply units for FY 24-25?
"""
```

**Step 3: Gemini Routes Correctly**
With both:
1. System instruction (permanent rules)
2. Routing hint (per-query instruction)

Gemini now understands to call:
```python
get_quarters_by_year_range(start_year=2024, end_year=2024)
```

**Step 4: Enhanced Response**
Returns comprehensive quarterly data:
```
Location: Chakan, Pune, Maharashtra
Total Supply Units: 6,894 units
Quarterly Breakdown: Q1-Q4
Aggregated Metrics: Absorption rate, averages
```

---

## Pattern Detection Logic

### Fiscal Year Patterns
```python
['fy ', 'fiscal year', 'financial year', 'f.y.']
```

**Matches:**
- "FY 24-25"
- "fiscal year 2023"
- "F.Y. 2024-25"
- "FY2023"

### Year Numbers
```python
range(2014, 2027)  # 2014 to 2026
```

**Matches:**
- "2024"
- "2023-24"
- "24-25"

### Market Keywords
```python
['supply units', 'sales units', 'market data', 'chakan', 'quarterly']
```

**Matches:**
- "supply units"
- "sales data"
- "market data"
- "Chakan"
- "quarterly trends"

### Known Project Names (Exclusion)
```python
['sara city', 'gulmohar city', 'vtp pegasus', 'megapolis', 'urbana',
 'sara nilaay', 'pradnyesh', 'siddhivinayak', 'sarangi', 'kalpavruksh', 'shubhan']
```

**If any project name found → NO routing hint (use project-specific functions)**

---

## Test Cases

### Test 1: FY Query (No Project)
```
Input: "What is supply units for FY 24-25?"

Pattern Detection:
  has_fy_pattern = True
  has_year_number = True
  has_market_keyword = True
  has_project_name = False

Routing Hint: YES

Expected Function Call:
  get_quarters_by_year_range(start_year=2024, end_year=2024)

Expected Response:
  Chakan quarterly data for FY 24-25
```

### Test 2: Year Query (No Project)
```
Input: "Show me sales in 2023"

Pattern Detection:
  has_fy_pattern = False
  has_year_number = True
  has_market_keyword = True (contains "sales")
  has_project_name = False

Routing Hint: YES

Expected Function Call:
  get_quarters_by_year_range(start_year=2023, end_year=2023)

Expected Response:
  Chakan quarterly data for 2023
```

### Test 3: Market Query (No Year, No Project)
```
Input: "Show me market data"

Pattern Detection:
  has_fy_pattern = False
  has_year_number = False
  has_market_keyword = True
  has_project_name = False

Routing Hint: NO (year number required for get_quarters_by_year_range)

Gemini Behavior:
  May call get_recent_quarters(n=8) based on system instruction
  OR may ask for clarification (year or project)
```

### Test 4: Project-Specific Query
```
Input: "What is supply for Sara City in FY 24-25?"

Pattern Detection:
  has_fy_pattern = True
  has_year_number = True
  has_market_keyword = True
  has_project_name = True ("sara city" found)

Routing Hint: NO (project name detected)

Expected Function Call:
  get_project_by_name(project_name="Sara City")

Expected Response:
  Sara City project-specific data
```

---

## Why Dual-Layered Approach?

### Layer 1 (System Instruction)
**Pros:**
- Permanent, applies to all queries
- Educates the model about routing patterns
- Works for Gemini's internal reasoning

**Cons:**
- Sometimes ignored if query is ambiguous
- May not be strong enough alone

### Layer 2 (Routing Hint)
**Pros:**
- **VERY explicit** - hard for Gemini to ignore
- Per-query, dynamically generated
- Acts as a "forcing function"
- Includes "DO NOT ask for project name" directive

**Cons:**
- Requires pattern matching (false positives possible)
- Adds slight processing overhead

### Combined Effect
**Synergy:**
- System instruction provides **context and examples**
- Routing hint provides **explicit directive** for matching queries
- Together they create a **strong routing signal**

---

## Files Modified

### 1. `app/services/gemini_function_calling_service.py`

**Function:** `_initialize_model_with_functions()` (Lines 145-186)
- Added CRITICAL ROUTING RULES to system instruction

**Function:** `_build_initial_prompt()` (Lines 361-433)
- Added pattern detection logic
- Added dynamic routing hint injection

### 2. `app/services/function_registry.py`

**Function:** `get_quarters_by_year_range` schema (Lines 1147-1169)
- Updated description to emphasize "DEFAULT FUNCTION"

**Function:** `_handle_get_quarters_by_year_range()` (Lines 1272-1307)
- Enhanced to return aggregated metrics + location context

---

## Deployment Steps

### 1. Backend Restart Required
```bash
# Kill old process
kill <old_pid>

# Start new process
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
```

### 2. Verify Routing
Test with:
```
Query: "What is supply units for FY 24-25?"

Expected in logs:
  <ROUTING_INSTRUCTION> injected
  Function called: get_quarters_by_year_range
  Parameters: {"start_year": 2024, "end_year": 2024}
```

### 3. Frontend Test
Use Streamlit interface:
1. Navigate to query input
2. Enter: "What is supply units for FY 24-25?"
3. Verify response includes Chakan quarterly data

---

## Troubleshooting

### Issue: Still Asking for Project Name

**Check 1: Backend Restart**
```bash
ps aux | grep uvicorn
# Verify PID is new (after code changes)
```

**Check 2: Routing Hint Injection**
Add debug logging:
```python
if routing_hint:
    print(f"[DEBUG] Routing hint injected for query: {query}")
    print(f"[DEBUG] Routing hint: {routing_hint}")
```

**Check 3: Pattern Detection**
Add debug logging:
```python
print(f"[DEBUG] has_fy_pattern: {has_fy_pattern}")
print(f"[DEBUG] has_year_number: {has_year_number}")
print(f"[DEBUG] has_market_keyword: {has_market_keyword}")
print(f"[DEBUG] has_project_name: {has_project_name}")
```

### Issue: False Positives (Routes When Shouldn't)

**Solution:** Tighten pattern matching
```python
# Require BOTH fiscal year AND market keyword
if has_fy_pattern and has_market_keyword and not has_project_name:
    routing_hint = ...
```

---

## Future Enhancements

### 1. Multi-Region Support
When adding other regions (Hinjewadi, Baner):

```python
# Detect region in query
regions = ['chakan', 'hinjewadi', 'baner', 'kharadi']
detected_region = next((r for r in regions if r in query_lower), 'chakan')

routing_hint = f"""
<ROUTING_INSTRUCTION>
This query is about MARKET-LEVEL data for {detected_region.title()}.
Use get_quarters_by_year_range with region filter.
</ROUTING_INSTRUCTION>
"""
```

### 2. Adaptive Learning
Track which queries get routed incorrectly:

```python
# Log routing decisions
log_routing_decision({
    "query": query,
    "routing_hint_used": bool(routing_hint),
    "function_called": function_name,
    "user_feedback": feedback  # From UI
})
```

### 3. More Granular Patterns
Add support for:
- Quarter-specific queries: "Q3 2023"
- Month queries: "September 2023"
- Relative dates: "last year", "last quarter"

---

**Update Date:** 2025-01-28
**Status:** ✅ Implemented - **Backend Restart Required**
**Impact:** High - Fixes core UX issue with fiscal year queries
