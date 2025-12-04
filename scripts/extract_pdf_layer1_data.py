"""
PDF Layer 1 Data Extraction Script
Extracts raw data from GetMicromarketPdf.pdf to create L1 nodes

Priority Extraction Order (as per PDF-first strategy):
- Page 2 (Weight 10/10): Top 10 Projects table
- Page 5 (Weight 9/10): Unit Type Analysis with Product Efficiency
- Page 8 (Weight 8/10): Quarterly Market Summary with QoQ/YoY changes

Output: L1 (raw data) nodes mapped to L0 dimensions (U, L², T, CF)
"""

import pdfplumber
import json
import re
from typing import Dict, List, Optional
from datetime import datetime


class PDFLayer1Extractor:
    """Extract Layer 1 raw data from PDF following dimensional architecture"""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.extracted_data = {
            "metadata": {
                "source_file": pdf_path,
                "extraction_timestamp": datetime.now().isoformat(),
                "data_layer": "L1",  # Raw input data
                "extraction_priority": {
                    "page_2": {"weight": 10, "description": "Top 10 Projects - L0 foundation"},
                    "page_5": {"weight": 9, "description": "Unit Type Analysis - L1 metrics"},
                    "page_8": {"weight": 8, "description": "Quarterly Market Summary - Time series"}
                }
            },
            "page_2_projects": [],  # L1 nodes: Project-level raw data
            "page_5_unit_types": [],  # L1 nodes: Unit type analysis
            "page_8_quarterly_summary": []  # L1 nodes: Time series data
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

        Creates L1 nodes with dimensional mapping to L0:
        - U (Units): total_supply, annual_sales_units
        - L² (Area): project_size, unit_saleable_size
        - T (Time): launch_date, possession_date
        - CF (Cash Flow): annual_sales_value_cr, launch_price_psf, current_price_psf
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
            # We'll use flexible column matching
            for row_idx, row in enumerate(main_table[1:], 1):  # Skip header
                if not row or len(row) < 10:
                    continue

                try:
                    project = {
                        "layer": "L1",
                        "node_type": "Project_L1",
                        "project_name": row[0],
                        "developer_name": row[1] if len(row) > 1 else None,
                        "location": row[2] if len(row) > 2 else None,

                        # Layer 0 Dimensions (U, L², T, CF)
                        "dimensions_L0": {
                            "U": {  # Units dimension
                                "total_supply_units": self.clean_numeric(row[3]) if len(row) > 3 else None,
                                "annual_sales_units": self.clean_numeric(row[4]) if len(row) > 4 else None,
                                "sold_pct": self.clean_numeric(row[5]) if len(row) > 5 else None,
                                "unsold_pct": self.clean_numeric(row[6]) if len(row) > 6 else None
                            },
                            "L2": {  # Area dimension (sqft)
                                "project_size": self.clean_numeric(row[7]) if len(row) > 7 else None,
                                "unit_saleable_size_sqft": self.clean_numeric(row[8]) if len(row) > 8 else None
                            },
                            "T": {  # Time dimension
                                "launch_date": row[9] if len(row) > 9 else None,
                                "possession_date": row[10] if len(row) > 10 else None
                            },
                            "CF": {  # Cash Flow dimension (INR)
                                "annual_sales_value_cr": self.clean_numeric(row[11]) if len(row) > 11 else None,
                                "launch_price_psf": self.clean_numeric(row[12]) if len(row) > 12 else None,
                                "current_price_psf": self.clean_numeric(row[13]) if len(row) > 13 else None
                            }
                        },

                        # Layer 1 Derived Metrics (Simple Ratios from L0)
                        "metrics_L1": {
                            "monthly_sales_velocity": self.clean_numeric(row[14]) if len(row) > 14 else None,
                            "months_inventory": self.clean_numeric(row[15]) if len(row) > 15 else None,
                            "rera_registered": row[16] if len(row) > 16 else None
                        },

                        "priority_weight": 10,
                        "extraction_timestamp": datetime.now().isoformat()
                    }

                    projects.append(project)
                    print(f"  ✓ Extracted: {project['project_name']}")

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

        Creates L1 nodes for unit type performance with Product Efficiency metric
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
                    unit_type = {
                        "layer": "L1",
                        "node_type": "UnitType_L1",
                        "flat_type": row[0],  # 1BHK, 2BHK, 3BHK, etc.

                        # Layer 0 Dimensions
                        "dimensions_L0": {
                            "L2": {  # Area dimension
                                "saleable_min_size_sqft": self.clean_numeric(row[1]) if len(row) > 1 else None,
                                "saleable_max_size_sqft": self.clean_numeric(row[2]) if len(row) > 2 else None
                            },
                            "CF": {  # Cash Flow dimension
                                "min_cost": self.clean_numeric(row[3]) if len(row) > 3 else None,
                                "max_cost": self.clean_numeric(row[4]) if len(row) > 4 else None
                            },
                            "U": {  # Units dimension
                                "annual_sales_units": self.clean_numeric(row[5]) if len(row) > 5 else None,
                                "unsold_units": self.clean_numeric(row[6]) if len(row) > 6 else None,
                                "total_supply": self.clean_numeric(row[7]) if len(row) > 7 else None
                            }
                        },

                        # Layer 1 Derived Metrics
                        "metrics_L1": {
                            "wt_avg_saleable_price_psf": self.clean_numeric(row[8]) if len(row) > 8 else None,
                            "wt_avg_carpet_price_psf": self.clean_numeric(row[9]) if len(row) > 9 else None,
                            "product_efficiency_pct": self.clean_numeric(row[10]) if len(row) > 10 else None,  # Unique LF metric
                            "months_inventory": self.clean_numeric(row[11]) if len(row) > 11 else None,
                            "sales_velocity": self.clean_numeric(row[12]) if len(row) > 12 else None
                        },

                        "priority_weight": 9,
                        "extraction_timestamp": datetime.now().isoformat()
                    }

                    unit_types.append(unit_type)
                    print(f"  ✓ Extracted: {unit_type['flat_type']}")

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

        Creates L1 nodes for time series data with QoQ and YoY changes
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
                    quarter = {
                        "layer": "L1",
                        "node_type": "QuarterlySummary_L1",
                        "quarter_label": row[0],  # e.g., "Q2 25-26"

                        # Layer 0 Dimensions (Time series)
                        "dimensions_L0": {
                            "U": {  # Units dimension
                                "marketable_supply_units": self.clean_numeric(row[1]) if len(row) > 1 else None,
                                "quarterly_sales_units": self.clean_numeric(row[2]) if len(row) > 2 else None,
                                "annual_sales_units": self.clean_numeric(row[3]) if len(row) > 3 else None,
                                "unsold_stock_units": self.clean_numeric(row[4]) if len(row) > 4 else None
                            },
                            "L2": {  # Area dimension
                                "marketable_supply_sqft": self.clean_numeric(row[5]) if len(row) > 5 else None,
                                "quarterly_sales_sqft": self.clean_numeric(row[6]) if len(row) > 6 else None,
                                "unsold_stock_sqft": self.clean_numeric(row[7]) if len(row) > 7 else None
                            },
                            "CF": {  # Cash Flow dimension
                                "wt_avg_price_saleable_psf": self.clean_numeric(row[8]) if len(row) > 8 else None,
                                "wt_avg_price_carpet_psf": self.clean_numeric(row[9]) if len(row) > 9 else None,
                                "unsold_stock_value_cr": self.clean_numeric(row[10]) if len(row) > 10 else None
                            }
                        },

                        # Layer 1 Derived Metrics
                        "metrics_L1": {
                            "sales_velocity_pct": self.clean_numeric(row[11]) if len(row) > 11 else None,
                            "months_inventory": self.clean_numeric(row[12]) if len(row) > 12 else None
                        },

                        # Layer 2 Aggregated Metrics (QoQ/YoY changes)
                        "metrics_L2": {
                            "qoq_change_pct": self.clean_numeric(row[13]) if len(row) > 13 else None,
                            "yoy_change_pct": self.clean_numeric(row[14]) if len(row) > 14 else None
                        },

                        "priority_weight": 8,
                        "extraction_timestamp": datetime.now().isoformat()
                    }

                    quarterly_data.append(quarter)
                    print(f"  ✓ Extracted: {quarter['quarter_label']}")

                except Exception as e:
                    print(f"  ⚠️  Error extracting row {row_idx}: {e}")
                    continue

            print(f"  ✓ Page 8 Complete: {len(quarterly_data)} quarters extracted")

        except Exception as e:
            print(f"  ❌ Error extracting Page 8: {e}")

        return quarterly_data

    def extract_all(self) -> Dict:
        """Extract all priority pages from PDF"""
        print("="*60)
        print("PDF LAYER 1 DATA EXTRACTION")
        print("="*60)
        print(f"Source: {self.pdf_path}")
        print(f"Target: Layer 1 (Raw Input Data) mapped to L0 dimensions\n")

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

        print("="*60)
        print("EXTRACTION COMPLETE")
        print("="*60)
        print(f"Output saved to: {output_path}")
        print(f"Projects (Page 2): {self.extracted_data['metadata']['extraction_summary']['total_projects_extracted']}")
        print(f"Unit Types (Page 5): {self.extracted_data['metadata']['extraction_summary']['total_unit_types_extracted']}")
        print(f"Quarterly Data (Page 8): {self.extracted_data['metadata']['extraction_summary']['total_quarters_extracted']}")
        print("="*60)


def main():
    """Main execution"""
    pdf_path = "/Users/tusharsikand/Documents/Projects/liases-foras/GetMicromarketPdf.pdf"
    output_path = "/Users/tusharsikand/Documents/Projects/liases-foras/data/extracted/lf_layer1_data_from_pdf.json"

    extractor = PDFLayer1Extractor(pdf_path)
    extractor.extract_all()
    extractor.save_to_json(output_path)


if __name__ == "__main__":
    main()
