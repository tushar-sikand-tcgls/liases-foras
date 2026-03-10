"""
Quarterly Market Trends Visualization Component
Layer 0 time-series data (U, L², T) with interactive charts and analytics
Pillar 1: Market Intelligence - Temporal Analysis
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any, Optional
from datetime import datetime


class QuarterlyMarketPanel:
    """
    Visualization component for quarterly sales and marketable supply data

    Features:
    - Time-series charts (sales, supply, absorption rate)
    - YoY and QoQ growth analysis
    - Summary statistics
    - Interactive filtering by year range
    - Layer 0 dimensional view
    """

    def __init__(self):
        """Initialize the quarterly market panel"""
        self.api_base_url = "http://localhost:8000"

    def fetch_quarterly_data(self) -> Dict[str, Any]:
        """Fetch all quarterly data from the backend"""
        try:
            import requests
            response = requests.get(
                f"{self.api_base_url}/api/quarterly-market/all",
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            st.error(f"Error fetching quarterly data: {e}")
            return None

    def fetch_yoy_growth(self, metric: str = 'sales_units') -> Dict[str, Any]:
        """Fetch YoY growth data"""
        try:
            import requests
            response = requests.get(
                f"{self.api_base_url}/api/quarterly-market/yoy-growth",
                params={"metric": metric},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            st.error(f"Error fetching YoY growth: {e}")
            return None

    def fetch_absorption_rate_trend(self) -> Dict[str, Any]:
        """Fetch absorption rate trend"""
        try:
            import requests
            response = requests.get(
                f"{self.api_base_url}/api/quarterly-market/absorption-rate",
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            st.error(f"Error fetching absorption rate: {e}")
            return None

    def create_sales_supply_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create dual-axis chart for sales and supply"""
        fig = go.Figure()

        # Sales line (left axis)
        fig.add_trace(go.Scatter(
            x=df['quarter'],
            y=df['sales_units'],
            name='Sales (Units)',
            mode='lines+markers',
            line=dict(color='#2E86AB', width=2),
            marker=dict(size=6),
            yaxis='y1'
        ))

        # Supply line (right axis)
        fig.add_trace(go.Scatter(
            x=df['quarter'],
            y=df['supply_units'],
            name='Supply (Units)',
            mode='lines+markers',
            line=dict(color='#A23B72', width=2),
            marker=dict(size=6),
            yaxis='y2'
        ))

        # Layout with dual y-axes
        fig.update_layout(
            title='Quarterly Sales vs Marketable Supply (Units)',
            xaxis=dict(
                title='Quarter',
                tickangle=-45
            ),
            yaxis=dict(
                title='Sales (Units)',
                titlefont=dict(color='#2E86AB'),
                tickfont=dict(color='#2E86AB')
            ),
            yaxis2=dict(
                title='Supply (Units)',
                titlefont=dict(color='#A23B72'),
                tickfont=dict(color='#A23B72'),
                overlaying='y',
                side='right'
            ),
            hovermode='x unified',
            height=500,
            showlegend=True,
            legend=dict(x=0.01, y=0.99)
        )

        return fig

    def create_area_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create area chart for sales and supply in million sq ft"""
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df['quarter'],
            y=df['sales_area_mn_sqft'],
            name='Sales Area (mn sq ft)',
            mode='lines',
            line=dict(color='#2E86AB', width=0),
            fillcolor='rgba(46, 134, 171, 0.3)',
            fill='tozeroy'
        ))

        fig.add_trace(go.Scatter(
            x=df['quarter'],
            y=df['supply_area_mn_sqft'],
            name='Supply Area (mn sq ft)',
            mode='lines',
            line=dict(color='#A23B72', width=0),
            fillcolor='rgba(162, 59, 114, 0.3)',
            fill='tozeroy'
        ))

        fig.update_layout(
            title='Quarterly Sales vs Supply (Area in Million Sq Ft)',
            xaxis=dict(title='Quarter', tickangle=-45),
            yaxis=dict(title='Area (Million Sq Ft)'),
            hovermode='x unified',
            height=450,
            showlegend=True,
            legend=dict(x=0.01, y=0.99)
        )

        return fig

    def create_absorption_rate_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create absorption rate trend chart"""
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df['quarter'],
            y=df['absorption_rate_pct'],
            name='Absorption Rate (%)',
            mode='lines+markers',
            line=dict(color='#F18F01', width=3),
            marker=dict(size=7),
            fill='tozeroy',
            fillcolor='rgba(241, 143, 1, 0.2)'
        ))

        # Add horizontal line for average
        avg_absorption = df['absorption_rate_pct'].mean()
        fig.add_hline(
            y=avg_absorption,
            line_dash='dash',
            line_color='red',
            annotation_text=f'Avg: {avg_absorption:.1f}%',
            annotation_position='right'
        )

        fig.update_layout(
            title='Quarterly Absorption Rate Trend (Layer 1 Derived Metric)',
            xaxis=dict(title='Quarter', tickangle=-45),
            yaxis=dict(title='Absorption Rate (%)'),
            hovermode='x unified',
            height=450
        )

        return fig

    def create_yoy_growth_chart(self, df: pd.DataFrame, metric_name: str) -> go.Figure:
        """Create YoY growth chart"""
        fig = go.Figure()

        # Create color array (green for positive, red for negative)
        colors = ['#27AE60' if x > 0 else '#E74C3C' for x in df['yoy_growth_pct']]

        fig.add_trace(go.Bar(
            x=df['quarter'],
            y=df['yoy_growth_pct'],
            name='YoY Growth (%)',
            marker=dict(color=colors),
            text=df['yoy_growth_pct'].apply(lambda x: f'{x:+.1f}%'),
            textposition='outside'
        ))

        fig.add_hline(y=0, line_dash='solid', line_color='gray', line_width=1)

        fig.update_layout(
            title=f'Year-over-Year Growth: {metric_name}',
            xaxis=dict(title='Quarter', tickangle=-45),
            yaxis=dict(title='YoY Growth (%)'),
            height=450,
            showlegend=False
        )

        return fig

    def render_summary_statistics(self, data: List[Dict[str, Any]]):
        """Render summary statistics cards"""
        df = pd.DataFrame(data)

        st.markdown("### 📊 Summary Statistics (All Time)")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Average Sales",
                f"{df['sales_units'].mean():.0f} units",
                delta=None
            )
            st.metric(
                "Peak Sales",
                f"{df['sales_units'].max():,} units",
                delta=None
            )

        with col2:
            st.metric(
                "Average Supply",
                f"{df['supply_units'].mean():.0f} units",
                delta=None
            )
            st.metric(
                "Peak Supply",
                f"{df['supply_units'].max():,} units",
                delta=None
            )

        with col3:
            avg_absorption = ((df['sales_units'] / df['supply_units']) * 100).mean()
            st.metric(
                "Avg Absorption Rate",
                f"{avg_absorption:.2f}%",
                delta=None
            )
            st.metric(
                "Total Quarters",
                f"{len(df)}",
                delta=None
            )

        with col4:
            total_sales = df['sales_units'].sum()
            total_supply = df['supply_units'].sum()
            st.metric(
                "Total Sales",
                f"{total_sales:,} units",
                delta=None
            )
            st.metric(
                "Total Supply",
                f"{total_supply:,} units",
                delta=None
            )

    def render_layer0_dimensions(self, quarter_data: Dict[str, Any]):
        """Render Layer 0 dimensional breakdown for a selected quarter"""
        st.markdown(f"### 🔍 Layer 0 Dimensions: {quarter_data['quarter']}")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**U (Units) - Dimension**")
            st.info(f"""
            - Sales Units: **{quarter_data['sales_units']:,}**
            - Supply Units: **{quarter_data['supply_units']:,}**
            - Dimension Type: Discrete count (U)
            """)

            st.markdown("**L² (Area) - Dimension**")
            st.info(f"""
            - Sales Area: **{quarter_data['sales_area_mn_sqft']:.2f} million sq ft**
            - Supply Area: **{quarter_data['supply_area_mn_sqft']:.2f} million sq ft**
            - Dimension Type: Continuous area (L²)
            """)

        with col2:
            st.markdown("**T (Time) - Dimension**")
            st.info(f"""
            - Quarter: **{quarter_data['quarter']}**
            - Quarter ID: **{quarter_data['quarter_id']}**
            - Year: **{quarter_data['year']}**
            - Dimension Type: Temporal (T)
            """)

            # Calculate Layer 1 derived metrics
            absorption_rate = (quarter_data['sales_units'] / quarter_data['supply_units'] * 100) if quarter_data['supply_units'] > 0 else 0
            avg_sale_unit_size = (quarter_data['sales_area_mn_sqft'] * 1_000_000 / quarter_data['sales_units']) if quarter_data['sales_units'] > 0 else 0

            st.markdown("**Layer 1 Derived Metrics**")
            st.success(f"""
            - Absorption Rate: **{absorption_rate:.2f}%** = (U_sales / U_supply) × 100
            - Avg Unit Size (Sales): **{avg_sale_unit_size:,.0f} sq ft** = L²_sales / U_sales
            """)

    def render(self):
        """Main render method for the quarterly market panel"""
        st.title("📈 Quarterly Market Trends")
        st.markdown("**Layer 0 Time-Series Data (U, L², T) | Pillar 1: Market Intelligence**")
        st.markdown("---")

        # Fetch data directly from backend service
        try:
            from app.services.quarterly_market_service import quarterly_market_service

            all_data = quarterly_market_service.get_all_quarters()
            metadata = quarterly_market_service.get_metadata()

            if not all_data:
                st.warning("No quarterly data available")
                return

            # Display metadata with location
            location_info = metadata.get('location', {})
            # Build location string dynamically from metadata
            region = location_info.get('region', 'Region')
            city = location_info.get('city', '')
            state = location_info.get('state', '')

            location_parts = [region]
            if city:
                location_parts.append(city)
            if state:
                location_parts.append(state)
            location_str = ', '.join(location_parts)

            st.markdown(f"""
            **📍 Location:** {location_str}
            **Data Source:** {metadata.get('source')}
            **Pillar:** {metadata.get('pillar')}
            **Date Range:** {metadata.get('date_range', {}).get('start')} to {metadata.get('date_range', {}).get('end')}
            **Last Updated:** {metadata.get('last_updated')}
            """)

            st.markdown("---")

            # Summary statistics
            self.render_summary_statistics(all_data)

            st.markdown("---")

            # Convert to DataFrame
            df = pd.DataFrame(all_data)

            # Year range filter
            st.markdown("### 🎯 Filter by Year Range")
            col1, col2 = st.columns(2)
            with col1:
                start_year = st.selectbox("Start Year", options=sorted(df['year'].unique()), index=0)
            with col2:
                end_year = st.selectbox("End Year", options=sorted(df['year'].unique()), index=len(df['year'].unique())-1)

            # Filter data
            filtered_df = df[(df['year'] >= start_year) & (df['year'] <= end_year)]

            st.info(f"Showing {len(filtered_df)} quarters from {start_year} to {end_year}")

            st.markdown("---")

            # Main charts
            st.markdown("### 📊 Sales and Supply Trends")

            tab1, tab2, tab3, tab4 = st.tabs([
                "Units (U)",
                "Area (L²)",
                "Absorption Rate",
                "YoY Growth"
            ])

            with tab1:
                st.plotly_chart(
                    self.create_sales_supply_chart(filtered_df),
                    use_container_width=True
                )

            with tab2:
                st.plotly_chart(
                    self.create_area_chart(filtered_df),
                    use_container_width=True
                )

            with tab3:
                # Calculate absorption rate
                absorption_df = pd.DataFrame(
                    quarterly_market_service.calculate_absorption_rate_trend()
                )
                filtered_absorption = absorption_df[
                    absorption_df['quarter'].isin(filtered_df['quarter'])
                ]
                st.plotly_chart(
                    self.create_absorption_rate_chart(filtered_absorption),
                    use_container_width=True
                )

            with tab4:
                metric_choice = st.selectbox(
                    "Select Metric for YoY Growth",
                    options=[
                        ('Sales Units', 'sales_units'),
                        ('Sales Area', 'sales_area_mn_sqft'),
                        ('Supply Units', 'supply_units'),
                        ('Supply Area', 'supply_area_mn_sqft')
                    ],
                    format_func=lambda x: x[0]
                )

                yoy_data = quarterly_market_service.calculate_yoy_growth(metric_choice[1])
                yoy_df = pd.DataFrame(yoy_data)
                filtered_yoy = yoy_df[yoy_df['quarter'].isin(filtered_df['quarter'])]

                if not filtered_yoy.empty:
                    st.plotly_chart(
                        self.create_yoy_growth_chart(filtered_yoy, metric_choice[0]),
                        use_container_width=True
                    )
                else:
                    st.info("Not enough data for YoY comparison in selected range")

            st.markdown("---")

            # Quarter selector for Layer 0 dimensions
            st.markdown("### 🔬 Explore Layer 0 Dimensions")
            selected_quarter = st.selectbox(
                "Select Quarter to View Dimensional Breakdown",
                options=filtered_df['quarter'].tolist(),
                index=len(filtered_df)-1  # Default to most recent
            )

            quarter_data = filtered_df[filtered_df['quarter'] == selected_quarter].iloc[0].to_dict()
            self.render_layer0_dimensions(quarter_data)

            st.markdown("---")

            # Raw data table
            with st.expander("📋 View Raw Data Table"):
                st.dataframe(
                    filtered_df[[
                        'quarter', 'year', 'quarter_num',
                        'sales_units', 'sales_area_mn_sqft',
                        'supply_units', 'supply_area_mn_sqft'
                    ]],
                    use_container_width=True
                )

        except Exception as e:
            st.error(f"Error rendering quarterly market panel: {e}")
            import traceback
            st.code(traceback.format_exc())


# Convenience function for direct import
def render_quarterly_market_panel():
    """Render the quarterly market panel"""
    panel = QuarterlyMarketPanel()
    panel.render()
