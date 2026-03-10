"""
Chart Generation Service
Exposes charting capabilities as tools for Gemini to enhance user experience
"""

from typing import Dict, List, Any, Optional, Literal
import json
from datetime import datetime


ChartType = Literal["line", "bar", "column", "pie", "scatter", "area", "multi_line", "grouped_bar"]


class ChartService:
    """
    Service for generating chart specifications that can be rendered by frontend

    This service:
    1. Analyzes data structure to recommend appropriate chart types
    2. Generates Plotly-compatible chart specifications
    3. Exposes as tools for Gemini to invoke
    """

    @staticmethod
    def recommend_chart_type(data: List[Dict[str, Any]], context: str = "") -> str:
        """
        Analyze data and recommend the most appropriate chart type

        Args:
            data: List of data dictionaries
            context: Optional context about what the data represents

        Returns:
            Recommended chart type
        """
        if not data or len(data) == 0:
            return "table"

        num_rows = len(data)
        keys = list(data[0].keys()) if data else []

        # Count numeric vs non-numeric columns
        numeric_cols = []
        categorical_cols = []

        for key in keys:
            sample_val = data[0].get(key)
            if isinstance(sample_val, (int, float)):
                numeric_cols.append(key)
            else:
                categorical_cols.append(key)

        # Decision logic
        if num_rows <= 10 and len(numeric_cols) == 1:
            # Small dataset with one metric → pie chart or bar chart
            return "pie"
        elif num_rows > 10 and any(keyword in str(keys).lower() for keyword in ['quarter', 'year', 'month', 'date', 'time']):
            # Time-series data → line chart
            return "line"
        elif len(numeric_cols) >= 2:
            # Multiple metrics → multi-line or grouped bar
            return "multi_line"
        elif num_rows > 5:
            # Many rows → column chart
            return "column"
        else:
            # Default to bar chart
            return "bar"

    @staticmethod
    def create_line_chart(
        data: List[Dict[str, Any]],
        x_field: str,
        y_fields: List[str],
        title: str = "Line Chart",
        x_label: str = "",
        y_label: str = "",
        height: int = 500
    ) -> Dict[str, Any]:
        """
        Create a line chart specification

        Args:
            data: List of data dictionaries
            x_field: Field name for X-axis
            y_fields: List of field names for Y-axis (supports multiple lines)
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            height: Chart height in pixels

        Returns:
            Plotly chart specification
        """
        traces = []

        for y_field in y_fields:
            traces.append({
                "type": "scatter",
                "mode": "lines+markers",
                "x": [row[x_field] for row in data],
                "y": [row[y_field] for row in data],
                "name": y_field.replace('_', ' ').title(),
                "line": {"width": 2},
                "marker": {"size": 6}
            })

        layout = {
            "title": title,
            "xaxis": {"title": x_label or x_field.replace('_', ' ').title()},
            "yaxis": {"title": y_label},
            "hovermode": "x unified",
            "height": height
        }

        return {
            "chart_type": "line",
            "data": traces,
            "layout": layout
        }

    @staticmethod
    def create_bar_chart(
        data: List[Dict[str, Any]],
        x_field: str,
        y_field: str,
        title: str = "Bar Chart",
        x_label: str = "",
        y_label: str = "",
        orientation: Literal["v", "h"] = "v",
        height: int = 500
    ) -> Dict[str, Any]:
        """
        Create a bar/column chart specification

        Args:
            data: List of data dictionaries
            x_field: Field name for X-axis (categories)
            y_field: Field name for Y-axis (values)
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            orientation: 'v' for vertical (column), 'h' for horizontal (bar)
            height: Chart height in pixels

        Returns:
            Plotly chart specification
        """
        trace = {
            "type": "bar",
            "x": [row[x_field] for row in data],
            "y": [row[y_field] for row in data],
            "name": y_field.replace('_', ' ').title(),
            "orientation": orientation
        }

        layout = {
            "title": title,
            "xaxis": {"title": x_label or x_field.replace('_', ' ').title()},
            "yaxis": {"title": y_label or y_field.replace('_', ' ').title()},
            "height": height
        }

        return {
            "chart_type": "bar",
            "data": [trace],
            "layout": layout
        }

    @staticmethod
    def create_pie_chart(
        data: List[Dict[str, Any]],
        label_field: str,
        value_field: str,
        title: str = "Pie Chart",
        height: int = 500
    ) -> Dict[str, Any]:
        """
        Create a pie chart specification

        Args:
            data: List of data dictionaries
            label_field: Field name for labels
            value_field: Field name for values
            title: Chart title
            height: Chart height in pixels

        Returns:
            Plotly chart specification
        """
        trace = {
            "type": "pie",
            "labels": [row[label_field] for row in data],
            "values": [row[value_field] for row in data],
            "textinfo": "label+percent",
            "hoverinfo": "label+value+percent"
        }

        layout = {
            "title": title,
            "height": height
        }

        return {
            "chart_type": "pie",
            "data": [trace],
            "layout": layout
        }

    @staticmethod
    def create_grouped_bar_chart(
        data: List[Dict[str, Any]],
        x_field: str,
        y_fields: List[str],
        title: str = "Grouped Bar Chart",
        x_label: str = "",
        y_label: str = "",
        height: int = 500
    ) -> Dict[str, Any]:
        """
        Create a grouped bar chart specification (multiple metrics side-by-side)

        Args:
            data: List of data dictionaries
            x_field: Field name for X-axis (categories)
            y_fields: List of field names for Y-axis (multiple series)
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            height: Chart height in pixels

        Returns:
            Plotly chart specification
        """
        traces = []

        for y_field in y_fields:
            traces.append({
                "type": "bar",
                "x": [row[x_field] for row in data],
                "y": [row[y_field] for row in data],
                "name": y_field.replace('_', ' ').title()
            })

        layout = {
            "title": title,
            "xaxis": {"title": x_label or x_field.replace('_', ' ').title()},
            "yaxis": {"title": y_label},
            "barmode": "group",
            "height": height
        }

        return {
            "chart_type": "grouped_bar",
            "data": traces,
            "layout": layout
        }

    @staticmethod
    def create_area_chart(
        data: List[Dict[str, Any]],
        x_field: str,
        y_fields: List[str],
        title: str = "Area Chart",
        x_label: str = "",
        y_label: str = "",
        stacked: bool = False,
        height: int = 500
    ) -> Dict[str, Any]:
        """
        Create an area chart specification

        Args:
            data: List of data dictionaries
            x_field: Field name for X-axis
            y_fields: List of field names for Y-axis
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            stacked: Whether to stack areas
            height: Chart height in pixels

        Returns:
            Plotly chart specification
        """
        traces = []

        for i, y_field in enumerate(y_fields):
            trace = {
                "type": "scatter",
                "mode": "lines",
                "x": [row[x_field] for row in data],
                "y": [row[y_field] for row in data],
                "name": y_field.replace('_', ' ').title(),
                "fill": "tonexty" if i > 0 and stacked else "tozeroy",
                "line": {"width": 0}
            }
            traces.append(trace)

        layout = {
            "title": title,
            "xaxis": {"title": x_label or x_field.replace('_', ' ').title()},
            "yaxis": {"title": y_label},
            "hovermode": "x unified",
            "height": height
        }

        return {
            "chart_type": "area",
            "data": traces,
            "layout": layout
        }

    @staticmethod
    def create_scatter_chart(
        data: List[Dict[str, Any]],
        x_field: str,
        y_field: str,
        title: str = "Scatter Chart",
        x_label: str = "",
        y_label: str = "",
        size_field: Optional[str] = None,
        color_field: Optional[str] = None,
        height: int = 500
    ) -> Dict[str, Any]:
        """
        Create a scatter chart specification

        Args:
            data: List of data dictionaries
            x_field: Field name for X-axis
            y_field: Field name for Y-axis
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            size_field: Optional field for bubble size
            color_field: Optional field for color coding
            height: Chart height in pixels

        Returns:
            Plotly chart specification
        """
        trace = {
            "type": "scatter",
            "mode": "markers",
            "x": [row[x_field] for row in data],
            "y": [row[y_field] for row in data],
            "marker": {
                "size": [row[size_field] for row in data] if size_field else 10
            }
        }

        if color_field:
            trace["marker"]["color"] = [row[color_field] for row in data]
            trace["marker"]["colorscale"] = "Viridis"
            trace["marker"]["showscale"] = True

        layout = {
            "title": title,
            "xaxis": {"title": x_label or x_field.replace('_', ' ').title()},
            "yaxis": {"title": y_label or y_field.replace('_', ' ').title()},
            "height": height
        }

        return {
            "chart_type": "scatter",
            "data": [trace],
            "layout": layout
        }

    @staticmethod
    def auto_generate_chart(
        data: List[Dict[str, Any]],
        chart_type: Optional[str] = None,
        title: str = "",
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Automatically generate the best chart for the given data

        This is the main tool-callable function that Gemini will use.

        Args:
            data: List of data dictionaries
            chart_type: Optional explicit chart type, otherwise auto-detected
            title: Chart title
            description: Description of what the chart shows

        Returns:
            Chart specification with metadata
        """
        if not data or len(data) == 0:
            return {
                "status": "error",
                "message": "No data provided for chart generation"
            }

        # Auto-detect chart type if not specified
        if not chart_type:
            chart_type = ChartService.recommend_chart_type(data, description)

        keys = list(data[0].keys())

        # Identify likely X and Y fields
        x_field = None
        y_fields = []

        # Look for time/category field for X-axis
        for key in keys:
            if any(keyword in key.lower() for keyword in ['quarter', 'year', 'month', 'date', 'time', 'period']):
                x_field = key
                break
            elif isinstance(data[0][key], str):
                x_field = key
                break

        if not x_field:
            x_field = keys[0]

        # Remaining numeric fields are Y-axis candidates
        for key in keys:
            if key != x_field and isinstance(data[0][key], (int, float)):
                y_fields.append(key)

        # Generate chart based on type
        if chart_type == "line" and len(y_fields) > 0:
            chart_spec = ChartService.create_line_chart(
                data, x_field, y_fields, title=title or f"{', '.join(y_fields)} over {x_field}"
            )
        elif chart_type == "bar" and len(y_fields) > 0:
            chart_spec = ChartService.create_bar_chart(
                data, x_field, y_fields[0], title=title or f"{y_fields[0]} by {x_field}"
            )
        elif chart_type == "column" and len(y_fields) > 0:
            chart_spec = ChartService.create_bar_chart(
                data, x_field, y_fields[0], title=title or f"{y_fields[0]} by {x_field}", orientation="v"
            )
        elif chart_type == "pie" and len(y_fields) > 0:
            chart_spec = ChartService.create_pie_chart(
                data, x_field, y_fields[0], title=title or f"Distribution of {y_fields[0]}"
            )
        elif chart_type == "multi_line" and len(y_fields) > 1:
            chart_spec = ChartService.create_line_chart(
                data, x_field, y_fields, title=title or f"Trends: {', '.join(y_fields)}"
            )
        elif chart_type == "grouped_bar" and len(y_fields) > 1:
            chart_spec = ChartService.create_grouped_bar_chart(
                data, x_field, y_fields, title=title or f"Comparison: {', '.join(y_fields)}"
            )
        elif chart_type == "area" and len(y_fields) > 0:
            chart_spec = ChartService.create_area_chart(
                data, x_field, y_fields, title=title or f"Area: {', '.join(y_fields)}"
            )
        else:
            # Fallback to bar chart
            chart_spec = ChartService.create_bar_chart(
                data, x_field, y_fields[0] if y_fields else x_field,
                title=title or "Data Visualization"
            )

        # Add metadata
        chart_spec["metadata"] = {
            "generated_at": datetime.utcnow().isoformat(),
            "data_rows": len(data),
            "fields": keys,
            "description": description,
            "recommended_type": chart_type
        }

        return {
            "status": "success",
            "chart": chart_spec
        }


# Singleton instance
_chart_service = None

def get_chart_service() -> ChartService:
    """Get singleton instance of ChartService"""
    global _chart_service
    if _chart_service is None:
        _chart_service = ChartService()
    return _chart_service
