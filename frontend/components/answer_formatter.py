"""
Answer Formatter - Transform JSON responses into human-readable format
Shows answer upfront, then collapsible chain-of-thought explanation
"""

import streamlit as st
from typing import Dict, Any, Optional


class AnswerFormatter:
    """Format backend responses with answer upfront and collapsible explanations"""

    @staticmethod
    def format_query_result(result: Dict[str, Any]) -> None:
        """
        Format query result with:
        1. Answer upfront (prominent)
        2. Collapsible chain-of-thought explanation
        3. Collapsible provenance/data source

        Args:
            result: Backend response with status, answer, calculation, provenance
        """
        if result.get('status') != 'success':
            st.error(f"❌ {result.get('error', 'Query failed')}")
            return

        answer = result.get('answer', {})
        understanding = answer.get('understanding', {})
        calc_result = answer.get('result', {})
        calculation = answer.get('calculation', {})
        provenance = answer.get('provenance', {})

        # ===================================================================
        # ANSWER UPFRONT - Prominent display
        # ===================================================================
        AnswerFormatter._render_answer_upfront(calc_result, understanding)

        # ===================================================================
        # COLLAPSIBLE: How We Calculated This
        # ===================================================================
        if calculation:
            AnswerFormatter._render_calculation_explanation(calculation, understanding)

        # ===================================================================
        # COLLAPSIBLE: Data Source & Provenance
        # ===================================================================
        if provenance:
            AnswerFormatter._render_provenance(provenance)

    @staticmethod
    def _render_answer_upfront(calc_result: Dict, understanding: Dict) -> None:
        """Render the answer prominently at the top"""

        # Get the answer value and text
        value = calc_result.get('value')
        text = calc_result.get('text', str(value))
        unit = calc_result.get('unit', '')

        # Display prominently
        st.markdown("### 📊 Answer")

        # Large metric display
        if value is not None:
            # Use st.metric for prominent display
            layer = understanding.get('layer', 'N/A')
            dimension = understanding.get('dimension', 'N/A')
            operation = understanding.get('operation', 'N/A')

            # Create columns for layout
            col1, col2 = st.columns([2, 1])

            with col1:
                # Main answer
                st.metric(
                    label="Result",
                    value=text,
                    help=f"Layer {layer} | Dimension: {dimension} | Operation: {operation}"
                )

            with col2:
                # Context badges
                st.markdown(f"""
                <div style="padding: 10px; background-color: #f0f2f6; border-radius: 5px; margin-top: 10px;">
                    <div style="font-size: 12px; color: #666;">
                        <strong>Layer:</strong> {layer}<br>
                        <strong>Dimension:</strong> {dimension}<br>
                        <strong>Operation:</strong> {operation}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        else:
            st.info(text)

        st.markdown("---")

    @staticmethod
    def _render_calculation_explanation(calculation: Dict, understanding: Dict) -> None:
        """Render collapsible step-by-step explanation"""

        with st.expander("🔍 **How We Calculated This** (Step-by-Step)", expanded=False):

            # Step 1: Understanding the Query
            st.markdown("#### Step 1: Understanding Your Query")

            layer = understanding.get('layer', 'N/A')
            dimension = understanding.get('dimension', 'N/A')
            operation = understanding.get('operation', 'N/A')

            layer_descriptions = {
                0: "Layer 0 - Raw Dimensions (atomic data from Liases Foras)",
                1: "Layer 1 - Derived Metrics (calculated ratios like PSF, ASP)",
                2: "Layer 2 - Financial Metrics (NPV, IRR, payback)",
                3: "Layer 3 - Optimization Solutions (product mix, scenarios)"
            }

            operation_descriptions = {
                "AGGREGATION": "Combining multiple values (sum, average, count)",
                "DIVISION": "Ratio calculation (creating derived metric)",
                "FILTER": "Selecting specific subset of data",
                "CALCULATION": "Complex multi-step computation"
            }

            st.markdown(f"""
- **Query Type:** {layer_descriptions.get(layer, f'Layer {layer}')}
- **Dimension:** `{dimension}` (what we're measuring)
- **Operation:** {operation_descriptions.get(operation, operation)}
            """)

            # Step 2: Formula
            if calculation.get('formula'):
                st.markdown("#### Step 2: Mathematical Formula")
                formula = calculation.get('formula')
                st.code(formula, language="text")

                # Explain formula in plain English
                AnswerFormatter._explain_formula(formula, dimension, operation)

            # Step 3: Data Breakdown
            if calculation.get('breakdown'):
                st.markdown("#### Step 3: Data Used in Calculation")

                breakdown = calculation.get('breakdown')
                project_count = calculation.get('projectCount', len(breakdown))

                st.markdown(f"**Projects analyzed:** {project_count}")

                # Show breakdown as table
                if isinstance(breakdown, list) and len(breakdown) > 0:
                    import pandas as pd

                    # Convert to DataFrame for better display
                    df = pd.DataFrame(breakdown)

                    # Rename columns for readability
                    if 'projectName' in df.columns:
                        df = df.rename(columns={'projectName': 'Project Name', 'value': 'Value'})

                    # Display as table
                    st.dataframe(df, use_container_width=True, hide_index=True)

                    # Summary stats
                    if 'Value' in df.columns:
                        total = calculation.get('total', df['Value'].sum())
                        average = total / len(df)

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total", f"{total:,.0f}")
                        with col2:
                            st.metric("Count", len(df))
                        with col3:
                            st.metric("Average", f"{average:,.1f}")

            # Step 4: Final Calculation
            st.markdown("#### Step 4: Final Result")

            if calculation.get('formula') and calculation.get('total'):
                total = calculation.get('total')
                count = calculation.get('projectCount')
                result = total / count if count else 0

                st.markdown(f"""
**Calculation:**
```
{calculation.get('formula')}
= {total} ÷ {count}
= {result:.1f}
```
                """)

    @staticmethod
    def _explain_formula(formula: str, dimension: str, operation: str) -> None:
        """Explain formula in plain English"""

        explanations = {
            ("U", "AGGREGATION"): "We're calculating the **average number of units** across all projects.",
            ("CF", "AGGREGATION"): "We're calculating the **total cash flow** across all projects.",
            ("CF/L²", "DIVISION"): "We're calculating **Price Per Square Foot (PSF)** by dividing total revenue by total area.",
            ("CF/U", "DIVISION"): "We're calculating **Average Selling Price (ASP)** by dividing total revenue by total units.",
        }

        key = (dimension, operation)
        explanation = explanations.get(key, f"We're performing a {operation.lower()} on {dimension}.")

        st.info(f"💡 **In Plain English:** {explanation}")

    @staticmethod
    def _render_provenance(provenance: Dict) -> None:
        """Render collapsible provenance/data source information"""

        with st.expander("📚 **Data Source & Provenance**", expanded=False):

            # V4 API uses data_sources (plural, list) instead of dataSource (singular)
            data_sources = provenance.get('data_sources', [])
            if data_sources:
                # Join list of sources, always show "Liases Foras" if present
                data_source = ', '.join(data_sources)
            else:
                # Fallback to old v3 format for backwards compatibility
                data_source = provenance.get('dataSource', 'Liases Foras')

            layer = provenance.get('layer', 'N/A')
            target_attr = provenance.get('targetAttribute', 'N/A')
            operation = provenance.get('operation', 'N/A')

            st.markdown(f"""
**Data Source:** {data_source}

**Analysis Details:**
- **Layer:** {layer}
- **Target Attribute:** {target_attr}
- **Operation:** {operation}

**Data Quality:**
- All values validated for type and range
- Missing values excluded from calculation
- Nested data structure properly extracted
            """)

            # Show raw provenance for debugging
            with st.expander("🔧 Raw Provenance (Debug)", expanded=False):
                st.json(provenance)


# Convenience function for direct use
def format_answer(result: Dict[str, Any]) -> None:
    """
    Format and display query result with answer upfront and collapsible explanations

    Usage:
        from frontend.components.answer_formatter import format_answer
        format_answer(api_response)
    """
    AnswerFormatter.format_query_result(result)
