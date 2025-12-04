"""
Context Panel Component: Visual and Informational Context
Displays maps, images, weather, and news for locations and projects
"""
import streamlit as st
import requests
from typing import Dict, Any, Optional


def get_location_context(location_name: str, city: str, api_base_url: str = "http://localhost:8000") -> Optional[Dict]:
    """
    Fetch location context data from API without rendering

    Args:
        location_name: Location name (e.g., "Chakan")
        city: City name (e.g., "Pune")
        api_base_url: Base URL for the API

    Returns:
        Dictionary with context data or None if fetch fails
    """
    try:
        params = {
            "location": location_name,
            "location_type": "region"
        }
        if city:
            params["city"] = city

        response = requests.get(
            f"{api_base_url}/api/context/location",
            params=params,
            timeout=10
        )

        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        return None


def render_context_panel(location_name: str, city: str = None, location_type: str = "region", api_base_url: str = "http://localhost:8000"):
    """
    Render a unified visual context panel for a location

    Displays in ONE section:
    - Google Maps (static image + link)
    - Image collage (4-5 photos)
    - Current weather
    - Air Quality Index

    Args:
        location_name: Location name (e.g., "Chakan")
        city: City name (e.g., "Pune")
        location_type: Type of location ("region" or "project")
        api_base_url: Base URL for the API
    """
    # Title with location name (pre-populated - shown immediately)
    st.markdown(f"### 📍 Location: {location_name}" + (f", {city}" if city else ""))

    try:
        # Show loading state while fetching context data
        with st.spinner("Loading location context..."):
            # Fetch context data from API
            params = {
                "location": location_name,
                "location_type": location_type
            }
            if city:
                params["city"] = city

            response = requests.get(
                f"{api_base_url}/api/context/location",
                params=params,
                timeout=30  # Increased from 10 to 30 seconds
            )

        if response.status_code != 200:
            st.error(f"Failed to load context data: {response.status_code}")
            return

        context = response.json()

        # Render context in a unified panel
        _render_unified_context(context)

    except Exception as e:
        st.error(f"Error loading context: {str(e)}")
        st.info("Make sure the API server is running and context service is configured.")


def _render_unified_context(context: Dict[str, Any]):
    """Render all context components in a unified layout"""

    # 1. MAP SECTION (Full width)
    st.markdown("#### 🗺️ Map")
    map_data = context.get("map", {})

    if map_data.get("static_url"):
        # Display static map image
        st.image(map_data["static_url"], use_column_width=True)

        # Interactive map link
        if map_data.get("embed_url"):
            st.markdown(f"[🔗 Open Interactive Map]({map_data['embed_url']})")
    elif map_data.get("maps_link"):
        # Fallback: Show link to Google Maps
        st.info("🗺️ Map preview unavailable (API key not configured)")
        st.markdown(f"[🔗 View on Google Maps]({map_data['maps_link']})")
    else:
        st.warning("Map data unavailable")

    st.markdown("---")

    # 2. WEATHER & ENVIRONMENT SECTION (2x2 Grid - Visible by Default)
    st.markdown("#### ☀️ Weather & Environment")

    # Create 2x2 grid
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)

    # Row 1, Column 1: WEATHER
    with row1_col1:
        st.markdown("**🌡️ Current Weather**")
        weather = context.get("weather", {})

        if weather.get("temperature") is not None:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 15px; border-radius: 10px; color: white; text-align: center;">
                <h2 style="margin: 0; font-size: 2.5rem;">{weather['temperature']}°C</h2>
                <p style="margin: 5px 0; font-size: 1rem; text-transform: capitalize;">
                    {weather.get('condition', 'Unknown')}
                </p>
                {f'<img src="{weather["icon_url"]}" width="60" />' if weather.get('icon_url') else ''}
                <p style="margin: 8px 0; font-size: 0.8rem;">
                    Feels like {weather.get('feels_like', 'N/A')}°C<br/>
                    Humidity: {weather.get('humidity', 'N/A')}%<br/>
                    Wind: {weather.get('wind_speed', 'N/A')} m/s
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("☀️ Weather unavailable")
            if weather.get("note"):
                st.caption(weather["note"])

    # Row 1, Column 2: AIR QUALITY
    with row1_col2:
        st.markdown("**🌬️ Air Quality**")
        air_quality = context.get("air_quality", {})

        if air_quality.get("aqi") is not None:
            aqi = air_quality["aqi"]
            quality = air_quality["quality"]

            # Color coding based on AQI level
            color_map = {
                1: ("#28a745", "Good"),           # Green
                2: ("#90ee90", "Fair"),           # Light Green
                3: ("#ffc107", "Moderate"),       # Yellow
                4: ("#fd7e14", "Poor"),           # Orange
                5: ("#dc3545", "Very Poor")       # Red
            }

            bg_color, quality_text = color_map.get(aqi, ("#6c757d", "Unknown"))

            st.markdown(f"""
            <div style="background: {bg_color}; padding: 15px; border-radius: 10px;
                        color: white; text-align: center;">
                <h2 style="margin: 0; font-size: 2.2rem;">AQI: {aqi}</h2>
                <p style="margin: 8px 0; font-size: 1.1rem; font-weight: bold;">
                    {quality_text}
                </p>
                <p style="margin: 5px 0; font-size: 0.75rem;">
                    PM2.5: {air_quality.get('components', {}).get('pm2_5', 'N/A')} µg/m³<br/>
                    PM10: {air_quality.get('components', {}).get('pm10', 'N/A')} µg/m³<br/>
                    NO₂: {air_quality.get('components', {}).get('no2', 'N/A')} µg/m³
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("🌬️ Air quality unavailable")
            if air_quality.get("note"):
                st.caption(air_quality["note"])

    # Row 2, Column 1: ELEVATION
    with row2_col1:
        st.markdown("**⛰️ Elevation**")
        elevation = context.get("elevation", {})

        if elevation.get("elevation_m") is not None:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                        padding: 15px; border-radius: 10px; color: white; text-align: center;">
                <h3 style="margin: 0; font-size: 2rem;">{elevation['elevation_m']} m</h3>
                <p style="margin: 5px 0; font-size: 0.85rem;">
                    ({elevation.get('elevation_ft', 0)} ft)
                </p>
                <p style="margin: 8px 0; font-size: 0.75rem;">
                    Temp Adjustment: -{elevation.get('temperature_adjustment', 0)}°C<br/>
                    Adjusted Temp: {elevation.get('adjusted_temperature', 'N/A')}°C
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("⛰️ Elevation data unavailable")

    # Row 2, Column 2: TEMPERATURE DETAILS
    with row2_col2:
        st.markdown("**🌡️ Temperature Details**")
        if weather.get("temperature") is not None and elevation.get("elevation_m") is not None:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                        padding: 15px; border-radius: 10px; color: white; text-align: center;">
                <p style="margin: 5px 0; font-size: 0.9rem;">
                    <strong>Sea Level:</strong> {weather.get('temperature', 'N/A')}°C
                </p>
                <p style="margin: 5px 0; font-size: 0.9rem;">
                    <strong>At {elevation.get('elevation_m', 0)}m:</strong><br/>
                    {elevation.get('adjusted_temperature', 'N/A')}°C
                </p>
                <p style="margin: 8px 0; font-size: 0.75rem;">
                    Difference: -{elevation.get('temperature_adjustment', 0)}°C<br/>
                    (0.65°C per 100m altitude)
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("🌡️ Temperature details unavailable")

    st.markdown("---")

    # 3. LOCATION PHOTOS SECTION
    st.markdown("#### 📷 Location Photos")
    images = context.get("images", [])

    # Filter out images without URLs and validate availability
    valid_images = [img for img in images if img.get("url")]

    if valid_images:
        # Display valid images in a grid (2 columns) with proper height
        num_images = min(len(valid_images), 4)

        if num_images >= 2:
            img_col1, img_col2 = st.columns(2)
            for i, img in enumerate(valid_images[:num_images]):
                with img_col1 if i % 2 == 0 else img_col2:
                    try:
                        # Use width parameter instead of use_column_width for better control
                        st.image(img["url"], caption=img.get("title", "")[:50], width=300)
                    except Exception as e:
                        # Skip images that fail to load (don't show error)
                        pass
        else:
            # Single image
            for img in valid_images[:num_images]:
                try:
                    st.image(img["url"], caption=img.get("title", ""), width=600)
                except Exception as e:
                    # Skip images that fail to load
                    pass
    else:
        st.info("📷 Images unavailable (API key not configured)")
        if images and images[0].get("note"):
            st.caption(images[0]["note"])

    st.markdown("---")

    # 4. STREET VIEW SECTION
    st.markdown("#### 👁️ Street View")
    street_view = context.get("street_view", {})

    if street_view.get("available") and street_view.get("street_view_url"):
        st.image(street_view["street_view_url"], width=600,
                 caption="Street View")
    else:
        st.info("👁️ Street view not available for this location")
        if street_view.get("note"):
            st.caption(street_view["note"])

    st.markdown("---")

    # 5. AERIAL/SATELLITE VIEW SECTION
    st.markdown("#### 🛰️ Aerial/Satellite View")
    aerial_view = context.get("aerial_view", {})

    if aerial_view.get("satellite_url"):
        st.image(aerial_view["satellite_url"], width=600,
                 caption="Satellite View")
        if aerial_view.get("note"):
            st.caption(aerial_view["note"])
    else:
        st.info("🛰️ Aerial view unavailable")

    # ADDITIONAL INFO SECTIONS
    st.markdown("---")

    # 6. DISTANCE MATRIX SECTION
    st.markdown("#### 📏 Key Distances")
    distances = context.get("distances", {})

    if distances and not distances.get("error"):
        # Create table data
        table_data = []
        for key, data in distances.items():
            if isinstance(data, dict) and not data.get("error"):
                dest_name = key.replace("_", " ").title()
                table_data.append({
                    "Destination": dest_name,
                    "Location": data.get("destination", "N/A"),
                    "Distance": data.get("distance", "N/A"),
                    "Travel Time": data.get("duration", "N/A")
                })

        if table_data:
            import pandas as pd
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("📏 Distance data unavailable")
    else:
        st.info("📏 Distance data unavailable")

    st.markdown("---")

    # 7. NEARBY PLACES SECTION
    st.markdown("#### 📍 Nearby Places of Interest")
    nearby_places = context.get("nearby_places", {})

    if nearby_places and not nearby_places.get("error"):
        # Group places into tabs
        tabs = st.tabs(["🏥 Healthcare", "🎓 Education", "🍽️ Dining", "🏨 Hotels",
                        "🛍️ Shopping", "🚉 Transport", "🎭 Recreation", "🕌 Worship"])

        categories = ["hospitals", "schools", "restaurants", "hotels",
                      "malls", "transport", "recreation", "worship"]

        for tab, category in zip(tabs, categories):
            with tab:
                places = nearby_places.get(category, [])
                if places:
                    for i, place in enumerate(places[:5], 1):
                        st.markdown(f"**{i}. {place.get('name', 'Unknown')}**")
                        if place.get('address'):
                            st.caption(f"📍 {place['address']}")
                        st.markdown("---")
                else:
                    st.info(f"No {category} found nearby")
    else:
        st.info("📍 Nearby places data unavailable")

    st.markdown("---")

    # 6. CITY INSIGHTS SECTION (from vectorized city reports)
    st.markdown("#### 📚 City/Region Insights")
    city_insights = context.get("city_insights", {})

    if city_insights.get("salient_features"):
        # Display salient features
        st.markdown(f"**{city_insights.get('city')}" + (f", {city_insights.get('region')}" if city_insights.get('region') and city_insights['region'] != city_insights.get('city') else "") + "**")

        features = city_insights["salient_features"]

        # Display first 5 features in formatted list
        for i, feature in enumerate(features[:5], 1):
            # Clean up feature text (remove markdown bold markers)
            clean_feature = feature.replace("**", "").replace("- ", "").strip()

            # Shorten very long features
            if len(clean_feature) > 200:
                clean_feature = clean_feature[:200] + "..."

            st.markdown(f"{i}. {clean_feature}")

        # Show full context in expander if available
        if city_insights.get("full_context"):
            with st.expander("📖 View Full Context"):
                for idx, context_chunk in enumerate(city_insights["full_context"], 1):
                    st.markdown(f"**Context {idx}:**")
                    st.text(context_chunk[:500] + ("..." if len(context_chunk) > 500 else ""))
                    st.markdown("---")
    elif city_insights.get("error"):
        st.warning(f"⚠️ {city_insights.get('note', 'Unable to fetch city insights')}")
        st.caption(f"Error: {city_insights['error']}")
    elif city_insights.get("note"):
        st.info(city_insights["note"])
    else:
        st.info("📚 City insights unavailable - no vectorized reports for this location")

    st.markdown("---")

    # 11. NEWS SECTION (from newsdata.io)
    st.markdown("#### 📰 Latest News")
    news = context.get("news", {})

    if news.get("articles"):
        articles = news["articles"]
        total_results = news.get("total_results", len(articles))

        st.caption(f"Showing {len(articles)} of {total_results} articles")

        # Display each news article
        for i, article in enumerate(articles, 1):
            with st.container():
                # Article title with link
                if article.get("link"):
                    st.markdown(f"**{i}. [{article.get('title', 'Untitled')}]({article['link']})**")
                else:
                    st.markdown(f"**{i}. {article.get('title', 'Untitled')}**")

                # Article description
                if article.get("description"):
                    st.caption(article["description"][:300] + ("..." if len(article.get("description", "")) > 300 else ""))

                # Article metadata (source and date)
                metadata_parts = []
                if article.get("source_name"):
                    metadata_parts.append(f"📰 {article['source_name']}")
                if article.get("pubDate"):
                    metadata_parts.append(f"📅 {article['pubDate'][:10]}")  # Show only date part

                if metadata_parts:
                    st.caption(" | ".join(metadata_parts))

                st.markdown("---")
    elif news.get("error"):
        st.warning(f"⚠️ {news.get('note', 'Unable to fetch news')}")
        st.caption(f"Error: {news['error']}")
    elif news.get("note"):
        st.info(news["note"])
    else:
        st.info("📰 News unavailable")


def render_region_insights(region: str, city: str = "Pune", api_base_url: str = "http://localhost:8000"):
    """
    Render Layer 4 regional insights panel

    Args:
        region: Region name (e.g., "Chakan")
        city: City name
        api_base_url: Base URL for the API
    """
    st.markdown(f"### 📊 Regional Market Insights: {region}, {city}")

    try:
        response = requests.get(
            f"{api_base_url}/api/context/region",
            params={"region": region, "city": city},
            timeout=10
        )

        if response.status_code != 200:
            st.error(f"Failed to load region insights: {response.status_code}")
            return

        insights = response.json()

        # Display micro-markets
        if insights.get("micro_markets"):
            st.markdown("#### 🏘️ Micro-Markets")
            for mm in insights["micro_markets"][:5]:
                with st.expander(f"📍 {mm.get('text', 'Unknown')[:100]}"):
                    st.markdown(mm.get("text", "No data available"))
                    if mm.get("metadata"):
                        st.caption(f"Source: {mm['metadata'].get('source', 'N/A')}")

        # Display infrastructure
        if insights.get("infrastructure"):
            st.markdown("#### 🏗️ Infrastructure")
            for infra in insights["infrastructure"][:3]:
                st.info(infra.get("text", "No data available"))

        # Display development trends
        if insights.get("development_trends"):
            st.markdown("#### 📈 Development Trends")
            for trend in insights["development_trends"][:3]:
                st.success(trend.get("text", "No data available"))

        # Display price trends
        if insights.get("price_trends"):
            st.markdown("#### 💰 Price Trends")
            for price in insights["price_trends"][:3]:
                st.warning(price.get("text", "No data available"))

    except Exception as e:
        st.error(f"Error loading region insights: {str(e)}")


def render_catchment_insights(catchment_area: str, city: str = "Pune", radius_km: float = None, api_base_url: str = "http://localhost:8000"):
    """
    Render Layer 4 catchment area insights panel

    Args:
        catchment_area: Catchment area name (e.g., "Western Pune")
        city: City name
        radius_km: Radius in kilometers
        api_base_url: Base URL for the API
    """
    st.markdown(f"### 🌐 Catchment Area Insights: {catchment_area}, {city}")

    try:
        params = {"catchment_area": catchment_area, "city": city}
        if radius_km:
            params["radius_km"] = radius_km

        response = requests.get(
            f"{api_base_url}/api/context/catchment",
            params=params,
            timeout=10
        )

        if response.status_code != 200:
            st.error(f"Failed to load catchment insights: {response.status_code}")
            return

        insights = response.json()

        # Display major projects
        if insights.get("major_projects"):
            st.markdown("#### 🏗️ Major Projects")
            for proj in insights["major_projects"][:5]:
                with st.expander(f"📍 {proj.get('text', 'Unknown')[:100]}"):
                    st.markdown(proj.get("text", "No data available"))
                    if proj.get("metadata"):
                        st.caption(f"Similarity: {proj.get('similarity_score', 0):.2%}")

        # Display demographics
        if insights.get("demographics"):
            st.markdown("#### 👥 Demographics & Economic Indicators")
            for demo in insights["demographics"][:3]:
                st.info(demo.get("text", "No data available"))

    except Exception as e:
        st.error(f"Error loading catchment insights: {str(e)}")
