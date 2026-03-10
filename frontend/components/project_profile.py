"""
Project Profile Components

Rich visual components for displaying project information:
- Google Maps embeds
- Photo carousels
- Performance metrics
- Area comparisons
"""

import streamlit as st
from typing import Dict, Any, Optional, List
import requests


def render_google_map(latitude: float, longitude: float, project_name: str, zoom: int = 15) -> None:
    """
    Render an embedded Google Map with RED PIN MARKER centered on project location

    Args:
        latitude: Project latitude
        longitude: Project longitude
        project_name: Project name for marker label
        zoom: Map zoom level (default: 15)
    """
    # Google Maps embed URL with marker parameter to show RED PIN
    # The marker=color:red|18.7556934,73.8367202 adds a red pin
    # Note: This uses the free Maps Embed API (no key required for basic embeds)
    # Format: &markers=color:red|label:|lat,lon
    map_url = f"https://www.google.com/maps/embed/v1/place?key=AIzaSyAJMeaJeH1XD-wKlKRZaDeKrp5IbHMynXU&q={latitude},{longitude}&zoom={zoom}&maptype=roadmap"

    # Fallback: Use iframe with search query (automatically shows pin)
    fallback_url = f"https://www.google.com/maps?q={latitude},{longitude}&output=embed&z={zoom}"

    # Render iframe with red pin marker
    st.markdown(f"""
    <div style="margin: 20px 0;">
        <h4 style="margin-bottom: 10px;">📍 Location: {project_name}</h4>
        <iframe
            width="100%"
            height="450"
            frameborder="0"
            style="border:0; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.15);"
            src="{map_url}"
            allowfullscreen>
        </iframe>
        <p style="font-size: 12px; color: #666; margin-top: 8px;">
            <span style="color: #dc3545; font-weight: 600;">📍 Red Pin:</span> {latitude:.6f}°, {longitude:.6f}°
            &nbsp;|&nbsp;
            <a href="https://www.google.com/maps?q={latitude},{longitude}" target="_blank" style="color: #667eea; text-decoration: none;">Open in Google Maps ↗</a>
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_photo_carousel(photos: List[str], project_name: str) -> None:
    """
    Render a photo carousel for project images

    Args:
        photos: List of image URLs
        project_name: Project name for captions
    """
    if not photos:
        return

    st.markdown(f"""
    <div style="margin: 20px 0;">
        <h4 style="margin-bottom: 10px;">🖼️ Photos: {project_name}</h4>
    </div>
    """, unsafe_allow_html=True)

    # Use Streamlit's native image carousel
    cols = st.columns(min(len(photos), 3))
    for idx, photo_url in enumerate(photos[:6]):  # Limit to 6 photos
        with cols[idx % 3]:
            st.image(photo_url, use_container_width=True)


def render_metadata_card(project_data: Dict[str, Any]) -> None:
    """
    Render project metadata card

    Args:
        project_data: Project data dict with all attributes
    """
    # Extract values using the v4 nested structure
    def get_value(attr):
        if isinstance(attr, dict) and 'value' in attr:
            return attr['value']
        return attr

    project_name = get_value(project_data.get('projectName', 'Unknown'))
    developer = get_value(project_data.get('developerName', 'Unknown'))
    location = get_value(project_data.get('location', 'Unknown'))
    launch_date = get_value(project_data.get('launchDate', 'N/A'))
    possession_date = get_value(project_data.get('possessionDate', 'N/A'))
    rera = get_value(project_data.get('reraRegistered', 'Unknown'))

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        margin: 20px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    ">
        <h2 style="margin: 0 0 10px 0; font-size: 28px;">{project_name}</h2>
        <p style="margin: 5px 0; font-size: 16px; opacity: 0.9;">
            <b>Developer:</b> {developer}
        </p>
        <p style="margin: 5px 0; font-size: 16px; opacity: 0.9;">
            <b>Location:</b> {location}
        </p>
        <div style="display: flex; gap: 30px; margin-top: 15px;">
            <div>
                <p style="margin: 0; font-size: 12px; opacity: 0.7;">Launch Date</p>
                <p style="margin: 0; font-size: 16px; font-weight: bold;">{launch_date}</p>
            </div>
            <div>
                <p style="margin: 0; font-size: 12px; opacity: 0.7;">Possession</p>
                <p style="margin: 0; font-size: 16px; font-weight: bold;">{possession_date}</p>
            </div>
            <div>
                <p style="margin: 0; font-size: 12px; opacity: 0.7;">RERA Status</p>
                <p style="margin: 0; font-size: 16px; font-weight: bold;">{"✅ Yes" if rera == "Yes" else "❌ No" if rera == "No" else rera}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_key_stats(project_data: Dict[str, Any]) -> None:
    """
    Render key project statistics in a grid

    Args:
        project_data: Project data dict with all attributes
    """
    def get_value(attr):
        if isinstance(attr, dict) and 'value' in attr:
            return attr['value']
        return attr

    def get_unit(attr):
        if isinstance(attr, dict) and 'unit' in attr:
            return attr['unit']
        return ''

    # Extract stats
    stats = [
        {
            'label': 'Project Size',
            'value': get_value(project_data.get('projectSizeUnits', 'N/A')),
            'unit': 'units',
            'icon': '🏢'
        },
        {
            'label': 'Total Supply',
            'value': get_value(project_data.get('totalSupplyUnits', 'N/A')),
            'unit': 'units',
            'icon': '📦'
        },
        {
            'label': 'Current PSF',
            'value': get_value(project_data.get('currentPricePSF', 'N/A')),
            'unit': '₹/sqft',
            'icon': '💰'
        },
        {
            'label': 'Sold',
            'value': f"{get_value(project_data.get('soldPct', 'N/A'))}%",
            'unit': '',
            'icon': '✅'
        },
        {
            'label': 'Unsold',
            'value': f"{get_value(project_data.get('unsoldPct', 'N/A'))}%",
            'unit': '',
            'icon': '📊'
        },
        {
            'label': 'Annual Sales',
            'value': get_value(project_data.get('annualSalesUnits', 'N/A')),
            'unit': 'units/yr',
            'icon': '📈'
        }
    ]

    st.markdown("<h4 style='margin: 20px 0 10px 0;'>📊 Key Statistics</h4>", unsafe_allow_html=True)

    # Render in 3 columns
    cols = st.columns(3)
    for idx, stat in enumerate(stats):
        with cols[idx % 3]:
            value_display = f"{stat['value']:,}" if isinstance(stat['value'], (int, float)) else stat['value']
            st.markdown(f"""
            <div style="
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                margin-bottom: 10px;
                border-left: 4px solid #667eea;
            ">
                <div style="font-size: 24px; margin-bottom: 5px;">{stat['icon']}</div>
                <div style="font-size: 12px; color: #666; margin-bottom: 5px;">{stat['label']}</div>
                <div style="font-size: 20px; font-weight: bold; color: #333;">
                    {value_display} <span style="font-size: 12px; font-weight: normal;">{stat['unit']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_suggested_questions(project_name: str, location: str) -> None:
    """
    Render suggested follow-up questions

    Args:
        project_name: Name of the project
        location: Project location
    """
    questions = [
        f"What is the absorption rate for {project_name}?",
        f"Compare {project_name} with other projects in {location}",
        f"What is the price trend for {project_name}?",
        f"Show me unsold inventory for {project_name}",
        f"What are the nearby amenities to {project_name}?",
        f"Top projects in {location} by PSF"
    ]

    st.markdown("""
    <h4 style='margin: 20px 0 10px 0;'>💡 Suggested Questions</h4>
    """, unsafe_allow_html=True)

    cols = st.columns(2)
    for idx, question in enumerate(questions):
        with cols[idx % 2]:
            st.markdown(f"""
            <div style="
                background: #fff3cd;
                padding: 10px 15px;
                border-radius: 6px;
                margin-bottom: 8px;
                border-left: 3px solid #ffc107;
                font-size: 14px;
                cursor: pointer;
            ">
                💬 {question}
            </div>
            """, unsafe_allow_html=True)


def detect_location_query(question: str) -> bool:
    """
    Detect if question is asking for location/map

    Args:
        question: User's question

    Returns:
        True if location query detected
    """
    location_keywords = [
        'where is', 'location of', 'location', 'show on map', 'map of',
        'coordinates of', 'gps', 'address of', 'where can i find', 'address'
    ]
    return any(kw in question.lower() for kw in location_keywords)


def detect_project_overview_query(question: str) -> bool:
    """
    Detect if question is asking for comprehensive project overview

    Args:
        question: User's question

    Returns:
        True if overview query detected
    """
    overview_keywords = [
        'tell me about', 'what is', 'details of', 'information about',
        'overview of', 'profile of', 'describe', 'summary of'
    ]
    return any(kw in question.lower() for kw in overview_keywords)
