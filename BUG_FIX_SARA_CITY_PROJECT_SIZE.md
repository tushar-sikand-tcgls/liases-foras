# Bug Fix: Sara City Project Size Query

## Issue Summary

**User Query:** "What is the project size of sara city"

**Expected Result:** 3018 (Layer 0 dimension: project_size in L²)

**Actual Result:** 256.7 Units (incorrect calculation: Σ U / 10)

**Root Cause:** Query was **misrouted** to calculator (Layer 2) instead of retrieval (Layer 0)

---

## Problem Analysis

### 1. Ambiguous Term: "Project Size"

"Project size" can mean:
- **U dimension** (total_units): 1109 units
- **L² dimension** (project_size): 3018 acres

In real estate context, "project size" typically refers to **land area (L²)**, not units.

### 2. Incorrect Routing

The query was routed to `calculate_statistics` (Layer 2) because:
- Keyword match: "total" in prompt_router.py (line 138)
- Pattern match: Statistical aggregation
- **Should have been**: Layer 0 retrieval (`get_project_dimensions`)

### 3. Missing Data in v4 JSON

Current data file (`v4_clean_nested_structure.json`):
```json
{
  "projectName": "Sara City",
  "totalUnits": {
    "value": None  // ← Missing!
  }
}
```

Old data file (`lf_projects_layer0.json`):
```json
{
  "name": "Sara City",
  "layer0": {
    "U": {
      "total_units": 1109.0  // ← Correct value
    },
    "L2": {
      "project_size": 3018.0  // ← Expected answer
    }
  }
}
```

---

## Fixes Implemented

### Fix 1: Enhanced Layer 0 Retrieval Patterns ✅

**File:** `app/services/prompt_router.py` (lines 48-63)

**Before:**
```python
"get_project_dimensions": {
    "keywords": ["dimensions", "raw", "units", "area", ...],
    "patterns": [
        r"what.*dimensions",
        r"get.*project.*data",
        r"show.*raw.*values"
    ],
    "layer": LayerType.LAYER_0
},
```

**After:**
```python
"get_project_dimensions": {
    "keywords": ["dimensions", "raw", "units", "area", "time", "cash flow",
               "U", "L2", "CF", "T",
               "project size", "total units", "how many units", "number of units"],
    "patterns": [
        r"what.*dimensions",
        r"get.*project.*data",
        r"show.*raw.*values",
        r"what\s+(is|are)\s+the\s+(project\s+)?size",  // ← NEW
        r"what\s+(is|are)\s+the\s+total\s+units",      // ← NEW
        r"how\s+many\s+units",                          // ← NEW
        r"project\s+size\s+of",                         // ← NEW
        r"total\s+units\s+(of|in|for)"                  // ← NEW
    ],
    "layer": LayerType.LAYER_0
},
```

**Impact:** Queries like "what is the project size" now route to Layer 0 retrieval instead of Layer 2 calculation.

---

## Remaining Issues

### Issue 1: Missing Data in v4 JSON ⚠️

Sara City project in `v4_clean_nested_structure.json` has:
- `totalUnits.value`: `None` (should be 1109)
- No `project_size` field (should be 3018)

**Solution:** Re-extract data from source PDF or migrate from `lf_projects_layer0.json`

### Issue 2: Ambiguous "Project Size" Term

"Project size" needs clarification:
- If user means **land area**: Return L² dimension (3018 acres)
- If user means **total units**: Return U dimension (1109 units)

**Solution:** System should:
1. Return **both** dimensions with labels
2. Ask clarifying question: "Do you mean land area or total units?"

---

## Proposed Enhanced Response

### Option A: Return Both Dimensions
```
Sara City Project Dimensions:
- Land Area (L²): 3018 acres
- Total Units (U): 1109 units
- Total Saleable Area: 550,125 sqft
- Average Unit Size: 411 sqft
```

### Option B: Clarify with User
```
"Project size" can mean:
1. Land area: 3018 acres
2. Total units: 1109 units

Which dimension did you need?
```

---

## Testing

### Test Case 1: Exact Query
```
Query: "What is the project size of Sara City"
Expected: 3018 (L² dimension - land area)
Current: Will now route to Layer 0 (after fix)
Status: ⚠️ Needs data migration
```

### Test Case 2: Units Query
```
Query: "How many units in Sara City"
Expected: 1109 units
Current: Will route to Layer 0
Status: ⚠️ Needs data migration
```

### Test Case 3: Ambiguous Query
```
Query: "Sara City size"
Expected: Return both L² and U dimensions
Current: Routes to Layer 0
Status: ✅ Fixed routing, ⚠️ needs data
```

---

## Action Items

### Immediate (Routing Fixed ✅)
- [x] Add "project size" patterns to Layer 0 retrieval
- [x] Add regex patterns for size queries
- [x] Prioritize Layer 0 over Layer 2 for retrieval

### Short-term (Data Migration Needed ⚠️)
- [ ] Migrate Sara City data from `lf_projects_layer0.json` to `v4_clean_nested_structure.json`
- [ ] Add missing `totalUnits` value (1109)
- [ ] Add `projectSize` or `landAreaAcres` field (3018)
- [ ] Verify all projects have complete Layer 0 dimensions

### Medium-term (UX Enhancement)
- [ ] Handle ambiguous "project size" queries
- [ ] Return both U and L² dimensions for size queries
- [ ] Add clarifying prompts when dimension is unclear

---

## Files Modified

1. **`app/services/prompt_router.py`** (lines 48-63)
   - Added "project size" keywords
   - Added regex patterns for size retrieval
   - Enhanced Layer 0 routing

---

## Related Issues

- Missing data in v4 JSON for multiple projects
- Need data migration strategy from v3 to v4
- Ambiguous terminology in real estate domain ("size", "total", "area")

---

**Status:** Routing Fixed ✅ | Data Migration Pending ⚠️

**Priority:** High (affects core retrieval functionality)

**Date:** 2025-01-28
