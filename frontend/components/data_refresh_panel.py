"""
V3.0.0 Data Refresh Panel
=========================

Streamlit component for triggering data refresh operations via UI button.
Displays:
- Current data status
- Refresh button
- Progress and results display
"""

import streamlit as st
import requests
from typing import Dict
from datetime import datetime


def render_data_refresh_panel(api_base_url: str = "http://localhost:8000"):
    """
    Render data refresh panel with status and button

    Args:
        api_base_url: FastAPI base URL (default: http://localhost:8000)
    """

    # Custom CSS for refresh panel
    st.markdown("""
        <style>
        .refresh-panel {
            background-color: #f0f2f6;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .status-good {
            color: #28a745;
            font-weight: bold;
        }
        .status-warning {
            color: #ffc107;
            font-weight: bold;
        }
        .status-error {
            color: #dc3545;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("### Data Refresh Control")

    # Get current data status
    try:
        response = requests.get(f"{api_base_url}/api/data/status", timeout=5)
        if response.status_code == 200:
            status_data = response.json()

            if status_data.get("status") == "data_available":
                last_extraction = status_data.get("last_extraction", "Unknown")
                file_size = status_data.get("file_size_bytes", 0)

                # Format timestamp
                try:
                    dt = datetime.fromisoformat(last_extraction)
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    formatted_time = last_extraction

                st.success(f"✓ Data Available - Last extracted: {formatted_time}")
                st.caption(f"File size: {file_size / 1024:.1f} KB")
            else:
                st.warning("⚠ No data found. Click 'Refresh Data' to extract and load.")
        else:
            st.error(f"Failed to get status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        st.error(f"Cannot connect to API server: {e}")
        return

    # Refresh button
    col1, col2 = st.columns([3, 3])

    with col1:
        if st.button("🔄 Refresh Data from PDF", type="primary", use_container_width=True):
            with st.spinner("Extracting PDF to nested format..."):
                try:
                    response = requests.post(
                        f"{api_base_url}/api/data/refresh",
                        timeout=180  # 3 minute timeout
                    )

                    if response.status_code == 200:
                        result = response.json()

                        if result.get("status") == "success":
                            st.success(f"✓ Data refresh completed in {result.get('duration_seconds', 0):.1f}s")

                            # Show step results
                            with st.expander("View Details"):
                                for step in result.get("results", []):
                                    step_name = step.get("step", "Unknown")
                                    step_status = step.get("status", "unknown")

                                    if step_status == "success":
                                        st.markdown(f"✓ **{step_name}**: Success")
                                    else:
                                        st.markdown(f"✗ **{step_name}**: Failed")
                                        st.code(step.get("error", "Unknown error"))
                        else:
                            st.error(f"✗ Refresh failed: {result.get('message', 'Unknown error')}")

                            # Show error details
                            with st.expander("Error Details"):
                                st.json(result)
                    else:
                        st.error(f"API error: {response.status_code}")
                        st.code(response.text)

                except requests.exceptions.Timeout:
                    st.error("Refresh timed out after 3 minutes. Check server logs.")
                except requests.exceptions.RequestException as e:
                    st.error(f"Request failed: {e}")

    with col2:
        if st.button("📊 View Knowledge Graph", use_container_width=True):
            st.session_state.show_graph = not st.session_state.get('show_graph', False)
            st.rerun()

    # Help text
    with st.expander("ℹ️ How to use"):
        st.markdown("""
        **🔄 Refresh Data from PDF**: Extract data from PDF directly into nested {value, unit, dimension, relationships} format

        **📊 View Knowledge Graph**: Visualize the knowledge graph with dimensional relationships

        **Data Format**: All attributes stored as `{value, unit, dimension, relationships}` with explicit dimensional relationships (IS, NUMERATOR, DENOMINATOR, INVERSE_OF)

        **Note**: Extraction may take 30-60 seconds depending on PDF size.
        """)
