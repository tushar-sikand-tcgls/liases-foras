"""
Layer 1 Calculator: Derived Metrics (Simple Ratios & Products)

Calculates derived metrics from Layer 0 dimensions using dimensional analysis:
- PSF (Price Per Sqft): C/L²
- ASP (Average Selling Price): C/U
- Absorption Rate: (U/U_total)/T
- Sales Velocity: U/T
- Density: U/L²
- Cost Per Sqft: C/L²
- Revenue Run Rate: C/T
"""
from typing import Dict, Optional
from datetime import datetime


class Layer1Calculator:
    """Calculate Layer 1 derived metrics from Layer 0 dimensions"""

    @staticmethod
    def calculate_psf(total_revenue: float, saleable_area: float) -> Dict:
        """
        Price Per Sqft = Total Revenue / Saleable Area

        Dimension: C/L² (Cash per Area)
        Physical Analog: Pressure/Stress
        LF Source: Pillar 1.1 (Price & Market Movement Engine)
        """
        if saleable_area <= 0:
            raise ValueError("Saleable area must be positive")

        psf = total_revenue / saleable_area

        return {
            "metric": "PSF",
            "value": round(psf, 2),
            "unit": "INR/sqft",
            "dimension": "C/L2",
            "formula": f"{total_revenue:,.0f} / {saleable_area:,.0f}",
            "components": {
                "totalRevenue_C": total_revenue,
                "saleableArea_L2": saleable_area
            }
        }

    @staticmethod
    def calculate_asp(total_revenue: float, total_units: int) -> Dict:
        """
        Average Selling Price = Total Revenue / Total Units

        Dimension: C/U (Cash per Unit)
        Physical Analog: Price per unit
        LF Source: Pillar 2.1 (Typology Performance)
        """
        if total_units <= 0:
            raise ValueError("Total units must be positive")

        asp = total_revenue / total_units

        return {
            "metric": "ASP",
            "value": round(asp, 2),
            "unit": "INR/unit",
            "dimension": "C/U",
            "formula": f"{total_revenue:,.0f} / {total_units}",
            "components": {
                "totalRevenue_C": total_revenue,
                "totalUnits_U": total_units
            }
        }

    @staticmethod
    def calculate_absorption_rate(
        units_sold: int,
        total_units: int,
        months_elapsed: int
    ) -> Dict:
        """
        Absorption Rate = (% Units Sold) / Month

        Dimension: (U/U_total)/T
        Physical Analog: Fraction per time
        LF Source: Pillar 1.2 (Absorption & Sales Velocity)
        """
        if total_units <= 0:
            raise ValueError("Total units must be positive")
        if months_elapsed <= 0:
            raise ValueError("Months elapsed must be positive")

        rate = (units_sold / total_units) / months_elapsed
        rate_percent = rate * 100

        return {
            "metric": "AbsorptionRate",
            "value": round(rate_percent, 3),
            "unit": "%/month",
            "dimension": "(U/U_total)/T",
            "formula": f"({units_sold} / {total_units}) / {months_elapsed}",
            "components": {
                "unitsSold_U": units_sold,
                "totalUnits_U": total_units,
                "monthsElapsed_T": months_elapsed,
                "fractionSold": round(units_sold / total_units, 4)
            }
        }

    @staticmethod
    def calculate_sales_velocity(units_sold: int, months_elapsed: int) -> Dict:
        """
        Sales Velocity = Units Sold / Months

        Dimension: U/T
        Physical Analog: Rate (velocity)
        LF Source: Pillar 1.2 (Absorption & Sales Velocity)
        """
        if months_elapsed <= 0:
            raise ValueError("Months elapsed must be positive")

        velocity = units_sold / months_elapsed

        return {
            "metric": "SalesVelocity",
            "value": round(velocity, 2),
            "unit": "units/month",
            "dimension": "U/T",
            "formula": f"{units_sold} / {months_elapsed}",
            "components": {
                "unitsSold_U": units_sold,
                "monthsElapsed_T": months_elapsed
            }
        }

    @staticmethod
    def calculate_density(total_units: int, land_area: float) -> Dict:
        """
        Density = Total Units / Land Area

        Dimension: U/L²
        Physical Analog: Density
        LF Source: Pillar 2.1 (Typology & Efficiency)
        """
        if land_area <= 0:
            raise ValueError("Land area must be positive")

        density = total_units / land_area

        return {
            "metric": "Density",
            "value": round(density, 4),
            "unit": "units/sqft",
            "dimension": "U/L2",
            "formula": f"{total_units} / {land_area:,.0f}",
            "components": {
                "totalUnits_U": total_units,
                "landArea_L2": land_area
            }
        }

    @staticmethod
    def calculate_cost_per_sqft(total_cost: float, area: float) -> Dict:
        """
        Cost Per Sqft = Total Cost / Area

        Dimension: C/L²
        Physical Analog: Cost intensity
        LF Source: Pillar 4.1 (Feasibility Analysis)
        """
        if area <= 0:
            raise ValueError("Area must be positive")

        cost_per_sqft = total_cost / area

        return {
            "metric": "CostPerSqft",
            "value": round(cost_per_sqft, 2),
            "unit": "INR/sqft",
            "dimension": "C/L2",
            "formula": f"{total_cost:,.0f} / {area:,.0f}",
            "components": {
                "totalCost_C": total_cost,
                "area_L2": area
            }
        }

    @staticmethod
    def calculate_revenue_run_rate(monthly_revenue: float) -> Dict:
        """
        Revenue Run Rate = Monthly Revenue × 12

        Dimension: C/T (annualized)
        Physical Analog: Cash flow rate
        LF Source: Pillar 4.2 (Cash Flow Modeling)
        """
        annual_revenue = monthly_revenue * 12

        return {
            "metric": "RevenueRunRate",
            "value": round(annual_revenue, 2),
            "unit": "INR/year",
            "dimension": "C/T",
            "formula": f"{monthly_revenue:,.0f} × 12",
            "components": {
                "monthlyRevenue_C": monthly_revenue,
                "annualization_factor": 12
            }
        }

    @staticmethod
    def calculate_total_saleable_area(units: list) -> Dict:
        """
        Total Saleable Area = Sum(Units × Area per Unit)

        Dimension: L²
        Physical Analog: Cumulative area
        """
        total_area = sum(unit['count'] * unit['saleablePerUnit_sqft'] for unit in units)

        return {
            "metric": "TotalSaleableArea",
            "value": round(total_area, 2),
            "unit": "sqft",
            "dimension": "L2",
            "formula": "Σ(units × area_per_unit)",
            "components": {
                "units_breakdown": [
                    {
                        "unitType": unit['unitType'],
                        "count": unit['count'],
                        "area_per_unit": unit['saleablePerUnit_sqft'],
                        "subtotal": unit['count'] * unit['saleablePerUnit_sqft']
                    }
                    for unit in units
                ]
            }
        }

    @staticmethod
    def create_provenance(
        metric_name: str,
        input_dimensions: list,
        lf_source: str,
        data_version: str = "Q3_FY25"
    ) -> Dict:
        """Create provenance tracking for Layer 1 calculation"""
        return {
            "inputDimensions": input_dimensions,
            "calculationMethod": f"Layer 1 derived metric: {metric_name}",
            "lfSource": lf_source,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "dataVersion": data_version,
            "layer": 1
        }
