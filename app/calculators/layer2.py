"""
Layer 2 Calculator: Financial Metrics (Complex Aggregations)

Calculates advanced financial metrics requiring integration of multiple Layer 1 metrics:
- NPV (Net Present Value): C
- IRR (Internal Rate of Return): T^-1
- Payback Period: T
- Profitability Index: Dimensionless
- Cap Rate: T^-1
"""
from scipy.optimize import newton
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from app.models.domain import FinancialProjection


class Layer2Calculator:
    """Calculate Layer 2 financial metrics"""

    @staticmethod
    def calculate_npv(projection: FinancialProjection) -> float:
        """
        Net Present Value = ∑[C_t / (1+r)^t] - Initial_Investment

        Dimension: C (Currency)
        Formula: NPV = -I₀ + ∑(Cₜ / (1+r)ᵗ)
        LF Source: Pillar 4.3 (IRR & ROI Calculations)

        Args:
            projection: Financial projection with cash flows and discount rate

        Returns:
            NPV in INR
        """
        npv = -projection.initial_investment

        for year, cf in enumerate(projection.annual_cash_flows, start=1):
            npv += cf / ((1 + projection.discount_rate) ** year)

        return npv

    @staticmethod
    def calculate_irr(projection: FinancialProjection, max_iter: int = 100) -> Optional[float]:
        """
        Internal Rate of Return = r such that NPV(r) = 0

        Dimension: T^-1 (Rate per year)
        Formula: Solve NPV(r) = 0 using Newton's method
        LF Source: Pillar 4.3 (IRR & ROI Calculations)
        Algorithm: scipy.optimize.newton

        Args:
            projection: Financial projection with cash flows
            max_iter: Maximum iterations for Newton's method

        Returns:
            IRR as decimal (e.g., 0.24 for 24%) or None if calculation fails
        """

        def npv_func(rate: float) -> float:
            """NPV as a function of discount rate"""
            npv = -projection.initial_investment
            for year, cf in enumerate(projection.annual_cash_flows, start=1):
                if rate <= -1:  # Avoid division by zero
                    return float('inf')
                npv += cf / ((1 + rate) ** year)
            return npv

        try:
            # Initial guess: 20% (typical real estate IRR)
            irr = newton(npv_func, x0=0.20, maxiter=max_iter, tol=1e-6)

            # Validate result: check if NPV is actually close to zero
            npv_at_irr = npv_func(irr)
            # For large cash flows (Crores), use generous absolute tolerance
            # 1 lakh INR error is acceptable for Crore-scale projects
            if abs(npv_at_irr) < 100000:  # Within 1 lakh INR
                # IRR should be reasonable for real estate (typically -50% to 200%)
                if -0.5 <= irr <= 2.0:
                    return irr

            # If not within tolerance, return None
            return None

        except RuntimeError:
            # Newton's method did not converge, try with different initial guesses
            for guess in [0.10, 0.15, 0.25, 0.30, 0.50]:
                try:
                    irr = newton(npv_func, x0=guess, maxiter=max_iter, tol=1e-6)
                    npv_at_irr = npv_func(irr)
                    if abs(npv_at_irr) < 100000 and -0.5 <= irr <= 2.0:
                        return irr
                except:
                    continue
            return None
        except Exception:
            return None

    @staticmethod
    def calculate_payback_period(projection: FinancialProjection) -> Optional[float]:
        """
        Payback Period = Time when cumulative C = Initial_Investment

        Dimension: T (Years)
        Formula: Find t where ∑Cₜ = I₀
        LF Source: Pillar 4.1 (Feasibility Analysis)

        Args:
            projection: Financial projection with cash flows

        Returns:
            Payback period in years (fractional) or None if not achieved
        """
        cumulative = 0

        for year, cf in enumerate(projection.annual_cash_flows, start=1):
            cumulative += cf

            if cumulative >= projection.initial_investment:
                # Calculate fractional year
                shortfall = projection.initial_investment - (cumulative - cf)
                fraction = shortfall / cf if cf > 0 else 0
                return (year - 1) + fraction

        # Payback not achieved within project duration
        return None

    @staticmethod
    def calculate_profitability_index(projection: FinancialProjection) -> float:
        """
        Profitability Index = (NPV + Initial_Inv) / Initial_Inv
        Or equivalently: PV(Future CFs) / Initial_Inv

        Dimension: Dimensionless
        Formula: PI = (NPV + I₀) / I₀
        LF Source: Pillar 4.3 (IRR & ROI Calculations)

        Args:
            projection: Financial projection

        Returns:
            Profitability Index (PI > 1 means profitable)
        """
        # Calculate present value of future cash flows
        pv_future_cfs = sum(
            cf / ((1 + projection.discount_rate) ** (year + 1))
            for year, cf in enumerate(projection.annual_cash_flows)
        )

        pi = pv_future_cfs / projection.initial_investment

        return pi

    @staticmethod
    def calculate_cap_rate(annual_noi: float, property_value: float) -> float:
        """
        Capitalization Rate = Annual NOI / Property Value

        Dimension: T^-1 (% per year)
        Formula: Cap Rate = NOI / Value
        LF Source: Pillar 4.3 (IRR & ROI Calculations)

        Args:
            annual_noi: Annual Net Operating Income
            property_value: Current property value

        Returns:
            Cap rate as decimal (e.g., 0.08 for 8%)
        """
        if property_value <= 0:
            raise ValueError("Property value must be positive")

        return annual_noi / property_value

    @staticmethod
    def calculate_roi(net_profit: float, initial_investment: float) -> float:
        """
        Return on Investment = (Net Profit / Initial Investment) × 100

        Dimension: Dimensionless (%)
        Formula: ROI = (Profit / Investment) × 100
        LF Source: Pillar 4.3 (IRR & ROI Calculations)

        Args:
            net_profit: Total net profit
            initial_investment: Initial investment amount

        Returns:
            ROI as percentage
        """
        if initial_investment <= 0:
            raise ValueError("Initial investment must be positive")

        roi = (net_profit / initial_investment) * 100
        return roi

    @staticmethod
    def calculate_sensitivity_analysis(
        projection: FinancialProjection,
        absorption_range: Tuple[float, float] = (0.7, 1.3),
        price_range: Tuple[float, float] = (0.9, 1.1)
    ) -> Dict:
        """
        Sensitivity Analysis: IRR/NPV under different absorption & price scenarios

        Generates Base, Optimistic, and Stress case scenarios

        Args:
            projection: Base case financial projection
            absorption_range: (min, max) absorption multipliers (default: 70%-130%)
            price_range: (min, max) price multipliers (default: 90%-110%)

        Returns:
            Dictionary with baseCase, optimisticCase, stressCase IRR/NPV
        """
        # Base case
        base_npv = Layer2Calculator.calculate_npv(projection)
        base_irr = Layer2Calculator.calculate_irr(projection)

        # Optimistic case: higher absorption (faster sales) and higher prices
        optimistic_cfs = [cf * absorption_range[1] * price_range[1]
                          for cf in projection.annual_cash_flows]
        optimistic_proj = FinancialProjection(
            initial_investment=projection.initial_investment,
            annual_cash_flows=optimistic_cfs,
            discount_rate=projection.discount_rate,
            project_duration_years=projection.project_duration_years
        )
        optimistic_npv = Layer2Calculator.calculate_npv(optimistic_proj)
        optimistic_irr = Layer2Calculator.calculate_irr(optimistic_proj)

        # Stress case: lower absorption (slower sales) and lower prices
        stress_cfs = [cf * absorption_range[0] * price_range[0]
                      for cf in projection.annual_cash_flows]
        stress_proj = FinancialProjection(
            initial_investment=projection.initial_investment,
            annual_cash_flows=stress_cfs,
            discount_rate=projection.discount_rate,
            project_duration_years=projection.project_duration_years
        )
        stress_npv = Layer2Calculator.calculate_npv(stress_proj)
        stress_irr = Layer2Calculator.calculate_irr(stress_proj)

        return {
            "baseCase": {
                "npv_inr": round(base_npv, 2),
                "irr_percent": round(base_irr * 100, 2) if base_irr else None,
                "scenario": "Base"
            },
            "optimisticCase": {
                "npv_inr": round(optimistic_npv, 2),
                "irr_percent": round(optimistic_irr * 100, 2) if optimistic_irr else None,
                "scenario": "Optimistic",
                "assumptions": {
                    "absorption_multiplier": absorption_range[1],
                    "price_multiplier": price_range[1]
                }
            },
            "stressCase": {
                "npv_inr": round(stress_npv, 2),
                "irr_percent": round(stress_irr * 100, 2) if stress_irr else None,
                "scenario": "Stress",
                "assumptions": {
                    "absorption_multiplier": absorption_range[0],
                    "price_multiplier": price_range[0]
                }
            },
            "sensitivity_ranges": {
                "absorption_range": absorption_range,
                "price_range": price_range
            }
        }

    @staticmethod
    def create_result_dict(
        metric_name: str,
        value: float,
        unit: str,
        dimension: str,
        projection: FinancialProjection,
        formula: str,
        algorithm: Optional[str] = None
    ) -> Dict:
        """Create standardized result dictionary for Layer 2 metrics"""
        return {
            "metric": metric_name,
            "value": round(value, 4) if value is not None else None,
            "unit": unit,
            "dimension": dimension,
            "formula": formula,
            "algorithm": algorithm,
            "inputs": {
                "initialInvestment": projection.initial_investment,
                "discountRate": projection.discount_rate,
                "cashFlows": projection.annual_cash_flows,
                "projectDuration_years": projection.project_duration_years
            }
        }

    @staticmethod
    def create_provenance(
        metric_name: str,
        algorithm: str,
        lf_source: str = "Pillar_4.3",
        data_version: str = "Q3_FY25"
    ) -> Dict:
        """Create provenance tracking for Layer 2 calculation"""
        return {
            "inputDimensions": ["C", "T"],
            "calculationMethod": f"Layer 2 financial metric: {metric_name}",
            "lfSource": lf_source,
            "algorithm": algorithm,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "dataVersion": data_version,
            "layer": 2
        }
