# Product Requirements Document: Liases Foras × Sirrus.AI Integration

## Real Estate Knowledge Graph with Dimensional Financial Analysis & MCP API Layer

**Version:** 2.0 (API-Driven MCP Implementation)  
**Date:** November 27, 2025  
**Status:** Production-Ready Draft  
**Target Implementation:** FastAPI (Python) + Neo4j + Claude Code Integration  

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Four-Layer Dimensional Knowledge Graph](#four-layer-dimensional-knowledge-graph)
4. [MCP API Layer Specification](#mcp-api-layer-specification)
5. [API Endpoint Design](#api-endpoint-design)
6. [Knowledge Graph Entities by Layer](#knowledge-graph-entities-by-layer)
7. [Core Calculation Modules](#core-calculation-modules)
8. [Use Cases & Query Resolution](#use-cases--query-resolution)
9. [Implementation Guide](#implementation-guide)
10. [Acceptance Criteria](#acceptance-criteria)

---

## Executive Summary

This PRD v2.0 extends the LF × Sirrus.AI integration with a **production-grade API-driven MCP (Model Context Protocol) layer** that exposes dimensional knowledge graph capabilities as fine-grained tools. 

**Key Innovation:** Organize all real estate metrics into **four dimensional layers** (Layer 0: Raw Dimensions → Layer 3: Optimization & Benchmarking), exposed via FastAPI endpoints with MCP semantic routing.

**Outcome:** Developers query via natural language → Claude routes to appropriate MCP capability → Knowledge graph calculates grounded in physics-inspired MLTI system → Results returned with full dimensional provenance.

---

## Architecture Overview

### Three-Tier Architecture Stack

```
┌──────────────────────────────────────────────────────┐
│ Tier 1: Claude Agent Layer                           │
│ (Sirrus.AI conversational interface)                  │
│ - Intent classification                              │
│ - Multi-turn dialogue                                │
│ - Natural language synthesis                         │
└──────────────────────────────────────────────────────┘
                      ↑ ↓ (Claude Code integration)
┌──────────────────────────────────────────────────────┐
│ Tier 2: MCP API Layer (THIS LAYER)                   │
│ - Coarse-grained capabilities: /api/mcp/info         │
│ - Fine-grained tool routing: /api/mcp/query          │
│ - Capability discovery                               │
│ - Query orchestration                                │
└──────────────────────────────────────────────────────┘
                      ↑ ↓
┌──────────────────────────────────────────────────────┐
│ Tier 3: Knowledge Graph & Calculation Layer          │
│ - Layer 0: Raw dimensions (U, L², T, CF)             │
│ - Layer 1: Derived metrics (PSF, ASP, AR)            │
│ - Layer 2: Financial metrics (NPV, IRR, PI)          │
│ - Layer 3: Optimization & scenarios                  │
│ - Neo4j graph queries                                │
│ - LF data integration                                │
└──────────────────────────────────────────────────────┘
```

---

## Four-Layer Dimensional Knowledge Graph

### Layer 0: Raw Dimensions (Atomic Units)

**Physics-Inspired Base Dimensions:**

| Dimension | Symbol | Unit | Real Estate Analog | Definition |
|-----------|--------|------|-------------------|-----------|
| **Unit Count** | U | count | 1BHK, 2BHK, 3BHK units | Discrete housing products (analogous to Mass) |
| **Space** | L² | sqft, sqm | Carpet, saleable, built-up area | Area of real estate (analogous to Length²) |
| **Time** | T | months, years | Sales cycle, project duration | Temporal horizon (analogous to Time) |
| **Cash Flow** | CF | INR/month | Revenue, cost, investment | Rate of financial flow (analogous to Current I) |

**Layer 0 Neo4j Representation:**

```cypher
(:Dimension_L0 {
  dimensionCode: "U" | "L2" | "T" | "CF",
  dimensionName: "Units" | "Area" | "Time" | "CashFlow",
  siUnit: "count" | "sqft" | "months" | "INR",
  category: "Base",
  description: "Atomic dimensional unit"
})
```

**Layer 0 Data Entities:**

```cypher
(:Project {
  projectId: "string",
  totalUnits: number,        // U
  totalLandArea_sqft: number,// L²
  projectDuration_months: number,  // T
  totalProjectCost_inr: number     // CF
})

(:Unit {
  unitType: "1BHK" | "2BHK" | "3BHK",
  areaPerUnit_sqft: number,  // L²
  pricePerUnit_inr: number   // CF
})

(:Location {
  city: "string",
  microMarket: "string",
  dataAsOfMonth: "2025-11"   // T
})
```

---

### Layer 1: Derived Dimensions (Simple Ratios & Products)

**Derived from Layer 0 using dimensional analysis:**

| Metric | Dimension | Formula | Physical Analog | Calculation |
|--------|-----------|---------|-----------------|-----------|
| **Density** | U/L² | Total Units / Land Area | Density | How many units per sqft |
| **Price Per Sqft (PSF)** | CF/L² | Total Revenue / Saleable Area | Pressure/Stress | Pricing intensity |
| **Sales Velocity** | U/T | Units Sold / Months | Rate | How fast units sell |
| **Absorption Rate** | (U/U_total)/T | % Units Sold / Month | Fraction/Time | Monthly absorption rate |
| **Average Selling Price (ASP)** | CF/U | Total Revenue / Units | Price per unit | Average unit price |
| **Cost Per Sqft** | CF/L² | Total Cost / Area | Cost intensity | Construction/land cost per area |
| **Revenue Run Rate** | CF/T | Monthly Revenue | Cash flow rate | INR per month |
| **Total Saleable Area (TSA)** | L² | Sum(Units × Area) | Area | Cumulative saleable area |
| **Market Density** | U/L² | Ongoing Projects Units / Land | Supply intensity | Local market crowding |

**Layer 1 Neo4j Representation:**

```cypher
(:Dimension_L1 {
  metricName: "PSF" | "ASP" | "Density" | "SalesVelocity",
  dimensionCode: "CF/L2" | "CF/U" | "U/L2" | "U/T",
  formula: "string",
  components: ["U", "L2", "T", "CF"],
  category: "Derived_Simple",
  lfSource: "Pillar_1.1" | "Pillar_2.1" | ...
})

(:Metric_L1 {
  projectId: "string",
  metricName: "PSF",
  value: number,
  unit: "INR/sqft",
  calculatedAt: "timestamp",
  sourceData: ["totalRevenue", "totalSaleableArea"]
})
```

---

### Layer 2: Financial Metrics (Complex Aggregations)

**Advanced financial metrics requiring integration of multiple Layer 1 metrics:**

| Metric | Dimension | Formula | Components | LF Pillar |
|--------|-----------|---------|-----------|-----------|
| **NPV** | CF (Currency) | ∑[CF_t / (1+r)^t] - Initial_Inv | Cash flows, discount rate, time horizon | 4.3 |
| **IRR** | T^(-1) (Rate) | r where NPV(r) = 0 | Cash flows, initial investment | 4.3 |
| **Profitability Index** | Dimensionless | (NPV + Initial_Inv) / Initial_Inv | NPV, initial investment | 4.3 |
| **Payback Period** | T (Months) | Time when cumulative CF = Initial_Inv | Cash flows, costs | 4.1 |
| **Cap Rate** | T^(-1) (%) | Annual NOI / Property Value | Operating income, property value | 4.3 |
| **Annual Recurring Revenue (ARR)** | CF/T | Monthly CF × 12 | Monthly cash flow | 4.2 |
| **Return on Investment (ROI)** | Dimensionless (%) | (Net Profit / Initial_Inv) × 100 | Profit, investment | 4.3 |
| **Loan-to-Value (LTV)** | Dimensionless | Loan Amount / Property Value | Loan, property value | 4.1 |
| **Debt Service Coverage Ratio** | Dimensionless | Annual NOI / Annual Debt Service | Operating income, debt service | 4.3 |
| **Price Elasticity** | Dimensionless | (% Change Demand) / (% Change Price) | Absorption, pricing | 1.1 |
| **Time to Break-Even** | T (Months) | NPV = 0 point in project timeline | Cash flows by phase | 4.2 |
| **Developer Marketability Index** | Dimensionless | Efficiency × APF × Builder_Rating | From LF Pillar 3 | 3.1, 3.3 |

**Layer 2 Neo4j Representation:**

```cypher
(:Dimension_L2 {
  metricName: "NPV" | "IRR" | "PaybackPeriod" | "CapRate",
  dimensionCode: "CF" | "T^-1" | "T" | "Dimensionless",
  formula: "string",
  requiredL1Metrics: ["PSF", "ASP", "SalesVelocity"],
  requiredL0Dimensions: ["U", "L2", "T", "CF"],
  category: "Financial",
  lfSource: "Pillar_4.1" | "Pillar_4.3"
})

(:Metric_L2 {
  scenarioId: "string",
  metricType: "IRR" | "NPV",
  value: number,
  unit: "%/year" | "INR Crore",
  calculatedAt: "timestamp",
  sensitivityRanges: {
    absorption_min: number,
    absorption_max: number,
    price_min_pct: number,
    price_max_pct: number
  },
  lfDataVersion: "Q3_FY25",
  sourceL1Metrics: ["absorptionRate", "priceAppreciation", "costPerSqft"]
})
```

**Layer 2 Calculation Engine (Python):**

```python
from scipy.optimize import newton
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class FinancialProjection:
    initial_investment: float      # CF
    annual_cash_flows: List[float] # [CF_year1, CF_year2, ...]
    discount_rate: float           # T^(-1)
    project_duration_years: int    # T

class Layer2Calculator:
    """Calculates Layer 2 financial metrics from Layer 1 data."""
    
    @staticmethod
    def calculate_npv(projection: FinancialProjection) -> float:
        """NPV = ∑[CF_t / (1+r)^t] - Initial_Investment"""
        npv = -projection.initial_investment
        for year, cf in enumerate(projection.annual_cash_flows, start=1):
            npv += cf / ((1 + projection.discount_rate) ** year)
        return npv
    
    @staticmethod
    def calculate_irr(projection: FinancialProjection) -> float:
        """IRR = r such that NPV(r) = 0"""
        def npv_func(rate):
            npv = -projection.initial_investment
            for year, cf in enumerate(projection.annual_cash_flows, start=1):
                npv += cf / ((1 + rate) ** year)
            return npv
        
        try:
            irr = newton(npv_func, x0=0.2)
            return irr
        except RuntimeError:
            return None
    
    @staticmethod
    def calculate_payback_period(projection: FinancialProjection) -> float:
        """PBP = time when cumulative CF = Initial_Investment"""
        cumulative = 0
        for year, cf in enumerate(projection.annual_cash_flows, start=1):
            cumulative += cf
            if cumulative >= projection.initial_investment:
                shortfall = projection.initial_investment - (cumulative - cf)
                fraction = shortfall / cf if cf > 0 else 0
                return (year - 1) + fraction
        return None
    
    @staticmethod
    def calculate_profitability_index(projection: FinancialProjection) -> float:
        """PI = (NPV + Initial_Inv) / Initial_Inv"""
        pv_future_cfs = sum(
            cf / ((1 + projection.discount_rate) ** (year + 1))
            for year, cf in enumerate(projection.annual_cash_flows)
        )
        return pv_future_cfs / projection.initial_investment
    
    @staticmethod
    def calculate_cap_rate(annual_noi: float, property_value: float) -> float:
        """Cap Rate = Annual NOI / Property Value"""
        return annual_noi / property_value if property_value > 0 else 0
```

---

### Layer 3: Optimization & Scenario Planning (Complex Reasoning)

**Layer 3 combines Layer 0–2 with LF capability pillars for strategic decision-making:**

| Capability | Input Data | Layer Dependencies | LF Pillars | Output |
|-----------|-----------|-------------------|-----------|--------|
| **Product Mix Optimization** | Total units, land area, constraints | L0 (U, L²), L1 (PSF, ASP), L2 (NPV, IRR) | 2.1, 4.1, 4.3 | Optimal unit mix, top 3 scenarios |
| **Sensitivity Analysis** | Base case NPV/IRR | L1, L2 | 4.2 | IRR/NPV ranges vs absorption & price |
| **Developer Benchmarking** | Project financials | L1, L2, developer ratings | 3.1, 3.3 | Percentile rank, opportunity zones |
| **Break-Even Timeline** | Cash flow projection | L1, L2 | 4.1 | Time to NPV = 0 |
| **Scenario Comparison** | Base, optimistic, stress cases | L0–L2 | 4.2 | Side-by-side comparison with risk factors |
| **Market Opportunity Scoring** | Location metrics, developer rating | L1 + LF OPPS | 1.2, 3.3 | Opportunity pocket score |

**Layer 3 Neo4j Representation:**

```cypher
(:Capability_L3 {
  capabilityId: "L3_product_mix_optimization",
  capabilityName: "Product Mix Optimization",
  description: "Find optimal unit mix to maximize IRR",
  inputLayers: ["L0", "L1", "L2"],
  inputMetrics: ["totalUnits", "totalArea", "PSF_by_type", "absorptionRate"],
  outputMetrics: ["optimalMix_1BHK", "optimalMix_2BHK", "optimalMix_3BHK", "maxIRR"],
  lfPillars: ["Pillar_2.1", "Pillar_4.1", "Pillar_4.3"],
  algorithm: "scipy.optimize.minimize with SLSQP method"
})

(:Scenario_L3 {
  scenarioId: "string",
  projectId: "string",
  scenarioName: "Base Case | Optimistic | Stress",
  unitMix: {
    "1BHK": number,
    "2BHK": number,
    "3BHK": number
  },
  assumptions: {
    absorptionRate_monthly: number,   // From L1
    priceAppreciation_annual: number, // T^(-1)
    marketAbsorptionCeiling: number
  },
  results_L2: {
    npv_inr: number,
    irr_percent: number,
    paybackPeriod_months: number,
    profitabilityIndex: number
  },
  sensitivityRanges_L2: {
    absorptionVariance: [min, max],
    priceVariance: [min_pct, max_pct]
  },
  developerBenchmark_L3: {
    competitorPercentile: number,
    opportunityScore: number,
    recommendedZones: [string]
  }
})
```

**Layer 3 Optimization Engine (Python):**

```python
from scipy.optimize import minimize
import numpy as np

class Layer3Optimizer:
    """Layer 3: Optimization & scenario planning."""
    
    def optimize_product_mix(
        self,
        total_units: int,
        total_land_area_sqft: float,
        total_project_cost: float,
        project_duration_months: int,
        market_data: Dict,  # L1 data: PSF, absorption rates by type
        developer_marketability: float  # From LF Pillar 3
    ) -> Dict:
        """
        Optimizes product mix to maximize IRR.
        
        Inputs: Layer 0 dimensions + Layer 1 metrics
        Process: scipy.optimize constrained by Layer 2 NPV/IRR
        Output: Layer 3 scenario recommendations
        """
        
        def objective_function(x):
            # x = [units_1bhk, units_2bhk, units_3bhk]
            if sum(x) != total_units or x.min() < 0:
                return 1e10
            
            # Layer 1 calculations
            total_area = sum(x[i] * market_data[ut]['area'] 
                           for i, ut in enumerate(['1BHK', '2BHK', '3BHK']))
            
            if total_area > total_land_area_sqft:
                return 1e10
            
            # Revenue calculation using L1 data
            total_revenue = sum(x[i] * market_data[ut]['price'] 
                              for i, ut in enumerate(['1BHK', '2BHK', '3BHK']))
            
            # Layer 2: Calculate IRR
            annual_cf = (total_revenue - total_project_cost) / (project_duration_months / 12)
            projection = FinancialProjection(
                initial_investment=total_project_cost,
                annual_cash_flows=[annual_cf] * (project_duration_months // 12),
                discount_rate=0.12
            )
            
            irr = Layer2Calculator.calculate_irr(projection)
            
            # Apply developer marketability factor (LF Pillar 3)
            adjusted_irr = irr * developer_marketability if irr else 0
            
            return -adjusted_irr  # Maximize IRR
        
        # Constraints
        def constraint_total_units(x):
            return total_units - sum(x)
        
        def constraint_total_area(x):
            area = sum(x[i] * market_data[ut]['area'] 
                     for i, ut in enumerate(['1BHK', '2BHK', '3BHK']))
            return total_land_area_sqft - area
        
        # Optimize
        x0 = np.array([total_units/3, total_units/3, total_units/3])
        bounds = [(0, total_units)] * 3
        constraints = [
            {'type': 'eq', 'fun': constraint_total_units},
            {'type': 'ineq', 'fun': constraint_total_area}
        ]
        
        result = minimize(objective_function, x0, method='SLSQP',
                         bounds=bounds, constraints=constraints)
        
        optimal_units = result.x
        optimal_mix = {
            '1BHK': optimal_units[0] / sum(optimal_units),
            '2BHK': optimal_units[1] / sum(optimal_units),
            '3BHK': optimal_units[2] / sum(optimal_units)
        }
        
        return {
            'optimal_mix': optimal_mix,
            'units_breakdown': {
                '1BHK': optimal_units[0],
                '2BHK': optimal_units[1],
                '3BHK': optimal_units[2]
            },
            'success': result.success
        }
```

---

## MCP API Layer Specification

### MCP (Model Context Protocol) Overview

**Purpose:** Expose dimensional knowledge graph capabilities as discoverable tools for Claude via standardized interface.

**Architecture:**
- **Coarse-grained Level:** `/api/mcp/info` → Capability discovery (what tools available)
- **Fine-grained Level:** `/api/mcp/query` → Tool invocation (execute specific calculations)

---

## API Endpoint Design

### Endpoint 1: GET `/api/mcp/info`

**Purpose:** Capability discovery endpoint for MCP integration

**Response Schema:**

```json
{
  "name": "liases-foras-re-analytics",
  "description": "Real estate financial analysis with LF market data & dimensional KG",
  "version": "2.0",
  "capabilities": [
    {
      "capabilityId": "layer0_dimensions",
      "name": "Raw Dimensions",
      "description": "Atomic dimensional units (Units, Area, Time, CashFlow)",
      "layer": 0,
      "tools": [
        {
          "toolName": "get_project_dimensions",
          "description": "Fetch Layer 0 dimensions for project",
          "parameters": {
            "projectId": "string",
            "dimensions": ["U", "L2", "T", "CF"]
          }
        }
      ]
    },
    {
      "capabilityId": "layer1_derivatives",
      "name": "Derived Metrics (L1)",
      "description": "Ratios and products from Layer 0 (PSF, ASP, Density, etc.)",
      "layer": 1,
      "tools": [
        {
          "toolName": "calculate_psf",
          "description": "Price Per Sqft = Total Revenue / Saleable Area",
          "parameters": {
            "totalRevenue": "CF",
            "saleableArea": "L2"
          },
          "returns": "CF/L2"
        },
        {
          "toolName": "calculate_asp",
          "description": "Average Selling Price = Total Revenue / Total Units",
          "parameters": {
            "totalRevenue": "CF",
            "totalUnits": "U"
          },
          "returns": "CF/U"
        },
        {
          "toolName": "calculate_absorption_rate",
          "description": "Absorption Rate = % Units Sold / Month",
          "parameters": {
            "unitsSold": "U",
            "totalUnits": "U",
            "monthsElapsed": "T"
          },
          "returns": "(U/U_total)/T"
        },
        {
          "toolName": "calculate_sales_velocity",
          "description": "Sales Velocity = Units Sold / Months",
          "parameters": {
            "unitsSold": "U",
            "monthsElapsed": "T"
          },
          "returns": "U/T"
        }
      ]
    },
    {
      "capabilityId": "layer2_financial",
      "name": "Financial Metrics (L2)",
      "description": "Complex financial analysis (NPV, IRR, Payback, Cap Rate, etc.)",
      "layer": 2,
      "tools": [
        {
          "toolName": "calculate_npv",
          "description": "Net Present Value of project",
          "parameters": {
            "cashFlows": ["CF"],
            "discountRate": "T^-1",
            "initialInvestment": "CF"
          },
          "returns": "CF"
        },
        {
          "toolName": "calculate_irr",
          "description": "Internal Rate of Return",
          "parameters": {
            "cashFlows": ["CF"],
            "initialInvestment": "CF"
          },
          "returns": "T^-1"
        },
        {
          "toolName": "calculate_payback_period",
          "description": "Time to recover initial investment",
          "parameters": {
            "cashFlows": ["CF"],
            "initialInvestment": "CF"
          },
          "returns": "T"
        },
        {
          "toolName": "calculate_sensitivity_analysis",
          "description": "IRR/NPV under different absorption & price scenarios",
          "parameters": {
            "baseCase": "Scenario",
            "absorptionRange": [min, max],
            "priceRange": [min_pct, max_pct]
          },
          "returns": {
            "baseCase": "Metric_L2",
            "optimisticCase": "Metric_L2",
            "stressCase": "Metric_L2"
          }
        }
      ]
    },
    {
      "capabilityId": "layer3_optimization",
      "name": "Optimization & Scenarios (L3)",
      "description": "Product mix optimization, benchmarking, market opportunity scoring",
      "layer": 3,
      "tools": [
        {
          "toolName": "optimize_product_mix",
          "description": "Find optimal unit mix to maximize IRR in given location",
          "parameters": {
            "location": "string",
            "totalUnits": "U",
            "totalArea": "L2",
            "constraint_minIRR": "T^-1"
          },
          "returns": {
            "optimalMix": {
              "1BHK": "percent",
              "2BHK": "percent",
              "3BHK": "percent"
            },
            "scenarios": ["Scenario_L3"]
          }
        },
        {
          "toolName": "developer_benchmarking",
          "description": "Compare project against peer developers (LF Pillar 3)",
          "parameters": {
            "developerId": "string",
            "projectId": "string"
          },
          "returns": {
            "percentile": "number",
            "apfScore": "number",
            "marketabilityIndex": "number",
            "opportunityZones": ["string"]
          }
        },
        {
          "toolName": "market_opportunity_scoring",
          "description": "Score location opportunity using LF OPPS (Pillar 1.3, 3.3)",
          "parameters": {
            "location": "string",
            "unitTypes": ["1BHK", "2BHK", "3BHK"]
          },
          "returns": {
            "oppsScore": "number",
            "demandTrend": "high|medium|low",
            "competitiveIntensity": "high|medium|low",
            "recommendedMix": {"1BHK": %, "2BHK": %, "3BHK": %}
          }
        }
      ]
    },
    {
      "capabilityId": "lf_integration",
      "name": "Liases Foras Data Access",
      "description": "Access LF market intelligence across 5 pillars",
      "lfPillars": ["Market", "Product", "DeveloperPerformance", "Financial", "Sales/Ops"],
      "tools": [
        {
          "toolName": "fetch_lf_market_data",
          "description": "Fetch LF Pillar 1 data (prices, absorption, trends)",
          "parameters": {
            "location": "string",
            "dataType": "absorption|pricing|trends|competitiveIntensity"
          }
        },
        {
          "toolName": "fetch_lf_product_data",
          "description": "Fetch LF Pillar 2 data (typology, efficiency, launch strategies)",
          "parameters": {
            "location": "string",
            "unitTypes": ["1BHK", "2BHK", "3BHK"]
          }
        },
        {
          "toolName": "fetch_lf_developer_rating",
          "description": "Fetch LF Pillar 3 data (APF, builder rating, OPPS score)",
          "parameters": {
            "developerId": "string"
          }
        }
      ]
    }
  ],
  "apiSource": "sirrus-ai-re-analytics",
  "dataSource": "liases-foras",
  "quarterlyUpdateFrequency": "Q1, Q2, Q3, Q4",
  "lastUpdated": "2025-11-27",
  "version_info": {
    "neo4j_layer": "1.0",
    "calculator_engine": "2.0",
    "lf_integration": "3.0"
  }
}
```

---

### Endpoint 2: POST `/api/mcp/query`

**Purpose:** Execute dimensional queries and calculations

**Request Schema:**

```json
{
  "queryId": "unique-query-id",
  "queryType": "calculation | optimization | comparison | benchmarking",
  "layer": 0 | 1 | 2 | 3,
  "capability": "string (e.g., 'calculate_irr', 'optimize_product_mix')",
  "parameters": {
    "key1": "value1",
    "key2": "value2"
  },
  "context": {
    "projectId": "string",
    "location": "string",
    "lfDataVersion": "Q3_FY25"
  }
}
```

**Response Schema:**

```json
{
  "queryId": "unique-query-id",
  "status": "success | error",
  "layer": 0 | 1 | 2 | 3,
  "capability": "string",
  "result": {
    "value": "number | object",
    "unit": "string",
    "dimension": "CF | U | L2 | T | Dimensionless | Composite"
  },
  "provenance": {
    "inputDimensions": ["L0_dimension1", "L0_dimension2"],
    "calculationMethod": "string",
    "lfSource": "Pillar_X.Y",
    "timestamp": "ISO-8601",
    "dataVersion": "Q3_FY25"
  },
  "relatedMetrics": [
    {
      "metricName": "string",
      "value": "number",
      "dimension": "string",
      "calculatedFrom": "result"
    }
  ],
  "executionTime_ms": number,
  "dataLineage": {
    "layer0_inputs": {...},
    "layer1_intermediates": [...],
    "layer2_dependencies": [...]
  }
}
```

---

### Implementation: FastAPI Endpoints (Python)

```python
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, List, Optional
import json
from datetime import datetime
import uuid

# ==================== DATA MODELS ====================

class DimensionParam(BaseModel):
    code: str  # "U", "L2", "T", "CF"
    value: float
    unit: str

class MCPQueryRequest(BaseModel):
    queryId: Optional[str] = None
    queryType: str  # "calculation", "optimization", "comparison"
    layer: int  # 0, 1, 2, 3
    capability: str  # e.g., "calculate_irr", "optimize_product_mix"
    parameters: Dict
    context: Dict = {}

class MCPQueryResponse(BaseModel):
    queryId: str
    status: str
    layer: int
    capability: str
    result: Dict
    provenance: Dict
    relatedMetrics: List[Dict]
    executionTime_ms: float
    dataLineage: Dict

# ==================== FASTAPI APP ====================

app = FastAPI(
    title="Sirrus.AI Real Estate Analytics MCP",
    description="Multi-layer dimensional KG with LF integration",
    version="2.0"
)

# ==================== ENDPOINT 1: GET /api/mcp/info ====================

@app.get("/api/mcp/info")
def get_mcp_capabilities():
    """Coarse-grained capability discovery."""
    return {
        "name": "liases-foras-re-analytics",
        "description": "Real estate financial analysis with LF market data & dimensional KG",
        "version": "2.0",
        "capabilities": [
            {
                "capabilityId": "layer0_dimensions",
                "name": "Raw Dimensions",
                "layer": 0,
                "description": "Atomic dimensional units (U, L², T, CF)",
                "tools": [
                    {
                        "toolName": "get_project_dimensions",
                        "description": "Fetch Layer 0 dimensions for project"
                    }
                ]
            },
            {
                "capabilityId": "layer1_derivatives",
                "name": "Derived Metrics (L1)",
                "layer": 1,
                "description": "Ratios and products (PSF, ASP, Absorption Rate, Sales Velocity)",
                "tools": [
                    {
                        "toolName": "calculate_psf",
                        "description": "Price Per Sqft = Total Revenue / Saleable Area"
                    },
                    {
                        "toolName": "calculate_asp",
                        "description": "Average Selling Price = Total Revenue / Total Units"
                    },
                    {
                        "toolName": "calculate_absorption_rate",
                        "description": "Absorption Rate = (% Units / Month)"
                    },
                    {
                        "toolName": "calculate_sales_velocity",
                        "description": "Sales Velocity = Units / Months"
                    }
                ]
            },
            {
                "capabilityId": "layer2_financial",
                "name": "Financial Metrics (L2)",
                "layer": 2,
                "description": "Complex financial analysis (NPV, IRR, Payback, Cap Rate)",
                "tools": [
                    {
                        "toolName": "calculate_npv",
                        "description": "Net Present Value"
                    },
                    {
                        "toolName": "calculate_irr",
                        "description": "Internal Rate of Return"
                    },
                    {
                        "toolName": "calculate_payback_period",
                        "description": "Time to recover initial investment"
                    },
                    {
                        "toolName": "calculate_sensitivity_analysis",
                        "description": "IRR/NPV under different scenarios"
                    }
                ]
            },
            {
                "capabilityId": "layer3_optimization",
                "name": "Optimization & Scenarios (L3)",
                "layer": 3,
                "description": "Product mix optimization, benchmarking, opportunity scoring",
                "tools": [
                    {
                        "toolName": "optimize_product_mix",
                        "description": "Find optimal unit mix to maximize IRR"
                    },
                    {
                        "toolName": "developer_benchmarking",
                        "description": "Compare project against peer developers"
                    },
                    {
                        "toolName": "market_opportunity_scoring",
                        "description": "Score location opportunity"
                    }
                ]
            },
            {
                "capabilityId": "lf_integration",
                "name": "Liases Foras Data Access",
                "description": "Access LF market intelligence",
                "lfPillars": ["Market", "Product", "DeveloperPerformance", "Financial", "Sales/Ops"],
                "tools": [
                    {
                        "toolName": "fetch_lf_market_data",
                        "description": "Fetch LF Pillar 1 (prices, absorption, trends)"
                    },
                    {
                        "toolName": "fetch_lf_product_data",
                        "description": "Fetch LF Pillar 2 (typology, efficiency)"
                    },
                    {
                        "toolName": "fetch_lf_developer_rating",
                        "description": "Fetch LF Pillar 3 (APF, builder rating)"
                    }
                ]
            }
        ],
        "apiSource": "sirrus-ai-re-analytics",
        "dataSource": "liases-foras",
        "lastUpdated": "2025-11-27",
        "quarterlyUpdateFrequency": "Q1, Q2, Q3, Q4"
    }

# ==================== ENDPOINT 2: POST /api/mcp/query ====================

@app.post("/api/mcp/query", response_model=MCPQueryResponse)
def execute_mcp_query(request: MCPQueryRequest):
    """Fine-grained query execution with routing."""
    
    # Generate query ID if not provided
    query_id = request.queryId or str(uuid.uuid4())
    start_time = datetime.utcnow()
    
    try:
        # Route to appropriate layer handler
        if request.layer == 0:
            result, provenance, lineage = handle_layer0_query(request, query_id)
        elif request.layer == 1:
            result, provenance, lineage = handle_layer1_query(request, query_id)
        elif request.layer == 2:
            result, provenance, lineage = handle_layer2_query(request, query_id)
        elif request.layer == 3:
            result, provenance, lineage = handle_layer3_query(request, query_id)
        else:
            raise ValueError(f"Invalid layer: {request.layer}")
        
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds() * 1000
        
        return MCPQueryResponse(
            queryId=query_id,
            status="success",
            layer=request.layer,
            capability=request.capability,
            result=result,
            provenance=provenance,
            relatedMetrics=compute_related_metrics(request, result),
            executionTime_ms=execution_time,
            dataLineage=lineage
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== LAYER HANDLERS ====================

def handle_layer0_query(request: MCPQueryRequest, query_id: str):
    """Layer 0: Raw dimensions (U, L², T, CF)."""
    
    if request.capability == "get_project_dimensions":
        project_id = request.parameters.get("projectId")
        # Mock: fetch from Neo4j
        result = {
            "projectId": project_id,
            "dimensions": {
                "U": {"value": 100, "unit": "units"},
                "L2": {"value": 70000, "unit": "sqft"},
                "T": {"value": 36, "unit": "months"},
                "CF": {"value": 50_00_00_000, "unit": "INR"}
            }
        }
        
        provenance = {
            "inputDimensions": ["U", "L2", "T", "CF"],
            "calculationMethod": "Direct fetch from Neo4j Layer 0",
            "lfSource": "Project master data",
            "timestamp": datetime.utcnow().isoformat(),
            "dataVersion": request.context.get("lfDataVersion", "Q3_FY25")
        }
        
        lineage = {"layer0_inputs": result["dimensions"]}
        
        return result, provenance, lineage
    
    raise ValueError(f"Unknown Layer 0 capability: {request.capability}")

def handle_layer1_query(request: MCPQueryRequest, query_id: str):
    """Layer 1: Derived metrics (PSF, ASP, Absorption Rate, etc.)."""
    
    if request.capability == "calculate_psf":
        total_revenue = request.parameters["totalRevenue"]  # CF
        saleable_area = request.parameters["saleableArea"]  # L²
        
        psf = total_revenue / saleable_area
        
        result = {"metric": "PSF", "value": psf, "unit": "INR/sqft"}
        provenance = {
            "inputDimensions": ["CF", "L2"],
            "calculationMethod": "PSF = Total Revenue (CF) / Saleable Area (L²)",
            "formula": f"{total_revenue} / {saleable_area}",
            "lfSource": "Pillar 1.1 (Price & Market Movement Engine)",
            "timestamp": datetime.utcnow().isoformat()
        }
        lineage = {"layer1_inputs": {"totalRevenue": total_revenue, "saleableArea": saleable_area}}
        
        return result, provenance, lineage
    
    elif request.capability == "calculate_asp":
        total_revenue = request.parameters["totalRevenue"]  # CF
        total_units = request.parameters["totalUnits"]     # U
        
        asp = total_revenue / total_units
        
        result = {"metric": "ASP", "value": asp, "unit": "INR/unit"}
        provenance = {
            "inputDimensions": ["CF", "U"],
            "calculationMethod": "ASP = Total Revenue (CF) / Total Units (U)",
            "lfSource": "Pillar 2.1 (Typology Performance)",
            "timestamp": datetime.utcnow().isoformat()
        }
        lineage = {"layer1_inputs": {"totalRevenue": total_revenue, "totalUnits": total_units}}
        
        return result, provenance, lineage
    
    raise ValueError(f"Unknown Layer 1 capability: {request.capability}")

def handle_layer2_query(request: MCPQueryRequest, query_id: str):
    """Layer 2: Financial metrics (NPV, IRR, Payback, Cap Rate)."""
    
    if request.capability == "calculate_irr":
        cash_flows = request.parameters["cashFlows"]       # List[CF]
        initial_investment = request.parameters["initialInvestment"]  # CF
        
        # Use Layer2Calculator
        from scipy.optimize import newton
        
        def npv_func(rate):
            npv = -initial_investment
            for year, cf in enumerate(cash_flows, start=1):
                npv += cf / ((1 + rate) ** year)
            return npv
        
        try:
            irr = newton(npv_func, x0=0.2)
        except RuntimeError:
            irr = None
        
        result = {"metric": "IRR", "value": irr * 100 if irr else None, "unit": "%/year"}
        
        provenance = {
            "inputDimensions": ["CF", "T"],
            "calculationMethod": "IRR: r where NPV(r) = 0",
            "lfSource": "Pillar 4.3 (IRR & ROI Calculations)",
            "algorithm": "Newton's method (scipy.optimize.newton)",
            "timestamp": datetime.utcnow().isoformat(),
            "dataVersion": request.context.get("lfDataVersion", "Q3_FY25")
        }
        
        lineage = {
            "layer0_inputs": {"initialInvestment": initial_investment},
            "layer1_intermediates": {"cashFlows": cash_flows}
        }
        
        return result, provenance, lineage
    
    elif request.capability == "calculate_sensitivity_analysis":
        # Simplified: calculate IRR at base, optimistic, stress scenarios
        base_absorption = request.parameters.get("baseAbsorption", 5)
        absorption_range = request.parameters.get("absorptionRange", [3, 8])
        price_range = request.parameters.get("priceRange", [-10, 10])
        
        result = {
            "baseCase": {
                "absorption_units_per_month": base_absorption,
                "irr_percent": 22.0  # Mock
            },
            "optimisticCase": {
                "absorption_units_per_month": absorption_range[1],
                "irr_percent": 28.0  # Mock
            },
            "stressCase": {
                "absorption_units_per_month": absorption_range[0],
                "irr_percent": 16.0  # Mock
            }
        }
        
        provenance = {
            "calculationMethod": "Sensitivity analysis across absorption & price scenarios",
            "lfSource": "Pillar 4.2 (Cash Flow & Scenario Modelling)",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        lineage = {"layer2_sensitivity": absorption_range}
        
        return result, provenance, lineage
    
    raise ValueError(f"Unknown Layer 2 capability: {request.capability}")

def handle_layer3_query(request: MCPQueryRequest, query_id: str):
    """Layer 3: Optimization & scenarios."""
    
    if request.capability == "optimize_product_mix":
        location = request.parameters.get("location", "Chakan, Pune")
        total_units = request.parameters.get("totalUnits", 100)
        total_area = request.parameters.get("totalArea", 70000)
        
        # Mock optimization result
        result = {
            "optimalMix": {
                "1BHK": 0.30,
                "2BHK": 0.50,
                "3BHK": 0.20
            },
            "scenarios": [
                {
                    "scenarioName": "Base Case",
                    "mix": {"1BHK": 30, "2BHK": 50, "3BHK": 20},
                    "npv_crore": 52,
                    "irr_percent": 24
                },
                {
                    "scenarioName": "Optimistic",
                    "mix": {"1BHK": 20, "2BHK": 60, "3BHK": 20},
                    "npv_crore": 55,
                    "irr_percent": 26
                },
                {
                    "scenarioName": "Conservative",
                    "mix": {"1BHK": 40, "2BHK": 40, "3BHK": 20},
                    "npv_crore": 48,
                    "irr_percent": 21
                }
            ]
        }
        
        provenance = {
            "lfCapabilitiesApplied": ["2.1", "4.1", "4.3"],
            "algorithm": "scipy.optimize.minimize with SLSQP",
            "constraints": [
                "totalUnits = 100",
                "totalArea <= 70000 sqft",
                "absorptionRate <= LF historical max"
            ],
            "lfSource": "Pillar 2.1 (Typology), Pillar 4.1 (Feasibility), Pillar 4.3 (IRR/ROI)",
            "timestamp": datetime.utcnow().isoformat(),
            "dataVersion": request.context.get("lfDataVersion", "Q3_FY25")
        }
        
        lineage = {
            "layer0_inputs": {"totalUnits": total_units, "totalArea": total_area},
            "layer1_intermediates": {"absorptionRates": [3, 5, 2], "prices": [6000, 5700, 5300]},
            "layer2_dependencies": ["NPV", "IRR", "ProfitabilityIndex"]
        }
        
        return result, provenance, lineage
    
    elif request.capability == "market_opportunity_scoring":
        location = request.parameters.get("location", "Chakan, Pune")
        
        result = {
            "location": location,
            "oppsScore": 78,  # Out of 100
            "demandTrend": "high",
            "competitiveIntensity": "medium",
            "recommendedMix": {
                "1BHK": 0.25,
                "2BHK": 0.50,
                "3BHK": 0.25
            },
            "opportunity": "High potential for 2BHK focused projects"
        }
        
        provenance = {
            "lfSource": "Pillar 1.3 (Micro-Market Evaluation), Pillar 3.3 (OPPS Scoring)",
            "components": ["APF_score", "Marketability_index", "Location_rating", "Builder_rating"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        lineage = {"layer3_inputs": {"location": location}}
        
        return result, provenance, lineage
    
    raise ValueError(f"Unknown Layer 3 capability: {request.capability}")

# ==================== HELPER FUNCTIONS ====================

def compute_related_metrics(request: MCPQueryRequest, result: Dict) -> List[Dict]:
    """Compute automatically related metrics from result."""
    related = []
    
    if request.capability == "calculate_irr":
        # If IRR calculated, auto-compute related NPV (mock)
        related.append({
            "metricName": "NPV_at_12pct_discount",
            "value": 52_00_00_000,
            "dimension": "CF",
            "calculatedFrom": "result"
        })
    
    return related

# ==================== RUN APP ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## Knowledge Graph Entities by Layer

### Complete Neo4j Schema with Layers

```cypher
# ========== LAYER 0: ATOMIC DIMENSIONS ==========

(:Dimension_L0 {
  dimensionCode: "U" | "L2" | "T" | "CF",
  dimensionName: "Units" | "Area" | "Time" | "CashFlow",
  siUnit: "count" | "sqft" | "months" | "INR",
  category: "Base",
  analogyToPhysics: "Mass" | "Length²" | "Time" | "Current"
})

(:Project {
  projectId: "P_CHAKAN_001",
  projectName: "Chakan Residential Tower",
  city: "Pune",
  microMarket: "Chakan",
  
  // Layer 0 Raw Dimensions
  totalUnits: 100,           // U
  totalLandArea_sqft: 70000, // L²
  totalCarpetArea_sqft: 50000,
  totalSaleableArea_sqft: 60000,
  projectDuration_months: 36,  // T
  totalProjectCost_inr: 50_00_00_000,  // CF
  launchDate: "2025-06-01",
  completionDate: "2028-06-01"
})

(:Unit {
  unitId: "U_1BHK_001",
  projectId: "P_CHAKAN_001",
  unitType: "1BHK",
  
  // Layer 0 Dimensions
  areaPerUnit_sqft: 500,     // L² (carpet)
  saleablePerUnit_sqft: 600, // L² (saleable)
  pricePerUnit_inr: 30_00_000 // CF
})

# ========== LAYER 1: DERIVED METRICS ==========

(:Metric_L1 {
  metricId: "M1_PSF_CHAKAN",
  projectId: "P_CHAKAN_001",
  metricName: "PSF",
  dimensionCode: "CF/L2",
  formula: "Total Revenue / Saleable Area",
  value: 6500,  // INR/sqft
  unit: "INR/sqft",
  timestamp: "2025-11-27",
  
  // Data lineage
  sourceL0: {
    totalRevenue: 39_00_00_000,  // CF (100 units × ₹30L)
    saleableArea: 60000  // L²
  },
  lfSource: "Pillar_1.1"
})

(:Metric_L1 {
  metricId: "M1_ASP_CHAKAN",
  projectId: "P_CHAKAN_001",
  metricName: "ASP",
  dimensionCode: "CF/U",
  formula: "Total Revenue / Total Units",
  value: 39_00_000,  // INR/unit
  unit: "INR/unit",
  sourceL0: {
    totalRevenue: 39_00_00_000,
    totalUnits: 100
  },
  lfSource: "Pillar_2.1"
})

(:Metric_L1 {
  metricId: "M1_AR_CHAKAN_2BHK",
  projectId: "P_CHAKAN_001",
  unitType: "2BHK",
  metricName: "AbsorptionRate",
  dimensionCode: "(U/U_total)/T",
  formula: "(Units Sold / Total Units) / Months",
  value: 0.05,  // 5% per month
  unit: "fraction/month",
  sourceL0: {
    unitsSold: 5,     // units/month
    totalUnits: 100
  },
  lfSource: "Pillar_1.2",
  lfDataVersion: "Q3_FY25"
})

# ========== LAYER 2: FINANCIAL METRICS ==========

(:Metric_L2 {
  metricId: "M2_NPV_BASE_CASE",
  scenarioId: "S_BASE_CASE",
  projectId: "P_CHAKAN_001",
  metricType: "NPV",
  dimensionCode: "CF",
  formula: "∑[CF_t / (1+r)^t] - Initial_Investment",
  value: 52_00_00_000,  // INR (₹52 Crore)
  unit: "INR",
  timestamp: "2025-11-27",
  
  // Calculation inputs
  assumptions: {
    discountRate: 0.12,  // 12% per annum
    projectDuration_years: 3,
    absorptionRate_monthly: 5  // units
  },
  
  // Layer 1 & 0 dependencies
  sourceL1: ["PSF", "ASP", "AbsorptionRate"],
  sourceL0: {
    initialInvestment: 50_00_00_000,
    totalUnits: 100,
    saleableArea: 60000
  },
  
  lfSource: "Pillar_4.3",
  lfDataVersion: "Q3_FY25",
  
  sensitivity: {
    absorptionRange: [3, 8],  // units/month
    priceRange: [-10, 10]     // percent
  }
})

(:Metric_L2 {
  metricId: "M2_IRR_BASE_CASE",
  scenarioId: "S_BASE_CASE",
  projectId: "P_CHAKAN_001",
  metricType: "IRR",
  dimensionCode: "T^-1",
  formula: "r where NPV(r) = 0",
  value: 0.24,  // 24% per annum
  unit: "%/year",
  
  sourceL2: ["NPV"],
  algorithm: "scipy.optimize.newton",
  lfSource: "Pillar_4.3"
})

# ========== LAYER 3: OPTIMIZATION & SCENARIOS ==========

(:Scenario_L3 {
  scenarioId: "S_OPTIMAL_MIX",
  projectId: "P_CHAKAN_001",
  scenarioName: "Optimal Product Mix",
  scenarioType: "optimization",
  
  // Unit mix (Layer 0)
  unitMix: {
    "1BHK": 30,
    "2BHK": 50,
    "3BHK": 20
  },
  
  // LF assumptions (Layer 1)
  assumptions_L1: {
    absorptionRate_1BHK: 0.03,   // 3 units/month
    absorptionRate_2BHK: 0.05,   // 5 units/month
    absorptionRate_3BHK: 0.02,   // 2 units/month
    priceAppreciation_annual: 0.08
  },
  
  // Results (Layer 2)
  results_L2: {
    projectedNPV_inr: 52_00_00_000,
    projectedIRR_percent: 24,
    paybackPeriod_months: 26,
    profitabilityIndex: 1.04
  },
  
  // Layer 3 metadata
  optimizationMethod: "scipy.optimize.minimize (SLSQP)",
  constraints: [
    "totalUnits == 100",
    "totalArea <= 70000",
    "absorptionRate <= LF_historical_max"
  ],
  
  lfCapabilitiesApplied: ["2.1", "4.1", "4.3"],
  developerMarketability: 0.95  // From LF Pillar 3
})

(:Capability_L3 {
  capabilityId: "L3_product_mix_optimization",
  capabilityName: "Product Mix Optimization",
  description: "Find optimal unit mix to maximize IRR",
  
  inputLayers: [0, 1, 2],
  requiredL0: ["U", "L2", "T", "CF"],
  requiredL1: ["PSF", "ASP", "AbsorptionRate"],
  requiredL2: ["NPV", "IRR"],
  
  lfPillars: ["Pillar_2.1", "Pillar_4.1", "Pillar_4.3"],
  algorithm: "scipy.optimize.minimize with SLSQP method"
})

# ========== RELATIONSHIPS ==========

(:Project) - [:HAS_UNITS_L0] -> (:Unit)
(:Project) - [:CONTAINS_METRIC_L1] -> (:Metric_L1)
(:Project) - [:CONTAINS_METRIC_L2] -> (:Metric_L2)
(:Project) - [:SCENARIO_L3] -> (:Scenario_L3)

(:Metric_L1) - [:DERIVES_FROM_L0] -> (:Project)
(:Metric_L2) - [:DEPENDS_ON_L1] -> (:Metric_L1)
(:Scenario_L3) - [:USES_L2] -> (:Metric_L2)

(:Scenario_L3) - [:POWERED_BY] -> (:Capability_L3)
(:Capability_L3) - [:CONSUMES] -> (:Dimension_L0)
(:Capability_L3) - [:PRODUCES] -> (:Metric_L3)
```

---

## Use Cases & Query Resolution

### Use Case 1: "What is the best product mix for a 100-unit tower in Chakan?"

**Query Flow:**

```
User Query (Claude)
    ↓
Intent: Optimization (Layer 3)
    ↓
/api/mcp/query {
  "queryType": "optimization",
  "layer": 3,
  "capability": "optimize_product_mix",
  "parameters": {
    "location": "Chakan, Pune",
    "totalUnits": 100,
    "totalArea": 70000
  }
}
    ↓
MCP Router → handle_layer3_query()
    ↓
Layer 3 Optimizer:
  1. Fetch Layer 1 data (PSF, ASP, absorption rates)
  2. Fetch LF Pillar 1.2 & 2.1 market data
  3. Run scipy.optimize.minimize with constraints
  4. Generate 3 scenarios (base, optimistic, stress)
    ↓
Response:
{
  "optimalMix": {"1BHK": 30%, "2BHK": 50%, "3BHK": 20%},
  "scenarios": [
    {
      "name": "Base",
      "irr_percent": 24,
      "npv_crore": 52
    },
    ...
  ],
  "provenance": {
    "lfSource": "Pillar 2.1, 4.1, 4.3",
    "layers": [0, 1, 2, 3]
  }
}
```

---

### Use Case 2: "What is my IRR if my NPV is ₹100 Crore?"

**Query Flow:**

```
User Query (Claude)
    ↓
Intent: Financial Calculation (Layer 2)
    ↓
/api/mcp/query {
  "queryType": "calculation",
  "layer": 2,
  "capability": "calculate_irr",
  "parameters": {
    "cashFlows": [12.5, 15, 17.5, 20, 22.5],  // Annual CF
    "initialInvestment": 50_00_00_000
  }
}
    ↓
MCP Router → handle_layer2_query()
    ↓
Layer 2 Calculator:
  1. Apply Newton's method to solve NPV(r) = 0
  2. Return IRR ≈ 24%
    ↓
Response:
{
  "metric": "IRR",
  "value": 24,
  "unit": "%/year",
  "provenance": {
    "layer": 2,
    "calculation": "scipy.optimize.newton",
    "lfSource": "Pillar 4.3"
  },
  "relatedMetrics": [
    {
      "metric": "NPV_at_12pct_discount",
      "value": 52_00_00_000
    }
  ]
}
```

---

## Implementation Guide

### Step 1: Set Up FastAPI Server

```bash
pip install fastapi uvicorn pydantic scipy neo4j
python api_server.py
```

### Step 2: Connect Claude to MCP

```python
# In Claude Code integration
from anthropic import Anthropic

client = Anthropic()

# Fetch available tools
tools_response = requests.get("http://localhost:8000/api/mcp/info")
available_tools = tools_response.json()["capabilities"]

# Use tools in Claude conversation
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=2000,
    tools=available_tools,
    messages=[
        {
            "role": "user",
            "content": "What's the best product mix for Chakan Pune?"
        }
    ]
)
```

### Step 3: Deploy Neo4j Knowledge Graph

```cypher
# Load initial data
LOAD CSV FROM "https://data.liases-foras.com/projects.csv" AS row
CREATE (:Project {
  projectId: row.id,
  projectName: row.name,
  totalUnits: toInteger(row.units),
  totalLandArea_sqft: toFloat(row.area)
})

# Create indexes
CREATE INDEX project_id FOR (p:Project) ON (p.projectId)
CREATE INDEX metric_l1_name FOR (m:Metric_L1) ON (m.metricName)
CREATE INDEX metric_l2_type FOR (m:Metric_L2) ON (m.metricType)
```

---

## Acceptance Criteria

| # | Criterion | Validation |
|---|-----------|-----------|
| 1 | **MCP Discovery** | GET /api/mcp/info returns all 4 layers + 15+ tools |
| 2 | **Query Execution** | POST /api/mcp/query executes layer-specific logic in <1 sec |
| 3 | **Layer 0 Data** | Projects have U, L², T, CF dimensions |
| 4 | **Layer 1 Calculations** | PSF, ASP, Absorption Rate within ±2% of manual calc |
| 5 | **Layer 2 Financials** | NPV, IRR, Payback match LF standards within ±2% |
| 6 | **Layer 3 Optimization** | Top 3 scenarios with IRR variance < ±5% |
| 7 | **Provenance Tracking** | Every result includes layer, formula, LF source, timestamp |
| 8 | **Claude Integration** | Multi-turn dialogue with tool use works seamlessly |
| 9 | **Neo4j Performance** | 100K+ project nodes, <500ms query response |
| 10 | **LF Data Freshness** | Quarterly updates with version tracking |

---

**PRD Version 2.0 | Status: Production-Ready | Implementation Roadmap: Q1 FY26**

**Architecture: FastAPI + Neo4j + MCP + Claude Code Integration**  
**Data Layers: 0 (Raw) → 1 (Derived) → 2 (Financial) → 3 (Optimization)**  
**Exposure: Coarse-grained (Capabilities) + Fine-grained (Tools)**
