"""
Calculation Proof Display Component

Provides step-by-step visual breakdown of financial calculations (IRR, NPV, etc.)
and derived attribute formulas with mathematical proofs.

Features:
- Formula display with variable substitution
- Intermediate calculation steps
- Final result with units
- Color-coded sections (formula, inputs, steps, result)
"""

import streamlit as st
from typing import Dict, List, Optional, Any


def display_calculation_proof(
    calculation_type: str,
    formula: str,
    inputs: Dict[str, Any],
    steps: List[Dict[str, Any]],
    result: Any,
    unit: Optional[str] = None
) -> None:
    """
    Display calculation proof with step-by-step breakdown

    Args:
        calculation_type: Name of calculation (e.g., "Sellout Efficiency", "IRR", "NPV")
        formula: Mathematical formula as string (e.g., "(annualSales × 12) / supply")
        inputs: Dict of input values with keys and values
                e.g., {"annualSales": 527, "supply": 1109}
        steps: List of intermediate calculation steps
               e.g., [{"description": "Multiply annual sales by 12", "value": 6324, "formula": "527 × 12"}]
        result: Final calculated result
        unit: Optional unit for the result (e.g., "%", "Rs Cr", "Years")

    Example:
        >>> display_calculation_proof(
        ...     calculation_type="Sellout Efficiency",
        ...     formula="(annualSales × 12) / supply",
        ...     inputs={"annualSales": 527, "supply": 1109},
        ...     steps=[
        ...         {"description": "Step 1: Multiply annual sales by 12", "value": 6324, "formula": "527 × 12 = 6324"},
        ...         {"description": "Step 2: Divide by supply", "value": 5.7, "formula": "6324 / 1109 = 5.7"}
        ...     ],
        ...     result=5.7,
        ...     unit="%"
        ... )
    """

    # Container for the proof
    with st.expander("📊 **Show Calculation Proof**", expanded=False):
        # Header
        st.markdown(f"### Calculation: **{calculation_type}**")
        st.markdown("---")

        # Section 1: Formula
        st.markdown("#### 🔢 **Formula**")
        st.code(formula, language="text")

        # Section 2: Input Values
        st.markdown("#### 📥 **Input Values**")
        input_cols = st.columns(2)
        for idx, (key, value) in enumerate(inputs.items()):
            col_idx = idx % 2
            with input_cols[col_idx]:
                # Clean up key for display (convert camelCase to Title Case)
                display_key = camel_to_title(key)
                if isinstance(value, float):
                    st.metric(label=display_key, value=f"{value:,.2f}")
                else:
                    st.metric(label=display_key, value=f"{value:,}")

        # Section 3: Step-by-Step Calculation
        if steps:
            st.markdown("#### 🧮 **Step-by-Step Calculation**")
            for idx, step in enumerate(steps, 1):
                step_description = step.get("description", f"Step {idx}")
                step_formula = step.get("formula", "")
                step_value = step.get("value")

                # Display step with indentation
                st.markdown(f"**{step_description}:**")
                if step_formula:
                    st.code(step_formula, language="text")
                if step_value is not None:
                    if isinstance(step_value, float):
                        st.write(f"   → Result: **{step_value:,.2f}**")
                    else:
                        st.write(f"   → Result: **{step_value:,}**")
                st.write("")  # Spacing

        # Section 4: Final Result
        st.markdown("#### ✅ **Final Result**")
        result_display = f"{result:,.2f}" if isinstance(result, float) else f"{result:,}"
        if unit:
            st.success(f"**{calculation_type} = {result_display} {unit}**")
        else:
            st.success(f"**{calculation_type} = {result_display}**")

        st.markdown("---")
        st.caption("💡 This calculation uses data directly from the Knowledge Graph with formulas from the Managed RAG Excel sheet.")


def display_derived_attribute_proof(
    attribute_name: str,
    project_name: str,
    formula: str,
    inputs: Dict[str, Any],
    result: Any,
    unit: Optional[str] = None
) -> None:
    """
    Display proof for derived attribute calculation (L1 layer)

    Args:
        attribute_name: Name of derived attribute (e.g., "Sellout Efficiency")
        project_name: Project name for context
        formula: Formula from Excel (e.g., "(AnnualSales × 12) / Supply")
        inputs: Dict of L0 input values
        result: Calculated result
        unit: Unit of measurement

    Example:
        >>> display_derived_attribute_proof(
        ...     attribute_name="Sellout Efficiency",
        ...     project_name="Sara City",
        ...     formula="(AnnualSales × 12) / Supply",
        ...     inputs={"AnnualSales": 527, "Supply": 1109},
        ...     result=5.7,
        ...     unit="%"
        ... )
    """

    # Auto-generate steps from formula and inputs
    steps = []

    # For simple formulas, auto-generate 1-2 steps
    if "×" in formula or "*" in formula:
        # Identify multiplication step
        # This is a simplified example - can be extended with regex parsing
        parts = formula.replace("(", "").replace(")", "").split("/")
        if len(parts) == 2:
            # Numerator / Denominator structure
            numerator_formula = parts[0].strip()
            denominator_formula = parts[1].strip()

            # Step 1: Calculate numerator
            if "×" in numerator_formula or "*" in numerator_formula:
                # Extract values and calculate
                # For now, manually detect pattern
                pass  # Will be filled in with actual calculation

            # Step 2: Divide
            pass  # Will be filled in with actual calculation

    # For now, use simple steps based on common patterns
    # This can be enhanced with a formula parser

    # Display using the general proof function
    display_calculation_proof(
        calculation_type=f"{attribute_name} for {project_name}",
        formula=formula,
        inputs=inputs,
        steps=steps,  # Empty for now, can be auto-generated
        result=result,
        unit=unit
    )


def display_financial_metric_proof(
    metric_type: str,
    project_name: str,
    cash_flows: List[float],
    discount_rate: Optional[float] = None,
    result: Any = None,
    unit: Optional[str] = None
) -> None:
    """
    Display proof for financial metric calculation (IRR, NPV, Payback Period)

    Args:
        metric_type: "IRR", "NPV", "Payback Period", etc.
        project_name: Project name for context
        cash_flows: List of cash flows by period
        discount_rate: Discount rate for NPV (optional for IRR)
        result: Calculated result
        unit: Unit of measurement (e.g., "%", "Rs Cr", "Years")

    Example:
        >>> display_financial_metric_proof(
        ...     metric_type="NPV",
        ...     project_name="Sara City",
        ...     cash_flows=[-100, 30, 40, 50, 40],
        ...     discount_rate=12,
        ...     result=15.3,
        ...     unit="Rs Cr"
        ... )
    """

    with st.expander(f"📊 **Show {metric_type} Calculation Proof**", expanded=False):
        st.markdown(f"### {metric_type} Calculation for **{project_name}**")
        st.markdown("---")

        # Section 1: Formula
        st.markdown("#### 🔢 **Formula**")
        if metric_type == "NPV":
            st.latex(r"NPV = \sum_{t=0}^{n} \frac{CF_t}{(1 + r)^t}")
            st.write("Where:")
            st.write("- CF_t = Cash flow at time t")
            st.write(f"- r = Discount rate = {discount_rate}%")
            st.write("- t = Time period (years)")
        elif metric_type == "IRR":
            st.latex(r"NPV = \sum_{t=0}^{n} \frac{CF_t}{(1 + IRR)^t} = 0")
            st.write("Where:")
            st.write("- IRR is the rate that makes NPV = 0")
            st.write("- Solved using Newton's method (scipy)")
        elif metric_type == "Payback Period":
            st.write("Payback Period = Time when cumulative cash flow = 0")

        # Section 2: Cash Flows
        st.markdown("#### 💰 **Cash Flows**")
        cf_data = {"Period (Year)": list(range(len(cash_flows))), "Cash Flow (Rs Cr)": cash_flows}
        st.table(cf_data)

        # Section 3: Calculation Steps
        if metric_type == "NPV":
            st.markdown("#### 🧮 **Discounted Cash Flows**")
            discount_factor = 1 + (discount_rate / 100)

            discounted_cfs = []
            for t, cf in enumerate(cash_flows):
                discounted = cf / (discount_factor ** t)
                discounted_cfs.append(discounted)
                st.write(f"Year {t}: CF_{t} / (1 + {discount_rate/100})^{t} = {cf:,.2f} / {discount_factor**t:.4f} = **{discounted:,.2f}**")

            st.markdown("#### ✅ **Sum of Discounted Cash Flows**")
            total_npv = sum(discounted_cfs)
            st.write(f"NPV = {' + '.join([f'{cf:,.2f}' for cf in discounted_cfs])}")
            st.write(f"NPV = **{total_npv:,.2f} {unit}**")

        elif metric_type == "IRR":
            st.markdown("#### 🧮 **IRR Calculation (Newton's Method)**")
            st.write(f"Using scipy.optimize.newton to solve for IRR:")
            st.code(f"IRR = {result:.2f}%", language="text")
            st.write(f"This means the project returns **{result:.2f}% annually** on invested capital.")

        elif metric_type == "Payback Period":
            st.markdown("#### 🧮 **Cumulative Cash Flow**")
            cumulative = 0
            payback_year = None
            for t, cf in enumerate(cash_flows):
                cumulative += cf
                st.write(f"Year {t}: Cumulative = {cumulative:,.2f} Rs Cr")
                if cumulative >= 0 and payback_year is None:
                    payback_year = t

            if payback_year is not None:
                st.success(f"**Payback Period = {payback_year} years**")
            else:
                st.warning("Project does not pay back within the given timeline.")

        # Final Result
        st.markdown("---")
        if result is not None:
            st.success(f"**{metric_type} = {result:,.2f} {unit if unit else ''}**")


def camel_to_title(camel_str: str) -> str:
    """
    Convert camelCase to Title Case

    Args:
        camel_str: camelCase string (e.g., "annualSales")

    Returns:
        Title Case string (e.g., "Annual Sales")

    Example:
        >>> camel_to_title("annualSales")
        'Annual Sales'
        >>> camel_to_title("totalSupplyUnits")
        'Total Supply Units'
    """
    import re

    # Insert space before capital letters
    spaced = re.sub(r'([A-Z])', r' \1', camel_str)

    # Title case
    titled = spaced.title().strip()

    return titled


def display_formula_breakdown(formula_text: str) -> None:
    """
    Display visual breakdown of a formula with variable explanations

    Args:
        formula_text: Formula string (e.g., "(AnnualSales × 12) / Supply")

    Example:
        >>> display_formula_breakdown("(AnnualSales × 12) / Supply")
    """
    st.markdown("#### 📐 **Formula Breakdown**")

    # Extract variables from formula (simple regex - can be enhanced)
    import re
    variables = re.findall(r'[A-Za-z]+', formula_text)
    unique_vars = list(set(variables))

    st.code(formula_text, language="text")

    if unique_vars:
        st.markdown("**Variables:**")
        for var in unique_vars:
            st.write(f"- **{camel_to_title(var)}**: {var}")
