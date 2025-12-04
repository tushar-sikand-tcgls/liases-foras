# Quick Start Guide - New LLM-Orchestrated Architecture

## ✅ Startup Verification

All systems operational! Run this to verify:
```bash
python test_startup.py
```

Expected output:
- ✓ Function Registry: **20 functions** registered
- ✓ Gemini Service: Initialized with API key
- ✓ Chat History: Auto-compacting at 8000 tokens
- ✓ Orchestrator: Coordinating all services
- ✓ Main Application: **7 new endpoints** added

---

## 🚀 Starting the Server

```bash
# Option 1: Using api_server.py
python api_server.py

# Option 2: Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at: `http://localhost:8000`

---

## 📡 New API Endpoints

### Primary Endpoint (Recommended)

#### **POST `/api/qa/question/v2`** - Natural Language Query with LLM Orchestration

**Example 1: IRR Calculation**
```bash
curl -X POST http://localhost:8000/api/qa/question/v2 \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Calculate IRR for project 1 and explain if it's good",
    "project_id": "1"
  }'
```

**Example 2: "Why" Question (GraphRAG + Insights)**
```bash
curl -X POST http://localhost:8000/api/qa/question/v2 \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Why is absorption rate low for Sara City?",
    "project_id": "1",
    "location_context": {
      "region": "Chakan",
      "city": "Pune"
    }
  }'
```

**Example 3: Project Comparison**
```bash
curl -X POST http://localhost:8000/api/qa/question/v2 \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Compare top 3 projects by PSF in Chakan"
  }'
```

**Example 4: Market Opportunity**
```bash
curl -X POST http://localhost:8000/api/qa/question/v2 \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the market opportunity score for Chakan?",
    "location_context": {
      "region": "Chakan",
      "city": "Pune"
    }
  }'
```

---

### Alternative Endpoint (MCP Protocol)

#### **POST `/api/mcp/query/natural`**

Same functionality as `/api/qa/question/v2` but follows MCP response format.

```bash
curl -X POST http://localhost:8000/api/mcp/query/natural \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Calculate NPV for project 1 with 12% discount rate",
    "project_id": 1
  }'
```

---

### Session Management

#### **GET `/api/mcp/sessions`** - List All Sessions
```bash
curl http://localhost:8000/api/mcp/sessions
```

#### **GET `/api/mcp/session/{session_id}`** - Get Session Summary
```bash
curl http://localhost:8000/api/mcp/session/session_abc123
```

#### **DELETE `/api/mcp/session/{session_id}`** - Delete Session
```bash
curl -X DELETE http://localhost:8000/api/mcp/session/session_abc123
```

#### **POST `/api/mcp/session/{session_id}/clear`** - Clear Session History
```bash
curl -X POST http://localhost:8000/api/mcp/session/session_abc123/clear
```

---

### Function Discovery

#### **GET `/api/mcp/functions`** - List Available Functions
```bash
curl http://localhost:8000/api/mcp/functions
```

Returns:
```json
{
  "total_functions": 20,
  "by_layer": {
    "layer0": 4,
    "layer1": 5,
    "layer2": 6,
    "layer3": 2,
    "layer4": 3
  },
  "by_category": {
    "calculator": 9,
    "graphrag": 3,
    "data_retrieval": 5,
    "context": 1,
    "optimizer": 2
  },
  "function_names": [
    "get_project_dimensions",
    "calculate_psf",
    "calculate_irr",
    "optimize_product_mix",
    "semantic_search_market_insights",
    ...
  ]
}
```

---

## 🧪 Testing Scenarios

### 1. Calculation Query (Deterministic)
```bash
# Query
"Calculate IRR for cash flows [10, 15, 20, 25] with initial investment 50"

# Expected Behavior
- LLM calls: calculate_irr(initial_investment=50, annual_cash_flows=[10,15,20,25])
- Returns: IRR value (e.g., 18.5%)
- Commentary: "This IRR of 18.5% is within typical real estate range..."
```

### 2. Insight Query (GraphRAG)
```bash
# Query
"Why is PSF higher in Hinjewadi compared to Chakan?"

# Expected Behavior
- LLM calls: get_projects_by_location("Hinjewadi")
- LLM calls: get_projects_by_location("Chakan")
- LLM calls: semantic_search_market_insights("Hinjewadi vs Chakan")
- Returns: Comparative analysis with market intelligence from vector DB
```

### 3. Comparison Query
```bash
# Query
"Compare projects 1, 2, 3 by PSF, units, and land area"

# Expected Behavior
- LLM calls: compare_projects(project_ids=[1,2,3], metrics=["currentPricePSF","totalUnits","landAreaAcres"])
- Returns: Structured comparison table + insights
```

### 4. Optimization Query
```bash
# Query
"Optimize product mix for 100 units with total land 50000 sqft"

# Expected Behavior
- LLM calls: optimize_product_mix(total_units=100, total_land_area_sqft=50000, ...)
- Returns: Optimal 1BHK/2BHK/3BHK mix with IRR for Base/Optimistic/Conservative scenarios
```

---

## 🔍 Response Format

All responses follow this structure:

```json
{
  "status": "success",
  "answer": {
    "response": "**Calculation:**\nIRR: 24.5%\nNPV: ₹12.5 Cr\n\n**Analysis:**\nThis IRR is excellent...\n\n**Insights:**\nDriven by...\n\n**Recommendations:**\n1. ...\n2. ...",
    "function_calls": [
      {
        "name": "calculate_irr",
        "arguments": {
          "initial_investment": 50000000,
          "annual_cash_flows": [12500000, 15000000, 17500000, 20000000, 22500000]
        }
      }
    ],
    "understanding": {
      "query_type": "calculation",
      "session_id": "session_abc123"
    },
    "metadata": {
      "timestamp": "2025-12-02T10:30:00Z",
      "total_turns": 1,
      "session_tokens": 234
    }
  }
}
```

---

## 📊 Function Registry (20 Functions)

### Layer 0: Raw Dimensions (4 functions)
- `get_project_dimensions(project_id)` - Fetch U, L², T, CF values
- `get_project_by_name(project_name)` - Find project by name
- `get_projects_by_location(location)` - Filter by location
- `compare_projects(project_ids, metrics)` - Compare projects

### Layer 1: Derived Metrics (5 functions)
- `calculate_psf(total_revenue, saleable_area)` - Price per sqft
- `calculate_asp(total_revenue, total_units)` - Average selling price
- `calculate_absorption_rate(units_sold, total_units, months_elapsed)` - Absorption rate
- `calculate_sales_velocity(units_sold, months_elapsed)` - Sales velocity
- `calculate_density(total_units, land_area)` - Project density

### Layer 2: Financial Metrics (6 functions)
- `calculate_npv(initial_investment, annual_cash_flows, discount_rate)` - Net present value
- `calculate_irr(initial_investment, annual_cash_flows)` - Internal rate of return
- `calculate_payback_period(initial_investment, annual_cash_flows)` - Payback period
- `calculate_statistics(metric_name, location)` - Statistical analysis
- `get_top_n_projects(metric_name, n, location, order)` - Ranking/sorting

### Layer 3: Optimization (2 functions)
- `optimize_product_mix(total_units, total_land_area_sqft, ...)` - Product mix optimization
- `market_opportunity_scoring(location, unit_types)` - OPPS scoring

### Layer 4: GraphRAG (3 functions)
- `semantic_search_market_insights(query, city, n_results)` - Vector DB search
- `get_city_overview(city)` - City market summary
- `get_locality_insights(locality, city)` - Micro-market insights

### Context APIs (1 function)
- `get_location_context(location_name, city)` - Google APIs (8 APIs: Maps, Places, Distance Matrix, Elevation, Static Map, Street View, Air Quality, Custom Search)

---

## 🔧 Configuration

### Environment Variables

Required in `.env` file:

```bash
# Gemini API (LLM Orchestration)
GOOGLE_API_KEY=AIzaSyAG33P0W7MaScsX7VJxBy-dPJiiIbZ_XhM

# Google Maps APIs (Context Service)
GOOGLE_MAPS_API_KEY=your_key_here
GOOGLE_SEARCH_API_KEY=your_key_here
GOOGLE_SEARCH_CX=your_cx_here

# Optional: Government Data (Future)
GOV_IN_API_KEY=to_be_added
GOV_IN_API_BASE_URL=to_be_added
```

---

## 💡 Tips for Using the New System

### 1. **Be Specific in Queries**
- ✅ "Calculate IRR for project 1"
- ✅ "Why is absorption rate low for Sara City?"
- ❌ "Tell me about projects" (too vague)

### 2. **Provide Context When Needed**
- Include `project_id` for project-specific queries
- Include `location_context` for location-based insights

### 3. **Use Natural Language**
- The LLM understands variations:
  - "Calculate IRR" = "What's the IRR?" = "Show me internal rate of return"
  - "Compare projects" = "Which project is better?" = "Show me top 3"

### 4. **Leverage Chat History**
- Sessions maintain context automatically
- Ask follow-up questions without repeating context
- History auto-compacts at 8000 tokens

### 5. **Trust the Function Calling**
- LLM automatically selects appropriate functions
- No need to manually specify which calculation to use
- System is transparent: see all function calls in response

---

## 🐛 Troubleshooting

### Issue: Import Error
```
ImportError: cannot import name 'FunctionDeclaration'
```
**Fix:** Upgrade google-generativeai
```bash
pip install --upgrade google-generativeai
```

### Issue: API Key Error
```
ValueError: Gemini API key not provided
```
**Fix:** Set environment variable
```bash
export GOOGLE_API_KEY=AIzaSyAG33P0W7MaScsX7VJxBy-dPJiiIbZ_XhM
# Or add to .env file
```

### Issue: Session Not Found
```
{"error": "Session not found"}
```
**Fix:** Sessions are in-memory (lost on restart). Create new session by sending query.

---

## 📚 Additional Resources

- **Architecture Summary**: `ARCHITECTURE-RESTRUCTURE-SUMMARY.md`
- **Original PRD**: `PRD-v2-API-MCP-Implementation.md`
- **Project Instructions**: `CLAUDE.md`

---

## 🎯 Next Steps

1. **Test all 20 functions** via `/api/mcp/functions`
2. **Run end-to-end scenarios** (IRR calculation, "why" question, comparison)
3. **Monitor performance** (response time < 3s for enriched insights)
4. **Implement persistent sessions** (Redis/PostgreSQL for production)
5. **Add Government data integration** (RERA, Smart Cities, Census)

---

**Ready to Query! 🚀**

The system is fully operational and ready to handle natural language queries with LLM orchestration, deterministic calculations, and GraphRAG-powered insights.
