"""
Sirrus.AI ATLAS - Advanced Territorial Location Analytics & Strategy
Clean UI with proper color palette and searchable tree selector
"""
import streamlit as st
import requests
from typing import Dict, Optional
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file in parent directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Add frontend directory to path to avoid conflicts with system 'frontend' package
sys.path.insert(0, str(Path(__file__).parent))

from components.dynamic_renderer import DynamicRenderer
from components.clean_styles import CLEAN_CSS_STYLES, COLORS
from components.searchable_tree_selector import render_searchable_tree_selector, render_breadcrumb
from components.content_tabs import render_content_tabs
from components.graph_view import render_knowledge_graph_view
from services.weather_service import WeatherService

# Configuration
API_BASE_URL = "http://localhost:8000"
USE_DYNAMIC_RENDERER = True

# SECURITY FIX: Load Google Maps API key from environment variable
# This prevents exposing the key in source code
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

# Page config (MUST be first Streamlit command)
st.set_page_config(
    page_title="Sirrus.AI ATLAS",
    page_icon="🗺️",  # World map emoji - stylish, modern representation of an ATLAS
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Validate API key after set_page_config
if not GOOGLE_MAPS_API_KEY:
    st.warning("⚠️ Google Maps API key not configured. Please set the GOOGLE_MAPS_API_KEY environment variable.")

# Apply clean CSS styles
st.markdown(CLEAN_CSS_STYLES, unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'selected_location' not in st.session_state:
    st.session_state.selected_location = None
if 'show_graph' not in st.session_state:
    st.session_state.show_graph = False
if 'location_data_cache' not in st.session_state:
    st.session_state.location_data_cache = {}
if 'current_location_key' not in st.session_state:
    st.session_state.current_location_key = None
if 'loading_states' not in st.session_state:
    st.session_state.loading_states = {}  # Track what's currently loading
if 'display_mode' not in st.session_state:
    st.session_state.display_mode = 'bullets'  # Default display mode for query results

# Initialize Dynamic Renderer
if USE_DYNAMIC_RENDERER:
    dynamic_renderer = DynamicRenderer()

# Initialize Weather Service
weather_service = WeatherService()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_location_key(region: str, city: str) -> str:
    """Generate cache key for location"""
    return f"{region}_{city}"

def render_loading_spinner(message: str = "Loading..."):
    """Render a loading spinner with custom message"""
    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: center; padding: 20px;">
        <div class="spinner" style="
            border: 3px solid #f3f3f3;
            border-top: 3px solid #3498db;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin-right: 10px;
        "></div>
        <span style="color: #666; font-size: 14px;">{message}</span>
    </div>
    <style>
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    </style>
    """, unsafe_allow_html=True)

def render_interactive_map(location_name: str, lat: float, lon: float, api_key: str, height: int = 400):
    """
    Render an interactive Google Map using JavaScript

    Args:
        location_name: Name of the location (for display)
        lat: Latitude
        lon: Longitude
        api_key: Google Maps API key
        height: Map height in pixels (default 400)
    """
    map_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            #map {{
                height: {height}px;
                width: 100%;
                border-radius: 8px;
            }}
            body {{
                margin: 0;
                padding: 0;
            }}
        </style>
    </head>
    <body>
        <div id="map"></div>

        <script>
            function initMap() {{
                const location = {{ lat: {lat}, lng: {lon} }};
                const map = new google.maps.Map(document.getElementById("map"), {{
                    zoom: 13,
                    center: location,
                    mapTypeControl: true,
                    streetViewControl: true,
                    fullscreenControl: true,
                }});

                // Add marker at the location
                const marker = new google.maps.Marker({{
                    position: location,
                    map: map,
                    title: "{location_name}",
                }});
            }}
        </script>
        <script async defer src="https://maps.googleapis.com/maps/api/js?key={api_key}&callback=initMap"></script>
    </body>
    </html>
    """

    st.components.v1.html(map_html, height=height + 20, scrolling=False)

def render_interactive_carousel(images: list, location_name: str, height: int = 450):
    """
    Render an interactive image carousel using JavaScript

    Args:
        images: List of image dicts with 'url', 'title', 'source'
        location_name: Name of the location (for display)
        height: Carousel height in pixels (default 450)
    """
    if not images or len(images) == 0:
        st.info(f"📷 No photos available for {location_name}")
        return

    # Prepare image data for JavaScript (escape quotes)
    images_js = []
    for img in images:
        url = img.get('url', '').replace("'", "\\'").replace('"', '\\"')
        title = img.get('title', 'Photo').replace("'", "\\'").replace('"', '\\"')
        source = img.get('source', 'Unknown').replace("'", "\\'").replace('"', '\\"')
        if url:
            images_js.append(f'{{"url": "{url}", "title": "{title}", "source": "{source}"}}')

    images_json = "[" + ", ".join(images_js) + "]"

    carousel_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background: #f5f5f5;
            }}
            .carousel-container {{
                position: relative;
                max-width: 100%;
                margin: 0 auto;
                overflow: hidden;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            .carousel-slide {{
                display: flex;
                transition: transform 0.5s ease-in-out;
            }}
            .carousel-img {{
                width: 100%;
                height: {height - 100}px;
                object-fit: cover;
                display: block;
                flex-shrink: 0;
            }}
            .prev, .next {{
                position: absolute;
                top: 50%;
                transform: translateY(-50%);
                background: rgba(0, 0, 0, 0.5);
                color: white;
                border: none;
                padding: 16px;
                cursor: pointer;
                font-size: 20px;
                border-radius: 4px;
                transition: background 0.3s;
                z-index: 10;
            }}
            .prev:hover, .next:hover {{
                background: rgba(0, 0, 0, 0.8);
            }}
            .prev {{ left: 10px; }}
            .next {{ right: 10px; }}
            .carousel-caption {{
                position: absolute;
                bottom: 60px;
                left: 0;
                right: 0;
                background: linear-gradient(to top, rgba(0,0,0,0.8), transparent);
                color: white;
                padding: 20px;
                text-align: center;
            }}
            .carousel-title {{
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 5px;
            }}
            .carousel-source {{
                font-size: 12px;
                opacity: 0.9;
            }}
            .carousel-indicators {{
                position: absolute;
                bottom: 10px;
                left: 50%;
                transform: translateX(-50%);
                display: flex;
                gap: 8px;
                padding: 10px;
                background: rgba(0,0,0,0.3);
                border-radius: 20px;
            }}
            .indicator {{
                width: 10px;
                height: 10px;
                border-radius: 50%;
                background: rgba(255,255,255,0.5);
                cursor: pointer;
                transition: all 0.3s;
            }}
            .indicator.active {{
                background: white;
                width: 30px;
                border-radius: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="carousel-container">
            <div class="carousel-slide" id="carousel-slide">
                <!-- Images will be injected here by JavaScript -->
            </div>
            <button class="prev" onclick="prevSlide()">&#10094;</button>
            <button class="next" onclick="nextSlide()">&#10095;</button>
            <div class="carousel-caption" id="carousel-caption"></div>
            <div class="carousel-indicators" id="carousel-indicators"></div>
        </div>

        <script>
            const images = {images_json};
            let currentSlide = 0;

            function updateCaption() {{
                const caption = document.getElementById('carousel-caption');
                if (images.length > 0) {{
                    const current = images[currentSlide];
                    caption.innerHTML = `
                        <div class="carousel-title">${{current.title}}</div>
                        <div class="carousel-source">Source: ${{current.source}}</div>
                    `;
                }}
            }}

            function updateIndicators() {{
                const indicators = document.getElementById('carousel-indicators');
                indicators.innerHTML = '';
                images.forEach((_, index) => {{
                    const dot = document.createElement('div');
                    dot.className = 'indicator' + (index === currentSlide ? ' active' : '');
                    dot.onclick = () => goToSlide(index);
                    indicators.appendChild(dot);
                }});
            }}

            function showSlides(n) {{
                if (images.length === 0) return;

                // Wrap around logic
                if (n >= images.length) currentSlide = 0;
                if (n < 0) currentSlide = images.length - 1;

                const slideContainer = document.getElementById('carousel-slide');
                slideContainer.style.transform = `translateX(${{-currentSlide * 100}}%)`;

                updateCaption();
                updateIndicators();
            }}

            function nextSlide() {{
                showSlides(currentSlide += 1);
            }}

            function prevSlide() {{
                showSlides(currentSlide -= 1);
            }}

            function goToSlide(n) {{
                currentSlide = n;
                showSlides(currentSlide);
            }}

            function initCarousel() {{
                const carouselSlide = document.getElementById('carousel-slide');

                images.forEach(image => {{
                    const imgElement = document.createElement('img');
                    imgElement.src = image.url;
                    imgElement.alt = image.title;
                    imgElement.className = 'carousel-img';
                    imgElement.onerror = function() {{
                        this.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100"%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em"%3EImage not available%3C/text%3E%3C/svg%3E';
                    }};
                    carouselSlide.appendChild(imgElement);
                }});

                // Set initial display
                showSlides(currentSlide);

                // Auto-advance carousel every 5 seconds
                setInterval(() => {{
                    nextSlide();
                }}, 5000);
            }}

            // Initialize when page loads
            initCarousel();
        </script>
    </body>
    </html>
    """

    st.components.v1.html(carousel_html, height=height, scrolling=False)

def is_loading(cache_key: str) -> bool:
    """Check if a component is currently loading"""
    return st.session_state.loading_states.get(cache_key, False)

def set_loading(cache_key: str, state: bool):
    """Set loading state for a component"""
    st.session_state.loading_states[cache_key] = state

def load_weather_data(region: str, city: str) -> Dict:
    """Load weather data (text-heavy API)"""
    location_key = get_location_key(region, city)
    cache_key = f"{location_key}_weather"

    if cache_key in st.session_state.location_data_cache:
        return st.session_state.location_data_cache[cache_key]

    data = {'weather_data': None, 'aqi_data': None}
    try:
        data['weather_data'] = weather_service.get_weather_data(city, region)
        data['aqi_data'] = weather_service.get_aqi_data(city, region)
    except Exception as e:
        print(f"[WARNING] Weather data load failed: {e}")

    st.session_state.location_data_cache[cache_key] = data
    return data

def load_map_data(region: str, city: str) -> Dict:
    """Load map data (image API - priority 3a)"""
    location_key = get_location_key(region, city)
    cache_key = f"{location_key}_map"

    if cache_key in st.session_state.location_data_cache:
        return st.session_state.location_data_cache[cache_key]

    data = {'map_data': None, 'error': None}
    try:
        print(f"[INFO] Loading map data for {region}, {city}...")
        map_response = requests.get(
            f"{API_BASE_URL}/api/context/location",
            params={"location": f"{region}, {city}", "location_type": "region"},
            timeout=8  # Reduced from 15s to 8s
        )
        if map_response.status_code == 200:
            data['map_data'] = map_response.json()
            print(f"[INFO] Map data loaded successfully")
        else:
            data['error'] = f"API returned {map_response.status_code}"
            print(f"[WARNING] Map API error: {map_response.status_code}")
    except requests.Timeout:
        data['error'] = "Request timeout (>8s)"
        print(f"[WARNING] Map data load timeout")
    except Exception as e:
        data['error'] = str(e)
        print(f"[WARNING] Map data load failed: {e}")

    st.session_state.location_data_cache[cache_key] = data
    return data



def process_query(prompt: str, location: str, admin_mode: bool = False) -> Dict:
    """Process user query and call appropriate API endpoint

    Args:
        prompt: User's question
        location: Location string (e.g., "Chakan, Pune")
        admin_mode: If True, returns rich HTML tables; if False, returns GPT-like markdown
    """

    try:
        # NO HARDCODED KEYWORD MATCHING - Let backend handle ALL query understanding
        # All queries go to /api/qa/question which uses semantic/vector-based matching

        # Include location context from selected location
        location_context = None
        if st.session_state.selected_location:
            state, city, region, project = st.session_state.selected_location
            location_context = {
                "region": region,
                "city": city,
                "state": state
            }

        response = requests.post(
            f"{API_BASE_URL}/api/qa/question",
            json={
                "question": prompt,
                "project_id": None,  # Will use first project (Sara City by default)
                "location_context": location_context,  # Pass location context
                "admin_mode": admin_mode  # Pass admin mode flag (ADMIN: prefix)
            }
        )

        if response.status_code == 200:
            result = response.json()

            # Check if QA service successfully answered
            if result.get("status") == "success":
                # Return the answer structure
                return result
            else:
                # QA service couldn't answer, show error
                error_msg = result.get('error', 'Query not recognized')
                return {
                    "status": "error",
                    "error": error_msg
                }
        else:
                return f"API Error: {response.status_code}"

    except Exception as e:
        return f"Error: {str(e)}"


# =============================================================================
# MAIN APP UI
# =============================================================================

# Header
st.title("🗺️ SIRRUS.AI ATLAS")
st.markdown('<p class="secondary-text">Advanced Territorial Location Analytics & Strategy</p>', unsafe_allow_html=True)
st.markdown("---")


# =============================================================================
# SCREEN 1: LAUNCH SCREEN (No Location Selected)
# =============================================================================

if st.session_state.selected_location is None:
    col_selector, col_guide = st.columns([1, 1])

    with col_selector:
        # Searchable tree location selector
        location_selection = render_searchable_tree_selector()

        if location_selection:
            st.session_state.selected_location = location_selection
            st.rerun()

    with col_guide:
        st.subheader("About ATLAS")
        st.write("**ATLAS empowers real estate developers with AI-driven decision intelligence** to maximize returns and minimize risks.")

        st.write("")
        st.write("**What ATLAS Does:**")
        st.write("▸ **Optimize Product Mix** - Determine the ideal unit type distribution (1BHK/2BHK/3BHK) for maximum profitability")
        st.write("▸ **Financial Modeling** - Calculate NPV, IRR, and payback periods with scenario analysis")
        st.write("▸ **Market Intelligence** - Identify high-potential micro-markets and pricing opportunities")
        st.write("▸ **Risk Assessment** - Evaluate location-specific risks and infrastructure development timelines")
        st.write("▸ **Competitive Benchmarking** - Compare project performance against market standards")

        st.write("")
        st.write("**Decision-Making Outcomes:**")
        st.write("• Launch the right project at the right time in the right location")
        st.write("• Avoid costly mistakes in product configuration and pricing")
        st.write("• Maximize IRR through data-driven unit mix optimization")
        st.write("• Reduce sales cycle time with market-aligned strategies")

        st.write("")
        st.markdown("**Get Started:** Select a location from the tree to explore analytics and insights.")


# =============================================================================
# SCREEN 2: POST-SELECT SCREEN (Location Selected)
# =============================================================================

else:
    state, city, region, project = st.session_state.selected_location

    # Breadcrumb and action buttons
    col_bread, col_graph, col_clear = st.columns([4, 1, 1])

    with col_bread:
        render_breadcrumb(state, city, region, project)

    with col_graph:
        graph_btn_label = "Hide Graph" if st.session_state.show_graph else "View Graph"
        if st.button(graph_btn_label, key="toggle_graph"):
            st.session_state.show_graph = not st.session_state.show_graph
            st.rerun()

    with col_clear:
        if st.button("Change Location"):
            st.session_state.selected_location = None
            st.session_state.messages = []
            st.session_state.show_graph = False
            st.rerun()

    st.markdown("---")

    # Show knowledge graph if toggled
    if st.session_state.show_graph:
        render_knowledge_graph_view()
        st.markdown("---")

    # Two-column layout with dynamic width adjustment
    # When expander is collapsed: [5, 95] (narrow left panel)
    # When expander is expanded: [35, 65] (normal layout)
    # Track expander state in session state
    if 'context_panel_expanded' not in st.session_state:
        st.session_state.context_panel_expanded = False  # Start collapsed

    # Determine column proportions based on expander state
    if st.session_state.context_panel_expanded:
        col_proportions = [35, 65]  # Expanded: normal width
    else:
        col_proportions = [5, 95]   # Collapsed: narrow left panel

    col_left, col_right = st.columns(col_proportions, gap="small")

    # =================================================================
    # RIGHT COLUMN FIRST: AI Chat Interface (NO BLOCKING - RENDERS IMMEDIATELY)
    # =================================================================
    with col_right:
        # Header row with title and settings
        col_title, col_settings = st.columns([3, 1])

        with col_title:
            st.subheader("Analytics AI Chat")

        # Removed display mode toggle - freed up space for chat interface

        # Display available projects in region (compact list)
        if region and region != "-- None --":
            try:
                import requests
                response = requests.get(
                    f"{api_url}/api/projects/by-location",
                    params={"location": region},
                    timeout=3
                )

                if response.status_code == 200:
                    projects = response.json()
                    if projects:
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            padding: 10px 15px;
                            border-radius: 8px;
                            margin-bottom: 15px;
                        ">
                            <p style="margin: 0; color: white; font-size: 13px; font-weight: 500;">
                                📋 {len(projects)} projects in {region}:
                            </p>
                            <div style="margin-top: 8px; display: flex; flex-wrap: wrap; gap: 6px;">
                        """, unsafe_allow_html=True)

                        for p in projects:
                            name = p.get('projectName', 'Unknown')
                            st.markdown(f"""
                                <span style="
                                    display: inline-block;
                                    background: rgba(255, 255, 255, 0.2);
                                    color: white;
                                    padding: 4px 10px;
                                    border-radius: 12px;
                                    font-size: 11px;
                                    font-weight: 500;
                                ">🏢 {name}</span>
                            """, unsafe_allow_html=True)

                        st.markdown("</div></div>", unsafe_allow_html=True)
            except:
                pass  # Silently fail if can't fetch projects

        # Suggested questions (only show if no messages)
        if len(st.session_state.messages) == 0:
            st.write("**Suggested Questions:**")

            col1, col2 = st.columns(2)

            with col1:
                st.write("**📊 Project-Specific Queries**")
                if st.button("What is the project size of Sara City?", key="q1", use_container_width=True):
                    st.session_state.messages.append({
                        "role": "user",
                        "content": "What is the project size of Sara City?"
                    })
                    st.rerun()

                if st.button("How many units in Sara City?", key="q2", use_container_width=True):
                    st.session_state.messages.append({
                        "role": "user",
                        "content": "How many total units in Sara City"
                    })
                    st.rerun()

                if st.button("Show me Sara City data", key="q3", use_container_width=True):
                    st.session_state.messages.append({
                        "role": "user",
                        "content": "Show me Sara City project data"
                    })
                    st.rerun()

            with col2:
                st.write(f"**📈 Regional Statistics**")
                if st.button(f"Average project size in {region}", key="q4", use_container_width=True):
                    st.session_state.messages.append({
                        "role": "user",
                        "content": f"What is the average project size"
                    })
                    st.rerun()

                if st.button(f"Total project size", key="q5", use_container_width=True):
                    st.session_state.messages.append({
                        "role": "user",
                        "content": f"What is the total project size"
                    })
                    st.rerun()

                if st.button(f"Standard deviation in {region}", key="q6", use_container_width=True):
                    st.session_state.messages.append({
                        "role": "user",
                        "content": f"Find the standard deviation in project size"
                    })
                    st.rerun()

            st.markdown("---")

        # Chat message display
        for idx, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                if isinstance(message["content"], dict):
                # Check if dict has "answer" field with HTML content (STRING, not dict)
                    if "answer" in message["content"] and isinstance(message["content"]["answer"], str):
                        answer = message["content"]["answer"]

                        # DEBUG: Print what we're receiving
                        print(f"[DEBUG] Answer type: {type(answer)}")
                        print(f"[DEBUG] Answer first 100 chars: {str(answer)[:100]}")

                        # INNOVATIVE FIX: Use regex to ensure complete table structure
                        if isinstance(answer, str) and ("<tr" in answer or "<table" in answer):
                            import re

                            # Check if HTML starts with <tr> (incomplete)
                            stripped = answer.strip()
                            print(f"[DEBUG] Stripped starts with: {stripped[:20]}")

                            if stripped.startswith("<tr"):
                                # Wrap with complete table structure
                                print("[DEBUG] Wrapping incomplete HTML with table tags")
                                answer = f'''<div style="margin: 20px 0;">
<table style="width: 100%; border-collapse: collapse; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden;">
    <thead>
        <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
            <th style="padding: 12px; text-align: left; font-weight: 600;">Layer</th>
            <th style="padding: 12px; text-align: left; font-weight: 600;">Metric</th>
            <th style="padding: 12px; text-align: right; font-weight: 600;">Value</th>
            <th style="padding: 12px; text-align: left; font-weight: 600;">Unit</th>
            <th style="padding: 12px; text-align: left; font-weight: 600;">Description</th>
        </tr>
    </thead>
    <tbody>
{answer}
</div>'''
                            else:
                                print(f"[DEBUG] HTML looks complete, starts with: {stripped[:50]}")

                            # ACTION BUTTONS: Copy and Export (ONLY for assistant messages)
                            if message["role"] == "assistant":
                                import html
                                from bs4 import BeautifulSoup
                                import re

                                # Extract plain text for copy/export (strip HTML tags)
                                soup = BeautifulSoup(answer, 'html.parser')
                                plain_text = soup.get_text(separator='\n').strip()

                                # Create unique ID for this answer
                                answer_id = f"answer_{idx}_{hash(answer) % 10000}"
                                unique_key = f"export_{answer_id}"
                                copy_key = f"copy_{answer_id}"

                                # Add action buttons above the answer
                                col1, col2, col3 = st.columns([8, 1, 1])
                                with col2:
                                    # Copy button using Streamlit's code block with copy functionality
                                    if st.button("📋", key=copy_key, help="Copy to clipboard"):
                                        # Store in session state for copying
                                        st.session_state[f'copy_text_{answer_id}'] = plain_text
                                        st.code(plain_text, language=None)
                                with col3:
                                    # Export to .md button
                                    import datetime
                                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                                    md_filename = f"answer_{timestamp}.md"

                                    # Convert HTML to markdown-friendly format
                                    md_content = f"# Real Estate Analytics Answer\n\n"
                                    md_content += f"**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                                    md_content += f"---\n\n{plain_text}\n"

                                    st.download_button(
                                        label="📥",
                                        data=md_content,
                                        file_name=md_filename,
                                        mime="text/markdown",
                                        help="Export answer to Markdown file",
                                        key=unique_key
                                    )

                            # Use st.components for complex HTML instead of markdown
                            if ("<table" in answer or "<tr" in answer):
                                # Calculate height based on number of rows
                                row_count = answer.count("<tr")
                                height = min(600, max(300, row_count * 40))
                                print(f"[DEBUG] Rendering HTML with st.components, height={height}, rows={row_count}")

                                # Wrap answer with hidden div for clipboard access
                                answer_with_id = f'<div id="{answer_id}" style="display:none;">{plain_text}</div>{answer}'
                                st.components.v1.html(answer_with_id, height=height, scrolling=True)
                            else:
                                st.write(answer)
                        else:
                            st.write(answer)
                    else:
                        # Check if this is a query result from our semantic matcher
                        if message["content"].get("status") == "success" and "answer" in message["content"]:
                            # Use simple transformer to convert JSON to clean text
                            from components.answer_transformer import transform_answer

                            # Get display mode from session state (default: bullets)
                            display_mode = st.session_state.get('display_mode', 'bullets')

                            # Transform the answer
                            text_output, table_data = transform_answer(message["content"], display_mode)

                            if table_data is not None:
                                # Display as table
                                st.table(table_data)
                            elif text_output:
                                # Display as markdown text (allow HTML for collapsible details)
                                st.markdown(text_output, unsafe_allow_html=True)
                            else:
                                # Fallback to JSON
                                st.json(message["content"])

                        elif USE_DYNAMIC_RENDERER:
                            # Use dynamic renderer for other types
                            dynamic_renderer.render_response(message["content"])
                        else:
                            # Fallback to JSON for other responses
                            st.json(message["content"])
                else:
                # String content
                    content = message["content"]

                    if isinstance(content, str):
                        import re
                        import html
                        from bs4 import BeautifulSoup
                        import datetime

                        stripped = content.strip()

                        # Fix incomplete HTML
                        if stripped.startswith("<tr"):
                            content = f'''<div style="margin: 20px 0;">
<table style="width: 100%; border-collapse: collapse; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden;">
    <thead>
        <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
            <th style="padding: 12px; text-align: left; font-weight: 600;">Layer</th>
            <th style="padding: 12px; text-align: left; font-weight: 600;">Metric</th>
            <th style="padding: 12px; text-align: right; font-weight: 600;">Value</th>
            <th style="padding: 12px; text-align: left; font-weight: 600;">Unit</th>
            <th style="padding: 12px; text-align: left; font-weight: 600;">Description</th>
        </tr>
    </thead>
    <tbody>
{content}
</div>'''

                        # Extract plain text and create unique ID (needed for both display and copy/export)
                        soup = BeautifulSoup(content, 'html.parser')
                        plain_text = soup.get_text(separator='\n').strip()
                        answer_id = f"answer_{idx}_{hash(content) % 10000}"

                        # ACTION BUTTONS for string content too (ONLY for assistant messages)
                        if message["role"] == "assistant":
                            unique_key = f"export_str_{answer_id}"
                            copy_key = f"copy_str_{answer_id}"

                            # Add action buttons
                            col1, col2, col3 = st.columns([8, 1, 1])
                            with col2:
                                # Copy button using Streamlit's code block with copy functionality
                                if st.button("📋", key=copy_key, help="Copy to clipboard"):
                                    st.session_state[f'copy_text_{answer_id}'] = plain_text
                                    st.code(plain_text, language=None)
                            with col3:
                                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                                md_filename = f"answer_{timestamp}.md"
                                md_content = f"# Real Estate Analytics Answer\n\n"
                                md_content += f"**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                                md_content += f"---\n\n{plain_text}\n"

                                st.download_button(
                                    label="📥",
                                    data=md_content,
                                    file_name=md_filename,
                                    mime="text/markdown",
                                    help="Export answer to Markdown file",
                                    key=unique_key
                                )

                        # Use st.components for HTML rendering
                        if ("<table" in content or "<tr" in content):
                            row_count = content.count("<tr")
                            height = min(600, max(300, row_count * 40))
                            content_with_id = f'<div id="{answer_id}" style="display:none;">{plain_text}</div>{content}'
                            st.components.v1.html(content_with_id, height=height, scrolling=True)
                        else:
                            st.write(content)
                    else:
                        st.write(content)

        # Check if last message needs processing
        if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
            last_user_message = st.session_state.messages[-1]["content"]

            # ADMIN: Prefix Detection (case-sensitive)
            admin_mode = False
            if last_user_message.startswith("ADMIN:"):
                admin_mode = True
                last_user_message = last_user_message[6:].strip()  # Remove "ADMIN:" prefix
                print(f"[ADMIN MODE] Enabled - Rich tables will be shown")

            print(f"[DEBUG] Processing user message: {last_user_message}")
            print(f"[DEBUG] Admin mode: {admin_mode}")

            with st.chat_message("assistant"):
                with st.spinner("Analyzing..."):
                    location_str = f"{region}, {city}"
                    response_content = process_query(last_user_message, location_str, admin_mode=admin_mode)
                    print(f"[DEBUG] Got response type: {type(response_content)}")
                    print(f"[DEBUG] Response keys: {response_content.keys() if isinstance(response_content, dict) else 'N/A'}")
                    st.session_state.messages.append({"role": "assistant", "content": response_content})
                    st.rerun()

        # Chat input
        if prompt := st.chat_input("Ask about pricing, absorption rates, financial analysis..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.rerun()

    # =================================================================
    # LEFT COLUMN: Collapsible Context Panel
    # Contains location context with vertical text when collapsed
    # Each widget loads independently with its own spinner
    # =================================================================
    with col_left:
        # Add custom CSS for vertical text in collapsed expander
        st.markdown("""
            <style>
            /* Make expander header text vertical when collapsed */
            div[data-testid="stExpander"] details:not([open]) summary {
                writing-mode: vertical-rl;
                text-orientation: mixed;
                transform: rotate(180deg);
                height: auto;
                min-height: 250px;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 15px 8px !important;
                white-space: nowrap;
                letter-spacing: 1px;
                font-weight: 500;
                background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                transition: all 0.3s ease;
            }

            /* Hover effect for collapsed expander */
            div[data-testid="stExpander"] details:not([open]) summary:hover {
                background: linear-gradient(180deg, #e9ecef 0%, #dee2e6 100%);
                box-shadow: 0 3px 6px rgba(0,0,0,0.1);
                cursor: pointer;
            }

            /* Normal horizontal text when expanded */
            div[data-testid="stExpander"] details[open] summary {
                writing-mode: horizontal-tb;
                text-orientation: mixed;
                transform: none;
                height: auto;
                min-height: auto;
                padding: 12px 16px !important;
                letter-spacing: normal;
                font-weight: 600;
                background: #fff;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.08);
                transition: all 0.3s ease;
            }

            /* Make the collapsed expander narrower */
            div[data-testid="stExpander"] details:not([open]) {
                max-width: 45px;
                margin: 10px 0;
                transition: all 0.3s ease;
            }

            /* Expand to full width when open */
            div[data-testid="stExpander"] details[open] {
                max-width: 100%;
                margin: 10px 0;
                transition: all 0.3s ease;
            }

            /* Smooth transition for expander content */
            div[data-testid="stExpander"] details div[role="region"] {
                transition: all 0.3s ease;
            }

            /* Smooth transition for column resize */
            div[data-testid="column"] {
                transition: width 0.3s ease !important;
            }

            /* Style for toggle button */
            button[data-testid="baseButton-primary"] {
                font-size: 24px !important;
                color: #dc3545 !important;
                background-color: #fff !important;
                border: 1px solid #dee2e6 !important;
                padding: 12px !important;
                min-height: 48px !important;
            }

            button[data-testid="baseButton-primary"]:hover {
                color: #c82333 !important;
                background-color: #f8f9fa !important;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
            }

            /* Make button vertical when collapsed (5% column) */
            div[data-testid="column"]:first-child {
                position: relative;
            }

            /* Detect collapsed state by column width and rotate button */
            @container (max-width: 80px) {
                button[data-testid="baseButton-primary"] {
                    writing-mode: vertical-rl !important;
                    transform: rotate(180deg) !important;
                    min-height: 200px !important;
                    padding: 20px 8px !important;
                }
            }
        </style>
        """, unsafe_allow_html=True)

        # Add a manual toggle button at the top of left column
        if st.session_state.context_panel_expanded:
            # Expanded state - red triangle pointing LEFT (collapse/hide to the left)
            if st.button("◀", key="context_panel_toggle", help="Collapse context panel", use_container_width=True):
                st.session_state.context_panel_expanded = False
                st.rerun()
        else:
            # Collapsed state - vertical red triangle pointing RIGHT (expand/show to the right)
            if st.button("▶", key="context_panel_toggle", help="Expand context panel", use_container_width=True):
                st.session_state.context_panel_expanded = True
                st.rerun()

        # Show content only when expanded
        if st.session_state.context_panel_expanded:
            # PRIORITY 1: Local Text Content (Instant - no API calls)
            st.markdown("#### ▸ Quick Info")
            st.markdown(f"""
            **Location:** {region}, {city}

            **About {region}:**
            Real estate market insights and project analytics for {region} in {city}.
            """)

            st.markdown("---")

            # PRIORITY 2: Weather Widget (Independent, Non-Blocking)
            st.markdown("#### ▸ Weather & Environment")
            weather_cache_key = f"{get_location_key(region, city)}_weather"

            # Check if data is cached
            if weather_cache_key in st.session_state.location_data_cache:
                # Data available - render immediately
                weather_data_container = st.session_state.location_data_cache[weather_cache_key]

                if weather_data_container.get('weather_data') and weather_data_container.get('aqi_data'):
                    weather_data = weather_data_container['weather_data']
                    aqi_data = weather_data_container['aqi_data']

                    temp_icon = weather_service.get_temperature_icon(
                        weather_data['temperature'],
                        weather_data['current_time'],
                        weather_data['sunrise'],
                        weather_data['sunset']
                    )
                    aqi_icon, aqi_category = weather_service.get_aqi_category(aqi_data['aqi'])
                    humidity_icon = weather_service.get_humidity_icon(weather_data['humidity'])

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(label=f"{temp_icon} Temperature", value=f"{weather_data['temperature']}°C")
                    with col2:
                        st.metric(label=f"{humidity_icon} Humidity", value=f"{weather_data['humidity']}%")

                    col3, col4 = st.columns(2)
                    with col3:
                        st.metric(label="🏔️ Elevation", value=f"{weather_data['elevation']} m")
                    with col4:
                        st.metric(label=f"{aqi_icon} AQI", value=f"{aqi_data['aqi']}", delta=aqi_category, delta_color="off")
                else:
                    st.warning("⚠️ Weather data unavailable")
            else:
                # Data not cached - load immediately (DON'T trigger rerun - let natural cycle handle it)
                render_loading_spinner("Loading weather data...")

                # Load in background without blocking
                try:
                    load_weather_data(region, city)
                except:
                    pass  # Error handled in load function

            st.markdown("---")

            # PRIORITY 3: Map Widget (Independent, Non-Blocking, Interactive)
            st.markdown("#### ▸ Google Map & Places")
            map_cache_key = f"{get_location_key(region, city)}_map"

            # Check if data is cached
            if map_cache_key in st.session_state.location_data_cache:
                # Data available - render immediately
                map_data_container = st.session_state.location_data_cache[map_cache_key]

                if map_data_container.get('error'):
                    st.error(f"⚠️ Map loading failed: {map_data_container['error']}")
                elif map_data_container.get('map_data'):
                        # Extract coordinates from aerial_view or street_view data
                    coords = None
                    if 'aerial_view' in map_data_container['map_data']:
                        coords = map_data_container['map_data']['aerial_view'].get('coordinates')
                    elif 'street_view' in map_data_container['map_data']:
                        coords = map_data_container['map_data']['street_view'].get('coordinates')
                    elif 'air_quality' in map_data_container['map_data']:
                        coords = map_data_container['map_data']['air_quality'].get('coordinates')

                    if coords and coords.get('lat') and coords.get('lon'):
                            # Render interactive Google Map
                        location_display = f"{region}, {city}"
                        render_interactive_map(
                            location_name=location_display,
                            lat=coords['lat'],
                            lon=coords['lon'],
                            api_key=GOOGLE_MAPS_API_KEY,
                            height=400
                        )
                    else:
                        st.info("📍 Map coordinates not available")
                else:
                    st.warning("⚠️ Map data unavailable")
            else:
                # Data not cached - load immediately (DON'T trigger rerun - let natural cycle handle it)
                render_loading_spinner("Loading map...")

                # Load in background without blocking
                try:
                    load_map_data(region, city)
                except:
                    pass  # Error handled in load function

            st.markdown("---")

            # PRIORITY 4: Photos Widget (Independent, Non-Blocking, Interactive Carousel)
            st.markdown("#### ▸ Photos")
            # Reuses map data
            if map_cache_key in st.session_state.location_data_cache:
                photo_data = st.session_state.location_data_cache[map_cache_key]
                if photo_data.get('map_data') and photo_data['map_data'].get('images'):
                    images = photo_data['map_data']['images']
                    location_display = f"{region}, {city}"
                    render_interactive_carousel(images, location_display, height=450)
                else:
                    st.info("📷 Photos unavailable")
            else:
                # Map still loading - photos will appear when map loads
                render_loading_spinner("Loading photos...")

            st.markdown("---")

            # PRIORITY 5: Aerial View Widget (Independent, Non-Blocking)
            st.markdown("#### ▸ Aerial / Satellite View")
            if map_cache_key in st.session_state.location_data_cache:
                aerial_data = st.session_state.location_data_cache[map_cache_key]
                if aerial_data.get('map_data') and 'aerial_view' in aerial_data['map_data']:
                    aerial_view = aerial_data['map_data']['aerial_view']
                    if aerial_view.get('image_url'):
                        st.image(aerial_view['image_url'], caption="Satellite View", width=600)
                        if aerial_view.get('note'):
                            st.caption(aerial_view['note'])
                    elif aerial_view.get('error'):
                        st.warning(f"⚠️ {aerial_view['error']}")
                    else:
                        st.info("🛰️ Aerial view not available")
                else:
                    st.info("🛰️ Aerial view not available")
            else:
                render_loading_spinner("Loading aerial view...")

            st.markdown("---")

            # PRIORITY 6: Street View Widget (Independent, Non-Blocking)
            st.markdown("#### ▸ Street View")
            if map_cache_key in st.session_state.location_data_cache:
                street_data = st.session_state.location_data_cache[map_cache_key]
                if street_data.get('map_data') and 'street_view' in street_data['map_data']:
                    street_view = street_data['map_data']['street_view']
                    if street_view.get('available') and street_view.get('image_url'):
                        st.image(street_view['image_url'], caption="Street View", width=600)
                        if street_view.get('note'):
                            st.caption(street_view['note'])
                    elif street_view.get('error'):
                        st.warning(f"⚠️ {street_view['error']}")
                    else:
                        st.info("🚗 Street view not available for this location")
                else:
                    st.info("🚗 Street view not available")
            else:
                render_loading_spinner("Loading street view...")

            st.markdown("---")

            # PRIORITY 7: Additional Tabbed Content (Instant - Local)
            st.markdown("#### Projects | Introduction | Wiki | Local News")
            render_content_tabs(region, city, API_BASE_URL)
        else:
            # Collapsed state - show minimal vertical info
            st.markdown("""
            <div style="writing-mode: vertical-rl; transform: rotate(180deg); text-align: center; padding: 20px 5px; letter-spacing: 2px; font-size: 14px; color: #666;">
                📍 Location Context
            </div>
            """, unsafe_allow_html=True)


# Footer
st.markdown("---")
st.markdown(
    '<p class="secondary-text" style="text-align: center;">Sirrus.AI ATLAS v2.5 | Powered by Liases Foras, Google APIs, Government Data</p>',
    unsafe_allow_html=True
)
