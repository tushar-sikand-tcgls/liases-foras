# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Liases Foras × Sirrus.AI Integration - A real estate knowledge graph with dimensional financial analysis, enriched with location intelligence and government data, exposed via MCP (Model Context Protocol) API layer.

**Core Innovation:**
1. Organize all real estate metrics into four dimensional layers inspired by physics (Layer 0: Raw Dimensions → Layer 3: Optimization & Benchmarking)
2. Enrich insights and recommendations with three complementary data sources
3. Expose via FastAPI endpoints with MCP semantic routing for Claude integration

**Current Status:** Active development with backend and frontend servers running. Three-input-source architecture with Google APIs integration complete, Government data integration pending.

## Data Sources Architecture

The application integrates **three complementary data sources** to provide comprehensive real estate intelligence:

### Input Source 1: Liases Foras Data
**Purpose:** Multi-layered knowledge graph for real estate financial analysis

**Data Model:** 4-dimensional Layer 0 system (L², U, T, CF) → Layer 3 optimization
- Layer 0: Raw dimensions (Area, Units, Time, Cash Flow)
- Layer 1: Derived metrics (PSF, ASP, Absorption Rate, Sales Velocity)
- Layer 2: Financial metrics (NPV, IRR, Payback Period, Profitability Index)
- Layer 3: Optimization solutions (Product Mix, Scenario Analysis, Benchmarking)

**Data Pillars:**
- Pillar 1: Market Intelligence (pricing, absorption, micro-markets)
- Pillar 2: Product Performance (typology, efficiency)
- Pillar 3: Developer Performance (APF, builder ratings, OPPS)
- Pillar 4: Financial Analysis (feasibility, cash flow, IRR/ROI)
- Pillar 5: Sales/Operations (velocity, distribution)

**Integration:** REST API with quarterly updates (Q1_FY25, Q2_FY25, etc.)

### Input Source 2: Google APIs
**Purpose:** Location intelligence and contextual enrichment

**APIs Integrated:** (Status: ✅ Implemented)
1. **Geocoding API** - Location name to coordinates conversion
2. **Places API (New)** - Nearby POIs (hospitals, schools, restaurants, hotels, malls, transport, recreation, worship)
3. **Distance Matrix API** - Travel distances and times to key destinations
4. **Maps Elevation API** - Elevation data with temperature adjustment calculations
5. **Maps Static API** - Static map images and satellite/aerial views
6. **Street View Static API** - Street-level imagery with availability checking
7. **Air Quality API** - AQI data and pollutant components
8. **Custom Search API** - Location-based image search

**Use Cases:**
- Proximity analysis (distance to hospitals, schools, transport hubs)
- Environmental context (weather, air quality, elevation)
- Visual context (maps, street views, aerial imagery, location photos)

**Integration:** Real-time API calls via `app/services/context_service.py`

### Input Source 3: Government of India Data
**Purpose:** Regulatory, planning, and demographic context

**Data Source:** data.gov.in (State and Central Government)

**Categories:** (Status: 🔄 Pending Implementation)
1. **RERA (Real Estate Regulatory Authority)**
   - Registered projects
   - Developer compliance records
   - Project approvals and permissions

2. **Smart Cities Mission**
   - Smart city plans and projects
   - Infrastructure development roadmaps
   - Investment plans

3. **Road Transport & Highways**
   - Highway projects and timelines
   - Road infrastructure plans
   - Connectivity improvements

4. **Census Data**
   - Population projections
   - Demographic trends
   - Economic indicators
   - Housing demand estimates

5. **Urban Development**
   - City master plans
   - Zoning regulations
   - Development control rules

**Use Cases:**
- Regulatory compliance verification
- Future growth projections
- Infrastructure planning insights
- Demographic demand analysis

**Integration:** (To be implemented) REST API / data.gov.in API with periodic updates

## Query Output Categories

The application processes queries across three domains, with **cross-enrichment** of insights:

### A. Liases Foras Queries

**A.1. Layer 0 Data Extraction (Raw Dimensions)**
- Queries for atomic dimensional data from LF
- Examples: "What's the total area of Project X?", "How many 2BHK units in this project?", "What's the project duration?", "What's the total investment?"
- Output: Raw U, L², T, CF values with provenance

**A.2. Layer 1 Derived Data (Simple Ratios)**
- Queries for calculated metrics from Layer 0 dimensions
- Examples: "What's the PSF?", "Calculate sales velocity", "What's the absorption rate?", "Show me the ASP"
- Output: Derived metrics with dimensional formula and source layers

**A.3. Layer 2 Financial Metrics (Complex Aggregations)**
- Queries for advanced financial calculations
- Examples: "Calculate IRR for this cash flow", "What's my NPV at 12% discount?", "Calculate payback period", "Run sensitivity analysis"
- Output: Financial metrics with calculation method, assumptions, and Layer 1 dependencies

**A.4. Layer 3 Optimization Solutions**
- Queries for strategic decision-making
- Examples: "Optimize product mix for max IRR", "Best vs worst case scenarios", "Show me 3 scenarios with different absorption rates"
- Output: Optimization results with constraints, scenarios, and trade-offs

**A.5. Insights on Liases Foras Numbers**
- Analytical interpretations of LF metrics
- Examples: "Why is absorption rate low?", "What does this IRR indicate?", "How does this compare to market average?"
- Output: **Enriched with Google (B) and Government (C) data sources**
- Example: "Low absorption rate (LF) may be due to poor proximity to transport hubs (Google) and lack of planned infrastructure (Government)"

**A.6. Recommendations on LF Insights**
- Actionable suggestions, especially for negative indicators
- Examples: "How can I improve this IRR?", "What should I do about slow sales velocity?", "Suggest product mix changes"
- Output: **Grounded in Google (B) and Government (C) data sources**
- Example: "To improve absorption, consider: (1) Proximity to upcoming metro station per Smart Cities plan (Government), (2) Distance to schools is 8km (Google) - consider shuttle service"

### B. Google Queries (Location Intelligence)
- Proximity queries: "How far is the nearest hospital?", "Show me schools within 5km"
- Environmental queries: "What's the current air quality?", "What's the elevation?", "Show me weather data"
- Visual queries: "Show me satellite view", "Display street view", "Show me photos of the area"
- Output: Real-time Google API data with maps, distances, and environmental context

### C. Government Queries (Regulatory & Planning Context)
- Regulatory queries: "Is this project RERA registered?", "Show me developer compliance record"
- Planning queries: "What are the city's growth projections?", "Show me Smart City plans for this area", "Upcoming infrastructure projects?"
- Demographic queries: "What's the population projection?", "Show me census data for this location"
- Output: Government data with source citations and update timestamps

## Cross-Source Enrichment Principle

**CRITICAL:** When generating insights (A.5) and recommendations (A.6), the system MUST:
1. Start with Liases Foras metrics as the foundation
2. Enrich with Google location intelligence (proximity, environment, visual context)
3. Ground in Government data (regulations, plans, projections)
4. Synthesize all three sources into actionable intelligence

**Example Flow:**
```
User Query: "Why is my project's absorption rate 30% below market average?"

Response:
┌─────────────────────────────────────────────────────────┐
│ LF Analysis (Source A):                                 │
│ - Absorption rate: 0.8%/month vs market avg 1.1%/month │
│ - PSF is competitive at ₹4,200 vs market ₹4,500        │
│ - Product mix: 60% 2BHK, 40% 3BHK (standard)           │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Google Context (Source B):                              │
│ - Nearest school: 12 km (above ideal 3-5 km)           │
│ - Nearest hospital: 8 km (above ideal 5 km)            │
│ - Public transport: Bus stop 2 km, no metro            │
│ - Air quality: AQI 156 (Moderate)                      │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Government Plans (Source C):                            │
│ - Metro extension planned: 3 km from project (2027)    │
│ - Smart City infrastructure: Road widening (2026)      │
│ - Census projection: 15% population growth (5 years)   │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ ENRICHED INSIGHT:                                       │
│ Your absorption is impacted by:                         │
│ 1. Distance to amenities (12km school, 8km hospital)   │
│ 2. Lack of current metro connectivity                  │
│                                                         │
│ However, upcoming government plans show:                │
│ - Metro extension by 2027 (3km away)                   │
│ - Road infrastructure improvements by 2026             │
│ - Strong population growth projection (15%)            │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ GROUNDED RECOMMENDATION:                                │
│ 1. Market timing: Launch phase 2 post-metro (2027)     │
│ 2. Amenities: Partner with schools/hospitals for       │
│    shuttle services (bridge the 12km/8km gap)          │
│ 3. Messaging: Emphasize upcoming metro + Smart City    │
│    infrastructure in marketing (Government plans)      │
│ 4. Product mix: Consider smaller units (1BHK) for      │
│    growing population (Census projection)              │
└─────────────────────────────────────────────────────────┘
```

## Technology Stack

**Backend:**
- FastAPI (Python) - REST API server
- Neo4j - Graph database for knowledge graph
- scipy - Optimization (SLSQP) and financial calculations (Newton's method for IRR)
- anthropic SDK - Claude AI integration via MCP
- pydantic - Request/response validation
- requests - HTTP client for API integrations
- python-dotenv - Environment configuration management
- Streamlit - Frontend web application framework

**Data Sources:**
- **Source 1:** Liases Foras market intelligence API (5 pillars of real estate data)
- **Source 2:** Google Maps APIs (8 APIs for location intelligence) - ✅ Integrated
- **Source 3:** Government of India data.gov.in API (RERA, Smart Cities, Census, Transport) - 🔄 Pending

**Planned Dependencies:**
```
fastapi
uvicorn
pydantic
scipy
neo4j
anthropic
pandas
numpy
```

**Environment Variables:**
- `NEO4J_URI` - Neo4j connection string
- `NEO4J_USER`, `NEO4J_PASSWORD` - Database credentials
- `LIASES_FORAS_API_KEY` - LF data access token
- `CLAUDE_API_KEY` - Anthropic API key
- `FASTAPI_HOST`, `FASTAPI_PORT` - Server configuration
- `DATA_VERSION` - Current LF data version (e.g., "Q3_FY25")
- `GOOGLE_MAPS_API_KEY` - Google Maps Platform API key ✅ Configured
- `GOOGLE_SEARCH_API_KEY` - Google Custom Search API key ✅ Configured
- `GOOGLE_SEARCH_CX` - Custom Search Engine ID ✅ Configured
- `OPENWEATHER_API_KEY` - OpenWeather API key for weather data (optional)
- `GOV_IN_API_KEY` - data.gov.in API access token 🔄 To be configured
- `GOV_IN_API_BASE_URL` - data.gov.in API base URL 🔄 To be configured

## Commands

**Development Setup (once implemented):**
```bash
# Install dependencies
pip install fastapi uvicorn pydantic scipy neo4j anthropic pandas numpy

# Run development server
python api_server.py
# or with uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run with Docker (future)
docker-compose up
```

**Testing (to be implemented):**
```bash
# Run all tests
pytest

# Run specific test module
pytest tests/test_layer2_calculator.py

# Run with coverage
pytest --cov=app --cov-report=html
```

**Neo4j Operations:**
```bash
# Connect to Neo4j browser
# http://localhost:7474

# Load initial data (future script)
python scripts/load_lf_data.py --version Q3_FY25
```

## Architecture

### Three-Tier Architecture Stack with Three-Input Sources

```
┌──────────────────────────────────────────────────────────────────┐
│ Tier 1: Claude Agent Layer (Sirrus.AI)                           │
│ - Intent classification & routing                                │
│ - Multi-turn dialogue management                                │
│ - Natural language synthesis with cross-source enrichment       │
│ - Query type detection: LF | Google | Government | Hybrid       │
└──────────────────────────────────────────────────────────────────┘
                              ↑ ↓ (MCP Protocol)
┌──────────────────────────────────────────────────────────────────┐
│ Tier 2: MCP API Layer (FastAPI)                                  │
│ - GET /api/mcp/info (capability discovery across all sources)   │
│ - POST /api/mcp/query (query execution with source routing)     │
│ - Cross-source enrichment orchestration                         │
│ - Response synthesis from multiple sources                      │
└──────────────────────────────────────────────────────────────────┘
                              ↑ ↓
┌──────────────────────────────────────────────────────────────────┐
│ Tier 3: Data Integration & Processing Layer                      │
│                                                                  │
│  ┌─────────────────┐  ┌──────────────┐  ┌────────────────────┐ │
│  │ Source 1:       │  │ Source 2:    │  │ Source 3:          │ │
│  │ Liases Foras    │  │ Google APIs  │  │ Government Data    │ │
│  │                 │  │              │  │                    │ │
│  │ • Layer 0: U,   │  │ • Geocoding  │  │ • RERA             │ │
│  │   L², T, CF     │  │ • Places     │  │ • Smart Cities     │ │
│  │ • Layer 1: PSF, │  │ • Distance   │  │ • Road Transport   │ │
│  │   ASP, AR       │  │   Matrix     │  │ • Census           │ │
│  │ • Layer 2: NPV, │  │ • Elevation  │  │ • Urban Plans      │ │
│  │   IRR, Payback  │  │ • Static Map │  │                    │ │
│  │ • Layer 3:      │  │ • Street View│  │ Status: 🔄 Pending │ │
│  │   Optimization  │  │ • Air Quality│  │                    │ │
│  │                 │  │              │  │                    │ │
│  │ 5 Pillars       │  │ 8 APIs ✅    │  │ data.gov.in API    │ │
│  └─────────────────┘  └──────────────┘  └────────────────────┘ │
│                                                                  │
│  Neo4j Knowledge Graph + Calculation Engine (scipy)             │
└──────────────────────────────────────────────────────────────────┘

Data Flow for Enriched Insights:
┌─────────────────────────────────────────────────────────────────┐
│ User: "Why is absorption rate low for Project X?"              │
└─────────────────────────────────────────────────────────────────┘
           ↓
    ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
    │ LF Data:    │ →  │ Google Data: │ →  │ Government:     │
    │ Absorption  │    │ Proximity to │    │ Metro plans,    │
    │ metrics,    │    │ schools,     │    │ Smart City      │
    │ PSF, market │    │ hospitals,   │    │ roadmap,        │
    │ comparison  │    │ transport,   │    │ census growth   │
    └─────────────┘    │ AQI          │    │ projections     │
                       └──────────────┘    └─────────────────┘
           ↓                  ↓                      ↓
    ┌──────────────────────────────────────────────────────────┐
    │ ENRICHED INSIGHT: "Absorption is 30% below average       │
    │ because: (1) 12km from nearest school (Google), (2) No   │
    │ current metro (Google), BUT (3) Metro extension planned  │
    │ by 2027 per Smart Cities Mission (Government)"           │
    └──────────────────────────────────────────────────────────┘
```

### Four-Layer Dimensional Knowledge Graph

The system organizes all metrics into 4 layers using dimensional analysis (physics-inspired):

**Layer 0: Raw Dimensions (Atomic Units)**
- **U** (Units): Count of housing units (1BHK, 2BHK, 3BHK) - analogous to Mass
- **L²** (Space): Area in sqft/sqm (carpet, saleable, built-up) - analogous to Length²
- **T** (Time): Months/years (sales cycle, project duration) - analogous to Time
- **CF** (Cash Flow): INR/month (revenue, cost, investment) - analogous to Current

**Layer 1: Derived Dimensions (Simple Ratios & Products)**

All Layer 1 metrics are calculated from Layer 0 using dimensional analysis:

| Metric | Dimension | Formula | LF Pillar |
|--------|-----------|---------|-----------|
| Price Per Sqft (PSF) | CF/L² | Total Revenue / Saleable Area | 1.1 |
| Average Selling Price (ASP) | CF/U | Total Revenue / Units | 2.1 |
| Sales Velocity | U/T | Units Sold / Months | 1.2 |
| Absorption Rate | (U/U_total)/T | % Units Sold / Month | 1.2 |
| Density | U/L² | Total Units / Land Area | 2.1 |
| Cost Per Sqft | CF/L² | Total Cost / Area | 4.1 |
| Revenue Run Rate | CF/T | Monthly Revenue | 4.2 |

**Layer 2: Financial Metrics (Complex Aggregations)**

Advanced financial metrics requiring integration of multiple Layer 1 metrics:

| Metric | Dimension | Formula | Algorithm |
|--------|-----------|---------|-----------|
| NPV | CF | ∑[CF_t / (1+r)^t] - Initial_Inv | Direct calculation |
| IRR | T^(-1) | r where NPV(r) = 0 | Newton's method (scipy) |
| Payback Period | T | Time when cumulative CF = Initial_Inv | Iterative |
| Profitability Index | Dimensionless | (NPV + Initial_Inv) / Initial_Inv | Direct |
| Cap Rate | T^(-1) | Annual NOI / Property Value | Direct |

**Layer 3: Optimization & Scenario Planning**

Strategic decision-making combining all layers:
- Product Mix Optimization (maximize IRR given constraints) - uses scipy.optimize.minimize with SLSQP
- Sensitivity Analysis (IRR/NPV under different absorption & price scenarios)
- Developer Benchmarking (compare against peer developers using LF Pillar 3)
- Market Opportunity Scoring (using LF OPPS scores)

## MCP API Endpoints

### GET /api/mcp/info

Capability discovery endpoint returning all available tools across 4 layers.

**Returns:**
- Layer 0 tools: `get_project_dimensions`
- Layer 1 tools: `calculate_psf`, `calculate_asp`, `calculate_absorption_rate`, `calculate_sales_velocity`
- Layer 2 tools: `calculate_npv`, `calculate_irr`, `calculate_payback_period`, `calculate_sensitivity_analysis`
- Layer 3 tools: `optimize_product_mix`, `developer_benchmarking`, `market_opportunity_scoring`
- LF integration tools: `fetch_lf_market_data`, `fetch_lf_product_data`, `fetch_lf_developer_rating`

### POST /api/mcp/query

Query execution endpoint with routing to appropriate layer handler.

**Request Schema:**
```json
{
  "queryId": "unique-query-id",
  "queryType": "calculation|optimization|comparison|benchmarking",
  "layer": 0-3,
  "capability": "calculate_irr|optimize_product_mix|...",
  "parameters": {...},
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
  "status": "success|error",
  "layer": 0-3,
  "capability": "string",
  "result": {
    "value": "number|object",
    "unit": "string",
    "dimension": "CF|U|L2|T|Dimensionless|Composite"
  },
  "provenance": {
    "inputDimensions": ["L0_dimension1", "L0_dimension2"],
    "calculationMethod": "string",
    "lfSource": "Pillar_X.Y",
    "timestamp": "ISO-8601",
    "dataVersion": "Q3_FY25"
  },
  "relatedMetrics": [...],
  "executionTime_ms": number,
  "dataLineage": {
    "layer0_inputs": {...},
    "layer1_intermediates": [...],
    "layer2_dependencies": [...]
  }
}
```

**Key Design Principle:** Every calculation result includes full provenance (which Layer 0 dimensions were used, which formula, which LF data pillar, timestamp) and data lineage tracking.

## Core Calculation Modules

### Layer2Calculator (Financial Metrics)

When implementing `app/calculators/layer2.py`:

```python
class Layer2Calculator:
    @staticmethod
    def calculate_npv(projection: FinancialProjection) -> float:
        """NPV = ∑[CF_t / (1+r)^t] - Initial_Investment"""

    @staticmethod
    def calculate_irr(projection: FinancialProjection) -> float:
        """IRR = r such that NPV(r) = 0
        Uses scipy.optimize.newton for root finding"""

    @staticmethod
    def calculate_payback_period(projection: FinancialProjection) -> float:
        """PBP = time when cumulative CF = Initial_Investment"""

    @staticmethod
    def calculate_profitability_index(projection: FinancialProjection) -> float:
        """PI = (NPV + Initial_Inv) / Initial_Inv"""

    @staticmethod
    def calculate_cap_rate(annual_noi: float, property_value: float) -> float:
        """Cap Rate = Annual NOI / Property Value"""
```

**Critical:** All financial calculations must match LF standards within ±2% tolerance (acceptance criteria #5).

### Layer3Optimizer (Product Mix Optimization)

When implementing `app/calculators/layer3.py`:

```python
class Layer3Optimizer:
    def optimize_product_mix(
        total_units: int,           # Layer 0: U
        total_land_area_sqft: float,  # Layer 0: L²
        total_project_cost: float,    # Layer 0: CF
        project_duration_months: int, # Layer 0: T
        market_data: Dict,            # Layer 1 metrics from LF
        developer_marketability: float  # Layer 3: LF Pillar 3
    ) -> Dict:
        """
        Optimizes unit mix (1BHK/2BHK/3BHK) to maximize IRR.

        Uses scipy.optimize.minimize with SLSQP method.

        Constraints:
        - Total units must equal specified count
        - Total area must not exceed land area
        - Absorption rate must not exceed LF historical max

        Returns 3 scenarios: Base Case, Optimistic, Conservative
        """
```

**Optimization Method:** Always use scipy's SLSQP (Sequential Least Squares Programming) for constrained optimization.

## Neo4j Knowledge Graph Schema

### Key Node Types

**Layer 0 Nodes:**
- `(:Dimension_L0)` - Atomic dimensional units (U, L², T, CF)
- `(:Project)` - Real estate projects with all L0 dimensions
- `(:Unit)` - Individual housing units with properties
- `(:Location)` - City/micromarket data

**Layer 1 Nodes:**
- `(:Metric_L1)` - Derived metrics (PSF, ASP, Absorption Rate, etc.)

**Layer 2 Nodes:**
- `(:Metric_L2)` - Financial metrics (NPV, IRR, etc.) with sensitivity ranges

**Layer 3 Nodes:**
- `(:Scenario_L3)` - Optimization scenarios with unit mix and results
- `(:Capability_L3)` - Reusable optimization capabilities

### Key Relationships

```cypher
(:Project) -[:HAS_UNITS_L0]-> (:Unit)
(:Project) -[:CONTAINS_METRIC_L1]-> (:Metric_L1)
(:Project) -[:CONTAINS_METRIC_L2]-> (:Metric_L2)
(:Project) -[:SCENARIO_L3]-> (:Scenario_L3)

(:Metric_L1) -[:DERIVES_FROM_L0]-> (:Project)
(:Metric_L2) -[:DEPENDS_ON_L1]-> (:Metric_L1)
(:Scenario_L3) -[:USES_L2]-> (:Metric_L2)

(:Scenario_L3) -[:POWERED_BY]-> (:Capability_L3)
(:Capability_L3) -[:CONSUMES]-> (:Dimension_L0)
```

### Neo4j Indexes (to be created)

```cypher
CREATE INDEX project_id FOR (p:Project) ON (p.projectId);
CREATE INDEX metric_l1_name FOR (m:Metric_L1) ON (m.metricName);
CREATE INDEX metric_l2_type FOR (m:Metric_L2) ON (m.metricType);
CREATE INDEX scenario_id FOR (s:Scenario_L3) ON (s.scenarioId);
```

**Performance Target:** 100K+ project nodes, <500ms query response (acceptance criteria #9).

## Liases Foras Integration

### Five Data Pillars

**Pillar 1: Market Intelligence**
- Price trends and movements (PSF, ASP)
- Absorption rates and sales velocity
- Micro-market evaluation
- Competitive intensity analysis

**Pillar 2: Product Performance**
- Typology performance (1BHK/2BHK/3BHK mix effectiveness)
- Efficiency metrics
- Launch strategies

**Pillar 3: Developer Performance**
- APF (Architect Performance Factor)
- Builder ratings
- OPPS (Opportunity Pocket Scoring)
- Marketability index

**Pillar 4: Financial**
- Feasibility analysis (4.1)
- Cash flow & scenario modeling (4.2)
- IRR & ROI calculations (4.3)

**Pillar 5: Sales/Operations**
- Sales velocity patterns
- Distribution strategies
- Operational efficiency

### MCP Tools for LF Access

```python
# Pillar 1 Access
fetch_lf_market_data(location: str, dataType: str)
# dataType: "absorption|pricing|trends|competitiveIntensity"

# Pillar 2 Access
fetch_lf_product_data(location: str, unitTypes: List[str])

# Pillar 3 Access
fetch_lf_developer_rating(developerId: str)
# Returns: APF score, builder rating, OPPS score
```

**Data Freshness:** Quarterly updates (Q1, Q2, Q3, Q4). All responses include `lfDataVersion` field.

## Government Data Integration

### MCP Tools for Government Data Access (To be implemented)

```python
# RERA Data Access
fetch_rera_project_data(project_name: str, city: str)
# Returns: Registration status, developer name, approved area, completion date

fetch_rera_developer_compliance(developer_id: str)
# Returns: Compliance history, pending approvals, violations

# Smart Cities Data Access
fetch_smart_city_projects(city: str, category: str = "all")
# category: "metro|roads|utilities|commercial|all"
# Returns: Project list with timelines, budgets, completion status

fetch_smart_city_master_plan(city: str)
# Returns: City development plan, zoning, future infrastructure

# Road Transport Data Access
fetch_highway_projects(city: str, radius_km: float = 50)
# Returns: Highway construction/widening projects within radius

fetch_metro_projects(city: str)
# Returns: Metro lines (operational, under construction, planned) with timelines

# Census Data Access
fetch_census_demographics(city: str, area: str = None)
# Returns: Population, growth rate, income distribution, housing demand

fetch_census_projections(city: str, years_ahead: int = 5)
# Returns: Population projections, economic indicators

# Urban Development Data Access
fetch_city_master_plan(city: str)
# Returns: Zoning regulations, development control rules, permitted FSI

fetch_development_approvals(area: str, radius_km: float = 10)
# Returns: Recent approvals, pending applications
```

### Data Schema (Government Sources)

**RERA Project Schema:**
```json
{
  "projectName": "string",
  "reraNumber": "string",
  "developerName": "string",
  "registrationDate": "YYYY-MM-DD",
  "approvedArea": "number (sqm)",
  "approvedUnits": "number",
  "completionDate": "YYYY-MM-DD",
  "complianceStatus": "Active|Lapsed|Revoked",
  "source": "rera.maharashtra.gov.in",
  "lastUpdated": "ISO-8601"
}
```

**Smart Cities Project Schema:**
```json
{
  "projectName": "string",
  "city": "string",
  "category": "metro|roads|utilities|commercial",
  "budget": "number (INR Cr)",
  "timeline": {
    "startDate": "YYYY-MM-DD",
    "expectedCompletion": "YYYY-MM-DD",
    "status": "Planned|Under Construction|Operational"
  },
  "location": {
    "coordinates": [lat, lng],
    "affectedAreas": ["area1", "area2"]
  },
  "source": "smartcities.gov.in",
  "lastUpdated": "ISO-8601"
}
```

**Census Projection Schema:**
```json
{
  "city": "string",
  "area": "string",
  "currentPopulation": "number",
  "projectedPopulation": {
    "year2025": "number",
    "year2030": "number"
  },
  "growthRate": "number (%)",
  "demographics": {
    "medianAge": "number",
    "householdSize": "number",
    "incomeDistribution": {
      "low": "number (%)",
      "middle": "number (%)",
      "high": "number (%)"
    }
  },
  "housingDemand": {
    "currentUnits": "number",
    "projectedUnits2030": "number"
  },
  "source": "censusindia.gov.in",
  "lastUpdated": "ISO-8601"
}
```

### Integration Workflow (To be implemented)

```python
# app/services/government_service.py

class GovernmentDataService:
    """Service for integrating Government of India data sources"""

    def __init__(self):
        self.api_key = os.getenv("GOV_IN_API_KEY")
        self.base_url = os.getenv("GOV_IN_API_BASE_URL")

    async def fetch_rera_data(self, project_name: str, city: str) -> Dict:
        """Fetch RERA registration data for a project"""
        # Implementation to be added

    async def fetch_smart_city_projects(self, city: str, category: str = "all") -> List[Dict]:
        """Fetch Smart Cities Mission projects for a city"""
        # Implementation to be added

    async def fetch_census_projections(self, city: str, years_ahead: int = 5) -> Dict:
        """Fetch census population projections"""
        # Implementation to be added

    async def fetch_metro_projects(self, city: str) -> List[Dict]:
        """Fetch metro rail projects (operational, under construction, planned)"""
        # Implementation to be added
```

## Common Use Cases

### Use Case 1: Product Mix Optimization

**Query:** "What's the best product mix for a 100-unit tower in Chakan, Pune?"

**Flow:**
1. Layer 3 query to `optimize_product_mix`
2. System fetches Layer 1 data (PSF, absorption rates by unit type)
3. System fetches LF Pillar 1.2 & 2.1 market data for Chakan
4. Runs scipy optimization with constraints
5. Generates 3 scenarios (Base, Optimistic, Conservative)
6. Returns optimal mix with IRR/NPV for each scenario

### Use Case 2: IRR Calculation

**Query:** "What's my IRR if cash flows are [12.5, 15, 17.5, 20, 22.5] Cr over 5 years with 50 Cr investment?"

**Flow:**
1. Layer 2 query to `calculate_irr`
2. System applies Newton's method to solve NPV(r) = 0
3. Returns IRR percentage with provenance
4. Auto-computes related metrics (NPV at 12% discount)

### Use Case 3: Sensitivity Analysis

**Query:** "How sensitive is my IRR to changes in absorption rate and pricing?"

**Flow:**
1. Layer 2 query to `calculate_sensitivity_analysis`
2. System runs scenarios across absorption range [min, max] and price variance [-x%, +x%]
3. Returns Base Case, Optimistic Case, Stress Case IRR/NPV
4. Includes variance ranges

### Use Case 4: Cross-Source Enriched Insight (CRITICAL EXAMPLE)

**Query:** "Why is my project's absorption rate 30% below market average, and what should I do?"

**Flow (Three-Source Enrichment):**

1. **Step 1: Fetch Liases Foras Data (Source A)**
   - Query Layer 1 metrics for the project
   - Fetch absorption rate: 0.8%/month vs market avg 1.1%/month (LF Pillar 1.2)
   - Fetch PSF: ₹4,200 vs market ₹4,500 (LF Pillar 1.1)
   - Fetch product mix: 60% 2BHK, 40% 3BHK (LF Pillar 2.1)
   - Result: Pricing is competitive, product mix is standard, but absorption is significantly low

2. **Step 2: Fetch Google Location Intelligence (Source B)**
   - Query `get_location_context()` for project location
   - Distance to nearest school: 12 km (via Distance Matrix API)
   - Distance to nearest hospital: 8 km (via Distance Matrix API)
   - Public transport: Bus stop 2 km, no metro station within 10km (via Places API)
   - Air quality: AQI 156 - Moderate (via Air Quality API)
   - Result: Poor proximity to key amenities, lack of metro connectivity

3. **Step 3: Fetch Government Plans & Regulations (Source C)**
   - Query `fetch_metro_projects("Pune")` → Metro extension planned 3km from project (completion 2027)
   - Query `fetch_smart_city_projects("Pune", "roads")` → Road widening project (completion 2026)
   - Query `fetch_census_projections("Pune", 5)` → 15% population growth projected over 5 years
   - Query `fetch_rera_project_data(project_name, "Pune")` → RERA registered, compliance active
   - Result: Strong government investment in infrastructure, positive growth trajectory, regulatory compliance confirmed

4. **Step 4: Synthesize Enriched Insight (Cross-Source)**

   **Response:**
   ```
   INSIGHT (Cross-Source Analysis):

   Your absorption rate is 30% below market average (0.8% vs 1.1%/month).

   ROOT CAUSE ANALYSIS (3 Sources):

   1. LF Analysis (Source A - Liases Foras):
      - Your PSF is competitive at ₹4,200 (market avg ₹4,500) ✅
      - Product mix is standard: 60% 2BHK, 40% 3BHK ✅
      - Absorption rate significantly below average ❌
      → Pricing and product mix are NOT the issue

   2. Location Context (Source B - Google APIs):
      - Distance to nearest school: 12 km (ideal: 3-5 km) ❌
      - Distance to nearest hospital: 8 km (ideal: <5 km) ❌
      - No metro connectivity within 10km ❌
      - Air quality: AQI 156 (Moderate) ⚠️
      → Poor proximity to amenities is a major factor

   3. Government Plans (Source C - Government Data):
      - Metro extension PLANNED: 3 km from project (2027) ✅
      - Smart Cities road widening: Completion 2026 ✅
      - Census population growth: +15% over 5 years ✅
      - RERA compliance: Active and current ✅
      → Future infrastructure and demographics are POSITIVE

   GROUNDED RECOMMENDATIONS:

   1. TIMING STRATEGY:
      - Phase current inventory conservatively (align with metro completion)
      - Launch Phase 2 post-metro extension (2027+) to capitalize on connectivity
      - Source: Smart Cities Mission timeline (data.gov.in)

   2. AMENITY GAP MITIGATION:
      - Partner with nearby schools (12km) for dedicated shuttle service
      - Partner with hospital (8km) for medical shuttle/emergency access
      - Add these partnerships to marketing materials
      - Source: Google Distance Matrix API showing 12km school, 8km hospital

   3. MARKETING REPOSITIONING:
      - Emphasize upcoming metro (3km, 2027) in all communications
      - Highlight Smart Cities road infrastructure (2026 completion)
      - Position as "growth corridor" based on 15% population projection
      - Source: Census projections (censusindia.gov.in) + Smart Cities data

   4. PRODUCT MIX ADJUSTMENT:
      - Consider adding 1BHK units (20-30% mix) for growing young demographic
      - Target first-time buyers who will benefit from future metro connectivity
      - Source: Census demographics showing population growth

   5. INTERIM INCENTIVES:
      - Offer price protection: Lock current price with delivery post-metro
      - Early bird benefits: "Pre-metro pricing" campaign
      - Guaranteed rental assistance until metro operational
      - Source: LF market intelligence showing price sensitivity

   EXPECTED IMPACT:
   - Short-term (6-12 months): Absorption improvement to 0.9-1.0%/month
   - Post-metro (2027+): Absorption expected at 1.2-1.4%/month (above market avg)
   - IRR impact: Maintain current 18% IRR with phased approach vs 15% with forced liquidation

   DATA SOURCES:
   - LF Pillar 1.2, 2.1 (Q3_FY25)
   - Google Distance Matrix API, Places API (2025-01-28)
   - Smart Cities Mission portal (smartcities.gov.in, updated 2024-12-15)
   - Census India projections (censusindia.gov.in, 2021 base year)
   ```

**Key Principle Demonstrated:**
This use case shows how insights are NEVER generated from LF data alone. Instead:
- LF identifies WHAT the problem is (low absorption)
- Google explains WHY it's happening (poor proximity to amenities)
- Government data provides FUTURE CONTEXT (upcoming infrastructure that changes the equation)
- The recommendation is GROUNDED in all three sources

## Implementation Roadmap

**Phase 1: Foundation ✅ COMPLETE**
- PRD specification complete ✓
- Reference dashboard sample ✓
- FastAPI server structure ✓
- Streamlit frontend ✓
- Basic data loading (3 projects, 5 LF datasets, 54 VectorDB documents) ✓

**Phase 2: Google APIs Integration ✅ COMPLETE**
1. ✅ Implement Context Service (`app/services/context_service.py`)
2. ✅ Integrate 8 Google Maps APIs (Geocoding, Places, Distance Matrix, Elevation, Static Map, Street View, Air Quality, Custom Search)
3. ✅ Implement frontend Context Panel (`frontend/components/context_panel.py`)
4. ✅ Display 9 location context sections (Map, Photos, Weather, Air Quality, Elevation, Distances, Nearby Places, Aerial View, Street View)
5. ✅ Configure environment variables and API keys
6. ⚠️ Pending: Enable Geocoding API and Air Quality API in Google Cloud Console (user action required)

**Phase 3: Government Data Integration 🔄 IN PROGRESS**
1. 🔄 Research data.gov.in API structure and available datasets
2. 🔄 Implement Government Data Service (`app/services/government_service.py`)
3. 🔄 Integrate RERA data (project registration, developer compliance)
4. 🔄 Integrate Smart Cities Mission data (metro projects, infrastructure plans)
5. 🔄 Integrate Census data (demographics, projections)
6. 🔄 Integrate Road Transport data (highway projects)
7. 🔄 Configure environment variables (GOV_IN_API_KEY, GOV_IN_API_BASE_URL)
8. 🔄 Add Government data sections to frontend

**Phase 4: Liases Foras Core Implementation (Next)**
1. ❌ Implement Layer 2 Calculator (NPV, IRR, Payback) (`app/calculators/layer2.py`)
2. ❌ Implement Layer 3 Optimizer (product mix optimization) (`app/calculators/layer3.py`)
3. ❌ Implement Layer 1 calculators (PSF, ASP, Absorption Rate, Sales Velocity)
4. ❌ Create MCP endpoints (/api/mcp/info, /api/mcp/query)
5. ❌ Implement cross-source enrichment logic for insights (A.5) and recommendations (A.6)

**Phase 5: Neo4j Integration**
1. ❌ Deploy Neo4j database
2. ❌ Create schema and indexes for 3-source architecture
3. ❌ Implement data loaders for LF data
4. ❌ Implement data loaders for Google data (caching layer)
5. ❌ Implement data loaders for Government data (caching layer)
6. ❌ Build query handlers for all layers with provenance tracking

**Phase 6: Claude Integration & MCP**
1. ❌ Integrate Anthropic SDK
2. ❌ Implement MCP protocol with three-source routing
3. ❌ Implement intent classification (LF | Google | Government | Hybrid)
4. ❌ Test multi-turn dialogues with cross-source enrichment
5. ❌ Validate tool routing and capability discovery

**Phase 7: Testing & Validation**
1. ❌ Unit tests for all calculators (±2% accuracy)
2. ❌ Integration tests for MCP endpoints
3. ❌ Cross-source enrichment validation (ensure A.5 and A.6 always use all 3 sources)
4. ❌ Performance testing (100K nodes, <500ms LF queries, <3s enriched insights)
5. ❌ End-to-end use case validation (Use Case 4 as benchmark)
6. ❌ Data provenance and citation accuracy testing

**Current Status Summary:**
- **Source 1 (Liases Foras):** Mock data loaded, calculators pending ⚠️
- **Source 2 (Google APIs):** Fully integrated and operational ✅
- **Source 3 (Government Data):** Not yet implemented 🔄

## Acceptance Criteria

When implementing features, validate against these criteria:

### Three-Source Architecture Criteria (CRITICAL)

1. **Cross-Source Enrichment Mandatory:**
   - ALL insights (A.5) MUST include data from all three sources (LF + Google + Government)
   - ALL recommendations (A.6) MUST be grounded in all three sources
   - System MUST refuse to generate A.5 or A.6 if any source is unavailable (fail gracefully with explanation)

2. **Source Attribution:**
   - Every insight MUST cite specific sources with timestamps
   - LF citations: Include pillar number (1.x, 2.x, etc.) and data version (Q3_FY25)
   - Google citations: Include API name and query timestamp
   - Government citations: Include source URL, agency, and last updated date

3. **Data Freshness Indicators:**
   - LF data: Display quarterly version (e.g., "Q3_FY25")
   - Google data: Display "Real-time" or timestamp
   - Government data: Display "Last updated: YYYY-MM-DD"

### Performance Criteria

4. **Query Performance:**
   - Single-source queries (A.1, A.2, A.3, A.4, B, C): <1 second response time
   - Cross-source enriched insights (A.5, A.6): <3 seconds response time
   - Neo4j queries: <500ms for LF data retrieval
   - Google API calls: <2 seconds for location context aggregation

5. **MCP Discovery:**
   - GET /api/mcp/info returns all 4 LF layers + 15+ LF tools
   - GET /api/mcp/info returns 8+ Google API tools
   - GET /api/mcp/info returns 10+ Government data tools
   - Total: 35+ tools across all three sources

### Data Quality Criteria

6. **Layer 0 Data:** All LF projects have U, L², T, CF dimensions with provenance

7. **Layer 1 Accuracy:** PSF, ASP, Absorption Rate, Sales Velocity within ±2% of manual calculation

8. **Layer 2 Accuracy:** NPV, IRR, Payback Period match LF standards within ±2%

9. **Layer 3 Scenarios:** Product mix optimization returns 3 scenarios (Base, Optimistic, Conservative) with IRR variance <±5%

10. **Google Data Accuracy:**
    - Distance calculations within ±5% of Google Maps UI
    - Air Quality AQI matches OpenWeather within ±10 points
    - Elevation data within ±10 meters

11. **Government Data Validation:**
    - RERA project IDs verified against rera.maharashtra.gov.in
    - Smart Cities projects match smartcities.gov.in official data
    - Census projections match censusindia.gov.in official reports

### Integration Criteria

12. **Claude Integration:** Multi-turn dialogue with tool use works seamlessly across all three sources

13. **Neo4j Performance:**
    - 100K+ project nodes from all three sources
    - <500ms query response for LF data
    - <200ms query response for cached Google/Government data

14. **Provenance Tracking (Three-Source):**
    - Every result includes source identification (LF | Google | Government)
    - Every result includes data lineage (which Layer 0 inputs → Layer 1 intermediates → Layer 2/3 outputs)
    - Every result includes temporal provenance (data version/timestamp)

15. **Use Case 4 Validation (Benchmark):**
    - Cross-source enrichment workflow completes successfully
    - Response includes data from all three sources
    - Recommendations are actionable and grounded in source citations
    - Total response time <3 seconds

## Key Design Principles

1. **Three-Source Enrichment (CRITICAL):**
   - All insights (A.5) and recommendations (A.6) MUST synthesize data from all three sources
   - Liases Foras provides the analytical foundation (metrics, financials)
   - Google APIs provide contextual grounding (proximity, environment, location)
   - Government data provides future-oriented validation (plans, regulations, projections)
   - Never generate insights from LF data alone - always enrich with Google and Government context

2. **Dimensional Consistency:** All Liases Foras metrics must trace back to Layer 0 dimensions (U, L², T, CF)

3. **Provenance First:** Every calculation must include full provenance and data lineage across all three sources
   - LF metrics: Include pillar (1.x, 2.x, 3.x, 4.x, 5.x) and data version (Q3_FY25)
   - Google APIs: Include API name and timestamp
   - Government data: Include source agency, dataset name, and publication date

4. **Source Citation Standards:**
   - LF data: Always cite pillar number and metric layer
   - Google data: Cite specific API and query parameters
   - Government data: Cite source URL and update frequency

5. **Accuracy Standards:** Financial calculations must match industry standards within ±2%

6. **Performance Targets:**
   - API responses <1s for single-source queries
   - API responses <3s for cross-source enriched insights
   - Neo4j queries <500ms

7. **Data Freshness:**
   - LF data: Quarterly updates with version tracking (Q1_FY25, Q2_FY25, etc.)
   - Google APIs: Real-time data
   - Government data: Variable frequency (mark update date on all responses)

## Reference Documentation

- **PRD:** `PRD-v2-API-MCP-Implementation.md` - Complete technical specification with code examples
- **Sample Dashboard:** `liases-foras-sample-dashboard-for-scraping-as-per-PRD.html` - Reference UI

For detailed implementation examples of Layer 2 Calculator, Layer 3 Optimizer, FastAPI endpoints, and Neo4j schema, refer to the PRD which contains complete Python code samples.
