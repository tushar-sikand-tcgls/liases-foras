"""
Answer Transformer - Convert JSON responses to clean GPT-style text
Natural paragraphs, headings, and bullet points (no excessive emojis)
"""

from typing import Dict, Any, Optional
import streamlit as st


class AnswerTransformer:
    """Transform JSON query results to GPT-style human-readable text"""

    @staticmethod
    def transform_to_text(result: Dict[str, Any], display_mode: str = "bullets") -> str:
        """
        Transform JSON result to clean GPT-style text

        Args:
            result: Backend response with status, answer, calculation, etc.
            display_mode: "bullets" or "table" (for multiple rows)

        Returns:
            Formatted text string ready to display (GPT-style)
        """
        if result.get('status') != 'success':
            return f"Error: {result.get('error', 'Query failed')}"

        answer = result.get('answer', {})

        # Extract key components
        understanding = answer.get('understanding', {})
        calc_result = answer.get('result', {})
        calculation = answer.get('calculation', {})
        provenance = answer.get('provenance', {})

        # Build output text
        output_lines = []

        # ===================================================================
        # ANSWER (Single line or multiple rows) - GPT STYLE
        # ===================================================================

        result_type = calc_result.get('type')

        if result_type == 'table':
            # Multiple rows → Bullets or Table
            rows = calc_result.get('rows', [])
            count = calc_result.get('count', len(rows))

            if display_mode == "table":
                # Return None to signal caller to use st.table()
                return None
            else:
                # Bullets format (GPT-style: clean, simple)
                output_lines.append(f"Here are the top {count} results:\n")

                for i, row in enumerate(rows, 1):
                    # Extract attributes
                    name = row.get('projectName', row.get('name', 'Unknown'))
                    value = row.get('value', 'N/A')

                    # Additional attributes (comma-separated)
                    extra_attrs = []
                    for key, val in row.items():
                        if key not in ['projectName', 'name', 'value']:
                            extra_attrs.append(f"{key}: {val}")

                    # Format bullet (simple, no bold, natural)
                    if extra_attrs:
                        output_lines.append(f"{i}. **{name}** - {value} ({', '.join(extra_attrs)})")
                    else:
                        output_lines.append(f"{i}. **{name}** - {value}")

        else:
            # Single answer → Natural paragraph (GPT-style)
            text = calc_result.get('text', calc_result.get('value', 'N/A'))
            unit = calc_result.get('unit', '')

            # Create natural answer paragraph
            dimension = understanding.get('dimension', '')
            operation = understanding.get('operation', '')

            if dimension and operation:
                # Contextual paragraph based on operation and dimension
                if operation.upper() == 'AGGREGATION':
                    # Check if this is a sum/total, average, or standard deviation
                    formula = calculation.get('formula', '') if calculation else ''
                    # provenance is already defined on line 34 from answer.get('provenance', {})
                    operation_type = provenance.get('operation', '')

                    if operation_type == 'standard_deviation' or 's = √' in formula or 'σ' in formula:
                        # This is a standard deviation
                        output_lines.append(f"The standard deviation is **{text}**.")
                    elif operation_type == 'mean' or ('/' in formula and 'Σ' in formula):
                        # This is an average (has both Σ and division)
                        output_lines.append(f"The average is **{text}**.")
                    elif operation_type == 'sum' or ('Σ' in formula and '/' not in formula) or 'sum' in formula.lower():
                        # This is a sum/total (has Σ but no division)
                        output_lines.append(f"The total is **{text}**.")
                    else:
                        # Fallback for other aggregations
                        output_lines.append(f"The result is **{text}**.")
                elif operation.upper() == 'DIVISION':
                    output_lines.append(f"The calculated value is **{text}**.")
                elif operation.upper() == 'FILTER':
                    output_lines.append(f"Based on the filter criteria, the result is **{text}**.")
                else:
                    output_lines.append(f"The result is **{text}**.")
            else:
                # Simple statement
                output_lines.append(f"{text}")

        # ===================================================================
        # OPTIONAL: Calculation Details (Collapsible by default)
        # ===================================================================

        if calculation:
            output_lines.append("")  # Blank line

            # Start collapsible section (HTML details tag)
            output_lines.append('<details>')
            output_lines.append('<summary><strong>Show calculation details</strong></summary>')
            output_lines.append("")  # Blank line for spacing

            formula = calculation.get('formula')
            if formula:
                output_lines.append(f"**Formula:** `{formula}`")
                output_lines.append("")

            project_count = calculation.get('projectCount')
            total = calculation.get('total')
            mean = calculation.get('mean')
            variance = calculation.get('variance')
            std_dev = calculation.get('stdDev')

            if project_count:
                output_lines.append(f"**Number of projects analyzed:** {project_count}")

            # Show mean for standard deviation calculations
            if mean is not None:
                output_lines.append(f"**Mean (X̄):** {mean}")

            # Show variance for standard deviation calculations
            if variance is not None:
                output_lines.append(f"**Variance (s²):** {variance}")

            # Show total for sum calculations
            if total is not None:
                output_lines.append(f"**Total sum:** {total}")

            output_lines.append("")  # Blank line before closing
            output_lines.append('</details>')  # End collapsible section

        # ===================================================================
        # OPTIONAL: Data Source (minimal footer)
        # ===================================================================

        if provenance:
            output_lines.append("")
            data_source = provenance.get('dataSource', 'Unknown')
            output_lines.append(f"*Source: {data_source}*")

        return "\n".join(output_lines)

    @staticmethod
    def transform_to_table(result: Dict[str, Any]) -> Optional[Any]:
        """
        Transform JSON result to table data for st.table()

        Returns:
            DataFrame or list of dicts suitable for st.table()
        """
        if result.get('status') != 'success':
            return None

        answer = result.get('answer', {})
        calc_result = answer.get('result', {})

        if calc_result.get('type') == 'table':
            rows = calc_result.get('rows', [])

            if rows:
                import pandas as pd

                # Convert to DataFrame for better display
                df = pd.DataFrame(rows)

                # Rename columns for readability
                column_renames = {
                    'projectName': 'Project Name',
                    'value': 'Value'
                }

                df = df.rename(columns=column_renames)

                return df

        return None


# =============================================================================
# SIMPLE TRANSFORMATION FUNCTION (DIRECT USE)
# =============================================================================

def transform_answer(result: Dict[str, Any], display_mode: str = "bullets") -> tuple:
    """
    Simple function to transform answer

    Args:
        result: Backend JSON response
        display_mode: "bullets" or "table"

    Returns:
        (text_output, table_data) tuple
        - If bullets mode: (text, None)
        - If table mode and has table data: (None, DataFrame)
        - Otherwise: (text, None)
    """
    transformer = AnswerTransformer()

    # Check if this is a table result and display_mode is table
    if display_mode == "table":
        table_data = transformer.transform_to_table(result)
        if table_data is not None:
            return (None, table_data)

    # Otherwise, return text
    text = transformer.transform_to_text(result, display_mode)
    return (text, None)
