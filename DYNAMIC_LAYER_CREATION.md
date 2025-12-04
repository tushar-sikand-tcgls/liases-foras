# Dynamic Layer Creation - On-The-Fly Dimensional Analysis

## Revolutionary Capability

**The system can create NEW metrics that were never predefined!**

Any valid L0÷L0 division creates a Layer 1 metric automatically, with:
- Auto-generated name
- Auto-calculated unit
- Auto-detected layer
- Full provenance tracking

---

## How It Works

### Example 1: "What is the cost per month?"

**User Query:**
```
"What is the cost per month?"
```

**System Analysis:**
```
LLM understands:
  → Asking for: Cost (CF) ÷ Time (T)
  → Dimension: CF/T
  → Fields: totalCost ÷ projectDuration
  → This is NOT predefined! ⚠️

Dynamic Layer Creator activates:
  → Dimension symbol: "CF/T"
  → Auto-generate name: "Cash Flow Per Time"
  → Auto-calculate unit: "INR" ÷ "months" = "INR/month"
  → Layer: 1 (L0÷L0)
  → Create on-the-fly! ✓
```

**Generated Cypher:**
```cypher
MATCH (p:Project)
WHERE p.totalCost IS NOT NULL AND p.projectDuration IS NOT NULL
WITH p,
     p.totalCost / p.projectDuration AS calculated_value,
     'CF/T' AS dimension_symbol,
     'Cash Flow Per Time' AS dimension_name,
     'INR/month' AS dimension_unit
RETURN p.projectName AS project,
       calculated_value AS value,
       avg(calculated_value) AS mean,
       dimension_symbol AS created_dimension
```

**Response:**
```json
{
  "status": "success",
  "query": "What is the cost per month?",
  "understanding": {
    "layer": 1,
    "dimension": "CF/T",
    "operation": "DIVISION"
  },
  "dynamic_dimension": {
    "symbol": "CF/T",
    "name": "Cash Flow Per Time",
    "unit": "INR/month",
    "formula": "totalCost ÷ projectDuration",
    "layer": 1,
    "created_on_the_fly": true,
    "note": "This dimension was created dynamically based on your query!"
  },
  "result": {
    "value": 236111111.1,
    "unit": "INR/month",
    "text": "236111111.1 INR/month"
  }
}
```

---

## All Possible L0÷L0 Combinations

### Matrix of All Valid Layer 1 Dimensions

|  Numerator ↓ \ Denominator → | **U** (Units) | **L²** (Area) | **T** (Time) | **CF** (Cash Flow) |
|-------------------------------|---------------|---------------|--------------|-------------------|
| **U** (Units)                  | 1 (dimensionless) | **U/L²** = Unit Density<br>(units/sqft) | **U/T** = Sales Velocity<br>(units/month) | **U/CF** = Units Per Cost<br>(units/INR) |
| **L²** (Area)                  | **L²/U** = Area Per Unit<br>(sqft/unit) | 1 (dimensionless) | **L²/T** = Area Velocity<br>(sqft/month) | **L²/CF** = Area Per Cost<br>(sqft/INR) |
| **T** (Time)                   | **T/U** = Time Per Unit<br>(months/unit) | **T/L²** = Time Per Area<br>(months/sqft) | 1 (dimensionless) | **T/CF** = Time Per Cost<br>(months/INR) |
| **CF** (Cash Flow)             | **CF/U** = ASP<br>(INR/unit) | **CF/L²** = PSF<br>(INR/sqft) | **CF/T** = Cash Flow Rate<br>(INR/month) | 1 (dimensionless) |

**Total:** 16 combinations, 12 meaningful dimensions (excluding 4 dimensionless 1s)

---

## Predefined vs Dynamic Dimensions

### Predefined Dimensions (Known Metrics)
These are commonly used and have standard names:

| Symbol | Name | Unit | When to Use |
|--------|------|------|-------------|
| CF/L² | Price Per Sqft (PSF) | INR/sqft | Pricing analysis |
| CF/U | Average Selling Price (ASP) | INR/unit | Unit pricing |
| U/T | Sales Velocity | units/month | Sales tracking |
| L²/U | Area Per Unit | sqft/unit | Unit sizing |

### Dynamic Dimensions (Created On-The-Fly)

These are created when you ask for them, even if never defined:

| Symbol | Auto-Generated Name | Unit | Example Query |
|--------|---------------------|------|---------------|
| CF/T | Cash Flow Per Time | INR/month | "What is cost per month?" |
| U/L² | Unit Density | units/sqft | "What is the unit density?" |
| T/U | Time Per Unit | months/unit | "How long to sell each unit?" |
| L²/T | Area Velocity | sqft/month | "Area sold per month?" |

---

## Examples of Dynamic Creation

### Example 2: "Show me unit density"

**Query:** `"Show me unit density"`

**Dynamic Creation:**
```
LLM: "unit density" → U ÷ L²
Auto-generate:
  - Symbol: "U/L²"
  - Name: "Unit Density"
  - Unit: "units/sqft"
  - Layer: 1
```

**Result:**
```json
{
  "dynamic_dimension": {
    "symbol": "U/L²",
    "name": "Unit Density",
    "unit": "units/sqft",
    "created_on_the_fly": true
  },
  "result": {
    "value": 0.00133,
    "unit": "units/sqft",
    "text": "0.00133 units/sqft"
  }
}
```

### Example 3: "Calculate area sold per month"

**Query:** `"Calculate area sold per month"`

**Dynamic Creation:**
```
LLM: "area per month" → L² ÷ T
Auto-generate:
  - Symbol: "L²/T"
  - Name: "Area Per Time"
  - Unit: "sqft/month"
  - Layer: 1
```

### Example 4: "What is time per unit?"

**Query:** `"What is time per unit?"`

**Dynamic Creation:**
```
LLM: "time per unit" → T ÷ U
Auto-generate:
  - Symbol: "T/U"
  - Name: "Time Per Units"
  - Unit: "months/unit"
  - Layer: 1
```

---

## Advanced: Multi-Layer Dynamic Creation

### Layer 2 Creation (Layer 1 ÷ Layer 0)

**Query:** `"What is PSF growth rate?"`

```
LLM understands:
  - PSF is Layer 1 (CF/L²)
  - Growth rate implies ÷ Time (T)
  - Result: (CF/L²) ÷ T = CF/(L²·T)

Dynamic creation:
  - Symbol: "CF/L²T"
  - Name: "Price Per Sqft Growth Rate"
  - Unit: "INR/sqft/month"
  - Layer: 2 (Layer 1 ÷ Layer 0)
```

### Layer 3 Creation (Layer 2 ÷ Layer 1)

**Query:** `"What is IRR per unit area?"`

```
LLM understands:
  - IRR is Layer 2
  - Per unit area means ÷ (L²/U)
  - Result: IRR ÷ (L²/U)

Dynamic creation:
  - Symbol: "IRR/(L²/U)"
  - Name: "IRR Per Unit Area"
  - Unit: "%/( sqft/unit)"
  - Layer: 3 (Layer 2 ÷ Layer 1)
```

---

## Caching and Reuse

Once a dynamic dimension is created, it's cached:

```python
self.kg_schema['layers']['1']['dynamic_metrics']['CF/T'] = {
    'symbol': 'CF/T',
    'name': 'Cash Flow Per Time',
    'unit': 'INR/month',
    'layer': 1,
    'created_dynamically': True,
    'timestamp': '2025-01-28 14:30:00'
}
```

**Future queries:**
- "Show me cost per month" → Reuses cached CF/T
- "What's the monthly cost?" → Reuses cached CF/T
- "Calculate cost rate" → Reuses cached CF/T

---

## API Usage

**Endpoint:** `POST /api/query/unified`

**Test Dynamic Creation:**

```bash
# Example 1: Cost per month (dynamic)
curl -X POST http://localhost:8000/api/query/unified \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the cost per month?"}'

# Example 2: Unit density (dynamic)
curl -X POST http://localhost:8000/api/query/unified \
  -d '{"query": "Show me unit density"}'

# Example 3: Area velocity (dynamic)
curl -X POST http://localhost:8000/api/query/unified \
  -d '{"query": "Calculate area sold per month"}'

# Example 4: Predefined metric (PSF)
curl -X POST http://localhost:8000/api/query/unified \
  -d '{"query": "What is the PSF?"}'
```

---

## Benefits of Dynamic Layer Creation

1. **Infinite Flexibility:** Any valid division creates a metric
2. **No Configuration:** No need to predefine every possible metric
3. **Self-Documenting:** Auto-generates names and units
4. **Extensible:** Works for Layer 2, Layer 3 as well
5. **Consistent:** Follows dimensional analysis rules strictly
6. **Caching:** Reuses once created

---

## Validation Rules

The system automatically validates:

1. **Dimensional Consistency:**
   - Only allows meaningful combinations
   - Prevents nonsensical divisions

2. **Data Availability:**
   - Checks if required Neo4j fields exist
   - Returns error if data missing

3. **Layer Assignment:**
   - L0÷L0 → Layer 1
   - L1÷L0 → Layer 2
   - L2÷L1 → Layer 3

4. **Unit Calculation:**
   - Automatically simplifies units
   - "INR/Units" → "INR/unit"
   - "Units/months" → "units/month"

---

## Limitations

**Division by Zero:**
- System checks for null/zero denominators
- Excludes projects with invalid data

**Unusual Combinations:**
- Some combinations are mathematically valid but business-meaningless
- Example: "Time per area" (months/sqft) - technically valid, but when would you use it?
- System creates it anyway if asked, leaves business interpretation to user

**Multiplication:**
- Currently NOT supported as layer creator (per DIMENSIONAL_ANALYSIS_RULES.md)
- May add if proven useful in real estate context

---

## Summary

**Revolutionary Capability:**
✓ Ask for ANY L0÷L0 division
✓ System creates it on-the-fly
✓ Auto-generates name, unit, layer
✓ Caches for future use
✓ Works for higher layers too (L1÷L0, L2÷L1)

**No hardcoding. No configuration. Pure dimensional analysis.**
