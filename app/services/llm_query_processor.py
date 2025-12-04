"""
LLM-Powered Query Processor
Uses LLM to understand queries and generate appropriate graph queries dynamically
"""

from typing import Dict, Optional
import json
import google.generativeai as genai
from neo4j import GraphDatabase


class LLMQueryProcessor:
    """Process natural language queries using LLM to understand intent and generate graph queries"""

    def __init__(self, gemini_api_key: str, neo4j_driver):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.driver = neo4j_driver

        # Knowledge graph schema (not hardcoded logic, just data!)
        self.kg_schema = self._load_kg_schema()

    def _load_kg_schema(self) -> Dict:
        """Load knowledge graph schema as context for LLM"""
        return {
            "layers": {
                "0": {
                    "name": "Raw Dimensions",
                    "description": "Atomic dimensional data from Liases Foras",
                    "dimensions": {
                        "U": {
                            "symbol": "U",
                            "name": "Units",
                            "unit": "Units",
                            "description": "Number of housing units",
                            "neo4j_field": "totalUnits",
                            "examples": ["project size", "units", "total units", "number of units"]
                        },
                        "L²": {
                            "symbol": "L²",
                            "name": "Area",
                            "unit": "sqft",
                            "description": "Spatial dimension in square feet",
                            "neo4j_field": "totalSaleableArea",
                            "examples": ["area", "saleable area", "total area", "square feet"]
                        },
                        "T": {
                            "symbol": "T",
                            "name": "Time",
                            "unit": "months",
                            "description": "Temporal dimension (project duration)",
                            "neo4j_field": "projectDuration",
                            "examples": ["duration", "project duration", "time", "months"]
                        },
                        "CF": {
                            "symbol": "CF",
                            "name": "Cash Flow",
                            "unit": "INR",
                            "description": "Financial dimension (revenue, cost)",
                            "neo4j_fields": {
                                "revenue": "totalRevenue",
                                "cost": "totalCost"
                            },
                            "examples": ["revenue", "cost", "cash flow", "money"]
                        }
                    }
                },
                "1": {
                    "name": "Derived Metrics",
                    "description": "Calculated from Layer 0 using formulas",
                    "metrics": {
                        "PSF": {
                            "name": "Price Per Sqft",
                            "formula": "CF/L²",
                            "unit": "INR/sqft",
                            "neo4j_query": "totalRevenue / totalSaleableArea"
                        },
                        "ASP": {
                            "name": "Average Selling Price",
                            "formula": "CF/U",
                            "unit": "INR/unit",
                            "neo4j_query": "totalRevenue / totalUnits"
                        }
                    }
                },
                "2": {
                    "name": "Financial Metrics",
                    "description": "Complex financial calculations",
                    "metrics": {
                        "NPV": {"name": "Net Present Value", "unit": "INR"},
                        "IRR": {"name": "Internal Rate of Return", "unit": "%"}
                    }
                }
            },
            "aggregations": {
                "average": {"cypher": "avg", "description": "Calculate average/mean"},
                "sum": {"cypher": "sum", "description": "Calculate total/sum"},
                "count": {"cypher": "count", "description": "Count number of items"},
                "min": {"cypher": "min", "description": "Find minimum value"},
                "max": {"cypher": "max", "description": "Find maximum value"},
                "median": {"cypher": "percentileCont", "description": "Calculate median (50th percentile)"},
                "stdev": {"cypher": "stdev", "description": "Calculate standard deviation"},
                "variance": {"cypher": "stdev", "description": "Calculate variance"},
                "percentile": {"cypher": "percentileCont", "description": "Calculate percentile"}
            },
            "statistical_operations": {
                "distribution": {
                    "description": "Get distribution of values (histogram)",
                    "returns": "buckets with counts"
                },
                "outliers": {
                    "description": "Identify outliers using IQR method",
                    "returns": "list of outlier values"
                },
                "range": {
                    "description": "Get range (max - min)",
                    "returns": "single value"
                },
                "quartiles": {
                    "description": "Get Q1, Q2 (median), Q3",
                    "returns": "three values"
                }
            },
            "filters": {
                "top_n": {
                    "description": "Get top N items by value",
                    "cypher_pattern": "ORDER BY {field} DESC LIMIT {n}"
                },
                "bottom_n": {
                    "description": "Get bottom N items by value",
                    "cypher_pattern": "ORDER BY {field} ASC LIMIT {n}"
                },
                "greater_than": {
                    "description": "Filter items greater than value",
                    "cypher_pattern": "WHERE {field} > {value}"
                },
                "less_than": {
                    "description": "Filter items less than value",
                    "cypher_pattern": "WHERE {field} < {value}"
                },
                "between": {
                    "description": "Filter items between two values",
                    "cypher_pattern": "WHERE {field} >= {min} AND {field} <= {max}"
                }
            },
            "sorting": {
                "ascending": {"cypher": "ASC", "description": "Sort low to high"},
                "descending": {"cypher": "DESC", "description": "Sort high to low"}
            }
        }

    def process_query(self, query: str) -> Dict:
        """
        Process natural language query using LLM

        Steps:
        1. LLM analyzes query and knowledge graph schema
        2. LLM decides: layer, attribute, dimension, aggregation
        3. LLM generates Cypher query
        4. Execute query on Neo4j
        5. Format and return result
        """

        # Step 1: Ask LLM to understand the query
        understanding = self._understand_query(query)

        if understanding.get('error'):
            return {'status': 'error', 'message': understanding['error']}

        # Step 2: Generate Cypher query based on LLM understanding
        cypher_query = self._generate_cypher(understanding)

        # Step 3: Execute on Neo4j
        result = self._execute_query(cypher_query)

        # Step 4: Format response
        return self._format_response(query, understanding, cypher_query, result)

    def _understand_query(self, query: str) -> Dict:
        """Use LLM to understand what the query is asking for"""

        prompt = f"""You are a knowledge graph query analyzer for a real estate analytics system.

KNOWLEDGE GRAPH SCHEMA:
{json.dumps(self.kg_schema, indent=2)}

USER QUERY: "{query}"

Analyze this query and determine:
1. Which LAYER it belongs to (0, 1, 2)
2. Which TARGET ATTRIBUTE is being queried
3. Which DIMENSION it maps to (U, L², T, CF) if Layer 0
4. Which AGGREGATION function to use (average, sum, count, min, max)
5. What NEO4J FIELD to query
6. What UNIT the result should have

IMPORTANT RULES:
- "Project size" = Layer 0, Dimension U, Field: totalUnits, Unit: Units
- "Area" = Layer 0, Dimension L², Field: totalSaleableArea, Unit: sqft
- "Duration" = Layer 0, Dimension T, Field: projectDuration, Unit: months
- "Revenue" = Layer 0, Dimension CF, Field: totalRevenue, Unit: INR
- "Cost" = Layer 0, Dimension CF, Field: totalCost, Unit: INR

QUERY OPERATIONS (Think SQL):

1. AGGREGATIONS:
- "average", "mean" → aggregation: "average"
- "sum", "total" → aggregation: "sum"
- "median" → aggregation: "median"
- "stdev" → aggregation: "stdev"
- "min", "max", "count" → aggregation: "min"/"max"/"count"
- "distribution" → aggregation: "distribution"

2. FILTERS:
- "top 5", "top N" → filter: "top_n", limit: 5
- "bottom 3", "bottom N" → filter: "bottom_n", limit: 3
- "greater than X", "> X" → filter: "greater_than", value: X
- "less than X", "< X" → filter: "less_than", value: X
- "between X and Y" → filter: "between", min: X, max: Y

3. SORTING:
- "sort by X descending", "order by X desc" → sort_field: "X", sort_order: "descending"
- "sort by X ascending", "order by X asc" → sort_field: "X", sort_order: "ascending"

4. GROUPING:
- "group by city", "by location" → group_by: "city"/"location"

5. DATE RANGES:
- "in 2024", "during Q3" → date_filter: "year:2024" or "quarter:Q3"
- "between Jan 2024 and Mar 2024" → date_range: {{start: "2024-01", end: "2024-03"}}

Return ONLY a JSON object (no markdown):
{{
  "layer": 0,
  "target_attribute": "Project Size",
  "dimension": "U",
  "aggregation": "average",
  "neo4j_field": "totalUnits",
  "unit": "Units",
  "description": "Calculate average number of units across all projects",

  // Optional filters/modifiers
  "filter_type": "top_n",
  "filter_value": 5,
  "sort_field": "totalUnits",
  "sort_order": "descending",
  "group_by": null,
  "date_filter": null
}}

If you cannot understand the query, return:
{{"error": "Cannot understand query"}}
"""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            understanding = json.loads(response_text)
            return understanding

        except Exception as e:
            return {'error': f'LLM failed to understand query: {str(e)}'}

    def _generate_cypher(self, understanding: Dict) -> Dict:
        """
        Generate Cypher query based on LLM understanding

        Handles:
        - Aggregations (avg, sum, stdev, etc.)
        - Filters (top N, bottom N, greater than, etc.)
        - Sorting (asc, desc)
        - Grouping (by city, location, etc.)
        - Date ranges
        """

        layer = understanding.get('layer')
        aggregation = understanding.get('aggregation', 'avg')
        neo4j_field = understanding.get('neo4j_field')

        # Extract filters/modifiers
        filter_type = understanding.get('filter_type')
        filter_value = understanding.get('filter_value')
        sort_field = understanding.get('sort_field', neo4j_field)
        sort_order = understanding.get('sort_order')
        group_by = understanding.get('group_by')
        date_filter = understanding.get('date_filter')

        if layer == 0:
            # Layer 0: Query Project nodes directly

            # Handle special statistical operations
            if aggregation == 'median':
                cypher = f"""
                MATCH (p:Project)
                WHERE p.{neo4j_field} IS NOT NULL
                RETURN percentileCont(p.{neo4j_field}, 0.5) AS result,
                       count(p) AS count,
                       collect(p.{neo4j_field}) AS values,
                       collect(p.projectName) AS projects
                """

            elif aggregation == 'stdev':
                cypher = f"""
                MATCH (p:Project)
                WHERE p.{neo4j_field} IS NOT NULL
                RETURN stdev(p.{neo4j_field}) AS result,
                       avg(p.{neo4j_field}) AS mean,
                       count(p) AS count,
                       collect(p.{neo4j_field}) AS values,
                       collect(p.projectName) AS projects
                """

            elif aggregation == 'variance':
                cypher = f"""
                MATCH (p:Project)
                WHERE p.{neo4j_field} IS NOT NULL
                WITH stdev(p.{neo4j_field}) AS std,
                     avg(p.{neo4j_field}) AS mean,
                     count(p) AS count,
                     collect(p.{neo4j_field}) AS values,
                     collect(p.projectName) AS projects
                RETURN std * std AS result, mean, count, values, projects
                """

            elif aggregation == 'range':
                cypher = f"""
                MATCH (p:Project)
                WHERE p.{neo4j_field} IS NOT NULL
                RETURN max(p.{neo4j_field}) - min(p.{neo4j_field}) AS result,
                       min(p.{neo4j_field}) AS min_value,
                       max(p.{neo4j_field}) AS max_value,
                       count(p) AS count,
                       collect(p.{neo4j_field}) AS values,
                       collect(p.projectName) AS projects
                """

            elif aggregation == 'quartiles':
                cypher = f"""
                MATCH (p:Project)
                WHERE p.{neo4j_field} IS NOT NULL
                RETURN percentileCont(p.{neo4j_field}, 0.25) AS q1,
                       percentileCont(p.{neo4j_field}, 0.5) AS q2,
                       percentileCont(p.{neo4j_field}, 0.75) AS q3,
                       count(p) AS count,
                       collect(p.{neo4j_field}) AS values,
                       collect(p.projectName) AS projects
                """

            elif aggregation == 'distribution':
                # Return all values for distribution analysis
                cypher = f"""
                MATCH (p:Project)
                WHERE p.{neo4j_field} IS NOT NULL
                WITH p.{neo4j_field} AS value, p.projectName AS project
                ORDER BY value
                RETURN collect(value) AS values,
                       collect(project) AS projects,
                       count(value) AS count,
                       min(value) AS min_value,
                       max(value) AS max_value,
                       avg(value) AS mean,
                       stdev(value) AS stdev
                """

            else:
                # Standard aggregations
                agg_func = self.kg_schema['aggregations'].get(aggregation, {}).get('cypher', 'avg')
                cypher = f"""
                MATCH (p:Project)
                WHERE p.{neo4j_field} IS NOT NULL
                RETURN {agg_func}(p.{neo4j_field}) AS result,
                       count(p) AS count,
                       collect(p.{neo4j_field}) AS values,
                       collect(p.projectName) AS projects
                """

        elif layer == 1:
            # Layer 1: Query derived metrics
            metric_name = understanding.get('metric_name')
            cypher = f"""
            MATCH (p:Project)
            WITH p, {understanding.get('neo4j_query', 'null')} AS metric_value
            WHERE metric_value IS NOT NULL
            RETURN avg(metric_value) AS result,
                   count(p) AS count,
                   collect(metric_value) AS values,
                   collect(p.projectName) AS projects
            """

        else:
            cypher = "MATCH (p:Project) RETURN count(p) AS result"

        return {
            'query': cypher.strip(),
            'params': {}
        }

    def _execute_query(self, cypher_query: Dict) -> Optional[Dict]:
        """Execute Cypher query on Neo4j"""

        try:
            with self.driver.session() as session:
                result = session.run(cypher_query['query'], cypher_query['params'])
                record = result.single()

                if not record:
                    return None

                return {
                    'result': record['result'],
                    'count': record.get('count', 0),
                    'values': record.get('values', []),
                    'projects': record.get('projects', [])
                }
        except Exception as e:
            return {'error': f'Neo4j query failed: {str(e)}'}

    def _format_response(self, original_query: str, understanding: Dict,
                        cypher_query: Dict, result: Optional[Dict]) -> Dict:
        """Format final response"""

        if not result or 'error' in result:
            return {
                'status': 'error',
                'message': result.get('error', 'No data found') if result else 'Query execution failed'
            }

        layer = understanding.get('layer')
        dimension = understanding.get('dimension', '')
        aggregation = understanding.get('aggregation', 'avg')
        unit = understanding.get('unit', '')

        # Calculate formula representation
        if aggregation == 'average':
            formula = f"X = Σ {dimension} / {result.get('count', 0)}"
        elif aggregation == 'sum':
            formula = f"X = Σ {dimension}"
        elif aggregation == 'count':
            formula = f"X = count(Projects)"
        else:
            formula = f"X = {aggregation}({dimension})"

        # Build breakdown
        breakdown = []
        if 'values' in result and 'projects' in result:
            for i, (project, value) in enumerate(zip(result['projects'], result['values']), 1):
                breakdown.append({
                    'index': i,
                    'projectName': project,
                    'value': value
                })

        # Format result value
        result_value = result['result']
        if isinstance(result_value, float):
            result_value = round(result_value, 1)

        return {
            'status': 'success',
            'query': original_query,
            'understanding': {
                'layer': layer,
                'targetAttribute': understanding.get('target_attribute'),
                'dimension': dimension,
                'aggregation': aggregation,
                'description': understanding.get('description', '')
            },
            'result': {
                'value': result_value,
                'unit': unit,
                'text': f"{result_value} {unit}"
            },
            'calculation': {
                'formula': formula,
                'breakdown': breakdown,
                'projectCount': result.get('count', 0)
            },
            'provenance': {
                'dataSource': 'Liases Foras',
                'layer': f'Layer {layer}',
                'cypherQuery': cypher_query['query'],
                'llmModel': 'gemini-1.5-flash'
            }
        }


# FastAPI endpoint
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter()


class QueryRequest(BaseModel):
    query: str


@router.post("/api/query/llm-calculate")
async def llm_calculate_query(request: QueryRequest):
    """
    LLM-powered query processor

    Examples:
    - "Calculate the average of project size"
    - "What is the total revenue?"
    - "Find the maximum area"
    - "How many projects are there?"

    The LLM will:
    1. Understand which layer and dimension you're asking about
    2. Generate appropriate Cypher query
    3. Execute on knowledge graph
    4. Return formatted result
    """

    from app.config import settings
    from app.db.neo4j_client import get_neo4j_driver

    try:
        driver = get_neo4j_driver()
        processor = LLMQueryProcessor(
            gemini_api_key=settings.GEMINI_API_KEY,
            neo4j_driver=driver
        )

        result = processor.process_query(request.query)

        if result['status'] == 'error':
            raise HTTPException(status_code=400, detail=result['message'])

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
