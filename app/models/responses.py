"""
API response models
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from app.models.domain import Provenance, DataLineage


class MCPQueryResponse(BaseModel):
    """Response model for /api/mcp/query endpoint"""
    queryId: str = Field(..., description="Query identifier")
    status: str = Field(..., description="success | error")
    layer: int = Field(..., description="Knowledge graph layer (0-3)")
    capability: str = Field(..., description="Capability invoked")
    result: Dict[str, Any] = Field(..., description="Calculation result")
    provenance: Dict[str, Any] = Field(..., description="Provenance tracking")
    relatedMetrics: List[Dict[str, Any]] = Field(default_factory=list, description="Related metrics computed")
    executionTime_ms: float = Field(..., description="Execution time in milliseconds")
    dataLineage: Dict[str, Any] = Field(..., description="Data lineage across layers")

    class Config:
        json_schema_extra = {
            "example": {
                "queryId": "550e8400-e29b-41d4-a716-446655440000",
                "status": "success",
                "layer": 2,
                "capability": "calculate_irr",
                "result": {
                    "metric": "IRR",
                    "value": 24.0,
                    "unit": "%/year",
                    "dimension": "T^-1"
                },
                "provenance": {
                    "inputDimensions": ["CF", "T"],
                    "calculationMethod": "IRR: r where NPV(r) = 0",
                    "lfSource": "Pillar_4.3",
                    "algorithm": "Newton's method (scipy.optimize.newton)",
                    "timestamp": "2025-11-27T12:00:00Z",
                    "dataVersion": "Q3_FY25"
                },
                "relatedMetrics": [
                    {
                        "metricName": "NPV_at_12pct_discount",
                        "value": 520000000,
                        "dimension": "CF",
                        "calculatedFrom": "result"
                    }
                ],
                "executionTime_ms": 45.2,
                "dataLineage": {
                    "layer0_inputs": {"initialInvestment": 500000000},
                    "layer1_intermediates": ["cashFlows"],
                    "layer2_dependencies": []
                }
            }
        }


class MCPCapabilityInfo(BaseModel):
    """Information about a single MCP capability"""
    capabilityId: str
    name: str
    layer: int
    description: str
    tools: List[str]


class MCPInfoResponse(BaseModel):
    """Response model for /api/mcp/info endpoint"""
    name: str = "liases-foras-re-analytics"
    description: str = "Real estate financial analysis with LF market data & dimensional KG"
    version: str = "2.0"
    capabilities: List[MCPCapabilityInfo]
    apiSource: str = "sirrus-ai-re-analytics"
    dataSource: str = "liases-foras"
    lastUpdated: str
    quarterlyUpdateFrequency: str = "Q1, Q2, Q3, Q4"


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: str
    queryId: Optional[str] = None
    timestamp: str


class StatisticalOperation(BaseModel):
    """Individual statistical operation result"""
    value: Optional[Any] = Field(None, description="Calculated value(s)")
    formula: str = Field(..., description="Mathematical formula used")
    use_case: str = Field(..., description="Real estate use case")
    dimension: str = Field(..., description="Dimensional unit of result")
    # Additional fields for specific operations
    mode: Optional[float] = None
    frequency: Optional[int] = None
    all_modes: Optional[List[float]] = None
    is_multimodal: Optional[bool] = None
    # Percentiles
    p10: Optional[float] = None
    p25: Optional[float] = None
    p50: Optional[float] = None
    p75: Optional[float] = None
    p90: Optional[float] = None
    # Normal distribution
    mean: Optional[float] = None
    std_dev: Optional[float] = None
    is_normal: Optional[bool] = None
    p_value: Optional[float] = None
    skewness: Optional[float] = None
    kurtosis: Optional[float] = None
    outliers: Optional[Dict] = None
    confidence_intervals: Optional[Dict] = None
    coefficient_of_variation: Optional[float] = None


class DataQuality(BaseModel):
    """Data quality metrics"""
    original_count: int = Field(..., description="Number of input values")
    valid_count: int = Field(..., description="Number of valid values after cleaning")
    missing_count: int = Field(..., description="Number of missing/invalid values")
    quality_score: float = Field(..., description="Quality percentage (0-100)")


class StatisticalInterpretation(BaseModel):
    """Business interpretation of statistical results"""
    insights: List[str] = Field(..., description="Key insights from the analysis")
    recommendations: List[str] = Field(..., description="Actionable recommendations")


class StatisticalAnalysisResponse(BaseModel):
    """Response for statistical analysis operations"""
    metric_name: str = Field(..., description="Name of the analyzed metric")
    context: str = Field(..., description="Business context")
    data_quality: DataQuality = Field(..., description="Data quality metrics")
    operations: Dict[str, Any] = Field(..., description="Results of requested operations")
    interpretation: StatisticalInterpretation = Field(..., description="Business interpretation")
    timestamp: str = Field(..., description="ISO-8601 timestamp")
    error: Optional[str] = Field(None, description="Error message if any")
    error_code: Optional[int] = Field(None, description="Error code (201-206)")

    class Config:
        json_schema_extra = {
            "example": {
                "metric_name": "Price PSF",
                "context": "market_pricing",
                "data_quality": {
                    "original_count": 10,
                    "valid_count": 8,
                    "missing_count": 2,
                    "quality_score": 80.0
                },
                "operations": {
                    "average": {
                        "value": 4462.5,
                        "formula": "Σ(x) / n",
                        "use_case": "Typical project price",
                        "dimension": "INR/sqft"
                    },
                    "std_dev": {
                        "value": 364.2,
                        "formula": "√[Σ(x-μ)²/(n-1)]",
                        "use_case": "Price volatility",
                        "dimension": "INR/sqft"
                    }
                },
                "interpretation": {
                    "insights": [
                        "Low volatility (CV=8.2%). Market is relatively stable."
                    ],
                    "recommendations": []
                },
                "timestamp": "2025-11-27T12:00:00Z"
            }
        }


class TopNProjectsResponse(BaseModel):
    """Response for top N projects query"""
    region: str = Field(..., description="Region/micromarket name")
    city: str = Field(..., description="City name")
    attribute: str = Field(..., description="Attribute name")
    ranking_type: str = Field(..., description="'top' or 'bottom'")
    n: int = Field(..., description="Number of projects requested")
    projects: List[Dict[str, Any]] = Field(..., description="List of projects with values")
    total_projects: int = Field(..., description="Total projects in region")


class AggregationByRegionResponse(BaseModel):
    """Response for regional aggregation query"""
    region: str = Field(..., description="Region/micromarket name")
    city: str = Field(..., description="City name")
    attribute: str = Field(..., description="Attribute name")
    statistics: Dict[str, Any] = Field(..., description="Statistical summary")
    projects: List[Dict[str, Any]] = Field(..., description="List of projects with values")
    project_count: int = Field(..., description="Number of projects analyzed")
