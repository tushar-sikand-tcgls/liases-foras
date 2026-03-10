"""
Quarterly Market Data Service: Time-series analysis for sales and supply
Layer 0 dimensional data (U, L², T) for market trends
Pillar 1: Market Intelligence - Temporal Analysis
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.config import settings


class QuarterlyMarketService:
    """
    Service for managing quarterly sales and marketable supply data

    Layer 0 Dimensions:
    - U (Units): Sales units, Supply units
    - L² (Area): Sales area (mn sq ft), Supply area (mn sq ft)
    - T (Time): Quarterly periods from Q2 FY14-15 to Q2 FY25-26

    Data Source: Liases Foras Pillar 1 - Market Intelligence
    """

    def __init__(self):
        self.quarterly_data: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
        self._load_data()

    def _load_data(self):
        """Load quarterly sales and supply data from JSON"""
        data_file = Path(settings.DATA_PATH) / "extracted" / "quarterly_sales_supply.json"

        if not data_file.exists():
            print(f"Warning: {data_file} not found")
            return

        with open(data_file, 'r', encoding='utf-8') as f:
            full_data = json.load(f)

        self.metadata = full_data.get('metadata', {})
        self.quarterly_data = full_data.get('data', [])

        print(f"✓ Loaded {len(self.quarterly_data)} quarterly data points")
        print(f"  Date range: {self.metadata.get('date_range', {}).get('start')} to {self.metadata.get('date_range', {}).get('end')}")

    def get_all_quarters(self) -> List[Dict[str, Any]]:
        """Get all quarterly data points with full details"""
        return self.quarterly_data

    def get_quarter_by_id(self, quarter_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific quarter data by quarter_id

        Args:
            quarter_id: Quarter identifier (e.g., "Q3_FY14_15", "Q2_FY25_26")

        Returns:
            Quarter data dict or None if not found
        """
        for quarter in self.quarterly_data:
            if quarter.get('quarter_id') == quarter_id:
                return quarter
        return None

    def get_quarters_by_year_range(self, start_year: int, end_year: int) -> List[Dict[str, Any]]:
        """
        Get quarters within a specific year range

        Args:
            start_year: Starting year (e.g., 2020)
            end_year: Ending year (e.g., 2024)

        Returns:
            List of quarters within the year range
        """
        filtered = [
            q for q in self.quarterly_data
            if start_year <= q.get('year', 0) <= end_year
        ]
        return filtered

    def get_recent_quarters(self, n: int = 8) -> List[Dict[str, Any]]:
        """
        Get the N most recent quarters

        Args:
            n: Number of recent quarters to retrieve (default: 8 = 2 years)

        Returns:
            List of most recent quarters
        """
        return self.quarterly_data[-n:] if len(self.quarterly_data) >= n else self.quarterly_data

    def calculate_yoy_growth(self, metric: str = 'sales_units') -> List[Dict[str, Any]]:
        """
        Calculate Year-over-Year growth for a specific metric

        Args:
            metric: Metric name ('sales_units', 'sales_area_mn_sqft', 'supply_units', 'supply_area_mn_sqft')

        Returns:
            List of dicts with quarter, value, yoy_value, yoy_growth_pct
        """
        growth_data = []

        for i, quarter in enumerate(self.quarterly_data):
            # Find same quarter in previous year (4 quarters back)
            yoy_index = i - 4

            if yoy_index >= 0:
                current_value = quarter.get(metric, 0)
                yoy_value = self.quarterly_data[yoy_index].get(metric, 0)

                if yoy_value > 0:
                    yoy_growth_pct = ((current_value - yoy_value) / yoy_value) * 100
                else:
                    yoy_growth_pct = None

                growth_data.append({
                    'quarter': quarter.get('quarter'),
                    'quarter_id': quarter.get('quarter_id'),
                    'current_value': current_value,
                    'yoy_value': yoy_value,
                    'yoy_growth_pct': round(yoy_growth_pct, 2) if yoy_growth_pct is not None else None,
                    'metric': metric
                })

        return growth_data

    def calculate_qoq_growth(self, metric: str = 'sales_units') -> List[Dict[str, Any]]:
        """
        Calculate Quarter-over-Quarter growth for a specific metric

        Args:
            metric: Metric name ('sales_units', 'sales_area_mn_sqft', 'supply_units', 'supply_area_mn_sqft')

        Returns:
            List of dicts with quarter, value, prev_value, qoq_growth_pct
        """
        growth_data = []

        for i in range(1, len(self.quarterly_data)):
            current = self.quarterly_data[i]
            previous = self.quarterly_data[i - 1]

            current_value = current.get(metric, 0)
            prev_value = previous.get(metric, 0)

            if prev_value > 0:
                qoq_growth_pct = ((current_value - prev_value) / prev_value) * 100
            else:
                qoq_growth_pct = None

            growth_data.append({
                'quarter': current.get('quarter'),
                'quarter_id': current.get('quarter_id'),
                'current_value': current_value,
                'prev_value': prev_value,
                'qoq_growth_pct': round(qoq_growth_pct, 2) if qoq_growth_pct is not None else None,
                'metric': metric
            })

        return growth_data

    def get_summary_statistics(self, metric: str = 'sales_units') -> Dict[str, Any]:
        """
        Calculate summary statistics for a metric across all quarters

        Args:
            metric: Metric name ('sales_units', 'sales_area_mn_sqft', 'supply_units', 'supply_area_mn_sqft')

        Returns:
            Dict with min, max, mean, median, total
        """
        values = [q.get(metric, 0) for q in self.quarterly_data]

        if not values:
            return {}

        sorted_values = sorted(values)
        n = len(values)

        return {
            'metric': metric,
            'min': min(values),
            'max': max(values),
            'mean': sum(values) / n,
            'median': sorted_values[n // 2] if n % 2 != 0 else (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2,
            'total': sum(values),
            'count': n
        }

    def calculate_absorption_rate_trend(self) -> List[Dict[str, Any]]:
        """
        Calculate quarterly absorption rate: (Sales Units / Supply Units) * 100

        Layer 1 Derived Metric: Absorption Rate = (U_sales / U_supply) * 100

        Returns:
            List of dicts with quarter, absorption_rate_pct, sales_units, supply_units
        """
        absorption_data = []

        for quarter in self.quarterly_data:
            sales = quarter.get('sales_units', 0)
            supply = quarter.get('supply_units', 0)

            if supply > 0:
                absorption_rate = (sales / supply) * 100
            else:
                absorption_rate = None

            absorption_data.append({
                'quarter': quarter.get('quarter'),
                'quarter_id': quarter.get('quarter_id'),
                'absorption_rate_pct': round(absorption_rate, 2) if absorption_rate is not None else None,
                'sales_units': sales,
                'supply_units': supply
            })

        return absorption_data

    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about the quarterly data source"""
        return self.metadata


# Singleton instance
quarterly_market_service = QuarterlyMarketService()
