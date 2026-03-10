"""
Test script for project profile features

Tests:
1. Location query → Google Maps embed
2. Project overview → Comprehensive profile

Run: streamlit run test_project_profile.py
"""

import streamlit as st
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from frontend.components.project_profile import (
    render_google_map,
    render_metadata_card,
    render_key_stats,
    render_suggested_questions,
    detect_location_query,
    detect_project_overview_query
)

# Page config
st.set_page_config(
    page_title="Project Profile Test",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 Project Profile Features - Test")

# Test data for Sara City
sara_city_data = {
    "projectName": {"value": "Sara City", "unit": "Text"},
    "developerName": {"value": "Sara Builders & Developers (Sara Group)", "unit": "Text"},
    "location": {"value": "Chakan", "unit": "Text"},
    "latitude": {"value": 18.7556934, "unit": "degrees"},
    "longitude": {"value": 73.8367202, "unit": "degrees"},
    "launchDate": {"value": "2014", "unit": "Year"},
    "possessionDate": {"value": "2020", "unit": "Year"},
    "reraRegistered": {"value": "Yes", "unit": "Text"},
    "projectSizeUnits": {"value": 3018, "unit": "units"},
    "totalSupplyUnits": {"value": 1109, "unit": "units"},
    "currentPricePSF": {"value": 3996, "unit": "INR/sqft"},
    "soldPct": {"value": 71, "unit": "%"},
    "unsoldPct": {"value": 29, "unit": "%"},
    "annualSalesUnits": {"value": 527, "unit": "units/year"}
}

# Sidebar navigation
test_mode = st.sidebar.radio(
    "Select Test",
    ["Location Query", "Project Overview", "Component Gallery"]
)

if test_mode == "Location Query":
    st.header("📍 Location Query Test")

    question = st.text_input(
        "Enter question:",
        value="Where is Sara City?"
    )

    if st.button("Test Location Detection"):
        is_location = detect_location_query(question)
        st.write(f"**Location query detected:** {is_location}")

        if is_location:
            st.markdown("---")
            st.success("✅ Location query detected! Rendering Google Maps embed...")

            # Render map
            render_google_map(
                sara_city_data['latitude']['value'],
                sara_city_data['longitude']['value'],
                sara_city_data['projectName']['value']
            )

elif test_mode == "Project Overview":
    st.header("📊 Project Overview Test")

    question = st.text_input(
        "Enter question:",
        value="Tell me about Sara City"
    )

    if st.button("Test Overview Detection"):
        is_overview = detect_project_overview_query(question)
        st.write(f"**Overview query detected:** {is_overview}")

        if is_overview:
            st.markdown("---")
            st.success("✅ Overview query detected! Rendering full profile...")

            # Render metadata card
            render_metadata_card(sara_city_data)

            # Render map
            render_google_map(
                sara_city_data['latitude']['value'],
                sara_city_data['longitude']['value'],
                sara_city_data['projectName']['value']
            )

            # Render key stats
            render_key_stats(sara_city_data)

            # Performance analysis (mock)
            st.markdown("""
            ### 📈 Performance Analysis

            Sara City has achieved **71% sales** over 11 years since launch. Key highlights:

            - **Absorption Rate:** 47.5% annually (Strong performance)
            - **Sales Velocity:** 527 units/year (Excellent demand)
            - **Price Growth:** ₹2,200 → ₹3,996 (82% increase over 11 years)

            **Assessment:** Excellent

            **Reason:** High absorption rate combined with strong price appreciation indicates this is a market favorite in Chakan. The 71% sales achievement over 11 years demonstrates consistent demand and good developer credibility.
            """)

            # Area comparison (mock)
            st.markdown("""
            ### 📊 Comparison with Chakan Market

            Sara City ranks **2nd** out of 9 projects in Chakan for overall performance:

            - **PSF:** ₹3,996 vs Market Avg ₹3,750 (Above by 6.6%)
            - **Absorption:** 47.5% vs Market Avg 35% (Above by 35.7%)
            - **Supply:** 1,109 units (12% of total Chakan supply)

            **Top Projects in Area:**
            1. Gulmohar City - PSF: ₹4,330, Absorption: 52%
            2. **Sara City** - PSF: ₹3,996, Absorption: 47.5%
            3. The Urbana - PSF: ₹3,725, Absorption: 42%

            **Market Position:** Above Average - Sara City outperforms most projects in Chakan across key metrics.
            """)

            # Suggested questions
            render_suggested_questions(
                sara_city_data['projectName']['value'],
                sara_city_data['location']['value']
            )

else:  # Component Gallery
    st.header("🎨 Component Gallery")

    st.subheader("1. Metadata Card")
    render_metadata_card(sara_city_data)

    st.subheader("2. Google Maps Embed")
    render_google_map(
        sara_city_data['latitude']['value'],
        sara_city_data['longitude']['value'],
        sara_city_data['projectName']['value']
    )

    st.subheader("3. Key Stats Grid")
    render_key_stats(sara_city_data)

    st.subheader("4. Suggested Questions")
    render_suggested_questions(
        sara_city_data['projectName']['value'],
        sara_city_data['location']['value']
    )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 12px;'>
    Project Profile Features Test | Liases Foras × Sirrus.AI
</div>
""", unsafe_allow_html=True)
