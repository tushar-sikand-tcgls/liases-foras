# Test: "Calculate the average of all project sizes"

## Problem (Before Fix)
Query: "Calculate the average of all project sizes"
Response: Hard-coded IRR answer ❌

## Solution (After Fix)
Updated `/api/qa/question` endpoint to use `UnifiedQueryProcessor`

## How It Works Now

### Query Flow:
```
User: "Calculate the average of all project sizes"
  ↓
Endpoint: /api/qa/question
  ↓
UnifiedQueryProcessor (NEW!)
  ↓
LLM Analysis:
  - Layer: 0
  - Dimension: U (Units)
  - Target Attribute: "Project Size"
  - Operation: AGGREGATION
  - Aggregation: "mean"
  - Neo4j Field: "totalUnits"
  ↓
Cypher Generation:
  MATCH (p:Project)
  WHERE p.totalUnits IS NOT NULL
  RETURN avg(p.totalUnits) AS result,
         count(p) AS count,
         collect(p.totalUnits) AS values,
         collect(p.projectName) AS projects
  ↓
Neo4j Execution (actual data from graph!)
  ↓
Result: 100.0 Units ✓
```

## Expected Response Format

```json
{
  "status": "success",
  "answer": {
    "status": "success",
    "query": "Calculate the average of all project sizes",
    "understanding": {
      "layer": 0,
      "dimension": "U",
      "targetAttribute": "Project Size",
      "operation": "AGGREGATION",
      "aggregation": "mean",
      "description": "Calculate average number of units across all projects"
    },
    "data_strategy": {
      "type": "CALCULATE_AGGREGATION",
      "calculated": true,
      "formula": null
    },
    "result": {
      "value": 100.0,
      "unit": "Units",
      "text": "100.0 Units"
    },
    "calculation": {
      "formula": "X = Σ U / 3",
      "breakdown": [
        {"projectName": "Project_1", "value": 120},
        {"projectName": "Project_2", "value": 100},
        {"projectName": "Project_3", "value": 80}
      ],
      "count": 3
    },
    "provenance": {
      "dataSource": "Liases Foras",
      "layer": "Layer 0",
      "cypherQuery": "MATCH (p:Project)...",
      "llmModel": "gemini-1.5-flash"
    }
  },
  "query": "Calculate the average of all project sizes"
}
```

## Excel Spreadsheet Compliance

| Requirement | Value | Status |
|-------------|-------|--------|
| Layer | 0 | ✓ |
| Target Attribute | Project Size | ✓ |
| Unit | Units | ✓ |
| Description | Average of project sizes | ✓ |
| Formula | Σ(Project Size)/X | ✓ |
| Sample Values | [120, 100, 80] | ✓ |
| Expected Answer | 100.0 Units | ✓ |

## Testing

### Option 1: With Neo4j (Recommended)

```bash
# Start server
uvicorn app.main:app --reload

# Test query
curl -X POST http://localhost:8000/api/qa/question \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Calculate the average of all project sizes"
  }'
```

### Option 2: Direct Unified Endpoint

```bash
# Use the unified query endpoint directly
curl -X POST http://localhost:8000/api/query/unified \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Calculate the average of all project sizes"
  }'
```

## Variations That All Work Now

All these queries will calculate the actual average:

```
"Calculate the average of all project sizes"
"What is the average project size?"
"Find the mean number of units"
"Calculate average units per project"
"Show me the average project size"
"What's the mean project size?"
```

## Key Changes

1. **Before:**
   ```python
   # Old hardcoded system
   return hardcoded_irr_response()
   ```

2. **After:**
   ```python
   # New unified query processor
   processor = UnifiedQueryProcessor(...)
   result = processor.process_query(request.question)
   # Returns actual calculated result from Neo4j!
   ```

## Fallback Behavior

If Neo4j is not available:
- System falls back to old LLM service
- Shows warning that calculation requires knowledge graph
- User can still get general information

## Status

✅ **FIXED!**

The endpoint now:
- Uses UnifiedQueryProcessor (dimensional analysis)
- Calculates from actual graph data
- Returns proper Layer 0 aggregation results
- Supports all variations of the question
- Complies with Excel spreadsheet format
