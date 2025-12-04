"""
MCP Info Endpoint: Capability discovery
"""
from fastapi import APIRouter
from datetime import datetime
from app.models.responses import MCPInfoResponse, MCPCapabilityInfo

router = APIRouter()


@router.get("/info", response_model=MCPInfoResponse)
def get_mcp_capabilities():
    """
    Capability discovery endpoint for MCP integration

    Returns all available tools across 5 layers (0-4) plus LF integration
    """

    capabilities = [
        MCPCapabilityInfo(
            capabilityId="layer0_dimensions",
            name="Raw Dimensions",
            layer=0,
            description="Atomic dimensional units (U, L², T, CF)",
            tools=["get_project_dimensions"]
        ),
        MCPCapabilityInfo(
            capabilityId="layer1_derivatives",
            name="Derived Metrics (L1)",
            layer=1,
            description="Ratios and products (PSF, ASP, Absorption Rate, Sales Velocity)",
            tools=[
                "calculate_psf",
                "calculate_asp",
                "calculate_absorption_rate",
                "calculate_sales_velocity",
                "calculate_density",
                "calculate_cost_per_sqft"
            ]
        ),
        MCPCapabilityInfo(
            capabilityId="layer2_financial",
            name="Financial Metrics & Statistics (L2)",
            layer=2,
            description="Complex financial analysis (NPV, IRR) and statistical operations (8 core operations)",
            tools=[
                "calculate_npv",
                "calculate_irr",
                "calculate_payback_period",
                "calculate_profitability_index",
                "calculate_cap_rate",
                "calculate_sensitivity_analysis",
                "calculate_statistics",
                "aggregate_by_region",
                "get_top_n_projects"
            ]
        ),
        MCPCapabilityInfo(
            capabilityId="layer2_statistical",
            name="Statistical Analysis (L2)",
            layer=2,
            description="8 statistical operations: TOTAL, AVERAGE, MEDIAN, MODE, STD_DEV, VARIANCE, PERCENTILE, NORMAL_DIST",
            tools=[
                "calculate_series_statistics",
                "calculate_mode",
                "calculate_normal_distribution",
                "aggregate_with_statistics",
                "get_distribution_analysis"
            ]
        ),
        MCPCapabilityInfo(
            capabilityId="layer3_optimization",
            name="Optimization & Scenarios (L3)",
            layer=3,
            description="Product mix optimization, benchmarking, opportunity scoring",
            tools=[
                "optimize_product_mix",
                "market_opportunity_scoring"
            ]
        ),
        MCPCapabilityInfo(
            capabilityId="layer4_insights",
            name="Market Insights & Context (L4)",
            layer=4,
            description="RAG-based market intelligence using city reports vector database",
            tools=[
                "get_market_insights",
                "enrich_irr_calculation",
                "semantic_search"
            ]
        ),
        MCPCapabilityInfo(
            capabilityId="lf_integration",
            name="Liases Foras Data Access",
            layer=-1,  # Special layer for LF integration
            description="Access LF market intelligence across 5 pillars",
            tools=[
                "fetch_lf_market_data",
                "fetch_lf_product_data",
                "fetch_lf_developer_rating"
            ]
        )
    ]

    return MCPInfoResponse(
        name="liases-foras-re-analytics",
        description="Real estate financial analysis with LF market data & dimensional KG",
        version="2.0",
        capabilities=capabilities,
        apiSource="sirrus-ai-re-analytics",
        dataSource="liases-foras",
        lastUpdated=datetime.utcnow().isoformat() + "Z",
        quarterlyUpdateFrequency="Q1, Q2, Q3, Q4"
    )
