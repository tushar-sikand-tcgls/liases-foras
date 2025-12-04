"""
Excel Data Enrichment Script for L1 Nodes
==========================================

Purpose:
- Enrich PDF-extracted L1 nodes with complementary Excel data (80 files)
- PDF = Primary source (Priority Weights 10, 9, 8)
- Excel = Supplementary source (fills gaps, adds buyer demographics, transaction trends)

Strategy:
- Load PDF-extracted L1 data (lf_layer1_data_from_pdf.json)
- Parse 80 Excel files (skiprows=6, header in row 6)
- Cross-reference and enrich matching nodes
- Output enriched JSON (lf_layer1_enriched_from_excel.json)

Data Mapping:
- Page 2 Projects → Top_10_Project_Data, New_Launch_Project_Details, IgrProjectDetails
- Page 5 Unit Types → Flat_Type_Analysis, Annual_Sales, Quarterly_Sales, Price_Trends
- Page 8 Quarterly → Quarterly_Marker_Summary, Yearly_Marker_Summary, Unsold_Stock
"""

import pandas as pd
import json
import os
import glob
from typing import Dict, List, Optional
from datetime import datetime


class ExcelEnricher:
    """Enrich L1 PDF data with supplementary Excel data"""

    def __init__(self, pdf_json_path: str, excel_dir: str):
        self.pdf_json_path = pdf_json_path
        self.excel_dir = excel_dir

        # Load PDF-extracted L1 data
        with open(pdf_json_path, 'r', encoding='utf-8') as f:
            self.pdf_data = json.load(f)

        # Initialize enriched data structure
        self.enriched_data = {
            "metadata": self.pdf_data.get("metadata", {}),
            "page_2_projects": self.pdf_data.get("page_2_projects", []),
            "page_5_unit_types": self.pdf_data.get("page_5_unit_types", []),
            "page_8_quarterly_summary": self.pdf_data.get("page_8_quarterly_summary", []),
            "excel_enrichments": {
                "project_enrichments": [],
                "unit_type_enrichments": [],
                "quarterly_enrichments": [],
                "buyer_demographics": [],
                "transaction_trends": []
            }
        }

        # Track enrichment stats
        self.stats = {
            "excel_files_processed": 0,
            "excel_files_skipped": 0,
            "projects_enriched": 0,
            "unit_types_enriched": 0,
            "quarterly_data_enriched": 0,
            "buyer_data_added": 0,
            "transaction_data_added": 0
        }

    def safe_read_excel(self, filepath: str, skiprows: int = 6) -> Optional[pd.DataFrame]:
        """Safely read Excel file with error handling"""
        try:
            df = pd.read_excel(filepath, skiprows=skiprows)
            # Drop rows that are completely empty
            df = df.dropna(how='all')
            # Drop columns that are completely empty
            df = df.dropna(axis=1, how='all')

            # Convert datetime columns to strings for JSON serialization
            for col in df.columns:
                if df[col].dtype == 'datetime64[ns]':
                    df[col] = df[col].dt.strftime('%Y-%m-%d')

            # Replace NaN with None for JSON serialization
            df = df.where(pd.notnull(df), None)

            return df
        except Exception as e:
            print(f"  ⚠️  Error reading {os.path.basename(filepath)}: {e}")
            self.stats["excel_files_skipped"] += 1
            return None

    def enrich_projects_from_excel(self):
        """Enrich Page 2 projects with Top 10, New Launch, and IGR data"""
        print("\n" + "=" * 70)
        print("ENRICHING PROJECTS (Page 2) WITH EXCEL DATA")
        print("=" * 70)

        # Find all project-related Excel files
        project_files = []
        project_files.extend(glob.glob(os.path.join(self.excel_dir, "Top_10_Project_Data*.xlsx")))
        project_files.extend(glob.glob(os.path.join(self.excel_dir, "New_Launch_Project_Details*.xlsx")))
        project_files.extend(glob.glob(os.path.join(self.excel_dir, "IgrProjectDetails*.xlsx")))

        for filepath in project_files:
            print(f"\n📄 Processing: {os.path.basename(filepath)}")
            df = self.safe_read_excel(filepath)

            if df is None:
                continue

            # Convert DataFrame to enrichment records
            enrichment_record = {
                "source_file": os.path.basename(filepath),
                "data_type": "project_metrics",
                "extraction_timestamp": datetime.now().isoformat(),
                "records": df.to_dict('records')
            }

            self.enriched_data["excel_enrichments"]["project_enrichments"].append(enrichment_record)
            self.stats["excel_files_processed"] += 1
            self.stats["projects_enriched"] += len(df)
            print(f"  ✓ Extracted {len(df)} project records")

    def enrich_unit_types_from_excel(self):
        """Enrich Page 5 unit types with Flat Analysis, Sales, Price data"""
        print("\n" + "=" * 70)
        print("ENRICHING UNIT TYPES (Page 5) WITH EXCEL DATA")
        print("=" * 70)

        # Find all unit-type-related Excel files
        unit_files = []
        unit_files.extend(glob.glob(os.path.join(self.excel_dir, "Flat_Type_Analysis*.xlsx")))
        unit_files.extend(glob.glob(os.path.join(self.excel_dir, "Annual_Sales_Data*.xlsx")))
        unit_files.extend(glob.glob(os.path.join(self.excel_dir, "Quarterly_Sales_Data*.xlsx")))
        unit_files.extend(glob.glob(os.path.join(self.excel_dir, "Sales_Velocity*.xlsx")))
        unit_files.extend(glob.glob(os.path.join(self.excel_dir, "Saleable_Area_Price*.xlsx")))
        unit_files.extend(glob.glob(os.path.join(self.excel_dir, "Carpet_Area_Price*.xlsx")))

        for filepath in unit_files:
            print(f"\n📄 Processing: {os.path.basename(filepath)}")
            df = self.safe_read_excel(filepath)

            if df is None:
                continue

            # Convert DataFrame to enrichment records
            enrichment_record = {
                "source_file": os.path.basename(filepath),
                "data_type": "unit_type_metrics",
                "extraction_timestamp": datetime.now().isoformat(),
                "records": df.to_dict('records')
            }

            self.enriched_data["excel_enrichments"]["unit_type_enrichments"].append(enrichment_record)
            self.stats["excel_files_processed"] += 1
            self.stats["unit_types_enriched"] += len(df)
            print(f"  ✓ Extracted {len(df)} unit type records")

    def enrich_quarterly_from_excel(self):
        """Enrich Page 8 quarterly data with Market Summary, Unsold Stock data"""
        print("\n" + "=" * 70)
        print("ENRICHING QUARTERLY DATA (Page 8) WITH EXCEL DATA")
        print("=" * 70)

        # Find all quarterly-related Excel files
        quarterly_files = []
        quarterly_files.extend(glob.glob(os.path.join(self.excel_dir, "Quarterly_Marker_Summary*.xlsx")))
        quarterly_files.extend(glob.glob(os.path.join(self.excel_dir, "Yearly_Marker_Summary*.xlsx")))
        quarterly_files.extend(glob.glob(os.path.join(self.excel_dir, "Quarterly_Sales_&_Marketable_Supply*.xlsx")))
        quarterly_files.extend(glob.glob(os.path.join(self.excel_dir, "Unsold_Stock_Data*.xlsx")))
        quarterly_files.extend(glob.glob(os.path.join(self.excel_dir, "Primary_Vs_Secondary*.xlsx")))

        for filepath in quarterly_files:
            print(f"\n📄 Processing: {os.path.basename(filepath)}")
            df = self.safe_read_excel(filepath)

            if df is None:
                continue

            # Convert DataFrame to enrichment records
            enrichment_record = {
                "source_file": os.path.basename(filepath),
                "data_type": "quarterly_market_metrics",
                "extraction_timestamp": datetime.now().isoformat(),
                "records": df.to_dict('records')
            }

            self.enriched_data["excel_enrichments"]["quarterly_enrichments"].append(enrichment_record)
            self.stats["excel_files_processed"] += 1
            self.stats["quarterly_data_enriched"] += len(df)
            print(f"  ✓ Extracted {len(df)} quarterly records")

    def add_buyer_demographics(self):
        """Add buyer demographic data (Layer 3 enrichment)"""
        print("\n" + "=" * 70)
        print("ADDING BUYER DEMOGRAPHICS (Layer 3 Enrichment)")
        print("=" * 70)

        # Find all buyer-related Excel files
        buyer_files = glob.glob(os.path.join(self.excel_dir, "Buyers_*.xlsx"))

        for filepath in buyer_files:
            print(f"\n📄 Processing: {os.path.basename(filepath)}")
            df = self.safe_read_excel(filepath)

            if df is None:
                continue

            # Determine demographic type from filename
            filename = os.path.basename(filepath)
            if "Agewise" in filename:
                demo_type = "age_distribution"
            elif "Genderwise" in filename:
                demo_type = "gender_distribution"
            elif "DistrictWise" in filename:
                demo_type = "district_distribution"
            elif "Localitywise" in filename:
                demo_type = "locality_distribution"
            elif "Pincode" in filename:
                demo_type = "pincode_distribution"
            elif "Satetwise" in filename:
                demo_type = "state_distribution"
            elif "Category" in filename:
                demo_type = "category_distribution"
            elif "Religionwise" in filename:
                demo_type = "religion_distribution"
            else:
                demo_type = "unknown"

            # Convert DataFrame to demographic record
            demographic_record = {
                "source_file": os.path.basename(filepath),
                "demographic_type": demo_type,
                "extraction_timestamp": datetime.now().isoformat(),
                "records": df.to_dict('records')
            }

            self.enriched_data["excel_enrichments"]["buyer_demographics"].append(demographic_record)
            self.stats["excel_files_processed"] += 1
            self.stats["buyer_data_added"] += len(df)
            print(f"  ✓ Extracted {len(df)} buyer demographic records ({demo_type})")

    def add_transaction_trends(self):
        """Add transaction trend data"""
        print("\n" + "=" * 70)
        print("ADDING TRANSACTION TRENDS")
        print("=" * 70)

        # Find all transaction-related Excel files
        transaction_files = glob.glob(os.path.join(self.excel_dir, "Transaction_Trends*.xlsx"))
        transaction_files.extend(glob.glob(os.path.join(self.excel_dir, "*Distribution*.xlsx")))
        transaction_files.extend(glob.glob(os.path.join(self.excel_dir, "Distance_Range*.xlsx")))
        transaction_files.extend(glob.glob(os.path.join(self.excel_dir, "Catchment_Projects*.xlsx")))

        for filepath in transaction_files:
            print(f"\n📄 Processing: {os.path.basename(filepath)}")
            df = self.safe_read_excel(filepath)

            if df is None:
                continue

            # Convert DataFrame to transaction record
            transaction_record = {
                "source_file": os.path.basename(filepath),
                "data_type": "transaction_metrics",
                "extraction_timestamp": datetime.now().isoformat(),
                "records": df.to_dict('records')
            }

            self.enriched_data["excel_enrichments"]["transaction_trends"].append(transaction_record)
            self.stats["excel_files_processed"] += 1
            self.stats["transaction_data_added"] += len(df)
            print(f"  ✓ Extracted {len(df)} transaction records")

    def enrich_all(self):
        """Execute all enrichment steps"""
        print("\n" + "=" * 70)
        print("PDF + EXCEL ENRICHMENT PIPELINE")
        print("=" * 70)
        print(f"PDF Source: {self.pdf_json_path}")
        print(f"Excel Directory: {self.excel_dir}")
        print(f"Total Excel Files: {len(glob.glob(os.path.join(self.excel_dir, '*.xlsx')))}")

        # Execute enrichment steps
        self.enrich_projects_from_excel()
        self.enrich_unit_types_from_excel()
        self.enrich_quarterly_from_excel()
        self.add_buyer_demographics()
        self.add_transaction_trends()

        # Update metadata
        self.enriched_data["metadata"]["enrichment_stats"] = self.stats
        self.enriched_data["metadata"]["enrichment_timestamp"] = datetime.now().isoformat()

    def save_enriched_data(self, output_path: str):
        """Save enriched data to JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.enriched_data, f, indent=2, ensure_ascii=False)

        print("\n" + "=" * 70)
        print("ENRICHMENT COMPLETE")
        print("=" * 70)
        print(f"Output: {output_path}")
        print(f"\nStatistics:")
        print(f"  Excel Files Processed: {self.stats['excel_files_processed']}")
        print(f"  Excel Files Skipped: {self.stats['excel_files_skipped']}")
        print(f"  Projects Enriched: {self.stats['projects_enriched']}")
        print(f"  Unit Types Enriched: {self.stats['unit_types_enriched']}")
        print(f"  Quarterly Data Enriched: {self.stats['quarterly_data_enriched']}")
        print(f"  Buyer Data Added: {self.stats['buyer_data_added']}")
        print(f"  Transaction Data Added: {self.stats['transaction_data_added']}")
        print("=" * 70)


def main():
    """Main execution"""
    pdf_json_path = "/Users/tusharsikand/Documents/Projects/liases-foras/data/extracted/lf_layer1_data_from_pdf.json"
    excel_dir = "/Users/tusharsikand/Documents/Projects/liases-foras/input"
    output_path = "/Users/tusharsikand/Documents/Projects/liases-foras/data/extracted/lf_layer1_enriched_from_excel.json"

    enricher = ExcelEnricher(pdf_json_path, excel_dir)
    enricher.enrich_all()
    enricher.save_enriched_data(output_path)


if __name__ == "__main__":
    main()
