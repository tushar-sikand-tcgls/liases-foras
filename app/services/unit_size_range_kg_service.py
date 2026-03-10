"""
Unit Size Range Knowledge Graph Service
Pillar 2: Product Performance - Unit Size Range Analysis

Each Size Range is a first-class node with:
- Layer 0: Raw dimensions (Annual Sales Units/Area, Supply Units/Area, Stock, etc.)
- Layer 1: Derived metrics (Absorption Rate, Avg Unit Size, Inventory Turnover, etc.)
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.config import settings


class SizeRangeNode:
    """
    Size Range as a first-class knowledge graph node

    Layer 0 Dimensions:
    - annual_sales_units (U): Annual sales units count
    - annual_sales_area_lakh_sqft (L²): Annual sales area in lakh sq ft
    - total_supply_units (U): Total supply units count
    - total_supply_area_lakh_sqft (L²): Total supply area in lakh sq ft
    - unsold_units (U): Unsold inventory units
    - total_stock_units (U): Total stock units
    - product_efficiency_pct (%): Product efficiency percentage

    Layer 1 Derived Metrics (calculated):
    - absorption_rate: (Annual Sales / Total Supply) * 100
    - avg_sales_unit_size_sqft: (Sales Area Lakh * 100000) / Sales Units
    - avg_supply_unit_size_sqft: (Supply Area Lakh * 100000) / Supply Units
    - inventory_turnover: Annual Market Absorption / Total Stock
    - unsold_ratio: (Unsold Units / Total Stock) * 100
    """

    def __init__(self, data: Dict[str, Any]):
        # Metadata
        self.size_range_id = data.get('size_range_id')
        self.saleable_size_range = data.get('saleable_size_range')
        self.size_min_sqft = data.get('size_min_sqft', 0)
        self.size_max_sqft = data.get('size_max_sqft', 0)
        self.flat_types = data.get('flat_types', [])

        # Layer 0: Raw dimensions
        self.annual_sales_units = data.get('annual_sales_units', 0)
        self.annual_sales_area_lakh_sqft = data.get('annual_sales_area_lakh_sqft', 0)
        self.total_supply_units = data.get('total_supply_units', 0)
        self.total_supply_area_lakh_sqft = data.get('total_supply_area_lakh_sqft', 0)
        self.unsold_units = data.get('unsold_units', 0)
        self.unsold_area_lakh_sqft = data.get('unsold_area_lakh_sqft', 0)
        self.total_stock_units = data.get('total_stock_units', 0)
        self.total_stock_area_lakh_sqft = data.get('total_stock_area_lakh_sqft', 0)
        self.annual_market_absorption_units = data.get('annual_market_absorption_units', 0)
        self.quarterly_units = data.get('quarterly_units', 0)
        self.monthly_units = data.get('monthly_units', 0)
        self.product_efficiency_pct = data.get('product_efficiency_pct', 0)

        # Layer 1: Derived metrics (calculated)
        self.absorption_rate = None
        self.avg_sales_unit_size_sqft = None
        self.avg_supply_unit_size_sqft = None
        self.inventory_turnover = None
        self.unsold_ratio = None

        # Calculate Layer 1 metrics
        self._calculate_layer1_metrics()

    def _calculate_layer1_metrics(self):
        """Calculate Layer 1 derived metrics from Layer 0 dimensions"""

        # Absorption Rate = (Annual Sales / Total Supply) * 100
        if self.total_supply_units > 0:
            self.absorption_rate = (self.annual_sales_units / self.total_supply_units) * 100

        # Average Sales Unit Size
        if self.annual_sales_units > 0:
            self.avg_sales_unit_size_sqft = (self.annual_sales_area_lakh_sqft * 100000) / self.annual_sales_units

        # Average Supply Unit Size
        if self.total_supply_units > 0:
            self.avg_supply_unit_size_sqft = (self.total_supply_area_lakh_sqft * 100000) / self.total_supply_units

        # Inventory Turnover = Annual Market Absorption / Total Stock
        if self.total_stock_units > 0:
            self.inventory_turnover = self.annual_market_absorption_units / self.total_stock_units

        # Unsold Ratio = (Unsold / Total Stock) * 100
        if self.total_stock_units > 0:
            self.unsold_ratio = (self.unsold_units / self.total_stock_units) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with Layer 0 + Layer 1 structure"""
        return {
            # Metadata
            "size_range_id": self.size_range_id,
            "saleable_size_range": self.saleable_size_range,
            "size_min_sqft": self.size_min_sqft,
            "size_max_sqft": self.size_max_sqft,
            "flat_types": self.flat_types,

            # Layer 0: Raw Dimensions
            "layer0": {
                "annual_sales_units": {"value": self.annual_sales_units, "unit": "Units", "dimension": "U"},
                "annual_sales_area": {"value": self.annual_sales_area_lakh_sqft, "unit": "Lakh sq ft", "dimension": "L²"},
                "total_supply_units": {"value": self.total_supply_units, "unit": "Units", "dimension": "U"},
                "total_supply_area": {"value": self.total_supply_area_lakh_sqft, "unit": "Lakh sq ft", "dimension": "L²"},
                "unsold_units": {"value": self.unsold_units, "unit": "Units", "dimension": "U"},
                "unsold_area": {"value": self.unsold_area_lakh_sqft, "unit": "Lakh sq ft", "dimension": "L²"},
                "total_stock_units": {"value": self.total_stock_units, "unit": "Units", "dimension": "U"},
                "total_stock_area": {"value": self.total_stock_area_lakh_sqft, "unit": "Lakh sq ft", "dimension": "L²"},
                "annual_market_absorption": {"value": self.annual_market_absorption_units, "unit": "Units", "dimension": "U"},
                "product_efficiency": {"value": self.product_efficiency_pct, "unit": "%", "dimension": "Dimensionless"}
            },

            # Layer 1: Derived Metrics
            "layer1": {
                "absorption_rate": {
                    "value": round(self.absorption_rate, 2) if self.absorption_rate else None,
                    "unit": "%",
                    "formula": "(Annual Sales Units / Total Supply Units) * 100"
                },
                "avg_sales_unit_size": {
                    "value": round(self.avg_sales_unit_size_sqft, 0) if self.avg_sales_unit_size_sqft else None,
                    "unit": "sq ft",
                    "formula": "(Annual Sales Area Lakh * 100000) / Annual Sales Units"
                },
                "avg_supply_unit_size": {
                    "value": round(self.avg_supply_unit_size_sqft, 0) if self.avg_supply_unit_size_sqft else None,
                    "unit": "sq ft",
                    "formula": "(Total Supply Area Lakh * 100000) / Total Supply Units"
                },
                "inventory_turnover": {
                    "value": round(self.inventory_turnover, 3) if self.inventory_turnover else None,
                    "unit": "ratio",
                    "formula": "Annual Market Absorption / Total Stock Units"
                },
                "unsold_ratio": {
                    "value": round(self.unsold_ratio, 2) if self.unsold_ratio else None,
                    "unit": "%",
                    "formula": "(Unsold Units / Total Stock Units) * 100"
                }
            }
        }


class UnitSizeRangeKGService:
    """
    Unit Size Range Knowledge Graph Service

    Manages size ranges as first-class KG nodes with:
    - Layer 0 raw dimensions
    - Layer 1 derived metrics
    - Product performance analysis
    """

    def __init__(self):
        self.size_ranges: List[SizeRangeNode] = []
        self.metadata: Dict[str, Any] = {}
        self._load_data()

    def _load_data(self):
        """Load unit size range data and create SizeRangeNode instances"""
        data_file = Path(settings.DATA_PATH) / "extracted" / "unit_size_range_analysis.json"

        if not data_file.exists():
            print(f"Warning: {data_file} not found")
            return

        with open(data_file, 'r', encoding='utf-8') as f:
            full_data = json.load(f)

        self.metadata = full_data.get('metadata', {})
        raw_data = full_data.get('data', [])

        # Create SizeRangeNode for each size range
        self.size_ranges = [SizeRangeNode(sr) for sr in raw_data]

        print(f"✓ Unit Size Range KG: {len(self.size_ranges)} size range nodes loaded")
        location_info = self.metadata.get('location', {})
        print(f"  Location: {location_info.get('region')}, {location_info.get('city')}")

    def get_size_range_by_id(self, size_range_id: str) -> Optional[SizeRangeNode]:
        """Get a specific size range by ID"""
        for sr in self.size_ranges:
            if sr.size_range_id == size_range_id:
                return sr
        return None

    def get_size_ranges_by_flat_type(self, flat_type: str) -> List[SizeRangeNode]:
        """Get all size ranges that include a specific flat type"""
        return [sr for sr in self.size_ranges if flat_type in sr.flat_types]

    def get_size_ranges_by_sqft_range(self, min_sqft: int, max_sqft: int) -> List[SizeRangeNode]:
        """Get size ranges that overlap with a given sqft range"""
        results = []
        for sr in self.size_ranges:
            # Check if ranges overlap
            if not (sr.size_max_sqft < min_sqft or sr.size_min_sqft > max_sqft):
                results.append(sr)
        return results

    def get_top_performing_ranges(self, metric: str = "absorption_rate", n: int = 5) -> List[SizeRangeNode]:
        """
        Get top N performing size ranges by a specific metric

        Args:
            metric: Metric to sort by (absorption_rate, product_efficiency_pct, inventory_turnover)
            n: Number of top ranges to return

        Returns:
            List of top performing size ranges
        """
        if metric == "absorption_rate":
            sorted_ranges = sorted(
                [sr for sr in self.size_ranges if sr.absorption_rate is not None],
                key=lambda x: x.absorption_rate,
                reverse=True
            )
        elif metric == "product_efficiency_pct":
            sorted_ranges = sorted(
                self.size_ranges,
                key=lambda x: x.product_efficiency_pct,
                reverse=True
            )
        elif metric == "inventory_turnover":
            sorted_ranges = sorted(
                [sr for sr in self.size_ranges if sr.inventory_turnover is not None],
                key=lambda x: x.inventory_turnover,
                reverse=True
            )
        else:
            sorted_ranges = self.size_ranges

        return sorted_ranges[:n]

    def get_all_size_ranges(self) -> List[SizeRangeNode]:
        """Get all size ranges"""
        return self.size_ranges

    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about the size range data"""
        return self.metadata

    def query_size_ranges(self, filters: Dict[str, Any]) -> List[SizeRangeNode]:
        """
        Query size ranges with flexible filters

        Examples:
        - {"flat_type": "1BHK"} → All ranges with 1BHK units
        - {"min_efficiency": 50} → Ranges with efficiency >= 50%
        - {"min_sales": 100} → Ranges with annual sales >= 100 units
        """
        results = self.size_ranges

        # Filter by flat type
        if "flat_type" in filters:
            flat_type = filters["flat_type"]
            results = [sr for sr in results if flat_type in sr.flat_types]

        # Filter by minimum efficiency
        if "min_efficiency" in filters:
            min_eff = filters["min_efficiency"]
            results = [sr for sr in results if sr.product_efficiency_pct >= min_eff]

        # Filter by minimum sales
        if "min_sales" in filters:
            min_sales = filters["min_sales"]
            results = [sr for sr in results if sr.annual_sales_units >= min_sales]

        # Filter by sqft range
        if "size_range" in filters:
            min_sqft, max_sqft = filters["size_range"]
            results = [sr for sr in results if not (sr.size_max_sqft < min_sqft or sr.size_min_sqft > max_sqft)]

        return results


# Singleton instance
_unit_size_range_kg_service = None

def get_unit_size_range_kg_service() -> UnitSizeRangeKGService:
    """Get singleton instance of UnitSizeRangeKGService"""
    global _unit_size_range_kg_service
    if _unit_size_range_kg_service is None:
        _unit_size_range_kg_service = UnitSizeRangeKGService()
    return _unit_size_range_kg_service
