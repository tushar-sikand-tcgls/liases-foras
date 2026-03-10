#!/usr/bin/env python3
"""
Enriched Knowledge Graph Transformation for Kolkata R&D Data

Combines multiple Excel sources to create a comprehensive knowledge graph:
1. Base project data (List_of_Comparables_Projects.xlsx)
2. Flat type analysis (unit mix breakdown)
3. Unit ticket size analysis (price range distribution)
4. Distance range analysis (geographic segmentation)
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
    source: str = "Kolkata_R&D_Excel_Enriched"
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


def load_excel_with_auto_header(filepath: Path, max_search=20) -> Optional[pd.DataFrame]:
    """Load Excel file by auto-detecting header row"""
    for skip in range(max_search):
        try:
            df = pd.read_excel(filepath, header=skip)
            # Check if we have valid column names
            valid_cols = [col for col in df.columns if not (pd.isna(col) or str(col).startswith('Unnamed'))]
            if len(valid_cols) >= 3:
                logger.info(f"  Header found at row {skip}")
                return df
        except:
            continue
    logger.warning(f"  Could not find valid header in {filepath.name}")
    return None


def enrich_kolkata_kg():
    """Transform and enrich Kolkata data to v4 format"""
    logger.info("="*80)
    logger.info("ENRICHED KOLKATA KNOWLEDGE GRAPH TRANSFORMATION")
    logger.info("="*80)

    # Paths
    base_dir = Path("/Users/tusharsikand/Downloads/Kolkata R&D")
    output_dir = Path("/Users/tusharsikand/Documents/Projects/liases-foras/data/extracted/kolkata")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "kolkata_v4_enriched.json"

    # Load base project data
    logger.info("\n[1] Loading base project data...")
    base_file = base_dir / "List_of_Comparables_Projects.xlsx"
    df_base = pd.read_excel(base_file, sheet_name=0)
    df_base.columns = df_base.iloc[5]
    df_base = df_base.iloc[6:].reset_index(drop=True)
    logger.info(f"  ✓ Loaded {len(df_base)} base projects")

    # Load flat type analysis
    logger.info("\n[2] Loading flat type analysis (unit mix)...")
    flat_type_file = base_dir / "Flat_Type_Analysis_Data (2).xlsx"
    df_flat_types = load_excel_with_auto_header(flat_type_file)
    logger.info(f"  ✓ Loaded {len(df_flat_types)} flat type records") if df_flat_types is not None else None

    # Load unit ticket size analysis
    logger.info("\n[3] Loading unit ticket size analysis (price ranges)...")
    ticket_size_file = base_dir / "Unit_Ticket_Size_Analysis_Data (1).xlsx"
    df_ticket_size = load_excel_with_auto_header(ticket_size_file)
    logger.info(f"  ✓ Loaded {len(df_ticket_size)} price range records") if df_ticket_size is not None else None

    # Load distance range analysis
    logger.info("\n[4] Loading distance range analysis (geographic)...")
    distance_file = base_dir / "Distance_Range_Analysis_Data (4).xlsx"
    df_distance = load_excel_with_auto_header(distance_file)
    logger.info(f"  ✓ Loaded {len(df_distance)} distance range projects") if df_distance is not None else None

    # Transform projects with enrichments
    logger.info("\n[5] Transforming and enriching projects...")
    projects = []

    for idx, row in df_base.iterrows():
        project_id = str(row.get('Project Id', f'KOL_{idx+1:04d}'))
        project_name = str(row.get('Project Name', 'Unknown Project'))

        logger.info(f"  Processing: {project_name} (ID: {project_id})")

        # Parse cost range
        cost_min, cost_max, cost_avg = parse_range(row.get('Total Cost (Rs.Lacs)'))

        # Parse saleable size range
        saleable_min, saleable_max, saleable_avg = parse_range(row.get('Saleable Size (Sq.Ft.)'))

        # Parse carpet size range
        carpet_min, carpet_max, carpet_avg = parse_range(row.get('Carpet Size (Sq.Ft.)'))

        # Base project attributes
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

            # Price Metrics
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

        # ENRICHMENT: Add unit mix breakdown
        if df_flat_types is not None:
            flat_type_breakdown = []
            for _, ft_row in df_flat_types.iterrows():
                flat_type_breakdown.append({
                    "flatType": create_v4_attribute(
                        str(ft_row.get('Flat', '')),
                        "text",
                        "I",
                        "Unit type"
                    ),
                    "saleableMinSize": create_v4_attribute(
                        parse_number(ft_row.get('Saleable Min Size')),
                        "sqft",
                        "L²",
                        "Minimum saleable area"
                    ),
                    "saleableMaxSize": create_v4_attribute(
                        parse_number(ft_row.get('Saleable Max Size')),
                        "sqft",
                        "L²",
                        "Maximum saleable area"
                    ),
                    "minCost": create_v4_attribute(
                        parse_number(ft_row.get('Min Cost(Rs.Lacs)')),
                        "lacs",
                        "C",
                        "Minimum cost"
                    ),
                    "maxCost": create_v4_attribute(
                        parse_number(ft_row.get('Max Cost(Rs.Lacs)')),
                        "lacs",
                        "C",
                        "Maximum cost"
                    ),
                    "annualSalesUnits": create_v4_attribute(
                        parse_number(ft_row.get('Annual Sales (Units)')),
                        "count",
                        "U",
                        "Annual sales units for this flat type"
                    ),
                    "unsoldUnits": create_v4_attribute(
                        parse_number(ft_row.get('Unsold (Units)')),
                        "count",
                        "U",
                        "Unsold units for this flat type"
                    ),
                    "productEfficiency": create_v4_attribute(
                        parse_number(ft_row.get('Product Efficiency (%)')),
                        "percent",
                        "U",
                        "Product efficiency percentage"
                    )
                })

            project["unitMixBreakdown"] = {
                "value": flat_type_breakdown,
                "unit": "list",
                "dimension": "I",
                "description": "Detailed unit mix breakdown by flat type",
                "source": "Flat_Type_Analysis_Data",
                "isPure": False,
                "relationships": [{"type": "HAS_MANY", "target": "flatType"}]
            }

        # ENRICHMENT: Add price range distribution
        if df_ticket_size is not None:
            price_distribution = []
            for _, ts_row in df_ticket_size.iterrows():
                price_distribution.append({
                    "priceRange": create_v4_attribute(
                        str(ts_row.get('Costrange', '')),
                        "text",
                        "C",
                        "Price range bucket"
                    ),
                    "annualSalesUnits": create_v4_attribute(
                        parse_number(ts_row.get('Annual Sales (Units)')),
                        "count",
                        "U",
                        "Annual sales in this price range"
                    ),
                    "unsoldUnits": create_v4_attribute(
                        parse_number(ts_row.get('Unsold (Units)')),
                        "count",
                        "U",
                        "Unsold units in this price range"
                    ),
                    "monthsInventory": create_v4_attribute(
                        parse_number(ts_row.get('Annual Months Inventory')),
                        "months",
                        "T",
                        "Months of inventory for this price range"
                    ),
                    "monthlySalesVelocity": create_v4_attribute(
                        parse_number(ts_row.get('Monthly Sales Velocity (%)')),
                        "percent",
                        "U/T",
                        "Monthly sales velocity"
                    )
                })

            project["priceRangeDistribution"] = {
                "value": price_distribution,
                "unit": "list",
                "dimension": "C",
                "description": "Price range distribution analysis",
                "source": "Unit_Ticket_Size_Analysis_Data",
                "isPure": False,
                "relationships": [{"type": "DISTRIBUTED_BY", "target": "priceRange"}]
            }

        projects.append(project)

    # Create market-level enrichments
    logger.info("\n[6] Creating market-level enrichments...")
    market_analysis = {}

    if df_flat_types is not None:
        market_analysis["unitMixSummary"] = {
            "totalFlatTypes": len(df_flat_types),
            "flatTypes": df_flat_types['Flat'].tolist() if 'Flat' in df_flat_types.columns else []
        }

    if df_ticket_size is not None:
        market_analysis["priceRangeSummary"] = {
            "totalPriceRanges": len(df_ticket_size),
            "priceRanges": df_ticket_size['Costrange'].tolist() if 'Costrange' in df_ticket_size.columns else []
        }

    # Create v4 format JSON
    v4_data = {
        "metadata": {
            "dataVersion": "Q4_FY25_Enriched",
            "city": "Kolkata",
            "region": "New Town",
            "extractionDate": datetime.utcnow().isoformat(),
            "schemaVersion": "v4_nested_enriched",
            "source": "Kolkata_R&D_Excel_Multi_Source_Enriched",
            "totalProjects": len(projects),
            "enrichmentSources": [
                "List_of_Comparables_Projects.xlsx",
                "Flat_Type_Analysis_Data (2).xlsx",
                "Unit_Ticket_Size_Analysis_Data (1).xlsx",
                "Distance_Range_Analysis_Data (4).xlsx"
            ]
        },
        "page_2_projects": projects,
        "market_analysis": market_analysis,
        "enrichment_metadata": {
            "transformationType": "multi_source_enriched_excel_to_v4",
            "transformedAt": datetime.utcnow().isoformat(),
            "dimensions": {
                "U": "Units (count)",
                "L²": "Area (square feet)",
                "C": "Currency (Rs Lacs)",
                "C/L²": "Price per area (Rs/sqft)",
                "T": "Time (date/months)",
                "I": "Information (text)",
                "L": "Location",
                "U/T": "Velocity (units per time)"
            },
            "enrichments": {
                "unitMixBreakdown": "Detailed breakdown by flat type (1RK, 1BHK, 2BHK, etc.)",
                "priceRangeDistribution": "Sales and inventory distribution across price ranges",
                "geographicSegmentation": "Distance-based market segmentation"
            }
        }
    }

    # Save to JSON
    logger.info(f"\n[7] Saving enriched KG to: {output_path}")
    with open(output_path, 'w') as f:
        json.dump(v4_data, f, indent=2)

    logger.info(f"\n✅ Successfully transformed {len(projects)} projects with enrichments")
    logger.info(f"✅ Output saved to: {output_path}")
    logger.info(f"✅ File size: {output_path.stat().st_size / 1024:.1f} KB")

    return output_path


if __name__ == "__main__":
    try:
        output_path = enrich_kolkata_kg()
        print(f"\n{'='*80}")
        print(f"SUCCESS: Enriched Kolkata KG created")
        print(f"Output: {output_path}")
        print(f"{'='*80}\n")
    except Exception as e:
        logger.error(f"❌ Transformation failed: {e}", exc_info=True)
        raise
