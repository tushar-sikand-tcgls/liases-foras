"""
Kolkata Knowledge Graph Viewer Component
Visualization for Kolkata real estate market with L0/L1/L2 layers

Features:
- Micromarket explorer (distance-based ranges)
- Project search and comparison
- Quarterly trends (44 quarters from Q2 14-15 to Q2 25-26)
- Unit type analysis (10 categories)
- Interactive charts and metrics
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any, Optional


class KolkataViewer:
    """
    Visualization component for Kolkata Knowledge Graph

    Provides interactive exploration of:
    - Micromarkets (distance-based segmentation)
    - 880+ Projects with L0/L1/L2 metrics
    - Time-series quarterly data
    - Unit type performance
    """

    def __init__(self):
        """Initialize the Kolkata viewer"""
        self.kg_service = None
        self._load_kg_service()

    def _load_kg_service(self):
        """Load Kolkata KG service"""
        try:
            from app.services.kolkata_kg_service import get_kolkata_kg_service
            self.kg_service = get_kolkata_kg_service()
        except Exception as e:
            st.error(f"Error loading Kolkata KG service: {e}")

    # ==================================================================
    # MICROMARKET VISUALIZATION
    # ==================================================================

    def render_micromarket_selector(self) -> Optional[str]:
        """Render micromarket dropdown and return selected ID"""
        if not self.kg_service or not self.kg_service.micromarkets:
            st.warning("No micromarket data available")
            return None

        micromarket_options = {
            f"{mm.micromarket_name} ({mm.distance_range.get('min_km', 0)}-{mm.distance_range.get('max_km', 0)} km)": mm.micromarket_id
            for mm in self.kg_service.micromarkets
        }

        selected_display = st.selectbox(
            "Select Micromarket",
            options=list(micromarket_options.keys()),
            index=0
        )

        return micromarket_options[selected_display]

    def create_micromarket_metrics_chart(self, micromarket_data: Dict) -> go.Figure:
        """Create radar chart for micromarket Layer 2 metrics"""
        layer2 = micromarket_data.get('layer2', {})

        # Extract values
        demand_score = layer2.get('demand_score', {}).get('value', 0) or 0
        opportunity_score = layer2.get('opportunity_score', {}).get('value', 0) or 0

        # Map categorical to numeric
        supply_pressure_map = {"low": 80, "medium": 50, "high": 20}
        competitive_intensity_map = {"low": 80, "medium": 50, "high": 20}

        supply_score = supply_pressure_map.get(layer2.get('supply_pressure', {}).get('value', 'medium'), 50)
        competitive_score = competitive_intensity_map.get(layer2.get('competitive_intensity', {}).get('value', 'medium'), 50)

        categories = ['Demand', 'Opportunity', 'Supply Ease', 'Competition Ease']
        values = [demand_score, opportunity_score, supply_score, competitive_score]

        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=micromarket_data['micromarket_name'],
            line=dict(color='#2E86AB', width=2),
            fillcolor='rgba(46, 134, 171, 0.3)'
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            title='Micromarket Performance Metrics (Layer 2)',
            height=400
        )

        return fig

    def render_micromarket_dashboard(self, micromarket_id: str):
        """Render comprehensive micromarket dashboard"""
        micromarket = self.kg_service.get_micromarket_by_id(micromarket_id)
        if not micromarket:
            st.error(f"Micromarket {micromarket_id} not found")
            return

        mm_data = micromarket.to_dict()

        # Header
        st.markdown(f"## 📍 {mm_data['micromarket_name']}")
        st.markdown(f"**Location:** {mm_data['city']}, {mm_data['state']}")
        st.markdown(f"**Distance Range:** {mm_data['distance_range'].get('min_km', 0)}-{mm_data['distance_range'].get('max_km', 0)} km from {mm_data['distance_range'].get('center_point', 'CBD')}")
        st.markdown(f"**Quarter:** {mm_data['quarter']} | **Data Version:** {mm_data['data_version']}")
        st.markdown("---")

        # Layer 0: Raw Dimensions
        st.markdown("### Layer 0: Raw Dimensions")
        layer0 = mm_data['layer0']

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Projects",
                f"{layer0['total_projects']['value']:,}",
                help="Number of projects in micromarket (U)"
            )
            st.metric(
                "Total Supply",
                f"{layer0['total_supply_units']['value']:,} units",
                help="Total launched units (U)"
            )

        with col2:
            st.metric(
                "Annual Sales",
                f"{layer0['annual_sales_units']['value']:,} units",
                help="Units sold in last 12 months (U/T)"
            )
            st.metric(
                "Unsold Units",
                f"{layer0['unsold_units']['value']:,}",
                help="Current unsold inventory (U)"
            )

        with col3:
            st.metric(
                "Saleable PSF",
                f"₹{layer0['saleable_psf']['value']:,}",
                help="Average price per sq ft (C/L²)"
            )
            st.metric(
                "New Launch PSF",
                f"₹{layer0['new_launch_saleable_psf']['value']:,}",
                help="PSF for new launches (C/L²)"
            )

        with col4:
            st.metric(
                "Months Inventory",
                f"{layer0['months_inventory']['value']:.1f}",
                help="Months to clear inventory (T)"
            )
            st.metric(
                "Avg Unit Size",
                f"{layer0['avg_unit_size_sqft']['value']:,.0f} sq ft",
                help="Average unit size (L²)"
            )

        st.markdown("---")

        # Layer 1: Derived Metrics
        st.markdown("### Layer 1: Derived Metrics")
        layer1 = mm_data['layer1']

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            absorption = layer1['absorption_rate']['value'] or 0
            st.metric(
                "Absorption Rate",
                f"{absorption:.2f}%",
                help=layer1['absorption_rate']['formula']
            )

        with col2:
            velocity = layer1['sales_velocity']['value'] or 0
            st.metric(
                "Sales Velocity",
                f"{velocity:.2f}%/month",
                help=layer1['sales_velocity']['formula']
            )

        with col3:
            unsold_ratio = layer1['unsold_ratio']['value'] or 0
            st.metric(
                "Unsold Ratio",
                f"{unsold_ratio:.2f}%",
                help=layer1['unsold_ratio']['formula']
            )

        with col4:
            turnover = layer1['inventory_turnover']['value'] or 0
            st.metric(
                "Inventory Turnover",
                f"{turnover:.3f}",
                help=layer1['inventory_turnover']['formula']
            )

        st.markdown("---")

        # Layer 2: Financial & Predictive Metrics
        st.markdown("### Layer 2: Financial & Predictive Metrics")
        layer2 = mm_data['layer2']

        col1, col2 = st.columns(2)

        with col1:
            # Metrics
            st.metric(
                "Demand Score",
                f"{layer2['demand_score']['value']}/100",
                help=layer2['demand_score']['formula']
            )
            st.metric(
                "Opportunity Score",
                f"{layer2['opportunity_score']['value']}/100",
                help=layer2['opportunity_score']['formula']
            )
            st.metric(
                "Clearance Timeline",
                f"{layer2['clearance_timeline']['value']:.1f} months",
                help=layer2['clearance_timeline']['formula']
            )

        with col2:
            # Radar chart
            st.plotly_chart(
                self.create_micromarket_metrics_chart(mm_data),
                use_container_width=True
            )

        # Categorical metrics
        col1, col2 = st.columns(2)
        with col1:
            supply_pressure = layer2['supply_pressure']['value']
            color = {"low": "green", "medium": "orange", "high": "red"}.get(supply_pressure, "gray")
            st.markdown(f"**Supply Pressure:** :{color}[{supply_pressure.upper()}]")

        with col2:
            competitive_intensity = layer2['competitive_intensity']['value']
            color = {"low": "green", "medium": "orange", "high": "red"}.get(competitive_intensity, "gray")
            st.markdown(f"**Competitive Intensity:** :{color}[{competitive_intensity.upper()}]")

    # ==================================================================
    # PROJECT VISUALIZATION
    # ==================================================================

    def render_project_search(self):
        """Render project search and list"""
        if not self.kg_service or not self.kg_service.projects:
            st.warning("No project data available")
            return

        st.markdown("### 🏗️ Project Explorer")

        # Search box
        search_query = st.text_input("Search by project name or developer", "")

        # Filter projects
        filtered_projects = self.kg_service.projects
        if search_query:
            search_lower = search_query.lower()
            filtered_projects = [
                p for p in filtered_projects
                if (search_lower in p.project_name.lower() if p.project_name else False) or
                   (search_lower in p.developer_name.lower() if p.developer_name else False)
            ]

        st.info(f"Found {len(filtered_projects)} projects")

        # Display top 10
        for project in filtered_projects[:10]:
            with st.expander(f"{project.project_name} - {project.developer_name}"):
                self.render_project_card(project)

    def render_project_card(self, project):
        """Render project details card"""
        proj_data = project.to_dict()

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Layer 0: Raw Dimensions**")
            layer0 = proj_data['layer0']
            st.markdown(f"""
            - Project ID: {proj_data['project_id']}
            - Location: {proj_data['location']}
            - Total Supply: {layer0['total_supply']['value']:,} units
            - Current Price: ₹{layer0['current_price_psf']['value']:,}/sq ft
            - Project Age: {layer0['project_age_months']['value']} months
            """)

        with col2:
            st.markdown("**Layer 1: Derived Metrics**")
            layer1 = proj_data['layer1']
            sold_pct = layer1['sold_percent']['value'] or 0
            price_appr = layer1['price_appreciation']['value'] or 0
            st.markdown(f"""
            - Sold: {sold_pct:.1f}%
            - Monthly Velocity: {layer1['monthly_sales_velocity']['value'] or 0:.2f}%
            - Price Appreciation: {price_appr:+.1f}%
            """)

            st.markdown("**Layer 2: Financial Metrics**")
            layer2 = proj_data['layer2']
            st.markdown(f"""
            - MOI: {layer2['months_of_inventory']['value'] or 0:.1f} months
            - Price Momentum: {layer2['price_momentum']['value'] or 'N/A'}
            """)

    # ==================================================================
    # QUARTERLY TRENDS VISUALIZATION
    # ==================================================================

    def create_quarterly_sales_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create quarterly sales trend chart"""
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df['quarter'],
            y=df['sales_units'],
            name='Sales (Units)',
            mode='lines+markers',
            line=dict(color='#2E86AB', width=2),
            marker=dict(size=6)
        ))

        fig.update_layout(
            title='Quarterly Sales Trend (U dimension)',
            xaxis=dict(title='Quarter', tickangle=-45),
            yaxis=dict(title='Sales (Units)'),
            hovermode='x unified',
            height=400
        )

        return fig

    def render_quarterly_trends(self):
        """Render quarterly trends dashboard"""
        if not self.kg_service or not self.kg_service.quarters:
            st.warning("No quarterly data available")
            return

        st.markdown("### 📈 Quarterly Trends (44 Quarters)")
        st.markdown("**Time Series: Q2 14-15 to Q2 25-26**")

        # Convert to DataFrame
        quarters_data = [q.to_dict() for q in self.kg_service.quarters]
        df = pd.DataFrame([{
            'quarter': q['quarter'],
            'year': q['year'],
            'sales_units': q['layer0']['sales_units']['value'],
            'supply_units': q['layer0']['supply_units']['value'],
            'avg_psf': q['layer0']['avg_psf']['value'],
            'absorption_rate': q['layer1']['absorption_rate']['value']
        } for q in quarters_data])

        # Summary stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Quarters", len(df))
        with col2:
            st.metric("Avg Sales", f"{df['sales_units'].mean():.0f} units")
        with col3:
            st.metric("Avg Absorption", f"{df['absorption_rate'].mean():.1f}%")
        with col4:
            st.metric("Latest PSF", f"₹{df['avg_psf'].iloc[-1]:,}")

        # Charts
        st.plotly_chart(
            self.create_quarterly_sales_chart(df),
            use_container_width=True
        )

    # ==================================================================
    # UNIT TYPE ANALYSIS
    # ==================================================================

    def render_unit_type_analysis(self):
        """Render unit type performance analysis"""
        if not self.kg_service or not self.kg_service.unit_types:
            st.warning("No unit type data available")
            return

        st.markdown("### 🏠 Unit Type Analysis (10 Categories)")

        # Create comparison DataFrame
        unit_types_data = [ut.to_dict() for ut in self.kg_service.unit_types]
        df = pd.DataFrame([{
            'unit_type': ut['unit_type'],
            'sales_units': ut['layer0']['sales_units']['value'],
            'supply_units': ut['layer0']['supply_units']['value'],
            'avg_psf': ut['layer0']['avg_psf']['value'],
            'absorption_rate': ut['layer1']['absorption_rate']['value'] or 0
        } for ut in unit_types_data])

        # Bar chart: Absorption by unit type
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df['unit_type'],
            y=df['absorption_rate'],
            marker=dict(color='#F18F01'),
            text=df['absorption_rate'].apply(lambda x: f'{x:.1f}%'),
            textposition='outside'
        ))

        fig.update_layout(
            title='Absorption Rate by Unit Type (Layer 1 Metric)',
            xaxis=dict(title='Unit Type'),
            yaxis=dict(title='Absorption Rate (%)'),
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

        # Data table
        with st.expander("📋 View Unit Type Data Table"):
            st.dataframe(df, use_container_width=True)

    # ==================================================================
    # MAIN RENDER METHOD
    # ==================================================================

    def render(self):
        """Main render method for Kolkata viewer"""
        st.title("🗺️ Kolkata Real Estate Knowledge Graph")
        st.markdown("**West Bengal | Mega Knowledge Graph with L0/L1/L2 Layers**")
        st.markdown("---")

        if not self.kg_service:
            st.error("Kolkata KG service not available")
            return

        # Metadata
        metadata = self.kg_service.get_metadata()
        st.markdown(f"""
        **📊 Data Coverage:**
        - Micromarkets: {len(self.kg_service.micromarkets)} distance-based ranges
        - Projects: {len(self.kg_service.projects)} real estate developments
        - Quarters: {len(self.kg_service.quarters)} (Q2 14-15 to Q2 25-26)
        - Unit Types: {len(self.kg_service.unit_types)} categories
        """)

        st.markdown("---")

        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs([
            "🏙️ Micromarkets",
            "🏗️ Projects",
            "📈 Quarterly Trends",
            "🏠 Unit Types"
        ])

        with tab1:
            micromarket_id = self.render_micromarket_selector()
            if micromarket_id:
                self.render_micromarket_dashboard(micromarket_id)

        with tab2:
            self.render_project_search()

        with tab3:
            self.render_quarterly_trends()

        with tab4:
            self.render_unit_type_analysis()


# Convenience function for direct import
def render_kolkata_viewer():
    """Render the Kolkata viewer"""
    viewer = KolkataViewer()
    viewer.render()
