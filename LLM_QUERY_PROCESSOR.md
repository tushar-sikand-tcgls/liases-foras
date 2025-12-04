# LLM-Powered Query Processor

## How It Works

**No Hardcoding!** The LLM analyzes your query and the knowledge graph schema dynamically.

```
User Query: "Calculate the average of project size"
     ↓
LLM receives:
  - Query: "Calculate the average of project size"
  - KG Schema: {layers, dimensions, aggregations}
     ↓
LLM understands:
  - Layer: 0 (Raw Dimensions)
  - Target Attribute: "Project Size"
  - Dimension: U (Units)
  - Aggregation: average
  - Neo4j Field: totalUnits
  - Unit: Units
     ↓
Generate Cypher:
  MATCH (p:Project)
  RETURN avg(p.totalUnits), collect(p.totalUnits), ...
     ↓
Execute on Neo4j
     ↓
Format Response:
  Result: 90.0 Units
  Formula: X = Σ U / 3
  Breakdown: [120, 90, 60]
```

## Key Difference from Previous Approach

### ❌ Old Way (Hardcoded)
```python
if "project size" in query:
    dimension = "U"
    field = "totalUnits"
```

### ✅ New Way (LLM-Powered)
```python
# LLM reads the schema and understands
understanding = llm.analyze(query, kg_schema)
# LLM decides: layer=0, dimension=U, field=totalUnits
```

## Knowledge Graph Schema (Context for LLM)

The LLM receives this as context (not hardcoded rules):

```json
{
  "layers": {
    "0": {
      "dimensions": {
        "U": {
          "symbol": "U",
          "name": "Units",
          "neo4j_field": "totalUnits",
          "unit": "Units",
          "examples": ["project size", "units", "total units"]
        },
        "L²": {
          "symbol": "L²",
          "name": "Area",
          "neo4j_field": "totalSaleableArea",
          "unit": "sqft",
          "examples": ["area", "saleable area"]
        }
      }
    }
  }
}
```

## API Usage

**Endpoint:** `POST /api/query/llm-calculate`

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
  "query": "Calculate the average of project size",
  "understanding": {
    "layer": 0,
    "targetAttribute": "Project Size",
    "dimension": "U",
    "aggregation": "average",
    "description": "Calculate average number of units across all projects"
  },
  "result": {
    "value": 90.0,
    "unit": "Units",
    "text": "90.0 Units"
  },
  "calculation": {
    "formula": "X = Σ U / 3",
    "breakdown": [
      {"projectName": "Project_1", "value": 120},
      {"projectName": "Project_2", "value": 90},
      {"projectName": "Project_3", "value": 60}
    ],
    "projectCount": 3
  },
  "provenance": {
    "dataSource": "Liases Foras",
    "layer": "Layer 0",
    "cypherQuery": "MATCH (p:Project) RETURN avg(p.totalUnits)...",
    "llmModel": "gemini-1.5-flash"
  }
}
```

## Supported Queries (Examples)

The LLM can understand various phrasings:

**Layer 0 (Raw Dimensions):**
- "Calculate the average of project size"
- "What is average project size?"
- "Find mean units"
- "Total area across all projects"
- "What is the maximum duration?"
- "Sum of all revenue"
- "How many projects?"

**Layer 1 (Derived Metrics):**
- "Calculate average PSF"
- "What is the PSF?"
- "Find average selling price"

**Layer 2 (Financial):**
- "What is the average IRR?"
- "Calculate mean NPV"

## Testing

### Start Server
```bash
cd /Users/tusharsikand/Documents/Projects/liases-foras
uvicorn app.main:app --reload
```

### Test with curl
```bash
curl -X POST http://localhost:8000/api/query/llm-calculate \
  -H "Content-Type: application/json" \
  -d '{"query": "Calculate the average of project size"}'
```

### Test with Python
```python
import requests

response = requests.post(
    'http://localhost:8000/api/query/llm-calculate',
    json={'query': 'Calculate the average of project size'}
)

print(response.json())
```

## How LLM Makes Decisions

**LLM Prompt Template:**
```
You are a knowledge graph query analyzer.

SCHEMA: {kg_schema}
USER QUERY: "Calculate the average of project size"

Determine:
1. Layer (0, 1, 2)
2. Target Attribute
3. Dimension (U, L², T, CF)
4. Aggregation (average, sum, count, min, max)
5. Neo4j Field
6. Unit

Return JSON:
{
  "layer": 0,
  "target_attribute": "Project Size",
  "dimension": "U",
  "aggregation": "average",
  "neo4j_field": "totalUnits",
  "unit": "Units"
}
```

The LLM:
1. Reads the schema
2. Sees "project size" maps to U dimension with field "totalUnits"
3. Sees "average" maps to avg aggregation
4. Returns structured understanding
5. System generates Cypher based on this understanding

## Extending to New Dimensions

**To add a new dimension:**

Just update the schema! No code changes needed.

```python
self.kg_schema["layers"]["0"]["dimensions"]["NEW_DIM"] = {
    "symbol": "X",
    "name": "New Metric",
    "neo4j_field": "newField",
    "unit": "units",
    "examples": ["new metric", "something new"]
}
```

The LLM will automatically understand queries about this new dimension!

## Configuration

**Required Environment Variables:**
```bash
GEMINI_API_KEY=your_gemini_api_key
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

## Excel Spreadsheet Compliance

✅ Matches Excel format:
- Layer: 0
- Target Attribute: Project Size
- Unit: Unit (from dimension)
- Description: From LLM understanding
- Formula/Derivation: X = Σ U / 3
- Expected Answer: Calculated dynamically

## Architecture Benefits

1. **No Hardcoding:** Schema is data, not code
2. **Extensible:** Add new dimensions/metrics by updating schema
3. **Flexible:** LLM understands various query phrasings
4. **Transparent:** Response includes LLM understanding + provenance
5. **Excel Compatible:** Matches spreadsheet format exactly
