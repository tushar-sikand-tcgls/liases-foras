"""
Pytest configuration and fixtures
"""
import pytest
from app.models.domain import FinancialProjection, Project, Developer, Location, Unit, MarketData, Financials


@pytest.fixture
def sample_projection():
    """Sample financial projection for testing"""
    return FinancialProjection(
        initial_investment=500000000,  # 50 Cr
        annual_cash_flows=[125000000, 150000000, 175000000, 200000000, 225000000],  # 5 years
        discount_rate=0.12,  # 12%
        project_duration_years=5
    )


@pytest.fixture
def sample_project():
    """Sample project for testing"""
    return Project(
        projectId="P_TEST_001",
        projectName="Test Project",
        developer=Developer(
            developerId="D_TEST",
            developerName="Test Developer",
            apfScore=0.90,
            marketabilityIndex=0.85
        ),
        location=Location(
            city="Pune",
            microMarket="Chakan",
            pincode="410501"
        ),
        totalUnits=100,
        totalLandArea_sqft=70000,
        totalSaleableArea_sqft=60000,
        totalCarpetArea_sqft=42000,
        projectDuration_months=36,
        totalProjectCost_inr=500000000,
        units=[
            Unit(
                unitType="1BHK",
                count=30,
                areaPerUnit_sqft=500,
                saleablePerUnit_sqft=600,
                pricePerUnit_inr=3000000
            ),
            Unit(
                unitType="2BHK",
                count=50,
                areaPerUnit_sqft=700,
                saleablePerUnit_sqft=840,
                pricePerUnit_inr=4200000
            ),
            Unit(
                unitType="3BHK",
                count=20,
                areaPerUnit_sqft=1000,
                saleablePerUnit_sqft=1200,
                pricePerUnit_inr=6000000
            )
        ],
        marketData=MarketData(
            absorptionRate_1BHK=0.03,
            absorptionRate_2BHK=0.05,
            absorptionRate_3BHK=0.02,
            priceAppreciation_annual=0.08,
            competitiveIntensity="medium",
            demandScore=78
        ),
        financials=Financials(
            initialInvestment=500000000,
            annualCashFlows=[125000000, 150000000, 175000000, 200000000, 225000000],
            discountRate=0.12,
            expectedIRR=0.24,
            expectedNPV=520000000
        )
    )
