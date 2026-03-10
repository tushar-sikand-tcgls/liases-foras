#!/usr/bin/env python3
"""
Direct transformation of Kolkata R&D Excel data to Liases Foras v4 nested format.
Bypasses KG ETL to avoid datetime serialization issues.
"""

import pandas as pd
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_v4_attribute(
    value: Any,
    unit: str,
    dimension: str,
    description: str,
    source: str = "Kolkata_R&D_Excel"
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
        # Remove commas and convert
        return float(str(value).replace(',', ''))
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


def transform_kolkata_to_v4():
    """Transform Kolkata Excel data to v4 format"""
    logger.info("="*80)
    logger.info("KOLKATA DATA TRANSFORMATION TO V4 FORMAT")
    logger.info("="*80)

    # Input and output paths
    excel_path = "/Users/tusharsikand/Downloads/Kolkata R&D/List_of_Comparables_Projects.xlsx"
    output_dir = Path("/Users/tusharsikand/Documents/Projects/liases-foras/data/extracted/kolkata")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "kolkata_v4_format.json"

    logger.info(f"Reading Excel: {excel_path}")

    # Read Excel file
    df = pd.read_excel(excel_path, sheet_name=0)

    # The headers are in row 5 (index 5), data starts from row 6
    # Set row 5 as headers
    df.columns = df.iloc[5]
    df = df.iloc[6:].reset_index(drop=True)

    logger.info(f"Found {len(df)} projects")

    # Transform each project
    projects = []
    for idx, row in df.iterrows():
        project_id = str(row.get('Project Id', f'KOL_{idx+1:04d}'))
        project_name = str(row.get('Project Name', 'Unknown Project'))

        logger.info(f"  Processing: {project_name} (ID: {project_id})")

        # Parse cost range
        cost_min, cost_max, cost_avg = parse_range(row.get('Total Cost (Rs.Lacs)'))

        # Parse saleable size range
        saleable_min, saleable_max, saleable_avg = parse_range(row.get('Saleable Size (Sq.Ft.)'))

        # Parse carpet size range
        carpet_min, carpet_max, carpet_avg = parse_range(row.get('Carpet Size (Sq.Ft.)'))

        project = {
            "projectId": project_id,
            "projectName": project_name,

            # Location
            "location": create_v4_attribute(
                str(row.get('Location', 'Kolkata')),
                "text",
                "L",
                "Project location"
            ),

            # Developer
            "developerName": create_v4_attribute(
                str(row.get('Developer Name', 'Unknown')),
                "text",
                "I",
                "Developer name"
            ),

            # Launch Date
            "launchDate": create_v4_attribute(
                str(row.get('Launch Date', '')),
                "date",
                "T",
                "Project launch date"
            ),

            # Possession Date
            "possessionDate": create_v4_attribute(
                str(row.get('Possession Date', '')),
                "date",
                "T",
                "Expected possession date"
            ),

            # Total Supply
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

            # Sales Metrics
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

            # Flat Configuration
            "flatType": create_v4_attribute(
                str(row.get('Flat Type', '')),
                "text",
                "I",
                "Flat type configuration"
            ),

            # Price Metrics (using averages)
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

            # Rate per sq ft
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

        projects.append(project)

    # Create v4 format JSON
    v4_data = {
        "metadata": {
            "dataVersion": "Q4_FY25",
            "city": "Kolkata",
            "region": "New Town",
            "extractionDate": datetime.utcnow().isoformat(),
            "schemaVersion": "v4_nested",
            "source": "Kolkata_R&D_Excel_Direct_Transform",
            "totalProjects": len(projects)
        },
        "page_2_projects": projects,
        "enrichment_metadata": {
            "transformationType": "direct_excel_to_v4",
            "originalFile": "List_of_Comparables_Projects.xlsx",
            "transformedAt": datetime.utcnow().isoformat(),
            "dimensions": {
                "U": "Units (count)",
                "L²": "Area (square feet)",
                "C": "Currency (Rs Lacs)",
                "C/L²": "Price per area (Rs/sqft)",
                "T": "Time (date)",
                "I": "Information (text)",
                "L": "Location"
            }
        }
    }

    # Save to JSON
    logger.info(f"\nSaving to: {output_path}")
    with open(output_path, 'w') as f:
        json.dump(v4_data, f, indent=2)

    logger.info(f"✅ Successfully transformed {len(projects)} projects")
    logger.info(f"✅ Output saved to: {output_path}")

    return output_path


if __name__ == "__main__":
    try:
        output_path = transform_kolkata_to_v4()
        print(f"\n{'='*80}")
        print(f"SUCCESS: Kolkata data transformed to v4 format")
        print(f"Output: {output_path}")
        print(f"{'='*80}\n")
    except Exception as e:
        logger.error(f"❌ Transformation failed: {e}", exc_info=True)
        raise
