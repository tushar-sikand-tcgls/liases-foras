"""
MCP Query Endpoint: Natural language query execution with LLM orchestration

New Architecture:
- Accepts natural language queries (not structured requests)
- Routes through Orchestrator Service with LLM-driven function calling
- Supports session management and chat history
- Returns LLM-generated responses with analysis and insights
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
from app.models.requests import MCPQueryRequest
from app.models.responses import MCPQueryResponse, ErrorResponse
from app.services.query_router import query_router
from app.services.orchestrator_service import get_orchestrator

router = APIRouter()


# New natural language query request model
class NaturalLanguageQueryRequest(BaseModel):
    """Natural language query request (new architecture)"""
    query: str
    session_id: Optional[str] = None
    project_id: Optional[int] = None
    location: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class NaturalLanguageQueryResponse(BaseModel):
    """Natural language query response (new architecture)"""
    response: str
    session_id: str
    function_calls: List[Dict[str, Any]]
    query_type: str
    metadata: Dict[str, Any]


@router.post("/query/natural", response_model=NaturalLanguageQueryResponse)
def execute_natural_language_query(request: NaturalLanguageQueryRequest):
    """
    Execute natural language query with LLM orchestration (NEW PRIMARY ENDPOINT)

    Uses the new architecture:
    1. Input enrichment (spell check, context extraction)
    2. LLM routing (Gemini decides which functions to call)
    3. Function execution (deterministic calculations or GraphRAG)
    4. LLM commentary (analysis, insights, recommendations)
    5. Chat history update (with auto-compacting)

    Example queries:
    - "Calculate IRR for project 1"
    - "Why is absorption rate low for Sara City?"
    - "Compare top 3 projects by PSF"
    - "What's the market opportunity in Chakan?"
    """
    try:
        # Get orchestrator instance
        orchestrator = get_orchestrator()

        # Process query through orchestrator
        result = orchestrator.process_query(
            query=request.query,
            session_id=request.session_id,
            project_id=request.project_id,
            location=request.location,
            metadata=request.metadata
        )

        return NaturalLanguageQueryResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Query Processing Error",
                "detail": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )


@router.post("/query", response_model=MCPQueryResponse)
def execute_mcp_query(request: MCPQueryRequest):
    """
    Execute MCP query with layer routing (LEGACY ENDPOINT - kept for backwards compatibility)

    Routes query to appropriate layer handler (0-3) and returns result
    with full provenance and data lineage tracking.

    NOTE: New applications should use /query/natural endpoint instead.
    """

    # Generate query ID if not provided
    query_id = request.queryId or str(uuid.uuid4())
    start_time = datetime.utcnow()

    try:
        # Route to appropriate layer handler
        result, provenance, lineage = query_router.route(request)

        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds() * 1000

        # Compute related metrics (if applicable)
        related_metrics = _compute_related_metrics(request, result)

        return MCPQueryResponse(
            queryId=query_id,
            status="success",
            layer=request.layer,
            capability=request.capability,
            result=result,
            provenance=provenance,
            relatedMetrics=related_metrics,
            executionTime_ms=round(execution_time, 2),
            dataLineage=lineage
        )

    except ValueError as e:
        # Handle validation errors
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Validation Error",
                "detail": str(e),
                "queryId": query_id,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )

    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "detail": str(e),
                "queryId": query_id,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )


@router.get("/session/{session_id}")
def get_session_summary(session_id: str):
    """Get summary of a conversation session"""
    try:
        orchestrator = get_orchestrator()
        summary = orchestrator.get_session_summary(session_id)

        if not summary:
            raise HTTPException(
                status_code=404,
                detail={"error": "Session not found", "session_id": session_id}
            )

        return summary

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )


@router.delete("/session/{session_id}")
def delete_session(session_id: str):
    """Delete a conversation session"""
    try:
        orchestrator = get_orchestrator()
        success = orchestrator.delete_session(session_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail={"error": "Session not found", "session_id": session_id}
            )

        return {"status": "deleted", "session_id": session_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )


@router.post("/session/{session_id}/clear")
def clear_session(session_id: str):
    """Clear conversation history for a session"""
    try:
        orchestrator = get_orchestrator()
        success = orchestrator.clear_session(session_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail={"error": "Session not found", "session_id": session_id}
            )

        return {"status": "cleared", "session_id": session_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )


@router.get("/sessions")
def list_sessions():
    """List all active conversation sessions"""
    try:
        orchestrator = get_orchestrator()
        sessions = orchestrator.list_sessions()
        return {"sessions": sessions, "count": len(sessions)}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )


@router.get("/functions")
def get_available_functions():
    """Get list of all available functions for LLM routing"""
    try:
        orchestrator = get_orchestrator()
        functions_summary = orchestrator.get_available_functions()
        return functions_summary

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )


def _compute_related_metrics(request: MCPQueryRequest, result: dict) -> list:
    """
    Compute automatically related metrics from result

    For example, if IRR is calculated, auto-compute NPV
    """
    related = []

    # If IRR was calculated, suggest NPV
    if request.capability == "calculate_irr" and "value" in result:
        related.append({
            "metricName": "NPV_at_12pct_discount",
            "description": "Net Present Value at 12% discount rate",
            "suggestion": "Use calculate_npv with same parameters"
        })

    # If NPV was calculated, suggest IRR
    elif request.capability == "calculate_npv" and "value" in result:
        related.append({
            "metricName": "IRR",
            "description": "Internal Rate of Return",
            "suggestion": "Use calculate_irr with same parameters"
        })

    # If PSF was calculated, suggest ASP
    elif request.capability == "calculate_psf":
        related.append({
            "metricName": "ASP",
            "description": "Average Selling Price per unit",
            "suggestion": "Use calculate_asp to get pricing per unit"
        })

    # If optimization was done, suggest sensitivity analysis
    elif request.capability == "optimize_product_mix":
        related.append({
            "metricName": "SensitivityAnalysis",
            "description": "Sensitivity of IRR/NPV to market changes",
            "suggestion": "Use calculate_sensitivity_analysis for risk assessment"
        })

    return related
