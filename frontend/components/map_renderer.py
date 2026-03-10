"""
Chart Renderer for Streamlit Chat Integration

Renders various chart types inline in chat conversations:
- Heat-maps for spatial comparison (e.g., "Compare prices across locations")
- Bar charts for rankings (e.g., "Top 3 projects by size")
- Line charts for trends (e.g., "Sales velocity over time")
- Pie charts for distributions (e.g., "Unit type breakdown")

Automatically triggered by LLM responses based on question intent.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Any, Tuple
import requests


def render_heat_map(
    projects: List[Dict[str, Any]],
    metric: str,
    metric_unit: str = "",
    title: Optional[str] = None,
    height: int = 500
) -> go.Figure:
    """
    Render a heat-map visualization of projects colored by a metric

    Args:
        projects: List of projects with lat, lon, and metric_value
        metric: Metric name being visualized (e.g., "currentPricePSF")
        metric_unit: Unit for the metric (e.g., "INR/sqft")
        title: Optional custom title
        height: Map height in pixels

    Returns:
        Plotly Figure object for st.plotly_chart()

    Example:
        >>> projects = [
        ...     {"projectName": "Sara City", "latitude": 18.755, "longitude": 73.836,
        ...      "metric_value": 3996, "location": "Chakan"},
        ...     ...
        ... ]
        >>> fig = render_heat_map(projects, "currentPricePSF", "INR/sqft")
        >>> st.plotly_chart(fig, use_container_width=True)
    """
    if not projects:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No project data available for visualization",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        return fig

    # Extract data for plotting
    latitudes = [p["latitude"] for p in projects]
    longitudes = [p["longitude"] for p in projects]
    values = [p["metric_value"] for p in projects]
    names = [p["projectName"] for p in projects]
    locations = [p.get("location", "Unknown") for p in projects]

    # Create hover text with formatting
    unit_str = f" {metric_unit}" if metric_unit else ""
    hover_text = [
        f"<b>{names[i]}</b><br>" +
        f"Location: {locations[i]}<br>" +
        f"{metric}: {values[i]:,.2f}{unit_str}<br>" +
        f"Coordinates: ({latitudes[i]:.4f}, {longitudes[i]:.4f})"
        for i in range(len(projects))
    ]

    # Calculate center point for map
    center_lat = sum(latitudes) / len(latitudes)
    center_lon = sum(longitudes) / len(longitudes)

    # Create scatter mapbox with color gradient
    fig = go.Figure(go.Scattermapbox(
        lat=latitudes,
        lon=longitudes,
        mode='markers',
        marker=dict(
            size=14,
            color=values,
            colorscale='RdYlGn_r',  # Red (low) to Yellow to Green (high)
            showscale=True,
            colorbar=dict(
                title=f"{metric}<br>{unit_str}" if unit_str else metric,
                x=1.02
            ),
            opacity=0.8
        ),
        text=hover_text,
        hoverinfo='text',
        name=metric
    ))

    # Set map layout
    map_title = title or f"{metric} Heat-Map ({len(projects)} projects)"

    fig.update_layout(
        title=dict(
            text=map_title,
            x=0.5,
            xanchor='center'
        ),
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=11
        ),
        height=height,
        margin=dict(l=0, r=0, t=40, b=0),
        hovermode='closest'
    )

    return fig


def fetch_and_render_heat_map(
    metric: str,
    region: Optional[str] = None,
    backend_url: str = "http://localhost:8000"
) -> Optional[go.Figure]:
    """
    Fetch heat-map data from backend and render it

    Args:
        metric: Metric to visualize (e.g., "currentPricePSF")
        region: Optional region filter
        backend_url: Backend API base URL

    Returns:
        Plotly Figure or None if request fails

    Example:
        >>> fig = fetch_and_render_heat_map("currentPricePSF", region="Chakan")
        >>> if fig:
        ...     st.plotly_chart(fig, use_container_width=True)
    """
    try:
        # Build API URL
        url = f"{backend_url}/api/maps/heat-map"
        params = {"metric": metric}
        if region:
            params["region"] = region

        # Fetch data from backend
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "success":
            st.error(f"Heat-map data fetch failed: {data.get('error', 'Unknown error')}")
            return None

        projects = data.get("projects", [])

        if not projects:
            st.warning(f"No projects found for metric '{metric}'" + (f" in region '{region}'" if region else ""))
            return None

        # Extract metric unit from first project
        metric_unit = projects[0].get("metric_unit", "") if projects else ""

        # Render map
        title = f"{metric} Heat-Map"
        if region:
            title += f" - {region}"

        return render_heat_map(projects, metric, metric_unit, title=title)

    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch heat-map data: {e}")
        return None
    except Exception as e:
        st.error(f"Heat-map rendering error: {e}")
        return None


def display_heat_map_in_chat(
    metric: str,
    region: Optional[str] = None,
    backend_url: str = "http://localhost:8000"
) -> None:
    """
    Display heat-map inline in Streamlit chat

    This is the main function to call from the chat message renderer.

    Args:
        metric: Metric to visualize
        region: Optional region filter
        backend_url: Backend API base URL

    Example (from streamlit_app.py):
        >>> # In message rendering loop
        >>> if message.get("type") == "heat_map":
        ...     display_heat_map_in_chat(
        ...         metric=message["metric"],
        ...         region=message.get("region")
        ...     )
    """
    fig = fetch_and_render_heat_map(metric, region, backend_url)

    if fig:
        st.plotly_chart(fig, use_container_width=True)


def render_bar_chart(
    data: List[Dict[str, Any]],
    x_field: str,
    y_field: str,
    title: Optional[str] = None,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    orientation: str = "v",
    color_scale: Optional[str] = None,
    height: int = 500
) -> go.Figure:
    """
    Render a bar chart for ranking/comparison

    Args:
        data: List of dicts with data to plot
        x_field: Field name for x-axis (usually project name or category)
        y_field: Field name for y-axis (usually metric value)
        title: Chart title
        x_label: X-axis label
        y_label: Y-axis label
        orientation: 'v' for vertical, 'h' for horizontal
        color_scale: Color scale name (e.g., 'Blues', 'Greens')
        height: Chart height in pixels

    Returns:
        Plotly Figure object

    Example:
        >>> data = [
        ...     {"projectName": "Sara City", "projectSize": 1234, "unit": "sqft"},
        ...     {"projectName": "Nilaay", "projectSize": 2345, "unit": "sqft"}
        ... ]
        >>> fig = render_bar_chart(data, "projectName", "projectSize",
        ...                         title="Top 3 Projects by Size")
        >>> st.plotly_chart(fig, use_container_width=True)
    """
    if not data:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for chart",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        return fig

    # Extract values
    x_values = [item[x_field] for item in data]
    y_values = [item[y_field] for item in data]

    # Handle newlines in project names (replace with spaces)
    x_values = [str(x).replace('\n', ' ') for x in x_values]

    # Create bar chart
    if color_scale:
        # Use color gradient based on values
        fig = go.Figure(go.Bar(
            x=x_values if orientation == "v" else y_values,
            y=y_values if orientation == "v" else x_values,
            orientation=orientation,
            marker=dict(
                color=y_values,
                colorscale=color_scale,
                showscale=True
            ),
            text=[f"{y:,.2f}" for y in y_values],
            textposition='outside'
        ))
    else:
        # Single color bars
        fig = go.Figure(go.Bar(
            x=x_values if orientation == "v" else y_values,
            y=y_values if orientation == "v" else x_values,
            orientation=orientation,
            marker=dict(color='#636EFA'),
            text=[f"{y:,.2f}" for y in y_values],
            textposition='outside'
        ))

    # Update layout
    fig.update_layout(
        title=dict(text=title or f"{y_field} by {x_field}", x=0.5, xanchor='center'),
        xaxis_title=x_label or x_field,
        yaxis_title=y_label or y_field,
        height=height,
        margin=dict(l=50, r=50, t=60, b=50),
        showlegend=False
    )

    return fig


def render_line_chart(
    data: List[Dict[str, Any]],
    x_field: str,
    y_field: str,
    series_field: Optional[str] = None,
    title: Optional[str] = None,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    height: int = 500
) -> go.Figure:
    """
    Render a line chart for trends over time or sequence

    Args:
        data: List of dicts with data to plot
        x_field: Field for x-axis (e.g., "date", "month", "quarter")
        y_field: Field for y-axis (metric value)
        series_field: Optional field to group by (creates multiple lines)
        title: Chart title
        x_label: X-axis label
        y_label: Y-axis label
        height: Chart height in pixels

    Returns:
        Plotly Figure object

    Example:
        >>> data = [
        ...     {"month": "Jan", "salesVelocity": 10, "project": "Sara City"},
        ...     {"month": "Feb", "salesVelocity": 12, "project": "Sara City"},
        ...     ...
        ... ]
        >>> fig = render_line_chart(data, "month", "salesVelocity",
        ...                          series_field="project")
        >>> st.plotly_chart(fig, use_container_width=True)
    """
    if not data:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for chart",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        return fig

    fig = go.Figure()

    if series_field:
        # Group by series_field (multiple lines)
        series_values = list(set(item[series_field] for item in data))

        for series in series_values:
            series_data = [item for item in data if item[series_field] == series]
            x_values = [item[x_field] for item in series_data]
            y_values = [item[y_field] for item in series_data]

            fig.add_trace(go.Scatter(
                x=x_values,
                y=y_values,
                mode='lines+markers',
                name=str(series).replace('\n', ' '),
                line=dict(width=2),
                marker=dict(size=8)
            ))
    else:
        # Single line
        x_values = [item[x_field] for item in data]
        y_values = [item[y_field] for item in data]

        fig.add_trace(go.Scatter(
            x=x_values,
            y=y_values,
            mode='lines+markers',
            line=dict(width=2, color='#636EFA'),
            marker=dict(size=8)
        ))

    # Update layout
    fig.update_layout(
        title=dict(text=title or f"{y_field} over {x_field}", x=0.5, xanchor='center'),
        xaxis_title=x_label or x_field,
        yaxis_title=y_label or y_field,
        height=height,
        margin=dict(l=50, r=50, t=60, b=50),
        hovermode='x unified'
    )

    return fig


def render_pie_chart(
    data: List[Dict[str, Any]],
    label_field: str,
    value_field: str,
    title: Optional[str] = None,
    height: int = 500
) -> go.Figure:
    """
    Render a pie chart for distribution/breakdown

    Args:
        data: List of dicts with data to plot
        label_field: Field for labels (e.g., "unitType", "location")
        value_field: Field for values (e.g., "count", "percentage")
        title: Chart title
        height: Chart height in pixels

    Returns:
        Plotly Figure object

    Example:
        >>> data = [
        ...     {"unitType": "1BHK", "count": 120},
        ...     {"unitType": "2BHK", "count": 200},
        ...     {"unitType": "3BHK", "count": 80}
        ... ]
        >>> fig = render_pie_chart(data, "unitType", "count",
        ...                         title="Unit Type Distribution")
        >>> st.plotly_chart(fig, use_container_width=True)
    """
    if not data:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for chart",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        return fig

    # Extract values
    labels = [str(item[label_field]).replace('\n', ' ') for item in data]
    values = [item[value_field] for item in data]

    # Create pie chart
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.3,  # Donut chart style
        textinfo='label+percent',
        hovertemplate='<b>%{label}</b><br>Value: %{value:,.0f}<br>Percent: %{percent}<extra></extra>'
    ))

    # Update layout
    fig.update_layout(
        title=dict(text=title or f"{value_field} Distribution", x=0.5, xanchor='center'),
        height=height,
        margin=dict(l=50, r=50, t=60, b=50),
        showlegend=True
    )

    return fig


def should_display_heat_map(question: str) -> Optional[Dict[str, str]]:
    """
    Detect if a question should trigger a heat-map visualization

    Args:
        question: User's question

    Returns:
        Dict with {"metric": str, "region": Optional[str]} if heat-map should be shown,
        None otherwise

    Examples:
        >>> should_display_heat_map("Compare prices across all projects")
        {"metric": "currentPricePSF", "region": None}

        >>> should_display_heat_map("Which projects in Chakan have the highest supply?")
        {"metric": "totalSupplyUnits", "region": "Chakan"}

        >>> should_display_heat_map("What is the PSF of Sara City?")
        None  # Single project query, no heat-map needed
    """
    question_lower = question.lower()

    # Keywords that suggest comparison/spatial analysis
    comparison_keywords = [
        "compare", "comparison", "across", "all projects",
        "which projects", "highest", "lowest", "best", "worst",
        "rank", "ranking", "top", "bottom", "heat", "map",
        "visualize", "show me", "distribution", "spread"
    ]

    # Check if question contains comparison keywords
    is_comparison = any(keyword in question_lower for keyword in comparison_keywords)

    if not is_comparison:
        return None

    # Detect metric from question
    metric_mapping = {
        "price": "currentPricePSF",
        "psf": "currentPricePSF",
        "supply": "totalSupplyUnits",
        "units": "totalSupplyUnits",
        "sold": "soldUnits",
        "unsold": "unsoldUnits",
        "revenue": "totalRevenue"
    }

    detected_metric = "currentPricePSF"  # Default
    for keyword, metric in metric_mapping.items():
        if keyword in question_lower:
            detected_metric = metric
            break

    # Detect region from question
    region_keywords = ["chakan", "talegaon", "pune", "hinjewadi"]
    detected_region = None
    for region in region_keywords:
        if region in question_lower:
            detected_region = region.capitalize()
            break

    return {
        "metric": detected_metric,
        "region": detected_region
    }


# Streamlit-specific utilities
def display_map_with_summary(
    projects: List[Dict[str, Any]],
    metric: str,
    metric_unit: str = ""
) -> None:
    """
    Display heat-map with statistical summary

    Args:
        projects: Project data
        metric: Metric name
        metric_unit: Metric unit

    Example:
        >>> display_map_with_summary(projects, "currentPricePSF", "INR/sqft")
    """
    if not projects:
        st.warning("No projects to display")
        return

    # Display heat-map
    fig = render_heat_map(projects, metric, metric_unit)
    st.plotly_chart(fig, use_container_width=True)

    # Display summary statistics
    values = [p["metric_value"] for p in projects]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Projects", len(projects))
    with col2:
        st.metric(f"Avg {metric}", f"{sum(values)/len(values):,.2f} {metric_unit}")
    with col3:
        st.metric(f"Max {metric}", f"{max(values):,.2f} {metric_unit}")
    with col4:
        st.metric(f"Min {metric}", f"{min(values):,.2f} {metric_unit}")


def detect_chart_type(question: str, data: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
    """
    Intelligently detect which chart type to use based on question intent

    Args:
        question: User's question
        data: Optional data that will be visualized (helps with detection)

    Returns:
        Dict with chart configuration:
        {
            "chart_type": "bar|line|pie|heat_map",
            "metric": str,
            "config": {...}  # Chart-specific configuration
        }
        or None if no chart should be displayed

    Examples:
        >>> detect_chart_type("Top 3 projects by project size")
        {"chart_type": "bar", "metric": "projectSize", "config": {"orientation": "v", "limit": 3}}

        >>> detect_chart_type("Compare prices across all projects")
        {"chart_type": "heat_map", "metric": "currentPricePSF", "config": {}}

        >>> detect_chart_type("Unit type breakdown")
        {"chart_type": "pie", "metric": "count", "config": {"label_field": "unitType"}}
    """
    question_lower = question.lower()

    # Chart type indicators
    ranking_keywords = ["top", "bottom", "best", "worst", "rank", "ranking", "highest", "lowest"]
    trend_keywords = ["trend", "over time", "timeline", "growth", "change", "history", "progression"]
    distribution_keywords = ["breakdown", "distribution", "composition", "percentage", "share", "mix"]
    spatial_keywords = ["map", "heat", "location", "geography", "spatial", "across", "compare all"]

    # Detect chart type
    chart_type = None
    if any(kw in question_lower for kw in ranking_keywords):
        chart_type = "bar"
    elif any(kw in question_lower for kw in trend_keywords):
        chart_type = "line"
    elif any(kw in question_lower for kw in distribution_keywords):
        chart_type = "pie"
    elif any(kw in question_lower for kw in spatial_keywords):
        chart_type = "heat_map"

    # If no chart type detected, check for comparison indicators
    if not chart_type:
        comparison_keywords = ["compare", "comparison", "which projects", "all projects", "show me"]
        if any(kw in question_lower for kw in comparison_keywords):
            chart_type = "bar"  # Default to bar for comparisons

    if not chart_type:
        return None  # No visualization needed

    # Detect metric
    metric_mapping = {
        "price": "currentPricePSF",
        "psf": "currentPricePSF",
        "size": "projectSize",
        "supply": "totalSupplyUnits",
        "units": "totalSupplyUnits",
        "sold": "soldUnits",
        "unsold": "unsoldUnits",
        "revenue": "totalRevenue",
        "absorption": "absorptionRate",
        "velocity": "salesVelocity"
    }

    detected_metric = "currentPricePSF"  # Default
    for keyword, metric in metric_mapping.items():
        if keyword in question_lower:
            detected_metric = metric
            break

    # Detect limit for rankings
    limit = None
    for word in question_lower.split():
        if word.isdigit():
            limit = int(word)
            break

    # Build configuration
    config = {}

    if chart_type == "bar":
        config["orientation"] = "v"
        config["limit"] = limit
        config["sort_desc"] = "top" in question_lower or "highest" in question_lower or "best" in question_lower
        config["color_scale"] = "Blues"

    elif chart_type == "heat_map":
        # Extract region if specified
        region_keywords = ["chakan", "talegaon", "pune", "hinjewadi"]
        config["region"] = None
        for region in region_keywords:
            if region in question_lower:
                config["region"] = region.capitalize()
                break

    elif chart_type == "pie":
        # Detect label field for pie chart
        if "unit type" in question_lower or "bhk" in question_lower:
            config["label_field"] = "unitType"
        elif "location" in question_lower or "region" in question_lower:
            config["label_field"] = "location"
        else:
            config["label_field"] = "category"

    elif chart_type == "line":
        # Detect time field
        if "month" in question_lower:
            config["x_field"] = "month"
        elif "quarter" in question_lower:
            config["x_field"] = "quarter"
        elif "year" in question_lower:
            config["x_field"] = "year"
        else:
            config["x_field"] = "date"

    return {
        "chart_type": chart_type,
        "metric": detected_metric,
        "config": config
    }


def render_chart_from_detection(
    question: str,
    data: List[Dict[str, Any]],
    backend_url: str = "http://localhost:8000"
) -> bool:
    """
    Detect chart type and render appropriate visualization

    Args:
        question: User's question
        data: Data to visualize (list of dicts)
        backend_url: Backend API base URL

    Returns:
        True if chart was rendered, False otherwise

    Example (from streamlit_app.py):
        >>> # In chat message rendering
        >>> data = response.get("data", [])
        >>> if render_chart_from_detection(user_question, data):
        ...     # Chart was displayed
        ...     pass
    """
    detection = detect_chart_type(question, data)

    if not detection:
        return False  # No chart needed

    chart_type = detection["chart_type"]
    config = detection["config"]

    try:
        if chart_type == "heat_map":
            # Use existing heat-map function
            display_heat_map_in_chat(
                metric=detection["metric"],
                region=config.get("region"),
                backend_url=backend_url
            )
            return True

        elif chart_type == "bar":
            # Prepare data for bar chart
            if not data:
                return False

            # Sort and limit data
            limit = config.get("limit")
            sort_desc = config.get("sort_desc", True)

            # Assume data has projectName and the metric
            metric = detection["metric"]

            # Find metric field in data
            if data and metric in data[0]:
                sorted_data = sorted(
                    data,
                    key=lambda x: x.get(metric, 0),
                    reverse=sort_desc
                )

                if limit:
                    sorted_data = sorted_data[:limit]

                # Render bar chart
                fig = render_bar_chart(
                    data=sorted_data,
                    x_field="projectName",
                    y_field=metric,
                    title=question,
                    color_scale=config.get("color_scale")
                )
                st.plotly_chart(fig, use_container_width=True)
                return True

        elif chart_type == "pie":
            # Render pie chart
            if not data:
                return False

            fig = render_pie_chart(
                data=data,
                label_field=config.get("label_field", "category"),
                value_field=detection["metric"],
                title=question
            )
            st.plotly_chart(fig, use_container_width=True)
            return True

        elif chart_type == "line":
            # Render line chart
            if not data:
                return False

            fig = render_line_chart(
                data=data,
                x_field=config.get("x_field", "date"),
                y_field=detection["metric"],
                title=question
            )
            st.plotly_chart(fig, use_container_width=True)
            return True

    except Exception as e:
        st.error(f"Chart rendering failed: {e}")
        return False

    return False


def render_chartjs_from_json(chart_json: str) -> bool:
    """
    Render a Chart.js JSON specification as an interactive chart using Plotly

    Args:
        chart_json: JSON string containing Chart.js configuration

    Returns:
        True if chart was rendered, False otherwise

    Example:
        >>> chart_json = '{"type": "bar", "data": {...}, "options": {...}}'
        >>> render_chartjs_from_json(chart_json)
    """
    import json
    import re

    try:
        # Parse JSON
        chart_config = json.loads(chart_json)

        chart_type = chart_config.get("type", "bar")
        data = chart_config.get("data", {})
        options = chart_config.get("options", {})

        # Extract labels and datasets
        labels = data.get("labels", [])
        datasets = data.get("datasets", [])

        if not datasets:
            return False

        # Get the first dataset (for simplicity)
        dataset = datasets[0]
        values = dataset.get("data", [])
        dataset_label = dataset.get("label", "Data")

        # Get title from options
        title = None
        if "plugins" in options and "title" in options["plugins"]:
            title = options["plugins"]["title"].get("text", "Chart")

        # Render based on chart type
        if chart_type == "bar":
            fig = go.Figure(go.Bar(
                x=labels,
                y=values,
                name=dataset_label,
                marker=dict(
                    color='rgba(0, 0, 0, 0.7)',  # Black bars for minimalist theme
                    line=dict(color='rgba(0, 0, 0, 1)', width=1)
                ),
                text=[f"{v:,.0f}" for v in values],
                textposition='outside'
            ))

            # Update layout with minimal style
            fig.update_layout(
                title=dict(text=title, x=0.5, xanchor='center', font=dict(size=16, color='#000000')),
                xaxis_title=options.get("scales", {}).get("x", {}).get("title", {}).get("text", ""),
                yaxis_title=options.get("scales", {}).get("y", {}).get("title", {}).get("text", ""),
                height=400,
                margin=dict(l=50, r=50, t=60, b=50),
                showlegend=False,
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(family='Inter, sans-serif', size=14, color='#000000'),
                xaxis=dict(
                    showgrid=False,
                    showline=True,
                    linecolor='#E5E5E5',
                    linewidth=1
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='#F7F7F8',
                    showline=True,
                    linecolor='#E5E5E5',
                    linewidth=1
                )
            )

            st.plotly_chart(fig, use_container_width=True)
            return True

        elif chart_type == "line":
            fig = go.Figure(go.Scatter(
                x=labels,
                y=values,
                mode='lines+markers',
                name=dataset_label,
                line=dict(color='rgba(0, 0, 0, 0.8)', width=2),
                marker=dict(size=8, color='rgba(0, 0, 0, 0.8)')
            ))

            fig.update_layout(
                title=dict(text=title, x=0.5, xanchor='center', font=dict(size=16, color='#000000')),
                xaxis_title=options.get("scales", {}).get("x", {}).get("title", {}).get("text", ""),
                yaxis_title=options.get("scales", {}).get("y", {}).get("title", {}).get("text", ""),
                height=400,
                margin=dict(l=50, r=50, t=60, b=50),
                showlegend=False,
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(family='Inter, sans-serif', size=14, color='#000000'),
                xaxis=dict(showgrid=False, showline=True, linecolor='#E5E5E5'),
                yaxis=dict(showgrid=True, gridcolor='#F7F7F8', showline=True, linecolor='#E5E5E5')
            )

            st.plotly_chart(fig, use_container_width=True)
            return True

        elif chart_type == "pie":
            fig = go.Figure(go.Pie(
                labels=labels,
                values=values,
                hole=0.3,
                marker=dict(colors=['#000000', '#333333', '#666666', '#999999', '#CCCCCC']),
                textfont=dict(color='white', size=14)
            ))

            fig.update_layout(
                title=dict(text=title, x=0.5, xanchor='center', font=dict(size=16, color='#000000')),
                height=400,
                margin=dict(l=50, r=50, t=60, b=50),
                showlegend=True,
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(family='Inter, sans-serif', size=14, color='#000000')
            )

            st.plotly_chart(fig, use_container_width=True)
            return True

    except Exception as e:
        st.error(f"Failed to render chart: {e}")
        return False

    return False


def detect_and_render_chart_json(text: str) -> bool:
    """
    Detect if text contains a Chart.js JSON specification and render it

    Args:
        text: Text that may contain chart JSON

    Returns:
        True if chart was found and rendered, False otherwise
    """
    import re
    import json

    # Try to find JSON object in the text
    # Look for pattern: {"type": "bar"|"line"|"pie", "data": {...}, ...}
    json_pattern = r'\{[\s\S]*?"type"\s*:\s*"(?:bar|line|pie)"[\s\S]*?"data"\s*:[\s\S]*?\}'

    matches = re.finditer(json_pattern, text, re.MULTILINE)

    for match in matches:
        json_str = match.group(0)

        # Try to parse and render
        try:
            # Validate it's proper JSON
            json.loads(json_str)

            # Render the chart
            if render_chartjs_from_json(json_str):
                return True
        except:
            continue

    return False
