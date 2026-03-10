"""
Convert Kolkata data from flat format to v4 nested format
Converts kolkata_projects.json to v4_nested format to match Chakan data structure
"""

import json
from pathlib import Path
from datetime import datetime

# Paths
DATA_DIR = Path(__file__).parent.parent / "data" / "extracted" / "kolkata"
INPUT_FILE = DATA_DIR / "kolkata_projects.json"
OUTPUT_FILE = DATA_DIR / "kolkata_v4_format.json"

def create_v4_attribute(value, unit="count", dimension="U", source="Kolkata_Dataset", is_pure=True):
    """Create a v4 format attribute with value, unit, dimension, relationships"""
    return {
        "value": value,
        "unit": unit,
        "dimension": dimension,
        "relationships": [{"type": "IS", "target": dimension}] if dimension != "None" else [],
        "source": source,
        "isPure": is_pure
    }

def convert_flat_to_v4(flat_project):
    """Convert flat Kolkata project format to v4 nested format"""

    v4_project = {
        "projectId": create_v4_attribute(
            flat_project.get("project_id"),
            unit="Integer",
            dimension="None",
            source="Kolkata_Projects"
        ),
        "projectName": create_v4_attribute(
            flat_project.get("project_name"),
            unit="Text",
            dimension="None",
            source="Kolkata_Projects"
        ),
        "developerName": create_v4_attribute(
            flat_project.get("developer_name"),
            unit="Text",
            dimension="None",
            source="Kolkata_Projects"
        ),
        "location": create_v4_attribute(
            flat_project.get("location"),
            unit="Text",
            dimension="None",
            source="Kolkata_Projects"
        ),
        "micromarketId": create_v4_attribute(
            flat_project.get("micromarket_id", ""),
            unit="Text",
            dimension="None",
            source="Kolkata_Projects"
        ),
        "layer": create_v4_attribute(
            "L1",
            unit="Text",
            dimension="None",
            source="Kolkata_Projects"
        ),
        "nodeType": create_v4_attribute(
            "Project_L1",
            unit="Text",
            dimension="None",
            source="Kolkata_Projects"
        ),

        # Layer 0: Raw Dimensions
        "totalSupplyUnits": create_v4_attribute(
            flat_project.get("total_supply", 0),
            unit="count",
            dimension="U",
            source="Kolkata_Projects"
        ),
        "soldUnits": create_v4_attribute(
            flat_project.get("sold_units", 0),
            unit="count",
            dimension="U",
            source="Kolkata_Projects"
        ),
        "unsoldUnits": create_v4_attribute(
            flat_project.get("unsold_units", 0),
            unit="count",
            dimension="U",
            source="Kolkata_Projects"
        ),
        "annualSalesUnits": create_v4_attribute(
            flat_project.get("annual_sales_units", 0),
            unit="count/year",
            dimension="U/T",
            source="Kolkata_Projects"
        ),

        # Area (L² dimension)
        "totalSaleableArea": create_v4_attribute(
            flat_project.get("total_saleable_area", 0),
            unit="sqft",
            dimension="L²",
            source="Kolkata_Projects"
        ),
        "unsoldArea": create_v4_attribute(
            flat_project.get("unsold_area", 0),
            unit="sqft",
            dimension="L²",
            source="Kolkata_Projects"
        ),
        "unitSaleableSize": create_v4_attribute(
            flat_project.get("unit_saleable_size", 0),
            unit="sqft",
            dimension="L²",
            source="Kolkata_Projects"
        ),

        # Cash Flow (CF dimension)
        "launchPricePSF": create_v4_attribute(
            flat_project.get("launch_price_psf", 0),
            unit="₹/sqft",
            dimension="CF/L²",
            source="Kolkata_Projects"
        ),
        "currentPricePSF": create_v4_attribute(
            flat_project.get("current_price_psf", 0),
            unit="₹/sqft",
            dimension="CF/L²",
            source="Kolkata_Projects"
        ),
        "annualSalesValue": create_v4_attribute(
            flat_project.get("annual_sales_value", 0),
            unit="₹ Crores/year",
            dimension="CF/T",
            source="Kolkata_Projects"
        ),

        # Time (T dimension)
        "launchDate": create_v4_attribute(
            flat_project.get("launch_date", ""),
            unit="Text",
            dimension="None",
            source="Kolkata_Projects"
        ),
        "possessionDate": create_v4_attribute(
            flat_project.get("possession_date", ""),
            unit="Text",
            dimension="None",
            source="Kolkata_Projects"
        ),
        "projectAgeMonths": create_v4_attribute(
            flat_project.get("project_age_months", 0),
            unit="months",
            dimension="T",
            source="Kolkata_Projects"
        ),

        # Boolean flags
        "reraRegistered": create_v4_attribute(
            flat_project.get("rera_registered", False),
            unit="Boolean",
            dimension="None",
            source="Kolkata_Projects"
        ),

        # Project size
        "projectSize": create_v4_attribute(
            flat_project.get("project_size", 0),
            unit="count",
            dimension="U",
            source="Kolkata_Projects"
        ),

        # Metadata
        "extractionTimestamp": create_v4_attribute(
            datetime.now().isoformat(),
            unit="ISO-8601",
            dimension="None",
            source="Kolkata_Projects"
        )
    }

    return v4_project


def main():
    """Main conversion function"""

    print(f"Loading Kolkata data from: {INPUT_FILE}")

    # Load flat format data
    with open(INPUT_FILE, 'r') as f:
        kolkata_data = json.load(f)

    flat_projects = kolkata_data.get("data", [])
    metadata = kolkata_data.get("metadata", {})

    print(f"Found {len(flat_projects)} projects to convert")

    # Convert each project to v4 format
    v4_projects = []
    for project in flat_projects:
        v4_project = convert_flat_to_v4(project)
        v4_projects.append(v4_project)

    # Create v4 format output structure (matching Chakan structure)
    v4_output = {
        "metadata": {
            "source_file": metadata.get("source_file", "Kolkata Dataset"),
            "extraction_timestamp": datetime.now().isoformat(),
            "architecture_version": "v4.0.0",
            "data_layer": "L1",
            "description": "Kolkata project data in v4 nested format with {value, unit, dimension, relationships}",
            "city": "Kolkata",
            "state": "West Bengal",
            "total_projects": metadata.get("total_projects", len(v4_projects)),
            "converted_from": "flat_format"
        },
        "page_2_projects": v4_projects  # Use same structure as Chakan data
    }

    # Save v4 format data
    print(f"Saving v4 format data to: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(v4_output, f, indent=2)

    print(f"✅ Conversion complete!")
    print(f"   - Converted {len(v4_projects)} projects")
    print(f"   - Output file: {OUTPUT_FILE}")
    print(f"   - Format: v4_nested (matches Chakan data)")


if __name__ == "__main__":
    main()
