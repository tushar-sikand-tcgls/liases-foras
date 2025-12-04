"""
Location Selector Component with Hierarchical Tree View
"""
import streamlit as st
from typing import Dict, List, Optional, Tuple


# Location hierarchy data structure
LOCATION_HIERARCHY = {
    "Mumbai": {
        "regions": ["Andheri", "Bandra", "Worli", "Powai"],
        "projects": {
            "Andheri": ["Skyline Towers", "Green Valley"],
            "Bandra": ["Sea View Residency"],
            "Worli": ["Luxury Heights"],
            "Powai": ["Lake View Apartments"]
        }
    },
    "Pune": {
        "regions": ["Baner", "Chakan", "Hinjewadi"],
        "projects": {
            "Baner": ["Urban Nest", "Serene Villas"],
            "Chakan": ["Sara City", "Industrial Park Residency"],
            "Hinjewadi": ["Tech Park Homes", "IT Hub Apartments", "Modern Living"]
        }
    }
}


def render_location_selector() -> Optional[Tuple[str, str, Optional[str]]]:
    """
    Render hierarchical location selector

    Returns:
        Tuple of (city, region, project) or None if nothing selected
    """

    st.markdown("### Search & Select Location")

    # City selection
    cities = list(LOCATION_HIERARCHY.keys()) + ["-- None --"]
    selected_city = st.selectbox(
        "City",
        cities,
        index=len(cities) - 1,  # Default to "-- None --"
        key="city_selector"
    )

    if selected_city == "-- None --":
        return None

    # Region selection
    regions = LOCATION_HIERARCHY[selected_city]["regions"] + ["-- None --"]
    selected_region = st.selectbox(
        "Region / Micro-market",
        regions,
        index=len(regions) - 1,  # Default to "-- None --"
        key="region_selector"
    )

    if selected_region == "-- None --":
        return (selected_city, None, None)

    # Project selection (optional)
    projects = LOCATION_HIERARCHY[selected_city]["projects"].get(selected_region, []) + ["-- None --"]
    selected_project = st.selectbox(
        "Project (Optional)",
        projects,
        index=len(projects) - 1,  # Default to "-- None --"
        key="project_selector"
    )

    if selected_project == "-- None --":
        return (selected_city, selected_region, None)

    return (selected_city, selected_region, selected_project)


def render_location_breadcrumb(city: str, region: Optional[str] = None, project: Optional[str] = None):
    """Render location breadcrumb navigation"""

    breadcrumb_parts = []
    if project:
        breadcrumb_parts = [project, region, city]
    elif region:
        breadcrumb_parts = [region, city]
    elif city:
        breadcrumb_parts = [city]

    if breadcrumb_parts:
        breadcrumb_html = f"""
        <div style="
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 15px 25px;
            border-radius: 8px;
            font-size: 1.4rem;
            font-weight: 600;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        ">
            📍 {', '.join(breadcrumb_parts)}
        </div>
        """
        st.markdown(breadcrumb_html, unsafe_allow_html=True)


def render_tree_view_selector() -> Optional[Tuple[str, str, Optional[str]]]:
    """
    Render a more compact tree-like view selector

    Returns:
        Tuple of (city, region, project) or None
    """

    st.markdown("### 🔍 Search Location")

    # Create expandable tree structure
    selected_location = None

    for city, city_data in LOCATION_HIERARCHY.items():
        with st.expander(f"📍 {city}", expanded=False):
            for region in city_data["regions"]:
                col1, col2 = st.columns([1, 3])

                with col1:
                    if st.button(f"Select", key=f"btn_{city}_{region}"):
                        selected_location = (city, region, None)

                with col2:
                    st.markdown(f"**{region}**")

                # Show projects under region
                projects = city_data["projects"].get(region, [])
                if projects:
                    for project in projects:
                        col1_proj, col2_proj = st.columns([1, 3])
                        with col1_proj:
                            if st.button(f"Select", key=f"btn_{city}_{region}_{project}"):
                                selected_location = (city, region, project)
                        with col2_proj:
                            st.markdown(f"  └─ _{project}_")

    return selected_location
