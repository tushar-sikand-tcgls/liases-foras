"""
Chart Renderer Component
Renders Plotly charts from backend-generated chart specifications
"""

import streamlit as st
import plotly.graph_objects as go
from typing import Dict, Any, Optional


def render_chart_from_spec(chart_spec: Dict[str, Any], use_container_width: bool = True) -> None:
    """
    Render a Plotly chart from a backend-generated chart specification

    Args:
        chart_spec: Chart specification dictionary with structure:
            {
                "chart_type": str,
                "data": list of trace dictionaries,
                "layout": dict with layout configuration,
                "metadata": dict with chart metadata (optional)
            }
        use_container_width: Whether to use full container width

    Example chart_spec:
        {
            "chart_type": "line",
            "data": [
                {
                    "type": "scatter",
                    "mode": "lines+markers",
                    "x": ["Q1 24-25", "Q2 24-25", "Q3 24-25", "Q4 24-25"],
                    "y": [9.63, 9.79, 9.81, 10.33],
                    "name": "Supply Area",
                    "line": {"width": 2},
                    "marker": {"size": 6}
                }
            ],
            "layout": {
                "title": "Quarterly Supply Area",
                "xaxis": {"title": "Quarter"},
                "yaxis": {"title": "Supply Area (mn sq ft)"},
                "hovermode": "x unified",
                "height": 500
            }
        }
    """
    if not chart_spec or not isinstance(chart_spec, dict):
        st.warning("Invalid chart specification")
        return

    # Extract components
    data = chart_spec.get("data", [])
    layout = chart_spec.get("layout", {})
    metadata = chart_spec.get("metadata", {})

    if not data:
        st.info("No chart data available")
        return

    try:
        # Create Plotly figure
        fig = go.Figure(data=data, layout=layout)

        # Apply theme customization for better integration with Streamlit
        fig.update_layout(
            template="plotly_white",
            font=dict(
                family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif",
                size=12
            ),
            margin=dict(l=10, r=10, t=50, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )

        # Render chart
        st.plotly_chart(fig, use_container_width=use_container_width)

        # Optionally show chart metadata
        if metadata and st.session_state.get("show_chart_metadata", False):
            with st.expander("📊 Chart Details"):
                st.json(metadata)

    except Exception as e:
        st.error(f"Error rendering chart: {str(e)}")
        # Show chart spec for debugging
        with st.expander("🐛 Debug: Chart Specification"):
            st.json(chart_spec)


def check_and_render_charts(response: Dict[str, Any]) -> bool:
    """
    Check if response contains chart specifications and render them

    Args:
        response: API response dictionary

    Returns:
        True if charts were rendered, False otherwise
    """
    # Check for chart_spec in response
    chart_spec = response.get("chart_spec")

    if chart_spec and isinstance(chart_spec, dict):
        # Add visual separator
        st.markdown("---")
        st.markdown("### 📊 Data Visualization")

        # Render the chart
        render_chart_from_spec(chart_spec)

        return True

    return False


def render_multiple_charts(charts: list, cols: int = 2) -> None:
    """
    Render multiple charts in a grid layout

    Args:
        charts: List of chart specifications
        cols: Number of columns in the grid
    """
    if not charts:
        return

    # Create columns for grid layout
    for i in range(0, len(charts), cols):
        chart_cols = st.columns(cols)

        for j, col in enumerate(chart_cols):
            chart_index = i + j
            if chart_index < len(charts):
                with col:
                    render_chart_from_spec(charts[chart_index], use_container_width=True)


def get_chart_download_button(chart_spec: Dict[str, Any], filename: str = "chart") -> None:
    """
    Add a download button for chart as static image (future enhancement)

    Args:
        chart_spec: Chart specification
        filename: Filename for download (without extension)

    Note: This is a placeholder for future implementation
    Currently Plotly in Streamlit doesn't support easy image export
    """
    # Future: Add export functionality
    # For now, users can use Plotly's built-in camera icon to download
    pass
