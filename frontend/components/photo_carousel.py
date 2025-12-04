"""
Location Photos Carousel Component
Displays photos in a carousel with thumbnail navigation, expandable views
"""
import streamlit as st
from typing import List, Dict


def render_photo_carousel(images: List[Dict], location_name: str):
    """
    Render photo carousel with thumbnail strip navigation

    Args:
        images: List of image dicts with 'url', 'title', 'source', 'thumbnail'
        location_name: Name of the location for display
    """

    if not images or len(images) == 0:
        st.info(f"📷 No photos available for {location_name}")
        return

    # Filter out broken images (optional - skip images that might be broken)
    valid_images = [img for img in images if img.get('url')]

    if len(valid_images) == 0:
        st.info(f"📷 No valid photos available for {location_name}")
        return

    # Initialize carousel index in session state
    if 'carousel_index' not in st.session_state:
        st.session_state.carousel_index = 0

    # Ensure index is within bounds
    if st.session_state.carousel_index >= len(valid_images):
        st.session_state.carousel_index = 0

    current_index = st.session_state.carousel_index
    current_image = valid_images[current_index]

    # Main photo display with alt-text overlay
    st.markdown(f"### 📸 Location Photos: {location_name}")

    # Display main image with error handling
    try:
        st.image(
            current_image['url'],
            use_container_width=True,
            caption=f"{current_image.get('title', 'Photo')} | Source: {current_image.get('source', 'Unknown')}"
        )
    except Exception as e:
        st.error(f"⚠️ Error loading image: {str(e)}")
        # Auto-skip to next valid image
        if len(valid_images) > 1:
            st.session_state.carousel_index = (current_index + 1) % len(valid_images)
            st.rerun()

    # Navigation controls
    col1, col2, col3 = st.columns([1, 3, 1])

    with col1:
        if st.button("◀ Previous", key="prev_photo", use_container_width=True):
            st.session_state.carousel_index = (current_index - 1) % len(valid_images)
            st.rerun()

    with col2:
        st.markdown(
            f"<div style='text-align: center; padding: 8px;'>"
            f"Photo {current_index + 1} of {len(valid_images)}"
            f"</div>",
            unsafe_allow_html=True
        )

    with col3:
        if st.button("Next ▶", key="next_photo", use_container_width=True):
            st.session_state.carousel_index = (current_index + 1) % len(valid_images)
            st.rerun()

    # Thumbnail strip navigation
    st.markdown("---")
    st.markdown("**Quick Navigation:**")

    # Display thumbnails in a grid (max 6 per row)
    num_cols = min(6, len(valid_images))
    cols = st.columns(num_cols)

    for idx, img in enumerate(valid_images[:6]):  # Show max 6 thumbnails
        with cols[idx % num_cols]:
            # Highlight current thumbnail
            if idx == current_index:
                st.markdown(
                    f"<div style='border: 3px solid #667eea; padding: 2px; border-radius: 4px;'>",
                    unsafe_allow_html=True
                )

            if st.button(f"●", key=f"thumb_{idx}", use_container_width=True):
                st.session_state.carousel_index = idx
                st.rerun()

            if idx == current_index:
                st.markdown("</div>", unsafe_allow_html=True)

    # Expandable full-screen view
    with st.expander("🔍 View Full Screen", expanded=False):
        try:
            st.image(current_image['url'], use_container_width=True)
            st.markdown(f"**Title:** {current_image.get('title', 'Untitled')}")
            st.markdown(f"**Source:** {current_image.get('source', 'Unknown')}")
        except Exception as e:
            st.error(f"⚠️ Error displaying full-screen image: {str(e)}")


def render_street_view(map_data: Dict, location_name: str):
    """Render Street View section (expandable)"""

    with st.expander("🚗 Street View", expanded=False):
        if map_data and 'street_view' in map_data and map_data['street_view'].get('available'):
            street_view_url = map_data['street_view'].get('image_url')
            if street_view_url:
                try:
                    st.image(street_view_url, use_container_width=True)
                    st.caption(f"Street view of {location_name}")
                except Exception as e:
                    st.warning(f"⚠️ Street view not available: {str(e)}")
            else:
                st.info("📍 Street view not available for this location")
        else:
            st.info("📍 Street view not available for this location")


def render_aerial_view(map_data: Dict, location_name: str):
    """Render Aerial/Satellite View section (expandable)"""

    with st.expander("🛰️ Aerial View", expanded=False):
        if map_data and 'aerial_view' in map_data and map_data['aerial_view'].get('image_url'):
            aerial_url = map_data['aerial_view']['image_url']
            try:
                st.image(aerial_url, use_container_width=True)
                st.caption(f"Satellite view of {location_name}")
            except Exception as e:
                st.warning(f"⚠️ Aerial view not available: {str(e)}")
        else:
            st.info("🛰️ Aerial view not available for this location")


def render_location_photos_section(map_data: Dict, location_name: str):
    """
    Render complete location photos section
    - Carousel with main photos
    - Street View (expandable)
    - Aerial View (expandable)

    This section should be placed ABOVE the Introduction|Wiki|News tabs
    """

    if not map_data:
        return

    # Extract images from map_data
    images = map_data.get('images', [])

    # Render carousel
    render_photo_carousel(images, location_name)

    st.markdown("---")

    # Render Street View and Aerial View
    render_street_view(map_data, location_name)
    render_aerial_view(map_data, location_name)
