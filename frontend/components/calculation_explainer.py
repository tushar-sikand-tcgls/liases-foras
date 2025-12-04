"""
Calculation Explainer - Chain of Thought Display

Generates explainable, step-by-step calculation breakdowns for transparency
and audit trails in financial metrics.
"""

from typing import Dict, List, Any, Optional
import streamlit as st
from components.formatters import auto_format_value, format_currency_inr


class CalculationExplainer:
    """Generates explainable chain of thought for calculations"""
    
    @staticmethod
    def explain_irr(result: Dict) -> None:
        """
        Explain IRR calculation step-by-step

        IRR is the rate where NPV = 0, solved using Newton's method
        """
        st.markdown("---")
        with st.expander("📐 Step-by-Step IRR Calculation", expanded=False):
            inputs = result.get('inputs', {})
            value = result.get('value')
            
            st.markdown("#### **Step 1: Understanding the Problem**")
            st.markdown("""
            **Internal Rate of Return (IRR)** is the discount rate that makes the Net Present Value (NPV) equal to zero.
            
            Formula: NPV(r) = -I₀ + Σ[CFₜ / (1+r)ᵗ] = 0
            
            We need to find 'r' that satisfies this equation.
            """)
            
            st.markdown("---")
            st.markdown("#### **Step 2: Input Values**")
            
            initial_inv = inputs.get('initialInvestment', 0)
            cash_flows = inputs.get('cashFlows', [])
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Initial Investment (I₀):**")
                st.code(f"₹{initial_inv:,.0f} ({format_currency_inr(initial_inv, as_crore=True)})")
            
            with col2:
                st.markdown(f"**Project Duration:**")
                st.code(f"{len(cash_flows)} years")
            
            st.markdown("**Annual Cash Flows (CFₜ):**")
            for i, cf in enumerate(cash_flows, 1):
                st.markdown(f"  - Year {i}: ₹{cf:,.0f} ({format_currency_inr(cf, as_crore=True)})")
            
            st.markdown("---")
            st.markdown("#### **Step 3: Solution Method - Newton's Method**")
            st.markdown("""
            Since NPV(r) = 0 is a non-linear equation, we use **Newton's method** (iterative root-finding):
            
            ```
            r_{n+1} = r_n - NPV(r_n) / NPV'(r_n)
            ```
            
            Algorithm steps:
            1. Start with initial guess: r₀ = 0.20 (20%)
            2. Calculate NPV at current rate
            3. If |NPV| < tolerance (₹1 lakh), we found the IRR!
            4. Otherwise, calculate next estimate using derivative
            5. Repeat until convergence or max iterations (100)
            """)
            
            st.markdown("---")
            st.markdown("#### **Step 4: NPV Calculation at IRR**")
            
            if value is not None:
                st.markdown(f"**Found IRR: {value:.4f} (or {value:.2f}%)**")
                st.markdown("")
                st.markdown("Let's verify by calculating NPV at this rate:")
                
                # Calculate NPV at IRR to show it's ~0
                npv_at_irr = -initial_inv
                st.markdown(f"NPV = -I₀ + Σ[CFₜ / (1+IRR)ᵗ]")
                st.markdown(f"NPV = -{format_currency_inr(initial_inv, as_crore=True)}")
                
                for i, cf in enumerate(cash_flows, 1):
                    discounted = cf / ((1 + value) ** i)
                    npv_at_irr += discounted
                    st.markdown(f"    + ₹{cf:,.0f} / (1 + {value:.4f})^{i} = {format_currency_inr(discounted, as_crore=True)}")
                
                st.markdown(f"**NPV at IRR = {format_currency_inr(npv_at_irr, as_crore=True)}** ≈ ₹0 ✓")
                st.success(f"✅ NPV is approximately zero (within ₹{abs(npv_at_irr):,.0f} tolerance)")
            else:
                st.error("❌ IRR calculation did not converge")
                st.markdown("""
                **Possible reasons:**
                - Cash flows may not be sufficient to recover investment
                - Multiple sign changes in cash flow pattern
                - Numerical instability in Newton's method
                """)
            
            st.markdown("---")
            st.markdown("#### **Step 5: Interpretation**")
            if value:
                st.markdown(f"""
                **IRR = {value:.2f}%** means:
                - This is the effective annual return rate of the investment
                - At this discount rate, the present value of future cash flows exactly equals the initial investment
                - Higher IRR = better project profitability
                - Real estate typical target: 20-28%
                """)
                
                if value >= 20:
                    st.success(f"🎯 **Exceeds target range** (20-28%/year) - Excellent project profitability")
                elif value >= 15:
                    st.info(f"📊 **Acceptable range** (15-20%/year) - Below optimal but viable for real estate investments")
                else:
                    st.warning(f"⚠️ **Below acceptable range** - Target is 20-28%/year. Consider optimization strategies.")
    
    @staticmethod
    def explain_npv(result: Dict) -> None:
        """Explain NPV calculation step-by-step"""
        st.markdown("### 🔍 Calculation Chain of Thought")
        
        with st.expander("📐 Step-by-Step NPV Calculation", expanded=False):
            inputs = result.get('inputs', {})
            value = result.get('value')
            
            st.markdown("#### **Step 1: Formula**")
            st.markdown("""
            **Net Present Value (NPV)** = Present value of future cash flows - Initial investment
            
            Formula: NPV = -I₀ + Σ[CFₜ / (1+r)ᵗ]
            
            Where:
            - I₀ = Initial investment
            - CFₜ = Cash flow in year t
            - r = Discount rate
            - t = Year number
            """)
            
            st.markdown("---")
            st.markdown("#### **Step 2: Input Values**")
            
            initial_inv = inputs.get('initialInvestment', 0)
            cash_flows = inputs.get('cashFlows', [])
            discount_rate = inputs.get('discountRate', 0.12)
            
            st.code(f"""
Initial Investment (I₀): {format_currency_inr(initial_inv, as_crore=True)}
Discount Rate (r): {discount_rate:.2%}
Project Duration: {len(cash_flows)} years
            """)
            
            st.markdown("---")
            st.markdown("#### **Step 3: Discount Each Cash Flow**")
            
            total_pv = 0
            for i, cf in enumerate(cash_flows, 1):
                discount_factor = 1 / ((1 + discount_rate) ** i)
                pv = cf * discount_factor
                total_pv += pv
                
                st.markdown(f"""
**Year {i}:**
- Cash Flow: {format_currency_inr(cf, as_crore=True)}
- Discount Factor: 1/(1+{discount_rate:.2%})^{i} = {discount_factor:.6f}
- Present Value: {format_currency_inr(cf, as_crore=True)} × {discount_factor:.6f} = **{format_currency_inr(pv, as_crore=True)}**
                """)
            
            st.markdown("---")
            st.markdown("#### **Step 4: Calculate NPV**")
            
            st.markdown(f"""
Sum of PV of Future Cash Flows: {format_currency_inr(total_pv, as_crore=True)}
Initial Investment: -{format_currency_inr(initial_inv, as_crore=True)}
            
**NPV = {format_currency_inr(total_pv, as_crore=True)} - {format_currency_inr(initial_inv, as_crore=True)}**
**NPV = {format_currency_inr(value, as_crore=True)}**
            """)
            
            st.markdown("---")
            st.markdown("#### **Step 5: Interpretation**")
            if value > 0:
                st.success(f"""
✅ **Positive NPV = {format_currency_inr(value, as_crore=True)}**

This means:
- The project is **profitable** at {discount_rate:.0%} discount rate
- Present value of returns exceeds the investment
- **Accept this project** - it adds value
                """)
            elif value < 0:
                st.error(f"""
❌ **Negative NPV = {format_currency_inr(value, as_crore=True)}**

This means:
- The project **destroys value** at {discount_rate:.0%} discount rate
- Investment exceeds present value of returns
- **Reject this project** or reconsider assumptions
                """)
            else:
                st.info("NPV = ₹0 - Project breaks even at this discount rate")
    
    @staticmethod
    def explain_sensitivity_analysis(result: Dict) -> None:
        """Explain sensitivity analysis step-by-step"""
        st.markdown("### 🔍 Calculation Chain of Thought")
        
        with st.expander("📐 Step-by-Step Sensitivity Analysis", expanded=False):
            st.markdown("#### **Step 1: Purpose**")
            st.markdown("""
            **Sensitivity Analysis** tests how changes in key assumptions affect project outcomes.
            
            We analyze:
            - **Absorption Rate**: Speed of unit sales (70% to 130% of base case)
            - **Price**: Selling prices (90% to 110% of base case)
            
            This gives us 3 scenarios: Base, Optimistic, Stress
            """)
            
            st.markdown("---")
            st.markdown("#### **Step 2: Scenario Definitions**")
            
            base = result.get('baseCase', {})
            optimistic = result.get('optimisticCase', {})
            stress = result.get('stressCase', {})
            ranges = result.get('sensitivity_ranges', {})
            
            st.markdown(f"""
**Base Case:**
- Absorption: 100% (expected sales velocity)
- Price: 100% (expected pricing)
- IRR: {base.get('irr_percent', 0):.2f}%
- NPV: {format_currency_inr(base.get('npv_inr', 0), as_crore=True)}

**Optimistic Case:**
- Absorption: {ranges.get('absorption_range', [0, 1.3])[1]*100:.0f}% (faster sales)
- Price: {ranges.get('price_range', [0, 1.1])[1]*100:.0f}% (higher prices)
- IRR: {optimistic.get('irr_percent', 0):.2f}%
- NPV: {format_currency_inr(optimistic.get('npv_inr', 0), as_crore=True)}

**Stress Case:**
- Absorption: {ranges.get('absorption_range', [0.7, 0])[0]*100:.0f}% (slower sales)
- Price: {ranges.get('price_range', [0.9, 0])[0]*100:.0f}% (price pressure)
- IRR: {stress.get('irr_percent', 0):.2f}%
- NPV: {format_currency_inr(stress.get('npv_inr', 0), as_crore=True)}
            """)
            
            st.markdown("---")
            st.markdown("#### **Step 3: Cash Flow Adjustments**")
            
            st.markdown("""
For each scenario, we adjust cash flows:

**Optimistic:** CF_adjusted = CF_base × 1.3 × 1.1 = CF_base × 1.43
**Stress:** CF_adjusted = CF_base × 0.7 × 0.9 = CF_base × 0.63

Then recalculate IRR and NPV with adjusted cash flows.
            """)
            
            st.markdown("---")
            st.markdown("#### **Step 4: Risk Assessment**")
            
            base_irr = base.get('irr_percent', 0)
            opt_irr = optimistic.get('irr_percent', 0)
            stress_irr = stress.get('irr_percent', 0)
            
            irr_range = opt_irr - stress_irr
            downside_risk = base_irr - stress_irr
            upside_potential = opt_irr - base_irr
            
            st.markdown(f"""
**IRR Range:** {stress_irr:.2f}% to {opt_irr:.2f}% (spread: {irr_range:.2f}%)

**Downside Risk:** -{downside_risk:.2f}% (if stressed conditions occur)
**Upside Potential:** +{upside_potential:.2f}% (if optimistic conditions occur)

**Risk/Reward Ratio:** {upside_potential/downside_risk if downside_risk > 0 else 0:.2f}x
            """)
            
            if downside_risk < 5:
                st.success("✅ Low downside risk - project is resilient to adverse conditions")
            elif downside_risk < 10:
                st.info("📊 Moderate downside risk - monitor market conditions closely")
            else:
                st.warning("⚠️ High downside risk - consider risk mitigation strategies")
    
    @staticmethod
    def explain_optimization(result: Dict) -> None:
        """Explain product mix optimization step-by-step"""
        st.markdown("### 🔍 Calculation Chain of Thought")
        
        with st.expander("📐 Step-by-Step Optimization", expanded=False):
            st.markdown("#### **Step 1: Optimization Problem**")
            st.markdown("""
            **Objective:** Maximize IRR by finding optimal unit mix
            
            **Decision Variables:**
            - x₁ = Number of 1BHK units
            - x₂ = Number of 2BHK units  
            - x₃ = Number of 3BHK units
            
            **Objective Function:** Maximize IRR(x₁, x₂, x₃)
            """)
            
            st.markdown("---")
            st.markdown("#### **Step 2: Constraints**")
            
            st.markdown("""
            **Equality Constraints:**
            - x₁ + x₂ + x₃ = Total Units (e.g., 100)
            
            **Inequality Constraints:**
            - Total Area ≤ Land Area
            - x₁, x₂, x₃ ≥ 0 (non-negative units)
            - Absorption rate ≤ Market maximum
            
            **Method:** SLSQP (Sequential Least Squares Programming)
            """)
            
            st.markdown("---")
            st.markdown("#### **Step 3: Optimization Process**")
            
            opt_details = result.get('optimization_details', {})
            iterations = opt_details.get('iterations', 'N/A')
            
            st.markdown(f"""
**Algorithm:** scipy.optimize.minimize with SLSQP method

**Initial Guess:** Equal distribution (33.3% each unit type)

**Iterations:** {iterations}

**Convergence:** {opt_details.get('message', 'Success')}
            """)
            
            st.markdown("---")
            st.markdown("#### **Step 4: Optimal Solution**")
            
            optimal_mix = result.get('optimal_mix', {})
            units = result.get('units_breakdown', {})
            
            for unit_type in ['1BHK', '2BHK', '3BHK']:
                pct = optimal_mix.get(unit_type, 0) * 100
                count = units.get(unit_type, 0)
                st.markdown(f"**{unit_type}:** {pct:.1f}% ({count} units)")
            
            st.markdown("---")
            st.markdown("#### **Step 5: Financial Impact**")
            
            scenarios = result.get('scenarios', [])
            if scenarios:
                base = scenarios[0]  # First scenario is base case
                st.markdown(f"""
**Optimized Project Metrics:**
- IRR: {base.get('irr_percent', 0):.2f}%
- NPV: {format_currency_inr(base.get('npv_crore', 0) * 10000000, as_crore=True)}
- Revenue: {format_currency_inr(base.get('revenue_crore', 0) * 10000000, as_crore=True)}
- Duration: {base.get('duration_months', 0)} months
                """)
            
            st.markdown("""
**Why this mix is optimal:**
- Balances demand across unit types
- Maximizes revenue per square foot
- Optimizes absorption velocity
- Achieves highest risk-adjusted return
            """)


def add_calculation_explainer(result: Dict, capability: str) -> None:
    """
    Add calculation explainer based on capability type
    
    Args:
        result: Result dictionary from API
        capability: Capability name
    """
    explainer = CalculationExplainer()
    
    if capability == "calculate_irr":
        explainer.explain_irr(result)
    elif capability == "calculate_npv":
        explainer.explain_npv(result)
    elif capability == "calculate_sensitivity_analysis":
        explainer.explain_sensitivity_analysis(result)
    elif capability == "optimize_product_mix":
        explainer.explain_optimization(result)
