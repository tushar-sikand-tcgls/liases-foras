# NON-LLM Architecture: L0 → L1 → L2 → Rules → L3

## Overview

The knowledge graph uses a **deterministic, rule-based system** for all data processing and insights generation. **LLM is ONLY used for recommendations** on "Okay" and "Bad" metrics.

```
┌────────────────────────────────────────────────────────────┐
│ L0: Base Dimensions (Center)                               │
│ ─────────────────────────────────────────────────────────  │
│ U (Units), L² (Space), T (Time), C (Cash Flow)            │
└────────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ L1: Raw Data from PDF (Inner Ring)                         │
│ ─────────────────────────────────────────────────────────  │
│ • Extraction: PDF → Nested JSON (NON-LLM)                 │
│ • Format: {value, unit, dimension, relationships}         │
│ • Examples: soldPct, currentPricePSF, totalSupplyUnits    │
└────────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ L2: Calculated Financial Metrics (Middle Ring)             │
│ ─────────────────────────────────────────────────────────  │
│ • Calculation: Deterministic formulas (NON-LLM)           │
│ • Metrics: NPV, IRR, ROI, Payback Period, etc            │
│ • Input: L1 attributes + industry assumptions             │
│ • Output: Nested format with calculation details          │
└────────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ Rules: Threshold Configuration                             │
│ ─────────────────────────────────────────────────────────  │
│ • File: data/config/metric_rules.json                      │
│ • Format: {metric: {Excellent: {...}, Okay: {...}, Bad}}  │
│ • Example: NPV > ₹100 Cr = Excellent                      │
│ • Configurable: Can be updated via UI (future)            │
└────────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ L3: Non-LLM Insights (Outer Ring)                          │
│ ─────────────────────────────────────────────────────────  │
│ • Engine: Rule-based evaluation (NON-LLM)                 │
│ • Process: Apply thresholds → Classify as E/O/B           │
│ • Output: Simple insights like "NPV is Bad"              │
│ • Pre-calculated: Generated during data extraction         │
└────────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ AI-Play: LLM Recommendations (Runtime Only)                │
│ ─────────────────────────────────────────────────────────  │
│ • Trigger: User asks question                             │
│ • Input: L3 insights marked as "Okay" or "Bad"           │
│ • LLM Task: Generate actionable recommendations           │
│ • Excellent metrics: NO recommendations needed             │
└────────────────────────────────────────────────────────────┘
```

---

## Detailed Layer Breakdown

### L0: Base Dimensions (Conceptual Center)

**Purpose**: Define the fundamental dimensional units inspired by physics

| Dimension | Name | Description | Unit | Analogy |
|-----------|------|-------------|------|---------|
| **U** | Units | Count of housing units | count | Mass |
| **L²** | Space | Area in sqft/sqm | sqft | Length² |
| **T** | Time | Months/years | months | Time |
| **C** | Cash Flow | INR revenue/cost | INR | Current |

**Implementation**: Defined in `app/services/knowledge_graph_service.py`

**Characteristics**:
- ✅ Immutable conceptual definitions
- ✅ All L1 and L2 attributes link to these via relationships
- ✅ Non-LLM (just definitions)

---

### L1: Raw Data from PDF

**Purpose**: Extract and structure data from PDF with explicit dimensional relationships

**Process**:
1. PDF → pdfplumber extraction
2. Parse tables and create nested structure
3. Assign dimensions using DimensionParser
4. Generate explicit relationships (IS, NUMERATOR, DENOMINATOR, INVERSE_OF)

**Output Format**:
```json
{
  "currentPricePSF": {
    "value": 3996.0,
    "unit": "INR/sqft",
    "dimension": "C/L²",
    "relationships": [
      {"type": "NUMERATOR", "target": "C"},
      {"type": "DENOMINATOR", "target": "L²"}
    ],
    "source": "LF_PDF_Page2",
    "isPure": false,
    "layer": "L1"
  }
}
```

**Example L1 Attributes**:
- `totalSupplyUnits` (U) - IS → U
- `soldPct` (Dimensionless) - Percentage sold
- `currentPricePSF` (C/L²) - NUMERATOR: C, DENOMINATOR: L²
- `monthlySalesVelocity` (Fraction/T) - INVERSE_OF → T
- `annualSalesValueCr` (C) - IS → C

**Implementation**: `scripts/v4_extract_nested_pdf_data.py`

**Characteristics**:
- ✅ Fully deterministic extraction
- ✅ No LLM involved
- ✅ All relationships explicit

---

### L2: Calculated Financial Metrics

**Purpose**: Calculate advanced financial metrics from L1 data using deterministic formulas

**Calculator**: `app/calculators/layer2_calculator.py`

**Metrics Calculated** (NON-LLM):

| Metric | Formula | Dimension | Calculation Method |
|--------|---------|-----------|-------------------|
| **NPV** | Σ(CF_t / (1+r)^t) - I₀ | C | Discounted cash flow |
| **IRR** | r where NPV(r) = 0 | Fraction/T | Newton-Raphson method |
| **ROI** | (Revenue - Cost) / Cost × 100 | Dimensionless | Simple ratio |
| **Payback Period** | Cost / Annual Cash Flow | T | Division |
| **Profitability Index** | (NPV + I₀) / I₀ | Dimensionless | Ratio |
| **Absorption Rate** | (Sold% / Duration) × 100 | Fraction/T | Rate calculation |

**Assumptions**:
- Construction cost: ₹2000/sqft
- Discount rate: 12%
- Land cost: ₹30 Cr/acre

**Output Format**: Same nested structure as L1

**Implementation Process**:
1. Load L1 data
2. Extract required values using helper methods
3. Apply mathematical formulas
4. Return nested format with calculation details

**Characteristics**:
- ✅ Pure mathematical calculations
- ✅ No LLM involved
- ✅ Transparent formulas (included in output)

---

### Rules: Threshold Configuration

**Purpose**: Define Excellent/Okay/Bad thresholds for all L1 and L2 metrics

**File**: `data/config/metric_rules.json`

**Structure**:
```json
{
  "L2_metrics": {
    "npvCr": {
      "metric_name": "Net Present Value",
      "unit": "INR Crore",
      "dimension": "C",
      "thresholds": {
        "Excellent": {"min": 100, "max": 1000000, "description": "> ₹100 Cr NPV"},
        "Okay": {"min": 0, "max": 100, "description": "0 to ₹100 Cr NPV"},
        "Bad": {"min": -1000000, "max": 0, "description": "Negative NPV"}
      }
    }
  }
}
```

**Example Rules**:

| Metric | Excellent | Okay | Bad |
|--------|-----------|------|-----|
| **NPV** | > ₹100 Cr | 0 to ₹100 Cr | Negative |
| **IRR** | ≥ 18% | 12-18% | < 12% |
| **ROI** | ≥ 50% | 20-50% | < 20% |
| **Sold %** | ≥ 80% | 50-80% | < 50% |
| **Sales Velocity** | ≥ 5%/month | 2-5%/month | < 2%/month |

**Configurable**: Can be updated via UI in future (one-time configuration)

**Characteristics**:
- ✅ Simple threshold comparisons
- ✅ No LLM involved
- ✅ User-configurable

---

### L3: Non-LLM Insights Engine

**Purpose**: Apply rules to L1+L2 metrics to generate Excellent/Okay/Bad insights

**Engine**: `app/services/layer3_insights_engine.py`

**Process**:
1. Load rules configuration
2. For each L1/L2 metric, check value against thresholds
3. Classify as Excellent/Okay/Bad
4. Flag Okay/Bad metrics for LLM recommendations
5. Generate summary statistics

**Output Format**:
```json
{
  "L2_insights": [
    {
      "metric": "npvCr",
      "metric_name": "Net Present Value",
      "value": -89839.4,
      "unit": "INR Crore",
      "evaluation": "Bad",
      "description": "Negative NPV",
      "requires_llm_recommendation": true,
      "layer": "L2"
    }
  ],
  "summary": {
    "excellent_count": 1,
    "okay_count": 2,
    "bad_count": 5,
    "overall_health": "Bad",
    "needs_llm_recommendations": ["npvCr", "irrPct", ...]
  }
}
```

**Characteristics**:
- ✅ Rule-based threshold evaluation
- ✅ No LLM involved
- ✅ Pre-calculated during data extraction
- ✅ Instant retrieval (no runtime calculation)

---

## AI-Play: LLM Recommendations (Runtime)

**When**: User asks questions about a project

**Trigger**: Metrics evaluated as "Okay" or "Bad" in L3

**LLM Task**: Generate actionable recommendations ONLY for non-Excellent metrics

**Example Flow**:

```
User: "What can I do to improve Sara City?"

1. Retrieve L3 insights (NON-LLM, pre-calculated)
2. Identify metrics needing recommendations:
   - NPV: Bad (-₹89,839 Cr)
   - IRR: Bad (-23.27%)
   - ROI: Bad (-99.8%)
   - Absorption Rate: Bad (4.43%/year)
   
3. LLM generates recommendations:
   "Your project has several critical issues:
   
   1. NPV is severely negative (-₹89,839 Cr):
      → Review land cost assumptions (seems inflated)
      → Consider phased development
      → Explore joint ventures
   
   2. IRR is negative (-23.27%):
      → Reduce project timeline
      → Increase pricing (currently ₹3,996/sqft is Okay)
      → Improve sales velocity
   
   3. Absorption Rate is low (4.43%/year vs target 40%):
      → Enhance marketing
      → Offer early bird incentives
      → Review pricing strategy"
```

**Key Principles**:
- ✅ LLM NEVER generates insights - only recommendations
- ✅ Insights are always pre-calculated (L3 engine)
- ✅ Excellent metrics don't get LLM recommendations
- ✅ LLM has full context (L1 + L2 + L3) for recommendations

---

## Data Pipeline: Pre-Population

**Complete Pipeline** (runs during data extraction):

```
1. Extract PDF
   ├─ Parse tables
   ├─ Create nested L1 attributes
   └─ Assign dimensions and relationships
   
2. Calculate L2 Metrics (for ALL projects)
   ├─ Run financial formulas
   ├─ Generate nested L2 attributes
   └─ Include calculation details
   
3. Generate L3 Insights (for ALL projects)
   ├─ Load rules configuration
   ├─ Apply thresholds to L1+L2
   ├─ Classify as Excellent/Okay/Bad
   └─ Flag metrics needing recommendations
   
4. Save to JSON
   └─ Single file with L0+L1+L2+L3 complete
```

**Script**: `scripts/v4_extract_nested_pdf_data.py`

**Output**: `data/extracted/v4_clean_nested_structure.json`

**Benefits**:
- ✅ All insights pre-calculated (instant retrieval)
- ✅ No runtime computation overhead
- ✅ Single source of truth
- ✅ Easy to version control

---

## API Endpoints

### GET /api/projects
List all projects with summary data

### GET /api/projects/{id}
Get complete project data (L1 + L2 + L3)

### GET /api/projects/{id}/l2-metrics
Get L2 calculated metrics (NON-LLM)

**Response**:
```json
{
  "projectId": "3306.0",
  "projectName": "Sara City",
  "l2_metrics": {
    "npvCr": {...},
    "irrPct": {...},
    ...
  },
  "note": "All metrics calculated using deterministic formulas (NON-LLM)"
}
```

### GET /api/projects/{id}/insights
Get L3 insights (NON-LLM)

**Response**:
```json
{
  "projectId": "3306.0",
  "projectName": "Sara City",
  "insights": {
    "L1_insights": [...],
    "L2_insights": [...],
    "summary": {
      "excellent_count": 1,
      "okay_count": 2,
      "bad_count": 5,
      "overall_health": "Bad",
      "needs_llm_recommendations": [...]
    }
  },
  "note": "All insights generated using NON-LLM rule-based thresholds"
}
```

### POST /api/data/refresh
Trigger complete data refresh (L0 → L1 → L2 → L3)

---

## Testing the Complete System

```python
# Test script
from app.services.data_service import data_service
from app.calculators.layer2_calculator import layer2_calculator
from app.services.layer3_insights_engine import layer3_engine

# Get project (L1)
sara = data_service.get_project_by_name("Sara City")

# Calculate L2
l2_metrics = layer2_calculator.calculate_all_metrics(sara)

# Generate L3 insights
insights = layer3_engine.generate_project_insights(sara, l2_metrics)

# Check summary
print(f"Excellent: {insights['summary']['excellent_count']}")
print(f"Okay: {insights['summary']['okay_count']}")
print(f"Bad: {insights['summary']['bad_count']}")
print(f"Needs LLM: {insights['summary']['needs_llm_recommendations']}")
```

---

## Summary

### What is NON-LLM

- **L0**: Dimension definitions ✅
- **L1**: PDF extraction ✅
- **L2**: Financial calculations ✅
- **Rules**: Threshold configuration ✅
- **L3**: Insight generation ✅

### What Uses LLM

- **Recommendations**: Only for "Okay" and "Bad" metrics ⚠️
- **Trigger**: User asks questions at runtime
- **Input**: Pre-calculated L3 insights
- **Output**: Actionable recommendations

### Key Benefits

1. **Fast**: All insights pre-calculated, instant retrieval
2. **Transparent**: All formulas and thresholds visible
3. **Configurable**: Rules can be updated via UI
4. **Deterministic**: Same input → same output
5. **Cost-effective**: LLM only for recommendations, not insights
6. **Offline-capable**: Core functionality works without LLM

---

**Architecture Version**: 1.0.0  
**Last Updated**: 2025-11-30  
**Author**: Claude Code
