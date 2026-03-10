# Enriched Layers Integration - Action Plan

**Date:** December 4, 2025
**Status:** 🔄 In Progress
**Issue:** "Sellout Time" returns "3018 Units" instead of calculated "2.1 years"

---

## 🔍 Problem Analysis

### Current Behavior (INCORRECT)
**User Query:** "What is sellout time for sara city"

**System Response:**
```
The result is 3018 Units.
Formula: Direct retrieval from Knowledge Graph (Layer 0)
Source: Liases Foras
```

**Issue:** System returns `projectSizeUnits` (3018) instead of calculating Sellout Time

---

### Expected Behavior (CORRECT)
**User Query:** "What is sellout time for sara city"

**Expected Response:**
```
The sellout time for Sara City is 2.1 years.

Formula: Supply / Annual Sales
Calculation: 1109 units / 527 units/year = 2.1 years
Source: Liases Foras (Layer 1 calculation)
```

---

## 📊 Root Cause Identification

### 1. Sara City Data (Verified)
```json
{
  "totalSupplyUnits": 1109,        // ← Supply
  "annualSalesUnits": 527,         // ← Annual Sales
  "projectSizeUnits": 3018         // ← WRONG VALUE being returned
}
```

**Correct Calculation:**
```
Sellout Time = Supply / Annual Sales
             = 1109 / 527
             = 2.1 years ✓
```

###2. System Architecture Gap

**Current Flow (BROKEN):**
```
User Query: "sellout time for sara city"
     ↓
[prompt_router.py]
     ↓ (doesn't recognize "sellout time")
[Falls back to Layer 0 retrieval]
     ↓
[Returns projectSizeUnits: 3018] ❌ WRONG
```

**Missing Components:**
1. ❌ `prompt_router.py` doesn't have "Sellout Time" in capability_patterns
2. ❌ No Layer 1 calculation logic for enriched attributes
3. ❌ No integration between enriched_layers_service and query execution

---

## ✅ What Has Been Created

### 1. Enriched Layers Knowledge Base (Completed)
**Location:** `change-request/enriched-layers/enriched_layers_knowledge.json`
- ✅ 67 attributes (41 Layer 0 + 26 Layer 1)
- ✅ Complete formulas, prompts, and examples
- ✅ Test suite with 100% pass rate (36/36 tests)

### 2. Enriched Layers Service (Completed)
**Location:** `app/services/enriched_layers_service.py`

**Features:**
- ✅ Loads all 67 enriched attributes from JSON
- ✅ Fast lookup by attribute name
- ✅ Prompt matching with confidence scoring
- ✅ Formula parsing and execution for Layer 1 calculations

**Test Results:**
```bash
✓ Loaded 41 Layer 0 attributes
✓ Loaded 26 Layer 1 attributes
✓ Found "Sellout Time" (Formula: Supply / Annual Sales)
✓ Prompt search for "what is sellout time" → 70% confidence match
✓ Calculation logic implemented for sellout time
```

---

## 🚀 Integration Steps (TODO)

### Step 1: Extend Prompt Router ⏳ IN PROGRESS
**File:** `app/services/prompt_router.py`

**Task:** Add all 26 Layer 1 attributes from enriched layers to `capability_patterns`

**Implementation:**
```python
# At the top of PromptRouter.__init__()
from app.services.enriched_layers_service import get_enriched_layers_service

# After existing capability_patterns
enriched_service = get_enriched_layers_service()
enriched_patterns = enriched_service.generate_capability_patterns()

# Merge with existing patterns
self.capability_patterns.update(enriched_patterns)
```

**Expected Outcome:**
- "Sellout Time" will be recognized as a Layer 1 capability
- Confidence score: 0.7 (based on prompt matching)
- Route to: `calculate_sellout_time` capability

---

### Step 2: Add Layer 1 Calculation Handler
**File:** `app/services/query_router.py` (or create new handler)

**Task:** When capability is an enriched Layer 1 attribute, execute calculation

**Implementation Option A (Modify existing router):**
```python
# In query_router.py route() method

# Check if this is an enriched Layer 1 attribute
enriched_service = get_enriched_layers_service()
attr_name = request.capability.replace('calculate_', '').replace('_', ' ').title()
attr = enriched_service.get_attribute(attr_name)

if attr and attr.requires_calculation:
    # Get project data
    project_data = self._get_project_data(request.context.get('project_name'))

    # Execute calculation
    result = enriched_service.execute_layer1_calculation(
        attr_name=attr.target_attribute,
        project_data=project_data
    )

    return result, provenance, lineage
```

**Implementation Option B (Create dedicated handler):**
```python
# Create app/services/enriched_calculator.py

class EnrichedLayerCalculator:
    def __init__(self):
        self.enriched_service = get_enriched_layers_service()

    def calculate(self, capability: str, project_name: str) -> Dict:
        """Execute enriched Layer 1 calculation"""
        # Extract attribute name from capability
        attr_name = self._parse_capability_name(capability)

        # Get attribute definition
        attr = self.enriched_service.get_attribute(attr_name)
        if not attr:
            raise ValueError(f"Attribute {attr_name} not found")

        # Get project data from Neo4j
        project_data = self._fetch_project_data(project_name)

        # Execute calculation
        result = self.enriched_service.execute_layer1_calculation(
            attr_name=attr.target_attribute,
            project_data=project_data
        )

        return self._format_response(result, attr, project_name)

    def _fetch_project_data(self, project_name: str) -> Dict:
        """Fetch required Layer 0 data from Neo4j"""
        # Query Neo4j for the project
        # Map field names to enriched layers expectations
        return {
            'supply': project['totalSupplyUnits'],
            'annual_sales': project['annualSalesUnits'],
            'sold_percent': project['soldPct'],
            'unsold_percent': project['unsoldPct'],
            'current_psf': project['currentPricePSF']['value'],
            'launch_psf': project['launchPricePSF']['value'],
            # ... map all Layer 0 fields
        }

    def _format_response(self, result: Dict, attr: EnrichedAttribute, project_name: str) -> Dict:
        """Format calculation result for API response"""
        return {
            'status': 'success',
            'project': project_name,
            'attribute': attr.target_attribute,
            'value': result['value'],
            'unit': result['unit'],
            'dimension': result['dimension'],
            'formula': result['formula'],
            'calculation_details': f"{result['formula']} = {result['value']} {result['unit']}",
            'layer': 1,
            'source': 'Enriched Layers (Layer 1 Calculation)',
            'provenance': {
                'dataSource': 'Liases Foras',
                'layer': 'Layer 1',
                'calculationMethod': result['formula']
            }
        }
```

---

### Step 3: Update Conversation API
**File:** `app/api/conversation.py`

**Task:** Route enriched Layer 1 queries to calculation handler

**Current Code (Line 133-144):**
```python
if user_msg.capability and user_msg.layer is not None:
    try:
        # Create MCP request from conversation context
        mcp_request = MCPQueryRequest(
            queryType="calculation",
            layer=user_msg.layer,
            capability=user_msg.capability,
            parameters=user_msg.parameters_extracted,
            context=execution_context
        )

        # Route to appropriate handler
        result_data, provenance, lineage = query_router.route(mcp_request)
```

**No Changes Needed** - query_router will handle the routing once Step 2 is complete

---

### Step 4: Test Sellout Time Query
**Test Case:** Sara City Sellout Time

**Test Command:**
```bash
curl -X POST http://localhost:8000/api/conversation/message \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session",
    "content": "What is sellout time for sara city"
  }'
```

**Expected Response:**
```json
{
  "assistant_response": "Based on the analysis, the sellout time for Sara City is 2.1 years",
  "result": {
    "attribute": "Sellout Time",
    "value": 2.1,
    "unit": "years",
    "dimension": "T",
    "formula": "Supply / Annual Sales",
    "calculation_details": "1109 / 527 = 2.1 years",
    "layer": 1,
    "source": "Enriched Layers (Layer 1 Calculation)"
  }
}
```

---

### Step 5: Validate All 26 Layer 1 Attributes
**Test File:** Create `tests/test_enriched_layer1_integration.py`

**Test Coverage:**
```python
import pytest

LAYER1_TESTS = [
    # (query, expected_attribute, expected_unit, project)
    ("what is sellout time for sara city", "Sellout Time", "years", "Sara City"),
    ("calculate months of inventory for sara city", "Months of Inventory", "months", "Sara City"),
    ("what's the price growth for sara city", "Price Growth (%)", "%", "Sara City"),
    ("show me realized psf for sara city", "Realised PSF", "INR/sqft", "Sara City"),
    # ... add all 26 Layer 1 attributes
]

@pytest.mark.parametrize("query,expected_attr,expected_unit,project", LAYER1_TESTS)
def test_layer1_calculation(query, expected_attr, expected_unit, project):
    """Test that Layer 1 queries calculate correctly"""
    response = send_query(query)

    assert response['status'] == 'success'
    assert response['result']['attribute'] == expected_attr
    assert response['result']['unit'] == expected_unit
    assert response['result']['layer'] == 1
    assert 'formula' in response['result']
    assert response['result']['value'] is not None
```

---

## 📋 Implementation Checklist

- [ ] **Step 1:** Extend prompt_router with enriched patterns (15 min)
  - [ ] Import enriched_layers_service
  - [ ] Generate capability patterns
  - [ ] Merge with existing patterns
  - [ ] Test prompt matching for "sellout time"

- [ ] **Step 2:** Create EnrichedLayerCalculator (30 min)
  - [ ] Create new file `app/services/enriched_calculator.py`
  - [ ] Implement calculate() method
  - [ ] Implement _fetch_project_data() with field mapping
  - [ ] Implement _format_response()
  - [ ] Test sellout time calculation directly

- [ ] **Step 3:** Integrate with query_router (15 min)
  - [ ] Add condition to check for enriched attributes
  - [ ] Call EnrichedLayerCalculator when detected
  - [ ] Return formatted result

- [ ] **Step 4:** Test Sara City Sellout Time (5 min)
  - [ ] Send query via API
  - [ ] Verify response shows "2.1 years"
  - [ ] Verify formula shown is "Supply / Annual Sales"
  - [ ] Verify calculation details are correct

- [ ] **Step 5:** Test all 26 Layer 1 attributes (1 hour)
  - [ ] Create test suite
  - [ ] Test each attribute with Sara City data
  - [ ] Validate prompt variations work
  - [ ] Document any issues

**Total Estimated Time:** ~2 hours

---

## 🐛 Known Issues & Considerations

### Issue 1: Field Name Mapping
**Problem:** Enriched layers use different field names than Neo4j

**Example:**
- Enriched layers expect: `supply`, `annual_sales`
- Neo4j returns: `totalSupplyUnits`, `annualSalesUnits`

**Solution:** Create field mapping in `_fetch_project_data()`:
```python
FIELD_MAPPING = {
    'supply': ['totalSupplyUnits', 'projectSizeUnits'],
    'annual_sales': ['annualSalesUnits', 'annualSales'],
    'sold_percent': ['soldPct'],
    'unsold_percent': ['unsoldPct'],
    'current_psf': ['currentPricePSF.value', 'currentPricePSF'],
    'launch_psf': ['launchPricePSF.value', 'launchPricePSF'],
    'size': ['unitSaleableSizeSqft.value', 'unitSaleableSizeSqft'],
    'value': ['annualSalesValueCr.value', 'annualSalesValueCr'],
    # ... add all field mappings
}
```

### Issue 2: Nested Field Access
**Problem:** Some Neo4j fields are nested (e.g., `currentPricePSF.value`)

**Solution:** Use safe nested access:
```python
def get_nested_value(data: Dict, path: str, default=None):
    """Safely get nested dictionary value"""
    keys = path.split('.')
    result = data
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key)
        else:
            return default
    return result if result is not None else default
```

### Issue 3: Unit Conversion
**Problem:** Some calculations need unit conversion (e.g., Cr to lakh)

**Solution:** Handle in formula execution:
```python
# Revenue per Unit should return lakh, not INR
if 'revenue per unit' in attr_name_lower:
    value_cr = data.get('value') or 0
    units = data.get('units') or 1
    return (value_cr * 1e7) / units / 1e5  # Convert to lakh
```

### Issue 4: Missing Data Handling
**Problem:** Some projects might not have all required fields

**Solution:** Graceful fallback with informative error:
```python
try:
    result = enriched_service.execute_layer1_calculation(...)
except Exception as e:
    return {
        'status': 'error',
        'message': f"Cannot calculate {attr_name}: {str(e)}",
        'required_fields': attr.formula_derivation,
        'available_fields': list(project_data.keys())
    }
```

---

## 📊 Testing Matrix

| Layer 1 Attribute | Test Query | Expected Result | Status |
|-------------------|-----------|-----------------|--------|
| Sellout Time | "sellout time for sara city" | 2.1 years | ⏳ Pending |
| Months of Inventory | "months of inventory" | 2.78 months | ⏳ Pending |
| Price Growth (%) | "price growth" | 81.63% | ⏳ Pending |
| Realised PSF | "realized psf" | 4860 INR/sqft | ⏳ Pending |
| Revenue per Unit | "revenue per unit" | 20.1 lakh | ⏳ Pending |
| Unsold Units | "unsold units" | 122 units | ⏳ Pending |
| Sold Units | "sold units" | 987 units | ⏳ Pending |
| Monthly Units Sold | "monthly sales" | 43.9 units/month | ⏳ Pending |
| Annual Clearance Rate | "clearance rate" | 47.5% | ⏳ Pending |
| PSF Gap | "psf gap" | 1796 INR/sqft | ⏳ Pending |
| ... | ... | ... | ... |
| **(26 total)** | | | |

---

## 🎯 Success Criteria

**Before:**
- ❌ "Sellout time for sara city" returns "3018 Units" (wrong)
- ❌ System treats as Layer 0 retrieval
- ❌ No calculation performed

**After:**
- ✅ "Sellout time for sara city" returns "2.1 years" (correct)
- ✅ System recognizes as Layer 1 calculation
- ✅ Formula shown: "Supply / Annual Sales = 1109 / 527"
- ✅ All 26 Layer 1 attributes work correctly
- ✅ Prompt variations match (e.g., "how long to sell all units")

---

## 📝 Next Immediate Actions

1. **Implement Step 1** (Extend prompt_router) - START HERE
2. **Implement Step 2** (Create EnrichedLayerCalculator)
3. **Test sellout time** - Verify it returns 2.1 years
4. **If successful**, proceed with full Layer 1 testing
5. **Document** any issues encountered

---

## 📞 Support Files Created

| File | Purpose | Status |
|------|---------|--------|
| `enriched_layers_knowledge.json` | 67 attributes with formulas | ✅ Complete |
| `enriched_layers_service.py` | Service for loading & calculations | ✅ Complete |
| `test_enriched_layers_calculations.py` | Unit tests (36/36 passing) | ✅ Complete |
| `ENRICHED_LAYERS_REFERENCE.md` | Complete documentation | ✅ Complete |
| `INTEGRATION_ACTION_PLAN.md` | This file | ✅ Complete |

---

**Status:** Ready for integration. All groundwork complete.
**Next:** Implement Step 1 (extend prompt_router) to enable enriched Layer 1 calculations.
