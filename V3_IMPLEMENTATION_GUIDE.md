# V3.0.0 Implementation Guide
## MLTI-Inspired Knowledge Graph Architecture

### Status: Phase 1 Complete ✅
- **L0 Foundation**: 4 immutable dimensions created in Neo4j (U, L², T, C)
- **Database**: Cleared and ready for v3 structure
- **Script**: `scripts/v3_create_l0_dimensions.py` ✅

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 0 (L0): Dimension Definitions                         │
│ - U (Units/Inventory) count                                 │
│ - L² (Space/Area) sqft                                      │
│ - T (Time) date/period                                      │
│ - C (Cash Flow) INR                                         │
│ Status: ✅ COMPLETE                                         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 1 (L1): Project Attributes (Actual Data)              │
│ - L1_Project nodes (Sara City, etc.)                        │
│ - L1_Attribute nodes with dimensional tags                  │
│   • Pure: totalUnits=3018 (U)                               │
│   • Composite: annualSales=₹106Cr (C/T) ← FROM LF           │
│ - Link: (L1_Attribute)-[:USES_DIMENSION]->(Dimension_L0)   │
│ Status: ⏳ PENDING                                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 2 (L2): Calculated Metrics                            │
│ - L2_Metric nodes (AR, PSF, Months Inventory, etc.)        │
│ - Auto-calculated from L1 using dimensional algebra         │
│ - Link: (L2_Metric)-[:DEPENDS_ON_L1]->(L1_Attribute)       │
│ Status: ⏳ PENDING                                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Rules Layer (Configurable in Neo4j)                         │
│ - L3_Rule nodes with thresholds                             │
│ - Evaluates L1/L2 metrics → Positive or Negative            │
│ - Example: If AR < 0.5% → CRITICAL (Negative)              │
│ Status: ⏳ PENDING                                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 3 (L3): Insights & Recommendations                    │
│ - Positive feedback → Template-based insight                │
│ - Negative feedback → Gemini API generates recommendation   │
│ - L3_Insight nodes with narratives                          │
│ - Link: (L3_Insight)-[:APPLIES_RULE]->(L3_Rule)            │
│ Status: ⏳ PENDING                                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Chat Interface Enhancement                                   │
│ - Layer-aware query routing (L1/L2/L3)                     │
│ - Display formatted responses with dimensional context      │
│ Status: ⏳ PENDING                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Roadmap

### ✅ Phase 1: L0 Foundation (COMPLETE)
**Script**: `scripts/v3_create_l0_dimensions.py`

**Result**: 4 dimension nodes in Neo4j
```cypher
MATCH (d:Dimension_L0) RETURN d.name, d.fullName, d.unit
// Returns: U, L², T, C
```

---

### ⏳ Phase 2: L1 Data Structure

#### Step 1: Update PDF Extraction
**File**: `scripts/extract_pdf_layer1_data.py` (existing)

**Required Changes**:
```python
# REMOVE: Nested dimensions_L0 structure
# ADD: l1_attributes with dimensional tags

# Example transformation:
project = {
    "projectId": "3306",
    "projectName": "Sara City",
    "developer": "Sara Builders",
    "location": "Chakan, Pune",
    "l1_attributes": {
        "totalUnits": {
            "value": 3018,
            "dimension": "U",
            "unit": "count",
            "source": "LF_PDF_Page2",
            "isPure": True
        },
        "soldUnits": {
            "value": 2684,
            "dimension": "U",
            "unit": "count",
            "source": "LF_PDF_Page2",
            "isPure": True
        },
        "unsoldUnits": {
            "value": 334,
            "dimension": "U",
            "unit": "count",
            "source": "LF_PDF_Page2",
            "isPure": True
        },
        "unitSaleableSize": {
            "value": 411,
            "dimension": "L²",
            "unit": "sqft",
            "source": "LF_PDF_Page2",
            "isPure": True
        },
        "launchDate": {
            "value": "2007-11-01",
            "dimension": "T",
            "unit": "date",
            "source": "LF_PDF_Page2",
            "isPure": True
        },
        "possessionDate": {
            "value": "2027-12-31",
            "dimension": "T",
            "unit": "date",
            "source": "LF_PDF_Page2",
            "isPure": True
        },
        "currentPricePSF": {
            "value": 3996,
            "dimension": "C/L²",  # Composite FROM LF
            "unit": "INR/sqft",
            "source": "LF_PDF_Page2",
            "isPure": False
        },
        "annualSalesValue": {
            "value": 10600000000,  # ₹106 Cr
            "dimension": "C/T",  # Composite FROM LF
            "unit": "INR/year",
            "source": "LF_PDF_Page2",
            "isPure": False
        }
    }
}
```

**Action**: Update `extract_pdf_layer1_data.py` with new structure

---

#### Step 2: Create Neo4j L1 Loader
**New File**: `scripts/v3_load_l1_to_neo4j.py`

**Code Template**:
```python
def load_l1_project(session, project_data):
    """Load L1 project with attribute nodes"""

    # Create L1 project container
    query_project = """
    MERGE (p:L1_Project {projectId: $projectId})
    SET p.projectName = $projectName,
        p.developer = $developer,
        p.location = $location,
        p.loadedAt = datetime()
    RETURN p
    """
    session.run(query_project,
                projectId=project_data['projectId'],
                projectName=project_data['projectName'],
                developer=project_data['developer'],
                location=project_data['location'])

    # Create L1 attribute nodes
    for attr_name, attr_data in project_data['l1_attributes'].items():
        query_attr = """
        MATCH (p:L1_Project {projectId: $projectId})
        MATCH (d:Dimension_L0 {name: $dimension})

        MERGE (attr:L1_Attribute {
            attributeId: $attributeId,
            projectId: $projectId
        })
        SET attr.attributeName = $attributeName,
            attr.value = $value,
            attr.dimension = $dimension,
            attr.unit = $unit,
            attr.source = $source,
            attr.isPure = $isPure

        MERGE (p)-[:HAS_ATTRIBUTE]->(attr)
        MERGE (attr)-[:USES_DIMENSION]->(d)
        """

        # Extract dimension for linking (e.g., "C/L²" → "C" and "L²")
        dimensions = parse_dimension(attr_data['dimension'])

        for dim in dimensions:
            session.run(query_attr,
                       projectId=project_data['projectId'],
                       attributeId=f"{attr_name}_{project_data['projectId']}",
                       attributeName=attr_name,
                       value=attr_data['value'],
                       dimension=dim,
                       unit=attr_data['unit'],
                       source=attr_data['source'],
                       isPure=attr_data['isPure'])
```

---

### ⏳ Phase 3: L2 Calculation Engine

**New File**: `app/calculators/layer2_calculator.py`

**Key Metrics to Implement** (from PRD v3.0.0 QuickRef):

#### Category 1: Absorption & Sales Velocity
```python
class Layer2Calculator:

    @staticmethod
    def calculate_absorption_rate(project_id):
        """
        Formula: (Sold / Total) / Months
        Dimension: Fraction/T
        """
        sold = get_l1_value(project_id, 'soldUnits')  # U
        total = get_l1_value(project_id, 'totalUnits')  # U
        launch_date = get_l1_value(project_id, 'launchDate')  # T

        months_elapsed = calculate_months_since(launch_date)  # T

        absorption_rate = (sold / total) / months_elapsed  # (U/U)/T = Fraction/T

        return create_l2_metric(
            metricId=f"L2_AR_{project_id}",
            metricName="Absorption Rate",
            value=absorption_rate,
            dimension="Fraction/T",
            unit="%/month",
            formula="(soldUnits / totalUnits) / monthsElapsed",
            category="Sales_Velocity",
            sourceL1=[f"soldUnits_{project_id}",
                     f"totalUnits_{project_id}",
                     f"launchDate_{project_id}"]
        )

    @staticmethod
    def calculate_months_inventory(project_id):
        """
        Formula: Unsold / (Sold / Months)
        Dimension: T
        """
        unsold = get_l1_value(project_id, 'unsoldUnits')  # U
        sold = get_l1_value(project_id, 'soldUnits')  # U
        months_elapsed = get_months_elapsed(project_id)  # T

        sales_velocity = sold / months_elapsed  # U/T
        months_inventory = unsold / sales_velocity  # U / (U/T) = T

        return create_l2_metric(
            metricId=f"L2_MonthsInv_{project_id}",
            metricName="Months Inventory",
            value=months_inventory,
            dimension="T",
            unit="months",
            formula="unsoldUnits / (soldUnits / monthsElapsed)",
            category="Inventory_Aging"
        )
```

**Other Categories** (implement similarly):
- Category 2: Pricing Metrics (PSF calculations)
- Category 3: Inventory Aging
- Category 4: Revenue Metrics
- Category 5: Profitability
- Category 6: Efficiency Ratios
- Category 7: Market Position
- Category 8: Risk Metrics
- Category 9: Time-based Metrics
- Category 10: Developer Performance

**Total**: ~50 metrics (see `change-request/v3.0.0/QuickRef-L0-L1-L2-L3-Complete-Metrics.md`)

---

### ⏳ Phase 4: Rules Layer (Configurable)

**New File**: `scripts/v3_create_l3_rules.py`

**Code Template**:
```python
def create_l3_rules(session):
    """Create configurable rule nodes in Neo4j"""

    rules = [
        {
            "ruleId": "R001",
            "ruleName": "Absorption_Rate_Sales_Health",
            "metricTrigger": "Absorption Rate",
            "thresholds": [
                {"condition": "< 0.005", "assessment": "CRITICAL", "severity": "HIGH", "isNegative": True},
                {"condition": "0.005-0.010", "assessment": "POOR", "severity": "MEDIUM", "isNegative": True},
                {"condition": "0.010-0.015", "assessment": "GOOD", "severity": "LOW", "isNegative": False},
                {"condition": "> 0.015", "assessment": "EXCELLENT", "severity": "INFO", "isNegative": False}
            ],
            "actionRequired": True,
            "isActive": True
        },
        {
            "ruleId": "R002",
            "ruleName": "Inventory_Aging_Risk",
            "metricTrigger": "Months Inventory",
            "thresholds": [
                {"condition": "> 36", "assessment": "CRITICAL", "severity": "HIGH", "isNegative": True},
                {"condition": "24-36", "assessment": "POOR", "severity": "MEDIUM", "isNegative": True},
                {"condition": "12-24", "assessment": "GOOD", "severity": "LOW", "isNegative": False},
                {"condition": "< 12", "assessment": "EXCELLENT", "severity": "INFO", "isNegative": False}
            ],
            "actionRequired": True,
            "isActive": True
        }
        # ... 30+ rules total
    ]

    for rule in rules:
        query = """
        MERGE (r:L3_Rule {ruleId: $ruleId})
        SET r.ruleName = $ruleName,
            r.metricTrigger = $metricTrigger,
            r.thresholds = $thresholds,
            r.actionRequired = $actionRequired,
            r.isActive = $isActive,
            r.createdAt = datetime()
        """
        session.run(query, **rule)
```

**Configuration UI** (future enhancement):
- Allow business users to update thresholds via admin panel
- No code changes required - just update Neo4j properties

---

### ⏳ Phase 5: L3 Insight Generator with Gemini API

**New File**: `app/services/l3_insight_generator.py`

**Code Template**:
```python
import google.generativeai as genai
import os

class L3InsightGenerator:

    def __init__(self):
        # Configure Gemini API
        genai.configure(api_key="AIzaSyAG33P0W7MaScsX7VJxBy-dPJiiIbZ_XhM")
        self.model = genai.GenerativeModel('gemini-pro')

    def generate_insight(self, project_id, l1_data, l2_metrics):
        """
        Generate L3 insights by evaluating rules against metrics

        Flow:
        1. Evaluate L2 metrics against L3 rules
        2. If positive → Template-based insight
        3. If negative → Gemini API generates recommendation
        """

        triggered_rules = []

        # Evaluate rules
        for metric_name, metric_value in l2_metrics.items():
            rule = get_rule_for_metric(metric_name)
            assessment = evaluate_rule(rule, metric_value)

            triggered_rules.append({
                'rule': rule,
                'metric': metric_name,
                'value': metric_value,
                'assessment': assessment['assessment'],
                'isNegative': assessment['isNegative']
            })

        # Generate insights
        insights = []

        for triggered in triggered_rules:
            if triggered['isNegative']:
                # Use Gemini API for negative feedback
                narrative = self._generate_gemini_recommendation(
                    project_id,
                    l1_data,
                    l2_metrics,
                    triggered
                )
            else:
                # Use template for positive feedback
                narrative = self._generate_template_insight(
                    project_id,
                    triggered
                )

            insights.append({
                'insightId': f"L3_{triggered['rule']['ruleId']}_{project_id}",
                'projectId': project_id,
                'assessment': triggered['assessment'],
                'severity': triggered['rule']['severity'],
                'narrative': narrative,
                'ruleApplied': triggered['rule']['ruleId']
            })

        # Save to Neo4j
        self._save_insights_to_neo4j(insights)

        return insights

    def _generate_template_insight(self, project_id, triggered):
        """Template-based insight for positive feedback"""
        templates = {
            "EXCELLENT": f"{triggered['metric']} is performing excellently at {triggered['value']:.2f}. This indicates strong market demand.",
            "GOOD": f"{triggered['metric']} is in good health at {triggered['value']:.2f}. Continue current strategy."
        }

        return templates.get(triggered['assessment'], "Performance is satisfactory.")

    def _generate_gemini_recommendation(self, project_id, l1_data, l2_metrics, triggered):
        """
        Use Gemini API to generate detailed recommendation for negative feedback
        """

        prompt = f"""You are a real estate analytics expert analyzing project performance.

Project: {l1_data.get('projectName')}
Location: {l1_data.get('location')}

L1 Data (Actual Values):
- Total Units: {l1_data.get('totalUnits')}
- Sold Units: {l1_data.get('soldUnits')}
- Unsold Units: {l1_data.get('unsoldUnits')}
- Launch Date: {l1_data.get('launchDate')}
- Current Price PSF: ₹{l1_data.get('currentPricePSF')}

L2 Metrics (Calculated):
- Absorption Rate: {l2_metrics.get('Absorption Rate'):.4f}%/month (CRITICAL - below 0.5% threshold)
- Months Inventory: {l2_metrics.get('Months Inventory'):.1f} months

Problem Identified:
- {triggered['metric']} is {triggered['assessment']} at {triggered['value']:.4f}
- Threshold: {triggered['rule']['thresholds'][0]['condition']}

Generate a concise analysis with:
1. Assessment (2-3 sentences explaining why this is problematic)
2. Root Cause Analysis (bullet points)
3. 3-5 Prioritized Recommendations (specific, actionable)

Format: Professional but concise. Use bullet points. Focus on actionable insights.
"""

        response = self.model.generate_content(prompt)
        return response.text

    def _save_insights_to_neo4j(self, insights):
        """Save L3 insights to Neo4j"""
        # Implementation to save insights as L3_Insight nodes
        pass
```

---

### ⏳ Phase 6: Chat Interface Enhancement

**File**: `app/services/chat_service.py` (create if doesn't exist)

**Code Template**:
```python
class ChatService:

    def process_query(self, user_query, project_id):
        """
        Layer-aware query routing

        Query types:
        - L1_DATA: "What's Sara City's total units?"
        - L2_METRIC: "What's the absorption rate?"
        - L3_INSIGHT: "Is this project performing well?"
        - L3_RECOMMENDATION: "What should I do to improve sales?"
        """

        query_type = self.classify_query(user_query)

        if query_type == "L1_DATA":
            return self.fetch_l1_data(project_id, user_query)

        elif query_type == "L2_METRIC":
            return self.fetch_l2_metric(project_id, user_query)

        elif query_type == "L3_INSIGHT":
            return self.fetch_l3_insights(project_id)

        elif query_type == "L3_RECOMMENDATION":
            return self.fetch_l3_recommendations(project_id)

    def fetch_l2_metric(self, project_id, query):
        """Query Neo4j for L2 metric with full context"""

        result = neo4j_query(f"""
            MATCH (p:L1_Project {{projectId: '{project_id}'}})
            -[:HAS_L2_METRIC]->(m:L2_Metric)
            WHERE m.metricName CONTAINS '{extract_metric_name(query)}'

            MATCH (m)-[:DEPENDS_ON_L1]->(attr:L1_Attribute)

            RETURN m.metricName as metricName,
                   m.value as value,
                   m.unit as unit,
                   m.dimension as dimension,
                   m.formula as formula,
                   collect(attr.attributeName) as l1_sources
        """)

        return {
            "layer": "L2",
            "metricName": result['metricName'],
            "value": result['value'],
            "unit": result['unit'],
            "dimension": result['dimension'],
            "formula": result['formula'],
            "l1_sources": result['l1_sources']
        }

    def fetch_l3_insights(self, project_id):
        """Query Neo4j for L3 insights"""

        result = neo4j_query(f"""
            MATCH (p:L1_Project {{projectId: '{project_id}'}})
            -[:HAS_L3_INSIGHT]->(insight:L3_Insight)
            -[:APPLIES_RULE]->(rule:L3_Rule)

            RETURN insight.assessment as assessment,
                   insight.severity as severity,
                   insight.narrative as narrative,
                   rule.ruleName as ruleName
            ORDER BY
                CASE insight.severity
                    WHEN 'HIGH' THEN 1
                    WHEN 'MEDIUM' THEN 2
                    WHEN 'LOW' THEN 3
                    ELSE 4
                END
        """)

        return {
            "layer": "L3",
            "insights": result
        }
```

---

## Next Steps (Execution Order)

1. **Update PDF Extraction** → `scripts/extract_pdf_layer1_data.py`
2. **Create L1 Loader** → `scripts/v3_load_l1_to_neo4j.py`
3. **Run L1 Loading** → Populate Neo4j with L1 data
4. **Implement L2 Calculator** → `app/calculators/layer2_calculator.py` (start with 10 key metrics)
5. **Create Rules** → `scripts/v3_create_l3_rules.py` (start with 5 key rules)
6. **Implement L3 Generator** → `app/services/l3_insight_generator.py` (Gemini integration)
7. **Update Chat Service** → `app/services/chat_service.py`
8. **Test End-to-End** → Query chat for L1/L2/L3 responses

---

## Testing Strategy

### Test Case 1: L1 Data Query
```
User: "What's Sara City's total units?"
Expected: {layer: "L1", attribute: "totalUnits", value: 3018, dimension: "U", unit: "count"}
```

### Test Case 2: L2 Metric Query
```
User: "What's the absorption rate?"
Expected: {layer: "L2", metricName: "Absorption Rate", value: 0.0037, unit: "%/month",
           dimension: "Fraction/T", formula: "(soldUnits / totalUnits) / monthsElapsed"}
```

### Test Case 3: L3 Insight Query
```
User: "Is this project performing well?"
Expected: {layer: "L3", assessment: "CRITICAL",
           narrative: "Absorption rate of 0.37%/month is critically low...",
           recommendations: [Gemini-generated list]}
```

---

## Gemini API Key
**API Key**: `AIzaSyAG33P0W7MaScsX7VJxBy-dPJiiIbZ_XhM`

**Usage**:
- Only called for **negative feedback** in L3
- Positive feedback uses templates
- Reduces API costs and latency

---

## References

**PRD v3.0.0 Documents**:
- `/change-request/v3.0.0/PRD-v3-MLTI-Layer-Architecture.md` - Complete specification
- `/change-request/v3.0.0/QuickRef-L0-L1-L2-L3-Complete-Metrics.md` - 50+ L2 metrics, 30+ L3 rules
- `/change-request/v3.0.0/VisualGuide-SaraCity-L0-L1-L2-L3.md` - Sara City walkthrough

---

## Current Progress

| Component | Status | File |
|-----------|--------|------|
| L0 Dimensions | ✅ Complete | `scripts/v3_create_l0_dimensions.py` |
| L1 Extraction | ⏳ Pending | `scripts/extract_pdf_layer1_data.py` (update needed) |
| L1 Loader | ⏳ Pending | `scripts/v3_load_l1_to_neo4j.py` (new file) |
| L2 Calculator | ⏳ Pending | `app/calculators/layer2_calculator.py` (new file) |
| L3 Rules | ⏳ Pending | `scripts/v3_create_l3_rules.py` (new file) |
| L3 Generator | ⏳ Pending | `app/services/l3_insight_generator.py` (new file) |
| Chat Service | ⏳ Pending | `app/services/chat_service.py` (new/update) |
| Graph Viz | ⏳ Pending | `frontend/components/graph_view.py` (update) |

---

## Summary

✅ **Completed**: L0 foundation with 4 immutable dimensions in Neo4j

⏳ **Next Priority**: Implement L1, L2, Rules, L3, and Chat in sequence

🎯 **Goal**: Enable chat interface to provide intelligent L1/L2/L3 responses with dimensional context and Gemini-powered recommendations for negative feedback
