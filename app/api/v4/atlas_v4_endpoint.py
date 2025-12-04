"""
ATLAS v4 API Endpoint

FastAPI endpoint for the LangGraph-based ATLAS v4 implementation.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
import uuid

from app.services.atlas_v4_langgraph_service import execute_atlas_v4_query


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class AtlasV4Request(BaseModel):
    """Request model for ATLAS v4 query."""

    question: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="Natural language query about real estate data",
        examples=["Why is absorption rate low in Chakan?"]
    )

    region: Optional[str] = Field(
        None,
        max_length=100,
        description="Optional region filter (e.g., 'Pune', 'Chakan')",
        examples=["Pune", "Chakan", "Mumbai"]
    )

    project_id: Optional[int] = Field(
        None,
        ge=1,
        description="Optional project ID filter",
        examples=[1, 2, 3]
    )

    session_id: Optional[str] = Field(
        None,
        description="Optional session ID for tracking multi-turn conversations"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "question": "What is the average PSF in Chakan and how does it compare to Pune?",
                "region": "Chakan",
                "project_id": None,
                "session_id": None
            }
        }


# ============================================================================
# ROUTER
# ============================================================================

router = APIRouter(
    prefix="/api/qa",
    tags=["ATLAS v4 - LangGraph"]
)


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post(
    "/question/v4",
    summary="ATLAS v4 - LangGraph Query Endpoint",
    description="""
    Execute a natural language query using ATLAS v4 (LangGraph implementation).

    **Features:**
    - Semantic intent classification (6 categories)
    - Dynamic tool sequencing based on query
    - Multi-agent orchestration (6 specialized agents)
    - 3-part mandatory output: ANALYSIS + INSIGHTS + RECOMMENDATIONS
    - Iterative refinement with loop-back (max 10 iterations)
    - Pydantic validation for output structure

    **Agents:**
    1. Intent Agent - Semantic classification
    2. Planning Agent - Dynamic tool sequencing
    3. Data Agent - Knowledge Graph L0 access
    4. Calculator Agent - L1/L2 metric calculations
    5. Insight Agent - VectorDB semantic search
    6. Synthesizer Agent - 3-part output generation

    **Example Query:**
    ```json
    {
      "question": "Why is absorption rate low in Chakan?",
      "region": "Chakan"
    }
    ```

    **Response Structure:**
    - `analysis`: What the data shows
    - `insights`: Why things are the way they are
    - `recommendations`: What to do about it (for_developers, for_investors, timing, risks)
    - `metadata`: Execution metadata (confidence, iterations, tool_calls, plan)
    """,
    response_description="Structured response with ANALYSIS + INSIGHTS + RECOMMENDATIONS"
)
async def atlas_v4_query(request: AtlasV4Request):
    """
    Execute ATLAS v4 query using LangGraph.

    Args:
        request: AtlasV4Request with question, optional region/project_id/session_id

    Returns:
        Dict with analysis, insights, recommendations, and metadata

    Raises:
        HTTPException: If query execution fails
    """

    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())

        # Execute query
        response = await execute_atlas_v4_query(
            query=request.question,
            region=request.region,
            project_id=request.project_id,
            session_id=session_id
        )

        # Add session_id to response
        response["session_id"] = session_id

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error executing ATLAS v4 query: {str(e)}"
        )


@router.get(
    "/v4/health",
    summary="ATLAS v4 Health Check",
    description="Check if ATLAS v4 service is operational"
)
async def v4_health_check():
    """
    Health check endpoint for ATLAS v4.

    Returns:
        Dict with status and version info
    """
    return {
        "status": "healthy",
        "version": "v4",
        "implementation": "LangGraph",
        "agents": [
            "intent_agent",
            "planning_agent",
            "data_agent",
            "calculator_agent",
            "insight_agent",
            "synthesizer_agent"
        ],
        "features": [
            "Semantic intent classification",
            "Dynamic tool sequencing",
            "Multi-agent orchestration",
            "3-part output (ANALYSIS + INSIGHTS + RECOMMENDATIONS)",
            "Iterative refinement with loop-back",
            "Pydantic validation"
        ]
    }


@router.get(
    "/v4/intents",
    summary="List Available Intent Categories",
    description="Get list of intent categories that ATLAS v4 can classify"
)
async def list_intents():
    """
    List available intent categories.

    Returns:
        Dict with intent categories and descriptions
    """
    return {
        "intents": [
            {
                "name": "DATA_RETRIEVAL",
                "description": "Simple data extraction queries",
                "examples": [
                    "What is the PSF of Project X?",
                    "How many units in this project?",
                    "Show me all projects in Chakan"
                ]
            },
            {
                "name": "CALCULATION",
                "description": "Metric calculation queries",
                "examples": [
                    "Calculate absorption rate for Project X",
                    "What is the sales velocity?",
                    "Compute IRR for this cash flow"
                ]
            },
            {
                "name": "COMPARISON",
                "description": "Comparative analysis queries",
                "examples": [
                    "Compare PSF of Chakan vs Pune",
                    "How does Project X compare to market average?",
                    "Show me best vs worst performing projects"
                ]
            },
            {
                "name": "INSIGHT",
                "description": "Causal analysis and 'why' questions",
                "examples": [
                    "Why is absorption rate low in Chakan?",
                    "What factors drive pricing in this area?",
                    "Why is this project performing poorly?"
                ]
            },
            {
                "name": "STRATEGIC",
                "description": "Strategic decision-making queries",
                "examples": [
                    "Should I invest in Chakan?",
                    "What is the best product mix for this project?",
                    "Optimize unit mix to maximize IRR"
                ]
            },
            {
                "name": "CONTEXT_ENRICHMENT",
                "description": "Location intelligence and context queries",
                "examples": [
                    "What is nearby this project?",
                    "Show me map and distances",
                    "What's the air quality in this area?"
                ]
            }
        ]
    }
