"""
Dynamic Renderer - Main Orchestrator

Coordinates schema analysis, pattern matching, and widget rendering
to automatically generate UI from JSON responses.
"""

from typing import Dict, Any
import streamlit as st
from components.schema_analyzer import SchemaAnalyzer
from components.pattern_matcher import PatternMatcher
from components.capability_config import get_capability_config
from components.formatters import auto_format_value, format_key_name
from components.calculation_explainer import add_calculation_explainer


class DynamicRenderer:
    """Main orchestrator for dynamic widget rendering"""
    
    def __init__(self):
        self.analyzer = SchemaAnalyzer()
        self.matcher = PatternMatcher()
    
    def render_response(self, response: Dict[str, Any]) -> None:
        """
        Main entry point: Render complete API response
        
        Args:
            response: MCPQueryResponse dictionary with structure:
                {
                    "queryId": str,
                    "status": str,
                    "layer": int,
                    "capability": str,
                    "result": dict,
                    "provenance": dict,
                    "executionTime_ms": float
                }
        """
        # Extract components
        capability = response.get("capability", "unknown")
        result = response.get("result", {})
        provenance = response.get("provenance", {})
        exec_time = response.get("executionTime_ms", 0)
        
        # Get capability-specific config
        config = get_capability_config(capability)
        
        # Render title
        if "title" in config:
            st.markdown(f"### {config['title']}")
        
        # Render description
        if "description" in config:
            st.caption(config['description'])
        
        # Analyze result structure
        metadata = self.analyzer.analyze(result)
        
        # Match to appropriate template
        template = self.matcher.match(result, metadata)
        
        # Render using matched template
        template.render(result, config)

        # Render calculation explainer (chain of thought)
        if config.get("show_calculation_steps", True):
            add_calculation_explainer(result, capability)

        # Render provenance (if configured)
        if config.get("show_provenance", True) and provenance:
            st.markdown("---")
            with st.expander("🔍 Provenance & Data Lineage"):
                self._render_provenance(provenance, exec_time)
    
    def _render_provenance(self, provenance: Dict, exec_time: float) -> None:
        """Render provenance information as a beautiful HTML table"""
        # Build table data
        table_rows = []

        for key, value in provenance.items():
            if isinstance(value, (dict, list)):
                continue  # Skip complex structures

            formatted_key = format_key_name(key)
            formatted_value = auto_format_value(key, value)
            table_rows.append((formatted_key, formatted_value))

        # Add execution time
        table_rows.append(("Execution Time", f"{exec_time:.2f} ms"))

        # Render as beautiful HTML table
        html = """
        <style>
            .provenance-table {
                width: 100%;
                border-collapse: collapse;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                border-radius: 8px;
                overflow: hidden;
            }
            .provenance-table thead {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .provenance-table th {
                padding: 14px 18px;
                text-align: left;
                font-weight: 600;
                font-size: 13px;
                letter-spacing: 0.5px;
                text-transform: uppercase;
            }
            .provenance-table tbody tr {
                border-bottom: 1px solid #e5e7eb;
                transition: background-color 0.2s ease;
            }
            .provenance-table tbody tr:hover {
                background-color: #f9fafb;
            }
            .provenance-table tbody tr:last-child {
                border-bottom: none;
            }
            .provenance-table td {
                padding: 12px 18px;
                font-size: 14px;
            }
            .provenance-table td:first-child {
                font-weight: 600;
                color: #374151;
                width: 35%;
            }
            .provenance-table td:last-child {
                color: #6b7280;
            }
        </style>
        <table class="provenance-table">
            <thead>
                <tr>
                    <th>Field</th>
                    <th>Value</th>
                </tr>
            </thead>
            <tbody>
        """

        for key, value in table_rows:
            html += f"""
                <tr>
                    <td>{key}</td>
                    <td>{value}</td>
                </tr>
            """

        html += """
            </tbody>
        </table>
        """

        st.markdown(html, unsafe_allow_html=True)
    
    def render_result_only(self, result: Dict, capability: str = "unknown") -> None:
        """
        Render only the result portion (without full response wrapper)
        
        Args:
            result: Result dictionary
            capability: Capability name for configuration lookup
        """
        config = get_capability_config(capability)
        metadata = self.analyzer.analyze(result)
        template = self.matcher.match(result, metadata)
        template.render(result, config)
