# Gemini Function Calling - Routing Rules Update

## Summary

Updated the Gemini system instruction to **explicitly route fiscal year queries to quarterly market data** when no specific project is mentioned.

---

## Problem

**User Query:** "What is supply units for FY 24-25?"

**Old Behavior:**
```
❌ Gemini: "I can help you find the current total supply units for specific real estate
projects. However, I do not have the ability to filter data by a specific financial
year like 'FY 24-25'. Could you please provide the name of the project?"
```

**Issue:** Gemini didn't understand that fiscal year queries should route to quarterly market data by default.

---

## Solution

Added **CRITICAL ROUTING RULES** to the Gemini system instruction (`gemini_function_calling_service.py`):

### Routing Rule 1: Quarterly Market Data (Default)

```
When user asks about "supply units", "sales units", "market data",
or mentions a FISCAL YEAR (e.g., "FY 24-25", "FY 2023-24")
WITHOUT specifying a specific project name:

→ ALWAYS use: get_quarters_by_year_range

Examples:
- "What is supply units for FY 24-25?"
  → get_quarters_by_year_range(start_year=2024, end_year=2024)

- "Show me sales in 2023"
  → get_quarters_by_year_range(start_year=2023, end_year=2023)

- "Market data for Chakan"
  → get_recent_quarters(n=8)

This returns aggregated quarterly data for Chakan, Pune micromarket.
```

### Routing Rule 2: Project-Specific Queries

```
When user mentions a SPECIFIC PROJECT NAME
(e.g., "Sara City", "Gulmohar City"):

→ Use: get_project_by_name

Examples:
- "What is supply for Sara City?"
  → get_project_by_name(project_name="Sara City")
```

---

## Expected Behavior After Update

**User Query:** "What is supply units for FY 24-25?"

**New Behavior:**
```
✅ Gemini: Calls get_quarters_by_year_range(start_year=2024, end_year=2024)

Response:
Location: Chakan, Pune, Maharashtra
Fiscal Year: FY 2024-24

Total Supply Units: 6,894 units
Total Sales Units: 807 units
Average Supply/Quarter: 1,724 units
Absorption Rate: 11.71%

Quarterly Breakdown:
  Q1 24-25: 1,741 units
  Q2 24-25: 1,731 units
  Q3 24-25: 1,699 units
  Q4 24-25: 1,723 units
```

---

## Implementation Details

### File Modified
**Path:** `app/services/gemini_function_calling_service.py`

**Function:** `_initialize_model_with_functions()`

**Change:** Updated `system_instruction` with explicit routing rules

### Before
```python
system_instruction = """You are an expert real estate intelligence assistant.

You have access to a comprehensive knowledge base...

Use the available functions to execute queries and calculations."""
```

### After
```python
system_instruction = """You are an expert real estate intelligence assistant.

You have access to a comprehensive knowledge base...

CRITICAL ROUTING RULES:

1. QUARTERLY MARKET DATA QUERIES (Default for market-level queries):
   When user asks about "supply units", "sales units", "market data",
   or mentions a FISCAL YEAR (e.g., "FY 24-25", "FY 2023-24")
   WITHOUT specifying a specific project name:

   → ALWAYS use: get_quarters_by_year_range

   ...

2. PROJECT-SPECIFIC QUERIES:
   When user mentions a SPECIFIC PROJECT NAME:

   → Use: get_project_by_name

   ...

REMEMBER: "FY 24-25" or "fiscal year" queries WITHOUT a project name
= quarterly market data for Chakan."""
```

---

## Key Trigger Phrases

Gemini will now recognize these patterns and route to quarterly data:

### Fiscal Year Patterns
- "FY 24-25"
- "FY 2023-24"
- "fiscal year 2024"
- "financial year 2023"

### Market Data Keywords
- "supply units"
- "sales units"
- "market data"
- "quarterly data"
- "market trends"

### Location Context (Without Project)
- "Chakan"
- "Pune market"
- "market performance"

---

## Testing

### Test Query 1: FY Query
```
Input: "What is supply units for FY 24-25?"
Expected: Calls get_quarters_by_year_range(2024, 2024)
Returns: 6,894 units total supply for Chakan
```

### Test Query 2: Year Query
```
Input: "Show me sales in 2023"
Expected: Calls get_quarters_by_year_range(2023, 2023)
Returns: Quarterly sales data for 2023
```

### Test Query 3: Market Query
```
Input: "Market data for Chakan"
Expected: Calls get_recent_quarters(n=8)
Returns: Last 8 quarters of data
```

### Test Query 4: Project-Specific (No Change)
```
Input: "What is supply for Sara City?"
Expected: Calls get_project_by_name("Sara City")
Returns: Sara City project data
```

---

## Benefits

1. **Better UX**: Users don't need to clarify when asking fiscal year questions
2. **Context-Aware**: System understands Chakan is the default location
3. **Explicit Routing**: Clear rules prevent ambiguity
4. **Examples in Prompt**: Gemini learns from examples
5. **Fallback Preserved**: Project-specific queries still work

---

## Edge Cases

### Case 1: Ambiguous Query
```
User: "What is supply?"
Gemini: Will likely ask for clarification (year or project)
```

### Case 2: Multi-year Range
```
User: "Show me data from 2020 to 2024"
Gemini: Calls get_quarters_by_year_range(2020, 2024)
```

### Case 3: Specific Project + Year
```
User: "What is supply for Sara City in FY 24-25?"
Gemini: Should use get_project_by_name("Sara City")
(Project-specific takes precedence)
```

---

## Rollback Plan

If this causes issues, revert by removing the CRITICAL ROUTING RULES section:

```python
system_instruction = """You are an expert real estate intelligence assistant.

You have access to a comprehensive knowledge base (LF-Layers_FULLY_ENRICHED_ALL_36.xlsx) that contains:
- ALL metric definitions and formulas
- Metric synonyms (e.g., "Efficiency Ratio" → "Sellout Efficiency")
- Dimensional relationships
- Real estate industry terminology

IMPORTANT: When users ask about ANY metric:
1. First search the knowledge base file for the metric definition
2. If you find a synonym, use the official metric name
3. Cite the knowledge base when explaining metrics

Use the available functions to execute queries and calculations."""
```

---

## Related Changes

This update works in conjunction with:

1. **Function Description** (`function_registry.py`):
   - `get_quarters_by_year_range` marked as "DEFAULT FUNCTION"

2. **Handler Enhancement** (`function_registry.py`):
   - Returns aggregated metrics + location context

3. **Data Model** (`quarterly_sales_supply.json`):
   - Includes Chakan location metadata

4. **ChromaDB** (`chroma_quarterly_db`):
   - 48 documents with location context

---

## Monitoring

To verify the routing is working:

1. **Check function calls in logs**:
   ```
   Function called: get_quarters_by_year_range
   Parameters: {"start_year": 2024, "end_year": 2024}
   ```

2. **Verify response includes location**:
   ```
   Location: Chakan, Pune, Maharashtra
   ```

3. **Check aggregated metrics are returned**:
   ```
   Total Supply Units: 6,894
   ```

---

**Update Date:** 2025-01-28
**File Modified:** `app/services/gemini_function_calling_service.py`
**Lines Changed:** 145-186
**Status:** ✅ Ready to Test
**Impact:** Improved routing for fiscal year queries
