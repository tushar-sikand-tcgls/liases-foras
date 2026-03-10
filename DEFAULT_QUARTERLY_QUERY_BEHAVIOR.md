# Default Quarterly Query Behavior

## Overview

When users ask about **supply units, sales units, or market data WITHOUT specifying a project**, the system now **defaults to quarterly market data for Chakan, Pune** from the comprehensive time-series dataset.

---

## Behavior Change

### ❌ Old Behavior (Before)
```
User: "What is supply units for FY 24-25?"
System: "Could you please specify which project you're interested in?"
```

**Problem:** User had to clarify even though quarterly aggregate data exists.

### ✅ New Behavior (After)
```
User: "What is supply units for FY 24-25?"
System: Returns aggregated quarterly data for Chakan:
  - Location: Chakan, Pune, Maharashtra
  - Total Supply Units: 6,894 units
  - Quarterly breakdown (Q1-Q4)
  - Aggregated metrics (avg, absorption rate)
```

**Benefit:** Immediate, comprehensive answer with location context.

---

## Query Patterns That Trigger Quarterly Data

### Pattern 1: Fiscal Year Queries
- "What is supply units for FY 24-25?"
- "Show me sales in FY 2023-24"
- "Get market data for FY 22-23"

**Response:** Quarterly data for that fiscal year (Chakan)

### Pattern 2: Year Range Queries
- "Show me data from 2020 to 2024"
- "What was supply in 2023?"
- "Sales trends from 2022 to 2024"

**Response:** Quarterly data for that year range (Chakan)

### Pattern 3: General Market Queries (No Project Specified)
- "What's the current supply?"
- "Show me recent sales"
- "Market trends"

**Response:** Recent quarterly data (default: last 8 quarters)

---

## Response Structure

When the `get_quarters_by_year_range` function is called, it returns:

```json
{
  "location": {
    "region": "Chakan",
    "city": "Pune",
    "state": "Maharashtra"
  },
  "fiscal_year": "FY 2024-24",
  "aggregated_metrics": {
    "total_sales_units": 807,
    "total_supply_units": 6894,
    "average_sales_per_quarter": 202,
    "average_supply_per_quarter": 1724,
    "overall_absorption_rate": 11.71
  },
  "quarterly_data": [
    {
      "quarter": "Q1 24-25",
      "sales_units": 227,
      "supply_units": 1741,
      ...
    },
    ...
  ],
  "quarters_count": 4,
  "message": "Chakan, Pune: 4 quarters from FY 2024-24 (Total Supply: 6,894 units, Total Sales: 807 units)"
}
```

---

## Function Description Update

The `get_quarters_by_year_range` function schema now includes:

```python
"description": "Get quarterly sales and supply data for Chakan, Pune within a specific year range. DEFAULT FUNCTION for queries about supply units, sales units, or market data when NO SPECIFIC PROJECT is mentioned. Examples: 'What is supply units for FY 24-25?', 'Show me sales in 2023', 'Get market data for FY2022-2023'. Returns aggregated market data for all projects in Chakan."
```

**Key phrase:** "DEFAULT FUNCTION for queries about supply units, sales units, or market data when NO SPECIFIC PROJECT is mentioned"

This tells Gemini to prioritize this function when:
1. User asks about supply/sales/market data
2. No specific project name is mentioned
3. A year/fiscal year is referenced

---

## Example Queries & Responses

### Example 1: FY 24-25 Supply
**Query:** "What is supply units for FY 24-25?"

**Function Call:**
```python
get_quarters_by_year_range(start_year=2024, end_year=2024)
```

**Response:**
```
Location: Chakan, Pune, Maharashtra
Fiscal Year: FY 2024-24

AGGREGATED METRICS:
  Total Supply Units:  6,894
  Total Sales Units:   807
  Avg Supply/Quarter:  1,724
  Avg Sales/Quarter:   202
  Absorption Rate:     11.71%

QUARTERLY BREAKDOWN:
  Q1 24-25: Supply=1,741 units, Sales=227 units
  Q2 24-25: Supply=1,731 units, Sales=163 units
  Q3 24-25: Supply=1,699 units, Sales=246 units
  Q4 24-25: Supply=1,723 units, Sales=171 units
```

### Example 2: Sales in 2023
**Query:** "What were the sales in 2023?"

**Function Call:**
```python
get_quarters_by_year_range(start_year=2023, end_year=2023)
```

**Response:**
```
Chakan, Pune: 4 quarters from FY 2023-23
Total Sales: 537 units
  Q1 23-24: 116 units
  Q2 23-24: 64 units
  Q3 23-24: 122 units
  Q4 23-24: 235 units
```

### Example 3: Multi-year Range
**Query:** "Show me supply from 2020 to 2024"

**Function Call:**
```python
get_quarters_by_year_range(start_year=2020, end_year=2024)
```

**Response:**
```
Chakan, Pune: 20 quarters from FY 2020-20 to FY 2024-24
Total Supply: 37,453 units
Average per quarter: 1,873 units
```

---

## When Project-Specific Data is Used

If a **specific project name** is mentioned, the system uses project-specific functions instead:

### Project-Specific Query
**Query:** "What is supply units for Sara City?"

**Function Call:**
```python
get_project_by_name(project_name="Sara City")
```

**Response:** Project-specific data for Sara City only

---

## Benefits of This Approach

1. **Better UX**: Users get immediate answers without clarification
2. **Context-Aware**: Automatically understands "Chakan" as the default location
3. **Comprehensive**: Provides both aggregated and quarterly breakdown
4. **Location Transparency**: Always shows "Chakan, Pune, Maharashtra"
5. **Time-Series Context**: Users see trends, not just single data points

---

## Technical Implementation

### Function Registry Change
**File:** `app/services/function_registry.py`

**Function:** `get_quarters_by_year_range`
- **Description:** Updated to emphasize "DEFAULT FUNCTION" for non-project queries
- **Handler:** Enhanced to return aggregated metrics + location info

### Handler Enhancement
```python
def _handle_get_quarters_by_year_range(self, params: Dict) -> Dict:
    # ... fetch data ...

    # Calculate aggregated metrics
    total_sales = sum(q.get('sales_units', 0) for q in data)
    total_supply = sum(q.get('supply_units', 0) for q in data)
    avg_absorption_rate = (total_sales / total_supply * 100) if total_supply > 0 else 0

    # Return with location context
    return {
        "location": {"region": "Chakan", "city": "Pune", "state": "Maharashtra"},
        "fiscal_year": f"FY {start_year}-{str(end_year)[-2:]}",
        "aggregated_metrics": {...},
        "quarterly_data": data,
        ...
    }
```

---

## Rollback Plan

If this behavior causes issues, revert by:

1. **Remove "DEFAULT FUNCTION" from description:**
   ```python
   "description": "Get quarterly data within a specific year range. ..."
   ```

2. **Simplify handler to original:**
   ```python
   return {
       "data": data,
       "count": len(data),
       "year_range": {"start": start_year, "end": end_year},
       "message": f"Retrieved {len(data)} quarters from {start_year} to {end_year}"
   }
   ```

---

## Testing

### Test Command
```bash
python -c "
from app.services.function_registry import get_function_registry
registry = get_function_registry()
result = registry.execute_function('get_quarters_by_year_range', {'start_year': 2024, 'end_year': 2024})
print(f\"Supply FY 24-25: {result['aggregated_metrics']['total_supply_units']:,} units\")
"
```

### Expected Output
```
✓ Loaded 45 quarterly data points
Supply FY 24-25: 6,894 units
```

---

## Documentation Updates

- ✅ Function description updated in `function_registry.py`
- ✅ Handler enhanced with aggregated metrics
- ✅ This behavior documented in `DEFAULT_QUARTERLY_QUERY_BEHAVIOR.md`
- ✅ Location context always included in responses

---

**Update Date:** 2025-01-28
**Status:** ✅ Active
**Impact:** Improved UX for market-level queries
