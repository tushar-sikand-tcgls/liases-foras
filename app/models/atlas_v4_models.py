"""
ATLAS v4 - Pydantic Models for Validation

Defines output structure validation for the 3-part output format.
"""

from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# RECOMMENDATIONS MODEL
# ============================================================================

class Recommendations(BaseModel):
    """Recommendations section with strategic guidance."""

    for_developers: str = Field(
        ...,
        min_length=50,
        description="Strategic guidance for developers (min 50 chars)"
    )

    for_investors: str = Field(
        ...,
        min_length=50,
        description="Strategic guidance for investors (min 50 chars)"
    )

    timing: str = Field(
        ...,
        min_length=20,
        description="When to act and market inflection points (min 20 chars)"
    )

    risks: List[str] = Field(
        ...,
        min_items=1,
        description="List of identified risks (min 1 risk)"
    )

    @field_validator("risks")
    @classmethod
    def validate_risks(cls, v: List[str]) -> List[str]:
        """Ensure each risk is non-empty."""
        if not all(risk.strip() for risk in v):
            raise ValueError("All risks must be non-empty strings")
        return v


# ============================================================================
# METADATA MODEL
# ============================================================================

class ResponseMetadata(BaseModel):
    """Metadata about query execution."""

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence score (0-1)"
    )

    completeness: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Data completeness score (0-1)"
    )

    iterations: int = Field(
        ...,
        ge=0,
        le=10,
        description="Number of graph iterations (0-10)"
    )

    tool_calls: List[Dict] = Field(
        default_factory=list,
        description="List of tool calls executed"
    )

    plan: List[str] = Field(
        default_factory=list,
        description="Planned tool sequence"
    )

    plan_reasoning: Optional[str] = Field(
        None,
        description="Reasoning behind the plan"
    )


# ============================================================================
# MAIN OUTPUT MODEL
# ============================================================================

class AtlasV4Response(BaseModel):
    """
    Complete ATLAS v4 response with mandatory 3-part structure.

    This is the validated output format that MUST be returned.
    """

    status: Literal["success", "error"] = Field(
        ...,
        description="Execution status"
    )

    query: str = Field(
        ...,
        min_length=1,
        description="Original user query"
    )

    intent: Optional[Literal[
        "DATA_RETRIEVAL",
        "CALCULATION",
        "COMPARISON",
        "INSIGHT",
        "STRATEGIC",
        "CONTEXT_ENRICHMENT"
    ]] = Field(
        None,
        description="Classified intent"
    )

    intent_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Intent classification confidence (0-1)"
    )

    # ========================================================================
    # PART 1: ANALYSIS (What the data shows)
    # ========================================================================

    analysis: str = Field(
        ...,
        min_length=100,
        description="Analysis section: What the data shows (min 100 chars)"
    )

    # ========================================================================
    # PART 2: INSIGHTS (Why things are the way they are)
    # ========================================================================

    insights: str = Field(
        ...,
        min_length=100,
        description="Insights section: Why things are the way they are (min 100 chars)"
    )

    # ========================================================================
    # PART 3: RECOMMENDATIONS (What to do about it)
    # ========================================================================

    recommendations: Recommendations = Field(
        ...,
        description="Recommendations section: What to do about it"
    )

    # ========================================================================
    # METADATA & ERRORS
    # ========================================================================

    metadata: ResponseMetadata = Field(
        ...,
        description="Execution metadata"
    )

    errors: List[str] = Field(
        default_factory=list,
        description="Errors encountered during execution"
    )

    warnings: List[str] = Field(
        default_factory=list,
        description="Warnings encountered during execution"
    )

    # ========================================================================
    # ERROR-SPECIFIC FIELD
    # ========================================================================

    error: Optional[str] = Field(
        None,
        description="Error message if status is 'error'"
    )

    # ========================================================================
    # VALIDATION
    # ========================================================================

    @field_validator("analysis", "insights")
    @classmethod
    def validate_min_content(cls, v: str, info) -> str:
        """
        Validate that analysis and insights have meaningful content.

        Args:
            v: Field value
            info: Validation info

        Returns:
            Validated value

        Raises:
            ValueError if content is too generic
        """
        # Strip whitespace
        v_stripped = v.strip()

        # Check for generic error messages
        generic_errors = [
            "error generating",
            "error in",
            "failed to generate",
            "unable to generate",
            "no data available"
        ]

        if any(err in v_stripped.lower() for err in generic_errors):
            if info.field_name == "analysis":
                raise ValueError(
                    "Analysis cannot be a generic error message. "
                    "Provide specific analysis based on available data."
                )
            elif info.field_name == "insights":
                raise ValueError(
                    "Insights cannot be a generic error message. "
                    "Provide specific insights based on available data."
                )

        return v_stripped

    @field_validator("recommendations")
    @classmethod
    def validate_recommendations_not_generic(cls, v: Recommendations) -> Recommendations:
        """
        Validate that recommendations are not generic fallback messages.

        Args:
            v: Recommendations object

        Returns:
            Validated recommendations

        Raises:
            ValueError if recommendations are too generic
        """
        # Check for generic advisor recommendations
        if "consult with real estate advisor" in v.for_developers.lower():
            if len(v.for_developers) < 100:
                raise ValueError(
                    "Recommendations for developers are too generic. "
                    "Provide specific strategic guidance."
                )

        if "consult with real estate advisor" in v.for_investors.lower():
            if len(v.for_investors) < 100:
                raise ValueError(
                    "Recommendations for investors are too generic. "
                    "Provide specific strategic guidance."
                )

        return v

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "status": "success",
                "query": "Why is absorption rate low in Chakan?",
                "intent": "INSIGHT",
                "intent_confidence": 0.95,
                "analysis": "Chakan's current absorption rate of 0.8%/month is 27% below the Pune average of 1.1%/month. This micromarket shows 15 active projects with an average PSF of ₹3,645, which is 49% below the city average of ₹7,200. The region has seen consistent launches over the past 6 quarters, indicating developer confidence despite slower absorption.",
                "insights": "The lower absorption is primarily driven by Chakan's positioning as an industrial belt. The area attracts workforce housing demand rather than end-user residential demand. Key factors include: (1) Distance from Pune's main IT hubs (Hinjewadi 25km, Baner 28km), (2) Limited current metro connectivity (nearest station 15km), (3) Industrial workforce typically prefers rental over ownership.",
                "recommendations": {
                    "for_developers": "Target 2BHK compact units (600-750 sqft) at ₹3,200-3,800 PSF for workforce housing. Partner with nearby industrial employers for bulk booking schemes. Phase launches to match absorption capacity (40-50 units per quarter).",
                    "for_investors": "Entry opportunity for rental yield plays (expected 4-5% gross yield). Focus on projects near proposed metro extension (2026 timeline). Avoid luxury segments; stick to mid-range workforce housing.",
                    "timing": "Current market (2024-2025) favors cautious entry. Wait for metro construction commencement (Q2 2025) for stronger capital appreciation prospects. Rental income can offset holding period.",
                    "risks": [
                        "Metro extension delays beyond 2026 would dampen absorption further",
                        "Industrial slowdown could reduce workforce housing demand",
                        "Oversupply risk with 15 active projects and 3,200+ units in pipeline"
                    ]
                },
                "metadata": {
                    "confidence": 0.85,
                    "completeness": 0.78,
                    "iterations": 3,
                    "tool_calls": [
                        {"tool": "get_layer0_data", "result_summary": "12 projects"},
                        {"tool": "calculate_layer1_metrics", "result_summary": "8 projects with metrics"},
                        {"tool": "search_vector_insights", "result_summary": "5 insights retrieved"}
                    ],
                    "plan": ["get_layer0_data", "calculate_layer1_metrics", "search_vector_insights"],
                    "plan_reasoning": "INSIGHT intent requires full pipeline"
                },
                "errors": [],
                "warnings": ["Data completeness: 78%. Some projects have null fields."]
            }
        }


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_atlas_v4_response(response_dict: Dict) -> AtlasV4Response:
    """
    Validate raw response dict against AtlasV4Response schema.

    Args:
        response_dict: Raw response dictionary from graph execution

    Returns:
        Validated AtlasV4Response instance

    Raises:
        ValidationError if response doesn't match schema
    """
    return AtlasV4Response(**response_dict)


def create_error_response(
    query: str,
    error: str,
    intent: Optional[str] = None
) -> AtlasV4Response:
    """
    Create a validated error response.

    Args:
        query: Original user query
        error: Error message
        intent: Optional classified intent

    Returns:
        Validated error response
    """
    return AtlasV4Response(
        status="error",
        query=query,
        intent=intent,
        intent_confidence=0.0,
        analysis="Unable to generate analysis due to error. Please check your query and try again.",
        insights="Unable to generate insights due to error. The system encountered an issue during processing.",
        recommendations=Recommendations(
            for_developers="Unable to provide recommendations. Please contact support if this error persists.",
            for_investors="Unable to provide recommendations. Please contact support if this error persists.",
            timing="Unable to determine timing due to error.",
            risks=["System error prevented complete analysis"]
        ),
        metadata=ResponseMetadata(
            confidence=0.0,
            completeness=0.0,
            iterations=0,
            tool_calls=[],
            plan=[],
            plan_reasoning=None
        ),
        errors=[error],
        warnings=[],
        error=error
    )
