"""
Searchable Hierarchical Tree Location Selector
"""
import streamlit as st
from typing import Dict, List, Optional, Tuple


# Hierarchical location tree (State > City > Region)
LOCATION_TREE = {
    "Maharashtra": {
        "Mumbai": ["Andheri", "Bander", "Worli", "Powai"],
        "Pune": ["Baner", "Chakan", "Hinjewadi"]
    },
    "West Bengal": {
        "Kolkata": ["Kolkata"]  # Single unified region
    }
}


def search_tree(search_term: str) -> List[List[str]]:
    """
    Search the location tree for matches (SQL LIKE '%search_term%')

    Args:
        search_term: Search string (minimum 2 characters)

    Returns:
        List of matching paths [state, city, region]
    """
    if len(search_term) < 2:
        return []

    search_lower = search_term.lower()
    matches = []

    for state, cities in LOCATION_TREE.items():
        state_match = search_lower in state.lower()

        for city, regions in cities.items():
            city_match = search_lower in city.lower()

            # Regions are now leaf nodes (list of strings)
            for region in regions:
                region_match = search_lower in region.lower()

                # If state/city/region matches, add the path
                if state_match or city_match or region_match:
                    matches.append([state, city, region])

    return matches


def render_tree_item(state: str, city: str = None, region: str = None,
                     level: int = 0, selectable: bool = True) -> bool:
    """Render a single tree item with proper indentation"""

    indent = "　　" * level  # Use full-width spaces for indentation

    if region:
        label = f"{indent}└─ {region}"
        key = f"{state}_{city}_{region}"
    elif city:
        label = f"{indent}└─ {city}"
        key = f"{state}_{city}"
    else:
        label = f"{state}"
        key = state

    if selectable:
        if st.button(label, key=f"btn_{key}", use_container_width=True):
            return True

    return False


def render_searchable_tree_selector() -> Optional[Tuple[str, str, str, Optional[str]]]:
    """
    Render searchable hierarchical tree selector

    Returns:
        Tuple of (state, city, region, project) or None
    """

    st.subheader("Search Location")

    # Search input
    search_term = st.text_input(
        "Type to search (minimum 2 characters)",
        key="location_search",
        placeholder="e.g., 'an' matches Maharashtra, Chakan, and Baner"
    )

    selected_location = None

    # Show search results if search term is >= 2 characters
    if len(search_term) >= 2:
        matches = search_tree(search_term)

        if matches:
            st.write(f"**Found {len(matches)} matches:**")

            for match in matches:
                state, city, region = match

                # Display full path
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(f"{state} > {city} > {region}")

                with col2:
                    if st.button("Select", key=f"select_{state}_{city}_{region}"):
                        selected_location = (state, city, region, None)
                        # Store in session state
                        st.session_state.selected_location = selected_location
                        return selected_location

        else:
            st.info("No matches found. Try a different search term.")

    # Show full tree if no search
    else:
        st.write("**Browse all locations:**")

        for state, cities in LOCATION_TREE.items():
            with st.expander(f"▸ {state}", expanded=False):
                for city, regions in cities.items():
                    # Make city names visible with explicit styling
                    st.markdown(f'<p style="color: #000000; font-weight: 600; margin: 8px 0 4px 0;">• {city}</p>', unsafe_allow_html=True)

                    # Regions are now leaf nodes (list of strings)
                    for region in regions:
                        if st.button(f"└─ {region}", key=f"select_{state}_{city}_{region}", use_container_width=True):
                            selected_location = (state, city, region, None)
                            st.session_state.selected_location = selected_location
                            return selected_location

                    st.write("")  # Spacing

    return selected_location


def render_breadcrumb(state: str, city: str, region: str, project: Optional[str] = None):
    """Render clean breadcrumb for selected location"""

    # Always show 3-level hierarchy (project parameter kept for backward compatibility but not used)
    breadcrumb = f"{state} > {city} > {region}"

    st.markdown(f"### Location: {breadcrumb}")
