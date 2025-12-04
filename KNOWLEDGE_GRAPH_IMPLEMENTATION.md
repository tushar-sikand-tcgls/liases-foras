# Knowledge Graph Implementation Guide

## Overview

**Goal:** Neo4j graph database integrating 3 data sources for real estate intelligence:
- **Source 1:** Liases Foras (4-layer metrics: L0→L3)
- **Source 2:** Google APIs (location context)
- **Source 3:** Government Data (regulations, planning)

**Core Concept:** Every metric traces back to 4 atomic dimensions (U, L², T, CF)

---

## Graph Schema

### Node Types

**Layer 0 (Raw Dimensions):**
```cypher
(:Project {projectId, totalUnits, totalArea, duration, revenue, cost})
(:Unit {unitId, type, area, price})
(:DimensionTemplate {symbol: 'U'|'L²'|'T'|'CF'})
```

**Layer 1 (Derived Metrics):**
```cypher
(:Metric_L1:PricePerSqft {value, formula: 'CF/L²', layer0Inputs})
(:Metric_L1:AbsorptionRate {value, formula: '(U/U_total)/T'})
```

**Layer 2 (Financial):**
```cypher
(:Metric_L2:NPV {value, discountRate, cashFlowSeries})
(:Metric_L2:IRR {value, calculationMethod: 'scipy.newton'})
```

**Layer 3 (Optimization):**
```cypher
(:Scenario_L3 {scenarioType, optimalMix, optimizedIRR, algorithm: 'SLSQP'})
```

**Google Source:**
```cypher
(:Location:GoogleSource {coordinates, aqi, elevation})
(:POI:GoogleSource {name, type, placeId, rating})
```

**Government Source:**
```cypher
(:RERAProject:GovernmentSource {reraId, complianceStatus})
(:SmartCityProject:GovernmentSource {projectName, expectedCompletion})
(:CensusData:GovernmentSource {populationProjection2030, growthRate})
```

### Key Relationships

```cypher
// Layer dependencies
(Project)-[:HAS_DIMENSION]->(DimensionTemplate)
(Metric_L1)-[:DERIVES_FROM_L0]->(Project)
(Metric_L2)-[:DEPENDS_ON_L1]->(Metric_L1)
(Scenario_L3)-[:USES_L2]->(Metric_L2)

// Cross-source enrichment
(Project)-[:LOCATED_AT]->(Location:GoogleSource)
(Location)-[:NEAR]->(POI:GoogleSource)
(Project)-[:REGISTERED_WITH]->(RERAProject:GovernmentSource)
(SmartCityProject)-[:AFFECTS_LOCATION]->(Location)
(Location)-[:HAS_CENSUS_DATA]->(CensusData)
```

---

## Key Queries

**Q1: Get all metrics for a project**
```cypher
MATCH (p:Project {projectId: $id})-[:HAS_METRIC_L1|HAS_METRIC_L2]->(m)
RETURN labels(m)[0] AS metric, m.value
```

**Q2: Cross-source enrichment (Why low absorption?)**
```cypher
MATCH (p:Project {projectId: $id})-[:HAS_METRIC_L1]->(ar:AbsorptionRate)
MATCH (p)-[:LOCATED_AT]->(loc:Location)-[:NEAR]->(poi:POI)
OPTIONAL MATCH (smart:SmartCityProject)-[:AFFECTS_LOCATION]->(loc)
OPTIONAL MATCH (loc)-[:HAS_CENSUS_DATA]->(census)
RETURN ar.value, ar.deviationFromMarket,
       collect(poi) AS nearbyPOIs,
       collect(smart) AS infrastructurePlans,
       census.growthRate
```

**Q3: Trace metric lineage**
```cypher
MATCH path = (irr:IRR {projectId: $id})
             -[:DEPENDS_ON_L2|DEPENDS_ON_L1|DEPENDS_ON_L0*1..5]->()
RETURN nodes(path)
```

---

## Implementation

### Layer 1 Calculator
```python
class Layer1Calculator:
    def calculate_psf(self, project_id):
        # Fetch Layer 0 data
        result = session.run("""
            MATCH (p:Project {projectId: $id})
            RETURN p.totalRevenue/p.totalSaleableArea AS psf
        """, id=project_id)

        # Store with provenance
        session.run("""
            MERGE (m:Metric_L1:PricePerSqft {metricId: $id})
            SET m.value = $psf, m.dimension = 'CF/L²'
            WITH m MATCH (p:Project {projectId: $pid})
            MERGE (p)-[:HAS_METRIC_L1]->(m)
            MERGE (m)-[:DERIVES_FROM_L0]->(p)
        """, id=f"{project_id}_PSF", psf=psf, pid=project_id)
```

### Layer 2 Calculator
```python
class Layer2Calculator:
    def calculate_irr(self, cash_flows):
        amounts = [cf['amount'] for cf in cash_flows]
        periods = [cf['period']/12 for cf in cash_flows]

        # scipy Newton's method
        irr = optimize.newton(
            lambda r: sum(amt/((1+r)**per) for amt, per in zip(amounts, periods)),
            x0=0.1
        )
        return irr
```

### Layer 3 Optimizer
```python
class Layer3Optimizer:
    def optimize_product_mix(self, total_units, unit_configs):
        def objective(x):
            revenue = sum(x[i] * config[i]['price'] for i in range(len(x)))
            return -revenue  # Maximize by minimizing negative

        result = minimize(objective, x0, method='SLSQP',
                         constraints=[{'type': 'eq', 'fun': lambda x: sum(x) - total_units}])
        return result.x
```

### Google Integration
```python
class GoogleContextService:
    def enrich_project(self, project_id):
        coords = get_project_coords(project_id)

        # Fetch POIs
        pois = gmaps.places_nearby(location=coords, radius=5000, type='school')

        # Store in graph
        session.run("""
            MERGE (loc:Location {locationId: $id})
            SET loc.coordinates = $coords
            WITH loc MERGE (poi:POI {poiId: $poi_id})
            SET poi.name = $name, poi.type = $type
            MERGE (loc)-[:NEAR]->(poi)
        """)
```

---

## Indexes

```cypher
CREATE INDEX project_id FOR (p:Project) ON (p.projectId);
CREATE INDEX metric_l1_project FOR (m:Metric_L1) ON (m.projectId);
CREATE INDEX location_id FOR (loc:Location) ON (loc.locationId);
CREATE INDEX rera_id FOR (rera:RERAProject) ON (rera.reraId);
```

---

## Roadmap

**Phase 1 (Weeks 1-2):** Neo4j setup, Layer 0 schema
**Phase 2 (Weeks 3-5):** Layer 1-3 calculators, LF integration
**Phase 3 (Weeks 6-7):** Google APIs integration
**Phase 4 (Weeks 8-9):** Government data integration
**Phase 5 (Weeks 10-11):** Cross-source enrichment workflows
**Phase 6 (Weeks 12-13):** Optimization, testing
**Phase 7 (Week 14):** MCP/Claude integration

---

## Performance Targets

- Neo4j queries: <500ms (LF data), <200ms (cached Google/Gov)
- Cross-source insights: <3s total
- 100K+ nodes supported
- All metrics ±2% accuracy vs LF standards
