"""
Dynamic Query Handler for Layer 0 Aggregations
Handles natural language queries and calculates results from graph data
"""

from typing import Dict, List, Optional
from neo4j import GraphDatabase
import re


class QueryHandler:
    """Handles dynamic calculations from natural language queries"""

    def __init__(self, driver):
        self.driver = driver

        # Layer 0 dimension mappings
        self.dimension_map = {
            'project size': {'symbol': 'U', 'field': 'totalUnits', 'unit': 'Units'},
            'units': {'symbol': 'U', 'field': 'totalUnits', 'unit': 'Units'},
            'area': {'symbol': 'L²', 'field': 'totalSaleableArea', 'unit': 'sqft'},
            'saleable area': {'symbol': 'L²', 'field': 'totalSaleableArea', 'unit': 'sqft'},
            'duration': {'symbol': 'T', 'field': 'projectDuration', 'unit': 'months'},
            'project duration': {'symbol': 'T', 'field': 'projectDuration', 'unit': 'months'},
            'revenue': {'symbol': 'CF', 'field': 'totalRevenue', 'unit': 'INR'},
            'cost': {'symbol': 'CF', 'field': 'totalCost', 'unit': 'INR'},
            'cash flow': {'symbol': 'CF', 'field': 'totalRevenue', 'unit': 'INR'},
        }

        # Aggregation functions
        self.aggregations = {
            'average': 'avg',
            'avg': 'avg',
            'mean': 'avg',
            'sum': 'sum',
            'total': 'sum',
            'count': 'count',
            'min': 'min',
            'minimum': 'min',
            'max': 'max',
            'maximum': 'max',
        }

    def parse_query(self, query: str) -> Dict:
        """Parse natural language query to extract intent"""

        query_lower = query.lower()

        # Detect aggregation type
        aggregation = None
        for keyword, func in self.aggregations.items():
            if keyword in query_lower:
                aggregation = func
                break

        if not aggregation:
            return {'error': 'No aggregation function detected (average, sum, count, min, max)'}

        # Detect dimension
        dimension_info = None
        for dimension_name, info in self.dimension_map.items():
            if dimension_name in query_lower:
                dimension_info = info
                break

        if not dimension_info:
            return {'error': 'No recognized dimension found in query'}

        # Detect filters (optional)
        filters = self._extract_filters(query_lower)

        return {
            'aggregation': aggregation,
            'dimension': dimension_info,
            'filters': filters,
            'original_query': query
        }

    def _extract_filters(self, query: str) -> Dict:
        """Extract filters from query (location, developer, etc.)"""

        filters = {}

        # Location filter
        location_match = re.search(r'(?:in|at|for)\s+([A-Za-z\s,]+?)(?:\s|$)', query)
        if location_match:
            filters['location'] = location_match.group(1).strip()

        # Developer filter
        developer_match = re.search(r'(?:by|developer)\s+([A-Za-z\s]+?)(?:\s|$)', query)
        if developer_match:
            filters['developer'] = developer_match.group(1).strip()

        return filters

    def execute_query(self, query: str) -> Dict:
        """Execute dynamic query and return calculated result"""

        # Parse query
        parsed = self.parse_query(query)

        if 'error' in parsed:
            return {'status': 'error', 'message': parsed['error']}

        # Build Cypher query
        cypher_query = self._build_cypher(parsed)

        # Execute
        with self.driver.session() as session:
            result = session.run(cypher_query['query'], cypher_query['params'])
            record = result.single()

            if not record:
                return {
                    'status': 'error',
                    'message': 'No data found matching query criteria'
                }

            # Format response
            return self._format_response(parsed, record, cypher_query)

    def _build_cypher(self, parsed: Dict) -> Dict:
        """Build Cypher query from parsed intent"""

        dimension = parsed['dimension']
        aggregation = parsed['aggregation']
        filters = parsed['filters']

        # Base query
        cypher = "MATCH (p:Project) "

        # Add filters
        params = {}
        where_clauses = []

        if 'location' in filters:
            where_clauses.append("p.location CONTAINS $location")
            params['location'] = filters['location']

        if 'developer' in filters:
            where_clauses.append("p.developer = $developer")
            params['developer'] = filters['developer']

        if where_clauses:
            cypher += "WHERE " + " AND ".join(where_clauses) + " "

        # Add aggregation
        field = dimension['field']

        if aggregation == 'avg':
            cypher += f"RETURN avg(p.{field}) AS result, count(p) AS count, collect(p.{field}) AS values, collect(p.name) AS projects"
        elif aggregation == 'sum':
            cypher += f"RETURN sum(p.{field}) AS result, count(p) AS count, collect(p.{field}) AS values, collect(p.name) AS projects"
        elif aggregation == 'count':
            cypher += f"RETURN count(p) AS result, collect(p.name) AS projects"
        elif aggregation == 'min':
            cypher += f"RETURN min(p.{field}) AS result, count(p) AS count, collect(p.{field}) AS values, collect(p.name) AS projects"
        elif aggregation == 'max':
            cypher += f"RETURN max(p.{field}) AS result, count(p) AS count, collect(p.{field}) AS values, collect(p.name) AS projects"

        return {
            'query': cypher,
            'params': params
        }

    def _format_response(self, parsed: Dict, record, cypher_query: Dict) -> Dict:
        """Format query result as structured response"""

        dimension = parsed['dimension']
        aggregation = parsed['aggregation']

        # Get result value
        result_value = record['result']

        # Round if numeric
        if isinstance(result_value, float):
            result_value = round(result_value, 1)

        # Build response
        response = {
            'status': 'success',
            'layer': 0,
            'dimension': dimension['symbol'],
            'aggregation': aggregation,
            'result': {
                'value': result_value,
                'unit': dimension['unit'],
                'text': f"{result_value} {dimension['unit']}"
            },
            'calculation': {
                'formula': self._get_formula(parsed, record),
                'breakdown': self._get_breakdown(record),
                'projectCount': record.get('count', 0)
            },
            'provenance': {
                'dataSource': 'Liases Foras',
                'layer': 'Layer 0',
                'cypherQuery': cypher_query['query'],
                'originalQuery': parsed['original_query']
            }
        }

        return response

    def _get_formula(self, parsed: Dict, record) -> str:
        """Generate formula representation"""

        aggregation = parsed['aggregation']
        dimension = parsed['dimension']
        count = record.get('count', 0)

        if aggregation == 'avg':
            return f"X = Σ {dimension['symbol']} / {count}"
        elif aggregation == 'sum':
            return f"X = Σ {dimension['symbol']}"
        elif aggregation == 'count':
            return f"X = count(Projects)"
        elif aggregation in ['min', 'max']:
            return f"X = {aggregation}({dimension['symbol']})"

        return ""

    def _get_breakdown(self, record) -> List[Dict]:
        """Get breakdown of individual values"""

        if 'values' not in record or 'projects' not in record:
            return []

        values = record['values']
        projects = record['projects']

        breakdown = []
        for i, (project, value) in enumerate(zip(projects, values), 1):
            breakdown.append({
                'projectName': project,
                'value': value,
                'index': i
            })

        return breakdown


# FastAPI endpoint integration
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter()


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    status: str
    result: Optional[Dict] = None
    message: Optional[str] = None


@router.post("/api/query/calculate", response_model=QueryResponse)
async def calculate_query(request: QueryRequest, driver=Depends(get_neo4j_driver)):
    """
    Dynamic calculation endpoint

    Examples:
    - "Calculate the average of project size"
    - "What is the total revenue?"
    - "Find the maximum area in Pune projects"
    """

    handler = QueryHandler(driver)
    result = handler.execute_query(request.query)

    if result['status'] == 'error':
        return QueryResponse(status='error', message=result['message'])

    return QueryResponse(status='success', result=result)


def get_neo4j_driver():
    """Dependency injection for Neo4j driver"""
    # This should be implemented in your main app
    from neo4j import GraphDatabase
    import os

    return GraphDatabase.driver(
        os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
        auth=(os.getenv('NEO4J_USER', 'neo4j'), os.getenv('NEO4J_PASSWORD'))
    )
