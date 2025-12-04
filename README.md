# Liases Foras Real Estate Analytics Platform

🏢 Four-Layer Dimensional Knowledge Graph with MCP API and Streamlit Chat Interface

## Overview

A comprehensive real estate analytics platform that organizes metrics into four dimensional layers (inspired by physics) and exposes them via MCP (Model Context Protocol) API for Claude integration, with a user-friendly Streamlit chat interface.

### Key Features

- ✅ **4-Layer Architecture**: Layer 0 (Raw Dimensions) → Layer 1 (Derived Metrics) → Layer 2 (Financial) → Layer 3 (Optimization)
- ✅ **MCP API**: GET /api/mcp/info (capability discovery) + POST /api/mcp/query (query execution)
- ✅ **Streamlit Chat**: Natural language interface for real estate analytics
- ✅ **Financial Calculations**: NPV, IRR, Payback Period with ±2% accuracy
- ✅ **Product Mix Optimization**: scipy-based SLSQP optimization to maximize IRR
- ✅ **Full Provenance**: Track data lineage across all layers
- ✅ **Sample Data**: 3 realistic Chakan (Pune) projects with market data

## Technology Stack

- **Backend**: FastAPI, scipy (optimization/IRR), pydantic
- **Frontend**: Streamlit
- **Data**: In-memory Python (mock LF data), future Neo4j integration
- **Testing**: pytest with coverage

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone <repo-url>
cd liases-foras

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Generate Sample Data

```bash
# Scrape market data from HTML dashboard
python scripts/scrape_dashboard.py

# Generate 3 sample projects
python scripts/generate_mock_data.py
```

**Output:**
- `data/chakan_market_data.json` - Market data for Chakan, Pune
- `data/sample_projects.json` - 3 sample projects (Sara City, Pradnyesh Shriniwas, Sara Nilaay)
- `data/lf_mock_responses/*.json` - 5 LF pillar mock responses

### 3. Run Backend API

```bash
# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

**API will be available at:**
- http://localhost:8000 - Root endpoint
- http://localhost:8000/docs - Interactive API documentation (Swagger)
- http://localhost:8000/api/mcp/info - MCP capability discovery
- http://localhost:8000/api/mcp/query - MCP query execution

### 4. Run Streamlit Chat Interface

```bash
# In a new terminal (keep FastAPI running)
streamlit run frontend/streamlit_app.py
```

**Chat interface will open at:** http://localhost:8501

## Architecture

### Four-Layer Dimensional Knowledge Graph

```
┌──────────────────────────────────────────────┐
│ Layer 0: Raw Dimensions (Atomic Units)       │
│ - U (Units): Count of housing units          │
│ - L² (Area): sqft/sqm                        │
│ - T (Time): months/years                     │
│ - CF (Cash Flow): INR                        │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│ Layer 1: Derived Metrics (Simple Ratios)     │
│ - PSF (Price Per Sqft): CF/L²                │
│ - ASP (Avg Selling Price): CF/U              │
│ - Absorption Rate: (U/U_total)/T             │
│ - Sales Velocity: U/T                        │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│ Layer 2: Financial Metrics (Complex)         │
│ - NPV: ∑[CF_t / (1+r)^t] - Initial_Inv       │
│ - IRR: r where NPV(r) = 0                    │
│ - Payback Period: Time to recover investment │
│ - Sensitivity Analysis                       │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│ Layer 3: Optimization & Scenarios            │
│ - Product Mix Optimization (scipy SLSQP)     │
│ - Market Opportunity Scoring (OPPS)          │
│ - Developer Benchmarking                     │
└──────────────────────────────────────────────┘
```

## Use Cases

### 1. Product Mix Optimization

**Query:** "What's the optimal product mix for a 100-unit tower in Chakan?"

```bash
curl -X POST http://localhost:8000/api/mcp/query \
  -H "Content-Type: application/json" \
  -d '{
    "queryType": "optimization",
    "layer": 3,
    "capability": "optimize_product_mix",
    "parameters": {
      "location": "Chakan, Pune",
      "totalUnits": 100,
      "totalArea": 70000
    }
  }'
```

**Response:**
```json
{
  "result": {
    "optimal_mix": {
      "1BHK": 0.30,
      "2BHK": 0.50,
      "3BHK": 0.20
    },
    "scenarios": [
      {"scenarioName": "Base Case", "irr_percent": 24.0, "npv_crore": 52.0},
      {"scenarioName": "Optimistic", "irr_percent": 26.0, "npv_crore": 55.0},
      {"scenarioName": "Conservative", "irr_percent": 21.0, "npv_crore": 48.0}
    ]
  },
  "provenance": {
    "lfCapabilitiesApplied": ["2.1", "4.1", "4.3"],
    "algorithm": "scipy.optimize.minimize with SLSQP method"
  }
}
```

### 2. IRR Calculation

**Query:** "Calculate IRR for cash flows of 12.5, 15, 17.5, 20, 22.5 Cr over 5 years"

```bash
curl -X POST http://localhost:8000/api/mcp/query \
  -H "Content-Type: application/json" \
  -d '{
    "queryType": "calculation",
    "layer": 2,
    "capability": "calculate_irr",
    "parameters": {
      "cashFlows": [125000000, 150000000, 175000000, 200000000, 225000000],
      "initialInvestment": 500000000
    }
  }'
```

**Response:**
```json
{
  "result": {
    "metric": "IRR",
    "value": 24.0,
    "unit": "%/year",
    "dimension": "T^-1"
  },
  "provenance": {
    "algorithm": "Newton's method (scipy.optimize.newton)",
    "lfSource": "Pillar_4.3"
  }
}
```

### 3. Sensitivity Analysis

**Query:** "Run sensitivity analysis on IRR"

```bash
curl -X POST http://localhost:8000/api/mcp/query \
  -H "Content-Type: application/json" \
  -d '{
    "queryType": "calculation",
    "layer": 2,
    "capability": "calculate_sensitivity_analysis",
    "parameters": {
      "cashFlows": [125000000, 150000000, 175000000, 200000000, 225000000],
      "initialInvestment": 500000000,
      "absorptionRange": [0.7, 1.3],
      "priceRange": [0.9, 1.1]
    }
  }'
```

## API Endpoints

### GET /api/mcp/info

Capability discovery endpoint returning all available tools across 4 layers.

**Response:**
- Layer 0 tools: `get_project_dimensions`
- Layer 1 tools: `calculate_psf`, `calculate_asp`, `calculate_absorption_rate`, `calculate_sales_velocity`
- Layer 2 tools: `calculate_npv`, `calculate_irr`, `calculate_payback_period`, `calculate_sensitivity_analysis`
- Layer 3 tools: `optimize_product_mix`, `market_opportunity_scoring`

### POST /api/mcp/query

Query execution endpoint with layer routing.

**Request Schema:**
```json
{
  "queryType": "calculation|optimization|comparison|benchmarking",
  "layer": 0-3,
  "capability": "string",
  "parameters": {},
  "context": {"lfDataVersion": "Q3_FY25"}
}
```

**Response Schema:**
```json
{
  "queryId": "uuid",
  "status": "success|error",
  "result": {},
  "provenance": {
    "inputDimensions": [],
    "calculationMethod": "",
    "lfSource": "",
    "timestamp": "",
    "dataVersion": ""
  },
  "dataLineage": {
    "layer0_inputs": {},
    "layer1_intermediates": [],
    "layer2_dependencies": []
  },
  "executionTime_ms": 0
}
```

## Sample Projects

### 1. Sara City (P_CHAKAN_001)
- **Units:** 100 (30 × 1BHK, 50 × 2BHK, 20 × 3BHK)
- **Total Area:** 70,000 sqft
- **Project Cost:** ₹50 Cr
- **Expected IRR:** 24%
- **Developer:** Sara Builders & Developers (APF: 0.92)

### 2. Pradnyesh Shriniwas (P_CHAKAN_002)
- **Units:** 80 (40 × 1BHK, 30 × 2BHK, 10 × 3BHK)
- **Total Area:** 55,000 sqft
- **Project Cost:** ₹40 Cr
- **Expected IRR:** 22%
- **Developer:** JJ Mauli Developers (APF: 0.85)

### 3. Sara Nilaay (P_CHAKAN_003)
- **Units:** 120 (20 × 1BHK, 70 × 2BHK, 30 × 3BHK)
- **Total Area:** 90,000 sqft
- **Project Cost:** ₹65 Cr
- **Expected IRR:** 26%
- **Developer:** Sara Builders & Developers (APF: 0.92)

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_calculators/test_layer2.py -v
```

**Test Coverage Targets:**
- Calculator accuracy: ±2% tolerance for financial metrics
- API integration: All endpoints tested
- End-to-end: 3 main use cases validated

## Project Structure

```
liases-foras/
├── app/                           # Backend application
│   ├── api/                       # FastAPI endpoints
│   │   ├── mcp_info.py           # GET /api/mcp/info
│   │   └── mcp_query.py          # POST /api/mcp/query
│   ├── calculators/               # Layer calculators
│   │   ├── layer0.py             # Raw dimensions handler
│   │   ├── layer1.py             # Derived metrics (PSF, ASP, etc.)
│   │   ├── layer2.py             # Financial metrics (NPV, IRR)
│   │   └── layer3.py             # Optimization & scenarios
│   ├── models/                    # Pydantic models
│   │   ├── domain.py             # Project, Unit, FinancialProjection
│   │   ├── requests.py           # API request models
│   │   ├── responses.py          # API response models
│   │   └── enums.py              # Enums (Layer, QueryType, etc.)
│   ├── services/                  # Business logic
│   │   ├── data_service.py       # Data management
│   │   └── query_router.py       # Query routing
│   ├── config.py                  # Configuration
│   └── main.py                    # FastAPI app
├── frontend/                      # Streamlit chat interface
│   └── streamlit_app.py
├── data/                          # Sample data
│   ├── chakan_market_data.json
│   ├── sample_projects.json
│   └── lf_mock_responses/        # LF Pillar 1-5 mock data
├── scripts/                       # Utility scripts
│   ├── scrape_dashboard.py
│   └── generate_mock_data.py
├── tests/                         # Test suite
├── requirements.txt
├── .env.example
├── CLAUDE.md                      # Claude Code guidance
├── PRD-v2-API-MCP-Implementation.md
└── README.md
```

## LF Data Integration

### 5 Data Pillars

1. **Pillar 1: Market Intelligence** - Prices, absorption, trends
2. **Pillar 2: Product Performance** - Typology, efficiency
3. **Pillar 3: Developer Performance** - APF, builder ratings, OPPS
4. **Pillar 4: Financial** - IRR/ROI, feasibility, benchmarks
5. **Pillar 5: Sales/Operations** - Sales velocity, distribution

## Development

### Add New Calculator

1. Create calculator in `app/calculators/`
2. Add capability to `app/api/mcp_info.py`
3. Add routing logic to `app/services/query_router.py`
4. Write tests in `tests/test_calculators/`

### Add New Endpoint

1. Create router in `app/api/`
2. Include router in `app/main.py`
3. Add tests in `tests/test_api/`

## Troubleshooting

### API Connection Error in Streamlit

**Problem:** "API connection error: Connection refused"

**Solution:**
```bash
# Make sure FastAPI is running
uvicorn app.main:app --reload --port 8000

# Check if server is responding
curl http://localhost:8000/health
```

### Import Errors

**Problem:** "ModuleNotFoundError: No module named 'app'"

**Solution:**
```bash
# Run from project root directory
cd /Users/tusharsikand/Documents/Projects/liases-foras

# Make sure you're in virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Data Not Loading

**Problem:** "Warning: data/sample_projects.json not found"

**Solution:**
```bash
# Generate sample data
python scripts/scrape_dashboard.py
python scripts/generate_mock_data.py

# Verify files exist
ls -la data/
```

## Roadmap

### Phase 1: MVP (Complete ✅)
- ✅ 4-layer calculator implementation
- ✅ MCP API endpoints
- ✅ Streamlit chat interface
- ✅ Sample data generation

### Phase 2: Enhancement (Planned)
- [ ] Neo4j graph database integration
- [ ] Real LF API integration
- [ ] Claude AI integration via Anthropic SDK
- [ ] Comprehensive test suite

### Phase 3: Production (Planned)
- [ ] Authentication & user management
- [ ] Data versioning & audit trail
- [ ] Performance optimization
- [ ] Deployment (Docker, K8s)

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## License

This project is proprietary to Liases Foras × Sirrus.AI.

## Contact

For questions or support, please refer to the PRD document or CLAUDE.md for implementation details.

---

🏢 **Liases Foras × Sirrus.AI** | Four-Layer Dimensional Knowledge Graph | v2.0
