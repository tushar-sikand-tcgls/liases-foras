# Knowledge Graph Enrichment Visualization - Changes Summary

## Date: 2026-02-25

## Overview
Modified the knowledge graph visualization to include ALL enriched data from the Kolkata JSON file as separate nodes, specifically the nested `unitMixBreakdown` and `priceRangeDistribution` attributes.

## Files Modified

### 1. `/Users/tusharsikand/Documents/Projects/liases-foras/app/services/knowledge_graph_service.py`

**Method Modified:** `get_graph_visualization_data` (lines 266-525)

**Changes Made:**
- Added new logic after L1 attribute handling (around line 391-462) to process nested list enrichments
- Created new node type: `L1_Enrichment` with purple color (#9C27B0)
- For each item in `unitMixBreakdown` and `priceRangeDistribution` lists:
  - Creates a unique enrichment node with all nested attributes
  - Extracts meaningful labels (flat type or price range)
  - Stores all nested attributes with their values, units, and dimensions
  - Creates edges from project to enrichment nodes
  - Creates edges from enrichment nodes to relevant L0 dimensions

**New Node Type:**
```python
{
    "id": "{proj_id}_{enrichment_type}_{index}",
    "label": "1BHK" or "20 Lac - 30 Lac",
    "type": "L1_Enrichment",
    "enrichmentType": "unit_mix" or "price_range",
    "layer": 1,
    "group": 1,
    "size": 18,
    "color": "#9C27B0",  # Purple
    # Plus all nested attributes as sub-objects
}
```

**New Edge Types:**
- `HAS_UNIT_MIX`: Project → Unit Mix Enrichment (Light purple #E1BEE7)
- `HAS_PRICE_RANGE`: Project → Price Range Enrichment (Light purple #E1BEE7)
- `CONTAINS_DIMENSION`: Enrichment → L0 Dimension (Medium purple #BA68C8)

**Stats Updated:**
Added new statistics to track enrichment nodes:
- `l1_enrichments`: Total enrichment nodes
- `l1_unit_mix`: Count of unit mix nodes
- `l1_price_range`: Count of price range nodes

**Docstring Updated:**
Updated method documentation to reflect new L1_Enrichment node type and purple color coding.

### 2. `/Users/tusharsikand/Documents/Projects/liases-foras/app/config/__init__.py`

**Lines Modified:** 32-37

**Change:**
```python
# BEFORE:
"Kolkata": {
    "data_file": "extracted/kolkata/kolkata_v4_format.json",
    "format": "v4_nested",
    "regions": ["Kolkata"],
    "default_region": "Kolkata"
}

# AFTER:
"Kolkata": {
    "data_file": "extracted/kolkata/kolkata_v4_enriched.json",  # Enriched: unitMixBreakdown + priceRangeDistribution (960KB)
    "format": "v4_nested_enriched",
    "regions": ["New Town", "Rajarhat", "E-M Bypass", "Salt Lake", "Park Street"],
    "default_region": "New Town"
}
```

**Reason:**
The config was pointing to `kolkata_v4_format.json` which doesn't contain the enriched data. Changed to `kolkata_v4_enriched.json` which has the full `unitMixBreakdown` (31 items per project) and `priceRangeDistribution` (37 items per project) data.

## Results

### Before Changes:
- **Total Nodes:** 74
  - 4 L0 Dimensions
  - 5 Projects
  - 65 L1 Attributes
  - 0 Enrichments
- **Total Edges:** 115

### After Changes:
- **Total Nodes:** 424 (5.7× increase)
  - 4 L0 Dimensions
  - 5 Projects
  - 75 L1 Attributes
  - **340 L1 Enrichments** ← NEW!
    - 155 Unit Mix nodes (31 per project)
    - 185 Price Range nodes (37 per project)
- **Total Edges:** 1,485 (12.9× increase)
  - 75 HAS_L1_ATTRIBUTE
  - 155 HAS_UNIT_MIX ← NEW!
  - 185 HAS_PRICE_RANGE ← NEW!
  - 1,020 CONTAINS_DIMENSION ← NEW!
  - 50 IS

## Enrichment Data Structure

### Unit Mix Breakdown Node Example:
```json
{
  "id": "proj_127557_unit_mix_1",
  "label": "1BHK",
  "type": "L1_Enrichment",
  "enrichmentType": "unit_mix",
  "flatType": {"value": "1BHK", "unit": "text", "dimension": "I"},
  "saleableMinSize": {"value": 259.0, "unit": "sqft", "dimension": "L²"},
  "saleableMaxSize": {"value": 445.0, "unit": "sqft", "dimension": "L²"},
  "minCost": {"value": 10.13, "unit": "lacs", "dimension": "C"},
  "maxCost": {"value": 16.37, "unit": "lacs", "dimension": "C"},
  "annualSalesUnits": {"value": 9.0, "unit": "count", "dimension": "U"},
  "unsoldUnits": {"value": 3.0, "unit": "count", "dimension": "U"},
  "productEfficiency": {"value": 77.0, "unit": "percent", "dimension": "None"}
}
```

### Price Range Distribution Node Example:
```json
{
  "id": "proj_127557_price_range_2",
  "label": "20 Lac - 30 Lac",
  "type": "L1_Enrichment",
  "enrichmentType": "price_range",
  "priceRange": {"value": "20 Lac - 30 Lac", "unit": "text", "dimension": "C"},
  "annualSalesUnits": {"value": 1151.0, "unit": "count", "dimension": "U"},
  "unsoldUnits": {"value": 2283.0, "unit": "count", "dimension": "U"},
  "monthsInventory": {"value": 20.0, "unit": "months", "dimension": "T"}
}
```

## Testing

Created test script: `/Users/tusharsikand/Documents/Projects/liases-foras/test_enriched_visualization.py`

**Test Results:**
- ✓ Graph has 424 nodes (expected ≥ 300)
- ✓ Found 340 enrichment nodes
- ✓ All enrichment nodes have proper structure with nested attributes
- ✓ Edges correctly connect projects → enrichments → dimensions

## Visual Representation

The graph now shows:
1. **L0 Dimensions** (Gray, center): U, L², T, C
2. **Projects** (Yellow): 5 Kolkata projects
3. **L1 Attributes** (Green): Regular project attributes
4. **L1 Enrichments** (Purple): NEW - Unit mix and price range breakdowns
5. **L2 Metrics** (Orange): Calculated metrics (if present)

## Impact

This enhancement provides:
- **Granular visibility** into unit type distributions across projects
- **Detailed price range** analysis showing sales velocity and inventory
- **Dimensional relationships** preserved at enrichment level
- **Scalable structure** that can easily add more enrichment types
- **Rich data** for market analysis and comparison

## Future Enhancements

Potential additions:
- Distance range analysis enrichments
- Builder/developer enrichments
- Historical trend enrichments
- Competitive comparison enrichments

---

**Modified by:** Claude Code
**Date:** 2026-02-25
**Test Status:** ✓ Passing
