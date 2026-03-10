"""
Kolkata Knowledge Graph Service
Mega Knowledge Graph with L0/L1/L2 layers for Kolkata real estate market

Node hierarchy:
- MicromarketNode (distance-based ranges)
- ProjectNode (880+ projects)
- QuarterNode (time series Q2 14-15 to Q2 25-26)
- UnitTypeNode (10 unit categories)

Dimensions: C (Cash Flow), L² (Area), T (Time), U (Units)
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.config import settings


class MicromarketNode:
    """
    Micromarket as a first-class knowledge graph node

    Represents distance-based micromarket segments in Kolkata
    (e.g., "0-2 KM", "2-4 KM", etc. from CBD)

    Layer 0: Raw dimensions (U, L², T, C)
    Layer 1: Derived metrics (Absorption Rate, Sales Velocity, etc.)
    Layer 2: Financial & predictive metrics (Demand Score, Opportunity Score, etc.)
    """

    def __init__(self, data: Dict[str, Any]):
        # Metadata
        self.micromarket_id = data.get('micromarket_id')
        self.micromarket_name = data.get('micromarket_name')
        self.distance_range = data.get('distance_range', {})
        self.city = data.get('city', 'Kolkata')
        self.state = data.get('state', 'West Bengal')
        self.quarter = data.get('quarter')
        self.data_version = data.get('data_version')

        # Layer 0: Raw Dimensions
        # U dimension (Units)
        self.total_projects = data.get('total_projects', 0)
        self.total_supply_units = data.get('total_supply_units', 0)
        self.unsold_units = data.get('unsold_units', 0)
        self.annual_sales_units = data.get('annual_sales_units', 0)
        self.quarterly_sales_units = data.get('quarterly_sales_units', 0)

        # L² dimension (Area)
        self.total_unsold_sqft = data.get('total_unsold_sqft', 0)
        self.annual_sales_sqft = data.get('annual_sales_sqft', 0)
        self.avg_unit_size_sqft = data.get('avg_unit_size_sqft', 0)

        # C dimension (Cash Flow)
        self.saleable_psf = data.get('saleable_psf', 0)
        self.carpet_psf = data.get('carpet_psf', 0)
        self.new_launch_saleable_psf = data.get('new_launch_saleable_psf', 0)
        self.annual_sales_value = data.get('annual_sales_value', 0)

        # T dimension (Time)
        self.months_inventory = data.get('months_inventory', 0)
        self.avg_project_age = data.get('avg_project_age', 0)

        # Layer 1: Derived metrics (calculated)
        self.absorption_rate = None
        self.sales_velocity = None
        self.unsold_ratio = None
        self.price_trend = None
        self.mom_change_percent = None
        self.inventory_turnover = None

        # Layer 2: Financial & Predictive metrics (calculated)
        self.demand_score = None
        self.supply_pressure = None
        self.competitive_intensity = None
        self.opportunity_score = None
        self.clearance_timeline = None

        # Relationships
        self.projects: List[ProjectNode] = []

        # Calculate derived layers
        self._calculate_layer1_metrics()
        self._calculate_layer2_metrics()

    def _calculate_layer1_metrics(self):
        """Calculate Layer 1 derived metrics from Layer 0 dimensions"""

        # Absorption Rate = (Annual Sales Units / Total Supply Units) * 100
        if self.total_supply_units > 0:
            self.absorption_rate = (self.annual_sales_units / self.total_supply_units) * 100

        # Sales Velocity = Absorption Rate / 12
        if self.absorption_rate is not None:
            self.sales_velocity = self.absorption_rate / 12

        # Unsold Ratio = (Unsold Units / Total Supply Units) * 100
        if self.total_supply_units > 0:
            self.unsold_ratio = (self.unsold_units / self.total_supply_units) * 100

        # Inventory Turnover = Annual Sales Units / Total Stock Units
        # Assuming total stock = total supply for now
        if self.total_supply_units > 0:
            self.inventory_turnover = self.annual_sales_units / self.total_supply_units

    def _calculate_layer2_metrics(self):
        """Calculate Layer 2 financial & predictive metrics from Layer 1"""

        # Demand Score (0-100): Weighted calculation
        if self.absorption_rate is not None and self.sales_velocity is not None:
            # Simplified demand score
            absorption_component = min(self.absorption_rate, 100) * 0.4
            velocity_component = min(self.sales_velocity * 10, 100) * 0.3
            price_momentum_component = 30  # Default neutral
            self.demand_score = int(absorption_component + velocity_component + price_momentum_component)

        # Supply Pressure: Based on months_inventory
        if self.months_inventory > 0:
            if self.months_inventory < 12:
                self.supply_pressure = "low"
            elif self.months_inventory <= 24:
                self.supply_pressure = "medium"
            else:
                self.supply_pressure = "high"

        # Competitive Intensity: Based on project count and supply
        if self.total_projects > 0:
            avg_supply_per_project = self.total_supply_units / self.total_projects
            if avg_supply_per_project < 100:
                self.competitive_intensity = "high"
            elif avg_supply_per_project <= 300:
                self.competitive_intensity = "medium"
            else:
                self.competitive_intensity = "low"

        # Opportunity Score: Weighted calculation
        if self.demand_score is not None:
            supply_pressure_score = {"low": 80, "medium": 50, "high": 20}.get(self.supply_pressure, 50)
            self.opportunity_score = int(self.demand_score * 0.5 + supply_pressure_score * 0.3 + 20)

        # Clearance Timeline = Months Inventory
        self.clearance_timeline = self.months_inventory

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with Layer 0 + Layer 1 + Layer 2 structure"""
        return {
            # Metadata
            "micromarket_id": self.micromarket_id,
            "micromarket_name": self.micromarket_name,
            "distance_range": self.distance_range,
            "city": self.city,
            "state": self.state,
            "quarter": self.quarter,
            "data_version": self.data_version,

            # Layer 0: Raw Dimensions
            "layer0": {
                "total_projects": {"value": self.total_projects, "unit": "count", "dimension": "U"},
                "total_supply_units": {"value": self.total_supply_units, "unit": "Units", "dimension": "U"},
                "unsold_units": {"value": self.unsold_units, "unit": "Units", "dimension": "U"},
                "annual_sales_units": {"value": self.annual_sales_units, "unit": "Units/year", "dimension": "U/T"},
                "quarterly_sales_units": {"value": self.quarterly_sales_units, "unit": "Units/quarter", "dimension": "U/T"},
                "total_unsold_sqft": {"value": self.total_unsold_sqft, "unit": "sq ft", "dimension": "L²"},
                "annual_sales_sqft": {"value": self.annual_sales_sqft, "unit": "sq ft/year", "dimension": "L²/T"},
                "avg_unit_size_sqft": {"value": self.avg_unit_size_sqft, "unit": "sq ft", "dimension": "L²"},
                "saleable_psf": {"value": self.saleable_psf, "unit": "INR/sq ft", "dimension": "C/L²"},
                "carpet_psf": {"value": self.carpet_psf, "unit": "INR/sq ft", "dimension": "C/L²"},
                "new_launch_saleable_psf": {"value": self.new_launch_saleable_psf, "unit": "INR/sq ft", "dimension": "C/L²"},
                "annual_sales_value": {"value": self.annual_sales_value, "unit": "INR Cr/year", "dimension": "C/T"},
                "months_inventory": {"value": self.months_inventory, "unit": "months", "dimension": "T"},
                "avg_project_age": {"value": self.avg_project_age, "unit": "months", "dimension": "T"}
            },

            # Layer 1: Derived Metrics
            "layer1": {
                "absorption_rate": {
                    "value": round(self.absorption_rate, 2) if self.absorption_rate else None,
                    "unit": "%",
                    "formula": "(Annual Sales Units / Total Supply Units) * 100"
                },
                "sales_velocity": {
                    "value": round(self.sales_velocity, 2) if self.sales_velocity else None,
                    "unit": "%/month",
                    "formula": "Absorption Rate / 12"
                },
                "unsold_ratio": {
                    "value": round(self.unsold_ratio, 2) if self.unsold_ratio else None,
                    "unit": "%",
                    "formula": "(Unsold Units / Total Supply Units) * 100"
                },
                "inventory_turnover": {
                    "value": round(self.inventory_turnover, 3) if self.inventory_turnover else None,
                    "unit": "ratio",
                    "formula": "Annual Sales Units / Total Stock Units"
                }
            },

            # Layer 2: Financial & Predictive Metrics
            "layer2": {
                "demand_score": {
                    "value": self.demand_score,
                    "unit": "score (0-100)",
                    "formula": "Weighted: 0.4*Absorption + 0.3*Velocity + 0.3*Price_Momentum"
                },
                "supply_pressure": {
                    "value": self.supply_pressure,
                    "unit": "categorical",
                    "formula": "Based on months_inventory: <12=low, 12-24=medium, >24=high"
                },
                "competitive_intensity": {
                    "value": self.competitive_intensity,
                    "unit": "categorical",
                    "formula": "Based on active projects and supply concentration"
                },
                "opportunity_score": {
                    "value": self.opportunity_score,
                    "unit": "score (0-100)",
                    "formula": "Weighted: 0.5*Demand + 0.3*(100-Supply_Pressure) + 0.2*Price_Momentum"
                },
                "clearance_timeline": {
                    "value": round(self.clearance_timeline, 1) if self.clearance_timeline else None,
                    "unit": "months",
                    "formula": "Months_Inventory"
                }
            }
        }


class ProjectNode:
    """
    Project as a first-class knowledge graph node

    Represents individual real estate projects in Kolkata

    Layer 0: Raw dimensions from PDF + Excel enrichment
    Layer 1: Derived metrics (Sold %, Monthly Velocity, Price Appreciation, etc.)
    Layer 2: Financial metrics (MOI, Sellout Efficiency, Revenue per Month, etc.)
    """

    def __init__(self, data: Dict[str, Any]):
        # Metadata
        self.project_id = data.get('project_id')
        self.project_name = data.get('project_name')
        self.developer_name = data.get('developer_name')
        self.location = data.get('location')
        self.micromarket_id = data.get('micromarket_id')
        self.rera_registered = data.get('rera_registered', False)

        # Layer 0: Raw Dimensions
        # U dimension
        self.project_size = data.get('project_size', 0)
        self.total_supply = data.get('total_supply', 0)
        self.sold_units = data.get('sold_units', 0)
        self.unsold_units = data.get('unsold_units', 0)
        self.annual_sales_units = data.get('annual_sales_units', 0)

        # L² dimension
        self.unit_saleable_size = data.get('unit_saleable_size', 0)
        self.total_saleable_area = data.get('total_saleable_area', 0)
        self.unsold_area = data.get('unsold_area', 0)

        # C dimension
        self.launch_price_psf = data.get('launch_price_psf', 0)
        self.current_price_psf = data.get('current_price_psf', 0)
        self.annual_sales_value = data.get('annual_sales_value', 0)

        # T dimension
        self.launch_date = data.get('launch_date')
        self.possession_date = data.get('possession_date')
        self.project_age_months = data.get('project_age_months', 0)

        # Layer 1: Derived metrics (calculated)
        self.sold_percent = None
        self.unsold_percent = None
        self.monthly_sales_velocity = None
        self.monthly_units_sold = None
        self.price_appreciation = None
        self.absorption_rate = None

        # Layer 2: Financial metrics (calculated)
        self.months_of_inventory = None
        self.revenue_per_month = None
        self.sellout_efficiency = None
        self.price_momentum = None

        # Calculate derived layers
        self._calculate_layer1_metrics()
        self._calculate_layer2_metrics()

    def _calculate_layer1_metrics(self):
        """Calculate Layer 1 derived metrics from Layer 0 dimensions"""

        # Sold % = (Sold Units / Total Supply) * 100
        if self.total_supply > 0:
            self.sold_percent = (self.sold_units / self.total_supply) * 100
            self.unsold_percent = 100 - self.sold_percent
            self.absorption_rate = self.sold_percent

        # Monthly Sales Velocity = (Annual Sales Units / Total Supply) / 12 * 100
        if self.total_supply > 0:
            self.monthly_sales_velocity = (self.annual_sales_units / self.total_supply) / 12 * 100

        # Monthly Units Sold = Annual Sales Units / 12
        if self.annual_sales_units > 0:
            self.monthly_units_sold = self.annual_sales_units / 12

        # Price Appreciation = ((Current PSF - Launch PSF) / Launch PSF) * 100
        if self.launch_price_psf > 0:
            self.price_appreciation = ((self.current_price_psf - self.launch_price_psf) / self.launch_price_psf) * 100

    def _calculate_layer2_metrics(self):
        """Calculate Layer 2 financial metrics from Layer 1"""

        # Months of Inventory = Unsold Units / Monthly Units Sold
        if self.monthly_units_sold and self.monthly_units_sold > 0:
            self.months_of_inventory = self.unsold_units / self.monthly_units_sold

        # Revenue per Month = Annual Sales Value / 12
        if self.annual_sales_value > 0:
            self.revenue_per_month = self.annual_sales_value / 12

        # Sellout Efficiency = (Sold % / Project Age in Months) * 100
        if self.sold_percent and self.project_age_months > 0:
            self.sellout_efficiency = (self.sold_percent / self.project_age_months) * 100

        # Price Momentum (categorical)
        if self.price_appreciation is not None:
            if self.price_appreciation > 10:
                self.price_momentum = "strong"
            elif self.price_appreciation >= 5:
                self.price_momentum = "moderate"
            else:
                self.price_momentum = "weak"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with Layer 0 + Layer 1 + Layer 2 structure"""
        return {
            # Metadata
            "project_id": self.project_id,
            "project_name": self.project_name,
            "developer_name": self.developer_name,
            "location": self.location,
            "micromarket_id": self.micromarket_id,
            "rera_registered": self.rera_registered,

            # Layer 0: Raw Dimensions
            "layer0": {
                "project_size": {"value": self.project_size, "unit": "Units", "dimension": "U"},
                "total_supply": {"value": self.total_supply, "unit": "Units", "dimension": "U"},
                "sold_units": {"value": self.sold_units, "unit": "Units", "dimension": "U"},
                "unsold_units": {"value": self.unsold_units, "unit": "Units", "dimension": "U"},
                "annual_sales_units": {"value": self.annual_sales_units, "unit": "Units/year", "dimension": "U/T"},
                "unit_saleable_size": {"value": self.unit_saleable_size, "unit": "sq ft", "dimension": "L²"},
                "total_saleable_area": {"value": self.total_saleable_area, "unit": "sq ft", "dimension": "L²"},
                "unsold_area": {"value": self.unsold_area, "unit": "sq ft", "dimension": "L²"},
                "launch_price_psf": {"value": self.launch_price_psf, "unit": "INR/sq ft", "dimension": "C/L²"},
                "current_price_psf": {"value": self.current_price_psf, "unit": "INR/sq ft", "dimension": "C/L²"},
                "annual_sales_value": {"value": self.annual_sales_value, "unit": "INR Cr/year", "dimension": "C/T"},
                "launch_date": {"value": self.launch_date, "unit": "Month-Year", "dimension": "T"},
                "possession_date": {"value": self.possession_date, "unit": "Month-Year", "dimension": "T"},
                "project_age_months": {"value": self.project_age_months, "unit": "months", "dimension": "T"}
            },

            # Layer 1: Derived Metrics
            "layer1": {
                "sold_percent": {
                    "value": round(self.sold_percent, 2) if self.sold_percent else None,
                    "unit": "%",
                    "formula": "(Sold Units / Total Supply) * 100"
                },
                "unsold_percent": {
                    "value": round(self.unsold_percent, 2) if self.unsold_percent else None,
                    "unit": "%",
                    "formula": "100 - Sold Percent"
                },
                "monthly_sales_velocity": {
                    "value": round(self.monthly_sales_velocity, 2) if self.monthly_sales_velocity else None,
                    "unit": "%/month",
                    "formula": "(Annual Sales Units / Total Supply) / 12 * 100"
                },
                "monthly_units_sold": {
                    "value": round(self.monthly_units_sold, 2) if self.monthly_units_sold else None,
                    "unit": "Units/month",
                    "formula": "Annual Sales Units / 12"
                },
                "price_appreciation": {
                    "value": round(self.price_appreciation, 2) if self.price_appreciation else None,
                    "unit": "%",
                    "formula": "((Current PSF - Launch PSF) / Launch PSF) * 100"
                },
                "absorption_rate": {
                    "value": round(self.absorption_rate, 2) if self.absorption_rate else None,
                    "unit": "%",
                    "formula": "(Sold Units / Total Supply) * 100"
                }
            },

            # Layer 2: Financial Metrics
            "layer2": {
                "months_of_inventory": {
                    "value": round(self.months_of_inventory, 1) if self.months_of_inventory else None,
                    "unit": "months",
                    "formula": "(Unsold Units / Monthly Units Sold)"
                },
                "revenue_per_month": {
                    "value": round(self.revenue_per_month, 2) if self.revenue_per_month else None,
                    "unit": "INR Cr/month",
                    "formula": "Annual Sales Value / 12"
                },
                "sellout_efficiency": {
                    "value": round(self.sellout_efficiency, 2) if self.sellout_efficiency else None,
                    "unit": "score",
                    "formula": "(Sold % / Project Age in Months) * 100"
                },
                "price_momentum": {
                    "value": self.price_momentum,
                    "unit": "categorical",
                    "formula": "Based on price appreciation: >10%=strong, 5-10%=moderate, <5%=weak"
                }
            }
        }


class QuarterNode:
    """
    Quarter as a first-class knowledge graph node

    Represents quarterly time-series data for Kolkata market
    (Q2 14-15 to Q2 25-26 = 44 quarters)

    Layer 0: Raw dimensions (sales, supply, pricing)
    Layer 1: Derived metrics (YoY growth, QoQ growth, absorption)
    """

    def __init__(self, data: Dict[str, Any]):
        # Metadata
        self.quarter_id = data.get('quarter_id')
        self.quarter = data.get('quarter')
        self.quarter_num = data.get('quarter_num')
        self.fiscal_year = data.get('fiscal_year')
        self.year = data.get('year')
        self.micromarket_id = data.get('micromarket_id')

        # Layer 0: Raw dimensions
        self.sales_units = data.get('sales_units', 0)
        self.supply_units = data.get('supply_units', 0)
        self.sales_area_mn_sqft = data.get('sales_area_mn_sqft', 0)
        self.supply_area_mn_sqft = data.get('supply_area_mn_sqft', 0)
        self.avg_psf = data.get('avg_psf', 0)

        # Layer 1: Derived metrics (calculated)
        self.absorption_rate = None
        self.yoy_growth_sales = None
        self.qoq_growth_sales = None
        self.avg_unit_size_sqft = None

        # Calculate Layer 1 metrics
        self._calculate_layer1_metrics()

    def _calculate_layer1_metrics(self):
        """Calculate Layer 1 derived metrics from Layer 0 dimensions"""

        # Absorption Rate = (Sales Units / Supply Units) * 100
        if self.supply_units > 0:
            self.absorption_rate = (self.sales_units / self.supply_units) * 100

        # Average Unit Size = (Sales Area * 1M) / Sales Units
        if self.sales_units > 0:
            self.avg_unit_size_sqft = (self.sales_area_mn_sqft * 1_000_000) / self.sales_units

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with Layer 0 + Layer 1 structure"""
        return {
            # Metadata
            "quarter_id": self.quarter_id,
            "quarter": self.quarter,
            "quarter_num": self.quarter_num,
            "fiscal_year": self.fiscal_year,
            "year": self.year,
            "micromarket_id": self.micromarket_id,

            # Layer 0: Raw Dimensions
            "layer0": {
                "sales_units": {"value": self.sales_units, "unit": "Units", "dimension": "U"},
                "supply_units": {"value": self.supply_units, "unit": "Units", "dimension": "U"},
                "sales_area": {"value": self.sales_area_mn_sqft, "unit": "mn sq ft", "dimension": "L²"},
                "supply_area": {"value": self.supply_area_mn_sqft, "unit": "mn sq ft", "dimension": "L²"},
                "avg_psf": {"value": self.avg_psf, "unit": "INR/sq ft", "dimension": "C/L²"}
            },

            # Layer 1: Derived Metrics
            "layer1": {
                "absorption_rate": {
                    "value": round(self.absorption_rate, 2) if self.absorption_rate else None,
                    "unit": "%",
                    "formula": "(Sales Units / Supply Units) * 100"
                },
                "yoy_growth_sales": {
                    "value": round(self.yoy_growth_sales, 2) if self.yoy_growth_sales is not None else None,
                    "unit": "%",
                    "formula": "((Current Q - Same Q Last Year) / Same Q Last Year) * 100"
                },
                "qoq_growth_sales": {
                    "value": round(self.qoq_growth_sales, 2) if self.qoq_growth_sales is not None else None,
                    "unit": "%",
                    "formula": "((Current Q - Previous Q) / Previous Q) * 100"
                },
                "avg_unit_size_sqft": {
                    "value": round(self.avg_unit_size_sqft, 0) if self.avg_unit_size_sqft else None,
                    "unit": "sq ft",
                    "formula": "(Sales Area * 1M) / Sales Units"
                }
            }
        }


class UnitTypeNode:
    """
    Unit Type as a first-class knowledge graph node

    Represents product categories (1BHK, 2BHK, 3BHK, etc.)

    Layer 0: Raw dimensions (sales, supply, pricing)
    Layer 1: Derived metrics (absorption, market share, price premium)
    """

    def __init__(self, data: Dict[str, Any]):
        # Metadata
        self.unit_type_id = data.get('unit_type_id')
        self.unit_type = data.get('unit_type')
        self.category = data.get('category', 'Residential')
        self.bhk_type = data.get('bhk_type')
        self.micromarket_id = data.get('micromarket_id')

        # Layer 0: Raw dimensions
        self.sales_units = data.get('sales_units', 0)
        self.supply_units = data.get('supply_units', 0)
        self.avg_size_sqft = data.get('avg_size_sqft', 0)
        self.avg_psf = data.get('avg_psf', 0)
        self.avg_ticket_size = data.get('avg_ticket_size', 0)

        # Layer 1: Derived metrics (calculated)
        self.absorption_rate = None
        self.market_share = None
        self.price_premium = None

        # Calculate Layer 1 metrics
        self._calculate_layer1_metrics()

    def _calculate_layer1_metrics(self):
        """Calculate Layer 1 derived metrics from Layer 0 dimensions"""

        # Absorption Rate = (Sales Units / Supply Units) * 100
        if self.supply_units > 0:
            self.absorption_rate = (self.sales_units / self.supply_units) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with Layer 0 + Layer 1 structure"""
        return {
            # Metadata
            "unit_type_id": self.unit_type_id,
            "unit_type": self.unit_type,
            "category": self.category,
            "bhk_type": self.bhk_type,
            "micromarket_id": self.micromarket_id,

            # Layer 0: Raw Dimensions
            "layer0": {
                "sales_units": {"value": self.sales_units, "unit": "Units", "dimension": "U"},
                "supply_units": {"value": self.supply_units, "unit": "Units", "dimension": "U"},
                "avg_size_sqft": {"value": self.avg_size_sqft, "unit": "sq ft", "dimension": "L²"},
                "avg_psf": {"value": self.avg_psf, "unit": "INR/sq ft", "dimension": "C/L²"},
                "avg_ticket_size": {"value": self.avg_ticket_size, "unit": "INR Lakhs", "dimension": "C"}
            },

            # Layer 1: Derived Metrics
            "layer1": {
                "absorption_rate": {
                    "value": round(self.absorption_rate, 2) if self.absorption_rate else None,
                    "unit": "%",
                    "formula": "(Sales Units / Supply Units) * 100"
                },
                "market_share": {
                    "value": round(self.market_share, 2) if self.market_share else None,
                    "unit": "%",
                    "formula": "(Unit Type Supply / Total Market Supply) * 100"
                },
                "price_premium": {
                    "value": round(self.price_premium, 2) if self.price_premium else None,
                    "unit": "%",
                    "formula": "((Unit PSF - Market Avg PSF) / Market Avg PSF) * 100"
                }
            }
        }


class KolkataKGService:
    """
    Kolkata Knowledge Graph Service

    Manages the mega knowledge graph for Kolkata real estate market with:
    - Micromarkets (distance-based ranges)
    - Projects (880+)
    - Quarterly time series (44 quarters)
    - Unit types (10 categories)

    All nodes have L0/L1/L2 layers with dimensional calculations
    """

    def __init__(self):
        self.micromarkets: List[MicromarketNode] = []
        self.projects: List[ProjectNode] = []
        self.quarters: List[QuarterNode] = []
        self.unit_types: List[UnitTypeNode] = []
        self.metadata: Dict[str, Any] = {}

        # Load data from JSON files
        self._load_data()

    def _load_data(self):
        """Load Kolkata knowledge graph data from JSON files"""
        data_dir = Path(settings.DATA_PATH) / "extracted" / "kolkata"

        # Load micromarkets
        micromarkets_file = data_dir / "kolkata_micromarkets.json"
        if micromarkets_file.exists():
            with open(micromarkets_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.metadata = data.get('metadata', {})
                self.micromarkets = [MicromarketNode(mm) for mm in data.get('data', [])]

        # Load projects
        projects_file = data_dir / "kolkata_projects.json"
        if projects_file.exists():
            with open(projects_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.projects = [ProjectNode(p) for p in data.get('data', [])]

        # Load quarters
        quarters_file = data_dir / "kolkata_quarters.json"
        if quarters_file.exists():
            with open(quarters_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.quarters = [QuarterNode(q) for q in data.get('data', [])]

        # Load unit types
        unit_types_file = data_dir / "kolkata_unit_types.json"
        if unit_types_file.exists():
            with open(unit_types_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.unit_types = [UnitTypeNode(ut) for ut in data.get('data', [])]

        print(f"✓ Kolkata KG: {len(self.micromarkets)} micromarkets, {len(self.projects)} projects, {len(self.quarters)} quarters, {len(self.unit_types)} unit types loaded")

    # ==================================================================
    # MICROMARKET QUERIES
    # ==================================================================

    def get_micromarket_by_id(self, micromarket_id: str) -> Optional[MicromarketNode]:
        """Get micromarket by ID"""
        for mm in self.micromarkets:
            if mm.micromarket_id == micromarket_id:
                return mm
        return None

    def get_micromarket_by_distance_range(self, min_km: float, max_km: float) -> Optional[MicromarketNode]:
        """Get micromarket by distance range"""
        for mm in self.micromarkets:
            if (mm.distance_range.get('min_km') == min_km and
                mm.distance_range.get('max_km') == max_km):
                return mm
        return None

    def get_all_micromarkets(self) -> List[MicromarketNode]:
        """Get all micromarkets"""
        return self.micromarkets

    def get_micromarket_summary(self, micromarket_id: str) -> Optional[Dict]:
        """Get comprehensive summary of a micromarket"""
        mm = self.get_micromarket_by_id(micromarket_id)
        if mm:
            return mm.to_dict()
        return None

    def compare_micromarkets(self, micromarket_ids: List[str]) -> Dict:
        """Compare multiple micromarkets"""
        comparison = []
        for mm_id in micromarket_ids:
            mm = self.get_micromarket_by_id(mm_id)
            if mm:
                comparison.append(mm.to_dict())
        return {"micromarkets": comparison}

    # ==================================================================
    # PROJECT QUERIES
    # ==================================================================

    def get_project_by_id(self, project_id: int) -> Optional[ProjectNode]:
        """Get project by ID"""
        for p in self.projects:
            if p.project_id == project_id:
                return p
        return None

    def get_project_by_name(self, name: str) -> Optional[ProjectNode]:
        """Get project by name (case-insensitive, fuzzy)"""
        normalized_search = ' '.join(name.lower().replace('\n', ' ').split())
        for p in self.projects:
            if p.project_name:
                normalized_name = ' '.join(p.project_name.lower().replace('\n', ' ').split())
                if normalized_name == normalized_search:
                    return p
        return None

    def get_projects_by_micromarket(self, micromarket_id: str) -> List[ProjectNode]:
        """Get all projects in a micromarket"""
        return [p for p in self.projects if p.micromarket_id == micromarket_id]

    def get_projects_by_developer(self, developer_name: str) -> List[ProjectNode]:
        """Get all projects by a developer"""
        normalized_search = developer_name.lower()
        return [p for p in self.projects if normalized_search in p.developer_name.lower()]

    def get_top_performing_projects(self, metric: str = "absorption_rate", n: int = 10) -> List[ProjectNode]:
        """Get top N performing projects by metric"""
        if metric == "absorption_rate":
            sorted_projects = sorted(
                [p for p in self.projects if p.absorption_rate is not None],
                key=lambda x: x.absorption_rate,
                reverse=True
            )
        elif metric == "price_appreciation":
            sorted_projects = sorted(
                [p for p in self.projects if p.price_appreciation is not None],
                key=lambda x: x.price_appreciation,
                reverse=True
            )
        elif metric == "sellout_efficiency":
            sorted_projects = sorted(
                [p for p in self.projects if p.sellout_efficiency is not None],
                key=lambda x: x.sellout_efficiency,
                reverse=True
            )
        else:
            sorted_projects = self.projects

        return sorted_projects[:n]

    # ==================================================================
    # QUARTERLY QUERIES
    # ==================================================================

    def get_quarter_by_id(self, quarter_id: str) -> Optional[QuarterNode]:
        """Get quarter by ID"""
        for q in self.quarters:
            if q.quarter_id == quarter_id:
                return q
        return None

    def get_quarters_by_year(self, year: int) -> List[QuarterNode]:
        """Get all quarters for a specific year"""
        return [q for q in self.quarters if q.year == year]

    def get_recent_quarters(self, n: int = 8) -> List[QuarterNode]:
        """Get N most recent quarters"""
        return self.quarters[-n:] if len(self.quarters) >= n else self.quarters

    def get_yoy_comparison(self, quarter_id: str) -> Optional[Dict]:
        """Get year-over-year comparison for a quarter"""
        q = self.get_quarter_by_id(quarter_id)
        if not q:
            return None

        # Find same quarter last year
        last_year = q.year - 1
        last_year_quarter_id = f"Q{q.quarter_num}_FY{str(last_year)[-2:]}_{str(last_year+1)[-2:]}"
        last_year_q = self.get_quarter_by_id(last_year_quarter_id)

        if last_year_q:
            return {
                "current_quarter": q.to_dict(),
                "last_year_quarter": last_year_q.to_dict(),
                "yoy_growth": q.yoy_growth_sales
            }
        return {"current_quarter": q.to_dict(), "last_year_quarter": None}

    # ==================================================================
    # UNIT TYPE QUERIES
    # ==================================================================

    def get_unit_type_performance(self, unit_type: str) -> Optional[Dict]:
        """Get performance metrics for a unit type"""
        ut = next((u for u in self.unit_types if u.unit_type == unit_type), None)
        if ut:
            return ut.to_dict()
        return None

    def get_all_unit_types(self) -> List[UnitTypeNode]:
        """Get all unit types"""
        return self.unit_types

    def compare_unit_types(self, micromarket_id: str) -> Dict:
        """Compare all unit types in a micromarket"""
        unit_types_in_mm = [ut for ut in self.unit_types if ut.micromarket_id == micromarket_id]
        return {
            "micromarket_id": micromarket_id,
            "unit_types": [ut.to_dict() for ut in unit_types_in_mm]
        }

    # ==================================================================
    # UTILITY METHODS
    # ==================================================================

    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about the Kolkata knowledge graph"""
        return self.metadata

    def export_full_graph(self) -> Dict[str, Any]:
        """Export the complete knowledge graph as a single JSON"""
        return {
            "metadata": self.metadata,
            "micromarkets": [mm.to_dict() for mm in self.micromarkets],
            "projects": [p.to_dict() for p in self.projects],
            "quarters": [q.to_dict() for q in self.quarters],
            "unit_types": [ut.to_dict() for ut in self.unit_types]
        }


# Singleton instance
_kolkata_kg_service = None

def get_kolkata_kg_service() -> KolkataKGService:
    """Get singleton instance of KolkataKGService"""
    global _kolkata_kg_service
    if _kolkata_kg_service is None:
        _kolkata_kg_service = KolkataKGService()
    return _kolkata_kg_service
