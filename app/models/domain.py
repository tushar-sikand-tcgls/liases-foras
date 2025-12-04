"""
Domain models for real estate analytics
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import date


class Developer(BaseModel):
    """Developer information"""
    developerId: str
    developerName: str
    apfScore: float = Field(..., ge=0, le=1, description="Architect Performance Factor (0-1)")
    marketabilityIndex: float = Field(..., ge=0, le=1, description="Market positioning strength (0-1)")


class Location(BaseModel):
    """Location information"""
    city: str
    microMarket: str
    pincode: Optional[str] = None


class Unit(BaseModel):
    """Individual unit configuration"""
    unitType: str  # "1BHK", "2BHK", "3BHK"
    count: int = Field(..., gt=0, description="Number of units of this type")
    areaPerUnit_sqft: float = Field(..., gt=0, description="Carpet area per unit")
    saleablePerUnit_sqft: float = Field(..., gt=0, description="Saleable area per unit")
    pricePerUnit_inr: float = Field(..., gt=0, description="Price per unit in INR")


class MarketData(BaseModel):
    """Market-specific data from LF"""
    absorptionRate_1BHK: float = Field(..., description="Monthly absorption rate for 1BHK")
    absorptionRate_2BHK: float = Field(..., description="Monthly absorption rate for 2BHK")
    absorptionRate_3BHK: float = Field(..., description="Monthly absorption rate for 3BHK")
    priceAppreciation_annual: float = Field(..., description="Annual price appreciation rate")
    competitiveIntensity: str = Field(..., description="low | medium | high")
    demandScore: int = Field(..., ge=0, le=100, description="Demand score (0-100)")


class Financials(BaseModel):
    """Financial projections"""
    initialInvestment: float = Field(..., gt=0, description="Initial investment in INR")
    annualCashFlows: List[float] = Field(..., description="Annual cash flows list")
    discountRate: float = Field(default=0.12, gt=0, lt=1, description="Discount rate for NPV")
    expectedIRR: Optional[float] = Field(None, description="Expected IRR")
    expectedNPV: Optional[float] = Field(None, description="Expected NPV")


class Project(BaseModel):
    """
    Complete project model with Layer 0 dimensions

    Layer 0 Dimensions:
    - U (Units): totalUnits
    - L² (Area): totalLandArea_sqft, totalSaleableArea_sqft
    - T (Time): projectDuration_months
    - CF (Cash Flow): totalProjectCost_inr
    """
    projectId: str
    projectName: str
    developer: Developer
    location: Location

    # Layer 0: Raw Dimensions
    totalUnits: int = Field(..., gt=0, description="U - Total number of units")
    totalLandArea_sqft: float = Field(..., gt=0, description="L² - Total land area")
    totalSaleableArea_sqft: float = Field(..., gt=0, description="L² - Total saleable area")
    totalCarpetArea_sqft: float = Field(..., gt=0, description="L² - Total carpet area")
    projectDuration_months: int = Field(..., gt=0, description="T - Project duration")
    totalProjectCost_inr: float = Field(..., gt=0, description="CF - Total project cost")

    launchDate: Optional[str] = None
    completionDate: Optional[str] = None

    # Unit breakdown
    units: List[Unit]

    # Market data
    marketData: MarketData

    # Financial projections
    financials: Financials

    @property
    def total_revenue(self) -> float:
        """Calculate total project revenue"""
        return sum(unit.pricePerUnit_inr * unit.count for unit in self.units)

    @property
    def unit_mix_percentages(self) -> Dict[str, float]:
        """Get unit mix as percentages"""
        return {
            unit.unitType: unit.count / self.totalUnits
            for unit in self.units
        }


class FinancialProjection(BaseModel):
    """Financial projection for Layer 2 calculations"""
    initial_investment: float = Field(..., ge=0, description="CF - Initial investment (0 if costs in cash flows)")
    annual_cash_flows: List[float] = Field(..., description="List of annual cash flows")
    discount_rate: float = Field(default=0.12, gt=0, lt=1, description="T^-1 - Discount rate")
    project_duration_years: int = Field(..., gt=0, description="T - Project duration in years")

    @classmethod
    def from_project(cls, project: Project) -> "FinancialProjection":
        """Create FinancialProjection from Project"""
        return cls(
            initial_investment=project.financials.initialInvestment,
            annual_cash_flows=project.financials.annualCashFlows,
            discount_rate=project.financials.discountRate,
            project_duration_years=len(project.financials.annualCashFlows)
        )


class MetricResult(BaseModel):
    """Result of a metric calculation"""
    metric: str
    value: float
    unit: str
    dimension: str  # e.g., "CF/L2", "CF/U", "T^-1"
    formula: Optional[str] = None


class Provenance(BaseModel):
    """Provenance tracking for calculations"""
    inputDimensions: List[str] = Field(..., description="Layer 0 dimensions used")
    calculationMethod: str = Field(..., description="Formula or algorithm used")
    lfSource: Optional[str] = Field(None, description="LF Pillar source (e.g., 'Pillar_4.3')")
    timestamp: str = Field(..., description="ISO-8601 timestamp")
    dataVersion: Optional[str] = Field(None, description="LF data version (e.g., 'Q3_FY25')")


class DataLineage(BaseModel):
    """Data lineage tracking across layers"""
    layer0_inputs: Optional[Dict] = Field(None, description="Layer 0 raw inputs")
    layer1_intermediates: Optional[List[str]] = Field(None, description="Layer 1 metrics used")
    layer2_dependencies: Optional[List[str]] = Field(None, description="Layer 2 metrics used")
