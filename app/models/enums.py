"""
Enums for the application
"""
from enum import Enum


class DimensionCode(str, Enum):
    """Layer 0: Base dimensional units (physics-inspired)"""
    U = "U"      # Units (count)
    L2 = "L2"    # Area (sqft)
    T = "T"      # Time (months)
    C = "C"      # Cash (INR) - analogous to Voltage in MLTI system


class UnitType(str, Enum):
    """Unit configuration types"""
    ONE_BHK = "1BHK"
    TWO_BHK = "2BHK"
    THREE_BHK = "3BHK"


class Layer(int, Enum):
    """Knowledge graph layers"""
    LAYER_0 = 0  # Raw dimensions
    LAYER_1 = 1  # Derived metrics
    LAYER_2 = 2  # Financial metrics
    LAYER_3 = 3  # Optimization & scenarios


class QueryType(str, Enum):
    """MCP query types"""
    CALCULATION = "calculation"
    OPTIMIZATION = "optimization"
    COMPARISON = "comparison"
    BENCHMARKING = "benchmarking"


class CapabilityId(str, Enum):
    """MCP capability identifiers"""
    # Layer 0
    LAYER0_DIMENSIONS = "layer0_dimensions"

    # Layer 1
    LAYER1_DERIVATIVES = "layer1_derivatives"

    # Layer 2
    LAYER2_FINANCIAL = "layer2_financial"

    # Layer 3
    LAYER3_OPTIMIZATION = "layer3_optimization"

    # LF Integration
    LF_INTEGRATION = "lf_integration"


class Layer1Metric(str, Enum):
    """Layer 1 metric names"""
    PSF = "PSF"  # Price Per Sqft
    ASP = "ASP"  # Average Selling Price
    ABSORPTION_RATE = "AbsorptionRate"
    SALES_VELOCITY = "SalesVelocity"
    DENSITY = "Density"
    COST_PER_SQFT = "CostPerSqft"
    REVENUE_RUN_RATE = "RevenueRunRate"


class Layer2Metric(str, Enum):
    """Layer 2 metric names"""
    NPV = "NPV"  # Net Present Value
    IRR = "IRR"  # Internal Rate of Return
    PAYBACK_PERIOD = "PaybackPeriod"
    PROFITABILITY_INDEX = "ProfitabilityIndex"
    CAP_RATE = "CapRate"
    ROI = "ROI"


class LFPillar(str, Enum):
    """Liases Foras data pillars"""
    MARKET = "1_market_intelligence"
    PRODUCT = "2_product_performance"
    DEVELOPER = "3_developer_performance"
    FINANCIAL = "4_financial"
    SALES_OPS = "5_sales_operations"
