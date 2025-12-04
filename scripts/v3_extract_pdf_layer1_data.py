"""
V3.0.0: PDF Layer 1 Data Extraction Script
===========================================

Extracts raw data from GetMicromarketPdf.pdf to create L1 attribute nodes.

MLTI-Inspired Architecture:
- L0 = Dimension definitions (U, L², T, C) - already created
- L1 = Attributes with dimensional tags (this script)
- L2 = Derived metrics (calculated later)
- L3 = Insights + Recommendations (generated later)

Key Changes from v2:
- REMOVED: Nested dimensions_L0 structure
- ADDED: Flat l1_attributes with dimensional tags
- Each attribute has: value, dimension, unit, source, isPure

Priority Extraction Order (PDF-first strategy):
- Page 2 (Weight 10/10): Top 10 Projects table
- Page 5 (Weight 9/10): Unit Type Analysis with Product Efficiency
- Page 8 (Weight 8/10): Quarterly Market Summary with QoQ/YoY changes
"""

import pdfplumber
import json
import re
from typing import Dict, List, Optional
from datetime import datetime


class V3PDFLayer1Extractor:
    """Extract Layer 1 raw data from PDF with v3.0.0 dimensional architecture"""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.extracted_data = {
            "metadata": {
                "source_file": pdf_path,
                "extraction_timestamp": datetime.now().isoformat(),
                "architecture_version": "v3.0.0",
                "data_layer": "L1",
                "description": "L1 attributes with dimensional tags (U, L², T, C)",
                "extraction_priority": {
                    "page_2": {"weight": 10, "description": "Top 10 Projects"},
                    "page_5": {"weight": 9, "description": "Unit Type Analysis"},
                    "page_8": {"weight": 8, "description": "Quarterly Market Summary"}
                }
            },
            "page_2_projects": [],  # L1 project nodes
            "page_5_unit_types": [],  # L1 unit type nodes
            "page_8_quarterly_summary": []  # L1 quarterly nodes
        }

    def clean_numeric(self, value: str) -> Optional[float]:
        """Clean and convert numeric values from PDF text"""
        if not value or value == '-':
            return None

        # Remove commas and spaces
        cleaned = str(value).replace(',', '').replace(' ', '').strip()

        # Handle percentage
        if '%' in cleaned:
            cleaned = cleaned.replace('%', '')
            try:
                return float(cleaned) / 100.0
            except:
                return None

        try:
            return float(cleaned)
        except:
            return None

    def extract_page_2_top_projects(self, pdf) -> List[Dict]:
        """
        Extract Page 2: Top 10 Projects Table (Priority Weight 10/10)

        V3.0.0 Structure: Flat l1_attributes with dimensional tags
        - Pure attributes: Single dimension (e.g., totalUnits = U)
        - Composite attributes: Multiple dimensions FROM LF (e.g., currentPricePSF = C/L²)
        """
        print("Extracting Page 2: Top 10 Projects (Weight 10/10)...")

        projects = []

        try:
            page = pdf.pages[1]  # Page 2 (0-indexed)
            tables = page.extract_tables()

            if not tables:
                print("  ⚠️  No tables found on Page 2")
                return projects

            # Find the main projects table (usually the largest table)
            main_table = max(tables, key=lambda t: len(t))

            # Expected columns (may vary based on PDF structure)
            for row_idx, row in enumerate(main_table[1:], 1):  # Skip header
                if not row or len(row) < 10:
                    continue

                try:
                    # V3.0.0: Flat l1_attributes structure
                    # CORRECTED COLUMN MAPPING (All 17 columns from Page 2)
                    # Column 0: Project Id
                    # Column 1: Project Name
                    # Column 2: Developer Name
                    # Column 3: Location
                    # Column 4: Launch Date
                    # Column 5: Possession Date
                    # Column 6: Project Size (acres)
                    # Column 7: Total Supply (Units)
                    # Column 8: Sold (%) Total Supply
                    # Column 9: Unsold
                    # Column 10: Annual Sales (Units)
                    # Column 11: Annual Sales Value (Rs.Cr.)
                    # Column 12: Unit Saleable Size (Sq.Ft.)
                    # Column 13: Saleable Launch Price (Rs/Psf)
                    # Column 14: Saleable Price (Psf)
                    # Column 15: Monthly Sales Velocity
                    # Column 16: RERA Registered

                    l1_attributes = {}

                    # ============================================
                    # PURE ATTRIBUTES (Single Dimension)
                    # ============================================

                    # U (Units) - Pure attributes
                    if len(row) > 7 and row[7]:  # Total Supply (Units)
                        l1_attributes["totalSupplyUnits"] = {
                            "value": self.clean_numeric(row[7]),
                            "dimension": "U",
                            "unit": "count",
                            "source": "LF_PDF_Page2",
                            "isPure": True
                        }

                    if len(row) > 10 and row[10]:  # Annual Sales (Units)
                        l1_attributes["annualSalesUnits"] = {
                            "value": self.clean_numeric(row[10]),
                            "dimension": "U",
                            "unit": "count",
                            "source": "LF_PDF_Page2",
                            "isPure": True
                        }

                    # L² (Area) - Pure attributes
                    if len(row) > 6 and row[6]:  # Project Size (in acres)
                        l1_attributes["projectSizeAcres"] = {
                            "value": self.clean_numeric(row[6]),
                            "dimension": "L²",
                            "unit": "acres",
                            "source": "LF_PDF_Page2",
                            "isPure": True
                        }

                    if len(row) > 12 and row[12]:  # Unit Saleable Size (Sq.Ft.)
                        l1_attributes["unitSaleableSizeSqft"] = {
                            "value": self.clean_numeric(row[12]),
                            "dimension": "L²/U",
                            "unit": "sqft/unit",
                            "source": "LF_PDF_Page2",
                            "isPure": False  # Composite: L²/U
                        }

                    # T (Time) - Pure attributes
                    if len(row) > 4 and row[4]:  # Launch Date
                        l1_attributes["launchDate"] = {
                            "value": row[4],
                            "dimension": "T",
                            "unit": "date",
                            "source": "LF_PDF_Page2",
                            "isPure": True
                        }

                    if len(row) > 5 and row[5]:  # Possession Date
                        l1_attributes["possessionDate"] = {
                            "value": row[5],
                            "dimension": "T",
                            "unit": "date",
                            "source": "LF_PDF_Page2",
                            "isPure": True
                        }

                    # C (Cash Flow) - Pure attributes
                    if len(row) > 11 and row[11]:  # Annual Sales Value (Rs.Cr.)
                        l1_attributes["annualSalesValueCr"] = {
                            "value": self.clean_numeric(row[11]),
                            "dimension": "C",
                            "unit": "INR Cr",
                            "source": "LF_PDF_Page2",
                            "isPure": True
                        }

                    # ============================================
                    # COMPOSITE ATTRIBUTES (Multiple Dimensions FROM LF)
                    # ============================================

                    # C/L² (Price per sqft) - Composite FROM LF
                    if len(row) > 13 and row[13]:  # Saleable Launch Price (Rs/Psf)
                        l1_attributes["launchPricePSF"] = {
                            "value": self.clean_numeric(row[13]),
                            "dimension": "C/L²",
                            "unit": "INR/sqft",
                            "source": "LF_PDF_Page2",
                            "isPure": False  # Composite FROM LF
                        }

                    if len(row) > 14 and row[14]:  # Saleable Price (Psf)
                        l1_attributes["currentPricePSF"] = {
                            "value": self.clean_numeric(row[14]),
                            "dimension": "C/L²",
                            "unit": "INR/sqft",
                            "source": "LF_PDF_Page2",
                            "isPure": False  # Composite FROM LF
                        }

                    # Fraction/T (Monthly Sales Velocity) - Composite FROM LF
                    if len(row) > 15 and row[15]:  # Monthly Sales Velocity
                        l1_attributes["monthlySalesVelocity"] = {
                            "value": self.clean_numeric(row[15]),
                            "dimension": "Fraction/T",
                            "unit": "fraction/month",
                            "source": "LF_PDF_Page2",
                            "isPure": False  # Composite FROM LF
                        }

                    # Dimensionless (Percentages) - Pure attributes
                    if len(row) > 8 and row[8]:  # Sold (%) Total Supply
                        l1_attributes["soldPct"] = {
                            "value": self.clean_numeric(row[8]),
                            "dimension": "Dimensionless",
                            "unit": "fraction",
                            "source": "LF_PDF_Page2",
                            "isPure": True
                        }

                    if len(row) > 9 and row[9]:  # Unsold
                        l1_attributes["unsoldPct"] = {
                            "value": self.clean_numeric(row[9]),
                            "dimension": "Dimensionless",
                            "unit": "fraction",
                            "source": "LF_PDF_Page2",
                            "isPure": True
                        }

                    # String attributes (non-dimensional)
                    if len(row) > 16 and row[16]:  # RERA Registered
                        l1_attributes["reraRegistered"] = {
                            "value": row[16],
                            "dimension": "String",
                            "unit": "text",
                            "source": "LF_PDF_Page2",
                            "isPure": True
                        }

                    # ============================================
                    # PROJECT NODE STRUCTURE (CORRECTED MAPPING)
                    # ============================================

                    project = {
                        "layer": "L1",
                        "node_type": "Project_L1",
                        "projectId": self.clean_numeric(row[0]) if len(row) > 0 and row[0] else None,  # Column 0: Project Id
                        "projectName": row[1] if len(row) > 1 else None,  # Column 1: Project Name
                        "developerName": row[2] if len(row) > 2 else None,  # Column 2: Developer Name
                        "location": row[3] if len(row) > 3 else None,  # Column 3: Location
                        "l1_attributes": l1_attributes,
                        "priority_weight": 10,
                        "extraction_timestamp": datetime.now().isoformat()
                    }

                    projects.append(project)
                    print(f"  ✓ Extracted: {project['projectName']} ({len(l1_attributes)} attributes)")

                except Exception as e:
                    print(f"  ⚠️  Error extracting row {row_idx}: {e}")
                    continue

            print(f"  ✓ Page 2 Complete: {len(projects)} projects extracted")

        except Exception as e:
            print(f"  ❌ Error extracting Page 2: {e}")

        return projects

    def extract_page_5_unit_types(self, pdf) -> List[Dict]:
        """
        Extract Page 5: Unit Type Analysis (Priority Weight 9/10)

        V3.0.0 Structure: Flat l1_attributes with dimensional tags
        """
        print("Extracting Page 5: Unit Type Analysis (Weight 9/10)...")

        unit_types = []

        try:
            page = pdf.pages[4]  # Page 5 (0-indexed)
            tables = page.extract_tables()

            if not tables:
                print("  ⚠️  No tables found on Page 5")
                return unit_types

            main_table = max(tables, key=lambda t: len(t))

            for row_idx, row in enumerate(main_table[1:], 1):
                if not row or len(row) < 5:
                    continue

                try:
                    l1_attributes = {}

                    # L² (Area) - Pure attributes
                    if len(row) > 1 and row[1]:
                        l1_attributes["saleableMinSizeSqft"] = {
                            "value": self.clean_numeric(row[1]),
                            "dimension": "L²",
                            "unit": "sqft",
                            "source": "LF_PDF_Page5",
                            "isPure": True
                        }

                    if len(row) > 2 and row[2]:
                        l1_attributes["saleableMaxSizeSqft"] = {
                            "value": self.clean_numeric(row[2]),
                            "dimension": "L²",
                            "unit": "sqft",
                            "source": "LF_PDF_Page5",
                            "isPure": True
                        }

                    # C (Cash Flow) - Pure attributes
                    if len(row) > 3 and row[3]:
                        l1_attributes["minCostINR"] = {
                            "value": self.clean_numeric(row[3]),
                            "dimension": "C",
                            "unit": "INR Lakh",
                            "source": "LF_PDF_Page5",
                            "isPure": True
                        }

                    if len(row) > 4 and row[4]:
                        l1_attributes["maxCostINR"] = {
                            "value": self.clean_numeric(row[4]),
                            "dimension": "C",
                            "unit": "INR Lakh",
                            "source": "LF_PDF_Page5",
                            "isPure": True
                        }

                    # U (Units) - Pure attributes
                    if len(row) > 5 and row[5]:
                        l1_attributes["annualSalesUnits"] = {
                            "value": self.clean_numeric(row[5]),
                            "dimension": "U",
                            "unit": "count",
                            "source": "LF_PDF_Page5",
                            "isPure": True
                        }

                    if len(row) > 6 and row[6]:
                        l1_attributes["unsoldUnits"] = {
                            "value": self.clean_numeric(row[6]),
                            "dimension": "U",
                            "unit": "count",
                            "source": "LF_PDF_Page5",
                            "isPure": True
                        }

                    if len(row) > 7 and row[7]:
                        l1_attributes["totalSupply"] = {
                            "value": self.clean_numeric(row[7]),
                            "dimension": "U",
                            "unit": "count",
                            "source": "LF_PDF_Page5",
                            "isPure": True
                        }

                    # C/L² (Price per sqft) - Composite FROM LF
                    if len(row) > 8 and row[8]:
                        l1_attributes["wtAvgSaleablePricePSF"] = {
                            "value": self.clean_numeric(row[8]),
                            "dimension": "C/L²",
                            "unit": "INR/sqft",
                            "source": "LF_PDF_Page5",
                            "isPure": False  # Composite FROM LF
                        }

                    if len(row) > 9 and row[9]:
                        l1_attributes["wtAvgCarpetPricePSF"] = {
                            "value": self.clean_numeric(row[9]),
                            "dimension": "C/L²",
                            "unit": "INR/sqft",
                            "source": "LF_PDF_Page5",
                            "isPure": False  # Composite FROM LF
                        }

                    # Dimensionless (Product Efficiency) - Composite FROM LF
                    if len(row) > 10 and row[10]:
                        l1_attributes["productEfficiencyPct"] = {
                            "value": self.clean_numeric(row[10]),
                            "dimension": "Dimensionless",
                            "unit": "fraction",
                            "source": "LF_PDF_Page5",
                            "isPure": False  # LF unique metric
                        }

                    # T (Time) - Composite FROM LF
                    if len(row) > 11 and row[11]:
                        l1_attributes["monthsInventory"] = {
                            "value": self.clean_numeric(row[11]),
                            "dimension": "T",
                            "unit": "months",
                            "source": "LF_PDF_Page5",
                            "isPure": False  # Derived FROM LF
                        }

                    # U/T (Sales velocity) - Composite FROM LF
                    if len(row) > 12 and row[12]:
                        l1_attributes["salesVelocity"] = {
                            "value": self.clean_numeric(row[12]),
                            "dimension": "U/T",
                            "unit": "units/month",
                            "source": "LF_PDF_Page5",
                            "isPure": False  # Composite FROM LF
                        }

                    unit_type = {
                        "layer": "L1",
                        "node_type": "UnitType_L1",
                        "flatType": row[0],  # 1BHK, 2BHK, 3BHK, etc.
                        "l1_attributes": l1_attributes,
                        "priority_weight": 9,
                        "extraction_timestamp": datetime.now().isoformat()
                    }

                    unit_types.append(unit_type)
                    print(f"  ✓ Extracted: {unit_type['flatType']} ({len(l1_attributes)} attributes)")

                except Exception as e:
                    print(f"  ⚠️  Error extracting row {row_idx}: {e}")
                    continue

            print(f"  ✓ Page 5 Complete: {len(unit_types)} unit types extracted")

        except Exception as e:
            print(f"  ❌ Error extracting Page 5: {e}")

        return unit_types

    def extract_page_8_quarterly_summary(self, pdf) -> List[Dict]:
        """
        Extract Page 8: Quarterly Market Summary (Priority Weight 8/10)

        V3.0.0 Structure: Flat l1_attributes with dimensional tags
        """
        print("Extracting Page 8: Quarterly Market Summary (Weight 8/10)...")

        quarterly_data = []

        try:
            page = pdf.pages[7]  # Page 8 (0-indexed)
            tables = page.extract_tables()

            if not tables:
                print("  ⚠️  No tables found on Page 8")
                return quarterly_data

            main_table = max(tables, key=lambda t: len(t))

            for row_idx, row in enumerate(main_table[1:], 1):
                if not row or len(row) < 5:
                    continue

                try:
                    l1_attributes = {}

                    # U (Units) - Pure attributes
                    if len(row) > 1 and row[1]:
                        l1_attributes["marketableSupplyUnits"] = {
                            "value": self.clean_numeric(row[1]),
                            "dimension": "U",
                            "unit": "count",
                            "source": "LF_PDF_Page8",
                            "isPure": True
                        }

                    if len(row) > 2 and row[2]:
                        l1_attributes["quarterlySalesUnits"] = {
                            "value": self.clean_numeric(row[2]),
                            "dimension": "U",
                            "unit": "count",
                            "source": "LF_PDF_Page8",
                            "isPure": True
                        }

                    if len(row) > 3 and row[3]:
                        l1_attributes["annualSalesUnits"] = {
                            "value": self.clean_numeric(row[3]),
                            "dimension": "U",
                            "unit": "count",
                            "source": "LF_PDF_Page8",
                            "isPure": True
                        }

                    if len(row) > 4 and row[4]:
                        l1_attributes["unsoldStockUnits"] = {
                            "value": self.clean_numeric(row[4]),
                            "dimension": "U",
                            "unit": "count",
                            "source": "LF_PDF_Page8",
                            "isPure": True
                        }

                    # L² (Area) - Pure attributes
                    if len(row) > 5 and row[5]:
                        l1_attributes["marketableSupplySqft"] = {
                            "value": self.clean_numeric(row[5]),
                            "dimension": "L²",
                            "unit": "sqft",
                            "source": "LF_PDF_Page8",
                            "isPure": True
                        }

                    if len(row) > 6 and row[6]:
                        l1_attributes["quarterlySalesSqft"] = {
                            "value": self.clean_numeric(row[6]),
                            "dimension": "L²",
                            "unit": "sqft",
                            "source": "LF_PDF_Page8",
                            "isPure": True
                        }

                    if len(row) > 7 and row[7]:
                        l1_attributes["unsoldStockSqft"] = {
                            "value": self.clean_numeric(row[7]),
                            "dimension": "L²",
                            "unit": "sqft",
                            "source": "LF_PDF_Page8",
                            "isPure": True
                        }

                    # C (Cash Flow) - Pure and Composite
                    if len(row) > 10 and row[10]:
                        l1_attributes["unsoldStockValueCr"] = {
                            "value": self.clean_numeric(row[10]),
                            "dimension": "C",
                            "unit": "INR Cr",
                            "source": "LF_PDF_Page8",
                            "isPure": True
                        }

                    # C/L² (Price per sqft) - Composite FROM LF
                    if len(row) > 8 and row[8]:
                        l1_attributes["wtAvgPriceSaleablePSF"] = {
                            "value": self.clean_numeric(row[8]),
                            "dimension": "C/L²",
                            "unit": "INR/sqft",
                            "source": "LF_PDF_Page8",
                            "isPure": False  # Composite FROM LF
                        }

                    if len(row) > 9 and row[9]:
                        l1_attributes["wtAvgPriceCarpetPSF"] = {
                            "value": self.clean_numeric(row[9]),
                            "dimension": "C/L²",
                            "unit": "INR/sqft",
                            "source": "LF_PDF_Page8",
                            "isPure": False  # Composite FROM LF
                        }

                    # Dimensionless (Percentages) - Composite FROM LF
                    if len(row) > 11 and row[11]:
                        l1_attributes["salesVelocityPct"] = {
                            "value": self.clean_numeric(row[11]),
                            "dimension": "Dimensionless",
                            "unit": "fraction",
                            "source": "LF_PDF_Page8",
                            "isPure": False  # Derived FROM LF
                        }

                    # T (Time) - Composite FROM LF
                    if len(row) > 12 and row[12]:
                        l1_attributes["monthsInventory"] = {
                            "value": self.clean_numeric(row[12]),
                            "dimension": "T",
                            "unit": "months",
                            "source": "LF_PDF_Page8",
                            "isPure": False  # Derived FROM LF
                        }

                    # NOTE: QoQ/YoY changes will be calculated in L2 layer
                    # We only extract base L1 data here

                    quarter = {
                        "layer": "L1",
                        "node_type": "QuarterlySummary_L1",
                        "quarterLabel": row[0],  # e.g., "Q2 25-26"
                        "l1_attributes": l1_attributes,
                        "priority_weight": 8,
                        "extraction_timestamp": datetime.now().isoformat()
                    }

                    quarterly_data.append(quarter)
                    print(f"  ✓ Extracted: {quarter['quarterLabel']} ({len(l1_attributes)} attributes)")

                except Exception as e:
                    print(f"  ⚠️  Error extracting row {row_idx}: {e}")
                    continue

            print(f"  ✓ Page 8 Complete: {len(quarterly_data)} quarters extracted")

        except Exception as e:
            print(f"  ❌ Error extracting Page 8: {e}")

        return quarterly_data

    def extract_all(self) -> Dict:
        """Extract all priority pages from PDF"""
        print("="*70)
        print("V3.0.0: PDF LAYER 1 DATA EXTRACTION")
        print("="*70)
        print(f"Source: {self.pdf_path}")
        print(f"Target: L1 attributes with dimensional tags (U, L², T, C)\n")

        with pdfplumber.open(self.pdf_path) as pdf:
            print(f"Total pages in PDF: {len(pdf.pages)}\n")

            # Priority-weighted extraction
            self.extracted_data["page_2_projects"] = self.extract_page_2_top_projects(pdf)
            print()

            self.extracted_data["page_5_unit_types"] = self.extract_page_5_unit_types(pdf)
            print()

            self.extracted_data["page_8_quarterly_summary"] = self.extract_page_8_quarterly_summary(pdf)
            print()

        # Add summary stats
        self.extracted_data["metadata"]["extraction_summary"] = {
            "total_projects_extracted": len(self.extracted_data["page_2_projects"]),
            "total_unit_types_extracted": len(self.extracted_data["page_5_unit_types"]),
            "total_quarters_extracted": len(self.extracted_data["page_8_quarterly_summary"])
        }

        return self.extracted_data

    def save_to_json(self, output_path: str):
        """Save extracted data to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.extracted_data, f, indent=2, ensure_ascii=False)

        print("="*70)
        print("V3.0.0 EXTRACTION COMPLETE")
        print("="*70)
        print(f"Output saved to: {output_path}")
        print(f"Projects (Page 2): {self.extracted_data['metadata']['extraction_summary']['total_projects_extracted']}")
        print(f"Unit Types (Page 5): {self.extracted_data['metadata']['extraction_summary']['total_unit_types_extracted']}")
        print(f"Quarterly Data (Page 8): {self.extracted_data['metadata']['extraction_summary']['total_quarters_extracted']}")
        print("="*70)
        print("\nNext Steps:")
        print("1. Review extracted JSON structure")
        print("2. Run: python scripts/v3_load_l1_to_neo4j.py")
        print("3. Verify L1 attributes linked to L0 dimensions in Neo4j")
        print("="*70)


def main():
    """Main execution"""
    pdf_path = "/Users/tusharsikand/Documents/Projects/liases-foras/GetMicromarketPdf.pdf"
    output_path = "/Users/tusharsikand/Documents/Projects/liases-foras/data/extracted/v3_lf_layer1_data_from_pdf.json"

    extractor = V3PDFLayer1Extractor(pdf_path)
    extractor.extract_all()
    extractor.save_to_json(output_path)


if __name__ == "__main__":
    main()
