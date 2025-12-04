"""
API request models
"""
from pydantic import BaseModel, Field
from typing import Dict, Optional
from app.models.enums import QueryType, Layer


class MCPQueryRequest(BaseModel):
    """Request model for /api/mcp/query endpoint"""
    queryId: Optional[str] = Field(None, description="Unique query identifier (auto-generated if not provided)")
    queryType: QueryType = Field(..., description="Type of query: calculation, optimization, comparison, benchmarking")
    layer: Layer = Field(..., description="Knowledge graph layer (0-3)")
    capability: str = Field(..., description="Capability to invoke (e.g., 'calculate_irr', 'optimize_product_mix')")
    parameters: Dict = Field(..., description="Parameters for the capability")
    context: Optional[Dict] = Field(default_factory=dict, description="Additional context (projectId, location, lfDataVersion)")

    class Config:
        json_schema_extra = {
            "example": {
                "queryType": "calculation",
                "layer": 2,
                "capability": "calculate_irr",
                "parameters": {
                    "cashFlows": [125000000, 150000000, 175000000, 200000000, 225000000],
                    "initialInvestment": 500000000
                },
                "context": {
                    "projectId": "P_CHAKAN_001",
                    "lfDataVersion": "Q3_FY25"
                }
            }
        }


class Layer1CalculationRequest(BaseModel):
    """Request for Layer 1 calculations"""
    totalRevenue: Optional[float] = None
    saleableArea: Optional[float] = None
    totalUnits: Optional[int] = None
    unitsSold: Optional[int] = None
    monthsElapsed: Optional[int] = None


class Layer2CalculationRequest(BaseModel):
    """Request for Layer 2 calculations"""
    cashFlows: Optional[list[float]] = None
    initialInvestment: Optional[float] = None
    discountRate: Optional[float] = 0.12
    annualNOI: Optional[float] = None
    propertyValue: Optional[float] = None


class Layer3OptimizationRequest(BaseModel):
    """Request for Layer 3 optimization"""
    location: str = Field(..., description="Location (e.g., 'Chakan, Pune')")
    totalUnits: int = Field(..., gt=0, description="Total number of units")
    totalArea: float = Field(..., gt=0, description="Total land area in sqft")
    totalProjectCost: Optional[float] = None
    projectDuration_months: Optional[int] = 36
    constraint_minIRR: Optional[float] = None


class StatisticalAnalysisRequest(BaseModel):
    """Request for statistical analysis of series data"""
    values: list[float] = Field(..., description="List of numerical values to analyze", min_items=1)
    operations: Optional[list[str]] = Field(
        None,
        description="Operations to perform (default: all). Options: TOTAL, AVERAGE, MEDIAN, MODE, STD_DEV, VARIANCE, PERCENTILE, NORMAL_DIST"
    )
    metric_name: str = Field("metric", description="Name of the metric being analyzed")
    context: str = Field("real_estate", description="Business context for interpretation")
    region: Optional[str] = Field(None, description="Region/micromarket for aggregation")
    city: Optional[str] = Field(None, description="City for aggregation")
    attribute_path: Optional[str] = Field(None, description="Path to attribute for project aggregation")

    class Config:
        json_schema_extra = {
            "example": {
                "values": [4200, 4500, 4300, 4800, 3900, 5100, 4400, 4600],
                "operations": ["AVERAGE", "MEDIAN", "STD_DEV", "PERCENTILE"],
                "metric_name": "Price PSF",
                "context": "market_pricing",
                "region": "Chakan",
                "city": "Pune"
            }
        }


class TopNProjectsRequest(BaseModel):
    """Request for top N projects by attribute"""
    region: str = Field(..., description="Region/micromarket name")
    city: str = Field(..., description="City name")
    attribute_path: str = Field(..., description="Path to attribute (e.g., 'l1_attributes.projectSize')")
    attribute_name: str = Field(..., description="Human-readable name of the attribute")
    n: int = Field(5, gt=0, le=50, description="Number of projects to return")
    ascending: bool = Field(False, description="If True, return bottom N (smallest values)")
