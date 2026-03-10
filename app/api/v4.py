"""
ATLAS v4 API - LangGraph Hexagonal Architecture

This is the production v4 endpoint that uses the LangGraph orchestrator
with hexagonal architecture (ports + adapters pattern).

Features:
- Intent classification (objective/analytical/financial)
- Vector DB semantic search for attributes
- Knowledge Graph entity resolution
- Multi-turn conversation support
- Deterministic financial calculations
- Comprehensive provenance tracking
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from app.orchestration.langgraph_orchestrator import get_orchestrator
import time

# Create router
router = APIRouter(prefix="/api/v4", tags=["ATLAS v4"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ConversationMessage(BaseModel):
    """Single message in conversation history"""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: Optional[str] = None


class QueryRequest(BaseModel):
    """Request model for v4 query endpoint"""
    query: str = Field(..., description="Natural language query")
    session_id: Optional[str] = Field(default="default", description="Session ID for multi-turn conversations")
    conversation_history: Optional[List[ConversationMessage]] = Field(default=None, description="Previous conversation turns")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "query": "What is the total units for Sara City?",
                    "session_id": "user_123"
                },
                {
                    "query": "Calculate IRR for Sara City",
                    "session_id": "user_123",
                    "conversation_history": [
                        {"role": "user", "content": "Tell me about Sara City"},
                        {"role": "assistant", "content": "Sara City is..."}
                    ]
                }
            ]
        }


class ProvenanceInfo(BaseModel):
    """Provenance trail for answer"""
    data_sources: List[str]
    lf_pillars: List[str] = []
    lf_data_version: str = "Q3_FY25"
    calculation_methods: List[str] = []
    timestamp: str
    layer0_inputs: List[str] = []
    layer1_intermediates: List[str] = []
    layer2_dependencies: List[str] = []
    assumptions: List[str] = []


class QueryResponse(BaseModel):
    """Response model for v4 query endpoint"""
    answer: str = Field(..., description="Natural language answer with provenance markers")
    intent: str = Field(..., description="Classified intent: objective, analytical, or financial")
    subcategory: Optional[str] = Field(default=None, description="Specific subcategory within intent")
    provenance: Optional[ProvenanceInfo] = Field(default=None, description="Full provenance trail")
    execution_path: List[str] = Field(..., description="List of nodes executed")
    execution_time_ms: float = Field(..., description="Total execution time in milliseconds")
    next_action: str = Field(..., description="Next action: answer or gather_parameters")
    clarification_question: Optional[str] = Field(default=None, description="Question if parameters missing")
    session_id: str = Field(..., description="Session ID for continuation")

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Sara City has 3,018 units. [DIRECT - KG]\n\nThis represents the total number of residential units...",
                "intent": "objective",
                "subcategory": "direct_retrieval",
                "provenance": {
                    "data_sources": ["Knowledge Graph", "Vector DB (Schema)"],
                    "lf_pillars": ["1.1"],
                    "timestamp": "2025-01-15T10:30:00Z",
                    "layer0_inputs": ["Total Units"]
                },
                "execution_path": ["intent_classifier", "attribute_resolver", "entity_resolver", "kg_query_planner", "kg_executor", "answer_composer"],
                "execution_time_ms": 450.5,
                "next_action": "answer",
                "session_id": "user_123"
            }
        }


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """
    Execute natural language query through LangGraph orchestrator

    This endpoint routes queries through the hexagonal architecture with:
    - Intent classification (LLM)
    - Attribute resolution (Vector DB semantic search)
    - Entity resolution (KG fuzzy matching)
    - Query planning (LLM)
    - Data retrieval (KG - single source of truth)
    - Computation (deterministic scipy, NOT LLM)
    - Answer composition (LLM with provenance)

    **Three Query Types:**
    1. **Objective**: Direct retrieval (e.g., "What is the total units for Sara City?")
    2. **Analytical**: Aggregation/comparison (e.g., "Average sold % in Chakan?")
    3. **Financial**: IRR/NPV calculations (e.g., "Calculate IRR for Sara City")

    **Multi-Turn Support:**
    For financial queries missing parameters, returns clarification_question.
    Include conversation_history in next request to continue.

    Args:
        request: QueryRequest with query, session_id, and optional conversation_history

    Returns:
        QueryResponse with answer, provenance, and execution metadata

    Raises:
        HTTPException: If orchestrator initialization or execution fails
    """
    try:
        # Get orchestrator instance
        orchestrator = get_orchestrator()

        # Convert conversation history to dict format
        conv_history = None
        if request.conversation_history:
            conv_history = [msg.dict() for msg in request.conversation_history]

        # Execute query
        response = orchestrator.query(
            query=request.query,
            session_id=request.session_id,
            conversation_history=conv_history
        )

        # Convert provenance to model if present
        provenance_model = None
        if response.get('provenance'):
            prov = response['provenance']
            provenance_model = ProvenanceInfo(
                data_sources=prov.get('data_sources', []),
                lf_pillars=prov.get('lf_pillars', []),
                lf_data_version=prov.get('lf_data_version', 'Q3_FY25'),
                calculation_methods=prov.get('calculation_methods', []),
                timestamp=prov.get('timestamp', ''),
                layer0_inputs=prov.get('layer0_inputs', []),
                layer1_intermediates=prov.get('layer1_intermediates', []),
                layer2_dependencies=prov.get('layer2_dependencies', []),
                assumptions=prov.get('assumptions', [])
            )

        # Build response
        return QueryResponse(
            answer=response.get('answer', 'No answer generated'),
            intent=response.get('intent', 'unknown'),
            subcategory=response.get('subcategory'),
            provenance=provenance_model,
            execution_path=response.get('execution_path', []),
            execution_time_ms=response.get('execution_time_ms', 0),
            next_action=response.get('next_action', 'answer'),
            clarification_question=response.get('clarification_question'),
            session_id=response.get('session_id', request.session_id)
        )

    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        raise HTTPException(
            status_code=500,
            detail=f"Orchestrator execution failed: {error_detail}"
        )


@router.get("/query/{query_text}")
async def execute_query_get(query_text: str, session_id: str = "default"):
    """
    Execute query via GET request (convenience endpoint)

    Args:
        query_text: The natural language query
        session_id: Optional session ID for multi-turn conversations

    Returns:
        Query response with answer and metadata
    """
    request = QueryRequest(query=query_text, session_id=session_id)
    return await execute_query(request)


@router.get("/info")
async def get_v4_info():
    """
    Get information about ATLAS v4 architecture

    Returns:
        Architecture details, supported query types, and flow diagram
    """
    return {
        "version": "4.0",
        "name": "ATLAS v4 - LangGraph Hexagonal Architecture",
        "description": "Query orchestrator using LangGraph state machine with ports & adapters",
        "architecture": {
            "pattern": "Hexagonal (Ports & Adapters)",
            "orchestration": "LangGraph State Machine",
            "layers": {
                "vector_db": {
                    "purpose": "Attribute schema understanding (WHAT attributes mean)",
                    "implementation": "ChromaDB + SentenceTransformers",
                    "data": "36 enriched attributes with embeddings"
                },
                "knowledge_graph": {
                    "purpose": "Data truth (WHAT values are) - SINGLE SOURCE OF TRUTH",
                    "implementation": "Neo4j via DataService wrapper",
                    "data": "Project data with fuzzy entity matching"
                },
                "llm": {
                    "purpose": "Intelligence (HOW to interpret) - NO data invention",
                    "implementation": "Gemini 2.0-flash-exp",
                    "capabilities": [
                        "Intent classification",
                        "Entity extraction",
                        "Query planning",
                        "Answer composition with provenance"
                    ]
                }
            },
            "nodes": [
                {"id": 1, "name": "intent_classifier", "purpose": "Classify intent (objective/analytical/financial)"},
                {"id": 2, "name": "attribute_resolver", "purpose": "Semantic search in Vector DB"},
                {"id": 3, "name": "entity_resolver", "purpose": "Fuzzy matching in KG"},
                {"id": 4, "name": "kg_query_planner", "purpose": "Generate structured query plan"},
                {"id": 5, "name": "kg_executor", "purpose": "Retrieve data from KG"},
                {"id": 6, "name": "parameter_gatherer", "purpose": "Check for missing params (financial queries)"},
                {"id": 7, "name": "computation", "purpose": "Deterministic calculations (scipy)"},
                {"id": 8, "name": "answer_composer", "purpose": "Natural language with provenance"}
            ]
        },
        "query_types": {
            "objective": {
                "description": "Direct retrieval of specific values",
                "example": "What is the total units for Sara City?",
                "flow": "intent → attribute → entity → plan → execute → answer",
                "skips": ["parameter_gatherer", "computation"]
            },
            "analytical": {
                "description": "Aggregation, comparison, multi-project analysis",
                "example": "What is the average sold % across all Chakan projects?",
                "flow": "intent → attribute → entity → plan → execute → answer",
                "skips": ["parameter_gatherer", "computation"]
            },
            "financial": {
                "description": "Financial calculations (IRR, NPV, payback, sensitivity)",
                "example": "Calculate IRR for Sara City with 12% discount rate",
                "flow": "intent → attribute → entity → plan → execute → parameters → computation → answer",
                "supports_multi_turn": True
            }
        },
        "provenance": {
            "markers": {
                "[DIRECT - KG]": "Value retrieved directly from Knowledge Graph",
                "[COMPUTED]": "Value calculated using deterministic formula (scipy)",
                "[ASSUMED]": "Value based on assumptions"
            },
            "tracking": [
                "Data sources (Vector DB, KG, LLM)",
                "LF pillars (1.1, 2.1, etc.)",
                "Layer 0 inputs (raw dimensions)",
                "Layer 1 intermediates (derived metrics)",
                "Layer 2 dependencies (financial calculations)",
                "Calculation methods (scipy.optimize.newton, etc.)",
                "Assumptions made"
            ]
        },
        "endpoints": {
            "POST /api/v4/query": "Main query endpoint with conversation history support",
            "GET /api/v4/query/{query_text}": "Convenience GET endpoint",
            "GET /api/v4/info": "This endpoint - architecture information",
            "GET /api/v4/test": "Run test queries",
            "GET /api/v4/health": "Health check"
        }
    }


@router.get("/test")
async def run_test_queries():
    """
    Run test queries demonstrating all three query types

    Returns:
        Results from 5 test queries with timing and success status
    """
    orchestrator = get_orchestrator()

    test_queries = [
        {"query": "What is the total units for Sara City?", "type": "objective"},
        {"query": "What is the sold percentage for The Urbana?", "type": "objective"},
        {"query": "What is the average sold % across all Chakan projects?", "type": "analytical"},
        {"query": "Compare sold % between Sara City and The Urbana", "type": "analytical"},
        {"query": "Calculate NPV for Sara City with 12% discount rate", "type": "financial"}
    ]

    results = []
    total_time = 0

    for test in test_queries:
        try:
            start = time.time()
            response = orchestrator.query(
                query=test["query"],
                session_id="test_session"
            )
            exec_time = (time.time() - start) * 1000
            total_time += exec_time

            results.append({
                "query": test["query"],
                "expected_type": test["type"],
                "actual_intent": response.get('intent'),
                "success": response.get('answer') is not None,
                "execution_path": response.get('execution_path', []),
                "execution_time_ms": exec_time,
                "next_action": response.get('next_action'),
                "has_answer": bool(response.get('answer'))
            })
        except Exception as e:
            results.append({
                "query": test["query"],
                "expected_type": test["type"],
                "success": False,
                "error": str(e)
            })

    return {
        "test_results": results,
        "summary": {
            "total_queries": len(test_queries),
            "successful": sum(1 for r in results if r.get("success", False)),
            "failed": sum(1 for r in results if not r.get("success", False)),
            "total_execution_time_ms": total_time,
            "avg_execution_time_ms": total_time / len(test_queries) if test_queries else 0
        }
    }


@router.get("/health")
async def health_check():
    """
    Health check for ATLAS v4

    Returns:
        Status of orchestrator and all adapters
    """
    try:
        orchestrator = get_orchestrator()

        # Check adapters
        adapter_status = {}

        try:
            # Vector DB adapter
            orchestrator.vector_db.search_attributes("test", k=1)
            adapter_status["vector_db"] = "healthy"
        except:
            adapter_status["vector_db"] = "unhealthy"

        try:
            # KG adapter
            orchestrator.kg.get_all_projects()
            adapter_status["knowledge_graph"] = "healthy"
        except:
            adapter_status["knowledge_graph"] = "unhealthy"

        try:
            # LLM adapter
            orchestrator.llm.classify_intent("test query")
            adapter_status["llm"] = "healthy"
        except:
            adapter_status["llm"] = "unhealthy"

        overall_healthy = all(status == "healthy" for status in adapter_status.values())

        return {
            "status": "healthy" if overall_healthy else "degraded",
            "orchestrator": "initialized",
            "adapters": adapter_status,
            "langgraph": "compiled",
            "nodes": 8,
            "version": "4.0"
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
