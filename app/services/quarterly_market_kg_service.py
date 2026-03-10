"""
Quarterly Market Knowledge Graph Service
Layer 0 + Layer 1 dimensional data for market trends

Each Quarter is a first-class node (like Projects) with:
- Layer 0: Raw dimensions (U, L², T)
- Layer 1: Derived metrics (Absorption Rate, YoY Growth, QoQ Growth, etc.)
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.config import settings


class QuarterNode:
    """
    Quarter as a first-class knowledge graph node

    Layer 0 Dimensions:
    - sales_units (U): Sales units count
    - sales_area_mn_sqft (L²): Sales area in million sq ft
    - supply_units (U): Supply units count
    - supply_area_mn_sqft (L²): Supply area in million sq ft
    - quarter (T): Time identifier (e.g., "Q1 24-25")

    Layer 1 Derived Metrics (calculated):
    - absorption_rate: (Sales / Supply) * 100
    - sales_avg_unit_size_sqft: (Sales Area * 1M) / Sales Units
    - supply_avg_unit_size_sqft: (Supply Area * 1M) / Supply Units
    - yoy_growth_sales: % change vs same quarter last year
    - yoy_growth_supply: % change vs same quarter last year
    - qoq_growth_sales: % change vs previous quarter
    - qoq_growth_supply: % change vs previous quarter
    """

    def __init__(self, data: Dict[str, Any]):
        # Layer 0: Raw dimensions
        self.quarter_id = data.get('quarter_id')
        self.quarter = data.get('quarter')
        self.year = data.get('year')
        self.quarter_num = data.get('quarter_num')

        # U dimension (Units)
        self.sales_units = data.get('sales_units', 0)
        self.supply_units = data.get('supply_units', 0)

        # L² dimension (Area in million sq ft)
        self.sales_area_mn_sqft = data.get('sales_area_mn_sqft', 0)
        self.supply_area_mn_sqft = data.get('supply_area_mn_sqft', 0)

        # Layer 1: Derived metrics (calculated)
        self.absorption_rate = None
        self.sales_avg_unit_size_sqft = None
        self.supply_avg_unit_size_sqft = None
        self.yoy_growth_sales = None
        self.yoy_growth_supply = None
        self.qoq_growth_sales = None
        self.qoq_growth_supply = None

        # Calculate Layer 1 metrics
        self._calculate_layer1_metrics()

    def _calculate_layer1_metrics(self):
        """Calculate Layer 1 derived metrics from Layer 0 dimensions"""

        # Absorption Rate = (Sales / Supply) * 100
        if self.supply_units > 0:
            self.absorption_rate = (self.sales_units / self.supply_units) * 100

        # Average Unit Size (Sales)
        if self.sales_units > 0:
            self.sales_avg_unit_size_sqft = (self.sales_area_mn_sqft * 1_000_000) / self.sales_units

        # Average Unit Size (Supply)
        if self.supply_units > 0:
            self.supply_avg_unit_size_sqft = (self.supply_area_mn_sqft * 1_000_000) / self.supply_units

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with Layer 0 + Layer 1 structure"""
        return {
            # Metadata
            "quarter_id": self.quarter_id,
            "quarter": self.quarter,
            "year": self.year,
            "quarter_num": self.quarter_num,

            # Layer 0: Raw Dimensions
            "layer0": {
                "sales_units": {"value": self.sales_units, "unit": "Units", "dimension": "U"},
                "sales_area": {"value": self.sales_area_mn_sqft, "unit": "mn sq ft", "dimension": "L²"},
                "supply_units": {"value": self.supply_units, "unit": "Units", "dimension": "U"},
                "supply_area": {"value": self.supply_area_mn_sqft, "unit": "mn sq ft", "dimension": "L²"}
            },

            # Layer 1: Derived Metrics
            "layer1": {
                "absorption_rate": {
                    "value": round(self.absorption_rate, 2) if self.absorption_rate else None,
                    "unit": "%",
                    "formula": "(Sales Units / Supply Units) * 100"
                },
                "sales_avg_unit_size": {
                    "value": round(self.sales_avg_unit_size_sqft, 0) if self.sales_avg_unit_size_sqft else None,
                    "unit": "sq ft",
                    "formula": "(Sales Area * 1M) / Sales Units"
                },
                "supply_avg_unit_size": {
                    "value": round(self.supply_avg_unit_size_sqft, 0) if self.supply_avg_unit_size_sqft else None,
                    "unit": "sq ft",
                    "formula": "(Supply Area * 1M) / Supply Units"
                },
                "yoy_growth_sales": {
                    "value": round(self.yoy_growth_sales, 2) if self.yoy_growth_sales is not None else None,
                    "unit": "%",
                    "formula": "((Current - Last Year Same Q) / Last Year Same Q) * 100"
                },
                "yoy_growth_supply": {
                    "value": round(self.yoy_growth_supply, 2) if self.yoy_growth_supply is not None else None,
                    "unit": "%",
                    "formula": "((Current - Last Year Same Q) / Last Year Same Q) * 100"
                },
                "qoq_growth_sales": {
                    "value": round(self.qoq_growth_sales, 2) if self.qoq_growth_sales is not None else None,
                    "unit": "%",
                    "formula": "((Current - Previous Q) / Previous Q) * 100"
                },
                "qoq_growth_supply": {
                    "value": round(self.qoq_growth_supply, 2) if self.qoq_growth_supply is not None else None,
                    "unit": "%",
                    "formula": "((Current - Previous Q) / Previous Q) * 100"
                }
            }
        }


class QuarterlyMarketKGService:
    """
    Quarterly Market Knowledge Graph Service

    Manages quarters as first-class KG nodes with:
    - Layer 0 raw dimensions
    - Layer 1 derived metrics
    - YoY/QoQ growth calculations
    """

    def __init__(self):
        self.quarters: List[QuarterNode] = []
        self.metadata: Dict[str, Any] = {}
        self._load_data()
        self._calculate_growth_metrics()

    def _load_data(self):
        """Load quarterly data and create QuarterNode instances"""
        data_file = Path(settings.DATA_PATH) / "extracted" / "quarterly_sales_supply.json"

        if not data_file.exists():
            print(f"Warning: {data_file} not found")
            return

        with open(data_file, 'r', encoding='utf-8') as f:
            full_data = json.load(f)

        self.metadata = full_data.get('metadata', {})
        raw_data = full_data.get('data', [])

        # Create QuarterNode for each quarter
        self.quarters = [QuarterNode(q) for q in raw_data]

        print(f"✓ Quarterly Market KG: {len(self.quarters)} quarter nodes loaded")
        print(f"  Date range: {self.metadata.get('date_range', {}).get('start')} to {self.metadata.get('date_range', {}).get('end')}")

    def _calculate_growth_metrics(self):
        """Calculate YoY and QoQ growth for all quarters"""

        # Create lookup maps for efficient access
        quarter_map = {q.quarter_id: q for q in self.quarters}

        for i, quarter in enumerate(self.quarters):
            # QoQ Growth (compare with previous quarter)
            if i > 0:
                prev_quarter = self.quarters[i - 1]

                if prev_quarter.sales_units > 0:
                    quarter.qoq_growth_sales = ((quarter.sales_units - prev_quarter.sales_units) / prev_quarter.sales_units) * 100

                if prev_quarter.supply_units > 0:
                    quarter.qoq_growth_supply = ((quarter.supply_units - prev_quarter.supply_units) / prev_quarter.supply_units) * 100

            # YoY Growth (compare with same quarter last year)
            # Find quarter from same quarter_num but previous year
            last_year = quarter.year - 1
            last_year_quarter_id = f"Q{quarter.quarter_num}_FY{str(last_year)[-2:]}_{str(last_year+1)[-2:]}"

            if last_year_quarter_id in quarter_map:
                last_year_quarter = quarter_map[last_year_quarter_id]

                if last_year_quarter.sales_units > 0:
                    quarter.yoy_growth_sales = ((quarter.sales_units - last_year_quarter.sales_units) / last_year_quarter.sales_units) * 100

                if last_year_quarter.supply_units > 0:
                    quarter.yoy_growth_supply = ((quarter.supply_units - last_year_quarter.supply_units) / last_year_quarter.supply_units) * 100

    def get_quarter_by_id(self, quarter_id: str) -> Optional[QuarterNode]:
        """Get a specific quarter by ID"""
        for q in self.quarters:
            if q.quarter_id == quarter_id:
                return q
        return None

    def get_quarters_by_year(self, year: int) -> List[QuarterNode]:
        """Get all quarters for a specific fiscal year"""
        return [q for q in self.quarters if q.year == year]

    def get_quarters_by_year_range(self, start_year: int, end_year: int) -> List[QuarterNode]:
        """Get all quarters within a year range"""
        return [q for q in self.quarters if start_year <= q.year <= end_year]

    def get_recent_quarters(self, n: int = 8) -> List[QuarterNode]:
        """Get N most recent quarters"""
        return self.quarters[-n:] if len(self.quarters) >= n else self.quarters

    def get_all_quarters(self) -> List[QuarterNode]:
        """Get all quarters"""
        return self.quarters

    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about the quarterly data"""
        return self.metadata

    def query_quarters(self, filters: Dict[str, Any]) -> List[QuarterNode]:
        """
        Query quarters with flexible filters

        Examples:
        - {"year": 2024} → All quarters in 2024
        - {"year_range": [2022, 2024]} → All quarters 2022-2024
        - {"quarter_num": 1} → All Q1 quarters across all years
        - {"min_absorption_rate": 10} → Quarters with absorption >= 10%
        """
        results = self.quarters

        # Filter by year
        if "year" in filters:
            results = [q for q in results if q.year == filters["year"]]

        # Filter by year range
        if "year_range" in filters:
            start, end = filters["year_range"]
            results = [q for q in results if start <= q.year <= end]

        # Filter by quarter number
        if "quarter_num" in filters:
            results = [q for q in results if q.quarter_num == filters["quarter_num"]]

        # Filter by minimum absorption rate
        if "min_absorption_rate" in filters:
            min_rate = filters["min_absorption_rate"]
            results = [q for q in results if q.absorption_rate and q.absorption_rate >= min_rate]

        # Filter by minimum sales
        if "min_sales_units" in filters:
            min_sales = filters["min_sales_units"]
            results = [q for q in results if q.sales_units >= min_sales]

        return results


# Singleton instance
_quarterly_market_kg_service = None

def get_quarterly_market_kg_service() -> QuarterlyMarketKGService:
    """Get singleton instance of QuarterlyMarketKGService"""
    global _quarterly_market_kg_service
    if _quarterly_market_kg_service is None:
        _quarterly_market_kg_service = QuarterlyMarketKGService()
    return _quarterly_market_kg_service
