# Missing Attributes to Add to Knowledge Base

**Date:** December 5, 2025
**Status:** 📋 **ACTION REQUIRED - 10 Attributes Missing**

---

## Overview

To achieve >= 80% pass rate in comprehensive testing, these **10 Layer 1 attributes** need to be added to `enriched_layers_knowledge.json`.

Each entry includes:
- Formula from Excel
- Keywords from Excel prompt variations
- Recommended patterns for routing
- Sample test cases that are currently failing

---

## 1. Price Growth (%)

**Formula (from Excel):** `((Current PSF - Launch PSF) / Launch PSF) × 100`

**Dimension:** Dimensionless (%)

**Keywords:** price growth, price appreciation, price increase, appreciation percentage

**Prompt Variations (from Excel):**
- "What is price appreciation?"
- "% price growth?"
- "How much have prices increased?"
- "Tell me the percentage price increase from launch till now"

**Sample Failing Test:**
```
Query: "What is price appreciation? for Sara City"
Current: Returns "3018 Units" (hardcoded)
Expected: Returns calculated % (e.g., "22.5 %")
```

**Knowledge Base Entry Needed:**
```json
{
  "target_attribute": "Price Growth (%)",
  "requires_calculation": true,
  "dimension": "-",
  "unit": "%",
  "formula": "((Current PSF - Launch PSF) / Launch PSF) × 100",
  "description": "Percentage price appreciation from launch to current",
  "variation_in_prompt": "What is price appreciation? | % price growth? | How much have prices increased? | Tell me the percentage price increase from launch till now",
  "example": "((3996 - 3200) / 3200) × 100 = 24.88%"
}
```

---

## 2. Monthly Velocity (Units)

**Formula (from Excel):** `Annual Sales / 12` OR `Monthly Units Sold`

**Dimension:** U/T (Units/month)

**Keywords:** monthly velocity, monthly sales, monthly absorption, units per month

**Prompt Variations (from Excel):**
- "What is monthly velocity?"
- "Monthly sales rate"
- "Units absorbed per month"

**Sample Failing Test:**
```
Query: "What is monthly velocity? for Sara City"
Current: Returns "3018 Units" (hardcoded)
Expected: Returns "43.92 Units/month" (527 / 12)
```

**Knowledge Base Entry Needed:**
```json
{
  "target_attribute": "Monthly Velocity (Units)",
  "requires_calculation": true,
  "dimension": "U/T",
  "unit": "Units/month",
  "formula": "Annual Sales / 12",
  "description": "Average monthly unit sales velocity",
  "variation_in_prompt": "What is monthly velocity? | Monthly sales rate | Units absorbed per month",
  "example": "527 / 12 = 43.92 Units/month"
}
```

---

## 3. Effective Realised PSF

**Formula (from Excel):** `Total Revenue / (Total Supply × Avg Unit Size)` OR `Realised PSF weighted by sold units`

**Dimension:** C/L² (₹/sqft)

**Keywords:** effective PSF, realized PSF, actual PSF, weighted PSF

**Prompt Variations (from Excel):**
- "What is effective realised PSF?"
- "Actual PSF realized"
- "Weighted average PSF"

**Sample Failing Test:**
```
Query: "What is effective realised PSF? for Sara City"
Current: Returns "3018 Units" (hardcoded)
Expected: Returns calculated PSF (e.g., "3850 ₹/sqft")
```

**Knowledge Base Entry Needed:**
```json
{
  "target_attribute": "Effective Realised PSF",
  "requires_calculation": true,
  "dimension": "C/L²",
  "unit": "₹/sqft",
  "formula": "(Annual Sales Value × Avg Unit Size) / (Sold Units × Avg Unit Size)",
  "description": "Weighted average PSF based on actual sales",
  "variation_in_prompt": "What is effective realised PSF? | Actual PSF realized | Weighted average PSF",
  "example": "Calculated from actual sales revenue per sqft"
}
```

---

## 4. Cumulative Possession Progress (%)

**Formula (from Excel):** `((Today - Launch Date) / (Possession Date - Launch Date)) × 100`

**Dimension:** Dimensionless (%)

**Keywords:** possession progress, construction progress, project timeline progress, completion percentage

**Prompt Variations (from Excel):**
- "What is cumulative possession progress?"
- "How far along is the project?"
- "Construction progress %"

**Sample Failing Test:**
```
Query: "What is cumulative possession progress? for Sara City"
Current: Returns "3018 Units" (hardcoded)
Expected: Returns "85 %" (project is 85% through timeline)
```

**Knowledge Base Entry Needed:**
```json
{
  "target_attribute": "Cumulative Possession Progress (%)",
  "requires_calculation": true,
  "dimension": "-",
  "unit": "%",
  "formula": "((Today - Launch Date) / (Possession Date - Launch Date)) × 100",
  "description": "Percentage completion of project timeline",
  "variation_in_prompt": "What is cumulative possession progress? | How far along is the project? | Construction progress %",
  "example": "If launched 2007, possession 2027, today 2025: ((2025-2007)/(2027-2007))×100 = 90%"
}
```

---

## 5. Revenue Concentration (%)

**Formula (from Excel):** `(Top 3 Unit Type Revenue / Total Revenue) × 100` OR `Revenue from largest unit type / Total Revenue`

**Dimension:** Dimensionless (%)

**Keywords:** revenue concentration, revenue distribution, top unit revenue, revenue breakdown

**Prompt Variations (from Excel):**
- "What is revenue concentration?"
- "Revenue distribution by unit type"
- "Top revenue contributors"

**Sample Failing Test:**
```
Query: "What is revenue concentration? for Sara City"
Current: Returns "3018 Units" (hardcoded)
Expected: Returns "75 %" (75% of revenue from top 3 unit types)
```

**Knowledge Base Entry Needed:**
```json
{
  "target_attribute": "Revenue Concentration (%)",
  "requires_calculation": true,
  "dimension": "-",
  "unit": "%",
  "formula": "(Revenue from Top Unit Type / Total Revenue) × 100",
  "description": "Percentage of revenue from dominant unit types",
  "variation_in_prompt": "What is revenue concentration? | Revenue distribution by unit type | Top revenue contributors",
  "example": "If 2BHK generates 60Cr of 80Cr total: (60/80)×100 = 75%"
}
```

---

## 6. Price Growth Rate (% per Year)

**Formula (from Excel):** `Price Growth % / Project Age (Years)`

**Dimension:** T⁻¹ (%/year)

**Keywords:** price growth rate, annual appreciation, yearly price increase, CAGR

**Prompt Variations (from Excel):**
- "What is price growth rate?"
- "Annual appreciation rate"
- "Yearly price increase %"

**Sample Failing Test:**
```
Query: "What is price growth rate? for Sara City"
Current: Returns "3018 Units" (hardcoded)
Expected: Returns "1.38 %/year" (24.88% / 18 years)
```

**Knowledge Base Entry Needed:**
```json
{
  "target_attribute": "Price Growth Rate (% per Year)",
  "requires_calculation": true,
  "dimension": "T⁻¹",
  "unit": "%/year",
  "formula": "Price Growth (%) / Project Age (Years)",
  "description": "Annualized price appreciation rate",
  "variation_in_prompt": "What is price growth rate? | Annual appreciation rate | Yearly price increase %",
  "example": "If 24.88% growth over 18 years: 24.88/18 = 1.38%/year"
}
```

---

## 7. Inventory Turnover Days

**Formula (from Excel):** `Months of Inventory × 30`

**Dimension:** T (Days)

**Keywords:** inventory turnover, days of inventory, inventory days, turnover period

**Prompt Variations (from Excel):**
- "What is inventory turnover in days?"
- "Days of inventory"
- "Inventory turnover period"

**Sample Failing Test:**
```
Query: "What is inventory turnover in days? for Sara City"
Current: Returns "3018 Units" (hardcoded)
Expected: Returns "83.3 Days" (2.78 months × 30)
```

**Knowledge Base Entry Needed:**
```json
{
  "target_attribute": "Inventory Turnover Days",
  "requires_calculation": true,
  "dimension": "T",
  "unit": "Days",
  "formula": "Months of Inventory × 30",
  "description": "Time to clear remaining inventory in days",
  "variation_in_prompt": "What is inventory turnover in days? | Days of inventory | Inventory turnover period",
  "example": "2.78 months × 30 = 83.3 days"
}
```

---

## 8. Margin per Unit (Approx)

**Formula (from Excel):** `(Current PSF - Cost PSF) × Avg Unit Size`

**Dimension:** C (₹)

**Keywords:** margin per unit, unit margin, profit per unit, unit profitability

**Prompt Variations (from Excel):**
- "What is margin per unit?"
- "Profit per unit"
- "Unit profitability"

**Sample Failing Test:**
```
Query: "What is margin per unit? for Sara City"
Current: Returns "3018 Units" (hardcoded)
Expected: Returns "15.5 Lakh" per unit margin
```

**Knowledge Base Entry Needed:**
```json
{
  "target_attribute": "Margin per Unit (Approx)",
  "requires_calculation": true,
  "dimension": "C",
  "unit": "₹ Lakh",
  "formula": "(Current PSF - Cost PSF) × Avg Unit Size / 100000",
  "description": "Approximate profit margin per unit sold",
  "variation_in_prompt": "What is margin per unit? | Profit per unit | Unit profitability",
  "example": "If PSF margin is 1000 and avg size is 1550 sqft: 1000×1550 = 15.5L"
}
```

**Note:** This requires `costPSF` field in data, which may not be available. Alternative formula: `Revenue per Unit - (Total Cost / Total Units)`

---

## 9. Remaining Project Timeline (Months)

**Formula (from Excel):** `MAX(Months to Sell Remaining, Time to Possession)`

**Dimension:** T (Months)

**Keywords:** remaining timeline, project timeline, time left, remaining duration

**Prompt Variations (from Excel):**
- "What is total remaining project timeline?"
- "Time till project is fully done"
- "Remaining timeline"

**Sample Failing Test:**
```
Query: "What is total remaining project timeline? for Sara City"
Current: Returns "3018 Units" (hardcoded)
Expected: Returns "24 Months" (MAX of sellout time vs possession time)
```

**Knowledge Base Entry Needed:**
```json
{
  "target_attribute": "Remaining Project Timeline (Months)",
  "requires_calculation": true,
  "dimension": "T",
  "unit": "Months",
  "formula": "MAX(Months to Sell Remaining × 12, Time to Possession)",
  "description": "Maximum time until project completion (sales or possession)",
  "variation_in_prompt": "What is total remaining project timeline? | Time till project is fully done | Remaining timeline",
  "example": "MAX(2.78 months, 24 months from today to possession) = 24 months"
}
```

---

## Implementation Steps

### Step 1: Add to `enriched_layers_knowledge.json`

Add each of the 10 attribute entries above to the `layer1_attributes` array in:
`/Users/tusharsikand/Documents/Projects/liases-foras/change-request/enriched-layers/enriched_layers_knowledge.json`

### Step 2: Add Formula Logic to `enriched_layers_service.py`

For each formula, ensure the calculation logic exists in:
`/Users/tusharsikand/Documents/Projects/liases-foras/app/services/enriched_layers_service.py`

**Example for Price Growth (%):**
```python
elif attr.target_attribute.lower() == 'price growth (%)':
    current_psf = data.get('current_psf', data.get('currentPSF'))
    launch_psf = data.get('launch_psf', data.get('launchPSF'))

    if not current_psf or not launch_psf:
        return None

    price_growth = ((current_psf - launch_psf) / launch_psf) * 100

    return {
        'value': price_growth,
        'unit': '%',
        'dimension': '-',
        'formula': '((Current PSF - Launch PSF) / Launch PSF) × 100'
    }
```

### Step 3: Re-run Tests

After adding all 10 attributes, run:
```bash
python3 test_l1_routing_and_precision.py
```

**Expected Result:**
- Pass rate: >= 80% (62/78 tests)
- Routing accuracy: >= 85% (66/78 tests)

---

## Priority Order

### High Priority (Easy to Implement):

1. **Inventory Turnover Days** - Simple: `MOI × 30`
2. **Monthly Velocity (Units)** - Simple: `Annual Sales / 12`
3. **Price Growth Rate** - Simple: `Price Growth / Project Age`

### Medium Priority (Moderate Complexity):

4. **Price Growth (%)** - Requires: Current PSF, Launch PSF
5. **Remaining Project Timeline** - Requires: MAX function
6. **Cumulative Possession Progress** - Requires: Date calculations

### Low Priority (Complex/Data Dependent):

7. **Effective Realised PSF** - May need weighted calculation
8. **Revenue Concentration (%)** - Needs unit type breakdown
9. **Margin per Unit** - Needs cost data (may not be available)

---

## Expected Impact

**Current State:**
- Pass Rate: 38.5% (30/78 tests)
- Working Attributes: 4/26 (15%)

**After Adding High Priority (3 attributes):**
- Pass Rate: ~50% (39/78 tests)
- Working Attributes: 7/26 (27%)

**After Adding All 10 Attributes:**
- Pass Rate: >= 80% (62/78 tests)
- Working Attributes: 14/26 (54%) fully working, rest partially

**After Enhancing Pattern Matching:**
- Pass Rate: >= 90% (70/78 tests)
- Working Attributes: 24/26 (92%) fully working

---

## Status: 📋 **ACTION REQUIRED**

**Next Steps:**
1. Add 10 missing attributes to `enriched_layers_knowledge.json`
2. Implement formula logic in `enriched_layers_service.py`
3. Re-run `test_l1_routing_and_precision.py`
4. Target: >= 80% pass rate

---

**Document Created:** December 5, 2025
**Priority:** HIGH
**Estimated Effort:** 2-4 hours
**Expected Outcome:** 80%+ pass rate on comprehensive tests
