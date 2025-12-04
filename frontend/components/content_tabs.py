"""
Content Tabs Component for Introduction, Wiki, and News
"""
import streamlit as st
import requests
from typing import Dict, Optional


def render_introduction_tab(location_name: str, city: str, api_base_url: str):
    """Render Introduction tab with location context"""

    st.markdown(f"""
    ### Introduction to {location_name}, {city}

    **Location**: {location_name} is a rapidly growing micro-market in {city}, India.

    #### Key Highlights:
    - **Strategic Location**: Well-connected to major highways and transport hubs
    - **Industrial Hub**: Home to numerous manufacturing and IT companies
    - **Growing Infrastructure**: Ongoing development of roads, metro connectivity
    - **Real Estate Demand**: High demand for residential and commercial properties

    #### Distance from Key Landmarks:
    """)

    # Fetch distance data from Google Distance Matrix API
    try:
        print(f"[DEBUG] Fetching distances for {location_name}, {city}")
        response = requests.get(
            f"{api_base_url}/api/context/distances",
            params={"location": location_name, "city": city},
            timeout=30  # Increased timeout for Distance Matrix API
        )
        print(f"[DEBUG] Distance API response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"[DEBUG] Distance API data: {data}")

            if "error" in data:
                st.warning(f"⚠️ {data['error']}")
            elif data.get("distances"):
                for destination in data["distances"]:
                    st.markdown(f"""
                    - **{destination['destination'].split(',')[0]}**: {destination['distance']}
                      ({destination['duration']} by car)
                    """)
            else:
                st.info("Distance data loading...")
        else:
            st.warning(f"⚠️ Distance API error: {response.status_code}")
    except Exception as e:
        print(f"[DEBUG] Distance API exception: {str(e)}")
        st.warning(f"⚠️ Error loading distances: {str(e)}")

    st.markdown("---")

    # Location Photos from Google Custom Search
    st.markdown("#### Location Photos")
    try:
        print(f"[DEBUG] Fetching images for {location_name}, {city}")
        response = requests.get(
            f"{api_base_url}/api/context/location",
            params={"location": f"{location_name}, {city}", "location_type": "region"},
            timeout=20  # Increased timeout for API calls
        )
        print(f"[DEBUG] Imagery API response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"[DEBUG] Imagery API data keys: {data.keys()}")

            # Extract images array and get URLs
            images_data = data.get("images", [])
            print(f"[DEBUG] Found {len(images_data)} image objects")

            if images_data:
                # Extract URLs from image objects
                image_urls = [img.get("url") for img in images_data if isinstance(img, dict) and img.get("url")]
                print(f"[DEBUG] Extracted {len(image_urls)} image URLs")

                if image_urls:
                    # Display images in 3-column grid
                    cols = st.columns(3)
                    for idx, img_url in enumerate(image_urls[:6]):  # Show max 6 images
                        with cols[idx % 3]:
                            try:
                                # Use width parameter instead for compatibility
                                st.image(img_url, width=300)
                            except Exception as img_err:
                                print(f"[DEBUG] Error displaying image {img_url}: {str(img_err)}")
                else:
                    st.info("📷 Location imagery loading from Google APIs...")
            else:
                st.info("📷 Location imagery loading from Google APIs...")
        else:
            st.warning(f"⚠️ Imagery API error: {response.status_code}")
    except Exception as e:
        print(f"[DEBUG] Imagery API exception: {str(e)}")
        st.warning(f"⚠️ Error loading images: {str(e)}")


def render_wiki_tab(location_name: str, city: str, api_base_url: str):
    """Render Wiki tab with detailed region information from VectorDB"""

    st.markdown(f"### Detailed Information: {location_name}, {city}")

    # Try to fetch wiki-like content from VectorDB
    try:
        response = requests.get(
            f"{api_base_url}/api/vectordb/region_info",
            params={"location": location_name, "city": city}
        )
        if response.status_code == 200:
            data = response.json()
            content = data.get("content", "")

            if content:
                st.markdown(content)
            else:
                # Fallback to default content
                render_default_wiki_content(location_name, city)
        else:
            render_default_wiki_content(location_name, city)
    except Exception as e:
        render_default_wiki_content(location_name, city)


def render_default_wiki_content(location_name: str, city: str):
    """Render default wiki-like content"""

    st.markdown(f"""
    #### History

    {location_name} has evolved from a rural area to a thriving {
        "industrial" if location_name == "Chakan" else "residential"
    } hub over the past two decades.

    #### Geography & Climate

    - **Elevation**: ~600m above sea level
    - **Climate**: Tropical wet and dry climate
    - **Temperature**: 20°C to 38°C (varies by season)
    - **Rainfall**: Moderate during monsoon season (June-September)

    #### Economy

    The region is known for:
    - {
        "Manufacturing and automobile industry" if location_name == "Chakan"
        else "IT and software services" if location_name in ["Hinjewadi", "Baner"]
        else "Mixed residential and commercial development"
    }
    - Growing real estate sector
    - Infrastructure development projects

    #### Culture & Lifestyle

    - **Education**: Multiple schools and educational institutions
    - **Healthcare**: Hospitals and medical facilities nearby
    - **Recreation**: Parks, malls, and entertainment options
    - **Cuisine**: Diverse dining options (Maharashtrian, North Indian, Chinese, Continental)

    #### Unique Features

    {location_name} stands out for:
    - {
        "Proximity to major automobile manufacturing plants" if location_name == "Chakan"
        else "IT park and tech campuses" if location_name == "Hinjewadi"
        else "Upscale residential developments" if location_name == "Baner"
        else "Balanced urban-suburban lifestyle"
    }
    """)


def render_news_tab(location_name: str, city: str, api_base_url: str):
    """Render News tab with 3 time-based news categories"""

    st.markdown(f"### 📰 News: {location_name}, {city}")

    # Try to fetch news from API
    try:
        response = requests.get(
            f"{api_base_url}/api/context/news",
            params={"location": location_name, "city": city},
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()

            if "error" in data:
                st.error(f"⚠️ {data['error']}")
                render_default_news(location_name, city)
                return

            latest = data.get("latest", [])
            month = data.get("month", [])
            year = data.get("year", [])

            # Category 1: Latest News (Last 7 days)
            st.markdown("#### 🔥 Latest News (Last 7 Days)")
            if latest:
                for idx, item in enumerate(latest, 1):
                    render_news_item(idx, item, "#e74c3c")
            else:
                st.info("No news in the last 7 days")

            st.markdown("---")

            # Category 2: Big Stories (Last Month)
            st.markdown("#### 📊 Big Stories (Last Month)")
            if month:
                for idx, item in enumerate(month, 1):
                    render_news_item(idx, item, "#3498db")
            else:
                st.info("No major stories in the last month")

            st.markdown("---")

            # Category 3: Big Stories (Last Year)
            st.markdown("#### 📈 Big Stories (Last Year)")
            if year:
                for idx, item in enumerate(year, 1):
                    render_news_item(idx, item, "#27ae60")
            else:
                st.info("No major stories in the last year")

        else:
            st.error(f"⚠️ API Error: {response.status_code}")
            render_default_news(location_name, city)
    except Exception as e:
        st.error(f"⚠️ Error fetching news: {str(e)}")
        render_default_news(location_name, city)


def render_news_item(idx: int, item: Dict, color: str):
    """Render a single news item card"""
    st.markdown(f"""
    <div style="
        border-left: 4px solid {color};
        padding: 12px 16px;
        margin-bottom: 15px;
        background-color: #f8f9fa;
        border-radius: 4px;
    ">
        <h4 style="margin:0; color:{color};">{idx}. {item.get('title', 'News Item')}</h4>
        <p style="margin:8px 0 0 0; color:#666; font-size:0.9rem; line-height:1.5;">
            {item.get('description', 'No description available')}
        </p>
        <p style="margin:8px 0 0 0; font-size:0.85rem; color:#999;">
            <strong>{item.get('source', 'Unknown source')}</strong> • {item.get('date', 'Recent')} • <a href="{item.get('url', '#')}" target="_blank" style="color:{color};">Read more →</a>
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_default_news(location_name: str, city: str):
    """Render placeholder news"""

    st.info(f"Loading latest news for {location_name}, {city} from newsdata.io and Google News API...")

    news_items = [
        {
            "title": "New Metro Line Extension Announced",
            "description": f"The government has approved a metro extension to {location_name}, expected to complete by 2027.",
            "date": "2 days ago",
            "url": "https://timesofindia.indiatimes.com/city/pune/metro-news"
        },
        {
            "title": "Real Estate Prices Show Upward Trend",
            "description": f"Property prices in {location_name} have increased by 8% this quarter due to improved connectivity.",
            "date": "5 days ago",
            "url": "https://economictimes.indiatimes.com/industry/services/property-/-cstruction/real-estate-news"
        },
        {
            "title": "New IT Park Development Begins",
            "description": f"Construction of a 5-acre IT park has begun in {location_name}, creating job opportunities.",
            "date": "1 week ago",
            "url": "https://www.business-standard.com/india-news"
        }
    ]

    for idx, item in enumerate(news_items, 1):
        with st.container():
            st.markdown(f"""
            <div style="
                border-left: 4px solid #1e3c72;
                padding: 10px 15px;
                margin-bottom: 15px;
                background-color: #f8f9fa;
                border-radius: 4px;
            ">
                <h4 style="margin:0; color:#1e3c72;">{idx}. {item['title']}</h4>
                <p style="margin:5px 0 0 0; color:#666; font-size:0.9rem;">
                    {item['description']}
                </p>
                <p style="margin:5px 0 0 0; font-size:0.85rem; color:#999;">
                    {item['date']} | <a href="{item.get('url', '#')}" target="_blank" style="color:#133D6E; text-decoration:none; font-weight:600;">Read more →</a>
                </p>
            </div>
            """, unsafe_allow_html=True)


def render_projects_tab(location_name: str, api_base_url: str):
    """Render Projects tab with 4-column HTML table"""

    st.markdown(f"""
    ### Projects in {location_name}
    """)

    try:
        # Fetch projects from the API
        response = requests.get(
            f"{api_base_url}/api/projects/by-location",
            params={"location": location_name},
            timeout=5
        )

        if response.status_code == 200:
            projects = response.json()

            if projects:
                # Create HTML table with 4 columns
                table_html = """
                <div style="margin: 20px 0;">
                <table style="width: 100%; border-collapse: collapse; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden;">
                    <thead>
                        <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                            <th style="padding: 14px; text-align: left; font-weight: 600; font-size: 14px;">Project Name</th>
                            <th style="padding: 14px; text-align: left; font-weight: 600; font-size: 14px;">Developer Name</th>
                            <th style="padding: 14px; text-align: left; font-weight: 600; font-size: 14px;">Launch Date</th>
                            <th style="padding: 14px; text-align: left; font-weight: 600; font-size: 14px;">Possession Date</th>
                        </tr>
                    </thead>
                    <tbody>
                """

                # Add rows for each project
                for idx, project in enumerate(projects):
                    # Alternate row colors
                    row_bg = "#f8f9fa" if idx % 2 == 0 else "#ffffff"

                    project_name = project.get('projectName', 'N/A')
                    developer_name = project.get('developerName', 'N/A')

                    # Clean up developer name (remove newlines and extra spaces)
                    if developer_name and developer_name != 'N/A':
                        developer_name = ' '.join(developer_name.split())

                    # Extract launch and possession dates (already extracted by data_service.get_value)
                    launch_date = project.get('launchDate') or 'N/A'
                    possession_date = project.get('possessionDate') or 'N/A'

                    # Convert to string if not None
                    if launch_date and launch_date != 'N/A':
                        launch_date = str(launch_date)
                    if possession_date and possession_date != 'N/A':
                        possession_date = str(possession_date)

                    # Escape HTML special characters
                    import html
                    project_name = html.escape(str(project_name))
                    developer_name = html.escape(str(developer_name))
                    launch_date = html.escape(str(launch_date))
                    possession_date = html.escape(str(possession_date))

                    table_html += f"""
                    <tr style="background: {row_bg}; border-bottom: 1px solid #e0e0e0;">
                        <td style="padding: 12px; font-size: 13px; color: #333; font-weight: 500;">{project_name}</td>
                        <td style="padding: 12px; font-size: 13px; color: #555;">{developer_name}</td>
                        <td style="padding: 12px; font-size: 13px; color: #555;">{launch_date}</td>
                        <td style="padding: 12px; font-size: 13px; color: #555;">{possession_date}</td>
                    </tr>
                    """

                table_html += """
                    </tbody>
                </table>
                </div>
                """

                # Display the table using st.components
                st.components.v1.html(table_html, height=min(600, max(250, len(projects) * 45 + 80)), scrolling=True)

                # Show count
                st.info(f"📊 Showing {len(projects)} project(s) in {location_name}")
            else:
                st.warning(f"No projects found in {location_name}")
        else:
            st.error(f"Failed to fetch projects (Status: {response.status_code})")

    except Exception as e:
        st.error(f"Error loading projects: {str(e)}")


def render_content_tabs(location_name: str, city: str, api_base_url: str):
    """Render all content tabs (Projects, Introduction, Wiki, News)"""

    # Projects tab is now the first and default selected tab
    tab0, tab1, tab2, tab3 = st.tabs(["Projects", "Introduction", "Wiki", "Local News"])

    with tab0:
        render_projects_tab(location_name, api_base_url)

    with tab1:
        render_introduction_tab(location_name, city, api_base_url)

    with tab2:
        render_wiki_tab(location_name, city, api_base_url)

    with tab3:
        render_news_tab(location_name, city, api_base_url)
