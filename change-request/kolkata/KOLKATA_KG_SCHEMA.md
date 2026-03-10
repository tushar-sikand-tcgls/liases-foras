# Kolkata Knowledge Graph Schema
## Mega Knowledge Graph Design with L0/L1/L2 Layers

**Date Created:** 2025-01-28
**Purpose:** Define comprehensive knowledge graph structure for Kolkata real estate market
**Dimensional System:** C (Connectivity/Cash Flow), L² (Location/Area), T (Time), U (Units)

---

## 1. Graph Architecture Overview

### Node Types Hierarchy

```
MicromarketNode (Top Level)
    ├── Metadata (location, distance range, quarter)
    ├── Layer 0: Raw Dimensions (U, L², T, C)
    ├── Layer 1: Derived Metrics (calculated from L0)
    └── Layer 2: Financial & Predictive Metrics (calculated from L1)
    └── Contains: List[ProjectNode]

ProjectNode (Mid Level)
    ├── Metadata (project_id, name, developer, location)
    ├── Layer 0: Raw Dimensions (U, L², T, C)
    ├── Layer 1: Derived Metrics
    └── Layer 2: Financial Metrics
    └── Contains: List[UnitTypeNode]

QuarterNode (Time Series)
    ├── Metadata (quarter_id, quarter, year, fiscal_year)
    ├── Layer 0: Raw Dimensions (sales, supply, pricing)
    ├── Layer 1: Derived Metrics (YoY growth, QoQ growth, absorption)
    └── Relationships: [MicromarketNode, ProjectNode]

UnitTypeNode (Product Analysis)
    ├── Metadata (unit_type, category, bhk_type)
    ├── Layer 0: Raw Dimensions
    ├── Layer 1: Derived Metrics
    └── Relationships: [ProjectNode, MicromarketNode]
```

---

## 2. MicromarketNode Schema

### Metadata
```python
{
    "micromarket_id": str,          # e.g., "KOLKATA_0_2KM"
    "micromarket_name": str,        # e.g., "0-2 KM from CBD"
    "distance_range": {
        "min_km": float,
        "max_km": float,
        "center_point": str         # e.g., "Kolkata CBD"
    },
    "city": "Kolkata",
    "state": "West Bengal",
    "quarter": str,                 # e.g., "Q2 FY25-26"
    "data_version": str,            # e.g., "Q3_FY25"
    "last_updated": str             # ISO-8601 timestamp
}
```

### Layer 0: Raw Dimensions

**Dimension: U (Units)**
```python
{
    "total_projects": {
        "value": int,
        "unit": "count",
        "dimension": "U",
        "description": "Total number of projects in micromarket"
    },
    "total_supply_units": {
        "value": int,
        "unit": "Units",
        "dimension": "U",
        "description": "Total launched units across all projects"
    },
    "unsold_units": {
        "value": int,
        "unit": "Units",
        "dimension": "U",
        "description": "Total unsold inventory"
    },
    "annual_sales_units": {
        "value": int,
        "unit": "Units/year",
        "dimension": "U/T",
        "description": "Total units sold in last 12 months"
    },
    "quarterly_sales_units": {
        "value": int,
        "unit": "Units/quarter",
        "dimension": "U/T",
        "description": "Units sold in last quarter"
    }
}
```

**Dimension: L² (Area)**
```python
{
    "total_unsold_sqft": {
        "value": float,
        "unit": "sq ft",
        "dimension": "L²",
        "description": "Total unsold area across micromarket"
    },
    "annual_sales_sqft": {
        "value": float,
        "unit": "sq ft/year",
        "dimension": "L²/T",
        "description": "Total area sold in last 12 months"
    },
    "avg_unit_size_sqft": {
        "value": float,
        "unit": "sq ft",
        "dimension": "L²",
        "description": "Average saleable unit size"
    }
}
```

**Dimension: C (Cash Flow)**
```python
{
    "saleable_psf": {
        "value": int,
        "unit": "INR/sq ft",
        "dimension": "C/L²",
        "description": "Average price per square foot (saleable area)"
    },
    "carpet_psf": {
        "value": int,
        "unit": "INR/sq ft",
        "dimension": "C/L²",
        "description": "Average price per square foot (carpet area)"
    },
    "new_launch_saleable_psf": {
        "value": int,
        "unit": "INR/sq ft",
        "dimension": "C/L²",
        "description": "PSF for newly launched projects"
    },
    "annual_sales_value": {
        "value": float,
        "unit": "INR Cr/year",
        "dimension": "C/T",
        "description": "Total sales value in last 12 months"
    }
}
```

**Dimension: T (Time)**
```python
{
    "months_inventory": {
        "value": float,
        "unit": "months",
        "dimension": "T",
        "description": "Months to clear current inventory at current velocity"
    },
    "avg_project_age": {
        "value": float,
        "unit": "months",
        "dimension": "T",
        "description": "Average time since project launch"
    }
}
```

### Layer 1: Derived Metrics

```python
{
    "absorption_rate": {
        "value": float,
        "unit": "%",
        "formula": "(Annual Sales Units / Total Supply Units) * 100",
        "dimension": "Dimensionless",
        "description": "Market absorption rate"
    },
    "sales_velocity": {
        "value": float,
        "unit": "%/month",
        "formula": "Absorption Rate / 12",
        "dimension": "T⁻¹",
        "description": "Monthly sales velocity"
    },
    "unsold_ratio": {
        "value": float,
        "unit": "%",
        "formula": "(Unsold Units / Total Supply Units) * 100",
        "dimension": "Dimensionless",
        "description": "Percentage of unsold inventory"
    },
    "price_trend": {
        "value": str,
        "unit": "categorical",
        "formula": "Compare current PSF vs previous quarter",
        "dimension": "None",
        "description": "stable|rising|declining"
    },
    "mom_change_percent": {
        "value": float,
        "unit": "%",
        "formula": "((Current Month PSF - Previous Month PSF) / Previous Month PSF) * 100",
        "dimension": "Dimensionless",
        "description": "Month-over-month price change"
    },
    "inventory_turnover": {
        "value": float,
        "unit": "ratio",
        "formula": "Annual Sales Units / Total Stock Units",
        "dimension": "Dimensionless",
        "description": "How many times inventory is sold per year"
    }
}
```

### Layer 2: Financial & Predictive Metrics

```python
{
    "demand_score": {
        "value": int,
        "unit": "score (0-100)",
        "formula": "Weighted calculation: 0.4*Absorption + 0.3*Velocity + 0.3*Price_Momentum",
        "dimension": "Dimensionless",
        "description": "Market demand intensity score"
    },
    "supply_pressure": {
        "value": str,
        "unit": "categorical",
        "formula": "Based on months_inventory: <12=low, 12-24=medium, >24=high",
        "dimension": "None",
        "description": "low|medium|high"
    },
    "competitive_intensity": {
        "value": str,
        "unit": "categorical",
        "formula": "Based on active projects and supply concentration",
        "dimension": "None",
        "description": "low|medium|high"
    },
    "opportunity_score": {
        "value": int,
        "unit": "score (0-100)",
        "formula": "Weighted: 0.5*Demand + 0.3*(100-Supply_Pressure) + 0.2*Price_Momentum",
        "dimension": "Dimensionless",
        "description": "Investment opportunity score"
    },
    "clearance_timeline": {
        "value": float,
        "unit": "months",
        "formula": "Months_Inventory (at current velocity)",
        "dimension": "T",
        "description": "Expected time to clear current inventory"
    }
}
```

---

## 3. ProjectNode Schema

### Metadata
```python
{
    "project_id": int,
    "project_name": str,
    "developer_name": str,
    "location": str,                # Micromarket name
    "micromarket_id": str,          # Foreign key to MicromarketNode
    "layer": str,                   # "L0"|"L1"|"L2"
    "node_type": str,               # "Project_L1"
    "extraction_timestamp": str,
    "rera_registered": bool
}
```

### Layer 0: Raw Dimensions

**From Enrichment Excel (36 attributes identified)**

**Dimension: U (Units)**
```python
{
    "project_size": {"value": int, "unit": "Units", "dimension": "U"},
    "total_supply": {"value": int, "unit": "Units", "dimension": "U"},
    "sold_units": {"value": int, "unit": "Units", "dimension": "U"},
    "unsold_units": {"value": int, "unit": "Units", "dimension": "U"},
    "annual_sales_units": {"value": int, "unit": "Units/year", "dimension": "U/T"}
}
```

**Dimension: L² (Area)**
```python
{
    "unit_saleable_size": {"value": float, "unit": "sq ft", "dimension": "L²"},
    "total_saleable_area": {"value": float, "unit": "sq ft", "dimension": "L²"},
    "unsold_area": {"value": float, "unit": "sq ft", "dimension": "L²"}
}
```

**Dimension: C (Cash Flow)**
```python
{
    "launch_price_psf": {"value": int, "unit": "INR/sq ft", "dimension": "C/L²"},
    "current_price_psf": {"value": int, "unit": "INR/sq ft", "dimension": "C/L²"},
    "annual_sales_value": {"value": float, "unit": "INR Cr/year", "dimension": "C/T"}
}
```

**Dimension: T (Time)**
```python
{
    "launch_date": {"value": str, "unit": "Month-Year", "dimension": "T"},
    "possession_date": {"value": str, "unit": "Month-Year", "dimension": "T"},
    "project_age_months": {"value": int, "unit": "months", "dimension": "T"}
}
```

### Layer 1: Derived Metrics

**From Enrichment Excel**
```python
{
    "sold_percent": {
        "value": float,
        "unit": "%",
        "formula": "(Sold Units / Total Supply) * 100",
        "dimension": "Dimensionless"
    },
    "unsold_percent": {
        "value": float,
        "unit": "%",
        "formula": "100 - Sold Percent",
        "dimension": "Dimensionless"
    },
    "monthly_sales_velocity": {
        "value": float,
        "unit": "%/month",
        "formula": "(Annual Sales Units / Total Supply) / 12 * 100",
        "dimension": "T⁻¹"
    },
    "monthly_units_sold": {
        "value": float,
        "unit": "Units/month",
        "formula": "Annual Sales Units / 12",
        "dimension": "U/T"
    },
    "price_appreciation": {
        "value": float,
        "unit": "%",
        "formula": "((Current PSF - Launch PSF) / Launch PSF) * 100",
        "dimension": "Dimensionless"
    },
    "absorption_rate": {
        "value": float,
        "unit": "%",
        "formula": "(Sold Units / Total Supply) * 100",
        "dimension": "Dimensionless"
    }
}
```

### Layer 2: Financial Metrics

```python
{
    "months_of_inventory": {
        "value": float,
        "unit": "months",
        "formula": "(Unsold Units / Monthly Units Sold)",
        "dimension": "T",
        "description": "Time to clear inventory at current velocity"
    },
    "revenue_per_month": {
        "value": float,
        "unit": "INR Cr/month",
        "formula": "Annual Sales Value / 12",
        "dimension": "C/T"
    },
    "sellout_efficiency": {
        "value": float,
        "unit": "score",
        "formula": "(Sold % / Project Age in Months) * 100",
        "dimension": "T⁻¹",
        "description": "How efficiently project is selling"
    },
    "price_momentum": {
        "value": str,
        "unit": "categorical",
        "formula": "Based on price appreciation: >10%=strong, 5-10%=moderate, <5%=weak",
        "dimension": "None"
    }
}
```

---

## 4. QuarterNode Schema

### Metadata
```python
{
    "quarter_id": str,              # e.g., "Q2_FY25_26"
    "quarter": str,                 # e.g., "Q2 25-26"
    "quarter_num": int,             # 1, 2, 3, 4
    "fiscal_year": str,             # "FY25-26"
    "year": int,                    # 2025
    "micromarket_id": str,          # Foreign key
    "node_type": "Quarter_TimeSeries"
}
```

### Layer 0: Raw Dimensions

```python
{
    "sales_units": {"value": int, "unit": "Units", "dimension": "U"},
    "supply_units": {"value": int, "unit": "Units", "dimension": "U"},
    "sales_area_mn_sqft": {"value": float, "unit": "mn sq ft", "dimension": "L²"},
    "supply_area_mn_sqft": {"value": float, "unit": "mn sq ft", "dimension": "L²"},
    "avg_psf": {"value": int, "unit": "INR/sq ft", "dimension": "C/L²"}
}
```

### Layer 1: Derived Metrics

```python
{
    "absorption_rate": {
        "value": float,
        "unit": "%",
        "formula": "(Sales Units / Supply Units) * 100"
    },
    "yoy_growth_sales": {
        "value": float,
        "unit": "%",
        "formula": "((Current Q - Same Q Last Year) / Same Q Last Year) * 100"
    },
    "qoq_growth_sales": {
        "value": float,
        "unit": "%",
        "formula": "((Current Q - Previous Q) / Previous Q) * 100"
    },
    "avg_unit_size_sqft": {
        "value": float,
        "unit": "sq ft",
        "formula": "(Sales Area * 1M) / Sales Units"
    }
}
```

---

## 5. UnitTypeNode Schema

### Metadata
```python
{
    "unit_type_id": str,            # e.g., "1BHK_KOLKATA"
    "unit_type": str,               # "1BHK", "2BHK", "3BHK", "4BHK+", etc.
    "category": str,                # "Residential", "Commercial"
    "bhk_type": int,                # 1, 2, 3, 4, 5
    "micromarket_id": str
}
```

### Layer 0: Raw Dimensions

**From PDF: 10 unit type categories identified**
- 1BHK
- 2BHK
- 3BHK
- 4BHK
- 5BHK+
- 1RK
- Studio
- Duplex
- Penthouse
- Commercial

```python
{
    "sales_units": {"value": int, "unit": "Units", "dimension": "U"},
    "supply_units": {"value": int, "unit": "Units", "dimension": "U"},
    "avg_size_sqft": {"value": float, "unit": "sq ft", "dimension": "L²"},
    "avg_psf": {"value": int, "unit": "INR/sq ft", "dimension": "C/L²"},
    "avg_ticket_size": {"value": float, "unit": "INR Lakhs", "dimension": "C"}
}
```

### Layer 1: Derived Metrics

```python
{
    "absorption_rate": {
        "value": float,
        "unit": "%",
        "formula": "(Sales Units / Supply Units) * 100"
    },
    "market_share": {
        "value": float,
        "unit": "%",
        "formula": "(Unit Type Supply / Total Market Supply) * 100"
    },
    "price_premium": {
        "value": float,
        "unit": "%",
        "formula": "((Unit PSF - Market Avg PSF) / Market Avg PSF) * 100"
    }
}
```

---

## 6. Relationships Schema

### MicromarketNode Relationships
```python
{
    "contains_projects": List[ProjectNode],
    "has_quarters": List[QuarterNode],
    "has_unit_types": List[UnitTypeNode],
    "neighboring_micromarkets": List[MicromarketNode]  # Adjacent distance ranges
}
```

### ProjectNode Relationships
```python
{
    "belongs_to_micromarket": MicromarketNode,
    "has_unit_types": List[UnitTypeNode],
    "developer": DeveloperNode,              # Future extension
    "quarter_performance": List[QuarterNode]  # Time series
}
```

### QuarterNode Relationships
```python
{
    "belongs_to_micromarket": MicromarketNode,
    "previous_quarter": QuarterNode,
    "next_quarter": QuarterNode,
    "same_quarter_last_year": QuarterNode
}
```

---

## 7. Data Source Mapping

### Kolkata PDF Structure (59 pages)
- **Pages 1-3:** Unit types (10 categories) + Construction stages (8 stages)
- **Pages 4-10:** Quarterly pricing data (44 quarters: Q2 14-15 to Q2 25-26)
- **Page 12:** Distance-based micromarkets (0-2 KM, 2-4 KM, ..., >60 KM)
- **Pages 11-15:** 880+ projects with IDs, names, locations, developers
- **Pages 16-25:** Unit type breakdowns, price ranges
- **Pages 36-37:** Sales velocity, months inventory

### Enrichment Excel (36 attributes)
- **Sheet: All_Attributes**
  - L0 attributes: 20 (Project ID, Name, Developer, Location, Launch Date, etc.)
  - L1 attributes: 12 (Sold %, Annual Sales, Monthly Velocity, etc.)
  - L2 attributes: 4 (MOI, Sellout Efficiency, Price Momentum, etc.)

---

## 8. Implementation Files

### Service Layer
```
app/services/kolkata_kg_service.py
    ├── MicromarketNode class
    ├── ProjectNode class
    ├── QuarterNode class
    ├── UnitTypeNode class
    └── KolkataKGService class

app/services/kolkata_data_loader.py
    ├── PDF parser (PyPDF2/pdfplumber)
    ├── Excel enrichment loader
    └── JSON exporter
```

### Data Files
```
data/extracted/kolkata/
    ├── kolkata_micromarkets.json
    ├── kolkata_projects.json
    ├── kolkata_quarters.json
    ├── kolkata_unit_types.json
    └── kolkata_kg_full.json (mega graph)
```

### Frontend Component
```
frontend/components/kolkata_viewer.py
    ├── Micromarket selector
    ├── Project list view
    ├── Time series charts (quarterly trends)
    └── Unit type analysis
```

---

## 9. Query Functions (Required)

### Micromarket Queries
```python
def get_micromarket_by_distance_range(min_km: float, max_km: float) -> MicromarketNode
def get_all_micromarkets() -> List[MicromarketNode]
def get_micromarket_summary(micromarket_id: str) -> Dict
def compare_micromarkets(micromarket_ids: List[str]) -> Dict
```

### Project Queries
```python
def get_project_by_id(project_id: int) -> ProjectNode
def get_project_by_name(name: str) -> ProjectNode
def get_projects_by_micromarket(micromarket_id: str) -> List[ProjectNode]
def get_projects_by_developer(developer_name: str) -> List[ProjectNode]
def get_top_performing_projects(metric: str, n: int) -> List[ProjectNode]
```

### Quarterly Queries
```python
def get_quarter_by_id(quarter_id: str) -> QuarterNode
def get_quarters_by_year(year: int) -> List[QuarterNode]
def get_recent_quarters(n: int) -> List[QuarterNode]
def get_yoy_comparison(quarter_id: str) -> Dict
```

### Unit Type Queries
```python
def get_unit_type_performance(unit_type: str) -> Dict
def get_all_unit_types() -> List[UnitTypeNode]
def compare_unit_types(micromarket_id: str) -> Dict
```

---

## 10. Calculation Engine

All Layer 1 and Layer 2 metrics will be pre-calculated during data ingestion and stored in the knowledge graph. No runtime calculation required for basic queries.

**Calculation Priority:**
1. Load L0 data from PDF + Excel
2. Calculate L1 metrics using formulas defined above
3. Calculate L2 metrics using L1 dependencies
4. Build relationships between nodes
5. Export to JSON for fast querying

---

## 11. Next Steps

1. ✅ Schema design complete
2. ⏳ Implement `kolkata_kg_service.py` with node classes
3. ⏳ Implement `kolkata_data_loader.py` for PDF + Excel parsing
4. ⏳ Build query functions
5. ⏳ Create frontend viewer component
6. ⏳ Add West Bengal to menu
7. ⏳ Test end-to-end integration

---

**Document Version:** 1.0
**Last Updated:** 2025-01-28
**Status:** Design Complete, Ready for Implementation
