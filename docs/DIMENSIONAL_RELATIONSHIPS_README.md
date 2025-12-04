# Dimensional Relationships Implementation

## Overview

This implementation transforms the Neo4j L1 layer to use **explicit dimensional relationships** between L1 nodes (Projects, Unit Types, Quarterly Summaries) and L0 dimension nodes (U, L², T, C).

## Key Features

### 1. **Nested Attribute Structure**

Each L1 attribute is stored with three properties:
```json
{
  "totalSupplyUnits": {
    "value": 1109,
    "unit": "count",
    "dimension": "U"
  },
  "currentPricePSF": {
    "value": 3996,
    "unit": "INR/sqft",
    "dimension": "C/L²"
  }
}
```

### 2. **Dimensional Relationships**

Based on the dimensional formula, specific relationships are created:

| Dimension Formula | Relationship Type | Example |
|-------------------|-------------------|---------|
| `U`, `T`, `L²`, `C` | **IS** | `totalSupplyUnits` → IS → U |
| `C/L²`, `L²/U`, `C/T` | **NUMERATOR**, **DENOMINATOR** | `currentPricePSF` → NUMERATOR → C, DENOMINATOR → L² |
| `1/T`, `Fraction/T` | **INVERSE_OF** | `monthlySalesVelocity` → INVERSE_OF → T |
| `None`, `Dimensionless` | (No relationships) | `reraRegistered` (no dimensional relationship) |

### 3. **Dimension Parser Utility**

The `dimension_parser.py` module provides:
- Automatic parsing of dimensional formulas
- Relationship generation
- Human-readable dimension summaries

```python
from dimension_parser import DimensionParser

parser = DimensionParser()

# Parse simple dimension
parser.parse_dimension("U")
# → [{"type": "IS", "target": "U"}]

# Parse composite dimension
parser.parse_dimension("C/L²")
# → [
#     {"type": "NUMERATOR", "target": "C"},
#     {"type": "DENOMINATOR", "target": "L²"}
#   ]

# Get human-readable summary
parser.get_dimension_summary("C/L²")
# → "C (Numerator) / L² (Denominator)"
```

## Files Created

### 1. **Dimension Parser**
- **Path**: `scripts/dimension_parser.py`
- **Purpose**: Parse dimensional formulas and generate relationship definitions
- **Features**:
  - Handles simple dimensions (U, T, L², C)
  - Handles composite dimensions (C/L², L²/U, C/T)
  - Handles inverse dimensions (1/T)
  - Generates Cypher queries for relationship creation

### 2. **V4 Neo4j Loader**
- **Path**: `scripts/v4_load_l1_with_dimensional_rels.py`
- **Purpose**: Load L1 data with dimensional relationships
- **Features**:
  - Preserves nested JSON structure
  - Creates flat properties for easy querying
  - Generates dimensional relationships automatically
  - Provides comprehensive loading statistics

### 3. **Query Engine**
- **Path**: `scripts/query_dimensional_relationships.py`
- **Purpose**: Demonstrate querying dimensional relationships
- **Features**:
  - Project dimensional profile
  - Find attributes by dimension formula
  - Compare projects by dimension
  - Get dimensional lineage

### 4. **Documentation**
- **Path**: `docs/neo4j_dimensional_relationships_guide.md`
- **Purpose**: Comprehensive guide with Cypher queries
- **Includes**:
  - 10+ sample Cypher queries
  - Visualization queries
  - Data quality checks
  - Expected results and statistics

## Usage

### Load Data with Dimensional Relationships

```bash
# Ensure Neo4j is running and L0 dimensions are created
python scripts/v4_load_l1_with_dimensional_rels.py
```

**Expected Output**:
```
✓ Loaded 10 Project_L1 nodes
✓ Created 715 dimensional relationships
✓ Loaded 4 UnitType_L1 nodes
✓ Created 104 dimensional relationships
✓ Loaded 14 QuarterlySummary_L1 nodes
✓ Created 735 dimensional relationships

Total HAS_DIMENSION relationships: 1,554
```

### Query Dimensional Relationships

```bash
# Run demo queries
python scripts/query_dimensional_relationships.py
```

### Neo4j Browser Queries

Open Neo4j Browser at http://localhost:7474 and run:

```cypher
// Visualize Sara City project with dimensional relationships
MATCH (p:Project_L1 {projectName: 'Sara City'})-[r:HAS_DIMENSION]->(d:Dimension_L0)
RETURN p, r, d
```

```cypher
// Find all price attributes (C/L²)
MATCH (n)-[r1:HAS_DIMENSION {dimensionType: 'NUMERATOR'}]->(c:Dimension_L0 {name: 'C'})
MATCH (n)-[r2:HAS_DIMENSION {dimensionType: 'DENOMINATOR'}]->(l:Dimension_L0 {name: 'L²'})
WHERE r1.attribute = r2.attribute
RETURN DISTINCT
  r1.attribute as priceAttribute,
  n[r1.attribute] as value,
  n[r1.attribute + '_unit'] as unit
LIMIT 20
```

## Data Model

### Neo4j Schema

```
(Project_L1)
  ├─ properties:
  │    ├─ projectId
  │    ├─ projectName
  │    ├─ developerName
  │    ├─ location
  │    ├─ totalSupplyUnits (value)
  │    ├─ totalSupplyUnits_dimension
  │    ├─ totalSupplyUnits_unit
  │    ├─ totalSupplyUnits_json
  │    └─ ... (other attributes)
  │
  └─ relationships:
       ├─ [:HAS_DIMENSION {attribute: "totalSupplyUnits", dimensionType: "IS"}]->(U)
       ├─ [:HAS_DIMENSION {attribute: "currentPricePSF", dimensionType: "NUMERATOR"}]->(C)
       ├─ [:HAS_DIMENSION {attribute: "currentPricePSF", dimensionType: "DENOMINATOR"}]->(L²)
       └─ ...

(Dimension_L0)
  ├─ name: "U" | "L²" | "T" | "C"
  ├─ full_name: "Units" | "Space" | "Time" | "Cash Flow"
  ├─ description
  ├─ unit
  ├─ analogy
  └─ examples
```

### Relationship Metadata

Each `HAS_DIMENSION` relationship contains:
- **attribute**: The L1 attribute name (e.g., "currentPricePSF")
- **dimensionType**: The relationship type ("IS", "NUMERATOR", "DENOMINATOR", "INVERSE_OF")
- **dimension**: The original dimension formula (e.g., "C/L²")
- **createdAt**: Timestamp of relationship creation

## Statistics

### Current Database

- **L0 Dimensions**: 4 (U, L², T, C)
- **Projects (L1)**: 10
- **Unit Types (L1)**: 4
- **Quarterly Summaries (L1)**: 14
- **Total Dimensional Relationships**: 1,554

### Relationship Distribution

| Type | Count | Percentage |
|------|-------|------------|
| IS | 1,125 | 72% |
| DENOMINATOR | 187 | 12% |
| NUMERATOR | 187 | 12% |
| INVERSE_OF | 55 | 4% |

### Dimension Usage

| Dimension | Relationships | Description |
|-----------|---------------|-------------|
| U (Units) | 621 | Most used dimension (housing units, counts) |
| L² (Space) | 563 | Second most used (area, size) |
| C (Cash Flow) | 193 | Financial metrics (revenue, cost, price) |
| T (Time) | 177 | Temporal metrics (dates, velocity) |

## Benefits

### 1. **Explicit Semantic Relationships**
Instead of storing dimension as a string property, relationships explicitly connect L1 data to L0 dimensions, making the knowledge graph more semantic and queryable.

### 2. **Dimensional Analysis**
Queries can now traverse dimensional relationships to:
- Find all attributes of a specific dimension
- Compare projects by dimensional categories
- Validate dimensional consistency
- Build dimensional lineage

### 3. **Foundation for Layer 2**
Layer 2 calculators can use these relationships to:
- Discover required inputs by traversing dimensions
- Validate calculation dependencies
- Ensure dimensional correctness

### 4. **Provenance Tracking**
Each relationship includes metadata about:
- Which attribute it represents
- What type of dimensional relationship it is
- When it was created

## Next Steps

### Phase 1: Layer 2 Implementation ✅
Use dimensional relationships to build Layer 2 calculators:
- NPV calculator (discovers required C and T dimensions)
- IRR calculator (validates cash flow dimensions)
- Sensitivity analysis (uses dimensional constraints)

### Phase 2: Dimensional Validation
Create validators that:
- Check dimensional consistency
- Verify calculation formulas match dimensional algebra
- Ensure all required dimensions are present

### Phase 3: Query Optimization
Use dimensional indexes to:
- Speed up queries by dimension
- Pre-compute dimensional aggregations
- Cache frequently accessed dimensional paths

## Comparison: Old vs New

### Old Approach (V3)
```cypher
// Generic relationship
(Project_L1)-[:USES_DIMENSION]->(Dimension_L0)

// Properties were flat
{
  "currentPricePSF": 3996,
  "currentPricePSF_dimension": "C/L²",
  "currentPricePSF_unit": "INR/sqft"
}
```

**Issues**:
- No semantic meaning in relationships
- Cannot query by relationship type
- Dimension is just a string property

### New Approach (V4)
```cypher
// Specific relationships with metadata
(Project_L1)-[:HAS_DIMENSION {
  attribute: "currentPricePSF",
  dimensionType: "NUMERATOR",
  dimension: "C/L²"
}]->(C)

(Project_L1)-[:HAS_DIMENSION {
  attribute: "currentPricePSF",
  dimensionType: "DENOMINATOR",
  dimension: "C/L²"
}]->(L²)

// Properties include nested structure + flat properties
{
  "currentPricePSF": 3996,
  "currentPricePSF_dimension": "C/L²",
  "currentPricePSF_unit": "INR/sqft",
  "currentPricePSF_json": "{\"value\": 3996, \"unit\": \"INR/sqft\", \"dimension\": \"C/L²\"}"
}
```

**Benefits**:
- Semantic relationships (NUMERATOR, DENOMINATOR, IS, INVERSE_OF)
- Can query by relationship type
- Dimensional formula is preserved in relationships
- Nested JSON structure available for complex queries

## Troubleshooting

### Issue: Duplicate Relationships
**Symptom**: Each attribute has multiple identical relationships
**Cause**: Relationship creation query matches all nodes instead of specific node
**Fix**: Use node-specific identifiers when creating relationships

### Issue: Missing Relationships
**Symptom**: Some attributes don't have dimensional relationships
**Cause**: Dimension parser doesn't recognize the dimensional formula
**Fix**: Add new dimension patterns to `dimension_parser.py`

### Issue: Wrong Dimension Type
**Symptom**: Relationship has incorrect dimensionType
**Cause**: Dimensional formula parsing error
**Fix**: Debug with `dimension_parser.py` test cases

## References

- **Project Documentation**: `CLAUDE.md`
- **Neo4j Guide**: `docs/neo4j_dimensional_relationships_guide.md`
- **PRD**: `PRD-v2-API-MCP-Implementation.md`
- **Original Loader**: `scripts/v3_load_l1_to_neo4j.py`
- **New Loader**: `scripts/v4_load_l1_with_dimensional_rels.py`

## License

Part of the Liases Foras × Sirrus.AI Integration project.

---

**Author**: Claude Code
**Date**: 2025-11-30
**Version**: 4.0.0
