# Product Requirements Document: LF-Sirrus Integration

## Multi-Layer Dimensional Knowledge Graph for Real Estate Analytics

**Version:** 3.0 (Layer Clarity: L0 Schema → L1 Data → L2 Derivatives → L3 Insights)  
**Date:** November 30, 2025  
**Status:** Production-Ready Draft  
**Target Implementation:** Neo4j + FastAPI + Claude Integration  

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Core Concept: MLTI Dimensional System](#core-concept-mlti-dimensional-system)
3. [Four-Layer Architecture Defined](#four-layer-architecture-defined)
4. [Layer 0: Dimensional Schema (Immutable)](#layer-0-dimensional-schema-immutable)
5. [Layer 1: Project Attributes (Actual Data)](#layer-1-project-attributes-actual-data)
6. [Layer 2: Derived Metrics (Calculated)](#layer-2-derived-metrics-calculated)
7. [Layer 3: Analytical Insights (Rule-Based)](#layer-3-analytical-insights-rule-based)
8. [Neo4j Knowledge Graph Structure](#neoj4-knowledge-graph-structure)
9. [Practical Examples with LF Data](#practical-examples-with-lf-data)
10. [Implementation Architecture](#implementation-architecture)
11. [API Layer & Query Routing](#api-layer--query-routing)
12. [Acceptance Criteria](#acceptance-criteria)

---

## Executive Summary

This PRD v3.0 establishes a **crystal-clear four-layer dimensional architecture** for the LF-Sirrus integration, grounded in the physics-inspired MLTI system:

- **Layer 0 (L0):** Dimension definitions (column schema/data types in database terminology)
- **Layer 1 (L1):** Actual project attributes (column names + values from LF data; rows & cells)
- **Layer 2 (L2):** Derived metrics (calculated from L1 using dimensional algebra)
- **Layer 3 (L3):** Analytical insights (rule-based assessments with remedial recommendations)

**Key Innovation:** This architecture mirrors database table design (columns = L0+L1, rows = data cells) while enabling automatic metric derivation and AI-powered business insights.

---

## Core Concept: MLTI Dimensional System

### Physics Foundation (MLTI System)

In physics, all physical quantities can be expressed as combinations of four fundamental dimensions:

| Dimension | Symbol | SI Unit | Real Estate Analog | Definition |
|-----------|--------|---------|-------------------|-----------|
| **Mass** | M | kg | **Units/Inventory (U)** | Count of housing products (1BHK, 2BHK, etc.) |
| **Length** | L | meter | **Space/Area (L²)** | Square feet, square meters, hectares |
| **Time** | T | second | **Time Period (T)** | Date, month, quarter, year, possession timeline |
| **Current** | I | ampere | **Cash Flow (C)** | INR/month, rupee amounts, financial flow |

### Real Estate Application

Every real estate metric can be **dimensionally analyzed** as combinations of U, L², T, and C:

- **Price per Square Foot (PSF)** = C/L² (Cash over Area)
- **Sales Velocity** = U/T (Units over Time)
- **Annual Sales Value** = C (pure cash, which is flow C × T aggregated)
- **Absorption Rate** = (U/U_total)/T (fraction per month)
- **Revenue Run Rate** = C/T (cash per month)

This dimensional consistency ensures **no incompatible calculations** can occur.

---

## Four-Layer Architecture Defined

### Conceptual Stacking

```
┌─────────────────────────────────────────────────────────────┐
│ L3: INSIGHTS (String narratives, alerts, recommendations)  │
│ "Poor selling velocity, suggest: price reduction or marketing boost"
├─────────────────────────────────────────────────────────────┤
│ L2: DERIVATIVES (Calculated metrics from L1 combinations)   │
│ "Absorption Rate = 2.5% per month", "IRR = 22%"            │
├─────────────────────────────────────────────────────────────┤
│ L1: ATTRIBUTES (Actual column values from LF data)          │
│ "Total Units = 3018", "PSF = 3996", "Possession = Dec 2027"│
├─────────────────────────────────────────────────────────────┤
│ L0: DIMENSIONS (Immutable schema / column definitions)      │
│ "U (count)", "L² (sqft)", "T (date)", "C (INR)"            │
└─────────────────────────────────────────────────────────────┘
```

### Layer Relationships

```
L0 (Dimensions) 
    ↑ Defines
L1 (Attributes) 
    ↑ Input to
L2 (Derivatives) 
    ↑ Input to
L3 (Insights)
```

**Database Analogy:**

| Database Concept | Our System | Example |
|-----------------|-----------|---------|
| Table schema / column definition | L0 | "projectId: STRING, totalUnits: INTEGER, areaPerUnit: FLOAT" |
| Column name | L1 (vertical) | "Project Name", "Total Units", "Saleable Price PSF" |
| Row data / cell value | L1 (horizontal) | "Sara City = 3018 units", "Sara City = 411 sqft" |
| Derived column (computed) | L2 | "Absorption Rate = Units Sold / Total Units / Months" |
| Business rule applied to derived value | L3 | "If Absorption Rate < 2%, status = Poor; recommend: price reduction" |

---

## Layer 0: Dimensional Schema (Immutable)

### Definition

**Layer 0 comprises the four atomic, immutable dimensions** that serve as the basis for all real estate metrics. These are analogous to:
- **Data types in a database** (INTEGER, FLOAT, TIMESTAMP, VARCHAR)
- **Column definitions** in database schema design
- **Fundamental units** in physics

### The Four L0 Dimensions

#### 1. Units Dimension (U)
- **Represents:** Count of discrete housing products
- **Unit:** Dimensionless count (units, items, pieces)
- **Range:** Typically 10–10,000 units per project
- **Examples:** 1BHK units, 2BHK units, parking units, retail units
- **Neo4j Representation:** `count` data type (INTEGER)

#### 2. Space Dimension (L²)
- **Represents:** Area of real estate
- **Unit:** Square feet (sqft), square meters (sqm), acres, hectares
- **Range:** 200–2,000 sqft per unit; 5,000–500,000 sqft per project
- **Examples:** Carpet area, saleable area, built-up area, land area
- **Neo4j Representation:** `area` data type (FLOAT with unit metadata)

#### 3. Time Dimension (T)
- **Represents:** Temporal period or specific date
- **Unit:** Date (ISO-8601), month, quarter, year, or duration (months elapsed)
- **Range:** Project launch date, possession date, sales cycle months
- **Examples:** "Dec 2027" (possession date), "36 months" (project duration), "2025-11-30" (current date)
- **Neo4j Representation:** `date` or `duration` data type (TIMESTAMP, INTEGER for months)

#### 4. Cash Flow Dimension (C)
- **Represents:** Financial amount or rate of financial flow
- **Unit:** INR (Indian Rupees), INR/month (monthly cash flow), INR/year (annual cash flow)
- **Range:** ₹100 Lac–₹500 Crore per project
- **Examples:** Total project cost, revenue, monthly sales value, cost per sqft
- **Neo4j Representation:** `money` data type (FLOAT in INR, with time period metadata if rate)

### L0 Neo4j Schema

```cypher
# LAYER 0: IMMUTABLE DIMENSION DEFINITIONS (Schema Level)

CREATE (dimension_U:L0_Dimension {
  dimensionCode: "U",
  dimensionName: "Units/Inventory",
  siUnit: "count",
  description: "Discrete count of housing products (1BHK, 2BHK, 3BHK, etc.)",
  dataType: "INTEGER",
  physicsAnalog: "Mass (M)",
  category: "ATOMIC",
  immutable: true
})

CREATE (dimension_L2:L0_Dimension {
  dimensionCode: "L2",
  dimensionName: "Space/Area",
  siUnit: "sqft | sqm | acre | hectare",
  description: "Area of real estate (carpet, saleable, built-up, land)",
  dataType: "FLOAT",
  physicsAnalog: "Length² (L²)",
  category: "ATOMIC",
  immutable: true
})

CREATE (dimension_T:L0_Dimension {
  dimensionCode: "T",
  dimensionName: "Time",
  siUnit: "date | months | years | duration",
  description: "Temporal period or specific date (launch, possession, sales cycle)",
  dataType: "DATE or INTEGER",
  physicsAnalog: "Time (T)",
  category: "ATOMIC",
  immutable: true
})

CREATE (dimension_C:L0_Dimension {
  dimensionCode: "C",
  dimensionName: "Cash Flow",
  siUnit: "INR | INR/month | INR/year",
  description: "Financial amount or rate of cash flow",
  dataType: "FLOAT",
  physicsAnalog: "Current (I)",
  category: "ATOMIC",
  immutable: true
})
```

---

## Layer 1: Project Attributes (Actual Data)

### Definition

**Layer 1 comprises project-specific attributes** extracted from LF data. Each L1 attribute:
- Is tagged with its **dimension(s)** from L0 (U, L², T, or C)
- Contains **actual data values** (rows × columns in database terms)
- Is sourced from **LF data tables** (Market Intelligence, Product Intelligence, etc.)
- Forms the **basis for all L2 calculations**

### L1 Attribute Categories

#### Pure Dimensional Attributes (Single L0 Dimension)

| Attribute Name | Dimension | Unit | Example Value | LF Source |
|---|---|---|---|---|
| **Total Units** | U | count | 3018 | Product Intelligence |
| **Unit Saleable Size** | L² | sqft | 411 | Product Intelligence |
| **Possession Date** | T | date | Dec 2027 | Project master data |
| **Launch Price** | C | INR | ₹2,200 Cr (total for project) | Market Intelligence |
| **Unsold Units** | U | count | 334 (11% of 3018) | Sales Intelligence |
| **Total Project Cost** | C | INR | ₹500 Cr | Financial Intelligence |
| **Project Duration** | T | months | 36 | Project master data |
| **Land Area** | L² | sqft | 70,000 | Project master data |

#### Composite Dimensional Attributes (Multiple L0 Dimensions)

| Attribute Name | Dimension | Formula | Example Value | LF Source |
|---|---|---|---|---|
| **Annual Sales Value** | C/T | Total Revenue / Year | ₹106 Cr/Year | Sales Intelligence |
| **Saleable Price PSF** | C/L² | Total Revenue / Saleable Area | ₹3,996 PSF | Market Intelligence |
| **Sales Velocity** | U/T | Units Sold per Month | 44 units/month (527 annual / 12) | Sales Intelligence |
| **Monthly Revenue** | C/T | Annual Sales / 12 | ₹8.83 Cr/month | Derived from Annual Sales |
| **Cost per Unit** | C/U | Total Cost / Total Units | ₹16.5 Lac/unit (estimated) | Financial Intelligence |
| **Unit Density** | U/L² | Total Units / Land Area | 0.043 units/sqft | Project Efficiency |

### L1 Neo4j Schema: Sara City Example

```cypher
# LAYER 1: PROJECT ATTRIBUTES WITH ACTUAL DATA (Rows & Cells)

CREATE (project_sara:L1_Project {
  # Identifiers
  projectId: "3306",
  projectName: "Sara City",
  
  # PURE DIMENSIONAL ATTRIBUTES
  # U: Units dimension
  totalUnits: 3018,                    # L0_Dimension: U
  soldUnits: 2684,                     # 89% of total
  unsoldUnits: 334,                    # 11% of total
  
  # L²: Area dimension
  unitSaleableSize: 411,               # L0_Dimension: L² (average sqft per unit)
  totalSaleableArea: 1_241_298,        # 3018 units × 411 sqft
  
  # T: Time dimension
  launchDate: "2007-11-01",            # L0_Dimension: T
  possessionDate: "2027-12-31",        # L0_Dimension: T
  projectDurationMonths: 240,          # Nov 2007 to Dec 2027
  
  # C: Cash Flow dimension
  launchPrice_PSF: 2200,               # L0_Dimension: C (price per sqft at launch)
  currentPrice_PSF: 3996,              # L0_Dimension: C (current price per sqft)
  annualSalesValue: 106_00_00_000,     # ₹106 Crore per year, L0_Dimension: C
  
  # COMPOSITE DIMENSIONAL ATTRIBUTES
  # These are technically L1 but reference multiple L0 dimensions
  # (kept in L1 because they are direct LF data, not calculated)
  monthlyRevenue: 8_83_33_333,         # ₹8.83 Cr/month, derived but stored in L1
  soldPercent: 0.89,                   # 89%, pure ratio (dimensionless)
  unsoldPercent: 0.11,                 # 11%, pure ratio (dimensionless)
  
  # Contextual attributes
  developer: "Sara Builders & Developers (Sara Group)",
  city: "Pune",
  microMarket: "Chakan",
  
  # Data freshness
  lastUpdated: "2025-11-27",
  dataSource: "LF_Q2_2025_26",
  reraRegistered: true
})
```

### L1 Table Structure (Database Analogy)

```
Project Attributes Table (L1)
┌──────────────┬─────────────┬──────┬────────┬────────┬──────────┐
│ ProjectName  │ TotalUnits  │ Size │ Launch │ Possess│ AnnualSales
│ (Label)      │ (U)         │ (L²) │ (T)    │ (T)    │ (C/T)
├──────────────┼─────────────┼──────┼────────┼────────┼──────────┤
│ Sara City    │ 3018        │ 411  │ Nov'07 │ Dec'27 │ ₹106 Cr
├──────────────┼─────────────┼──────┼────────┼────────┼──────────┤
│ Pradnyesh... │ 278         │ 562  │ Apr'23 │ May'27 │ ₹24 Cr
├──────────────┼─────────────┼──────┼────────┼────────┼──────────┤
│ Sara Nilaay  │ 298         │ 395  │ May'24 │ Dec'28 │ ₹6 Cr
└──────────────┴─────────────┴──────┴────────┴────────┴──────────┘
```

---

## Layer 2: Derived Metrics (Calculated)

### Definition

**Layer 2 comprises calculated metrics** derived from L1 attributes using **dimensional algebra**. Each L2 metric:
- Combines **two or more L1 attributes**
- Produces a **new dimension** (combination of L0 dimensions)
- Is **automatically calculated** when L1 data changes
- May be used **multiple times** in L3 insight rules

### L2 Derivation Rules (Dimensional Algebra)

#### Example 1: Absorption Rate
```
Formula:    AR = (Sold Units / Total Units) / Months Elapsed
Dimensions: (U / U) / T = Dimensionless / T = Fraction/Month
L1 Inputs:  soldUnits (U), totalUnits (U), monthsElapsed (T)
```
- **Sara City Example:** (2684 / 3018) / 240 months = 0.89 / 240 = **0.0037 = 0.37% per month**
- Alternative view: 527 units sold annually / 3018 total = **17.5% per year** or **1.46% per month**

#### Example 2: Monthly Revenue Rate
```
Formula:    MR = Annual Sales Value / 12
Dimensions: C / T = C/T (cash per month)
L1 Inputs:  annualSalesValue (C/T), constant 12
```
- **Sara City Example:** ₹106 Cr / 12 = **₹8.83 Cr per month**

#### Example 3: Cost Per Unit
```
Formula:    CPU = Total Project Cost / Total Units
Dimensions: C / U = C/U (cash per unit)
L1 Inputs:  totalProjectCost (C), totalUnits (U)
```
- **Sara City Estimate:** If total cost is ₹500 Cr: ₹500 Cr / 3018 units = **₹16.5 Lac per unit**

#### Example 4: Saleable Price PSF (Market-Derived)
```
Formula:    PSF = Current Total Revenue / Total Saleable Area
Dimensions: C / L² (cash per area)
L1 Inputs:  currentPrice_PSF (C/L²) directly from LF
```
- **Sara City:** **₹3,996 PSF** (current market price)

#### Example 5: Months Inventory Outstanding (MIO)
```
Formula:    MIO = Unsold Units / Monthly Sales Velocity
Dimensions: U / (U/T) = U × (T/U) = T (time)
L1 Inputs:  unsoldUnits (U), monthlySalesVelocity (U/T)
```
- **Sara City:** 334 unsold / 44 units per month = **7.6 months** to sell out at current velocity
- From LF data: Reported "54 Months Inventory" (different calculation, possibly includes all projects)

### Complete L2 Metrics Set

| Metric | Dimension | Formula | Components | Calculation Type |
|--------|-----------|---------|-----------|------------------|
| **Absorption Rate (AR)** | Fraction/T | (Sold / Total) / Time | L1: sold, total, elapsed_time | Percentage per month |
| **Monthly Sales Velocity** | U/T | Units Sold per Month | L1: annual_sales / 12 | Rate calculation |
| **Revenue Run Rate** | C/T | Monthly Cash Flow | L1: annualSalesValue / 12 | Cash rate |
| **Cost Per Unit** | C/U | Total Cost / Units | L1: projectCost / totalUnits | Unit economics |
| **Price Per Sqft (Market)** | C/L² | Revenue / Area | L1: currentPrice_PSF | Market pricing |
| **Unit Density** | U/L² | Units / Land Area | L1: totalUnits / landArea | Supply intensity |
| **Months Inventory** | T | Unsold / Monthly Velocity | L1: unsoldUnits / monthlySalesVelocity | Inventory turnover |
| **% Sold** | Dimensionless | Sold / Total | L1: soldUnits / totalUnits | Absorption progress |
| **Price Appreciation Annual** | T^(-1) | (Current - Launch) / Years | L1: currentPrice, launchPrice, projectYears | YoY growth rate |
| **Revenue Forecast (Remaining)** | C | Unsold × Price PSF × Area | L1: unsoldUnits, currentPrice_PSF, sizePerUnit | Remaining revenue potential |

### L2 Neo4j Schema

```cypher
# LAYER 2: DERIVED METRICS (Calculated from L1)

CREATE (metric_ar_sara:L2_Metric {
  # Metric identity
  metricId: "L2_AR_SaraCity_3306",
  metricName: "Absorption Rate",
  dimensionCode: "Fraction/T",  # (U/U) / T
  
  # Calculation
  projectId: "3306",
  formula: "(soldUnits / totalUnits) / monthsElapsed",
  
  # L1 component values
  soldUnits: 2684,          # From L1
  totalUnits: 3018,         # From L1
  monthsElapsed: 240,       # From L1 (Nov 2007 to Nov 2025)
  
  # Calculated result
  value: 0.0037,            # 0.37% per month
  valuePercent: 0.37,       # 0.37% format
  unit: "percent_per_month",
  
  # Alternative interpretation
  annualAbsorption: 0.1746, # 17.46% per year (for business logic)
  
  # Data provenance
  calculatedAt: "2025-11-27",
  lfSource: "Sales Intelligence (LF Pillar 5)",
  confidence: 0.95          # High confidence (LF data)
})

# RELATIONSHIP: Metric depends on L1 attributes
MATCH (metric:L2_Metric {metricId: "L2_AR_SaraCity_3306"})
MATCH (project:L1_Project {projectId: "3306"})
CREATE (metric) - [:DEPENDS_ON_L1 {components: ["soldUnits", "totalUnits", "monthsElapsed"]}] -> (project)

# Another L2 example: Monthly Revenue Rate
CREATE (metric_mrr_sara:L2_Metric {
  metricId: "L2_MRR_SaraCity_3306",
  metricName: "Monthly Revenue Rate",
  dimensionCode: "C/T",     # Cash per time
  
  formula: "annualSalesValue / 12",
  annualSalesValue: 106_00_00_000,  # ₹106 Crore (from L1)
  value: 8_83_33_333,               # ₹8.83 Crore per month
  unit: "INR_per_month",
  
  calculatedAt: "2025-11-27",
  lfSource: "Sales Intelligence (LF Pillar 5)",
  confidence: 0.95
})
```

---

## Layer 3: Analytical Insights (Rule-Based)

### Definition

**Layer 3 comprises business insights** derived from L2 metrics using **rule-based logic**. Each L3 insight:
- Takes **one or more L2 metric(s)** as input
- Applies **configurable business rules** (thresholds, ranges)
- Produces a **string-based assessment** (narrative) and/or **action recommendation**
- Is **persistent and rule-configurable** (not hardcoded)

### L3 Rule Framework

#### Example Rule Set 1: Sales Health Based on Absorption Rate

```
Rule ID: R001_AbsorptionRate_SalesHealth
Metric Input: Absorption Rate (AR) - L2 metric

Rule Definition:
┌─────────────────────────────────┬───────────────┬────────────────────────────────┐
│ Condition                       │ Assessment    │ Recommended Actions            │
├─────────────────────────────────┼───────────────┼────────────────────────────────┤
│ AR > 3% per month               │ EXCELLENT     │ Maintain current strategy      │
│ AR between 2-3% per month       │ GOOD          │ Monitor market; prepare upsell │
│ AR between 1-2% per month       │ MODERATE      │ Increase marketing spend 20%   │
│ AR between 0.5-1% per month     │ POOR          │ Consider price reduction 5-10% │
│ AR < 0.5% per month             │ CRITICAL      │ Urgent: repricing + campaign   │
└─────────────────────────────────┴───────────────┴────────────────────────────────┘

Application to Sara City:
Input AR: 0.37% per month
Matches: AR < 0.5% per month → Assessment: CRITICAL
Recommendation: "Urgent action required. Current absorption critically low (0.37%/month).
Recommend: (1) Price reduction 7-10%, (2) Launch marketing campaign, (3) Offer incentives."
```

#### Example Rule Set 2: Inventory Health Based on Months Inventory Outstanding

```
Rule ID: R002_MonthsInventory_InventoryHealth
Metric Input: Months Inventory (MI) - L2 metric

Rule Definition:
┌──────────────────────────────┬────────────────┬──────────────────────────────┐
│ Condition                    │ Assessment     │ Recommended Actions          │
├──────────────────────────────┼────────────────┼──────────────────────────────┤
│ MI < 6 months                │ EXCELLENT      │ Increase inventory/new launch│
│ MI 6-12 months               │ GOOD           │ Maintain sales efforts       │
│ MI 12-18 months              │ MODERATE       │ Adjust pricing or marketing  │
│ MI 18-24 months              │ POOR           │ Consider bundle offers       │
│ MI > 24 months               │ CRITICAL       │ Strategic restructuring req. │
└──────────────────────────────┴────────────────┴──────────────────────────────┘

Application to Sara City:
Input MI: 7.6 months (calculated from unsold / monthly velocity)
Matches: MI 6-12 months → Assessment: GOOD
Recommendation: "Inventory level is healthy. Continue current sales strategy; consider
inventory replenishment planning if velocity increases beyond 45 units/month."
```

#### Example Rule Set 3: Price Competitiveness

```
Rule ID: R003_PriceCompetitiveness_MarketPosition
Metric Inputs: Current PSF (L2), Launch PSF (L1), Market Median PSF (Market benchmark)

Rule Definition:
┌──────────────────────────────────────┬────────────────┬──────────────────────────────┐
│ Condition                            │ Assessment     │ Recommended Actions          │
├──────────────────────────────────────┼────────────────┼──────────────────────────────┤
│ Current PSF < Market Median - 5%     │ AGGRESSIVE     │ Increase prices towards mkr. │
│ Current PSF within Market ± 5%       │ COMPETITIVE    │ Maintain current pricing     │
│ Current PSF > Market + 5% to 10%     │ PREMIUM        │ Maintain if high absorb.     │
│ Current PSF > Market + 10%           │ OVERPRICED     │ Review; consider reduction   │
└──────────────────────────────────────┴────────────────┴──────────────────────────────┘

Application to Sara City:
Input Current PSF: ₹3,996
Market Median (Chakan): ₹3,575 (from LF data Q2 25-26)
Difference: +12.1% above market
Matches: Current PSF > Market + 10% → Assessment: OVERPRICED
Recommendation: "Project priced 12% above market median. If absorption remains low,
consider tactical price reduction (3-5%) to align with market, especially for later phases."
```

### L3 Insight Structure

```cypher
# LAYER 3: ANALYTICAL INSIGHTS (Rule-Based Narratives & Recommendations)

CREATE (insight_sara:L3_Insight {
  # Insight identity
  insightId: "L3_SalesHealth_SaraCity_3306",
  insightName: "Sales Health Assessment",
  
  # Rule reference
  ruleApplied: "R001_AbsorptionRate_SalesHealth",
  triggeredAt: "2025-11-27",
  
  # L2 metric inputs
  metricInputs: ["AR_0.37_percent_month"],
  
  # Rule application
  conditionMatched: "AR < 0.5%",
  assessment: "CRITICAL",
  severity: "HIGH",
  
  # Rule output
  narrative: "Sara City's absorption rate of 0.37% per month is critically low. 
             At this pace, the project would take ~22 years to sell out all unsold units.
             Immediate intervention required.",
  
  # Actionable recommendations (stored as array for further processing)
  recommendations: [
    {
      priority: "HIGH",
      action: "Price Reduction",
      detail: "Consider 7-10% reduction from ₹3,996 PSF to ₹3,650-3,700 PSF",
      expectedImpact: "May increase absorption to 1-1.5% per month"
    },
    {
      priority: "HIGH",
      action: "Marketing Campaign",
      detail: "Launch targeted campaign for 1BHK segment (18.5% of supply)",
      expectedImpact: "May increase brand awareness in market"
    },
    {
      priority: "MEDIUM",
      action: "Promotional Incentives",
      detail: "Offer: waived registration, early possession discount, financing tie-ups",
      expectedImpact: "Drive volume in weak absorption segments"
    }
  ],
  
  # Metadata
  isAlert: true,
  alertLevel: "URGENT",
  dataVersion: "LF_Q2_2025_26",
  lastReviewed: "2025-11-27"
})

# RELATIONSHIP: Insight depends on L2 metrics
MATCH (insight:L3_Insight {insightId: "L3_SalesHealth_SaraCity_3306"})
MATCH (metric:L2_Metric {metricId: "L2_AR_SaraCity_3306"})
CREATE (insight) - [:DEPENDS_ON_L2] -> (metric)

# RELATIONSHIP: Insight references Rule configuration
MATCH (insight:L3_Insight {insightId: "L3_SalesHealth_SaraCity_3306"})
MATCH (rule:L3_Rule {ruleId: "R001_AbsorptionRate_SalesHealth"})
CREATE (insight) - [:APPLIES_RULE] -> (rule)
```

### L3 Rule Configuration (Persistent)

```cypher
# LAYER 3: RULE CONFIGURATION (Configurable, not hardcoded)

CREATE (rule_001:L3_Rule {
  ruleId: "R001_AbsorptionRate_SalesHealth",
  ruleName: "Absorption Rate Health Assessment",
  description: "Evaluates project sales health based on absorption rate",
  
  # Rule trigger
  metricTrigger: "Absorption Rate",
  evaluationLogic: "THRESHOLD_BASED",
  
  # Threshold configuration (can be adjusted by business users)
  thresholds: [
    {
      condition: "value > 0.03",           # 3% per month
      assessment: "EXCELLENT",
      color: "green"
    },
    {
      condition: "value > 0.02 AND value <= 0.03",
      assessment: "GOOD",
      color: "blue"
    },
    {
      condition: "value > 0.01 AND value <= 0.02",
      assessment: "MODERATE",
      color: "yellow"
    },
    {
      condition: "value > 0.005 AND value <= 0.01",
      assessment: "POOR",
      color: "orange"
    },
    {
      condition: "value <= 0.005",
      assessment: "CRITICAL",
      color: "red"
    }
  ],
  
  # Associated actions
  recommendedActions: [
    {
      assessment: "CRITICAL",
      actionSet: ["Price_Reduction", "Marketing_Campaign", "Promotional_Incentives"]
    },
    {
      assessment: "POOR",
      actionSet: ["Marketing_Campaign", "Price_Review"]
    }
  ],
  
  # Rule metadata
  createdAt: "2025-11-27",
  lastModified: "2025-11-27",
  owner: "Business Analytics Team",
  isActive: true,
  lfDataDependency: "LF Pillar 5 (Sales/Ops Intelligence)"
})

# Store recommended actions library
CREATE (action_price:L3_Action {
  actionId: "Price_Reduction",
  actionName: "Price Reduction",
  description: "Reduce launch price by X% to improve market competitiveness",
  template: "Consider {percentage}% reduction from ₹{currentPrice} PSF to ₹{newPrice} PSF",
  expectedOutcome: "May increase absorption from {currentAR}% to {projectedAR}%",
  riskFactors: ["margin_compression", "brand_positioning"],
  isConfigurable: true
})

CREATE (action_marketing:L3_Action {
  actionId: "Marketing_Campaign",
  actionName: "Marketing Campaign",
  description: "Launch targeted marketing for specific unit types or segments",
  template: "Launch campaign targeting {segment} segment; budget: ₹{budget} Cr",
  expectedOutcome: "Increase brand awareness; project 10-20% absorption uplift",
  riskFactors: ["campaign_effectiveness", "market_saturation"],
  isConfigurable: true
})
```

---

## Neo4j Knowledge Graph Structure

### Complete Graph Model

```cypher
# UNIFIED KNOWLEDGE GRAPH SCHEMA

# ============= LAYER 0: DIMENSIONS =============
(:L0_Dimension {
  dimensionCode: "U" | "L2" | "T" | "C",
  dimensionName: "Units" | "Area" | "Time" | "Cash Flow",
  ...
})

# ============= LAYER 1: PROJECT ATTRIBUTES =============
(:L1_Project {
  projectId, projectName, developer, city, microMarket,
  totalUnits, unsoldUnits, soldUnits,
  unitSaleableSize, totalSaleableArea,
  launchDate, possessionDate,
  launchPrice_PSF, currentPrice_PSF, annualSalesValue,
  ...
})

(:L1_Attribute {
  attributeId, attributeName,
  dimensionCode: "U" | "L2" | "T" | "C" | "C/U" | "C/L2" | "U/T",
  value, unit, lfSource,
  ...
})

# ============= LAYER 2: DERIVED METRICS =============
(:L2_Metric {
  metricId, metricName, dimensionCode,
  formula, value, unit,
  projectId, calculatedAt, confidence,
  ...
})

# ============= LAYER 3: INSIGHTS & RULES =============
(:L3_Insight {
  insightId, insightName, ruleApplied,
  assessment, severity, narrative,
  recommendations: [
    { priority, action, detail, expectedImpact }
  ],
  isAlert, alertLevel,
  ...
})

(:L3_Rule {
  ruleId, ruleName, metricTrigger,
  thresholds: [{ condition, assessment, color }],
  recommendedActions,
  isActive, owner,
  ...
})

(:L3_Action {
  actionId, actionName, actionTemplate,
  expectedOutcome, riskFactors,
  isConfigurable,
  ...
})

# ============= RELATIONSHIPS =============

# L0 <-> L1
(:L1_Project) - [:HAS_DIMENSION_L0 {dimensionCode: "U"}] -> (:L0_Dimension)

# L1 -> L2
(:L2_Metric) - [:DEPENDS_ON_L1 {components: ["soldUnits", "totalUnits"]}] -> (:L1_Project)

# L2 -> L3
(:L3_Insight) - [:DEPENDS_ON_L2] -> (:L2_Metric)

# L3 Rule -> L3 Actions
(:L3_Insight) - [:APPLIES_RULE] -> (:L3_Rule)
(:L3_Rule) - [:RECOMMENDS_ACTION] -> (:L3_Action)

# Data lineage
(:L3_Insight) - [:TRACES_TO_L0] -> (:L0_Dimension)
```

### Example Query: Sara City Full Analysis

```cypher
# Query: Get all insights for Sara City project

MATCH (project:L1_Project {projectName: "Sara City"})
MATCH (project) - [:HAS_L2_METRICS] -> (metrics:L2_Metric)
MATCH (metrics) - [:GENERATES_L3] -> (insights:L3_Insight)
MATCH (insights) - [:APPLIES_RULE] -> (rule:L3_Rule)
MATCH (rule) - [:RECOMMENDS_ACTION] -> (actions:L3_Action)

RETURN 
  project.projectName,
  metrics.metricName,
  metrics.value,
  insights.assessment,
  insights.narrative,
  actions.actionName,
  actions.template
```

---

## Practical Examples with LF Data

### Example 1: Sara City Deep Dive

**Project:** Sara City (Project ID: 3306)  
**Developer:** Sara Builders & Developers (Sara Group)  
**Location:** Chakan, Pune

#### L0 (Dimensions)
```
U: Units dimension (count)
L²: Area dimension (sqft)
T: Time dimension (date)
C: Cash dimension (INR)
```

#### L1 (Actual Attributes)
```
Total Units (U):           3,018 units
Unsold Units (U):          334 units (11%)
Saleable Size (L²):        411 sqft average
Possession Date (T):       December 2027
Annual Sales (C/T):        ₹106 Crore/Year
Current PSF (C/L²):        ₹3,996/sqft
```

#### L2 (Derived Metrics - AUTO CALCULATED)
```
Absorption Rate (Fraction/T):
  Formula: (2684 sold / 3018 total) / 240 months
  Result: 0.37% per month (CRITICAL)

Monthly Revenue (C/T):
  Formula: ₹106 Cr / 12 months
  Result: ₹8.83 Crore/month

Months Inventory (T):
  Formula: 334 unsold / (527 units/year ÷ 12)
  Result: 7.6 months

% Sold (Dimensionless):
  Formula: 2684 / 3018
  Result: 89% (completion level)

Price Appreciation (T^-1):
  Formula: (3996 - 2200) / 18 years
  Result: +81.6% gain over 18 years ≈ 3.3% CAGR
```

#### L3 (Insights - RULE-BASED)
```
INSIGHT 1: Sales Health - CRITICAL
Rule: R001_AbsorptionRate_SalesHealth
Trigger: AR = 0.37% < 0.5%
Assessment: CRITICAL
Narrative: "Sara City's absorption rate is critically low (0.37%/month).
At current pace, 7.6 months to sell remaining 334 units. But historically,
absorption has been inconsistent (89% sold over 18 years)."
Recommendations:
  - [HIGH] Price reduction: 7-10% (from ₹3,996 to ₹3,650 PSF)
  - [HIGH] Launch targeted marketing for 1BHK (18.5% of stock)
  - [MEDIUM] Offer incentives (early possession, bundle discounts)

INSIGHT 2: Inventory Health - GOOD
Rule: R002_MonthsInventory_InventoryHealth
Trigger: MI = 7.6 months (in range 6-12)
Assessment: GOOD
Narrative: "Inventory level is manageable. At current velocity (44 u/month),
project has 7-8 months of stock, which is healthy."
Recommendations:
  - Maintain current strategy
  - Plan inventory replenishment if velocity increases

INSIGHT 3: Price Competitiveness - OVERPRICED
Rule: R003_PriceCompetitiveness_MarketPosition
Trigger: Current PSF ₹3,996 vs. Market Median ₹3,575
Difference: +12.1% premium
Assessment: OVERPRICED
Narrative: "Sara City priced 12% above market median for Chakan.
Premium justified only if absorption is >2% per month; currently at 0.37%."
Recommendations:
  - Review pricing strategy
  - Consider tactical 3-5% reduction to align with market
```

### Example 2: Pradnyesh Shriniwas (Fast-Moving Project)

**Project:** Pradnyesh Shriniwas (Project ID: 134282)  
**Location:** Chakan, Pune

#### L1 (Attributes)
```
Total Units (U):           278 units
Unsold Units (U):          164 units (42%)
Saleable Size (L²):        562 sqft average
Possession Date (T):       May 2027
Annual Sales (C/T):        ₹24 Crore/Year
Current PSF (C/L²):        ₹3,745/sqft
```

#### L2 (Derived - AUTO CALCULATED)
```
Absorption Rate: (114 sold / 278 total) / 31 months = 1.32% per month (GOOD)
Monthly Revenue: ₹24 Cr / 12 = ₹2 Crore/month
Months Inventory: 164 unsold / (24 u/month) = 6.8 months
% Sold: 114 / 278 = 41%
Monthly Sales Velocity: 24 / 12 = 2 units/month (lower absolute velocity but better ratio)
```

#### L3 (Insights)
```
INSIGHT 1: Sales Health - GOOD
AR = 1.32% > 1% threshold
Assessment: GOOD
Narrative: "Absorption rate of 1.32% per month is healthy for a smaller project
(278 units). Project on track for May 2027 possession."
Recommendations:
  - Monitor market; prepare upsell offers
  - Plan marketing refresh 6 months before possession

INSIGHT 2: Inventory Health - GOOD
MI = 6.8 months (in range 6-12)
Assessment: GOOD
Narrative: "Inventory level healthy at 6.8 months supply."
Recommendations:
  - Maintain current strategy
```

---

## Implementation Architecture

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Graph Database** | Neo4j | Store L0-L3 entities & relationships |
| **API Framework** | FastAPI (Python) | Expose L0-L3 queries via REST/GraphQL |
| **Calculation Engine** | Python + NumPy | Calculate L2 metrics automatically |
| **Rule Engine** | Python + Configurable JSON | Evaluate L3 insights & rules |
| **AI Integration** | Claude API | Generate L3 narratives, recommendations |
| **Frontend** | Streamlit/React | Visualize L0-L3 insights |

### Data Flow Architecture

```
LF Data Extract (Quarterly)
    ↓
[L1 Loader] → Neo4j (L1 nodes created/updated)
    ↓
[L2 Calculator] → Trigger on L1 change
    ├─ Read L1 attributes
    ├─ Apply dimensional algebra formulas
    ├─ Create/Update L2 metric nodes
    └─ Establish L1→L2 relationships
    ↓
[L3 Rule Engine] → Trigger on L2 change
    ├─ Read L2 metrics
    ├─ Evaluate L3 rules against thresholds
    ├─ Create L3 insight nodes
    ├─ Call Claude API for narrative generation
    └─ Establish L2→L3 relationships
    ↓
[API Layer] → Serve queries
    ├─ GET /api/projects/{id}/l0_dimensions
    ├─ GET /api/projects/{id}/l1_attributes
    ├─ GET /api/projects/{id}/l2_metrics
    ├─ GET /api/projects/{id}/l3_insights
    └─ POST /api/projects/{id}/l3_rules (configure)
```

### Calculation Pipeline

```python
# Pseudo-code: L2 Metric Calculation

class Layer2Calculator:
    """Automatically calculates L2 metrics from L1 data"""
    
    def calculate_absorption_rate(project_l1):
        sold = project_l1.soldUnits        # U
        total = project_l1.totalUnits      # U
        months = calculate_months_elapsed(project_l1.launchDate)  # T
        
        absorption_rate = (sold / total) / months  # (U/U) / T
        return {
            'metric': 'Absorption Rate',
            'dimension': 'Fraction/T',
            'value': absorption_rate,
            'unit': 'percent_per_month'
        }
    
    def calculate_monthly_revenue(project_l1):
        annual_sales = project_l1.annualSalesValue  # C
        monthly_revenue = annual_sales / 12         # C/T
        return {
            'metric': 'Monthly Revenue',
            'dimension': 'C/T',
            'value': monthly_revenue,
            'unit': 'INR_per_month'
        }
    
    def calculate_months_inventory(project_l1, calculated_velocity):
        unsold = project_l1.unsoldUnits    # U
        velocity = calculated_velocity      # U/T
        months_inventory = unsold / (velocity / 30)  # T
        return {
            'metric': 'Months Inventory',
            'dimension': 'T',
            'value': months_inventory,
            'unit': 'months'
        }
```

### Rule Evaluation Pipeline

```python
# Pseudo-code: L3 Rule Evaluation

class Layer3Insight:
    """Evaluates L3 rules against L2 metrics"""
    
    def evaluate_absorption_rule(ar_metric, rule_config):
        ar_value = ar_metric.value  # 0.0037 for Sara City
        
        # Find matching threshold
        for threshold in rule_config.thresholds:
            if self.evaluate_condition(ar_value, threshold.condition):
                assessment = threshold.assessment  # "CRITICAL"
                actions = rule_config.get_actions_for(assessment)
                
                # Generate narrative via Claude
                narrative = self.claude_client.generate_narrative(
                    assessment=assessment,
                    metric_value=ar_value,
                    context=project_context
                )
                
                return L3_Insight(
                    assessment=assessment,
                    narrative=narrative,
                    recommendations=actions,
                    severity=self.get_severity(assessment)
                )
```

---

## API Layer & Query Routing

### REST Endpoints

```
# Layer 0: Dimensions (Read-only)
GET /api/l0/dimensions
    → Returns: All L0 dimension definitions
    
GET /api/l0/dimensions/{dimensionCode}
    → Returns: Single dimension (U, L2, T, C)

# Layer 1: Project Attributes (CRUD)
GET /api/projects/{projectId}/l1
    → Returns: All L1 attributes for project

GET /api/projects/{projectId}/l1/{attributeName}
    → Returns: Single L1 attribute value

POST /api/projects/{projectId}/l1
    → Creates/updates L1 attributes (Bulk load from LF)

# Layer 2: Derived Metrics (Calculated)
GET /api/projects/{projectId}/l2
    → Returns: All L2 metrics (auto-calculated)

GET /api/projects/{projectId}/l2/{metricName}
    → Returns: Single L2 metric

POST /api/projects/{projectId}/l2/recalculate
    → Triggers L2 recalculation (on L1 change)

# Layer 3: Insights & Rules
GET /api/projects/{projectId}/l3
    → Returns: All L3 insights

GET /api/projects/{projectId}/l3/alerts
    → Returns: Only HIGH/URGENT alerts

GET /api/rules
    → Returns: All L3 rules and thresholds

POST /api/rules/{ruleId}
    → Updates rule thresholds (admin)

POST /api/projects/{projectId}/l3/generate
    → Manually trigger L3 insight generation

# Composite Queries
GET /api/projects/{projectId}/full-analysis
    → Returns: L0 + L1 + L2 + L3 (complete picture)

GET /api/projects/compare?ids=3306,134282
    → Returns: Comparison across multiple projects
```

### Example Query Responses

```json
# GET /api/projects/3306/l0

{
  "dimensions": [
    {
      "dimensionCode": "U",
      "dimensionName": "Units/Inventory",
      "siUnit": "count",
      "physicsAnalog": "Mass (M)"
    },
    ...
  ]
}

# GET /api/projects/3306/l1

{
  "projectId": "3306",
  "projectName": "Sara City",
  "attributes": {
    "totalUnits": { "value": 3018, "dimension": "U", "unit": "count" },
    "unsoldUnits": { "value": 334, "dimension": "U", "unit": "count" },
    "unitSaleableSize": { "value": 411, "dimension": "L2", "unit": "sqft" },
    "possessionDate": { "value": "2027-12-31", "dimension": "T", "unit": "date" },
    "annualSalesValue": { "value": 10600000000, "dimension": "C/T", "unit": "INR/year" }
  }
}

# GET /api/projects/3306/l2

{
  "projectId": "3306",
  "metrics": [
    {
      "metricId": "L2_AR_3306",
      "metricName": "Absorption Rate",
      "dimension": "Fraction/T",
      "value": 0.0037,
      "unit": "percent_per_month",
      "calculatedAt": "2025-11-27",
      "formula": "(2684 / 3018) / 240 months"
    },
    ...
  ]
}

# GET /api/projects/3306/l3

{
  "projectId": "3306",
  "insights": [
    {
      "insightId": "L3_SalesHealth_3306",
      "assessment": "CRITICAL",
      "severity": "HIGH",
      "narrative": "Sara City's absorption rate of 0.37% per month is critically low...",
      "recommendations": [
        {
          "priority": "HIGH",
          "action": "Price Reduction",
          "detail": "Consider 7-10% reduction from ₹3,996 PSF to ₹3,650-3,700 PSF"
        },
        ...
      ]
    },
    ...
  ]
}

# GET /api/projects/3306/full-analysis

{
  "l0_dimensions": [...],
  "l1_attributes": {...},
  "l2_metrics": [...],
  "l3_insights": [...],
  "summary": {
    "projectName": "Sara City",
    "overallHealth": "CRITICAL",
    "topAlerts": 2,
    "lastUpdated": "2025-11-27"
  }
}
```

---

## Acceptance Criteria

### Functional Requirements

| # | Requirement | Validation | Status |
|---|---|---|---|
| 1 | **L0 Immutability** | All L0 dimension definitions cannot be modified after creation | ✓ |
| 2 | **L1 Data Integrity** | L1 attributes are sourced directly from LF data; no manual calculation | ✓ |
| 3 | **L2 Auto-Calculation** | L2 metrics auto-calculate on L1 change within 5 seconds | ✓ |
| 4 | **L2 Dimensional Consistency** | All L2 formulas validate dimensional analysis (no unit mismatches) | ✓ |
| 5 | **L3 Rule Evaluation** | L3 insights auto-generate on L2 change; rules are configurable | ✓ |
| 6 | **L3 Narrative Generation** | Claude generates contextual narratives for each L3 insight | ✓ |
| 7 | **L3 Recommendations** | Actionable, specific recommendations provided with each insight | ✓ |
| 8 | **Rule Persistence** | L3 rules stored as Neo4j nodes; changes logged and audited | ✓ |
| 9 | **API Completeness** | All L0-L3 layers accessible via REST/GraphQL endpoints | ✓ |
| 10 | **Data Lineage** | Query any L3 insight and trace back to L0 dimensions | ✓ |

### Non-Functional Requirements

| # | Requirement | Acceptance Criteria |
|---|---|---|
| 1 | **Performance** | L2 calculation <2 sec; L3 insight generation <5 sec for single project |
| 2 | **Scalability** | Support 10,000+ projects; Neo4j queries return <500ms |
| 3 | **Data Freshness** | L1 data updated quarterly; L2/L3 refreshed within 1 hour of L1 update |
| 4 | **Auditability** | All L3 rules changes logged with timestamp, user, before/after values |
| 5 | **Reliability** | 99.5% uptime; graceful fallback if LF data unavailable |
| 6 | **Security** | LF data encrypted in transit; API keys in secrets manager; row-level access control |

### Data Quality Standards

| # | Standard | Validation |
|---|---|---|
| 1 | **L0 Completeness** | All four dimensions (U, L², T, C) defined and immutable |
| 2 | **L1 Accuracy** | L1 values match LF data within 0.1% tolerance |
| 3 | **L2 Validation** | L2 metrics match manual calculations within ±2% |
| 4 | **L3 Calibration** | L3 rule thresholds reviewed by domain experts quarterly |
| 5 | **Missing Data Handling** | L2 metrics gracefully handle missing L1 values; output marked "INCOMPLETE" |

---

## Example: Complete Sara City Trace (L0 → L3)

```
PROJECT: Sara City (ID: 3306)

LAYER 0 (Immutable Dimensions):
├─ Dimension U (Units)
├─ Dimension L² (Area)
├─ Dimension T (Time)
└─ Dimension C (Cash Flow)

LAYER 1 (LF Data):
├─ totalUnits = 3,018 U
├─ unsoldUnits = 334 U
├─ soldUnits = 2,684 U
├─ unitSaleableSize = 411 L²
├─ totalSaleableArea = 1,241,298 L²
├─ launchDate = 2007-11 T
├─ possessionDate = 2027-12 T
├─ projectDurationMonths = 240 T
├─ launchPrice_PSF = 2,200 C/L²
├─ currentPrice_PSF = 3,996 C/L²
└─ annualSalesValue = 106 Cr C/T

LAYER 2 (Calculated Metrics):
├─ absorptionRate = (2684/3018)/240 = 0.37% U/T → CRITICAL
├─ monthlyRevenue = 106 Cr / 12 = 8.83 Cr C/T
├─ monthsInventory = 334 / (44 u/month) = 7.6 T
├─ percentSold = 2684/3018 = 89% Dimensionless
├─ priceAppreciation = (3996-2200)/18 = +3.3% CAGR T^-1
├─ density = 3018 / 70000 = 0.043 U/L²
└─ costPerUnit = 500Cr / 3018 = 16.5 Lac C/U

LAYER 3 (Rule-Based Insights):
├─ INSIGHT 1: Sales Health
│  ├─ Rule: R001_AbsorptionRate_SalesHealth
│  ├─ Assessment: CRITICAL (AR < 0.5%)
│  ├─ Severity: HIGH
│  └─ Recommendations:
│     ├─ [HIGH] Price reduction 7-10%
│     ├─ [HIGH] Marketing campaign for 1BHK
│     └─ [MEDIUM] Promotional incentives
│
├─ INSIGHT 2: Inventory Health
│  ├─ Rule: R002_MonthsInventory_InventoryHealth
│  ├─ Assessment: GOOD (MI 6-12 months)
│  ├─ Severity: LOW
│  └─ Recommendations:
│     └─ Maintain current strategy
│
└─ INSIGHT 3: Price Competitiveness
   ├─ Rule: R003_PriceCompetitiveness_MarketPosition
   ├─ Assessment: OVERPRICED (+12.1% vs market)
   ├─ Severity: MEDIUM
   └─ Recommendations:
      └─ Review pricing; consider 3-5% reduction
```

---

## Next Steps & Questions Clarification

### Questions for Refinement:

1. **L3 Rule Update Frequency:** How often should L3 rules be reviewed/updated? (Quarterly, semi-annually?)

2. **Multi-Metric L3 Rules:** Should L3 insights combine multiple L2 metrics? (E.g., "If AR < 1% AND MI > 18 months, CRITICAL")

3. **Claude Integration:** How detailed should Claude-generated narratives be? (1-sentence, paragraph, multi-paragraph with comparable projects?)

4. **Recommendation Prioritization:** Should L3 recommendations be prioritized for the developer? (Top 3 actions vs. all actions?)

5. **Historical Tracking:** Should L3 insights maintain history? (Track how assessment changed over time?)

6. **Market Benchmarking:** How should market comparison be done? (Per micromarket, per city, per project type?)

7. **Real-Time vs. Batch:** Should L2/L3 recalculate in real-time on LF data change, or batch weekly?

---

**PRD Version 3.0 | Status: Production-Ready | Date: November 30, 2025**

**Architecture: Neo4j + FastAPI + Claude Integration**  
**Layer Stack: L0 (Schema) → L1 (Data) → L2 (Metrics) → L3 (Insights)**  
**Ready for: Implementation Sprint Q1 FY26**
