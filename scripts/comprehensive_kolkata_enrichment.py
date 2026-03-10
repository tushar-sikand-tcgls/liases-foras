#!/usr/bin/env python3
"""
Comprehensive Kolkata R&D Data Enrichment Script
================================================

Integrates ALL 57 Excel files from Kolkata R&D dataset into a comprehensive
knowledge graph with v4 nested attributes.

File Categories:
1. Base Data (1): List_of_Comparables_Projects.xlsx
2. Price Trends (28): Project_and_Benchmark_Location_Price_Trend, Saleable/Carpet Area Price
3. Sales Data (7): Annual_Sales_Data, Quarterly_Sales_Data (with construction stages)
4. Inventory & Stock (4): Months_Inventory, Unsold_Stock_Data
5. Analysis (4): Flat_Type, Unit_Ticket_Size, Distance_Range, Price_Range Analysis
6. Performance Metrics (4): Top_10_Project_Data (annual sales, supply, inventory, velocity)
7. Supply Data (2): Possession_Wise, Quarterly_Supply
8. Project Details (3): ProjectDetailsFlatwise, Project_Marketable_Wings, Catchment_Projects
9. Market Summary (2): Quarterly_Marker_Summary, Yearly_Marker_Summary

Output: kolkata_v4_comprehensive.json with dimensions: U, L², C, C/L², T, I, L, U/T
"""

import pandas as pd
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional
import glob
import re

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_v4_attribute(
    value: Any,
    unit: str,
    dimension: str,
    description: str,
    source: str = "Kolkata_R&D_Comprehensive"
) -> Dict[str, Any]:
    """Create a v4 nested attribute with relationships and metadata"""
    return {
        "value": value if value is not None else 0,
        "unit": unit,
        "dimension": dimension,
        "relationships": [{"type": "IS", "target": dimension}],
        "source": source,
        "isPure": True,
        "description": description
    }


def parse_number(value: Any) -> float:
    """Safely parse number from various formats"""
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(',', '').replace('%', ''))
    except:
        return 0.0


def parse_range(value: str) -> tuple:
    """Parse range like '131.63-351.46' to (min, max, avg)"""
    try:
        if pd.isna(value) or not isinstance(value, str):
            return (0, 0, 0)
        parts = str(value).split('-')
        if len(parts) == 2:
            min_val = float(parts[0])
            max_val = float(parts[1])
            avg_val = (min_val + max_val) / 2
            return (min_val, max_val, avg_val)
        else:
            val = float(parts[0])
            return (val, val, val)
    except:
        return (0, 0, 0)


def load_excel_with_auto_header(filepath: Path, max_search=20) -> Optional[pd.DataFrame]:
    """Load Excel file by auto-detecting header row"""
    try:
        for skip in range(max_search):
            try:
                df = pd.read_excel(filepath, header=skip)
                # Check if we have valid column names
                valid_cols = [col for col in df.columns if not (pd.isna(col) or str(col).startswith('Unnamed'))]
                if len(valid_cols) >= 3:
                    logger.info(f"    Header found at row {skip}")
                    return df
            except:
                continue
        logger.warning(f"    Could not find valid header in {filepath.name}")
        return None
    except Exception as e:
        logger.warning(f"    Error loading {filepath.name}: {e}")
        return None


def load_multiple_files(base_dir: Path, pattern: str) -> List[pd.DataFrame]:
    """Load multiple files matching a pattern"""
    files = sorted(base_dir.glob(pattern))
    dataframes = []
    for file in files:
        df = load_excel_with_auto_header(file)
        if df is not None:
            dataframes.append(df)
    return dataframes


def extract_time_series(dataframes: List[pd.DataFrame]) -> List[Dict]:
    """Extract time series data from multiple dataframes"""
    time_series = []
    for df in dataframes:
        for _, row in df.iterrows():
            time_series.append({
                "date": str(row.get('Date', row.get('Quarter', row.get('Month', '')))),
                "value": parse_number(row.get('Value', row.get('Price', row.get('Sales', 0)))),
                "metadata": {k: v for k, v in row.items() if k not in ['Date', 'Quarter', 'Month', 'Value', 'Price', 'Sales']}
            })
    return time_series


# ============================================================================
# DATA LOADERS BY CATEGORY
# ============================================================================

class DataLoader:
    """Handles loading of all data categories"""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.loaded_files = []

    def load_base_projects(self) -> pd.DataFrame:
        """Load base project data (1 file)"""
        logger.info("\n[1] Loading Base Project Data...")
        file = self.base_dir / "List_of_Comparables_Projects.xlsx"
        df = pd.read_excel(file, sheet_name=0)
        df.columns = df.iloc[5]
        df = df.iloc[6:].reset_index(drop=True)
        self.loaded_files.append(str(file.name))
        logger.info(f"  ✓ Loaded {len(df)} base projects")
        return df

    def load_price_trends(self) -> Dict[str, Any]:
        """Load price trend data (28 files)"""
        logger.info("\n[2] Loading Price Trend Data (28 files)...")

        data = {
            "project_benchmark_trends": [],
            "saleable_area_prices": [],
            "carpet_area_prices": []
        }

        # Project and Benchmark Location Price Trends (13 files)
        logger.info("  Loading Project_and_Benchmark_Location_Price_Trend files...")
        pattern = "Project_and_Benchmark_Location_Price_Trend*.xlsx"
        dfs = load_multiple_files(self.base_dir, pattern)
        data["project_benchmark_trends"] = dfs
        self.loaded_files.extend([f"Project_and_Benchmark_Location_Price_Trend ({i})" for i in range(len(dfs))])
        logger.info(f"    ✓ Loaded {len(dfs)} benchmark trend files")

        # Saleable Area Price Data (8 files)
        logger.info("  Loading Saleable_Area_Price_(Rs_PSF)_Data files...")
        pattern = "Saleable_Area_Price_(Rs_PSF)_Data*.xlsx"
        dfs = load_multiple_files(self.base_dir, pattern)
        data["saleable_area_prices"] = dfs
        self.loaded_files.extend([f"Saleable_Area_Price ({i})" for i in range(len(dfs))])
        logger.info(f"    ✓ Loaded {len(dfs)} saleable area price files")

        # Carpet Area Price Data (7 files)
        logger.info("  Loading Carpet_Area_Price_(Rs_PSF)_Data files...")
        pattern = "Carpet_Area_Price_(Rs_PSF)_Data*.xlsx"
        dfs = load_multiple_files(self.base_dir, pattern)
        data["carpet_area_prices"] = dfs
        self.loaded_files.extend([f"Carpet_Area_Price ({i})" for i in range(len(dfs))])
        logger.info(f"    ✓ Loaded {len(dfs)} carpet area price files")

        return data

    def load_sales_data(self) -> Dict[str, Any]:
        """Load sales data (7 files)"""
        logger.info("\n[3] Loading Sales Data (7 files)...")

        data = {
            "annual_sales": [],
            "quarterly_sales": [],
            "construction_stage_sales": []
        }

        # Annual Sales Data
        logger.info("  Loading Annual_Sales_Data files...")
        for pattern in ["Annual_Sales_Data*.xlsx"]:
            dfs = load_multiple_files(self.base_dir, pattern)
            data["annual_sales"].extend(dfs)
            self.loaded_files.extend([f"Annual_Sales_Data ({i})" for i in range(len(dfs))])
        logger.info(f"    ✓ Loaded {len(data['annual_sales'])} annual sales files")

        # Quarterly Sales Data
        logger.info("  Loading Quarterly_Sales_Data files...")
        for pattern in ["Quarterly_Sales_Data*.xlsx", "Quarterly_Sales_&_Marketable_Supply_Data*.xlsx"]:
            dfs = load_multiple_files(self.base_dir, pattern)
            data["quarterly_sales"].extend(dfs)
            self.loaded_files.extend([f"Quarterly_Sales ({i})" for i in range(len(dfs))])
        logger.info(f"    ✓ Loaded {len(data['quarterly_sales'])} quarterly sales files")

        # Construction Stage Sales
        logger.info("  Loading sales by construction stage...")
        pattern = "*Sales_Data_as_per_Construction_Stage*.xlsx"
        dfs = load_multiple_files(self.base_dir, pattern)
        data["construction_stage_sales"] = dfs
        self.loaded_files.extend([f"Construction_Stage_Sales ({i})" for i in range(len(dfs))])
        logger.info(f"    ✓ Loaded {len(dfs)} construction stage sales files")

        return data

    def load_inventory_stock_data(self) -> Dict[str, Any]:
        """Load inventory and stock data (4 files)"""
        logger.info("\n[4] Loading Inventory & Stock Data (4 files)...")

        data = {
            "months_inventory": None,
            "unsold_stock": [],
            "sales_velocity": None
        }

        # Months Inventory
        logger.info("  Loading Months_Inventory data...")
        file = self.base_dir / "Months_Inventory_(Months)_Data (2).xlsx"
        if file.exists():
            data["months_inventory"] = load_excel_with_auto_header(file)
            self.loaded_files.append(str(file.name))
            logger.info(f"    ✓ Loaded months inventory data")

        # Unsold Stock Data
        logger.info("  Loading Unsold_Stock_Data files...")
        pattern = "Unsold_Stock_Data*.xlsx"
        dfs = load_multiple_files(self.base_dir, pattern)
        data["unsold_stock"] = dfs
        self.loaded_files.extend([f"Unsold_Stock ({i})" for i in range(len(dfs))])
        logger.info(f"    ✓ Loaded {len(dfs)} unsold stock files")

        # Sales Velocity
        logger.info("  Loading Sales_Velocity data...")
        file = self.base_dir / "Sales_Velocity_(%_Monthly_Sales)_Data (2).xlsx"
        if file.exists():
            data["sales_velocity"] = load_excel_with_auto_header(file)
            self.loaded_files.append(str(file.name))
            logger.info(f"    ✓ Loaded sales velocity data")

        return data

    def load_analysis_data(self) -> Dict[str, Any]:
        """Load analysis data (4 files)"""
        logger.info("\n[5] Loading Analysis Data (4 files)...")

        data = {
            "flat_type_analysis": None,
            "unit_ticket_size": None,
            "distance_range": None,
            "price_range": None,
            "unit_size_range": None
        }

        # Flat Type Analysis
        logger.info("  Loading Flat_Type_Analysis...")
        file = self.base_dir / "Flat_Type_Analysis_Data (2).xlsx"
        if file.exists():
            data["flat_type_analysis"] = load_excel_with_auto_header(file)
            self.loaded_files.append(str(file.name))
            logger.info(f"    ✓ Loaded flat type analysis")

        # Unit Ticket Size Analysis
        logger.info("  Loading Unit_Ticket_Size_Analysis...")
        file = self.base_dir / "Unit_Ticket_Size_Analysis_Data (1).xlsx"
        if file.exists():
            data["unit_ticket_size"] = load_excel_with_auto_header(file)
            self.loaded_files.append(str(file.name))
            logger.info(f"    ✓ Loaded unit ticket size analysis")

        # Distance Range Analysis
        logger.info("  Loading Distance_Range_Analysis...")
        pattern = "Distance_Range_Analysis_Data*.xlsx"
        dfs = load_multiple_files(self.base_dir, pattern)
        if dfs:
            data["distance_range"] = dfs[0]  # Take first one
            self.loaded_files.append("Distance_Range_Analysis_Data")
            logger.info(f"    ✓ Loaded distance range analysis")

        # Price Range Analysis
        logger.info("  Loading Price_Range_Analysis...")
        pattern = "Price_Range_Analysis*.xlsx"
        dfs = load_multiple_files(self.base_dir, pattern)
        if dfs:
            data["price_range"] = dfs[0]
            self.loaded_files.append("Price_Range_Analysis")
            logger.info(f"    ✓ Loaded price range analysis")

        # Unit Size Range Analysis
        logger.info("  Loading Unit_Size_Range_Analysis...")
        pattern = "Unit_Size_Range_Analysis*.xlsx"
        dfs = load_multiple_files(self.base_dir, pattern)
        if dfs:
            data["unit_size_range"] = dfs[0]
            self.loaded_files.append("Unit_Size_Range_Analysis")
            logger.info(f"    ✓ Loaded unit size range analysis")

        return data

    def load_performance_metrics(self) -> Dict[str, Any]:
        """Load performance metrics data (4 files)"""
        logger.info("\n[6] Loading Performance Metrics (4 files)...")

        data = {
            "top_annual_sales": None,
            "top_marketable_supply": None,
            "top_month_inventory": None,
            "top_sales_velocity": None
        }

        files = {
            "top_annual_sales": "Top_10_Project_Data_(ANNUALSALES) (5).xlsx",
            "top_marketable_supply": "Top_10_Project_Data_(MARKETABLE_SUPPLY) (3).xlsx",
            "top_month_inventory": "Top_10_Project_Data_(MONTHINVENTORY) (3).xlsx",
            "top_sales_velocity": "Top_10_Project_Data_(SALESVELOCITY) (5).xlsx"
        }

        for key, filename in files.items():
            file = self.base_dir / filename
            if file.exists():
                data[key] = load_excel_with_auto_header(file)
                self.loaded_files.append(filename)
                logger.info(f"    ✓ Loaded {key}")

        return data

    def load_supply_data(self) -> Dict[str, Any]:
        """Load supply data (2 files)"""
        logger.info("\n[7] Loading Supply Data (2 files)...")

        data = {
            "possession_wise": None,
            "quarterly_supply": None
        }

        # Possession Wise Distribution
        file = self.base_dir / "Possession_Wise_Marketable_Supply_&_Sales_Distribution_Data (2).xlsx"
        if file.exists():
            data["possession_wise"] = load_excel_with_auto_header(file)
            self.loaded_files.append(str(file.name))
            logger.info(f"    ✓ Loaded possession wise distribution")

        # Quarterly Supply Data
        file = self.base_dir / "Quarterly_Sales_&_Marketable_Supply_Data (1).xlsx"
        if file.exists():
            data["quarterly_supply"] = load_excel_with_auto_header(file)
            self.loaded_files.append(str(file.name))
            logger.info(f"    ✓ Loaded quarterly supply data")

        return data

    def load_project_details(self) -> Dict[str, Any]:
        """Load project detail files (3 files)"""
        logger.info("\n[8] Loading Project Details (3 files)...")

        data = {
            "project_details_flatwise": None,
            "project_marketable_wings": None,
            "catchment_projects": None
        }

        # Project Details Flatwise
        file = self.base_dir / "ProjectDetailsFlatwise.xlsx"
        if file.exists():
            data["project_details_flatwise"] = load_excel_with_auto_header(file)
            self.loaded_files.append(str(file.name))
            logger.info(f"    ✓ Loaded project details flatwise")

        # Project Marketable Wings
        file = self.base_dir / "Project_Marketable_Wings.xlsx"
        if file.exists():
            data["project_marketable_wings"] = load_excel_with_auto_header(file)
            self.loaded_files.append(str(file.name))
            logger.info(f"    ✓ Loaded project marketable wings")

        # Catchment Projects
        file = self.base_dir / "Catchment_Projects (2).xlsx"
        if file.exists():
            data["catchment_projects"] = load_excel_with_auto_header(file)
            self.loaded_files.append(str(file.name))
            logger.info(f"    ✓ Loaded catchment projects")

        return data

    def load_market_summary(self) -> Dict[str, Any]:
        """Load market summary data (2 files)"""
        logger.info("\n[9] Loading Market Summary Data (2 files)...")

        data = {
            "quarterly_summary": None,
            "yearly_summary": None
        }

        # Quarterly Market Summary
        file = self.base_dir / "Quarterly_Marker_Summary (3).xlsx"
        if file.exists():
            data["quarterly_summary"] = load_excel_with_auto_header(file)
            self.loaded_files.append(str(file.name))
            logger.info(f"    ✓ Loaded quarterly market summary")

        # Yearly Market Summary
        file = self.base_dir / "Yearly_Marker_Summary (2).xlsx"
        if file.exists():
            data["yearly_summary"] = load_excel_with_auto_header(file)
            self.loaded_files.append(str(file.name))
            logger.info(f"    ✓ Loaded yearly market summary")

        return data


# ============================================================================
# PROJECT ENRICHMENT
# ============================================================================

class ProjectEnricher:
    """Enriches projects with all available data sources"""

    def __init__(self, all_data: Dict[str, Any]):
        self.data = all_data

    def enrich_project(self, row: pd.Series, idx: int) -> Dict[str, Any]:
        """Enrich a single project with all available data"""
        project_id = str(row.get('Project Id', f'KOL_{idx+1:04d}'))
        project_name = str(row.get('Project Name', 'Unknown Project'))

        logger.info(f"  Enriching: {project_name} (ID: {project_id})")

        # Parse ranges
        cost_min, cost_max, cost_avg = parse_range(row.get('Total Cost (Rs.Lacs)'))
        saleable_min, saleable_max, saleable_avg = parse_range(row.get('Saleable Size (Sq.Ft.)'))
        carpet_min, carpet_max, carpet_avg = parse_range(row.get('Carpet Size (Sq.Ft.)'))

        # Base project structure
        project = {
            "projectId": project_id,
            "projectName": project_name,

            # Location (L dimension)
            "location": create_v4_attribute(
                str(row.get('Location', 'Kolkata')),
                "text",
                "L",
                "Project location"
            ),

            # Developer (I dimension)
            "developerName": create_v4_attribute(
                str(row.get('Developer Name', 'Unknown')),
                "text",
                "I",
                "Developer name"
            ),

            # Time dimensions (T)
            "launchDate": create_v4_attribute(
                str(row.get('Launch Date', '')),
                "date",
                "T",
                "Project launch date"
            ),

            "possessionDate": create_v4_attribute(
                str(row.get('Possession Date', '')),
                "date",
                "T",
                "Expected possession date"
            ),

            # Supply dimensions (U, L²)
            "totalSupplyUnits": create_v4_attribute(
                parse_number(row.get('Total Supply (Units)')),
                "count",
                "U",
                "Total supply in units"
            ),

            "totalSupplyArea": create_v4_attribute(
                parse_number(row.get('Total Supply (Sq.Ft.)')),
                "sqft",
                "L²",
                "Total supply area"
            ),

            # Sales metrics (U, L²)
            "soldPercentage": create_v4_attribute(
                parse_number(row.get('Sold as on Date (%)')),
                "percent",
                "U",
                "Percentage sold"
            ),

            "quarterlySalesUnits": create_v4_attribute(
                parse_number(row.get('Quaterly Sales (Units)')),
                "count",
                "U",
                "Quarterly sales in units"
            ),

            "quarterlySalesArea": create_v4_attribute(
                parse_number(row.get('Quarterly Sales (Sq.Ft.)')),
                "sqft",
                "L²",
                "Quarterly sales area"
            ),

            "annualSalesUnits": create_v4_attribute(
                parse_number(row.get('Annual Sales (Units)')),
                "count",
                "U",
                "Annual sales in units"
            ),

            "annualSalesArea": create_v4_attribute(
                parse_number(row.get('Annual Sales (Sq.Ft.)')),
                "sqft",
                "L²",
                "Annual sales area"
            ),

            # Configuration (I)
            "flatType": create_v4_attribute(
                str(row.get('Flat Type', '')),
                "text",
                "I",
                "Flat type configuration"
            ),

            # Price metrics (C, C/L²)
            "averageCost": create_v4_attribute(
                cost_avg,
                "lacs",
                "C",
                f"Average cost (Range: {cost_min}-{cost_max} Lacs)"
            ),

            "averageSaleableArea": create_v4_attribute(
                saleable_avg,
                "sqft",
                "L²",
                f"Average saleable area (Range: {saleable_min}-{saleable_max} sqft)"
            ),

            "averageCarpetArea": create_v4_attribute(
                carpet_avg,
                "sqft",
                "L²",
                f"Average carpet area (Range: {carpet_min}-{carpet_max} sqft)"
            ),

            "saleableRate": create_v4_attribute(
                parse_number(row.get('Saleable Rate (Rs/PSF)')),
                "rs_per_sqft",
                "C/L²",
                "Saleable rate per square foot"
            ),

            "carpetRate": create_v4_attribute(
                parse_number(row.get('Carpet Rate (Rs/PSF)')),
                "rs_per_sqft",
                "C/L²",
                "Carpet rate per square foot"
            ),
        }

        # Add enrichments
        self._add_price_trends(project, project_id, project_name)
        self._add_sales_enrichments(project, project_id, project_name)
        self._add_inventory_enrichments(project, project_id, project_name)
        self._add_analysis_enrichments(project, project_id, project_name)
        self._add_performance_rankings(project, project_id, project_name)
        self._add_project_details(project, project_id, project_name)

        return project

    def _add_price_trends(self, project: Dict, project_id: str, project_name: str):
        """Add price trend time series data"""
        price_data = self.data.get("price_trends", {})

        trends = []

        # Extract trends from all benchmark files
        for df in price_data.get("project_benchmark_trends", []):
            if df is not None and len(df) > 0:
                for _, row in df.iterrows():
                    if str(row.get('Project Id', '')).strip() == project_id.strip() or \
                       str(row.get('Project Name', '')).strip().lower() == project_name.strip().lower():
                        trends.append({
                            "date": create_v4_attribute(
                                str(row.get('Date', row.get('Quarter', ''))),
                                "date",
                                "T",
                                "Time period"
                            ),
                            "saleablePrice": create_v4_attribute(
                                parse_number(row.get('Saleable Price', row.get('Price', 0))),
                                "rs_per_sqft",
                                "C/L²",
                                "Saleable area price per sqft"
                            ),
                            "carpetPrice": create_v4_attribute(
                                parse_number(row.get('Carpet Price', 0)),
                                "rs_per_sqft",
                                "C/L²",
                                "Carpet area price per sqft"
                            ),
                            "benchmarkPrice": create_v4_attribute(
                                parse_number(row.get('Benchmark Price', 0)),
                                "rs_per_sqft",
                                "C/L²",
                                "Benchmark location price"
                            )
                        })

        if trends:
            project["priceTrendTimeSeries"] = {
                "value": trends,
                "unit": "list",
                "dimension": "C/L²",
                "description": "Historical price trends over time",
                "source": "Project_and_Benchmark_Location_Price_Trend",
                "isPure": False,
                "relationships": [{"type": "HAS_MANY", "target": "T"}]
            }

    def _add_sales_enrichments(self, project: Dict, project_id: str, project_name: str):
        """Add detailed sales data enrichments"""
        sales_data = self.data.get("sales_data", {})

        # Annual sales time series
        annual_sales = []
        for df in sales_data.get("annual_sales", []):
            if df is not None:
                for _, row in df.iterrows():
                    if str(row.get('Project Id', '')).strip() == project_id.strip():
                        annual_sales.append({
                            "year": create_v4_attribute(
                                str(row.get('Year', row.get('Period', ''))),
                                "year",
                                "T",
                                "Year"
                            ),
                            "salesUnits": create_v4_attribute(
                                parse_number(row.get('Sales (Units)', row.get('Annual Sales (Units)', 0))),
                                "count",
                                "U",
                                "Units sold"
                            ),
                            "salesArea": create_v4_attribute(
                                parse_number(row.get('Sales (Sq.Ft.)', row.get('Annual Sales (Sq.Ft.)', 0))),
                                "sqft",
                                "L²",
                                "Area sold"
                            )
                        })

        if annual_sales:
            project["annualSalesTimeSeries"] = {
                "value": annual_sales,
                "unit": "list",
                "dimension": "U",
                "description": "Annual sales performance over time",
                "source": "Annual_Sales_Data",
                "isPure": False,
                "relationships": [{"type": "HAS_MANY", "target": "T"}]
            }

        # Quarterly sales time series
        quarterly_sales = []
        for df in sales_data.get("quarterly_sales", []):
            if df is not None:
                for _, row in df.iterrows():
                    if str(row.get('Project Id', '')).strip() == project_id.strip():
                        quarterly_sales.append({
                            "quarter": create_v4_attribute(
                                str(row.get('Quarter', row.get('Period', ''))),
                                "quarter",
                                "T",
                                "Quarter"
                            ),
                            "salesUnits": create_v4_attribute(
                                parse_number(row.get('Sales (Units)', row.get('Quarterly Sales (Units)', 0))),
                                "count",
                                "U",
                                "Units sold"
                            ),
                            "salesArea": create_v4_attribute(
                                parse_number(row.get('Sales (Sq.Ft.)', row.get('Quarterly Sales (Sq.Ft.)', 0))),
                                "sqft",
                                "L²",
                                "Area sold"
                            ),
                            "marketableSupply": create_v4_attribute(
                                parse_number(row.get('Marketable Supply (Units)', 0)),
                                "count",
                                "U",
                                "Marketable supply"
                            )
                        })

        if quarterly_sales:
            project["quarterlySalesTimeSeries"] = {
                "value": quarterly_sales,
                "unit": "list",
                "dimension": "U",
                "description": "Quarterly sales performance",
                "source": "Quarterly_Sales_Data",
                "isPure": False,
                "relationships": [{"type": "HAS_MANY", "target": "T"}]
            }

        # Construction stage sales
        construction_sales = []
        for df in sales_data.get("construction_stage_sales", []):
            if df is not None:
                for _, row in df.iterrows():
                    if str(row.get('Project Id', '')).strip() == project_id.strip():
                        construction_sales.append({
                            "stage": create_v4_attribute(
                                str(row.get('Construction Stage', row.get('Stage', ''))),
                                "text",
                                "I",
                                "Construction stage"
                            ),
                            "salesUnits": create_v4_attribute(
                                parse_number(row.get('Sales (Units)', 0)),
                                "count",
                                "U",
                                "Units sold at this stage"
                            ),
                            "unsoldUnits": create_v4_attribute(
                                parse_number(row.get('Unsold (Units)', 0)),
                                "count",
                                "U",
                                "Unsold units at this stage"
                            )
                        })

        if construction_sales:
            project["constructionStageSales"] = {
                "value": construction_sales,
                "unit": "list",
                "dimension": "U",
                "description": "Sales breakdown by construction stage",
                "source": "Sales_Data_as_per_Construction_Stage",
                "isPure": False,
                "relationships": [{"type": "CATEGORIZED_BY", "target": "constructionStage"}]
            }

    def _add_inventory_enrichments(self, project: Dict, project_id: str, project_name: str):
        """Add inventory and stock data enrichments"""
        inventory_data = self.data.get("inventory_stock", {})

        # Months inventory
        df_inventory = inventory_data.get("months_inventory")
        if df_inventory is not None:
            for _, row in df_inventory.iterrows():
                if str(row.get('Project Id', '')).strip() == project_id.strip():
                    project["monthsInventory"] = create_v4_attribute(
                        parse_number(row.get('Months Inventory', row.get('Month Inventory', 0))),
                        "months",
                        "T",
                        "Months of inventory remaining"
                    )
                    break

        # Unsold stock details
        unsold_stock = []
        for df in inventory_data.get("unsold_stock", []):
            if df is not None:
                for _, row in df.iterrows():
                    if str(row.get('Project Id', '')).strip() == project_id.strip():
                        unsold_stock.append({
                            "unsoldUnits": create_v4_attribute(
                                parse_number(row.get('Unsold (Units)', row.get('Unsold Units', 0))),
                                "count",
                                "U",
                                "Unsold units"
                            ),
                            "unsoldArea": create_v4_attribute(
                                parse_number(row.get('Unsold (Sq.Ft.)', row.get('Unsold Area', 0))),
                                "sqft",
                                "L²",
                                "Unsold area"
                            ),
                            "category": create_v4_attribute(
                                str(row.get('Category', row.get('Type', ''))),
                                "text",
                                "I",
                                "Stock category"
                            )
                        })

        if unsold_stock:
            project["unsoldStockBreakdown"] = {
                "value": unsold_stock,
                "unit": "list",
                "dimension": "U",
                "description": "Detailed unsold stock breakdown",
                "source": "Unsold_Stock_Data",
                "isPure": False,
                "relationships": [{"type": "HAS_MANY", "target": "stockCategory"}]
            }

        # Sales velocity
        df_velocity = inventory_data.get("sales_velocity")
        if df_velocity is not None:
            for _, row in df_velocity.iterrows():
                if str(row.get('Project Id', '')).strip() == project_id.strip():
                    project["monthlySalesVelocity"] = create_v4_attribute(
                        parse_number(row.get('Monthly Sales Velocity', row.get('Sales Velocity (%)', 0))),
                        "percent",
                        "U/T",
                        "Monthly sales velocity percentage"
                    )
                    break

    def _add_analysis_enrichments(self, project: Dict, project_id: str, project_name: str):
        """Add analysis data enrichments"""
        analysis_data = self.data.get("analysis", {})

        # Flat type analysis (unit mix)
        df_flat = analysis_data.get("flat_type_analysis")
        if df_flat is not None:
            unit_mix = []
            for _, row in df_flat.iterrows():
                if str(row.get('Project Id', '')).strip() == project_id.strip():
                    unit_mix.append({
                        "flatType": create_v4_attribute(
                            str(row.get('Flat', row.get('Flat Type', ''))),
                            "text",
                            "I",
                            "Unit type"
                        ),
                        "saleableMinSize": create_v4_attribute(
                            parse_number(row.get('Saleable Min Size', 0)),
                            "sqft",
                            "L²",
                            "Minimum saleable area"
                        ),
                        "saleableMaxSize": create_v4_attribute(
                            parse_number(row.get('Saleable Max Size', 0)),
                            "sqft",
                            "L²",
                            "Maximum saleable area"
                        ),
                        "minCost": create_v4_attribute(
                            parse_number(row.get('Min Cost(Rs.Lacs)', 0)),
                            "lacs",
                            "C",
                            "Minimum cost"
                        ),
                        "maxCost": create_v4_attribute(
                            parse_number(row.get('Max Cost(Rs.Lacs)', 0)),
                            "lacs",
                            "C",
                            "Maximum cost"
                        ),
                        "annualSalesUnits": create_v4_attribute(
                            parse_number(row.get('Annual Sales (Units)', 0)),
                            "count",
                            "U",
                            "Annual sales for this type"
                        ),
                        "unsoldUnits": create_v4_attribute(
                            parse_number(row.get('Unsold (Units)', 0)),
                            "count",
                            "U",
                            "Unsold units of this type"
                        ),
                        "productEfficiency": create_v4_attribute(
                            parse_number(row.get('Product Efficiency (%)', 0)),
                            "percent",
                            "U",
                            "Product efficiency"
                        )
                    })

            if unit_mix:
                project["unitMixBreakdown"] = {
                    "value": unit_mix,
                    "unit": "list",
                    "dimension": "I",
                    "description": "Detailed unit mix breakdown",
                    "source": "Flat_Type_Analysis_Data",
                    "isPure": False,
                    "relationships": [{"type": "HAS_MANY", "target": "flatType"}]
                }

        # Unit ticket size (price range distribution)
        df_ticket = analysis_data.get("unit_ticket_size")
        if df_ticket is not None:
            price_distribution = []
            for _, row in df_ticket.iterrows():
                if str(row.get('Project Id', '')).strip() == project_id.strip():
                    price_distribution.append({
                        "priceRange": create_v4_attribute(
                            str(row.get('Costrange', row.get('Price Range', ''))),
                            "text",
                            "C",
                            "Price range bucket"
                        ),
                        "annualSalesUnits": create_v4_attribute(
                            parse_number(row.get('Annual Sales (Units)', 0)),
                            "count",
                            "U",
                            "Annual sales in range"
                        ),
                        "unsoldUnits": create_v4_attribute(
                            parse_number(row.get('Unsold (Units)', 0)),
                            "count",
                            "U",
                            "Unsold in range"
                        ),
                        "monthsInventory": create_v4_attribute(
                            parse_number(row.get('Annual Months Inventory', 0)),
                            "months",
                            "T",
                            "Inventory months"
                        ),
                        "monthlySalesVelocity": create_v4_attribute(
                            parse_number(row.get('Monthly Sales Velocity (%)', 0)),
                            "percent",
                            "U/T",
                            "Monthly velocity"
                        )
                    })

            if price_distribution:
                project["priceRangeDistribution"] = {
                    "value": price_distribution,
                    "unit": "list",
                    "dimension": "C",
                    "description": "Price range distribution",
                    "source": "Unit_Ticket_Size_Analysis_Data",
                    "isPure": False,
                    "relationships": [{"type": "DISTRIBUTED_BY", "target": "priceRange"}]
                }

        # Unit size range analysis
        df_size = analysis_data.get("unit_size_range")
        if df_size is not None:
            size_distribution = []
            for _, row in df_size.iterrows():
                if str(row.get('Project Id', '')).strip() == project_id.strip():
                    size_distribution.append({
                        "sizeRange": create_v4_attribute(
                            str(row.get('Size Range', '')),
                            "text",
                            "L²",
                            "Size range bucket"
                        ),
                        "units": create_v4_attribute(
                            parse_number(row.get('Units', 0)),
                            "count",
                            "U",
                            "Units in this size range"
                        ),
                        "sales": create_v4_attribute(
                            parse_number(row.get('Sales', 0)),
                            "count",
                            "U",
                            "Sales in this range"
                        )
                    })

            if size_distribution:
                project["sizeRangeDistribution"] = {
                    "value": size_distribution,
                    "unit": "list",
                    "dimension": "L²",
                    "description": "Unit size range distribution",
                    "source": "Unit_Size_Range_Analysis",
                    "isPure": False,
                    "relationships": [{"type": "DISTRIBUTED_BY", "target": "sizeRange"}]
                }

    def _add_performance_rankings(self, project: Dict, project_id: str, project_name: str):
        """Add performance ranking data"""
        performance = self.data.get("performance_metrics", {})

        rankings = {}

        # Check each top 10 list
        top_lists = {
            "annualSalesRank": "top_annual_sales",
            "marketableSupplyRank": "top_marketable_supply",
            "monthInventoryRank": "top_month_inventory",
            "salesVelocityRank": "top_sales_velocity"
        }

        for rank_key, data_key in top_lists.items():
            df = performance.get(data_key)
            if df is not None:
                for rank_idx, row in df.iterrows():
                    if str(row.get('Project Id', '')).strip() == project_id.strip() or \
                       str(row.get('Project Name', '')).strip().lower() == project_name.strip().lower():
                        rankings[rank_key] = create_v4_attribute(
                            rank_idx + 1,
                            "rank",
                            "I",
                            f"Ranking in top 10 {rank_key.replace('Rank', '')}"
                        )
                        break

        if rankings:
            project["performanceRankings"] = {
                "value": rankings,
                "unit": "dict",
                "dimension": "I",
                "description": "Performance rankings across multiple metrics",
                "source": "Top_10_Project_Data",
                "isPure": False,
                "relationships": [{"type": "RANKED_IN", "target": "performanceMetric"}]
            }

    def _add_project_details(self, project: Dict, project_id: str, project_name: str):
        """Add detailed project information"""
        details = self.data.get("project_details", {})

        # Flatwise details
        df_flatwise = details.get("project_details_flatwise")
        if df_flatwise is not None:
            flatwise_details = []
            for _, row in df_flatwise.iterrows():
                if str(row.get('Project Id', '')).strip() == project_id.strip():
                    flatwise_details.append({
                        "wing": create_v4_attribute(
                            str(row.get('Wing', row.get('Tower', ''))),
                            "text",
                            "I",
                            "Wing/Tower name"
                        ),
                        "flatType": create_v4_attribute(
                            str(row.get('Flat Type', '')),
                            "text",
                            "I",
                            "Flat configuration"
                        ),
                        "saleableArea": create_v4_attribute(
                            parse_number(row.get('Saleable Area', 0)),
                            "sqft",
                            "L²",
                            "Saleable area"
                        ),
                        "carpetArea": create_v4_attribute(
                            parse_number(row.get('Carpet Area', 0)),
                            "sqft",
                            "L²",
                            "Carpet area"
                        ),
                        "totalUnits": create_v4_attribute(
                            parse_number(row.get('Total Units', 0)),
                            "count",
                            "U",
                            "Total units"
                        )
                    })

            if flatwise_details:
                project["flatwiseDetails"] = {
                    "value": flatwise_details,
                    "unit": "list",
                    "dimension": "I",
                    "description": "Detailed flatwise breakdown",
                    "source": "ProjectDetailsFlatwise",
                    "isPure": False,
                    "relationships": [{"type": "HAS_MANY", "target": "wing"}]
                }

        # Marketable wings
        df_wings = details.get("project_marketable_wings")
        if df_wings is not None:
            wings = []
            for _, row in df_wings.iterrows():
                if str(row.get('Project Id', '')).strip() == project_id.strip():
                    wings.append({
                        "wingName": create_v4_attribute(
                            str(row.get('Wing Name', row.get('Wing', ''))),
                            "text",
                            "I",
                            "Wing name"
                        ),
                        "marketableUnits": create_v4_attribute(
                            parse_number(row.get('Marketable Units', 0)),
                            "count",
                            "U",
                            "Marketable units"
                        ),
                        "soldUnits": create_v4_attribute(
                            parse_number(row.get('Sold Units', 0)),
                            "count",
                            "U",
                            "Sold units"
                        ),
                        "unsoldUnits": create_v4_attribute(
                            parse_number(row.get('Unsold Units', 0)),
                            "count",
                            "U",
                            "Unsold units"
                        )
                    })

            if wings:
                project["marketableWings"] = {
                    "value": wings,
                    "unit": "list",
                    "dimension": "U",
                    "description": "Wing-wise marketable supply",
                    "source": "Project_Marketable_Wings",
                    "isPure": False,
                    "relationships": [{"type": "HAS_MANY", "target": "wing"}]
                }


# ============================================================================
# MARKET-LEVEL ENRICHMENTS
# ============================================================================

class MarketEnricher:
    """Creates market-level enrichments and summaries"""

    def __init__(self, all_data: Dict[str, Any]):
        self.data = all_data

    def create_market_enrichments(self) -> Dict[str, Any]:
        """Create comprehensive market-level enrichments"""
        logger.info("\n[10] Creating Market-Level Enrichments...")

        market = {}

        # Supply data enrichments
        supply_data = self.data.get("supply_data", {})

        # Possession-wise distribution
        df_possession = supply_data.get("possession_wise")
        if df_possession is not None:
            possession_dist = []
            for _, row in df_possession.iterrows():
                possession_dist.append({
                    "possessionPeriod": create_v4_attribute(
                        str(row.get('Possession Period', row.get('Period', ''))),
                        "text",
                        "T",
                        "Possession time period"
                    ),
                    "marketableSupply": create_v4_attribute(
                        parse_number(row.get('Marketable Supply (Units)', 0)),
                        "count",
                        "U",
                        "Marketable supply"
                    ),
                    "sales": create_v4_attribute(
                        parse_number(row.get('Sales (Units)', 0)),
                        "count",
                        "U",
                        "Sales"
                    ),
                    "supplyArea": create_v4_attribute(
                        parse_number(row.get('Marketable Supply (Sq.Ft.)', 0)),
                        "sqft",
                        "L²",
                        "Supply area"
                    )
                })

            market["possessionWiseDistribution"] = {
                "value": possession_dist,
                "unit": "list",
                "dimension": "T",
                "description": "Market supply distribution by possession period",
                "source": "Possession_Wise_Marketable_Supply",
                "isPure": False,
                "relationships": [{"type": "DISTRIBUTED_BY", "target": "possessionPeriod"}]
            }

        # Quarterly supply summary
        df_quarterly_supply = supply_data.get("quarterly_supply")
        if df_quarterly_supply is not None:
            quarterly_supply = []
            for _, row in df_quarterly_supply.iterrows():
                quarterly_supply.append({
                    "quarter": create_v4_attribute(
                        str(row.get('Quarter', '')),
                        "quarter",
                        "T",
                        "Quarter"
                    ),
                    "sales": create_v4_attribute(
                        parse_number(row.get('Sales (Units)', 0)),
                        "count",
                        "U",
                        "Quarterly sales"
                    ),
                    "marketableSupply": create_v4_attribute(
                        parse_number(row.get('Marketable Supply (Units)', 0)),
                        "count",
                        "U",
                        "Marketable supply"
                    )
                })

            market["quarterlySupplySummary"] = {
                "value": quarterly_supply,
                "unit": "list",
                "dimension": "U",
                "description": "Quarterly supply and sales summary",
                "source": "Quarterly_Sales_&_Marketable_Supply_Data",
                "isPure": False,
                "relationships": [{"type": "HAS_MANY", "target": "T"}]
            }

        # Market summaries
        summary_data = self.data.get("market_summary", {})

        # Quarterly market summary
        df_quarterly_summary = summary_data.get("quarterly_summary")
        if df_quarterly_summary is not None:
            quarterly_summary = []
            for _, row in df_quarterly_summary.iterrows():
                quarterly_summary.append({
                    "quarter": create_v4_attribute(
                        str(row.get('Quarter', '')),
                        "quarter",
                        "T",
                        "Quarter"
                    ),
                    "totalSales": create_v4_attribute(
                        parse_number(row.get('Total Sales', 0)),
                        "count",
                        "U",
                        "Total market sales"
                    ),
                    "averagePrice": create_v4_attribute(
                        parse_number(row.get('Average Price', 0)),
                        "rs_per_sqft",
                        "C/L²",
                        "Average market price"
                    ),
                    "newLaunches": create_v4_attribute(
                        parse_number(row.get('New Launches', 0)),
                        "count",
                        "U",
                        "New project launches"
                    )
                })

            market["quarterlyMarketSummary"] = {
                "value": quarterly_summary,
                "unit": "list",
                "dimension": "U",
                "description": "Quarterly market overview",
                "source": "Quarterly_Marker_Summary",
                "isPure": False,
                "relationships": [{"type": "SUMMARIZES", "target": "T"}]
            }

        # Yearly market summary
        df_yearly_summary = summary_data.get("yearly_summary")
        if df_yearly_summary is not None:
            yearly_summary = []
            for _, row in df_yearly_summary.iterrows():
                yearly_summary.append({
                    "year": create_v4_attribute(
                        str(row.get('Year', '')),
                        "year",
                        "T",
                        "Year"
                    ),
                    "totalSales": create_v4_attribute(
                        parse_number(row.get('Total Sales', 0)),
                        "count",
                        "U",
                        "Annual market sales"
                    ),
                    "averagePrice": create_v4_attribute(
                        parse_number(row.get('Average Price', 0)),
                        "rs_per_sqft",
                        "C/L²",
                        "Average market price"
                    ),
                    "newLaunches": create_v4_attribute(
                        parse_number(row.get('New Launches', 0)),
                        "count",
                        "U",
                        "New project launches"
                    )
                })

            market["yearlyMarketSummary"] = {
                "value": yearly_summary,
                "unit": "list",
                "dimension": "U",
                "description": "Yearly market overview",
                "source": "Yearly_Marker_Summary",
                "isPure": False,
                "relationships": [{"type": "SUMMARIZES", "target": "T"}]
            }

        # Analysis summaries
        analysis_data = self.data.get("analysis", {})

        # Flat type market summary
        df_flat = analysis_data.get("flat_type_analysis")
        if df_flat is not None:
            flat_summary = {}
            for _, row in df_flat.iterrows():
                flat_type = str(row.get('Flat', ''))
                if flat_type:
                    if flat_type not in flat_summary:
                        flat_summary[flat_type] = {
                            "totalSales": 0,
                            "totalUnsold": 0,
                            "count": 0
                        }
                    flat_summary[flat_type]["totalSales"] += parse_number(row.get('Annual Sales (Units)', 0))
                    flat_summary[flat_type]["totalUnsold"] += parse_number(row.get('Unsold (Units)', 0))
                    flat_summary[flat_type]["count"] += 1

            market["flatTypeMarketSummary"] = {
                "value": flat_summary,
                "unit": "dict",
                "dimension": "I",
                "description": "Market-wide flat type distribution",
                "source": "Flat_Type_Analysis_Data",
                "isPure": False,
                "relationships": [{"type": "AGGREGATES", "target": "flatType"}]
            }

        # Performance metrics summary
        performance = self.data.get("performance_metrics", {})

        top_performers = {}
        for metric, df in performance.items():
            if df is not None and len(df) > 0:
                top_performers[metric] = []
                for idx, row in df.iterrows():
                    if idx < 10:  # Top 10
                        top_performers[metric].append({
                            "rank": idx + 1,
                            "projectName": str(row.get('Project Name', '')),
                            "projectId": str(row.get('Project Id', '')),
                            "value": parse_number(row.get('Value', 0))
                        })

        if top_performers:
            market["topPerformers"] = {
                "value": top_performers,
                "unit": "dict",
                "dimension": "I",
                "description": "Top 10 performers across various metrics",
                "source": "Top_10_Project_Data",
                "isPure": False,
                "relationships": [{"type": "RANKS", "target": "project"}]
            }

        logger.info(f"  ✓ Created {len(market)} market-level enrichments")

        return market


# ============================================================================
# MAIN TRANSFORMATION FUNCTION
# ============================================================================

def comprehensive_kolkata_enrichment():
    """Main function to create comprehensive enriched knowledge graph"""
    logger.info("="*80)
    logger.info("COMPREHENSIVE KOLKATA R&D DATA ENRICHMENT")
    logger.info("="*80)
    logger.info("Integrating ALL 57 Excel files into v4 knowledge graph format")
    logger.info("="*80)

    # Paths
    base_dir = Path("/Users/tusharsikand/Downloads/Kolkata R&D")
    output_dir = Path("/Users/tusharsikand/Documents/Projects/liases-foras/data/extracted/kolkata")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "kolkata_v4_comprehensive.json"

    # Initialize data loader
    loader = DataLoader(base_dir)

    # Load all data categories
    all_data = {
        "base_projects": loader.load_base_projects(),
        "price_trends": loader.load_price_trends(),
        "sales_data": loader.load_sales_data(),
        "inventory_stock": loader.load_inventory_stock_data(),
        "analysis": loader.load_analysis_data(),
        "performance_metrics": loader.load_performance_metrics(),
        "supply_data": loader.load_supply_data(),
        "project_details": loader.load_project_details(),
        "market_summary": loader.load_market_summary()
    }

    # Enrich projects
    logger.info("\n[11] Enriching Projects with All Data Sources...")
    enricher = ProjectEnricher(all_data)
    projects = []

    df_base = all_data["base_projects"]
    for idx, row in df_base.iterrows():
        try:
            project = enricher.enrich_project(row, idx)
            projects.append(project)
        except Exception as e:
            logger.error(f"  Error enriching project at index {idx}: {e}")
            continue

    logger.info(f"  ✓ Successfully enriched {len(projects)} projects")

    # Create market-level enrichments
    market_enricher = MarketEnricher(all_data)
    market_enrichments = market_enricher.create_market_enrichments()

    # Create final v4 format JSON
    logger.info("\n[12] Creating Final v4 Knowledge Graph...")

    v4_data = {
        "metadata": {
            "dataVersion": "Q4_FY25_Comprehensive",
            "city": "Kolkata",
            "region": "New Town",
            "extractionDate": datetime.utcnow().isoformat(),
            "schemaVersion": "v4_nested_comprehensive",
            "source": "Kolkata_R&D_Excel_All_57_Files",
            "totalProjects": len(projects),
            "totalFilesIntegrated": len(loader.loaded_files),
            "filesIntegrated": loader.loaded_files,
            "description": "Comprehensive knowledge graph integrating all 57 Excel files"
        },

        "page_2_projects": projects,

        "market_analysis": market_enrichments,

        "enrichment_metadata": {
            "transformationType": "comprehensive_multi_source_enriched",
            "transformedAt": datetime.utcnow().isoformat(),
            "dimensions": {
                "U": "Units (count)",
                "L²": "Area (square feet)",
                "C": "Currency (Rs Lacs)",
                "C/L²": "Price per area (Rs/sqft)",
                "T": "Time (date/months/quarters/years)",
                "I": "Information (text/categorical)",
                "L": "Location (geographic)",
                "U/T": "Velocity (units per time period)"
            },
            "enrichmentCategories": {
                "baseData": "List_of_Comparables_Projects.xlsx (1 file)",
                "priceTrends": "Price trend time series (28 files)",
                "salesData": "Annual, quarterly, and construction-stage sales (7 files)",
                "inventoryStock": "Months inventory, unsold stock, velocity (4 files)",
                "analysis": "Flat type, ticket size, distance, price range (4 files)",
                "performanceMetrics": "Top 10 rankings (4 files)",
                "supplyData": "Possession-wise and quarterly supply (2 files)",
                "projectDetails": "Flatwise details, wings, catchment (3 files)",
                "marketSummary": "Quarterly and yearly summaries (2 files)"
            },
            "enrichmentFeatures": [
                "Price trend time series with benchmark comparisons",
                "Annual and quarterly sales time series",
                "Construction stage sales breakdown",
                "Inventory metrics and sales velocity",
                "Unit mix and flat type distribution",
                "Price range and size range distribution",
                "Performance rankings (top 10 lists)",
                "Wing-wise and flatwise project details",
                "Possession-wise supply distribution",
                "Market-level quarterly and annual summaries",
                "Top performer rankings across metrics",
                "Comprehensive market analysis"
            ]
        }
    }

    # Save to JSON
    logger.info(f"\n[13] Saving Comprehensive KG to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(v4_data, f, indent=2, ensure_ascii=False)

    file_size_kb = output_path.stat().st_size / 1024
    file_size_mb = file_size_kb / 1024

    logger.info(f"\n{'='*80}")
    logger.info(f"✅ SUCCESS: Comprehensive Kolkata KG Created")
    logger.info(f"{'='*80}")
    logger.info(f"Output: {output_path}")
    logger.info(f"Total Projects: {len(projects)}")
    logger.info(f"Files Integrated: {len(loader.loaded_files)} / 57")
    logger.info(f"File Size: {file_size_mb:.2f} MB ({file_size_kb:.1f} KB)")
    logger.info(f"{'='*80}\n")

    return output_path


if __name__ == "__main__":
    try:
        output_path = comprehensive_kolkata_enrichment()
        print(f"\n{'='*80}")
        print(f"SUCCESS: Comprehensive enrichment completed")
        print(f"Output: {output_path}")
        print(f"{'='*80}\n")
    except Exception as e:
        logger.error(f"❌ Comprehensive enrichment failed: {e}", exc_info=True)
        raise
