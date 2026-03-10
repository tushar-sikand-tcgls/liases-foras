"""
Unit Ticket Size Analysis Service

Provides querying and analysis capabilities for unit ticket size ranges (price-based segmentation),
with Layer 0 (raw data), Layer 1 (derived metrics), and Layer 2 (financial metrics).

Based on Liases Foras Pillar 2: Product Performance - Unit Ticket Size Analysis
"""

import json
from typing import Dict, List, Optional, Any
from pathlib import Path


class UnitTicketSizeService:
    """Service for analyzing unit ticket size (price range) data with multi-layer derivatives"""

    def __init__(self, data_file: str = "data/extracted/unit_ticket_size_analysis.json"):
        self.data_file = Path(data_file)
        self.data = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        """Load unit ticket size data from JSON file"""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  Unit ticket size data file not found: {self.data_file}")
            return {"data": [], "metadata": {}}

    def get_all_ticket_ranges(self) -> List[Dict[str, Any]]:
        """Get all ticket size ranges with Layer 0 data"""
        return self.data.get("data", [])

    def get_ticket_range_by_id(self, range_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific ticket range by ID

        Args:
            range_id: Ticket range ID (e.g., "ticket_10_20")

        Returns:
            Ticket range data with all layers, or None if not found
        """
        for ticket_range in self.get_all_ticket_ranges():
            if ticket_range.get("ticket_range_id") == range_id:
                return self._enrich_with_derivatives(ticket_range)
        return None

    def get_ticket_range_by_price(self, price_lacs: float) -> Optional[Dict[str, Any]]:
        """Get the ticket range that contains a specific price point

        Args:
            price_lacs: Price in INR Lakhs

        Returns:
            Ticket range data, or None if not found
        """
        for ticket_range in self.get_all_ticket_ranges():
            min_lacs = ticket_range.get("ticket_min_lacs", 0)
            max_lacs = ticket_range.get("ticket_max_lacs", float('inf'))

            if min_lacs <= price_lacs <= max_lacs:
                return self._enrich_with_derivatives(ticket_range)
        return None

    def _enrich_with_derivatives(self, ticket_range: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich ticket range data with Layer 1 and Layer 2 derivatives

        Args:
            ticket_range: Raw ticket range data (Layer 0)

        Returns:
            Ticket range with Layer 1 and Layer 2 calculations
        """
        enriched = ticket_range.copy()

        # Add Layer 1 derivatives
        enriched["layer1_derivatives"] = self._calculate_layer1(ticket_range)

        # Add Layer 2 derivatives
        enriched["layer2_derivatives"] = self._calculate_layer2(ticket_range, enriched["layer1_derivatives"])

        return enriched

    def _calculate_layer1(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate Layer 1 derived metrics for price-based analysis

        Layer 1 metrics are simple ratios and rates derived from Layer 0 dimensions.

        Formulas:
        - Value Absorption Rate = (Annual Sales Value % / Total Supply Value %) * 100
        - Unit Absorption Rate = (Annual Sales Units / Total Supply Units) * 100
        - Value to Unit Ratio = Annual Sales Value % / Annual Sales Units %
        - Unsold Value Concentration = (Unsold Value % / Total Supply Value %) * 100
        - Marketability Index = (Annual Marketable Supply Units / Total Supply Units) * 100
        - Price Premium Index = Wt Avg Saleable PSF / Market Avg PSF
        - Inventory Efficiency = 1 / Annual Months Inventory (when > 0)

        Args:
            data: Layer 0 data

        Returns:
            Dictionary of Layer 1 metrics
        """
        layer1 = {}

        # Value Absorption Rate (%)
        annual_sales_value_pct = data.get("annual_sales_value_pct", 0)
        total_supply_value_pct = data.get("total_supply_value_pct", 1)
        if total_supply_value_pct > 0 and annual_sales_value_pct > 0:
            layer1["value_absorption_rate_pct"] = round((annual_sales_value_pct / total_supply_value_pct) * 100, 2)
        else:
            layer1["value_absorption_rate_pct"] = 0

        # Unit Absorption Rate (%)
        annual_sales_units = data.get("annual_sales_units", 0)
        total_supply_units = data.get("total_supply_units", 1)
        if total_supply_units > 0 and annual_sales_units > 0:
            layer1["unit_absorption_rate_pct"] = round((annual_sales_units / total_supply_units) * 100, 2)
        else:
            layer1["unit_absorption_rate_pct"] = 0

        # Value to Unit Ratio (how much value per unit of sales)
        annual_sales_units_nonzero = annual_sales_units if annual_sales_units > 0 else 1
        if annual_sales_value_pct > 0:
            layer1["value_to_unit_ratio"] = round(annual_sales_value_pct / annual_sales_units_nonzero, 4)
        else:
            layer1["value_to_unit_ratio"] = 0

        # Unsold Value Concentration (%)
        unsold_value_pct = data.get("unsold_value_pct", 0)
        if total_supply_value_pct > 0:
            layer1["unsold_value_concentration_pct"] = round((unsold_value_pct / total_supply_value_pct) * 100, 2)
        else:
            layer1["unsold_value_concentration_pct"] = 0

        # Marketability Index (%)
        annual_marketable_supply_units = data.get("annual_marketable_supply_units", 0)
        if total_supply_units > 0:
            layer1["marketability_index_pct"] = round((annual_marketable_supply_units / total_supply_units) * 100, 2)
        else:
            layer1["marketability_index_pct"] = 0

        # Price Premium Index (compared to market average)
        wt_avg_saleable_psf = data.get("wt_avg_saleable_area_price_psf", 0)
        market_avg_psf = self.data.get("summary_statistics", {}).get("price_range_spread", {}).get("min_psf_saleable", 2812)
        if market_avg_psf > 0 and wt_avg_saleable_psf > 0:
            layer1["price_premium_index"] = round(wt_avg_saleable_psf / market_avg_psf, 2)
        else:
            layer1["price_premium_index"] = 1.0

        # Inventory Efficiency (inverse of months inventory)
        annual_months_inventory = data.get("annual_months_inventory", 0)
        if annual_months_inventory > 0:
            layer1["inventory_efficiency_ratio"] = round(1 / annual_months_inventory, 4)
        else:
            layer1["inventory_efficiency_ratio"] = 0

        # Sales Velocity (quarterly to monthly conversion)
        quarterly_marketable_supply_units = data.get("quarterly_marketable_supply_units", 0)
        layer1["monthly_sales_velocity_units"] = round(quarterly_marketable_supply_units / 3, 2)

        # Supply to Sales Ratio
        if annual_sales_units > 0:
            layer1["supply_to_sales_ratio"] = round(total_supply_units / annual_sales_units, 2)
        else:
            layer1["supply_to_sales_ratio"] = 0

        # Market Share by Value (compared to total market)
        total_market_supply_value = sum([
            tr.get("total_supply_value_pct", 0)
            for tr in self.get_all_ticket_ranges()
        ])
        if total_market_supply_value > 0:
            layer1["market_share_by_value_pct"] = round((total_supply_value_pct / total_market_supply_value) * 100, 2)
        else:
            layer1["market_share_by_value_pct"] = 0

        return layer1

    def _calculate_layer2(self, data: Dict[str, Any], layer1: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate Layer 2 financial metrics for ticket size analysis

        Layer 2 metrics are complex aggregations requiring Layer 1 dependencies.

        Formulas:
        - Estimated Annual Sales Value = Annual Sales Units * Avg Price (derived from PSF)
        - Revenue Concentration = (Sales Value % / Total Market Sales Value %) * 100
        - Unsold Inventory Value = Unsold Units * Avg Price
        - Market Capitalization = Total Supply Units * Avg Price
        - Affordability Score = (Ticket Range Midpoint / Market Avg Income) * 100
        - Sellout Time = Annual Months Inventory (from Layer 0)
        - Price Efficiency = Product Efficiency % * Price Premium Index

        Args:
            data: Layer 0 data
            layer1: Layer 1 derived metrics

        Returns:
            Dictionary of Layer 2 financial metrics
        """
        layer2 = {}

        # Estimate average price per unit from PSF
        wt_avg_saleable_psf = data.get("wt_avg_saleable_area_price_psf", 0)
        # Assume average unit size based on ticket range midpoint
        ticket_min = data.get("ticket_min_lacs", 0)
        ticket_max = data.get("ticket_max_lacs", 0)
        ticket_midpoint_lacs = (ticket_min + ticket_max) / 2 if ticket_max > 0 else ticket_min

        # Estimated unit size (sqft) = Price (lacs) / PSF (in appropriate units)
        if wt_avg_saleable_psf > 0:
            estimated_unit_size_sqft = (ticket_midpoint_lacs * 100000) / wt_avg_saleable_psf
        else:
            estimated_unit_size_sqft = 0

        layer2["estimated_avg_unit_size_sqft"] = round(estimated_unit_size_sqft, 2)

        # Estimated Annual Sales Value (INR Lakhs)
        annual_sales_units = data.get("annual_sales_units", 0)
        layer2["estimated_annual_sales_value_lacs"] = round(annual_sales_units * ticket_midpoint_lacs, 2)

        # Revenue Concentration (how much of total market revenue this range represents)
        annual_sales_value_pct = data.get("annual_sales_value_pct", 0)
        total_market_sales_value = sum([
            tr.get("annual_sales_value_pct", 0)
            for tr in self.get_all_ticket_ranges()
        ])
        if total_market_sales_value > 0:
            layer2["revenue_concentration_pct"] = round((annual_sales_value_pct / total_market_sales_value) * 100, 2)
        else:
            layer2["revenue_concentration_pct"] = 0

        # Unsold Inventory Value (INR Lakhs)
        unsold_units = data.get("unsold_units", 0)
        layer2["unsold_inventory_value_lacs"] = round(unsold_units * ticket_midpoint_lacs, 2)

        # Market Capitalization (Total value of all supply in this range)
        total_supply_units = data.get("total_supply_units", 0)
        layer2["market_capitalization_lacs"] = round(total_supply_units * ticket_midpoint_lacs, 2)

        # Affordability Score (assuming market avg income of 15 Lacs/year in Chakan)
        market_avg_income_lacs = 15.0  # Assumption for Chakan, Pune
        layer2["affordability_score"] = round((ticket_midpoint_lacs / market_avg_income_lacs) * 100, 2)

        # Sellout Time (directly from Layer 0)
        layer2["annual_months_inventory"] = data.get("annual_months_inventory", 0)
        layer2["quarterly_months_inventory"] = data.get("quarterly_months_inventory", 0)

        # Price Efficiency (combining product efficiency with price premium)
        product_efficiency_pct = data.get("product_efficiency_pct", 0)
        price_premium_index = layer1.get("price_premium_index", 1.0)
        layer2["price_efficiency_score"] = round(product_efficiency_pct * price_premium_index, 2)

        # Marketable Supply Value (INR Lakhs)
        annual_marketable_supply_units = data.get("annual_marketable_supply_units", 0)
        layer2["annual_marketable_supply_value_lacs"] = round(annual_marketable_supply_units * ticket_midpoint_lacs, 2)

        quarterly_marketable_supply_units = data.get("quarterly_marketable_supply_units", 0)
        layer2["quarterly_marketable_supply_value_lacs"] = round(quarterly_marketable_supply_units * ticket_midpoint_lacs, 2)

        # Investment Concentration (how much capital is locked in this price range)
        total_market_cap = sum([
            tr.get("total_supply_units", 0) * ((tr.get("ticket_min_lacs", 0) + tr.get("ticket_max_lacs", 0)) / 2 if tr.get("ticket_max_lacs", 0) > 0 else tr.get("ticket_min_lacs", 0))
            for tr in self.get_all_ticket_ranges()
        ])
        if total_market_cap > 0:
            layer2["investment_concentration_pct"] = round((layer2["market_capitalization_lacs"] / total_market_cap) * 100, 2)
        else:
            layer2["investment_concentration_pct"] = 0

        return layer2

    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get market summary statistics across all ticket size ranges"""
        return self.data.get("summary_statistics", {})

    def get_top_performing_ranges(self, metric: str = "product_efficiency_pct", top_n: int = 5) -> List[Dict[str, Any]]:
        """Get top performing ticket ranges by a specific metric

        Args:
            metric: Metric to sort by (default: product_efficiency_pct)
            top_n: Number of top ranges to return

        Returns:
            List of top performing ticket ranges
        """
        all_ranges = [self._enrich_with_derivatives(tr) for tr in self.get_all_ticket_ranges()]

        # Sort by the metric
        sorted_ranges = sorted(
            all_ranges,
            key=lambda x: x.get(metric, x.get("layer1_derivatives", {}).get(metric, x.get("layer2_derivatives", {}).get(metric, 0))),
            reverse=True
        )

        return sorted_ranges[:top_n]

    def compare_ticket_ranges(self, range_ids: List[str]) -> Dict[str, Any]:
        """Compare multiple ticket ranges across all metrics

        Args:
            range_ids: List of ticket range IDs to compare

        Returns:
            Comparison data with all metrics for each range
        """
        comparison = {
            "ranges": [],
            "comparison_summary": {}
        }

        for range_id in range_ids:
            range_data = self.get_ticket_range_by_id(range_id)
            if range_data:
                comparison["ranges"].append(range_data)

        # Add comparison insights
        if len(comparison["ranges"]) > 1:
            comparison["comparison_summary"] = self._generate_comparison_insights(comparison["ranges"])

        return comparison

    def _generate_comparison_insights(self, ranges: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate insights from comparing multiple ranges

        Args:
            ranges: List of enriched ticket range data

        Returns:
            Comparison insights
        """
        insights = {}

        # Find best and worst performers
        insights["highest_sales_units"] = max(ranges, key=lambda x: x.get("annual_sales_units", 0))["ticket_size_range"]
        insights["highest_sales_value"] = max(ranges, key=lambda x: x.get("annual_sales_value_pct", 0))["ticket_size_range"]
        insights["highest_efficiency"] = max(ranges, key=lambda x: x.get("product_efficiency_pct", 0))["ticket_size_range"]
        insights["highest_value_absorption"] = max(ranges, key=lambda x: x.get("layer1_derivatives", {}).get("value_absorption_rate_pct", 0))["ticket_size_range"]

        # Calculate average metrics across compared ranges
        total_sales_units = sum([r.get("annual_sales_units", 0) for r in ranges])
        total_supply_units = sum([r.get("total_supply_units", 0) for r in ranges])
        avg_efficiency = sum([r.get("product_efficiency_pct", 0) for r in ranges]) / len(ranges)
        avg_psf = sum([r.get("wt_avg_saleable_area_price_psf", 0) for r in ranges]) / len(ranges)

        insights["total_sales_units"] = total_sales_units
        insights["total_supply_units"] = total_supply_units
        insights["average_efficiency_pct"] = round(avg_efficiency, 2)
        insights["average_psf"] = round(avg_psf, 2)

        return insights


# Global instance
_unit_ticket_size_service = None

def get_unit_ticket_size_service() -> UnitTicketSizeService:
    """Get or create the global UnitTicketSizeService instance"""
    global _unit_ticket_size_service
    if _unit_ticket_size_service is None:
        _unit_ticket_size_service = UnitTicketSizeService()
    return _unit_ticket_size_service
