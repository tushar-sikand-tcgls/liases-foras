# Dynamic Query Handler - Integration Guide

## Problem Solved

**Before:** Hard-coded responses (e.g., returning IRR for "Calculate average project size")
**After:** Dynamic calculation from Neo4j graph data

## How It Works

```
User Query: "Calculate the average of project size"
     ↓
Parse Intent: aggregation=avg, dimension=U (Units)
     ↓
Generate Cypher: MATCH (p:Project) RETURN avg(p.totalUnits), collect(p.totalUnits)
     ↓
Execute on Graph: Fetch actual project data
     ↓
Calculate Result: (120 + 90 + 60) / 3 = 90.0 Units
     ↓
Format Response: Include formula, breakdown, provenance
```

## API Usage

**Endpoint:** `POST /api/query/calculate`

**Request:**
```json
{
  "query": "Calculate the average of project size"
}
```

**Response:**
```json
{
  "status": "success",
  "layer": 0,
  "dimension": "U",
  "aggregation": "avg",
  "result": {
    "value": 90.0,
    "unit": "Units",
    "text": "90.0 Units"
  },
  "calculation": {
    "formula": "X = Σ U / 3",
    "breakdown": [
      {"projectName": "Project_1", "value": 120, "index": 1},
      {"projectName": "Project_2", "value": 90, "index": 2},
      {"projectName": "Project_3", "value": 60, "index": 3}
    ],
    "projectCount": 3
  },
  "provenance": {
    "dataSource": "Liases Foras",
    "layer": "Layer 0",
    "cypherQuery": "MATCH (p:Project) RETURN avg(p.totalUnits) AS result...",
    "originalQuery": "Calculate the average of project size"
  }
}
```

## Supported Queries

### Layer 0 Dimensions (Raw Data)

| Query | Dimension | Example |
|-------|-----------|---------|
| "Calculate average project size" | U (Units) | 90.0 Units |
| "What is the total area?" | L² (Area) | 180000 sqft |
| "Find the maximum duration" | T (Time) | 36 months |
| "What is total revenue?" | CF (Cash Flow) | 12000000000 INR |

### Aggregation Types

- **Average/Mean:** "Calculate average of project size"
- **Sum/Total:** "What is the total revenue?"
- **Count:** "How many projects?"
- **Min/Minimum:** "Find the minimum area"
- **Max/Maximum:** "What is the maximum duration?"

### Query Variations (All Work)

```
"Calculate the average of project size"
"What is the average project size?"
"Find the mean units"
"Calculate average units"
"Get avg project size"
```

## Integration Steps

### 1. Add to FastAPI App

```python
# app/main.py
from fastapi import FastAPI
from app.services.query_handler import router as query_router

app = FastAPI()
app.include_router(query_router)
```

### 2. Configure Neo4j Connection

```python
# app/db/neo4j.py
from neo4j import GraphDatabase
import os

def get_neo4j_driver():
    return GraphDatabase.driver(
        os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
        auth=(os.getenv('NEO4J_USER', 'neo4j'),
              os.getenv('NEO4J_PASSWORD', 'password'))
    )
```

### 3. Test Query

```bash
curl -X POST http://localhost:8000/api/query/calculate \
  -H "Content-Type: application/json" \
  -d '{"query": "Calculate the average of project size"}'
```

## Excel Spreadsheet Compliance

✓ **Layer:** 0 (Raw dimensions)
✓ **Formula:** X = Σ Project_Size/X
✓ **Breakdown:** Shows individual project values
✓ **Expected Answer:** Matches calculated result (90.0 Units)
✓ **Provenance:** Includes data source and calculation method

## Extending to Other Layers

**Layer 1 (Derived Metrics):**
```python
self.dimension_map.update({
    'psf': {'symbol': 'PSF', 'field': 'value', 'unit': 'INR/sqft', 'layer': 1},
    'absorption rate': {'symbol': 'AR', 'field': 'value', 'unit': '%/month', 'layer': 1}
})
```

Query: "Calculate average PSF in Pune"
→ Match Layer 1 PSF nodes, filter by location, aggregate

**Layer 2 (Financial):**
```python
'irr': {'symbol': 'IRR', 'field': 'value', 'unit': '%', 'layer': 2},
'npv': {'symbol': 'NPV', 'field': 'value', 'unit': 'INR', 'layer': 2}
```

Query: "What is the average IRR?"
→ Match Layer 2 IRR nodes, calculate average

## Next Steps

1. ✅ Layer 0 aggregations working
2. ⚠️ Add Layer 1 metric queries
3. ⚠️ Add Layer 2 financial queries
4. ⚠️ Add cross-source enrichment (Google + Gov data)
5. ⚠️ Add MCP integration for Claude
