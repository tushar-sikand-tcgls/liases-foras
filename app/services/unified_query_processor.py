"""
Unified Query Processor - LLM + Dimensional Calculator
Intelligently determines if data exists or needs to be calculated
"""

import json
import google.generativeai as genai
from typing import Dict, Optional
from neo4j import GraphDatabase
from app.services.dimensional_calculator import DimensionalCalculator, Dimension, DimensionalCypherGenerator


class UnifiedQueryProcessor:
    """
    Intelligent query processor that:
    1. Uses LLM to understand user intent
    2. Checks if data exists in knowledge graph
    3. If not, uses dimensional calculator to compute it
    4. Supports all operations: math, statistical, SQL, programming
    """

    def __init__(self, gemini_api_key: str, neo4j_driver):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.driver = neo4j_driver
        self.dim_calc = DimensionalCalculator()
        self.cypher_gen = DimensionalCypherGenerator(self.dim_calc)

        # Complete knowledge graph schema
        self.kg_schema = self._build_complete_schema()

    def _build_complete_schema(self) -> Dict:
        """Build complete schema including all operations"""
        return {
            "layers": {
                "0": {
                    "name": "Raw Dimensions",
                    "description": "Atomic data from Liases Foras",
                    "dimensions": {
                        "U": {
                            "symbol": "U",
                            "name": "Units",
                            "neo4j_field": "totalUnits",
                            "unit": "Units",
                            "examples": ["project size", "units", "total units", "number of units"]
                        },
                        "L²": {
                            "symbol": "L²",
                            "name": "Area",
                            "neo4j_field": "totalSaleableArea",
                            "unit": "sqft",
                            "examples": ["area", "saleable area", "total area"]
                        },
                        "T": {
                            "symbol": "T",
                            "name": "Time",
                            "neo4j_field": "projectDuration",
                            "unit": "months",
                            "examples": ["duration", "project duration", "time"]
                        },
                        "CF": {
                            "symbol": "CF",
                            "name": "CashFlow",
                            "neo4j_fields": {
                                "revenue": "totalRevenue",
                                "cost": "totalCost"
                            },
                            "unit": "INR",
                            "examples": ["revenue", "cost", "cash flow", "price"]
                        }
                    }
                },
                "1": {
                    "name": "Derived Metrics (L0÷L0)",
                    "description": "Created by dividing Layer 0 dimensions - DYNAMICALLY GENERATED ON DEMAND",
                    "note": "Any L0÷L0 division creates a valid Layer 1 metric automatically",
                    "known_metrics": {
                        "PSF": {
                            "symbol": "CF/L²",
                            "name": "Price Per Sqft",
                            "formula": "totalRevenue ÷ totalSaleableArea",
                            "unit": "INR/sqft",
                            "calculation": "DIVISION",
                            "components": {"numerator": "CF", "denominator": "L²"}
                        },
                        "ASP": {
                            "symbol": "CF/U",
                            "name": "Average Selling Price",
                            "formula": "totalRevenue ÷ totalUnits",
                            "unit": "INR/unit",
                            "calculation": "DIVISION",
                            "components": {"numerator": "CF", "denominator": "U"}
                        },
                        "SalesVelocity": {
                            "symbol": "U/T",
                            "name": "Sales Velocity",
                            "formula": "unitsSold ÷ timePeriod",
                            "unit": "units/month",
                            "calculation": "DIVISION",
                            "components": {"numerator": "U", "denominator": "T"}
                        },
                        "AreaPerUnit": {
                            "symbol": "L²/U",
                            "name": "Area Per Unit",
                            "formula": "totalSaleableArea ÷ totalUnits",
                            "unit": "sqft/unit",
                            "calculation": "DIVISION",
                            "components": {"numerator": "L²", "denominator": "U"}
                        }
                    }
                },
                "2": {
                    "name": "Financial Metrics (Complex)",
                    "description": "NPV, IRR, etc. - stored or calculated",
                    "metrics": {
                        "NPV": {"stored": True, "neo4j_field": "npv"},
                        "IRR": {"stored": True, "neo4j_field": "irr"}
                    }
                }
            },
            "operations": {
                "math": {
                    "addition": {"symbols": ["+", "plus", "sum", "total"], "same_dimension_only": True},
                    "subtraction": {"symbols": ["-", "minus", "difference"], "same_dimension_only": True},
                    "multiplication": {"symbols": ["*", "times", "multiply"], "creates_composite": True},
                    "division": {"symbols": ["/", "÷", "divide", "per"], "creates_new_layer": True}
                },
                "statistical": {
                    "mean": {"cypher": "avg", "aliases": ["average", "mean", "avg"]},
                    "median": {"cypher": "percentileCont(x, 0.5)"},
                    "stdev": {"cypher": "stdev", "aliases": ["standard deviation", "std"]},
                    "variance": {"calculation": "stdev^2"},
                    "quartiles": {"cypher": "percentileCont"},
                    "distribution": {"returns": "histogram"}
                },
                "sql": {
                    "filter": {"keywords": ["where", "filter", ">", "<", "=", "between"], "clause": "WHERE"},
                    "group_by": {"keywords": ["group by", "by city", "per location"], "clause": "WITH"},
                    "having": {"keywords": ["having"], "clause": "WITH ... WHERE"},
                    "sort": {"keywords": ["order by", "sort by", "ascending", "descending"], "clause": "ORDER BY"},
                    "limit": {"keywords": ["top N", "bottom N", "limit"], "clause": "LIMIT"}
                },
                "programming": {
                    "conditional": {"keywords": ["if", "when", "case"], "cypher": "CASE WHEN"},
                    "loop": {"keywords": ["for each", "map", "apply to all"], "cypher": "WITH ... UNWIND"}
                }
            }
        }

    def process_query(self, query: str) -> Dict:
        """
        Main query processing pipeline

        Steps:
        1. LLM analyzes query and determines intent
        2. Check if data exists in graph OR needs calculation
        3. If calculation needed, identify operation type
        4. Generate appropriate Cypher (retrieval or computation)
        5. Execute and format result
        """

        # Step 1: LLM understanding
        understanding = self._understand_query_with_operations(query)

        if understanding.get('error'):
            return {'status': 'error', 'message': understanding['error']}

        # Step 2: Determine if data exists or needs calculation
        data_strategy = self._determine_data_strategy(understanding)

        # Step 3: Generate Cypher based on strategy
        cypher_query = self._generate_cypher_for_strategy(understanding, data_strategy)

        # Step 4: Execute
        result = self._execute_query(cypher_query)

        # Step 5: Format response
        return self._format_response(query, understanding, data_strategy, cypher_query, result)

    def _understand_query_with_operations(self, query: str) -> Dict:
        """
        Enhanced LLM understanding that includes operation detection

        LLM now detects:
        - Layer (0, 1, 2)
        - Dimension
        - Operation type (RETRIEVAL, DIVISION, AGGREGATION, FILTER, etc.)
        - Operation parameters
        """

        prompt = f"""You are a knowledge graph query analyzer with dimensional analysis capabilities.

KNOWLEDGE GRAPH SCHEMA (with operations):
{json.dumps(self.kg_schema, indent=2)}

USER QUERY: "{query}"

**IMPORTANT - DYNAMIC LAYER CREATION:**
If the query asks for a metric NOT in the known_metrics list, you CAN create it dynamically!

Examples of DYNAMIC creation:
- "What is cost per month?" → CF/T (not predefined, but valid!) → Create dynamically
- "Show me area per time" → L²/T (unusual, but valid!) → Create dynamically
- "Calculate units per area" → U/L² (valid dimension!) → Create dynamically

Rules for dynamic creation:
1. ANY L0÷L0 division creates a valid Layer 1 metric
2. Determine the components (numerator and denominator from L0)
3. Calculate the unit (e.g., "INR/month", "sqft/Units", etc.)
4. Generate descriptive name (e.g., "Cost Per Month", "Area Per Time")

CRITICAL: You must determine if the query requires:
1. **RETRIEVAL**: Data exists in graph (Layer 0 stored, Layer 2 stored)
2. **DIVISION**: Data needs calculation via division (Layer 1 = L0÷L0)
3. **AGGREGATION**: Statistical operation (mean, median, etc.)
4. **FILTER**: WHERE clause needed
5. **GROUP_BY**: Grouping operation
6. **COMBINATION**: Multiple operations

EXAMPLES:

Query: "Calculate the average of project size"
→ operation: "AGGREGATION", layer: 0, dimension: "U", aggregation: "mean"

Query: "What is the PSF?"
→ operation: "DIVISION", layer: 1, dimension: "CF/L²", components: {{num: "CF", den: "L²"}}

Query: "Top 5 projects by revenue"
→ operation: "FILTER", filter_type: "top_n", value: 5, sort_field: "totalRevenue"

Query: "Average PSF by city"
→ operation: "COMBINATION", operations: ["DIVISION", "GROUP_BY", "AGGREGATION"]

Query: "Projects with revenue > 100 crore"
→ operation: "FILTER", condition: ">100", field: "totalRevenue"

Return ONLY valid JSON:
{{
  "layer": 0,
  "target_attribute": "...",
  "dimension": "U",
  "operation": "AGGREGATION|DIVISION|FILTER|GROUP_BY|COMBINATION",

  // For DIVISION operations
  "division_components": {{
    "numerator": "CF",
    "numerator_field": "totalRevenue",
    "denominator": "L²",
    "denominator_field": "totalSaleableArea"
  }},

  // For AGGREGATION operations
  "aggregation": "mean|median|sum|stdev|etc",

  // For FILTER operations
  "filter_type": "top_n|bottom_n|greater_than|less_than|between",
  "filter_value": 5,
  "filter_condition": ">100",

  // For GROUP_BY operations
  "group_by": "city|location|developer",

  // For SQL operations
  "sql_operations": ["WHERE", "GROUP BY", "HAVING", "ORDER BY"],

  // General
  "neo4j_field": "totalUnits",
  "unit": "Units",
  "description": "..."
}}

If you cannot understand: {{"error": "..."}}
"""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Clean markdown
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            understanding = json.loads(response_text)
            return understanding

        except Exception as e:
            return {'error': f'LLM failed to understand query: {str(e)}'}

    def _determine_data_strategy(self, understanding: Dict) -> Dict:
        """
        Determine if data exists or needs calculation

        Returns strategy:
        - type: "RETRIEVE" | "CALCULATE_DIVISION" | "CALCULATE_AGGREGATION" | etc.
        - layer: 0|1|2
        - operation: operation details
        """
        operation = understanding.get('operation')
        layer = understanding.get('layer')

        strategy = {
            'type': None,
            'layer': layer,
            'requires_calculation': False
        }

        if operation == 'RETRIEVAL':
            strategy['type'] = 'RETRIEVE'
            strategy['requires_calculation'] = False

        elif operation == 'DIVISION':
            # Layer 1 metrics created by division
            strategy['type'] = 'CALCULATE_DIVISION'
            strategy['requires_calculation'] = True
            strategy['formula'] = f"{understanding['division_components']['numerator']} ÷ {understanding['division_components']['denominator']}"

        elif operation == 'AGGREGATION':
            # Statistical operations
            strategy['type'] = 'CALCULATE_AGGREGATION'
            strategy['requires_calculation'] = True
            strategy['aggregation_func'] = understanding.get('aggregation')

        elif operation == 'FILTER':
            # SQL WHERE
            strategy['type'] = 'FILTER'
            strategy['requires_calculation'] = False

        elif operation == 'GROUP_BY':
            # SQL GROUP BY
            strategy['type'] = 'GROUP_BY_AGGREGATE'
            strategy['requires_calculation'] = True

        elif operation == 'COMBINATION':
            # Multiple operations
            strategy['type'] = 'COMBINATION'
            strategy['requires_calculation'] = True
            strategy['operations'] = understanding.get('sql_operations', [])

        return strategy

    def _generate_cypher_for_strategy(self, understanding: Dict, strategy: Dict) -> Dict:
        """
        Generate Cypher based on data strategy

        Different strategies require different Cypher patterns
        """
        strategy_type = strategy['type']

        if strategy_type == 'RETRIEVE':
            # Simple retrieval
            field = understanding.get('neo4j_field')
            return {
                'query': f"""
                MATCH (p:Project)
                WHERE p.{field} IS NOT NULL
                RETURN p.projectName AS project,
                       p.{field} AS value,
                       collect(p.{field}) AS all_values
                """,
                'params': {}
            }

        elif strategy_type == 'CALCULATE_DIVISION':
            # Division creates Layer 1 (DYNAMIC - any L0÷L0 is valid!)
            div_comp = understanding.get('division_components', {})
            num_field = div_comp.get('numerator_field')
            den_field = div_comp.get('denominator_field')
            num_dim = div_comp.get('numerator')
            den_dim = div_comp.get('denominator')

            # Auto-generate metadata for new dimension
            new_dimension = self._create_dynamic_dimension(num_dim, den_dim, num_field, den_field)

            return {
                'query': f"""
                MATCH (p:Project)
                WHERE p.{num_field} IS NOT NULL AND p.{den_field} IS NOT NULL
                WITH p,
                     p.{num_field} / p.{den_field} AS calculated_value,
                     '{new_dimension['symbol']}' AS dimension_symbol,
                     '{new_dimension['name']}' AS dimension_name,
                     '{new_dimension['unit']}' AS dimension_unit
                RETURN p.projectName AS project,
                       calculated_value AS value,
                       collect(calculated_value) AS all_values,
                       avg(calculated_value) AS mean,
                       stdev(calculated_value) AS stdev,
                       min(calculated_value) AS min_value,
                       max(calculated_value) AS max_value,
                       dimension_symbol AS created_dimension,
                       dimension_name AS created_metric_name,
                       dimension_unit AS created_unit
                LIMIT 1
                """,
                'params': {},
                'dynamic_dimension': new_dimension
            }

        elif strategy_type == 'CALCULATE_AGGREGATION':
            # Statistical aggregation
            field = understanding.get('neo4j_field')
            agg = understanding.get('aggregation', 'mean')

            agg_map = {
                'mean': 'avg',
                'median': 'percentileCont',
                'sum': 'sum',
                'count': 'count',
                'min': 'min',
                'max': 'max',
                'stdev': 'stdev'
            }

            cypher_agg = agg_map.get(agg, 'avg')

            if agg == 'median':
                cypher_agg = f'percentileCont(p.{field}, 0.5)'
            else:
                cypher_agg = f'{cypher_agg}(p.{field})'

            return {
                'query': f"""
                MATCH (p:Project)
                WHERE p.{field} IS NOT NULL
                RETURN {cypher_agg} AS result,
                       count(p) AS count,
                       collect(p.{field}) AS values,
                       collect(p.projectName) AS projects
                """,
                'params': {}
            }

        elif strategy_type == 'FILTER':
            # SQL WHERE clause
            field = understanding.get('neo4j_field')
            filter_type = understanding.get('filter_type')
            filter_value = understanding.get('filter_value')
            filter_condition = understanding.get('filter_condition', '')

            if filter_type == 'top_n':
                return {
                    'query': f"""
                    MATCH (p:Project)
                    WHERE p.{field} IS NOT NULL
                    RETURN p.projectName AS project, p.{field} AS value
                    ORDER BY p.{field} DESC
                    LIMIT {filter_value}
                    """,
                    'params': {}
                }
            elif filter_type == 'greater_than':
                threshold = filter_condition.replace('>', '').strip()
                return {
                    'query': f"""
                    MATCH (p:Project)
                    WHERE p.{field} > {threshold}
                    RETURN p.projectName AS project, p.{field} AS value
                    ORDER BY p.{field} DESC
                    """,
                    'params': {}
                }

        elif strategy_type == 'GROUP_BY_AGGREGATE':
            # SQL GROUP BY
            field = understanding.get('neo4j_field')
            group_by = understanding.get('group_by', 'city')
            agg = understanding.get('aggregation', 'mean')

            agg_map = {'mean': 'avg', 'sum': 'sum', 'count': 'count', 'min': 'min', 'max': 'max'}
            cypher_agg = agg_map.get(agg, 'avg')

            return {
                'query': f"""
                MATCH (p:Project)
                WHERE p.{field} IS NOT NULL
                RETURN p.{group_by} AS group_value,
                       {cypher_agg}(p.{field}) AS result,
                       count(p) AS count
                ORDER BY result DESC
                """,
                'params': {}
            }

        return {'query': 'MATCH (p:Project) RETURN count(p)', 'params': {}}

    def _create_dynamic_dimension(self, numerator: str, denominator: str,
                                  num_field: str, den_field: str) -> Dict:
        """
        Dynamically create a new Layer 1 dimension on-the-fly

        Args:
            numerator: Dimension symbol (e.g., "CF")
            denominator: Dimension symbol (e.g., "T")
            num_field: Neo4j field name (e.g., "totalRevenue")
            den_field: Neo4j field name (e.g., "projectDuration")

        Returns:
            Dict with dimension metadata (symbol, name, unit, formula, layer)

        Examples:
            CF ÷ T → {"symbol": "CF/T", "name": "Cash Flow Per Month", "unit": "INR/month"}
            L² ÷ U → {"symbol": "L²/U", "name": "Area Per Unit", "unit": "sqft/unit"}
            U ÷ L² → {"symbol": "U/L²", "name": "Unit Density", "unit": "units/sqft"}
        """

        # Get base dimension info
        num_info = self.kg_schema['layers']['0']['dimensions'].get(numerator, {})
        den_info = self.kg_schema['layers']['0']['dimensions'].get(denominator, {})

        # Calculate new dimension symbol
        new_symbol = f"{numerator}/{denominator}"

        # Auto-generate descriptive name
        num_name = num_info.get('name', numerator)
        den_name = den_info.get('name', denominator)
        new_name = f"{num_name} Per {den_name}"

        # Calculate unit
        num_unit = num_info.get('unit', '')
        den_unit = den_info.get('unit', '')
        new_unit = f"{num_unit}/{den_unit}" if num_unit and den_unit else ""

        # Simplify common units
        unit_simplifications = {
            'INR/sqft': 'INR/sqft',  # PSF
            'INR/Units': 'INR/unit',  # ASP
            'Units/months': 'units/month',  # Velocity
            'sqft/Units': 'sqft/unit',  # Area per unit
            'INR/months': 'INR/month',  # Revenue rate
            'months/Units': 'months/unit',  # Time per unit
        }
        new_unit = unit_simplifications.get(new_unit, new_unit)

        # Create dimension metadata
        new_dimension = {
            'symbol': new_symbol,
            'name': new_name,
            'unit': new_unit,
            'formula': f"{num_field} ÷ {den_field}",
            'layer': 1,  # L0÷L0 always creates Layer 1
            'components': {
                'numerator': numerator,
                'denominator': denominator,
                'numerator_field': num_field,
                'denominator_field': den_field
            },
            'created_dynamically': True,
            'timestamp': str(__import__('datetime').datetime.now())
        }

        # Store in schema for future use (optional caching)
        if 'dynamic_metrics' not in self.kg_schema['layers']['1']:
            self.kg_schema['layers']['1']['dynamic_metrics'] = {}

        self.kg_schema['layers']['1']['dynamic_metrics'][new_symbol] = new_dimension

        return new_dimension

    def _execute_query(self, cypher_query: Dict) -> Optional[Dict]:
        """Execute Cypher on Neo4j"""
        try:
            with self.driver.session() as session:
                result = session.run(cypher_query['query'], cypher_query['params'])

                # Handle different result structures
                records = list(result)
                if not records:
                    return None

                # Single aggregate result
                if len(records) == 1 and 'result' in records[0].keys():
                    return dict(records[0])

                # Multiple rows (GROUP BY, FILTER, etc.)
                return {'rows': [dict(record) for record in records]}

        except Exception as e:
            return {'error': f'Query execution failed: {str(e)}'}

    def _format_response(self, original_query: str, understanding: Dict,
                        strategy: Dict, cypher_query: Dict, result: Optional[Dict]) -> Dict:
        """Format final response with operation details"""

        if not result or 'error' in result:
            return {
                'status': 'error',
                'message': result.get('error', 'No data found') if result else 'Query failed'
            }

        operation = understanding.get('operation')
        layer = understanding.get('layer', 0)

        response = {
            'status': 'success',
            'query': original_query,
            'understanding': {
                'layer': layer,
                'dimension': understanding.get('dimension'),
                'operation': operation,
                'description': understanding.get('description', '')
            },
            'data_strategy': {
                'type': strategy['type'],
                'calculated': strategy.get('requires_calculation', False),
                'formula': strategy.get('formula', None)
            },
            'provenance': {
                'dataSource': 'Liases Foras',
                'layer': f'Layer {layer}',
                'cypherQuery': cypher_query['query'],
                'llmModel': 'gemini-1.5-flash'
            }
        }

        # Add dynamic dimension info if created
        if 'dynamic_dimension' in cypher_query:
            response['dynamic_dimension'] = {
                'symbol': cypher_query['dynamic_dimension']['symbol'],
                'name': cypher_query['dynamic_dimension']['name'],
                'unit': cypher_query['dynamic_dimension']['unit'],
                'formula': cypher_query['dynamic_dimension']['formula'],
                'layer': cypher_query['dynamic_dimension']['layer'],
                'created_on_the_fly': True,
                'note': 'This dimension was created dynamically based on your query!'
            }

        # Add result data
        if 'rows' in result:
            # Multiple rows (GROUP BY, FILTER, etc.)
            response['result'] = {
                'type': 'table',
                'rows': result['rows'],
                'count': len(result['rows'])
            }
        else:
            # Single aggregate result
            result_value = result.get('result')
            if isinstance(result_value, float):
                result_value = round(result_value, 2)

            response['result'] = {
                'value': result_value,
                'unit': understanding.get('unit', ''),
                'text': f"{result_value} {understanding.get('unit', '')}"
            }

            # Add calculation details if applicable
            if 'values' in result and 'count' in result:
                response['calculation'] = {
                    'breakdown': [
                        {'project': p, 'value': v}
                        for p, v in zip(result.get('projects', []), result.get('values', []))
                    ],
                    'count': result.get('count', 0)
                }

        return response


# FastAPI endpoint
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter()


class QueryRequest(BaseModel):
    query: str


@router.post("/api/query/unified")
async def unified_query_processor(request: QueryRequest):
    """
    Unified query processor with dimensional analysis

    Supports ALL operations:
    - Basic math: sum, difference, multiplication, DIVISION (creates layers!)
    - Statistical: mean, median, stdev, quartiles, distribution
    - SQL: WHERE, GROUP BY, HAVING, ORDER BY, LIMIT
    - Programming: IF/THEN, loops, conditional logic

    Examples:
    - "Calculate average project size" → AGGREGATION
    - "What is the PSF?" → DIVISION (CF÷L² creates Layer 1)
    - "Top 5 by revenue" → FILTER
    - "Average PSF by city" → COMBINATION (division + grouping)
    """

    from app.config import settings
    from app.db.neo4j_client import get_neo4j_driver

    try:
        driver = get_neo4j_driver()
        processor = UnifiedQueryProcessor(
            gemini_api_key=settings.GEMINI_API_KEY,
            neo4j_driver=driver
        )

        result = processor.process_query(request.query)

        if result['status'] == 'error':
            raise HTTPException(status_code=400, detail=result['message'])

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
