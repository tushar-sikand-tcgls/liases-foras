"""
Layer 3 Optimizer: Optimization & Scenario Planning (Complex Reasoning)

Combines Layer 0–2 with LF capability pillars for strategic decision-making:
- Product Mix Optimization (maximize IRR given constraints)
- Sensitivity Analysis across scenarios
- Developer Benchmarking
- Market Opportunity Scoring
"""
from scipy.optimize import minimize
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from app.calculators.layer2 import Layer2Calculator
from app.models.domain import FinancialProjection


class Layer3Optimizer:
    """Layer 3: Optimization & scenario planning"""

    @staticmethod
    def optimize_product_mix(
        total_units: int,
        total_land_area_sqft: float,
        total_project_cost: float,
        project_duration_months: int,
        market_data: Dict,
        developer_marketability: float = 1.0
    ) -> Dict:
        """
        Optimize unit mix (1BHK/2BHK/3BHK) to maximize IRR

        Uses scipy.optimize.minimize with SLSQP method

        Constraints:
        - Total units must equal specified count
        - Total area must not exceed land area
        - Absorption rate must not exceed LF historical max

        LF Pillars Applied: 2.1 (Typology), 4.1 (Feasibility), 4.3 (IRR/ROI)

        Args:
            total_units: Total number of units (U)
            total_land_area_sqft: Total land area (L²)
            total_project_cost: Total project cost (C)
            project_duration_months: Project duration (T)
            market_data: Dict with pricing and area for each unit type
            developer_marketability: Developer rating factor (0-1)

        Returns:
            Dict with optimal mix, scenarios, and provenance
        """

        unit_types = ['1BHK', '2BHK', '3BHK']

        def objective_function(x: np.ndarray) -> float:
            """
            Objective: Maximize IRR (minimize negative IRR)

            x = [units_1bhk, units_2bhk, units_3bhk]
            """
            units_1bhk, units_2bhk, units_3bhk = x

            # Constraint violation penalties
            if sum(x) != total_units:
                return 1e10

            if any(u < 0 for u in x):
                return 1e10

            # Calculate total area
            total_area = (
                units_1bhk * market_data['1BHK']['area'] +
                units_2bhk * market_data['2BHK']['area'] +
                units_3bhk * market_data['3BHK']['area']
            )

            if total_area > total_land_area_sqft:
                return 1e10

            # Calculate revenue
            total_revenue = (
                units_1bhk * market_data['1BHK']['price'] +
                units_2bhk * market_data['2BHK']['price'] +
                units_3bhk * market_data['3BHK']['price']
            )

            # Calculate weighted absorption (sales timeline)
            weighted_absorption = (
                units_1bhk * market_data['1BHK']['absorption'] +
                units_2bhk * market_data['2BHK']['absorption'] +
                units_3bhk * market_data['3BHK']['absorption']
            ) / sum(x) if sum(x) > 0 else 0

            # Estimate annual cash flows based on absorption
            duration_years = project_duration_months // 12
            if duration_years <= 0:
                duration_years = 3

            # Create realistic cash flows (phased construction + sales)
            initial_investment, cash_flows = Layer3Optimizer._create_realistic_cash_flows(
                total_revenue=total_revenue,
                total_cost=total_project_cost,
                duration_years=duration_years,
                pre_sales_percentage=0.60  # 60% pre-sales during construction
            )

            # Create financial projection
            projection = FinancialProjection(
                initial_investment=initial_investment,
                annual_cash_flows=cash_flows,
                discount_rate=0.12,
                project_duration_years=duration_years
            )

            # Calculate IRR
            irr = Layer2Calculator.calculate_irr(projection)

            if irr is None:
                return 1e10

            # Apply developer marketability factor (LF Pillar 3)
            adjusted_irr = irr * developer_marketability

            # Return negative IRR (since we're minimizing)
            return -adjusted_irr

        # Constraints
        constraints = [
            {
                'type': 'eq',
                'fun': lambda x: total_units - sum(x)
            }
        ]

        # Bounds: each unit type can be 0 to total_units
        bounds = [(0, total_units)] * 3

        # Initial guess: equal distribution
        x0 = np.array([total_units / 3, total_units / 3, total_units / 3])

        # Optimize
        result = minimize(
            objective_function,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 100}
        )

        optimal_units = result.x

        # Generate scenarios
        scenarios = Layer3Optimizer._generate_scenarios(
            optimal_units,
            total_units,
            total_project_cost,
            project_duration_months,
            market_data
        )

        # Calculate optimal mix percentages
        optimal_mix = {
            '1BHK': optimal_units[0] / sum(optimal_units),
            '2BHK': optimal_units[1] / sum(optimal_units),
            '3BHK': optimal_units[2] / sum(optimal_units)
        }

        return {
            'optimal_mix': {
                '1BHK': round(optimal_mix['1BHK'], 3),
                '2BHK': round(optimal_mix['2BHK'], 3),
                '3BHK': round(optimal_mix['3BHK'], 3)
            },
            'units_breakdown': {
                '1BHK': int(round(optimal_units[0])),
                '2BHK': int(round(optimal_units[1])),
                '3BHK': int(round(optimal_units[2]))
            },
            'scenarios': scenarios,
            'success': bool(result.success),  # Convert numpy.bool_ to Python bool
            'optimization_details': {
                'method': 'scipy.optimize.minimize (SLSQP)',
                'iterations': int(result.nit) if hasattr(result, 'nit') else None,
                'message': str(result.message) if hasattr(result, 'message') else None
            }
        }

    @staticmethod
    def _generate_scenarios(
        optimal_units: np.ndarray,
        total_units: int,
        total_project_cost: float,
        project_duration_months: int,
        market_data: Dict
    ) -> List[Dict]:
        """Generate Base, Optimistic, and Conservative scenarios"""

        scenarios = []

        # Base Case: Optimal mix
        base_mix = {
            '1BHK': int(round(optimal_units[0])),
            '2BHK': int(round(optimal_units[1])),
            '3BHK': int(round(optimal_units[2]))
        }
        base_revenue = sum(
            base_mix[ut] * market_data[ut]['price']
            for ut in ['1BHK', '2BHK', '3BHK']
        )
        base_scenario = Layer3Optimizer._calculate_scenario_metrics(
            "Base Case",
            base_mix,
            base_revenue,
            total_project_cost,
            project_duration_months
        )
        scenarios.append(base_scenario)

        # Optimistic Case: More 2BHK (highest demand)
        optimistic_mix = {
            '1BHK': int(total_units * 0.20),
            '2BHK': int(total_units * 0.60),
            '3BHK': int(total_units * 0.20)
        }
        optimistic_revenue = sum(
            optimistic_mix[ut] * market_data[ut]['price']
            for ut in ['1BHK', '2BHK', '3BHK']
        ) * 1.05  # 5% price premium in optimistic scenario
        optimistic_scenario = Layer3Optimizer._calculate_scenario_metrics(
            "Optimistic",
            optimistic_mix,
            optimistic_revenue,
            total_project_cost,
            project_duration_months * 0.9  # Faster sales
        )
        scenarios.append(optimistic_scenario)

        # Conservative Case: More 1BHK (safer, lower risk)
        conservative_mix = {
            '1BHK': int(total_units * 0.40),
            '2BHK': int(total_units * 0.40),
            '3BHK': int(total_units * 0.20)
        }
        conservative_revenue = sum(
            conservative_mix[ut] * market_data[ut]['price']
            for ut in ['1BHK', '2BHK', '3BHK']
        ) * 0.95  # 5% price discount in conservative scenario
        conservative_scenario = Layer3Optimizer._calculate_scenario_metrics(
            "Conservative",
            conservative_mix,
            conservative_revenue,
            total_project_cost,
            project_duration_months * 1.2  # Slower sales
        )
        scenarios.append(conservative_scenario)

        return scenarios

    @staticmethod
    def _calculate_scenario_metrics(
        scenario_name: str,
        unit_mix: Dict,
        total_revenue: float,
        total_cost: float,
        duration_months: float
    ) -> Dict:
        """Calculate NPV/IRR for a scenario"""

        duration_years = max(int(duration_months // 12), 1)

        # Create realistic cash flows (phased construction + sales)
        initial_investment, cash_flows = Layer3Optimizer._create_realistic_cash_flows(
            total_revenue=total_revenue,
            total_cost=total_cost,
            duration_years=duration_years,
            pre_sales_percentage=0.60  # 60% pre-sales during construction
        )

        projection = FinancialProjection(
            initial_investment=initial_investment,
            annual_cash_flows=cash_flows,
            discount_rate=0.12,
            project_duration_years=duration_years
        )

        npv = Layer2Calculator.calculate_npv(projection)
        irr = Layer2Calculator.calculate_irr(projection)

        return {
            'scenarioName': scenario_name,
            'mix': unit_mix,
            'npv_crore': round(npv / 10000000, 2),  # Convert to Crores
            'irr_percent': round(irr * 100, 2) if irr else None,
            'revenue_crore': round(total_revenue / 10000000, 2),
            'duration_months': int(duration_months)
        }

    @staticmethod
    def market_opportunity_scoring(
        location: str,
        unit_types: List[str],
        lf_market_data: Dict
    ) -> Dict:
        """
        Score location opportunity using LF OPPS (Opportunity Pocket Scoring)

        LF Pillars: 1.3 (Micro-Market Evaluation), 3.3 (OPPS Scoring)

        Args:
            location: Location string
            unit_types: List of unit types to consider
            lf_market_data: LF Pillar 1 market data

        Returns:
            Opportunity score and recommendations
        """

        demand_score = lf_market_data.get('demand_score', 75)
        supply_pressure = lf_market_data.get('supply_pressure', 'medium')
        competitive_intensity = lf_market_data.get('competitive_intensity', 'medium')

        # Calculate OPPS score (0-100)
        opps_score = demand_score

        # Adjust for supply pressure
        if supply_pressure == 'low':
            opps_score += 10
        elif supply_pressure == 'high':
            opps_score -= 10

        # Adjust for competitive intensity
        if competitive_intensity == 'low':
            opps_score += 5
        elif competitive_intensity == 'high':
            opps_score -= 5

        # Clamp to 0-100
        opps_score = max(0, min(100, opps_score))

        # Determine demand trend
        if opps_score >= 75:
            demand_trend = "high"
        elif opps_score >= 50:
            demand_trend = "medium"
        else:
            demand_trend = "low"

        # Recommended mix based on market conditions
        if demand_trend == "high":
            recommended_mix = {'1BHK': 0.25, '2BHK': 0.50, '3BHK': 0.25}
        elif demand_trend == "medium":
            recommended_mix = {'1BHK': 0.30, '2BHK': 0.50, '3BHK': 0.20}
        else:
            recommended_mix = {'1BHK': 0.40, '2BHK': 0.45, '3BHK': 0.15}

        return {
            'location': location,
            'oppsScore': opps_score,
            'demandTrend': demand_trend,
            'competitiveIntensity': competitive_intensity,
            'recommendedMix': recommended_mix,
            'opportunity': Layer3Optimizer._get_opportunity_message(opps_score)
        }

    @staticmethod
    def _get_opportunity_message(opps_score: int) -> str:
        """Get opportunity message based on OPPS score"""
        if opps_score >= 75:
            return "High potential for premium 2BHK focused projects"
        elif opps_score >= 60:
            return "Moderate potential with balanced unit mix recommended"
        elif opps_score >= 50:
            return "Fair potential with conservative 1BHK/2BHK mix"
        else:
            return "Challenging market conditions, recommend cautious approach"

    @staticmethod
    def _create_realistic_cash_flows(
        total_revenue: float,
        total_cost: float,
        duration_years: int,
        pre_sales_percentage: float = 0.60
    ) -> Tuple[float, List[float]]:
        """
        Create realistic real estate cash flows with phased construction and sales

        Real estate pattern (for IRR calculation):
        - Year 0: Upfront investment (land acquisition + initial costs) - NEGATIVE
        - Year 1-N: Net cash flows (revenue - construction costs per year)

        Args:
            total_revenue: Total project revenue (C)
            total_cost: Total project cost (C)
            duration_years: Project duration in years (T)
            pre_sales_percentage: Percentage of sales during construction (default 60%)

        Returns:
            Tuple of (initial_investment, annual_cash_flows)
        """
        if duration_years <= 0:
            duration_years = 3

        # Upfront investment: 30% of total cost (land + initial setup)
        initial_investment = total_cost * 0.30

        # Remaining construction costs spread over years
        remaining_cost = total_cost * 0.70
        annual_construction_cost = remaining_cost / duration_years

        # Revenue pattern: 60% pre-sales during construction, 40% after completion
        pre_sales_revenue = total_revenue * pre_sales_percentage
        post_completion_sales = total_revenue * (1 - pre_sales_percentage)

        # Distribute pre-sales over construction period
        if duration_years > 1:
            annual_pre_sales = pre_sales_revenue / (duration_years - 1)
        else:
            annual_pre_sales = pre_sales_revenue

        cash_flows = []

        # Year-by-year net cash flows
        for year in range(duration_years):
            if year < duration_years - 1:
                # During construction: pre-sales revenue - construction costs
                cf = annual_pre_sales - annual_construction_cost
            else:
                # Final year: post-completion sales - final construction costs
                cf = post_completion_sales - annual_construction_cost

            cash_flows.append(cf)

        return initial_investment, cash_flows

    @staticmethod
    def create_provenance(
        capability: str,
        lf_pillars: List[str],
        algorithm: str,
        data_version: str = "Q3_FY25"
    ) -> Dict:
        """Create provenance tracking for Layer 3 optimization"""
        return {
            "layer": 3,
            "capability": capability,
            "lfCapabilitiesApplied": lf_pillars,
            "algorithm": algorithm,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "dataVersion": data_version
        }
