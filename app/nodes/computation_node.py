"""
Computation Node - LangGraph Node 7

Performs deterministic financial calculations.

Flow:
1. Only runs for financial intent queries with all parameters
2. Uses scipy for IRR, NPV, payback period calculations
3. NEVER uses LLM for numeric calculations (deterministic only)
4. Updates state with computation_results
5. Routes to answer_composer_node

Key Principle: All financial calculations are DETERMINISTIC using scipy.
LLM is NEVER used to calculate numbers - only to explain results.
"""

from typing import Dict, List, Any, Optional
from app.orchestration.state_schema import QueryState
import numpy as np

# Financial calculation functions (using scipy)
try:
    from scipy.optimize import newton
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("⚠ scipy not available - financial calculations will be limited")


def computation_node(state: QueryState) -> QueryState:
    """
    Node 7: Perform deterministic financial calculations

    Args:
        state: Current QueryState with intent, kg_data, and all parameters

    Returns:
        Updated state with computation_results

    State Updates:
        - computation_results: Dict with calculated values
        - execution_path: Appends "computation"
    """
    print(f"\n{'='*80}")
    print(f"NODE 7: COMPUTATION")
    print(f"{'='*80}")

    # Track execution
    state['execution_path'].append('computation')

    # Only run for financial queries
    if state.get('intent') != 'financial':
        print(f"Intent is '{state.get('intent')}' - skipping computation")
        print(f"{'='*80}\n")
        return state

    # Check if all parameters present
    if not state.get('has_all_parameters', False):
        print(f"⚠ Not all parameters present - skipping computation")
        print(f"{'='*80}\n")
        return state

    print(f"Performing financial calculations...\n")

    kg_data = state.get('kg_data', {})
    subcategory = state.get('subcategory', '')

    computation_results = {
        'calculation_method': 'deterministic (scipy)',
        'assumptions': []
    }

    try:
        # Extract cash flow data
        cash_flows = extract_cash_flows(kg_data)

        if not cash_flows:
            print(f"⚠ No cash flow data available")
            state['computation_results'] = computation_results
            return state

        print(f"Cash flows extracted: {cash_flows}")

        # Extract initial investment
        initial_investment = extract_initial_investment(kg_data)
        print(f"Initial investment: {initial_investment}")

        # Calculate IRR
        if 'IRR' in subcategory or subcategory == 'default':
            if SCIPY_AVAILABLE and len(cash_flows) > 1:
                irr = calculate_irr(cash_flows, initial_investment)
                if irr is not None:
                    computation_results['irr'] = irr
                    computation_results['irr_percent'] = irr * 100
                    print(f"✓ IRR: {irr * 100:.2f}%")

        # Calculate NPV
        if 'NPV' in subcategory or 'discount' in state.get('query', '').lower():
            discount_rate = kg_data.get('discount_rate', 0.12)  # Default 12%
            computation_results['assumptions'].append(f"Discount rate: {discount_rate * 100}%")

            npv = calculate_npv(cash_flows, initial_investment, discount_rate)
            if npv is not None:
                computation_results['npv'] = npv
                print(f"✓ NPV: Rs. {npv:.2f} Cr")

        # Calculate Payback Period
        if 'payback' in subcategory.lower() or 'payback' in state.get('query', '').lower():
            payback = calculate_payback_period(cash_flows, initial_investment)
            if payback is not None:
                computation_results['payback_period_months'] = payback
                computation_results['payback_period_years'] = payback / 12
                print(f"✓ Payback Period: {payback:.1f} months ({payback/12:.1f} years)")

        # Sensitivity Analysis
        if 'sensitivity' in subcategory.lower():
            print(f"\n[Sensitivity Analysis]")
            sensitivity = perform_sensitivity_analysis(
                cash_flows, initial_investment, discount_rate=0.12
            )
            computation_results['sensitivity'] = sensitivity

            if sensitivity:
                print(f"  Base Case IRR: {sensitivity['base_case']['irr'] * 100:.2f}%")
                print(f"  Optimistic IRR: {sensitivity['optimistic']['irr'] * 100:.2f}%")
                print(f"  Conservative IRR: {sensitivity['conservative']['irr'] * 100:.2f}%")

        # Store computation metadata
        computation_results['cash_flows_used'] = cash_flows
        computation_results['initial_investment'] = initial_investment

    except Exception as e:
        print(f"✗ Error in computation: {e}")
        computation_results['error'] = str(e)

    # Update state
    state['computation_results'] = computation_results

    print(f"\n{'='*80}\n")

    return state


# ============================================================================
# FINANCIAL CALCULATION FUNCTIONS (Deterministic, using scipy)
# ============================================================================

def extract_cash_flows(kg_data: Dict[str, Any]) -> List[float]:
    """
    Extract cash flow sequence from KG data

    Args:
        kg_data: Data from Knowledge Graph

    Returns:
        List of cash flows (ordered by time period)
    """
    cash_flows = []

    # Look for cash flow fields in kg_data
    cf_keys = [k for k in kg_data.keys() if '.cf.' in k or 'cash_flow' in k.lower()]

    if cf_keys:
        # Extract and sort by period
        for key in sorted(cf_keys):
            value = kg_data[key]
            if isinstance(value, (int, float)):
                cash_flows.append(float(value))

    # If no explicit cash flows, estimate from annual_sales
    if not cash_flows:
        sales_keys = [k for k in kg_data.keys() if 'annual_sales' in k.lower() or 'monthly_revenue' in k.lower()]
        if sales_keys:
            annual_sales = kg_data[sales_keys[0]]
            if isinstance(annual_sales, (int, float)):
                # Estimate cash flows over project duration (default 5 years)
                for _ in range(5):
                    cash_flows.append(float(annual_sales))

    return cash_flows


def extract_initial_investment(kg_data: Dict[str, Any]) -> Optional[float]:
    """
    Extract initial investment from KG data

    Args:
        kg_data: Data from Knowledge Graph

    Returns:
        Initial investment value or None
    """
    # Look for investment fields
    inv_keys = [k for k in kg_data.keys() if 'investment' in k.lower() or 'total_cost' in k.lower()]

    if inv_keys:
        value = kg_data[inv_keys[0]]
        if isinstance(value, (int, float)):
            return float(value)

    return None


def calculate_irr(cash_flows: List[float], initial_investment: Optional[float] = None) -> Optional[float]:
    """
    Calculate Internal Rate of Return using scipy.optimize.newton

    Args:
        cash_flows: List of cash flows (period 1, 2, 3, ...)
        initial_investment: Initial investment (period 0, negative)

    Returns:
        IRR as decimal (e.g., 0.187 for 18.7%) or None if calculation fails
    """
    if not SCIPY_AVAILABLE:
        return None

    # Build full cash flow array [initial_investment, cf1, cf2, ...]
    if initial_investment is not None:
        full_cash_flows = [-abs(initial_investment)] + cash_flows
    else:
        # Assume first value is negative (investment)
        full_cash_flows = cash_flows

    # Define NPV function for root finding
    def npv_func(rate):
        return sum(cf / (1 + rate) ** i for i, cf in enumerate(full_cash_flows))

    try:
        # Use Newton's method to find rate where NPV = 0
        irr = newton(npv_func, x0=0.1)  # Start with 10% guess
        return irr

    except:
        # If Newton's method fails, try simple bisection
        try:
            from scipy.optimize import brentq
            irr = brentq(npv_func, -0.99, 10.0)  # Search between -99% and 1000%
            return irr
        except:
            return None


def calculate_npv(cash_flows: List[float], initial_investment: Optional[float], discount_rate: float) -> Optional[float]:
    """
    Calculate Net Present Value

    Args:
        cash_flows: List of cash flows
        initial_investment: Initial investment (negative)
        discount_rate: Discount rate as decimal (e.g., 0.12 for 12%)

    Returns:
        NPV value or None
    """
    if initial_investment is not None:
        full_cash_flows = [-abs(initial_investment)] + cash_flows
    else:
        full_cash_flows = cash_flows

    npv = sum(cf / (1 + discount_rate) ** i for i, cf in enumerate(full_cash_flows))

    return npv


def calculate_payback_period(cash_flows: List[float], initial_investment: Optional[float]) -> Optional[float]:
    """
    Calculate Payback Period (time to recover initial investment)

    Args:
        cash_flows: List of cash flows
        initial_investment: Initial investment

    Returns:
        Payback period in months or None
    """
    if not initial_investment:
        return None

    cumulative = 0
    investment = abs(initial_investment)

    for i, cf in enumerate(cash_flows):
        cumulative += cf

        if cumulative >= investment:
            # Linear interpolation for fractional period
            if i == 0:
                return i + 1
            else:
                prev_cumulative = cumulative - cf
                fraction = (investment - prev_cumulative) / cf
                return (i + fraction) * 12  # Convert to months (assuming annual cash flows)

    return None  # Payback never achieved


def perform_sensitivity_analysis(
    cash_flows: List[float],
    initial_investment: Optional[float],
    discount_rate: float = 0.12,
    variance: float = 0.2  # ±20% variance
) -> Dict[str, Dict[str, float]]:
    """
    Perform sensitivity analysis with three scenarios

    Args:
        cash_flows: Base case cash flows
        initial_investment: Initial investment
        discount_rate: Discount rate
        variance: Variance range (0.2 = ±20%)

    Returns:
        Dict with base_case, optimistic, conservative scenarios
    """
    results = {}

    # Base Case
    base_irr = calculate_irr(cash_flows, initial_investment)
    base_npv = calculate_npv(cash_flows, initial_investment, discount_rate)

    if base_irr is not None and base_npv is not None:
        results['base_case'] = {'irr': base_irr, 'npv': base_npv}

        # Optimistic Case (cash flows +20%)
        optimistic_cfs = [cf * (1 + variance) for cf in cash_flows]
        opt_irr = calculate_irr(optimistic_cfs, initial_investment)
        opt_npv = calculate_npv(optimistic_cfs, initial_investment, discount_rate)

        if opt_irr is not None and opt_npv is not None:
            results['optimistic'] = {'irr': opt_irr, 'npv': opt_npv}

        # Conservative Case (cash flows -20%)
        conservative_cfs = [cf * (1 - variance) for cf in cash_flows]
        cons_irr = calculate_irr(conservative_cfs, initial_investment)
        cons_npv = calculate_npv(conservative_cfs, initial_investment, discount_rate)

        if cons_irr is not None and cons_npv is not None:
            results['conservative'] = {'irr': cons_irr, 'npv': cons_npv}

    return results
