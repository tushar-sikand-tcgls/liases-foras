"""
Available Projects Panel - Collapsible Component
Displays all projects available in a selected region
"""
import streamlit as st
import requests
from typing import List, Dict, Optional


def render_available_projects(location: str, api_url: str = "http://localhost:8000") -> None:
    """
    Render collapsible panel showing all projects in a location/region

    Args:
        location: Location or micro-market name (e.g., "Chakan")
        api_url: Base URL of the backend API
    """
    if not location or location == "-- None --":
        return

    try:
        # Fetch projects from API
        response = requests.get(
            f"{api_url}/api/projects/by-location",
            params={"location": location},
            timeout=5
        )

        if response.status_code != 200:
            st.error(f"Failed to fetch projects for {location}")
            return

        projects = response.json()

        if not projects:
            st.info(f"ℹ️ No projects found in {location}")
            return

        # Render collapsible panel
        with st.expander(
            f"📋 Available Projects in {location} ({len(projects)} projects)",
            expanded=True
        ):
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 10px;
            ">
                <p style="margin: 0; color: #2c3e50; font-size: 14px;">
                    <strong>📍 Region:</strong> {location} &nbsp;|&nbsp;
                    <strong>🏢 Total Projects:</strong> {len(projects)}
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Display projects in a table
            for idx, project in enumerate(projects, 1):
                project_name = project.get('projectName', 'Unknown')
                total_units = project.get('totalSupplyUnits', 0)
                price_psf = project.get('currentPricePSF', {})
                developer = project.get('developerName', 'N/A')

                # Extract price value if nested
                if isinstance(price_psf, dict):
                    price_psf = price_psf.get('value', 0)

                # Color coding based on index
                bg_color = "#E8F4F8" if idx % 2 == 0 else "#F0F8FF"

                st.markdown(f"""
                <div style="
                    background: {bg_color};
                    padding: 12px 15px;
                    border-radius: 6px;
                    margin-bottom: 8px;
                    border-left: 4px solid #3498db;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 1;">
                            <p style="margin: 0 0 5px 0; font-size: 16px; font-weight: 600; color: #2c3e50;">
                                {idx}. {project_name}
                            </p>
                            <p style="margin: 0; font-size: 13px; color: #7f8c8d;">
                                <span style="margin-right: 15px;">
                                    🏗️ Developer: <strong>{developer}</strong>
                                </span>
                                <span style="margin-right: 15px;">
                                    🏠 Units: <strong>{total_units:,}</strong>
                                </span>
                                <span>
                                    💰 Price: <strong>₹{price_psf:,}/sqft</strong>
                                </span>
                            </p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Add helpful hint
            st.markdown("""
            <div style="
                background: #FFF3CD;
                border-left: 4px solid #FFC107;
                padding: 10px 15px;
                border-radius: 4px;
                margin-top: 15px;
            ">
                <p style="margin: 0; font-size: 13px; color: #856404;">
                    💡 <strong>Tip:</strong> You can ask questions about any of these projects by mentioning the project name in your query.
                </p>
            </div>
            """, unsafe_allow_html=True)

    except requests.exceptions.Timeout:
        st.error(f"⏱️ Timeout while fetching projects for {location}")
    except requests.exceptions.ConnectionError:
        st.error(f"🔌 Could not connect to API server. Make sure the backend is running.")
    except Exception as e:
        st.error(f"❌ Error fetching projects: {str(e)}")


def render_available_projects_compact(location: str, api_url: str = "http://localhost:8000") -> Optional[List[str]]:
    """
    Render compact project list (just names) in a collapsible

    Args:
        location: Location or micro-market name
        api_url: Base URL of the backend API

    Returns:
        List of project names or None
    """
    if not location or location == "-- None --":
        return None

    try:
        response = requests.get(
            f"{api_url}/api/projects/by-location",
            params={"location": location},
            timeout=5
        )

        if response.status_code != 200:
            return None

        projects = response.json()

        if not projects:
            return None

        project_names = [p.get('projectName', 'Unknown') for p in projects]

        # Render compact collapsible
        with st.expander(
            f"📋 {len(projects)} project(s) available in {location}",
            expanded=False
        ):
            st.markdown("""
            <style>
            .project-pill {
                display: inline-block;
                background: #E3F2FD;
                color: #1976D2;
                padding: 5px 12px;
                border-radius: 15px;
                margin: 4px;
                font-size: 13px;
                font-weight: 500;
            }
            </style>
            """, unsafe_allow_html=True)

            pills_html = "".join([
                f'<span class="project-pill">🏢 {name}</span>'
                for name in project_names
            ])

            st.markdown(f'<div style="line-height: 2.5;">{pills_html}</div>', unsafe_allow_html=True)

        return project_names

    except Exception as e:
        st.warning(f"Could not fetch projects for {location}: {str(e)}")
        return None
