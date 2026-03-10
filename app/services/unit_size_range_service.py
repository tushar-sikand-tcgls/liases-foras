"""
Unit Size Range Analysis Service

Provides querying and analysis capabilities for unit size ranges across the market,
with Layer 0 (raw data), Layer 1 (derived metrics), and Layer 2 (financial metrics).

Based on Liases Foras Pillar 2: Product Performance
"""

import json
from typing import Dict, List, Optional, Any
from pathlib import Path


class UnitSizeRangeService:
    """Service for analyzing unit size range data with multi-layer derivatives"""

    def __init__(self, data_file: str = "data/extracted/unit_size_range_analysis.json"):
        self.data_file = Path(data_file)
        self.data = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        """Load unit size range data from JSON file"""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  Unit size range data file not found: {self.data_file}")
            return {"data": [], "metadata": {}}

    def get_all_size_ranges(self) -> List[Dict[str, Any]]:
        """Get all size ranges with Layer 0 data"""
        return self.data.get("data", [])

    def get_size_range_by_id(self, range_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific size range by ID

        Args:
            range_id: Size range ID (e.g., "range_550_600")

        Returns:
            Size range data with all layers, or None if not found
        """
        for size_range in self.get_all_size_ranges():
            if size_range.get("size_range_id") == range_id:
                return self._enrich_with_derivatives(size_range)
        return None

    def get_size_ranges_by_flat_type(self, flat_type: str) -> List[Dict[str, Any]]:
        """Get all size ranges for a specific flat type (1BHK, 2BHK, etc.)

        Args:
            flat_type: Flat type to filter by

        Returns:
            List of size ranges matching the flat type
        """
        results = []
        for size_range in self.get_all_size_ranges():
            if flat_type in size_range.get("flat_types", []):
                results.append(self._enrich_with_derivatives(size_range))
        return results

    def get_size_range_by_sqft(self, sqft: int) -> Optional[Dict[str, Any]]:
        """Get the size range that contains a specific square footage

        Args:
            sqft: Square footage value

        Returns:
            Size range data, or None if not found
        """
        for size_range in self.get_all_size_ranges():
            min_sqft = size_range.get("size_min_sqft", 0)
            max_sqft = size_range.get("size_max_sqft", float('inf'))

            if min_sqft <= sqft <= max_sqft:
                return self._enrich_with_derivatives(size_range)
        return None

    def _enrich_with_derivatives(self, size_range: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich size range data with Layer 1 and Layer 2 derivatives

        Args:
            size_range: Raw size range data (Layer 0)

        Returns:
            Size range with Layer 1 and Layer 2 calculations
        """
        enriched = size_range.copy()

        # Add Layer 1 derivatives
        enriched["layer1_derivatives"] = self._calculate_layer1(size_range)

        # Add Layer 2 derivatives
        enriched["layer2_derivatives"] = self._calculate_layer2(size_range, enriched["layer1_derivatives"])

        return enriched

    def _calculate_layer1(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate Layer 1 derived metrics

        Layer 1 metrics are simple ratios and rates derived from Layer 0 dimensions.

        Formulas:
        - Absorption Rate = (Annual Sales Units / Total Supply Units) * 100
        - Avg Unit Size (Sales) = (Annual Sales Area * 100000) / Annual Sales Units
        - Avg Unit Size (Supply) = (Total Supply Area * 100000) / Total Supply Units
        - Inventory Turnover = Annual Market Absorption Units / Total Stock Units
        - Unsold Ratio = (Unsold Units / Total Stock Units) * 100
        - Sales Velocity = Annual Sales Units / 12 (units per month)
        - Supply to Sales Ratio = Total Supply Units / Annual Sales Units

        Args:
            data: Layer 0 data

        Returns:
            Dictionary of Layer 1 metrics
        """
        layer1 = {}

        # Absorption Rate (%)
        annual_sales = data.get("annual_sales_units", 0)
        total_supply = data.get("total_supply_units", 1)  # Avoid division by zero
        if total_supply > 0 and annual_sales > 0:
            layer1["absorption_rate_pct"] = round((annual_sales / total_supply) * 100, 2)
        else:
            layer1["absorption_rate_pct"] = 0

        # Average Unit Size for Sales (sqft)
        sales_area_lakh = data.get("annual_sales_area_lakh_sqft", 0)
        if annual_sales > 0:
            layer1["avg_unit_size_sales_sqft"] = round((sales_area_lakh * 100000) / annual_sales, 2)
        else:
            layer1["avg_unit_size_sales_sqft"] = 0

        # Average Unit Size for Supply (sqft)
        supply_area_lakh = data.get("total_supply_area_lakh_sqft", 0)
        if total_supply > 0:
            layer1["avg_unit_size_supply_sqft"] = round((supply_area_lakh * 100000) / total_supply, 2)
        else:
            layer1["avg_unit_size_supply_sqft"] = 0

        # Inventory Turnover (ratio)
        market_absorption = data.get("annual_market_absorption_units", 0)
        total_stock = data.get("total_stock_units", 1)
        if total_stock > 0:
            layer1["inventory_turnover_ratio"] = round(market_absorption / total_stock, 4)
        else:
            layer1["inventory_turnover_ratio"] = 0

        # Unsold Ratio (%)
        unsold_units = data.get("unsold_units", 0)
        if total_stock > 0:
            layer1["unsold_ratio_pct"] = round((unsold_units / total_stock) * 100, 2)
        else:
            layer1["unsold_ratio_pct"] = 0

        # Sales Velocity (units per month)
        layer1["sales_velocity_units_per_month"] = round(annual_sales / 12, 2)

        # Supply to Sales Ratio
        if annual_sales > 0:
            layer1["supply_to_sales_ratio"] = round(total_supply / annual_sales, 2)
        else:
            layer1["supply_to_sales_ratio"] = 0

        # Area Efficiency (sales area vs supply area)
        supply_area = data.get("total_supply_area_lakh_sqft", 1)
        if supply_area > 0:
            layer1["area_efficiency_pct"] = round((sales_area_lakh / supply_area) * 100, 2)
        else:
            layer1["area_efficiency_pct"] = 0

        # Quarterly Sales Rate (units)
        quarterly_units = data.get("quarterly_units", 0)
        layer1["quarterly_sales_rate"] = quarterly_units

        # Market Share by Units (compared to total market)
        total_market_stock = self.data.get("summary_statistics", {}).get("total_stock_units", 1)
        if total_market_stock > 0:
            layer1["market_share_by_units_pct"] = round((total_stock / total_market_stock) * 100, 2)
        else:
            layer1["market_share_by_units_pct"] = 0

        return layer1

    def _calculate_layer2(self, data: Dict[str, Any], layer1: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate Layer 2 financial metrics

        Layer 2 metrics are complex aggregations requiring Layer 1 dependencies.

        Formulas:
        - Estimated Revenue = Annual Sales Units * Monthly Price (from data)
        - Revenue Per Sqft = Estimated Revenue / Annual Sales Area
        - Market Capitalization = Total Stock Units * Monthly Price
        - Months of Inventory = Total Stock Units / Sales Velocity
        - Sellout Velocity = (Annual Sales Units / Total Stock Units) * 100
        - Price to Area Ratio = Monthly Price / Avg Unit Size

        Args:
            data: Layer 0 data
            layer1: Layer 1 derived metrics

        Returns:
            Dictionary of Layer 2 financial metrics
        """
        layer2 = {}

        # Get price data (stored in "monthly_units" field - appears to be price data based on context)
        monthly_price = data.get("monthly_units", 0)  # This seems to be avg price per unit

        # Estimated Annual Revenue (INR)
        annual_sales = data.get("annual_sales_units", 0)
        layer2["estimated_annual_revenue_inr"] = annual_sales * monthly_price

        # Revenue Per Sqft
        sales_area_sqft = data.get("annual_sales_area_lakh_sqft", 0) * 100000
        if sales_area_sqft > 0:
            layer2["revenue_per_sqft_inr"] = round(layer2["estimated_annual_revenue_inr"] / sales_area_sqft, 2)
        else:
            layer2["revenue_per_sqft_inr"] = 0

        # Market Capitalization (Total value of all stock)
        total_stock = data.get("total_stock_units", 0)
        layer2["market_capitalization_inr"] = total_stock * monthly_price

        # Months of Inventory
        sales_velocity = layer1.get("sales_velocity_units_per_month", 0)
        if sales_velocity > 0:
            layer2["months_of_inventory"] = round(total_stock / sales_velocity, 2)
        else:
            layer2["months_of_inventory"] = 0

        # Sellout Velocity (%)
        if total_stock > 0:
            layer2["sellout_velocity_pct"] = round((annual_sales / total_stock) * 100, 2)
        else:
            layer2["sellout_velocity_pct"] = 0

        # Price to Area Ratio (INR per sqft)
        avg_unit_size = layer1.get("avg_unit_size_sales_sqft", 1)
        if avg_unit_size > 0:
            layer2["price_to_area_ratio_inr_per_sqft"] = round(monthly_price / avg_unit_size, 2)
        else:
            layer2["price_to_area_ratio_inr_per_sqft"] = 0

        # Unsold Inventory Value (INR)
        unsold_units = data.get("unsold_units", 0)
        layer2["unsold_inventory_value_inr"] = unsold_units * monthly_price

        # Annual Marketable Supply Value (INR)
        annual_market_absorption = data.get("annual_market_absorption_units", 0)
        layer2["annual_marketable_supply_value_inr"] = annual_market_absorption * monthly_price

        # Product Efficiency Score (from Layer 0)
        layer2["product_efficiency_pct"] = data.get("product_efficiency_pct", 0)

        # Investment Concentration Score (higher = more capital locked in this range)
        total_market_cap = sum([
            sr.get("total_stock_units", 0) * sr.get("monthly_units", 0)
            for sr in self.get_all_size_ranges()
        ])
        if total_market_cap > 0:
            layer2["investment_concentration_pct"] = round((layer2["market_capitalization_inr"] / total_market_cap) * 100, 2)
        else:
            layer2["investment_concentration_pct"] = 0

        return layer2

    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get market summary statistics across all size ranges"""
        return self.data.get("summary_statistics", {})

    def get_top_performing_ranges(self, metric: str = "product_efficiency_pct", top_n: int = 5) -> List[Dict[str, Any]]:
        """Get top performing size ranges by a specific metric

        Args:
            metric: Metric to sort by (default: product_efficiency_pct)
            top_n: Number of top ranges to return

        Returns:
            List of top performing size ranges
        """
        all_ranges = [self._enrich_with_derivatives(sr) for sr in self.get_all_size_ranges()]

        # Sort by the metric
        sorted_ranges = sorted(
            all_ranges,
            key=lambda x: x.get(metric, x.get("layer1_derivatives", {}).get(metric, x.get("layer2_derivatives", {}).get(metric, 0))),
            reverse=True
        )

        return sorted_ranges[:top_n]

    def compare_size_ranges(self, range_ids: List[str]) -> Dict[str, Any]:
        """Compare multiple size ranges across all metrics

        Args:
            range_ids: List of size range IDs to compare

        Returns:
            Comparison data with all metrics for each range
        """
        comparison = {
            "ranges": [],
            "comparison_summary": {}
        }

        for range_id in range_ids:
            range_data = self.get_size_range_by_id(range_id)
            if range_data:
                comparison["ranges"].append(range_data)

        # Add comparison insights
        if len(comparison["ranges"]) > 1:
            comparison["comparison_summary"] = self._generate_comparison_insights(comparison["ranges"])

        return comparison

    def _generate_comparison_insights(self, ranges: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate insights from comparing multiple ranges

        Args:
            ranges: List of enriched size range data

        Returns:
            Comparison insights
        """
        insights = {}

        # Find best and worst performers
        insights["highest_sales"] = max(ranges, key=lambda x: x.get("annual_sales_units", 0))["saleable_size_range"]
        insights["highest_efficiency"] = max(ranges, key=lambda x: x.get("product_efficiency_pct", 0))["saleable_size_range"]
        insights["highest_absorption"] = max(ranges, key=lambda x: x.get("layer1_derivatives", {}).get("absorption_rate_pct", 0))["saleable_size_range"]

        # Calculate average metrics across compared ranges
        total_sales = sum([r.get("annual_sales_units", 0) for r in ranges])
        total_supply = sum([r.get("total_supply_units", 0) for r in ranges])
        avg_efficiency = sum([r.get("product_efficiency_pct", 0) for r in ranges]) / len(ranges)

        insights["total_sales_units"] = total_sales
        insights["total_supply_units"] = total_supply
        insights["average_efficiency_pct"] = round(avg_efficiency, 2)

        return insights


# Global instance
_unit_size_service = None

def get_unit_size_service() -> UnitSizeRangeService:
    """Get or create the global UnitSizeRangeService instance"""
    global _unit_size_service
    if _unit_size_service is None:
        _unit_size_service = UnitSizeRangeService()
    return _unit_size_service
