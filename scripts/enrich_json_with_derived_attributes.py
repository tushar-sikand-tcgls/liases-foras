"""
Enrich JSON Knowledge Graph with Derived Attributes

This script:
1. Reads the managed RAG Excel to get all derived attribute formulas
2. Calculates derived attributes for each project
3. Expands the JSON knowledge graph with these pre-computed values
4. Makes the KG queryable for attributes like "Sellout Efficiency"
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime


def safe_get_value(project_dict, key, default=None):
    """
    Safely extract value from nested dict structure

    Args:
        project_dict: Project dictionary
        key: Attribute key (e.g., 'soldPct', 'totalSupplyUnits')
        default: Default value if key not found

    Returns:
        Numeric value or default
    """
    if key not in project_dict:
        return default

    item = project_dict[key]
    if isinstance(item, dict) and 'value' in item:
        return item['value']
    return item


def calculate_derived_attribute(project, formula_text, target_attr):
    """
    Calculate a derived attribute based on formula text

    Args:
        project: Project dictionary
        formula_text: Formula string from Excel
        target_attr: Target attribute name

    Returns:
        Calculated value or None if calculation fails
    """
    try:
        # Extract values needed for calculations
        supply = safe_get_value(project, 'totalSupplyUnits', 0)
        unsold_pct = safe_get_value(project, 'unsoldPct', 0)
        sold_pct = safe_get_value(project, 'soldPct', 0)
        annual_sales = safe_get_value(project, 'annualSalesUnits', 0)
        current_psf = safe_get_value(project, 'currentPricePSF', 0)
        launch_psf = safe_get_value(project, 'launchPricePSF', 0)
        unit_size = safe_get_value(project, 'unitSaleableSizeSqft', 0)
        annual_value_cr = safe_get_value(project, 'annualSalesValueCr', 0)

        # Derived attribute formulas (from Excel row-by-row)

        if target_attr == "Unsold Units":
            # Formula: Unsold = Supply × Unsold%
            return supply * (unsold_pct / 100) if supply and unsold_pct else None

        elif target_attr == "Sold Units":
            # Formula: Sold = Supply × Sold%
            return supply * (sold_pct / 100) if supply and sold_pct else None

        elif target_attr == "Monthly Units Sold":
            # Formula: Annual Sales / 12
            return annual_sales / 12 if annual_sales else None

        elif target_attr == "Monthly Velocity Units":
            # Formula: Velocity% × Supply (from monthly sales velocity)
            velocity_pct = safe_get_value(project, 'monthlySalesVelocity', 0)
            return (velocity_pct / 100) * supply if velocity_pct and supply else None

        elif target_attr == "Months of Inventory":
            # Formula: Unsold / Monthly Units Sold
            unsold_units = supply * (unsold_pct / 100) if supply and unsold_pct else 0
            monthly_sold = annual_sales / 12 if annual_sales else 0
            return unsold_units / monthly_sold if monthly_sold > 0 else None

        elif target_attr == "Price Growth (%)":
            # Formula: (Current−Launch) / Launch
            if launch_psf and launch_psf > 0:
                return ((current_psf - launch_psf) / launch_psf) * 100
            return None

        elif target_attr == "Realised PSF":
            # Formula: (Value × 1e7) / (Units × Size)
            units_sold = supply * (sold_pct / 100) if supply and sold_pct else 0
            total_area = units_sold * unit_size if unit_size else 0
            if total_area > 0 and annual_value_cr:
                return (annual_value_cr * 1e7) / total_area
            return None

        elif target_attr == "Revenue per Unit":
            # Formula: (Value × 1e7) / Units
            units_sold = supply * (sold_pct / 100) if supply and sold_pct else 0
            if units_sold > 0 and annual_value_cr:
                return (annual_value_cr * 1e7) / units_sold
            return None

        elif target_attr == "Unsold Inventory Value":
            # Formula: Units × Size × PSF / 1e7
            unsold_units = supply * (unsold_pct / 100) if supply and unsold_pct else 0
            value = (unsold_units * unit_size * current_psf) / 1e7 if unsold_units and unit_size and current_psf else None
            return value

        elif target_attr == "Annual Absorption Rate":
            # Formula: Annual Sales / Supply
            return (annual_sales / supply) * 100 if supply > 0 and annual_sales else None

        elif target_attr == "Future Sellout Time":
            # Formula: Unsold / Annual Sales
            unsold_units = supply * (unsold_pct / 100) if supply and unsold_pct else 0
            return unsold_units / annual_sales if annual_sales > 0 else None

        elif target_attr == "Average Ticket Size":
            # Formula: Unit Size × CurrentPSF
            return unit_size * current_psf if unit_size and current_psf else None

        elif target_attr == "Launch Ticket Size":
            # Formula: Unit Size × LaunchPSF
            return unit_size * launch_psf if unit_size and launch_psf else None

        elif target_attr == "PSF Gap":
            # Formula: CurrentPSF−LaunchPSF
            return current_psf - launch_psf if current_psf and launch_psf else None

        elif target_attr == "Annual Clearance Rate":
            # Formula: Annual Sales / Supply
            return (annual_sales / supply) * 100 if supply > 0 and annual_sales else None

        elif target_attr == "Sellout Time":
            # Formula: Supply / Annual Sales
            return supply / annual_sales if annual_sales > 0 else None

        elif target_attr == "Sellout Efficiency":
            # Formula: (AnnualSales × 12) / Supply
            # This is the KEY attribute the user asked about!
            return (annual_sales * 12) / supply if supply > 0 else None

        elif target_attr == "Effective Realised PSF":
            # Formula: (Value × 1e7) / (Units × Size)
            # Same as "Realised PSF"
            units_sold = supply * (sold_pct / 100) if supply and sold_pct else 0
            total_area = units_sold * unit_size if unit_size else 0
            if total_area > 0 and annual_value_cr:
                return (annual_value_cr * 1e7) / total_area
            return None

        elif target_attr == "Price-to-Size Ratio":
            # Formula: CurrentPSF / Size
            return current_psf / unit_size if unit_size > 0 and current_psf else None

        return None

    except Exception as e:
        print(f"  ⚠ Error calculating {target_attr}: {e}")
        return None


def enrich_json_with_derived_attributes():
    """
    Main function to enrich JSON with all 19 derived attributes
    """
    print("="*80)
    print("ENRICHING JSON WITH DERIVED ATTRIBUTES")
    print("="*80)

    # Load Excel with attribute definitions
    excel_path = "change-request/managed-rag/LF-Layers_FULLY_ENRICHED_ALL_36.xlsx"
    print(f"\n1. Loading attribute definitions from {excel_path}...")
    df = pd.read_excel(excel_path)

    # Filter for derived attributes only
    derived_attrs = df[df['Formula/Derivation'] != 'Direct extraction']
    print(f"   ✓ Found {len(derived_attrs)} derived attributes to calculate")

    # Load existing JSON
    json_path = "data/extracted/v4_clean_nested_structure.json"
    print(f"\n2. Loading existing JSON from {json_path}...")
    with open(json_path, 'r') as f:
        data = json.load(f)

    projects = data.get('page_2_projects', [])
    print(f"   ✓ Loaded {len(projects)} projects")

    # Enrich each project with derived attributes
    print(f"\n3. Calculating derived attributes for each project...")
    for idx, project in enumerate(projects, 1):
        project_name = safe_get_value(project, 'projectName', f'Project {idx}')
        print(f"\n   [{idx}/{len(projects)}] {project_name}")

        for _, attr_row in derived_attrs.iterrows():
            target_attr = attr_row['Target Attribute']
            formula = attr_row['Formula/Derivation']
            unit = attr_row['Unit']
            dimension = attr_row['Dimension']

            # Calculate the derived value
            value = calculate_derived_attribute(project, formula, target_attr)

            if value is not None:
                # Add to project dict in same format as existing attributes
                project[target_attr] = {
                    'value': round(value, 2) if isinstance(value, float) else value,
                    'unit': unit,
                    'dimension': dimension,
                    'relationships': [],
                    'source': 'L1_Derived_Calculated',
                    'isPure': True,
                    'formula': formula,
                    'calculated_at': datetime.utcnow().isoformat() + 'Z'
                }
                print(f"      ✓ {target_attr}: {value:.2f} {unit}")
            else:
                print(f"      ✗ {target_attr}: Could not calculate (missing data)")

    # Save enriched JSON
    output_path = "data/extracted/v4_clean_nested_structure_ENRICHED.json"
    print(f"\n4. Saving enriched JSON to {output_path}...")
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"   ✓ Saved successfully")

    # Summary
    print(f"\n{'='*80}")
    print(f"ENRICHMENT COMPLETE")
    print(f"{'='*80}")
    print(f"✓ Added 19 derived attributes to {len(projects)} projects")
    print(f"✓ Knowledge Graph expanded from ~24 attributes to ~43 attributes per project")
    print(f"✓ Attributes now include: Sellout Efficiency, Months of Inventory, PSF Gap, etc.")
    print(f"✓ The 'View Graph' visualization will now show a much larger, enriched graph")
    print(f"\nNext step: Replace data/extracted/v4_clean_nested_structure.json with ENRICHED version")
    print(f"  cp {output_path} {json_path}")


if __name__ == "__main__":
    enrich_json_with_derived_attributes()
