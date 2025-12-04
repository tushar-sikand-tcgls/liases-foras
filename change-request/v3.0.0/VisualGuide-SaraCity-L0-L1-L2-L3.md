# Visual Guide: Sara City Through L0-L1-L2-L3 Layers

## Complete Data Flow Visualization

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                    SARA CITY PROJECT (ID: 3306)                          ║
║                    Complete Layer Analysis                               ║
╚═══════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────┐
│ L0: DIMENSIONAL SCHEMA (Immutable Foundation)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────┐  ┌──────────┐  ┌────────┐  ┌──────────┐                      │
│  │ U       │  │ L²       │  │ T      │  │ C        │                      │
│  │ Units   │  │ Area     │  │ Time   │  │ Cash     │                      │
│  │ (count) │  │ (sqft)   │  │ (date) │  │ (INR)    │                      │
│  │ count   │  │ float    │  │ date   │  │ float    │                      │
│  │ 0-∞     │  │ 0-∞      │  │ any    │  │ 0-∞      │                      │
│  │ Mass    │  │ Length² │  │ Time   │  │ Current  │                      │
│  └─────────┘  └──────────┘  └────────┘  └──────────┘                      │
│                                                                             │
│  These 4 dimensions NEVER CHANGE. They are the foundation for everything.│
│  All L1, L2, L3 values are expressions of these dimensions.               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
                        (L1 data tagged with L0 dims)
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ L1: PROJECT ATTRIBUTES (Actual Data from LF)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ProjectName              Label                 "Sara City"               │
│  ─────────────────────────────────────────────────────────────────────    │
│  totalUnits               3018 U                (dimension: U)            │
│  unsoldUnits             334 U                  (dimension: U)            │
│  soldUnits               2684 U                 (dimension: U)            │
│  ─────────────────────────────────────────────────────────────────────    │
│  unitSaleableSize        411 L²                 (dimension: L²)           │
│  totalSaleableArea       1,241,298 L²           (dimension: L²)           │
│  ─────────────────────────────────────────────────────────────────────    │
│  launchDate              2007-11-01 T           (dimension: T)            │
│  possessionDate          2027-12-31 T           (dimension: T)            │
│  projectDurationMonths   240 T                  (dimension: T)            │
│  ─────────────────────────────────────────────────────────────────────    │
│  launchPrice_PSF         2,200 C/L²             (dimension: C/L²)         │
│  currentPrice_PSF        3,996 C/L²             (dimension: C/L²)         │
│  annualSalesValue        ₹106 Cr C/T            (dimension: C/T)          │
│                                                                             │
│  Key Point: These are PURE DATA VALUES from LF. No calculation.           │
│  Each has a dimension tag. Together they form the "attributes" of Sara    │
│  City, like columns in a database table.                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
                  (Auto-calculated using L0 dimensional algebra)
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ L2: DERIVED METRICS (Calculated Automatically)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  METRIC 1: Absorption Rate (AR)                                           │
│  ─────────────────────────────                                            │
│  Formula:        (Sold / Total) / Months                                  │
│                = (2684 U / 3018 U) / 240 T                                │
│                = (dimensionless fraction) / T                             │
│                = Fraction/T (percent per month)                           │
│  Calculation:    0.8892 / 240 = 0.0037 = 0.37% per month                 │
│  Status:         ✓ CALCULATED automatically                               │
│  Dimension:      Fraction/T (correct!)                                    │
│                                                                             │
│  METRIC 2: Monthly Revenue Rate                                           │
│  ──────────────────────────────                                           │
│  Formula:        Annual Sales / 12                                        │
│                = ₹106 Cr C/T / 12                                         │
│                = C/T (cash per month)                                     │
│  Calculation:    ₹106 Cr / 12 = ₹8.83 Cr per month                       │
│  Status:         ✓ CALCULATED automatically                               │
│  Dimension:      C/T (correct!)                                           │
│                                                                             │
│  METRIC 3: Months Inventory Outstanding (MIO)                            │
│  ──────────────────────────────────────────────                          │
│  Formula:        Unsold / Monthly Velocity                                │
│                = 334 U / (44 U/month)                                     │
│                = U / (U/T) = T (time)                                     │
│  Calculation:    334 / 43.9 = 7.6 months                                 │
│  Status:         ✓ CALCULATED automatically                               │
│  Dimension:      T (correct! Result is in months)                         │
│                                                                             │
│  METRIC 4: % Sold (Completion %)                                          │
│  ─────────────────────────────────                                        │
│  Formula:        Sold / Total                                             │
│                = 2684 U / 3018 U                                          │
│                = dimensionless (pure ratio)                               │
│  Calculation:    0.8892 = 89%                                             │
│  Status:         ✓ CALCULATED automatically                               │
│  Dimension:      Dimensionless (%)                                        │
│                                                                             │
│  METRIC 5: Price Appreciation (Annual CAGR)                              │
│  ────────────────────────────────────────                                │
│  Formula:        (Current - Launch) / Years                               │
│                = (₹3996 - ₹2200) / 18 years                               │
│                = ₹1796 / 18 = ₹99.8 per year growth                      │
│                = T^(-1) (rate per year)                                   │
│  Calculation:    (3996/2200)^(1/18) - 1 = 3.3% CAGR                      │
│  Status:         ✓ CALCULATED automatically                               │
│  Dimension:      T^(-1) (correct! Rate per year)                          │
│                                                                             │
│  Key Point: All L2 metrics are AUTOMATICALLY CALCULATED from L1.         │
│  They combine L0 dimensions in valid ways (dimensional algebra).          │
│  If L1 changes, L2 automatically recalculates!                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
                        (Rule evaluation against L2 values)
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ L3: ANALYTICAL INSIGHTS (Rule-Based Assessment & Recommendations)          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  RULE: R001_AbsorptionRate_SalesHealth                                    │
│  ─────────────────────────────────────                                    │
│                                                                             │
│  Threshold Table (Configurable in Neo4j):                                 │
│  ┌──────────────────────┬────────────┬──────────────────────────┐        │
│  │ Condition            │ Assessment │ Recommended Actions      │        │
│  ├──────────────────────┼────────────┼──────────────────────────┤        │
│  │ AR > 3% per month    │ EXCELLENT  │ Maintain strategy        │        │
│  │ 2% < AR ≤ 3%         │ GOOD       │ Monitor + prepare upsell │        │
│  │ 1% < AR ≤ 2%         │ MODERATE   │ +20% marketing spend     │        │
│  │ 0.5% < AR ≤ 1%       │ POOR       │ Consider price -5-10%    │        │
│  │ AR ≤ 0.5%            │ CRITICAL   │ URGENT intervention      │        │
│  └──────────────────────┴────────────┴──────────────────────────┘        │
│                                                                             │
│  Evaluation for Sara City:                                                │
│  ────────────────────────                                                 │
│  Input: L2 Metric AR = 0.37% per month                                   │
│  Condition Matched: AR ≤ 0.5% ✓                                           │
│  Assessment: CRITICAL                                                      │
│  Severity: HIGH                                                            │
│                                                                             │
│  Generated Narrative (via Claude AI):                                      │
│  ─────────────────────────────────────                                    │
│  "Sara City's absorption rate of 0.37% per month is critically low.      │
│   At this pace, the project would take approximately 22 years to sell    │
│   the remaining 334 unsold units. Immediate strategic intervention is    │
│   required to accelerate sales."                                          │
│                                                                             │
│  Triggered Recommendations:                                               │
│  ───────────────────────────                                              │
│  [1] HIGH PRIORITY: Price Reduction                                       │
│      Detail: "Consider reducing launch price from ₹3,996 PSF to          │
│               ₹3,650-3,700 PSF (7-10% reduction) to align with          │
│               market sentiment. Current premium positioning (12% above    │
│               market median) may be unjustified at low absorption rates." │
│      Expected Impact: "May increase absorption to 1-1.5%/month"          │
│                                                                             │
│  [2] HIGH PRIORITY: Marketing Campaign                                    │
│      Detail: "Launch targeted marketing campaign focusing on 1BHK        │
│               segment (18.5% of inventory). Current segment mix is       │
│               75% 1BHK, indicating strong demand for this type."         │
│      Expected Impact: "Improve brand awareness; drive volume in 1BHK"    │
│                                                                             │
│  [3] MEDIUM PRIORITY: Promotional Incentives                              │
│      Detail: "Offer structured promotions: early possession discount     │
│               (2-3 months advance), waived registration fees, tie-up     │
│               with financing partners for reduced interest rates."       │
│      Expected Impact: "Remove buyer barriers; accelerate conversions"    │
│                                                                             │
│  Key Points:                                                               │
│  ───────────                                                               │
│  - L3 insights are STRING NARRATIVES, not numbers                         │
│  - Rules are CONFIGURABLE (stored in Neo4j, not hardcoded)               │
│  - Narratives are AI-GENERATED (via Claude) for context                  │
│  - Recommendations are SPECIFIC & ACTIONABLE                              │
│  - If rule threshold changes, ALL insights automatically recalculate!    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Sara City vs Pradnyesh: Comparison (Same L0, Different L1-L2-L3)

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                  TWO PROJECTS, SAME ARCHITECTURE                         ║
║                  Different L1 → Different L2 → Different L3              ║
╚═══════════════════════════════════════════════════════════════════════════╝

PROJECT 1: SARA CITY (3306)              PROJECT 2: PRADNYESH (134282)
─────────────────────────────            ──────────────────────────────

L1 DATA:                                 L1 DATA:
Total Units:        3018 U               Total Units:        278 U
Unsold Units:       334 U                Unsold Units:       164 U
Sold Units:         2684 U               Sold Units:         114 U
Size:               411 L²               Size:               562 L²
Possession:         Dec 2027 T           Possession:         May 2027 T
Annual Sales:       ₹106 Cr C/T          Annual Sales:       ₹24 Cr C/T

L2 METRICS (AUTO-CALCULATED):           L2 METRICS (AUTO-CALCULATED):
AR = 0.37% / month                       AR = 1.32% / month
Status: CRITICAL                         Status: GOOD
Monthly Revenue = ₹8.83 Cr               Monthly Revenue = ₹2 Cr
MI = 7.6 months                          MI = 6.8 months
% Sold = 89%                             % Sold = 41%

L3 INSIGHTS (RULE-BASED):               L3 INSIGHTS (RULE-BASED):
Assessment: CRITICAL                     Assessment: GOOD
Recommendations:                         Recommendations:
  - Price -7% to -10%                      - Monitor market
  - Marketing campaign                     - Prepare upsell offers
  - Promotional incentives                 - Plan marketing refresh

KEY INSIGHT:
Same rules (L0), different data (L1) → Different calculations (L2) → Different insights (L3)
This is CORRECT behavior. Each project is unique and evaluated independently.
```

---

## Data Flow: LF Quarterly Update Triggers Cascade

```
STEP 1: LF Quarterly Data File Arrives
──────────────────────────────────────
File: lf_export_q2_2025_26.csv
Contains: Sara City, Pradnyesh, Sara Nilaay, etc. with updated attributes

STEP 2: L1 Loader Reads File → Updates Neo4j L1 Nodes
─────────────────────────────────────────────────────
Old L1: unsoldUnits = 340, currentPrice_PSF = 3950
New L1: unsoldUnits = 334, currentPrice_PSF = 3996
Change: UPDATED in Neo4j

STEP 3: Trigger L2 Recalculation (Automatic)
────────────────────────────────────────────
Old L2 AR: (2690 / 3018) / 240 = 0.371%
New L2 AR: (2684 / 3018) / 240 = 0.369%

Old L2 MI: 340 / (527/12) = 7.75 months
New L2 MI: 334 / (527/12) = 7.60 months
Changes: UPDATED in Neo4j

STEP 4: Trigger L3 Insight Regeneration (Automatic)
──────────────────────────────────────────────────
Old L3 Assessment: CRITICAL (AR = 0.371%)
New L3 Assessment: CRITICAL (AR = 0.369%)
Same assessment, but Claude regenerates narrative with NEW data:
"AR has slightly improved from 0.37% to 0.37%, but remains critically low..."

Changes: UPDATED in Neo4j

STEP 5: API Responds with Latest Data
────────────────────────────────────
GET /api/projects/3306/full-analysis
→ Returns updated L0 + L1 + L2 + L3 (all current as of this moment)

Result: Complete cascade from LF → L0 → L1 → L2 → L3
        All dependencies automatically maintained.
```

---

## Neo4j Graph Model Visualization

```
                    L0_DIMENSIONS
                   ┌─────────────┐
                   │    U (count)│
                   │    L² (sqft)│
                   │    T (date) │
                   │    C (INR)  │
                   └─────────────┘
                         △
                         │ defines schema for
                         │
                   ┌─────────────────┐
      ┌──────────→ │ L1_PROJECT      │
      │            │ (Sara City)     │
      │            │ ┌─────────────┐ │
      │            │ │totalUnits:  │ │
      │            │ │  3018 (U)   │ │
      │            │ │unsoldUnits: │ │
      │            │ │  334 (U)    │ │
      │            │ └─────────────┘ │
      │            └─────────────────┘
      │                   △
      │                   │
      │ input to  ┌──────────────────┐
      └───────────│ L2_METRIC        │
                 │ (Absorption Rate)│
                 │ ┌──────────────┐ │
                 │ │ formula:     │ │
                 │ │ (sold/total) │ │
                 │ │ / months     │ │
                 │ │ value:       │ │
                 │ │ 0.37%/month  │ │
                 │ └──────────────┘ │
                 └──────────────────┘
                        △
                        │
                applies │ L3_RULE
                 ┌──────────────────┐
                 │ L3_INSIGHT       │
                 │ (Sales Health)   │
                 │ ┌──────────────┐ │
                 │ │assessment:   │ │
                 │ │  CRITICAL    │ │
                 │ │narrative:    │ │
                 │ │  "AR too low"│ │
                 │ │recommend:    │ │
                 │ │  Price -7%   │ │
                 │ └──────────────┘ │
                 └──────────────────┘

RELATIONSHIPS:
- L1_Project -[:HAS_DIMENSION]-> L0_Dimension
- L2_Metric -[:DEPENDS_ON_L1]-> L1_Project
- L3_Insight -[:DEPENDS_ON_L2]-> L2_Metric
- L3_Insight -[:APPLIES_RULE]-> L3_Rule
- L3_Rule -[:RECOMMENDS_ACTION]-> L3_Action
```

---

## API Response Example: Full Analysis

```json
GET /api/projects/3306/full-analysis

{
  "metadata": {
    "projectId": "3306",
    "projectName": "Sara City",
    "requestTime": "2025-11-27T10:35:00Z",
    "dataVersion": "LF_Q2_2025_26"
  },

  "l0_dimensions": {
    "U": {
      "name": "Units/Inventory",
      "unit": "count",
      "physicsAnalog": "Mass (M)",
      "immutable": true
    },
    "L2": {
      "name": "Space/Area",
      "unit": "sqft",
      "physicsAnalog": "Length² (L²)",
      "immutable": true
    },
    "T": {
      "name": "Time",
      "unit": "date | months",
      "physicsAnalog": "Time (T)",
      "immutable": true
    },
    "C": {
      "name": "Cash Flow",
      "unit": "INR",
      "physicsAnalog": "Current (I)",
      "immutable": true
    }
  },

  "l1_attributes": {
    "projectName": "Sara City",
    "totalUnits": {
      "value": 3018,
      "dimension": "U",
      "unit": "count",
      "source": "LF_ProductIntelligence"
    },
    "unsoldUnits": {
      "value": 334,
      "dimension": "U",
      "unit": "count",
      "source": "LF_SalesIntelligence"
    },
    "unitSaleableSize": {
      "value": 411,
      "dimension": "L²",
      "unit": "sqft",
      "source": "LF_ProductIntelligence"
    },
    "possessionDate": {
      "value": "2027-12-31",
      "dimension": "T",
      "unit": "date",
      "source": "LF_ProjectData"
    },
    "currentPrice_PSF": {
      "value": 3996,
      "dimension": "C/L²",
      "unit": "INR/sqft",
      "source": "LF_MarketIntelligence"
    },
    "annualSalesValue": {
      "value": 10600000000,
      "dimension": "C/T",
      "unit": "INR/year",
      "source": "LF_SalesIntelligence"
    }
  },

  "l2_metrics": [
    {
      "metricId": "L2_AR_3306",
      "metricName": "Absorption Rate",
      "dimension": "Fraction/T",
      "value": 0.0037,
      "unit": "%/month",
      "formula": "(soldUnits / totalUnits) / monthsElapsed",
      "calculation": "(2684 / 3018) / 240 = 0.37%",
      "calculatedAt": "2025-11-27T10:32:00Z",
      "confidence": 0.95
    },
    {
      "metricId": "L2_MR_3306",
      "metricName": "Monthly Revenue",
      "dimension": "C/T",
      "value": 883333333,
      "unit": "INR/month",
      "formula": "annualSalesValue / 12",
      "calculation": "106 Cr / 12 = 8.83 Cr",
      "calculatedAt": "2025-11-27T10:32:00Z",
      "confidence": 0.95
    },
    {
      "metricId": "L2_MI_3306",
      "metricName": "Months Inventory",
      "dimension": "T",
      "value": 7.6,
      "unit": "months",
      "formula": "unsoldUnits / (monthlyVelocity)",
      "calculation": "334 / 43.9 = 7.6 months",
      "calculatedAt": "2025-11-27T10:32:00Z",
      "confidence": 0.95
    }
  ],

  "l3_insights": [
    {
      "insightId": "L3_SalesHealth_3306",
      "ruleApplied": "R001_AbsorptionRate_SalesHealth",
      "assessment": "CRITICAL",
      "severity": "HIGH",
      "isAlert": true,
      "narrative": "Sara City's absorption rate of 0.37% per month is critically low. 
                   At the current pace, it would take approximately 22 years to 
                   sell all remaining unsold units. Immediate strategic 
                   intervention is required.",
      "recommendations": [
        {
          "priority": "HIGH",
          "action": "Price Reduction",
          "detail": "Reduce from ₹3,996 PSF to ₹3,650-3,700 PSF (7-10% reduction)",
          "expectedImpact": "May increase absorption to 1-1.5% per month"
        },
        {
          "priority": "HIGH",
          "action": "Marketing Campaign",
          "detail": "Launch targeted campaign for 1BHK segment (18.5% of supply)",
          "expectedImpact": "Improve brand awareness; drive volume"
        },
        {
          "priority": "MEDIUM",
          "action": "Promotional Incentives",
          "detail": "Offer early possession discounts, waived registration fees",
          "expectedImpact": "Remove buyer barriers; accelerate conversions"
        }
      ],
      "generatedAt": "2025-11-27T10:35:00Z",
      "generatedBy": "Claude API + L3_Rule_Engine"
    }
  ],

  "summary": {
    "overallHealth": "CRITICAL",
    "healthScore": 25,
    "topAlerts": 2,
    "alertSummary": "Sales absorption critically low; pricing misaligned with market",
    "lastUpdated": "2025-11-27T10:35:00Z",
    "nextReviewDate": "2025-12-27T10:35:00Z"
  }
}
```

---

**This visual guide complements PRD v3.0 and QuickRef documents**

Together these three documents provide complete clarity on the L0-L1-L2-L3 architecture.
