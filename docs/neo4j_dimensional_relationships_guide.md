# Neo4j Dimensional Relationships Guide

## Overview

This guide explains the dimensional relationship model in the Liases Foras knowledge graph, where L1 nodes (Projects, Unit Types, Quarterly Summaries) are connected to L0 dimension nodes (U, L², T, C) through specific relationship types based on their dimensional formulas.

## Architecture

### Layer 0: Base Dimensions

Four fundamental dimensions (inspired by physics):

| Dimension | Full Name | Description | Unit | Analogy |
|-----------|-----------|-------------|------|---------|
| **U** | Units | Count of housing units | count | Mass |
| **L²** | Space | Area in sqft/sqm | sqft | Length² |
| **T** | Time | Months/years | months | Time |
| **C** | Cash Flow | INR revenue/cost | INR | Current |

### Layer 1: Data Nodes with Dimensional Attributes

Each L1 node (Project_L1, UnitType_L1, QuarterlySummary_L1) contains attributes with:
- **value**: The actual numerical/textual value
- **unit**: The measurement unit (e.g., "INR/sqft", "count", "date")
- **dimension**: The dimensional formula (e.g., "U", "C/L²", "1/T")

### Dimensional Relationships

Based on the dimensional formula, specific relationships are created:

#### 1. **IS** Relationship
Simple dimensions that directly represent a base dimension.

**Examples:**
- `totalSupplyUnits` (dimension: "U") → IS → U
- `launchDate` (dimension: "T") → IS → T
- `annualSalesValueCr` (dimension: "C") → IS → C
- `projectSizeAcres` (dimension: "L²") → IS → L²

#### 2. **NUMERATOR** and **DENOMINATOR** Relationships
Composite dimensions that are ratios of two base dimensions.

**Examples:**
- `currentPricePSF` (dimension: "C/L²")
  - NUMERATOR → C
  - DENOMINATOR → L²

- `unitSaleableSizeSqft` (dimension: "L²/U")
  - NUMERATOR → L²
  - DENOMINATOR → U

- `annualSalesValueCr` (dimension: "C/T")
  - NUMERATOR → C
  - DENOMINATOR → T

#### 3. **INVERSE_OF** Relationship
Dimensions that represent the reciprocal of a base dimension (1/dimension).

**Examples:**
- `monthlySalesVelocity` (dimension: "1/T") → INVERSE_OF → T
- `salesVelocityPct` (dimension: "Fraction/T") → INVERSE_OF → T

#### 4. **No Relationships**
Dimensionless attributes (metadata, text fields, flags).

**Examples:**
- `reraRegistered` (dimension: "None")
- `projectName` (dimension: "String")
- `soldPct` (dimension: "Dimensionless")

## Neo4j Cypher Queries

### 1. Explore All Dimensional Relationships

```cypher
// View all dimensional relationships with metadata
MATCH (n)-[r:HAS_DIMENSION]->(d:Dimension_L0)
RETURN
  labels(n)[0] as nodeType,
  r.attribute as attribute,
  r.dimensionType as relationshipType,
  r.dimension as dimensionFormula,
  d.name as targetDimension
LIMIT 50
```

### 2. Visualize Sara City Project Dimensions

```cypher
// Show Sara City project with all its dimensional relationships
MATCH (p:Project_L1 {projectName: 'Sara City'})-[r:HAS_DIMENSION]->(d:Dimension_L0)
RETURN p, r, d
```

### 3. Find All Attributes with Composite Dimensions

```cypher
// Find all attributes that are ratios (C/L², L²/U, etc.)
MATCH (n)-[r:HAS_DIMENSION {dimensionType: 'NUMERATOR'}]->(d1:Dimension_L0)
MATCH (n)-[r2:HAS_DIMENSION {dimensionType: 'DENOMINATOR'}]->(d2:Dimension_L0)
WHERE r.attribute = r2.attribute
RETURN
  labels(n)[0] as nodeType,
  r.attribute as attribute,
  d1.name + '/' + d2.name as compositeDimension,
  count(*) as nodeCount
```

### 4. Analyze Dimensional Usage

```cypher
// Count how many times each dimension is used
MATCH ()-[r:HAS_DIMENSION]->(d:Dimension_L0)
RETURN
  d.name as dimension,
  d.full_name as fullName,
  count(r) as usageCount,
  collect(DISTINCT r.dimensionType) as relationshipTypes
ORDER BY usageCount DESC
```

### 5. Find All Price-Related Attributes (C/L²)

```cypher
// Find all attributes with dimension C/L² (price per area)
MATCH (n)-[r1:HAS_DIMENSION {dimensionType: 'NUMERATOR'}]->(c:Dimension_L0 {name: 'C'})
MATCH (n)-[r2:HAS_DIMENSION {dimensionType: 'DENOMINATOR'}]->(l:Dimension_L0 {name: 'L²'})
WHERE r1.attribute = r2.attribute
RETURN DISTINCT
  r1.attribute as priceAttribute,
  n.location as location,
  n[r1.attribute] as value,
  n[r1.attribute + '_unit'] as unit
LIMIT 20
```

### 6. Find All Time-Related Attributes

```cypher
// Find all attributes related to Time dimension
MATCH (n)-[r:HAS_DIMENSION]->(t:Dimension_L0 {name: 'T'})
RETURN
  labels(n)[0] as nodeType,
  r.attribute as attribute,
  r.dimensionType as relationshipType,
  count(*) as nodeCount
```

### 7. Project Dimensional Profile

```cypher
// Get dimensional profile of a project
MATCH (p:Project_L1 {projectName: 'Sara City'})-[r:HAS_DIMENSION]->(d:Dimension_L0)
RETURN
  d.name as dimension,
  collect({
    attribute: r.attribute,
    value: p[r.attribute],
    unit: p[r.attribute + '_unit'],
    relationshipType: r.dimensionType
  }) as attributes
ORDER BY d.name
```

### 8. Find All Velocity Metrics (1/T)

```cypher
// Find all velocity/rate metrics (inverse time)
MATCH (n)-[r:HAS_DIMENSION {dimensionType: 'INVERSE_OF'}]->(t:Dimension_L0 {name: 'T'})
RETURN
  labels(n)[0] as nodeType,
  r.attribute as attribute,
  n[r.attribute] as value,
  n[r.attribute + '_unit'] as unit,
  count(*) as nodeCount
```

### 9. Compare Projects by Dimension

```cypher
// Compare projects on Cash Flow dimension
MATCH (p:Project_L1)-[r:HAS_DIMENSION {dimensionType: 'IS'}]->(c:Dimension_L0 {name: 'C'})
RETURN
  p.projectName as project,
  p.location as location,
  collect({
    attribute: r.attribute,
    value: p[r.attribute],
    unit: p[r.attribute + '_unit']
  }) as cashFlowMetrics
LIMIT 10
```

### 10. Dimensional Dependency Graph

```cypher
// Show how attributes depend on base dimensions
MATCH (p:Project_L1)-[r:HAS_DIMENSION]->(d:Dimension_L0)
WITH r.attribute as attribute,
     collect(DISTINCT {dimension: d.name, type: r.dimensionType}) as dependencies
RETURN
  attribute,
  dependencies,
  size(dependencies) as dependencyCount
ORDER BY dependencyCount DESC
LIMIT 20
```

## Data Quality Queries

### Check for Missing Dimensions

```cypher
// Find attributes without dimension information
MATCH (p:Project_L1)
WITH p, [key in keys(p) WHERE key ENDS WITH '_dimension'] as dimKeys
UNWIND dimKeys as dimKey
WITH p, dimKey, p[dimKey] as dimValue
WHERE dimValue IS NULL OR dimValue = 'None' OR dimValue = 'Dimensionless'
RETURN
  dimKey,
  count(*) as nullCount
```

### Validate Dimensional Relationships

```cypher
// Ensure all composite dimensions have both numerator and denominator
MATCH (n)-[r1:HAS_DIMENSION {dimensionType: 'NUMERATOR'}]->(d1)
WHERE NOT exists((n)-[:HAS_DIMENSION {dimensionType: 'DENOMINATOR', attribute: r1.attribute}]->())
RETURN
  labels(n)[0] as nodeType,
  r1.attribute as attribute,
  'Missing DENOMINATOR' as issue
```

## Visualization Queries

### Full Graph View (Limited)

```cypher
// Visualize the entire dimensional structure (limited to 100 nodes)
MATCH (n)-[r:HAS_DIMENSION]->(d:Dimension_L0)
RETURN n, r, d
LIMIT 100
```

### Dimension-Centric View

```cypher
// Show all L0 dimensions and their connections
MATCH (d:Dimension_L0)
OPTIONAL MATCH (d)<-[r:HAS_DIMENSION]-(n)
RETURN d, r, n
LIMIT 50
```

### Project Comparison View

```cypher
// Compare two projects dimensionally
MATCH (p1:Project_L1 {projectName: 'Sara City'})-[r1:HAS_DIMENSION]->(d:Dimension_L0)
MATCH (p2:Project_L1 {projectName: 'The Urbana'})-[r2:HAS_DIMENSION]->(d)
WHERE r1.attribute = r2.attribute
RETURN p1, r1, d, r2, p2
LIMIT 30
```

## Statistics

### Current Database Stats

```cypher
// Get comprehensive database statistics
MATCH (d:Dimension_L0)
WITH count(d) as dimensionCount
MATCH (p:Project_L1)
WITH dimensionCount, count(p) as projectCount
MATCH (u:UnitType_L1)
WITH dimensionCount, projectCount, count(u) as unitTypeCount
MATCH (q:QuarterlySummary_L1)
WITH dimensionCount, projectCount, unitTypeCount, count(q) as quarterlyCount
MATCH ()-[r:HAS_DIMENSION]->()
RETURN
  dimensionCount as L0_Dimensions,
  projectCount as Projects,
  unitTypeCount as UnitTypes,
  quarterlyCount as QuarterlySummaries,
  count(r) as Total_Dimensional_Relationships
```

### Relationship Type Distribution

```cypher
// Distribution of relationship types
MATCH ()-[r:HAS_DIMENSION]->()
RETURN
  r.dimensionType as relationshipType,
  count(r) as count,
  round(100.0 * count(r) / 1554) as percentage
ORDER BY count DESC
```

## Expected Results

Based on the V4 loader output:

- **Total L0 Dimensions**: 4 (U, L², T, C)
- **Total Projects**: 10
- **Total Unit Types**: 4
- **Total Quarterly Summaries**: 14
- **Total Dimensional Relationships**: 1,554

**Relationship Type Distribution**:
- IS: 1,125 (72%)
- DENOMINATOR: 187 (12%)
- NUMERATOR: 187 (12%)
- INVERSE_OF: 55 (4%)

**Dimension Usage**:
- U (Units): 621 relationships
- L² (Space): 563 relationships
- C (Cash Flow): 193 relationships
- T (Time): 177 relationships

## Next Steps

1. **Open Neo4j Browser**: http://localhost:7474
2. **Run sample queries** from this guide
3. **Explore dimensional relationships** visually
4. **Build Layer 2 calculators** that traverse these dimensional relationships
5. **Create Layer 3 optimization queries** that use dimensional constraints

## References

- **Loader Script**: `scripts/v4_load_l1_with_dimensional_rels.py`
- **Dimension Parser**: `scripts/dimension_parser.py`
- **Data Source**: `data/extracted/v3_lf_layer1_data_from_pdf.json`
- **Project Documentation**: `CLAUDE.md`
