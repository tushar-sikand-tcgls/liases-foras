"""
Hexagonal Architecture API Endpoints

FastAPI endpoints that use the QueryOrchestrator (LangGraph state machine)
to route queries through the hexagonal architecture with ports and adapters.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Any, Dict
from app.orchestration import QueryOrchestrator

# Create router
router = APIRouter(prefix="/api/hexagonal", tags=["Hexagonal Architecture"])

# Initialize orchestrator (singleton pattern)
_orchestrator: Optional[QueryOrchestrator] = None

def get_orchestrator() -> QueryOrchestrator:
    """Get or create the query orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = QueryOrchestrator()
    return _orchestrator


# Request/Response models
class QueryRequest(BaseModel):
    """Request model for query execution"""
    query: str
    context: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is the PSF Gap of Sara City?",
                "context": {
                    "location": "Pune",
                    "developer": "Sara Group"
                }
            }
        }


class QueryResponse(BaseModel):
    """Response model for query execution"""
    query: str
    query_type: Optional[str]
    result: Optional[Any]
    error: Optional[str]
    execution_path: list[str]
    metadata: Dict[str, Any]

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is the PSF Gap of Sara City?",
                "query_type": "calculation",
                "result": {
                    "attribute": "PSF Gap",
                    "value": 1796.0,
                    "unit": "INR/sqft",
                    "dimension": "C/L²",
                    "formula": "CurrentPSF−LaunchPSF"
                },
                "error": None,
                "execution_path": ["classify_query", "extract_context", "resolve_attribute", "resolve_project", "execute_calculation", "format_response"],
                "metadata": {
                    "attribute_name": "PSF Gap",
                    "project_name": "Sara City",
                    "location": "Chakan",
                    "aggregation_type": None
                }
            }
        }


# Endpoints

@router.get("/info")
async def get_architecture_info():
    """
    Get information about the hexagonal architecture components

    Returns:
        - Available ports (input/output)
        - Available adapters
        - Query types supported
        - LangGraph workflow description
    """
    return {
        "architecture": "Hexagonal (Ports & Adapters)",
        "orchestration": "LangGraph State Machine",
        "components": {
            "input_ports": [
                {"name": "QueryAttributePort", "description": "Query attribute definitions"},
                {"name": "CalculateFormulaPort", "description": "Execute formula calculations"},
                {"name": "ProjectQueryPort", "description": "Query project data"},
                {"name": "StatisticalAnalysisPort", "description": "Statistical operations across projects"},
                {"name": "DimensionValidationPort", "description": "Validate dimensional consistency"},
            ],
            "output_ports": [
                {"name": "ProjectRepositoryPort", "description": "Project data persistence/retrieval"},
                {"name": "FormulaRepositoryPort", "description": "Formula/attribute definitions storage"},
                {"name": "VectorSearchPort", "description": "Vector-based semantic search"},
                {"name": "ExternalDataSourcePort", "description": "External data sources (Excel, APIs)"},
            ],
            "adapters": [
                {"name": "FormulaServiceAdapter", "wraps": "dynamic_formula_service", "implements": ["QueryAttributePort", "CalculateFormulaPort", "FormulaRepositoryPort"]},
                {"name": "ProjectServiceAdapter", "wraps": "data_service", "implements": ["ProjectQueryPort", "ProjectRepositoryPort"]},
                {"name": "StatisticalAnalysisAdapter", "wraps": "Python statistics", "implements": ["StatisticalAnalysisPort"]},
            ]
        },
        "query_types": [
            {
                "type": "calculation",
                "description": "Calculate or extract single attribute for a project",
                "example": "What is the PSF Gap of Sara City?"
            },
            {
                "type": "statistical",
                "description": "Statistical analysis across multiple projects",
                "example": "What is the average Launch PSF across all projects in Pune?"
            },
            {
                "type": "project_search",
                "description": "Search and list projects by criteria",
                "example": "Show all projects in Chakan"
            },
            {
                "type": "comparison",
                "description": "Compare attributes across projects",
                "example": "Compare PSF of Project A vs Project B"
            }
        ],
        "workflow": {
            "description": "LangGraph state machine with conditional routing",
            "nodes": [
                "classify_query",
                "extract_context",
                "resolve_attribute",
                "resolve_project",
                "resolve_projects_list",
                "execute_calculation",
                "execute_statistical",
                "execute_project_query",
                "format_response"
            ],
            "routing": "Conditional edges based on query type and state"
        }
    }


@router.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """
    Execute a query through the hexagonal architecture orchestrator

    This endpoint routes the query through the LangGraph state machine,
    which classifies the query, extracts context, resolves entities,
    and executes the appropriate operation through the adapters.

    Args:
        request: QueryRequest with query string and optional context

    Returns:
        QueryResponse with result, execution path, and metadata

    Raises:
        HTTPException: If orchestrator initialization fails
    """
    try:
        orchestrator = get_orchestrator()
        response = orchestrator.execute_query(request.query)

        return QueryResponse(**response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Orchestrator error: {str(e)}")


@router.get("/query/{query_text}")
async def execute_query_get(query_text: str):
    """
    Execute a query via GET request (convenience endpoint)

    Args:
        query_text: The query string

    Returns:
        Query result with execution metadata
    """
    request = QueryRequest(query=query_text)
    return await execute_query(request)


@router.get("/test")
async def test_orchestrator():
    """
    Test the orchestrator with sample queries

    Returns:
        Results from 3 test queries demonstrating different query types
    """
    orchestrator = get_orchestrator()

    test_queries = [
        "What is the PSF Gap of Sara City?",
        "What is the average Launch PSF across all projects in Pune?",
        "Show all projects in Chakan"
    ]

    results = []
    for query in test_queries:
        try:
            response = orchestrator.execute_query(query)
            results.append({
                "query": query,
                "query_type": response["query_type"],
                "success": response["error"] is None,
                "execution_path": response["execution_path"],
                "error": response["error"]
            })
        except Exception as e:
            results.append({
                "query": query,
                "success": False,
                "error": str(e)
            })

    return {
        "test_results": results,
        "summary": {
            "total": len(test_queries),
            "successful": sum(1 for r in results if r["success"]),
            "failed": sum(1 for r in results if not r["success"])
        }
    }


@router.get("/health")
async def health_check():
    """
    Health check for the hexagonal architecture

    Returns:
        Status of orchestrator and adapters
    """
    try:
        orchestrator = get_orchestrator()

        return {
            "status": "healthy",
            "orchestrator": "initialized",
            "adapters": {
                "formula_adapter": "ready",
                "project_adapter": "ready",
                "stats_adapter": "ready"
            },
            "langgraph": "compiled"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
