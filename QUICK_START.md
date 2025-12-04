# Quick Start Guide

## Installation & Testing

### 1. Start the Server

```bash
cd /Users/tusharsikand/Documents/Projects/liases-foras
uvicorn app.main:app --reload
```

### 2. Test Basic Query

```bash
curl -X POST http://localhost:8000/api/query/unified \
  -H "Content-Type: application/json" \
  -d '{"query": "Calculate the average of project size"}'
```

**Expected Response:**
```json
{
  "status": "success",
  "result": {
    "value": 90.0,
    "unit": "Units",
    "text": "90.0 Units"
  },
  "calculation": {
    "formula": "X = Σ U / 3",
    "breakdown": [...]
  }
}
```

### 3. Test Dynamic Layer Creation

```bash
curl -X POST http://localhost:8000/api/query/unified \
  -d '{"query": "What is the cost per month?"}'
```

**Expected Response:**
```json
{
  "status": "success",
  "dynamic_dimension": {
    "symbol": "CF/T",
    "name": "Cash Flow Per Time",
    "unit": "INR/month",
    "layer": 1,
    "created_on_the_fly": true,
    "note": "This dimension was created dynamically!"
  },
  "result": {
    "value": 236111111.1,
    "unit": "INR/month"
  }
}
```

### 4. Test SQL-Like Query

```bash
curl -X POST http://localhost:8000/api/query/unified \
  -d '{"query": "Top 5 projects by revenue"}'
```

### 5. Test Statistical Operations

```bash
curl -X POST http://localhost:8000/api/query/unified \
  -d '{"query": "Show me the median and standard deviation of project sizes"}'
```

---

## Quick Test Queries

### Basic Math
- "Calculate average project size"
- "What is total revenue?"
- "Sum of all areas"

### Dynamic Dimensions (Created On-The-Fly!)
- "What is cost per month?" → CF/T
- "Show me unit density" → U/L²
- "Calculate area per time" → L²/T
- "What is time per unit?" → T/U

### Statistical
- "Calculate median area"
- "Show me standard deviation of revenue"
- "Get quartiles for project durations"

### SQL-Like
- "Top 5 projects by revenue"
- "Projects with units > 100"
- "Average PSF by city"
- "Sort projects by area descending"

---

## Documentation Index

| File | Description |
|------|-------------|
| **COMPLETE_SOLUTION_SUMMARY.md** | Full overview and architecture |
| **DYNAMIC_LAYER_CREATION.md** | How dynamic layer creation works |
| **DIMENSIONAL_ANALYSIS_RULES.md** | Rules for operations and layers |
| **COMPREHENSIVE_QUERY_EXAMPLES.md** | 50+ query examples |
| **QUICK_START.md** | This file |

---

## Key Files

| File | Purpose |
|------|---------|
| `app/services/dimensional_calculator.py` | Math/stat/SQL operations |
| `app/services/unified_query_processor.py` | LLM + dynamic layer creation |
| `app/main.py` | FastAPI server |

---

## API Endpoint

**URL:** `POST /api/query/unified`

**Request:**
```json
{
  "query": "Your natural language query"
}
```

**Response:**
```json
{
  "status": "success",
  "understanding": {...},
  "data_strategy": {...},
  "result": {...},
  "dynamic_dimension": {...},
  "provenance": {...}
}
```

---

## Troubleshooting

**Neo4j not connected:**
- Check NEO4J_URI in environment
- Ensure Neo4j server is running

**LLM errors:**
- Check GEMINI_API_KEY is set
- Verify API key is valid

**Module not found:**
- Run: `pip install google-generativeai neo4j`

---

## Status

✅ **Ready to use!**

- Layer 0 queries working
- Dynamic Layer 1 creation working
- Statistical operations working
- SQL-like queries working
- All operations supported
