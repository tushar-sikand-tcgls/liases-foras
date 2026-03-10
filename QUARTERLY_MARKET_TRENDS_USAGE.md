# Quarterly Market Trends - Usage Guide

## Overview

The Quarterly Sales and Marketable Supply Knowledge Graph is now fully integrated into the system. This guide explains how to use the new functionality across all three tiers of the MCP architecture.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ Tier 1: Gemini Function Calling (LLM Routing)                   │
│ - 7 functions for quarterly market data queries                │
│ - Natural language → Function parameters                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Tier 2: Backend Services (FastAPI + Python)                     │
│ - QuarterlyMarketService: Data management & calculations       │
│ - FunctionRegistry: Gemini-compatible function schemas         │
│ - ChromaDB: 48 documents with semantic search                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Tier 3: Frontend (Streamlit)                                    │
│ - QuarterlyMarketPanel: Interactive visualizations             │
│ - Time-series charts (Sales, Supply, Absorption Rate)          │
│ - YoY/QoQ growth analysis                                       │
│ - Layer 0 dimensional explorer                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Data Details

**Location:** Chakan, Pune, Maharashtra, India
**Source:** Liases Foras Pillar 1 - Market Intelligence
**Layer:** Layer 0 - Raw Dimensions (U, L², T)
**Date Range:** Q2 FY 2014-15 to Q2 FY 2025-26
**Total Quarters:** 45 quarterly data points
**ChromaDB Documents:** 48 (45 quarters + 3 trend summaries)

**Important:** This dataset is **specific to the Chakan micromarket** in Pune. All sales, supply, and absorption metrics represent the Chakan region only, not citywide Pune data.

### Layer 0 Dimensions

- **U (Units)**: Sales units, Supply units
- **L² (Area)**: Sales area (mn sq ft), Supply area (mn sq ft)
- **T (Time)**: Quarterly periods

### Layer 1 Derived Metrics

- **Absorption Rate**: (Sales Units / Supply Units) × 100
- **YoY Growth**: Year-over-year comparison
- **QoQ Growth**: Quarter-over-quarter comparison
- **Summary Statistics**: Min, max, mean, median, total

## Usage

### 1. Frontend (Streamlit)

**Access the Quarterly Market Trends Dashboard:**

1. Start the Streamlit app:
   ```bash
   cd frontend
   streamlit run streamlit_app.py
   ```

2. Select any location

3. Click the **"Market Trends"** button in the top navigation

4. Explore the dashboard:
   - **Summary Statistics**: Overview of all-time market performance
   - **Units (U) Tab**: Sales vs Supply units over time
   - **Area (L²) Tab**: Sales vs Supply area over time
   - **Absorption Rate Tab**: Market absorption rate trends
   - **YoY Growth Tab**: Year-over-year growth analysis
   - **Layer 0 Dimensions**: Detailed breakdown for any selected quarter

5. **Filter by Year Range**: Use the dropdowns to focus on specific time periods

### 2. Backend (Python Service)

**Direct Service Usage:**

```python
from app.services.quarterly_market_service import quarterly_market_service

# Get all quarterly data
all_quarters = quarterly_market_service.get_all_quarters()
print(f"Total quarters: {len(all_quarters)}")

# Get recent 8 quarters (2 years)
recent = quarterly_market_service.get_recent_quarters(n=8)

# Get data by year range
data_2020_2024 = quarterly_market_service.get_quarters_by_year_range(2020, 2024)

# Calculate YoY growth
yoy_sales = quarterly_market_service.calculate_yoy_growth('sales_units')
for item in yoy_sales[-5:]:  # Last 5 quarters
    print(f"{item['quarter']}: {item['yoy_growth_pct']:+.1f}% YoY")

# Calculate QoQ growth
qoq_sales = quarterly_market_service.calculate_qoq_growth('sales_units')

# Get summary statistics
stats = quarterly_market_service.get_summary_statistics('sales_units')
print(f"Average sales: {stats['mean']:.0f} units")
print(f"Peak sales: {stats['max']:,} units")

# Calculate absorption rate trend
absorption = quarterly_market_service.calculate_absorption_rate_trend()
for item in absorption[-5:]:
    print(f"{item['quarter']}: {item['absorption_rate_pct']:.2f}%")
```

### 3. Gemini Function Calling

**Available Functions:**

1. **`get_all_quarterly_data`**
   - Returns all 45 quarters of sales and supply data
   - Example query: "Show me all quarterly sales data"

2. **`get_recent_quarters`**
   - Get N most recent quarters (default: 8 = 2 years)
   - Example query: "What are the last 4 quarters of sales?"

3. **`get_quarters_by_year_range`**
   - Filter data by year range
   - Example query: "Show me data from 2020 to 2024"

4. **`calculate_yoy_growth`**
   - Year-over-year growth for any metric
   - Metrics: `sales_units`, `sales_area_mn_sqft`, `supply_units`, `supply_area_mn_sqft`
   - Example query: "What's the YoY growth in sales?"

5. **`calculate_qoq_growth`**
   - Quarter-over-quarter growth for any metric
   - Example query: "Show me quarterly momentum in supply"

6. **`get_market_summary_statistics`**
   - Summary statistics (min, max, mean, median, total)
   - Example query: "What are the overall market statistics?"

7. **`calculate_absorption_rate_trend`**
   - Absorption rate trend over all quarters
   - Example query: "How is the market absorbing supply?"

**Function Calling Example:**

```python
from app.services.function_registry import get_function_registry

registry = get_function_registry()

# Example 1: Get recent quarters
result = registry.execute_function(
    "get_recent_quarters",
    {"n": 4}
)
print(result)

# Example 2: Calculate YoY growth
result = registry.execute_function(
    "calculate_yoy_growth",
    {"metric": "sales_units"}
)
print(result)

# Example 3: Get absorption rate
result = registry.execute_function(
    "calculate_absorption_rate_trend",
    {}
)
print(result)
```

### 4. ChromaDB Semantic Search

**Query the Vector Database:**

```python
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Connect to ChromaDB
client = chromadb.PersistentClient(
    path="data/chroma_quarterly_db",
    settings=Settings(anonymized_telemetry=False)
)

collection = client.get_collection("quarterly_market_data")

# Load embedding model
embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Semantic search
query = "What was the sales performance in 2023?"
query_embedding = embedding_model.encode(query).tolist()

results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5
)

for i, doc_id in enumerate(results['ids'][0]):
    print(f"{i+1}. {doc_id}")
    print(f"   {results['documents'][0][i][:200]}...")
```

## Example Queries

### Natural Language Queries (via Gemini)

1. **Trend Analysis**
   - "Show me sales trends over the last 5 years"
   - "What's the supply trend in recent quarters?"
   - "How has absorption rate changed over time?"

2. **Growth Analysis**
   - "Calculate YoY growth for sales"
   - "Show me quarter-over-quarter supply growth"
   - "What's the growth rate for the last 8 quarters?"

3. **Statistical Queries**
   - "What's the average quarterly sales?"
   - "What was the peak supply recorded?"
   - "Show me summary statistics for sales area"

4. **Specific Time Periods**
   - "Get data for 2020 to 2024"
   - "Show me Q3 FY 2023-24 data"
   - "What were the most recent 4 quarters?"

5. **Absorption Analysis**
   - "What's the current absorption rate?"
   - "Show me absorption rate trends"
   - "How fast is the market absorbing supply?"

### Direct Python Queries

```python
# Get specific quarter
quarter = quarterly_market_service.get_quarter_by_id("Q3_FY23_24")
print(f"Sales: {quarter['sales_units']:,} units")
print(f"Supply: {quarter['supply_units']:,} units")

# Year range filter
covid_period = quarterly_market_service.get_quarters_by_year_range(2020, 2021)
print(f"COVID period ({2020}-{2021}): {len(covid_period)} quarters")

# Calculate metrics for specific metric
metrics = ['sales_units', 'sales_area_mn_sqft', 'supply_units', 'supply_area_mn_sqft']
for metric in metrics:
    stats = quarterly_market_service.get_summary_statistics(metric)
    print(f"{metric}: Mean={stats['mean']:.2f}, Max={stats['max']:.2f}")
```

## Data Files

- **Source Data**: `data/extracted/quarterly_sales_supply.json`
- **ChromaDB**: `data/chroma_quarterly_db/`
- **Service**: `app/services/quarterly_market_service.py`
- **Functions**: `app/services/function_registry.py` (lines 1109-1329)
- **Frontend**: `frontend/components/quarterly_market_panel.py`

## Rebuilding ChromaDB Index

If you need to rebuild the ChromaDB index:

```bash
python scripts/index_quarterly_data_to_chromadb.py
```

This will:
- Delete existing collection
- Index 45 quarters
- Add 3 trend summaries
- Test semantic search
- Total: 48 documents

## Testing

### Quick Test

```bash
# Test the service directly
python -c "from app.services.quarterly_market_service import quarterly_market_service; print(f'Loaded {len(quarterly_market_service.get_all_quarters())} quarters')"

# Test function registry
python -c "from app.services.function_registry import get_function_registry; reg = get_function_registry(); result = reg.execute_function('get_recent_quarters', {'n': 4}); print(f\"Found {result['count']} quarters\")"
```

### Full Integration Test

```bash
# Start backend (Terminal 1)
cd /path/to/liases-foras
python app/main.py

# Start frontend (Terminal 2)
cd /path/to/liases-foras/frontend
streamlit run streamlit_app.py

# Open browser and click "Market Trends" button
```

## API Endpoints (Future)

To expose via FastAPI, add these endpoints to `app/main.py`:

```python
@app.get("/api/quarterly-market/all")
def get_all_quarterly_data():
    from app.services.quarterly_market_service import quarterly_market_service
    data = quarterly_market_service.get_all_quarters()
    metadata = quarterly_market_service.get_metadata()
    return {"data": data, "metadata": metadata, "count": len(data)}

@app.get("/api/quarterly-market/recent")
def get_recent_quarters(n: int = 8):
    from app.services.quarterly_market_service import quarterly_market_service
    data = quarterly_market_service.get_recent_quarters(n)
    return {"data": data, "count": len(data)}

@app.get("/api/quarterly-market/yoy-growth")
def get_yoy_growth(metric: str = 'sales_units'):
    from app.services.quarterly_market_service import quarterly_market_service
    growth_data = quarterly_market_service.calculate_yoy_growth(metric)
    return {"growth_data": growth_data, "count": len(growth_data), "metric": metric}

@app.get("/api/quarterly-market/absorption-rate")
def get_absorption_rate():
    from app.services.quarterly_market_service import quarterly_market_service
    absorption_data = quarterly_market_service.calculate_absorption_rate_trend()
    return {"absorption_data": absorption_data, "count": len(absorption_data)}
```

## Next Steps

1. **Add More Metrics**: Extend to include developer-specific quarterly trends
2. **Forecasting**: Add Layer 2 forecasting models (ARIMA, Prophet)
3. **Comparative Analysis**: Compare multiple micro-markets
4. **Export Functionality**: Allow CSV/Excel export from frontend
5. **Real-time Updates**: Implement quarterly data refresh mechanism

## Support

For issues or questions:
- Check logs in `scripts/index_quarterly_data_to_chromadb.py` output
- Verify data file exists: `data/extracted/quarterly_sales_supply.json`
- Ensure ChromaDB is initialized: `data/chroma_quarterly_db/`
- Test function registry: Use Quick Test commands above
