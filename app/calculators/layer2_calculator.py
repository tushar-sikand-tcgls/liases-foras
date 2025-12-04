"""
Layer 2 Calculator: Financial Metrics (NON-LLM)
================================================

Calculates financial metrics from Layer 1 raw data:
- NPV (Net Present Value)
- IRR (Internal Rate of Return)
- Payback Period
- Profitability Index
- Cap Rate
- ROI (Return on Investment)

All calculations are deterministic (NO LLM involved).
Works with v4 nested JSON structure.
"""

import math
from typing import Dict, Optional
from datetime import datetime
from app.services.data_service import data_service


class Layer2Calculator:
    """Calculator for Layer 2 financial metrics (NON-LLM)"""

    # Assumptions for financial calculations
    CONSTRUCTION_COST_PSF = 2000  # INR/sqft (industry average)
    DISCOUNT_RATE = 0.12  # 12% discount rate
    LAND_COST_PER_ACRE = 30  # INR Crore per acre

    @staticmethod
    def _parse_date(date_str: str) -> Optional[datetime]:
        """Parse date string from PDF (e.g., 'Nov 2007')"""
        if not date_str or date_str == 'NA':
            return None
        try:
            return datetime.strptime(date_str, "%b %Y")
        except:
            return None

    @staticmethod
    def _calculate_project_duration_years(launch_date: str, possession_date: str) -> float:
        """Calculate project duration in years"""
        launch = Layer2Calculator._parse_date(launch_date)
        possession = Layer2Calculator._parse_date(possession_date)

        if not launch or not possession:
            return 20.0  # Default 20 years if dates unavailable

        duration_months = (possession.year - launch.year) * 12 + (possession.month - launch.month)
        return duration_months / 12.0

    def calculate_all_metrics(self, project: Dict) -> Dict:
        """
        Calculate all L2 metrics for a project (NON-LLM)

        Args:
            project: Project dict with nested L1 attributes

        Returns:
            Dict with all L2 metrics in nested format
        """
        # Extract L1 values
        total_units = data_service.get_value(project.get('totalSupplyUnits', {})) or 0
        project_size_units = data_service.get_value(project.get('projectSizeUnits', {})) or total_units  # Fallback to totalSupplyUnits
        unit_size_sqft = data_service.get_value(project.get('unitSaleableSizeSqft', {})) or 0
        current_price_psf = data_service.get_value(project.get('currentPricePSF', {})) or 0
        launch_price_psf = data_service.get_value(project.get('launchPricePSF', {})) or 0
        project_size_acres = data_service.get_value(project.get('projectSizeAcres', {})) or 0
        annual_sales_value_cr = data_service.get_value(project.get('annualSalesValueCr', {})) or 0
        sold_pct = data_service.get_value(project.get('soldPct', {})) or 0
        launch_date = data_service.get_value(project.get('launchDate', {})) or ''
        possession_date = data_service.get_value(project.get('possessionDate', {})) or ''

        # Calculate project duration
        project_duration_years = self._calculate_project_duration_years(launch_date, possession_date)

        # Calculate total project area
        total_area_sqft = total_units * unit_size_sqft if total_units and unit_size_sqft else 0

        # Calculate total revenue (current market value)
        total_revenue_cr = (total_area_sqft * current_price_psf) / 10000000 if total_area_sqft and current_price_psf else 0

        # Calculate total cost (construction + land)
        construction_cost_cr = (total_area_sqft * self.CONSTRUCTION_COST_PSF) / 10000000 if total_area_sqft else 0

        # Calculate land cost from projectSizeAcres (already calculated from projectSizeUnits in extraction)
        # projectSizeAcres is derived from projectSizeUnits using density assumption (12 units/acre)
        land_cost_cr = project_size_acres * self.LAND_COST_PER_ACRE if project_size_acres else 0

        total_cost_cr = construction_cost_cr + land_cost_cr

        # Calculate simple NPV (assuming annual cash flows over project duration)
        annual_cashflow_cr = annual_sales_value_cr if annual_sales_value_cr > 0 else (total_revenue_cr / project_duration_years)
        npv_cr = self._calculate_npv(
            initial_investment=total_cost_cr,
            annual_cashflow=annual_cashflow_cr,
            years=int(project_duration_years),
            discount_rate=self.DISCOUNT_RATE
        )

        # Calculate simple IRR
        irr_pct = self._calculate_irr(
            initial_investment=total_cost_cr,
            annual_cashflow=annual_cashflow_cr,
            years=int(project_duration_years)
        )

        # Calculate payback period
        payback_period_years = total_cost_cr / annual_cashflow_cr if annual_cashflow_cr > 0 else 0

        # Calculate profitability index
        profitability_index = (npv_cr + total_cost_cr) / total_cost_cr if total_cost_cr > 0 else 0

        # Calculate ROI
        roi_pct = ((total_revenue_cr - total_cost_cr) / total_cost_cr * 100) if total_cost_cr > 0 else 0

        # Calculate absorption rate (% sold per year)
        absorption_rate_pct_per_year = (sold_pct / project_duration_years * 100) if project_duration_years > 0 else 0

        # Return all L2 metrics in nested format
        return {
            "totalRevenueCr": {
                "value": round(total_revenue_cr, 2),
                "unit": "INR Crore",
                "dimension": "C",
                "relationships": [{"type": "IS", "target": "C"}],
                "source": "L2_Calculated",
                "isPure": True,
                "layer": "L2",
                "calculation": "totalSupplyUnits × unitSaleableSizeSqft × currentPricePSF / 10^7"
            },
            "totalCostCr": {
                "value": round(total_cost_cr, 2),
                "unit": "INR Crore",
                "dimension": "C",
                "relationships": [{"type": "IS", "target": "C"}],
                "source": "L2_Calculated",
                "isPure": True,
                "layer": "L2",
                "calculation": "(area × construction_cost_psf) + (acres × land_cost)"
            },
            "npvCr": {
                "value": round(npv_cr, 2),
                "unit": "INR Crore",
                "dimension": "C",
                "relationships": [{"type": "IS", "target": "C"}],
                "source": "L2_Calculated",
                "isPure": True,
                "layer": "L2",
                "calculation": "Σ(annual_cashflow / (1+discount_rate)^t) - initial_investment"
            },
            "irrPct": {
                "value": round(irr_pct, 2),
                "unit": "%",
                "dimension": "Fraction/T",
                "relationships": [{"type": "INVERSE_OF", "target": "T"}],
                "source": "L2_Calculated",
                "isPure": False,
                "layer": "L2",
                "calculation": "Rate where NPV = 0"
            },
            "paybackPeriodYears": {
                "value": round(payback_period_years, 2),
                "unit": "years",
                "dimension": "T",
                "relationships": [{"type": "IS", "target": "T"}],
                "source": "L2_Calculated",
                "isPure": True,
                "layer": "L2",
                "calculation": "total_cost / annual_cashflow"
            },
            "profitabilityIndex": {
                "value": round(profitability_index, 2),
                "unit": "ratio",
                "dimension": "Dimensionless",
                "relationships": [],
                "source": "L2_Calculated",
                "isPure": True,
                "layer": "L2",
                "calculation": "(NPV + initial_investment) / initial_investment"
            },
            "roiPct": {
                "value": round(roi_pct, 2),
                "unit": "%",
                "dimension": "Dimensionless",
                "relationships": [],
                "source": "L2_Calculated",
                "isPure": True,
                "layer": "L2",
                "calculation": "(total_revenue - total_cost) / total_cost × 100"
            },
            "absorptionRatePctPerYear": {
                "value": round(absorption_rate_pct_per_year, 2),
                "unit": "%/year",
                "dimension": "Fraction/T",
                "relationships": [{"type": "INVERSE_OF", "target": "T"}],
                "source": "L2_Calculated",
                "isPure": False,
                "layer": "L2",
                "calculation": "sold_pct / project_duration_years × 100"
            },
            "projectDurationYears": {
                "value": round(project_duration_years, 2),
                "unit": "years",
                "dimension": "T",
                "relationships": [{"type": "IS", "target": "T"}],
                "source": "L2_Calculated",
                "isPure": True,
                "layer": "L2",
                "calculation": "(possession_date - launch_date) / 12"
            }
        }

    @staticmethod
    def _calculate_npv(initial_investment: float, annual_cashflow: float, years: int, discount_rate: float) -> float:
        """
        Calculate Net Present Value (NON-LLM)

        NPV = Σ(CF_t / (1+r)^t) - Initial_Investment
        """
        if years == 0 or annual_cashflow == 0:
            return -initial_investment

        npv = -initial_investment
        for year in range(1, years + 1):
            npv += annual_cashflow / ((1 + discount_rate) ** year)

        return npv

    @staticmethod
    def _calculate_irr(initial_investment: float, annual_cashflow: float, years: int) -> float:
        """
        Calculate Internal Rate of Return (NON-LLM)

        Uses Newton-Raphson method to find rate where NPV = 0
        """
        if years == 0 or annual_cashflow == 0:
            return 0.0

        # Initial guess
        rate = 0.15  # Start with 15%

        # Newton-Raphson iteration
        for _ in range(100):  # Max 100 iterations
            npv = -initial_investment
            npv_derivative = 0

            for year in range(1, years + 1):
                npv += annual_cashflow / ((1 + rate) ** year)
                npv_derivative -= year * annual_cashflow / ((1 + rate) ** (year + 1))

            if abs(npv) < 0.01:  # Converged
                break

            if npv_derivative == 0:  # Avoid division by zero
                break

            rate = rate - npv / npv_derivative

            # Bounds checking
            if rate < -0.99:
                rate = -0.99
            elif rate > 10.0:
                rate = 10.0

        return rate * 100  # Return as percentage


# Global calculator instance
layer2_calculator = Layer2Calculator()
