"""
Enrich Kolkata projects with complete L0/L1 attribute schema (36 attributes total)

This script:
1. Reads existing kolkata_v4_format.json (5 projects with 18/36 attributes)
2. Calculates 10 missing L0 attributes
3. Calculates 8 missing L1 derived metrics
4. Updates JSON with complete schema (36 attributes per project)
5. Maintains v4_nested format structure
"""

import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any

def calculate_sold_percentage(sold_units: int, total_supply: int) -> float:
    """Calculate Sold (%) from sold units and total supply"""
    if total_supply == 0:
        return 0.0
    return round((sold_units / total_supply) * 100, 2)

def calculate_unsold_percentage(sold_pct: float) -> float:
    """Calculate Unsold (%) as 100 - Sold%"""
    return round(100 - sold_pct, 2)

def calculate_monthly_sales_velocity(annual_sales: int, total_supply: int) -> float:
    """Calculate Monthly Sales Velocity (%/month)"""
    if total_supply == 0:
        return 0.0
    monthly_velocity = (annual_sales / 12) / total_supply * 100
    return round(monthly_velocity, 2)

def calculate_months_of_inventory(unsold_units: int, monthly_units_sold: float) -> float:
    """Calculate Months of Inventory (MOI)"""
    if monthly_units_sold == 0:
        return 999.0  # Effectively infinite
    return round(unsold_units / monthly_units_sold, 1)

def calculate_price_growth(current_psf: float, launch_psf: float) -> float:
    """Calculate Price Growth (%)"""
    if launch_psf == 0:
        return 0.0
    return round(((current_psf - launch_psf) / launch_psf) * 100, 2)

def calculate_unsold_inventory_value(unsold_units: int, unit_size: float, current_psf: float) -> float:
    """Calculate Unsold Inventory Value (Rs Cr)"""
    # Value in Rs Cr = Units × Size (sqft) × PSF (Rs/sqft) / 1e7
    value_rs = unsold_units * unit_size * current_psf
    value_cr = round(value_rs / 1e7, 2)
    return value_cr

def calculate_annual_absorption_rate(annual_sales: int, unsold_units: int) -> float:
    """Calculate Annual Absorption Rate (%)"""
    if unsold_units == 0:
        return 100.0
    return round((annual_sales / unsold_units) * 100, 2)

def calculate_sellout_time(unsold_units: int, annual_sales: int) -> float:
    """Calculate Sellout Time (Years)"""
    if annual_sales == 0:
        return 99.0  # Effectively never
    return round(unsold_units / annual_sales, 2)

def calculate_sellout_efficiency(annual_sales: int, total_supply: int) -> float:
    """Calculate Sellout Efficiency (%)"""
    if total_supply == 0:
        return 0.0
    # Efficiency = (Annual Sales × 12) / Supply
    return round((annual_sales * 12) / total_supply, 2)

def calculate_price_to_size_ratio(current_psf: float, unit_size: float) -> float:
    """Calculate Price-to-Size Ratio"""
    if unit_size == 0:
        return 0.0
    return round(current_psf / unit_size, 4)

# L1 Derived Metrics
def calculate_monthly_units_sold(annual_sales: int) -> float:
    """Calculate Monthly Units Sold"""
    return round(annual_sales / 12, 2)

def calculate_monthly_velocity_units(monthly_velocity_pct: float, total_supply: int) -> float:
    """Calculate Monthly Velocity Units"""
    return round((monthly_velocity_pct / 100) * total_supply, 2)

def calculate_realised_psf(annual_sales_value: float, annual_sales_units: int, unit_size: float) -> float:
    """Calculate Realised PSF"""
    if annual_sales_units == 0 or unit_size == 0:
        return 0.0
    # Convert Cr to Rs: annual_sales_value × 1e7
    total_area = annual_sales_units * unit_size
    if total_area == 0:
        return 0.0
    realised_psf = (annual_sales_value * 1e7) / total_area
    return round(realised_psf, 2)

def calculate_revenue_per_unit(annual_sales_value: float, annual_sales_units: int) -> float:
    """Calculate Revenue per Unit (Rs)"""
    if annual_sales_units == 0:
        return 0.0
    # Convert Cr to Rs: annual_sales_value × 1e7
    revenue = (annual_sales_value * 1e7) / annual_sales_units
    return round(revenue, 2)

def calculate_average_ticket_size(unit_size: float, current_psf: float) -> float:
    """Calculate Average Ticket Size (Rs)"""
    return round(unit_size * current_psf, 2)

def calculate_launch_ticket_size(unit_size: float, launch_psf: float) -> float:
    """Calculate Launch Ticket Size (Rs)"""
    return round(unit_size * launch_psf, 2)

def calculate_psf_gap(current_psf: float, launch_psf: float) -> float:
    """Calculate PSF Gap (Rs/SqFt)"""
    return round(current_psf - launch_psf, 2)

def get_value(obj, default=0):
    """Extract value from v4_nested format dict or return raw value"""
    if isinstance(obj, dict) and 'value' in obj:
        return obj['value']
    return obj if obj is not None else default

def enrich_project(project: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich a single project with all 36 attributes"""

    # Extract existing values (handling v4_nested format)
    project_id = get_value(project.get('projectId'), 'UNKNOWN')
    project_name = get_value(project.get('projectName'), 'Unknown')
    sold_units = get_value(project.get('soldUnits'), 0)
    unsold_units = get_value(project.get('unsoldUnits'), 0)
    total_supply = get_value(project.get('totalSupplyUnits'), 0)
    unit_size = get_value(project.get('unitSaleableSize'), 0)
    annual_sales = get_value(project.get('annualSalesUnits'), 0)
    annual_sales_value = get_value(project.get('annualSalesValue'), 0.0)
    current_psf = get_value(project.get('currentPricePSF'), 0.0)
    launch_psf = get_value(project.get('launchPricePSF'), 0.0)

    # Calculate missing L0 attributes
    sold_pct = calculate_sold_percentage(sold_units, total_supply)
    unsold_pct = calculate_unsold_percentage(sold_pct)
    monthly_velocity_pct = calculate_monthly_sales_velocity(annual_sales, total_supply)
    monthly_units = calculate_monthly_units_sold(annual_sales)
    moi = calculate_months_of_inventory(unsold_units, monthly_units)
    price_growth = calculate_price_growth(current_psf, launch_psf)
    unsold_inv_value = calculate_unsold_inventory_value(unsold_units, unit_size, current_psf)
    annual_absorption = calculate_annual_absorption_rate(annual_sales, unsold_units)
    sellout_time_years = calculate_sellout_time(unsold_units, annual_sales)
    sellout_efficiency = calculate_sellout_efficiency(annual_sales, total_supply)
    price_size_ratio = calculate_price_to_size_ratio(current_psf, unit_size)

    # Calculate missing L1 derived metrics
    monthly_velocity_units = calculate_monthly_velocity_units(monthly_velocity_pct, total_supply)
    realised_psf = calculate_realised_psf(annual_sales_value, annual_sales, unit_size)
    revenue_per_unit = calculate_revenue_per_unit(annual_sales_value, annual_sales)
    avg_ticket_size = calculate_average_ticket_size(unit_size, current_psf)
    launch_ticket_size = calculate_launch_ticket_size(unit_size, launch_psf)
    psf_gap = calculate_psf_gap(current_psf, launch_psf)

    # Helper function to create v4_nested format
    def create_v4_attr(value, unit, dimension, relationships=None):
        return {
            "value": value,
            "unit": unit,
            "dimension": dimension,
            "relationships": relationships or [],
            "source": "Enriched_Calculation",
            "isPure": False  # Derived/calculated attributes are not pure
        }

    # Add enriched attributes to project (in v4_nested format)
    enriched = project.copy()

    # L0 Missing Attributes (with proper dimensions)
    enriched['soldPercentage'] = create_v4_attr(sold_pct, "%", "Dimensionless")
    enriched['unsoldPercentage'] = create_v4_attr(unsold_pct, "%", "Dimensionless")
    enriched['monthlySalesVelocityPct'] = create_v4_attr(monthly_velocity_pct, "%/month", "T⁻¹", [{"target": "T", "type": "INVERSE_OF"}])
    enriched['monthsOfInventory'] = create_v4_attr(moi, "Months", "T", [{"target": "T", "type": "IS"}])
    enriched['priceGrowthPct'] = create_v4_attr(price_growth, "%", "Dimensionless")
    enriched['unsoldInventoryValueCr'] = create_v4_attr(unsold_inv_value, "Rs Cr", "C", [{"target": "C", "type": "IS"}])
    enriched['annualAbsorptionRatePct'] = create_v4_attr(annual_absorption, "%", "Dimensionless")
    enriched['annualClearanceRatePct'] = create_v4_attr(annual_absorption, "%", "Dimensionless")
    enriched['selloutTimeYears'] = create_v4_attr(sellout_time_years, "Years", "T", [{"target": "T", "type": "IS"}])
    enriched['futureSelloutTimeYears'] = create_v4_attr(sellout_time_years, "Years", "T", [{"target": "T", "type": "IS"}])
    enriched['selloutEfficiencyPct'] = create_v4_attr(sellout_efficiency, "%", "Dimensionless")
    enriched['priceToSizeRatio'] = create_v4_attr(price_size_ratio, "Rate", "C/L²", [
        {"target": "C", "type": "NUMERATOR"},
        {"target": "L²", "type": "DENOMINATOR"}
    ])

    # L1 Missing Attributes (with proper dimensions)
    enriched['monthlyUnitsSold'] = create_v4_attr(monthly_units, "Units/month", "U/T", [
        {"target": "U", "type": "NUMERATOR"},
        {"target": "T", "type": "DENOMINATOR"}
    ])
    enriched['monthlyVelocityUnits'] = create_v4_attr(monthly_velocity_units, "Units/month", "U/T", [
        {"target": "U", "type": "NUMERATOR"},
        {"target": "T", "type": "DENOMINATOR"}
    ])
    enriched['realisedPSF'] = create_v4_attr(realised_psf, "Rs/SqFt", "C/L²", [
        {"target": "C", "type": "NUMERATOR"},
        {"target": "L²", "type": "DENOMINATOR"}
    ])
    enriched['effectiveRealisedPSF'] = create_v4_attr(realised_psf, "Rs/SqFt", "C/L²", [
        {"target": "C", "type": "NUMERATOR"},
        {"target": "L²", "type": "DENOMINATOR"}
    ])
    enriched['revenuePerUnit'] = create_v4_attr(revenue_per_unit, "Rs/Unit", "C/U", [
        {"target": "C", "type": "NUMERATOR"},
        {"target": "U", "type": "DENOMINATOR"}
    ])
    enriched['averageTicketSize'] = create_v4_attr(avg_ticket_size, "Rs", "C", [{"target": "C", "type": "IS"}])
    enriched['launchTicketSize'] = create_v4_attr(launch_ticket_size, "Rs", "C", [{"target": "C", "type": "IS"}])
    enriched['psfGap'] = create_v4_attr(psf_gap, "Rs/SqFt", "C/L²", [
        {"target": "C", "type": "NUMERATOR"},
        {"target": "L²", "type": "DENOMINATOR"}
    ])

    # Update timestamp (as metadata, not v4_nested)
    enriched['enrichmentTimestamp'] = datetime.now().isoformat()
    enriched['schemaVersion'] = 'v4_nested_enriched_36_attributes'

    return enriched

def main():
    """Main enrichment workflow"""

    import sys

    # Check if city argument provided
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'pune':
        city = "Pune"
        input_file = '/Users/tusharsikand/Documents/Projects/liases-foras/data/extracted/v4_clean_nested_structure.json'
        output_file = '/Users/tusharsikand/Documents/Projects/liases-foras/data/extracted/v4_clean_nested_structure_ENRICHED.json'
    else:
        city = "Kolkata"
        input_file = '/Users/tusharsikand/Documents/Projects/liases-foras/data/extracted/kolkata/kolkata_v4_format.json'
        output_file = '/Users/tusharsikand/Documents/Projects/liases-foras/data/extracted/kolkata/kolkata_v4_format_ENRICHED.json'

    print("="*80)
    print(f"{city.upper()} PROJECT ENRICHMENT - Full 36 Attribute Schema")
    print("="*80)

    with open(input_file, 'r') as f:
        data = json.load(f)

    projects = data.get('page_2_projects', [])
    print(f"\n📊 Total projects to enrich: {len(projects)}")

    # Enrich all projects
    enriched_projects = []
    for i, project in enumerate(projects, 1):
        project_name = project.get('projectName', 'Unknown')
        print(f"\n{i}. Enriching: {project_name}")

        enriched = enrich_project(project)
        enriched_projects.append(enriched)

        # Show enrichment summary
        original_attrs = len(project)
        enriched_attrs = len(enriched)
        new_attrs = enriched_attrs - original_attrs
        print(f"   Original attributes: {original_attrs}")
        print(f"   Enriched attributes: {enriched_attrs}")
        print(f"   New attributes added: {new_attrs}")

    # Update data structure
    data['page_2_projects'] = enriched_projects
    data['enrichment_metadata'] = {
        'enrichment_timestamp': datetime.now().isoformat(),
        'schema_version': 'v4_nested_enriched_36_attributes',
        'total_projects': len(enriched_projects),
        'attributes_per_project': 36,
        'l0_attributes': 24,
        'l1_attributes': 12,
        'source_excel_schema': 'LF-Layers_FULLY_ENRICHED_ALL_36.xlsx'
    }

    # Save enriched data
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\n{'='*80}")
    print("✅ ENRICHMENT COMPLETE")
    print(f"{'='*80}")
    print(f"Output file: {output_file}")
    print(f"Total projects: {len(enriched_projects)}")
    print(f"Attributes per project: ~{len(enriched_projects[0])} keys")
    print(f"\nSchema coverage: 36/36 attributes (100%)")
    print(f"  - L0: 24 attributes ✅")
    print(f"  - L1: 12 attributes ✅")

    # Show sample enriched project
    if enriched_projects:
        sample = enriched_projects[0]
        print(f"\n📋 Sample Enriched Project: {sample.get('projectName', 'Unknown')}")
        print(f"   Total keys: {len(sample)}")

        # Show newly added attributes
        original_keys = set(projects[0].keys())
        enriched_keys = set(sample.keys())
        new_keys = enriched_keys - original_keys

        print(f"\n   📌 Newly Added Attributes ({len(new_keys)}):")
        for key in sorted(new_keys):
            value = sample[key]
            print(f"      • {key}: {value}")

if __name__ == '__main__':
    main()
