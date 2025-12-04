"""
V4.0.0: PDF Data Extraction with Nested Structure
==================================================

Extracts data from GetMicromarketPdf.pdf directly into nested {value, unit, dimension} format
with explicit dimensional relationships (Numerator, Denominator, Is).

Key Changes from v3:
- OUTPUT: Fully nested structure (no l1_attributes wrapper)
- ADDED: Explicit dimensional relationships for each attribute
- REMOVED: Flat attribute lists
- Each attribute: {value, unit, dimension, relationships, source, isPure}

Architecture:
- L0 = Base dimensions (U, L², T, C) - conceptual, not stored
- L1 = This script's output - nested attributes with explicit relationships
- L2 = Financial metrics (calculated later)
- L3 = Optimization solutions (generated later)
"""

import pdfplumber
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add scripts directory to path for dimension_parser
sys.path.append(str(Path(__file__).parent))
from dimension_parser import DimensionParser


class V4NestedPDFExtractor:
    """Extract data from PDF directly into nested format with explicit dimensional relationships"""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.parser = DimensionParser()
        self.extracted_data = {
            "metadata": {
                "source_file": pdf_path,
                "extraction_timestamp": datetime.now().isoformat(),
                "architecture_version": "v4.0.0",
                "data_layer": "L1",
                "description": "Nested {value, unit, dimension} with explicit relationships",
                "extraction_priority": {
                    "page_2": {"weight": 10, "description": "Top 10 Projects"},
                    "page_5": {"weight": 9, "description": "Unit Type Analysis"},
                    "page_8": {"weight": 8, "description": "Quarterly Market Summary"}
                }
            },
            "page_2_projects": [],
            "page_5_unit_types": [],
            "page_8_quarterly_summary": []
        }

    def create_nested_attribute(self, value, unit: str, dimension: str, source: str = "LF_PDF", is_pure: bool = True) -> Dict:
        """
        Create a nested attribute with explicit dimensional relationships

        Args:
            value: The actual value
            unit: Unit of measurement
            dimension: Dimensional formula (e.g., "U", "C/L²", "1/T")
            source: Data source
            is_pure: True if single dimension, False if composite

        Returns:
            {
                "value": value,
                "unit": unit,
                "dimension": dimension,
                "relationships": [{type, target}, ...],
                "source": source,
                "isPure": is_pure
            }
        """
        # Parse dimension to get explicit relationships
        relationships = self.parser.parse_dimension(dimension)

        return {
            "value": value,
            "unit": unit,
            "dimension": dimension,
            "relationships": relationships,
            "source": source,
            "isPure": is_pure
        }

    def clean_numeric(self, value: str):
        """
        Clean and convert numeric values from PDF text

        Returns:
            - Integer if value is whole number (no decimal point)
            - Float if value has decimal point
            - Percentages kept as-is (not converted to fractions)
        """
        if not value or value == '-':
            return None

        cleaned = str(value).replace(',', '').replace(' ', '').strip()

        # Handle percentages - keep as percentage values, don't convert to fractions
        if '%' in cleaned:
            cleaned = cleaned.replace('%', '')
            try:
                num = float(cleaned)
                # Return integer if whole number, else float
                return int(num) if num.is_integer() else num
            except:
                return None

        try:
            num = float(cleaned)
            # Return integer if whole number, else float
            return int(num) if num.is_integer() else num
        except:
            return None

    def extract_page_2_top_projects(self, pdf) -> List[Dict]:
        """
        Extract Page 2: Top 10 Projects Table (Priority Weight 10/10)

        Output: Fully nested structure with explicit dimensional relationships
        """
        print("Extracting Page 2: Top 10 Projects (Weight 10/10)...")

        projects = []

        try:
            page = pdf.pages[1]  # Page 2 (0-indexed)
            tables = page.extract_tables()

            if not tables:
                print("  ⚠️  No tables found on Page 2")
                return projects

            main_table = max(tables, key=lambda t: len(t))

            for row_idx, row in enumerate(main_table[1:], 1):  # Skip header
                if not row or len(row) < 10:
                    continue

                try:
                    # Create project with fully nested structure
                    project = {}

                    # Basic metadata (non-dimensional)
                    if len(row) > 0 and row[0]:  # Project ID
                        project["projectId"] = self.create_nested_attribute(
                            value=self.clean_numeric(row[0]),
                            unit="Integer",
                            dimension="None",
                            source="LF_PDF_Page2",
                            is_pure=True
                        )

                    if len(row) > 1 and row[1]:  # Project Name
                        project["projectName"] = self.create_nested_attribute(
                            value=row[1],
                            unit="Text",
                            dimension="None",
                            source="LF_PDF_Page2",
                            is_pure=True
                        )

                    if len(row) > 2 and row[2]:  # Developer Name
                        project["developerName"] = self.create_nested_attribute(
                            value=row[2],
                            unit="Text",
                            dimension="None",
                            source="LF_PDF_Page2",
                            is_pure=True
                        )

                    if len(row) > 3 and row[3]:  # Location
                        project["location"] = self.create_nested_attribute(
                            value=row[3],
                            unit="Text",
                            dimension="None",
                            source="LF_PDF_Page2",
                            is_pure=True
                        )

                    # Layer metadata
                    project["layer"] = self.create_nested_attribute(
                        value="L1",
                        unit="Text",
                        dimension="None",
                        source="LF_PDF_Page2",
                        is_pure=True
                    )

                    project["nodeType"] = self.create_nested_attribute(
                        value="Project_L1",
                        unit="Text",
                        dimension="None",
                        source="LF_PDF_Page2",
                        is_pure=True
                    )

                    project["priorityWeight"] = self.create_nested_attribute(
                        value=10,
                        unit="Integer",
                        dimension="None",
                        source="LF_PDF_Page2",
                        is_pure=True
                    )

                    project["extractionTimestamp"] = self.create_nested_attribute(
                        value=datetime.now().isoformat(),
                        unit="ISO-8601",
                        dimension="None",
                        source="LF_PDF_Page2",
                        is_pure=True
                    )

                    # ============================================
                    # U (Units) - Pure attributes with IS relationship
                    # ============================================

                    if len(row) > 7 and row[7]:  # Total Supply (Units)
                        project["totalSupplyUnits"] = self.create_nested_attribute(
                            value=self.clean_numeric(row[7]),
                            unit="count",
                            dimension="U",
                            source="LF_PDF_Page2",
                            is_pure=True
                        )

                    if len(row) > 10 and row[10]:  # Annual Sales (Units)
                        project["annualSalesUnits"] = self.create_nested_attribute(
                            value=self.clean_numeric(row[10]),
                            unit="count",
                            dimension="U",
                            source="LF_PDF_Page2",
                            is_pure=True
                        )

                    # ============================================
                    # L² (Area) - Pure and composite attributes
                    # ============================================

                    if len(row) > 6 and row[6]:  # Project Size (IN UNITS, NOT ACRES!)
                        # CORRECTED: The PROJECT_SIZE column contains UNITS (total project capacity)
                        # This is DIFFERENT from TOTAL_SUPPLY_UNITS (row[7]) which is current inventory
                        # Example: Sara City has PROJECT_SIZE=3018 units, TOTAL_SUPPLY_UNITS=1109 units

                        project_size_units = self.clean_numeric(row[6])
                        total_supply_units = self.clean_numeric(row[7]) if len(row) > 7 and row[7] else project_size_units
                        unit_size_sqft = self.clean_numeric(row[12]) if len(row) > 12 and row[12] else 500

                        # Store as projectSizeUnits (U dimension)
                        project["projectSizeUnits"] = self.create_nested_attribute(
                            value=project_size_units,
                            unit="count",
                            dimension="U",
                            source="LF_PDF_Page2",
                            is_pure=True
                        )

                        # Calculate projectSizeAcres using FAR (Floor Area Ratio) method
                        # This accounts for high-density projects correctly
                        # Formula: Land Area = (Total Built-up Area) / FAR
                        # Built-up Area ≈ Saleable Area × 1.5 (for common areas, circulation, etc.)
                        total_saleable_area_sqft = total_supply_units * unit_size_sqft
                        total_built_up_area_sqft = total_saleable_area_sqft * 1.5  # Add 50% for common areas
                        FAR = 2.0  # Typical FAR for residential projects in India
                        land_area_sqft = total_built_up_area_sqft / FAR if total_built_up_area_sqft else 0
                        land_area_acres = land_area_sqft / 43560 if land_area_sqft else 0  # Convert sqft to acres

                        project["projectSizeAcres"] = self.create_nested_attribute(
                            value=round(land_area_acres, 2),
                            unit="acres (calculated)",
                            dimension="L²",
                            source="LF_PDF_Page2_Calculated_From_FAR",
                            is_pure=True
                        )

                    if len(row) > 12 and row[12]:  # Unit Saleable Size (Sq.Ft.)
                        # L²/U - NUMERATOR/DENOMINATOR relationships
                        project["unitSaleableSizeSqft"] = self.create_nested_attribute(
                            value=self.clean_numeric(row[12]),
                            unit="sqft/unit",
                            dimension="L²/U",
                            source="LF_PDF_Page2",
                            is_pure=False
                        )

                    # ============================================
                    # T (Time) - Pure attributes with IS relationship
                    # ============================================

                    if len(row) > 4 and row[4]:  # Launch Date
                        project["launchDate"] = self.create_nested_attribute(
                            value=row[4],
                            unit="date",
                            dimension="T",
                            source="LF_PDF_Page2",
                            is_pure=True
                        )

                    if len(row) > 5 and row[5]:  # Possession Date
                        project["possessionDate"] = self.create_nested_attribute(
                            value=row[5],
                            unit="date",
                            dimension="T",
                            source="LF_PDF_Page2",
                            is_pure=True
                        )

                    # ============================================
                    # C (Cash Flow) - Pure attributes with IS relationship
                    # ============================================

                    if len(row) > 11 and row[11]:  # Annual Sales Value (Rs.Cr.)
                        project["annualSalesValueCr"] = self.create_nested_attribute(
                            value=self.clean_numeric(row[11]),
                            unit="INR Crore",
                            dimension="C",
                            source="LF_PDF_Page2",
                            is_pure=True
                        )

                    # ============================================
                    # C/L² (Price per sqft) - NUMERATOR/DENOMINATOR relationships
                    # ============================================

                    if len(row) > 13 and row[13]:  # Saleable Launch Price (Rs/Psf)
                        project["launchPricePSF"] = self.create_nested_attribute(
                            value=self.clean_numeric(row[13]),
                            unit="INR/sqft",
                            dimension="C/L²",
                            source="LF_PDF_Page2",
                            is_pure=False
                        )

                    if len(row) > 14 and row[14]:  # Saleable Price (Psf)
                        project["currentPricePSF"] = self.create_nested_attribute(
                            value=self.clean_numeric(row[14]),
                            unit="INR/sqft",
                            dimension="C/L²",
                            source="LF_PDF_Page2",
                            is_pure=False
                        )

                    # ============================================
                    # Fraction/T (Monthly Sales Velocity) - INVERSE_OF relationship
                    # ============================================

                    if len(row) > 15 and row[15]:  # Monthly Sales Velocity
                        project["monthlySalesVelocity"] = self.create_nested_attribute(
                            value=self.clean_numeric(row[15]),
                            unit="%/month",
                            dimension="Fraction/T",
                            source="LF_PDF_Page2",
                            is_pure=False
                        )

                    # ============================================
                    # Dimensionless (Percentages)
                    # ============================================

                    if len(row) > 8 and row[8]:  # Sold (%) Total Supply
                        project["soldPct"] = self.create_nested_attribute(
                            value=self.clean_numeric(row[8]),
                            unit="%",
                            dimension="Dimensionless",
                            source="LF_PDF_Page2",
                            is_pure=True
                        )

                    if len(row) > 9 and row[9]:  # Unsold
                        project["unsoldPct"] = self.create_nested_attribute(
                            value=self.clean_numeric(row[9]),
                            unit="%",
                            dimension="Dimensionless",
                            source="LF_PDF_Page2",
                            is_pure=True
                        )

                    # ============================================
                    # String attributes (non-dimensional)
                    # ============================================

                    if len(row) > 16 and row[16]:  # RERA Registered
                        project["reraRegistered"] = self.create_nested_attribute(
                            value=row[16],
                            unit="Boolean Flag",
                            dimension="None",
                            source="LF_PDF_Page2",
                            is_pure=True
                        )

                    projects.append(project)

                except Exception as e:
                    print(f"  ⚠️  Error processing row {row_idx}: {e}")
                    continue

            print(f"  ✓ Extracted {len(projects)} projects")

        except Exception as e:
            print(f"  ❌ Error extracting Page 2: {e}")

        return projects

    def calculate_l2_and_l3_for_all_projects(self):
        """
        Calculate L2 financial metrics and L3 insights for all projects
        Pre-populates all layers so insights are ready immediately
        """
        import sys
        sys.path.insert(0, '/Users/tusharsikand/Documents/Projects/liases-foras')

        from app.calculators.layer2_calculator import layer2_calculator
        from app.services.layer3_insights_engine import layer3_engine

        projects = self.extracted_data.get("page_2_projects", [])

        for idx, project in enumerate(projects):
            # Calculate L2 metrics
            l2_metrics = layer2_calculator.calculate_all_metrics(project)
            project["l2_metrics"] = l2_metrics

            # Generate L3 insights
            l3_insights = layer3_engine.generate_project_insights(project, l2_metrics)
            project["l3_insights"] = l3_insights

            if (idx + 1) % 5 == 0:
                print(f"  ✓ Processed {idx + 1}/{len(projects)} projects")

        print(f"  ✓ Completed L2+L3 for all {len(projects)} projects")

    def save_to_json(self, output_path: str):
        """Save extracted data to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.extracted_data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Data saved to: {output_path}")


def main():
    """Main execution"""
    print("="*70)
    print("V4.0.0 PDF EXTRACTION - NESTED FORMAT WITH EXPLICIT RELATIONSHIPS")
    print("="*70)

    pdf_path = "/Users/tusharsikand/Documents/Projects/liases-foras/GetMicromarketPdf.pdf"
    output_path = "/Users/tusharsikand/Documents/Projects/liases-foras/data/extracted/v4_clean_nested_structure.json"

    extractor = V4NestedPDFExtractor(pdf_path)

    # Extract L1 data from PDF
    with pdfplumber.open(pdf_path) as pdf:
        extractor.extracted_data["page_2_projects"] = extractor.extract_page_2_top_projects(pdf)
        # TODO: Add page 5 and page 8 extraction with same nested format

    # Calculate L2 metrics and L3 insights for all projects
    print("\nCalculating L2 financial metrics and L3 insights...")
    extractor.calculate_l2_and_l3_for_all_projects()

    # Save to JSON
    extractor.save_to_json(output_path)

    # Print sample
    print("\n" + "="*70)
    print("SAMPLE: Sara City Project (First 3 Attributes)")
    print("="*70)

    if extractor.extracted_data["page_2_projects"]:
        sara_city = extractor.extracted_data["page_2_projects"][0]
        for i, (attr_name, attr_data) in enumerate(sara_city.items()):
            if i >= 3:
                break
            print(f"\n\"{attr_name}\":")
            print(f"  value: {attr_data['value']}")
            print(f"  unit: {attr_data['unit']}")
            print(f"  dimension: {attr_data['dimension']}")
            if attr_data.get('relationships'):
                print(f"  relationships:")
                for rel in attr_data['relationships']:
                    print(f"    - type: {rel['type']}, target: {rel['target']}")

    print("\n" + "="*70)
    print("EXTRACTION STATISTICS")
    print("="*70)
    print(f"Projects: {len(extractor.extracted_data['page_2_projects'])}")
    print(f"Format: Fully nested {{value, unit, dimension, relationships}}")
    print(f"Relationships: Explicit (IS, NUMERATOR, DENOMINATOR, INVERSE_OF)")

    print("\n✅ Extraction complete! Data is in proper nested format.")


if __name__ == "__main__":
    main()
