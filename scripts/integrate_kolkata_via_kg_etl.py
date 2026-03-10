"""
Integrate Kolkata R&D Excel Data via KG ETL System

This script:
1. Uploads Kolkata Excel files to KG ETL /api/upload endpoint
2. Retrieves the built knowledge graph
3. Transforms KG format to Liases Foras v4 nested format
4. Saves to data/extracted/kolkata/kolkata_v4_format.json
5. Updates system configuration

Author: Integration Pipeline
Date: 2024-02-23
"""

import requests
import json
import glob
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
KG_ETL_BASE_URL = "http://localhost:8000"
KOLKATA_DATA_DIR = "/Users/tusharsikand/Downloads/Kolkata R&D"
OUTPUT_DIR = "/Users/tusharsikand/Documents/Projects/liases-foras/data/extracted/kolkata"
GRAPH_NAME = "Kolkata_Real_Estate_Complete"

class KGETLIntegrator:
    """Integrates Kolkata data via KG ETL system"""

    def __init__(self, kg_etl_url: str = KG_ETL_BASE_URL):
        self.kg_etl_url = kg_etl_url
        self.session = requests.Session()

    def upload_excel_files(self, excel_dir: str, graph_name: str) -> Dict[str, Any]:
        """
        Upload multiple Excel files to KG ETL system and build unified KG

        Args:
            excel_dir: Directory containing Excel files
            graph_name: Name for the knowledge graph

        Returns:
            Response from KG ETL build endpoint with UUID
        """
        logger.info(f"Scanning for Excel files in: {excel_dir}")

        # Find all Excel files
        excel_files = []
        for ext in ['*.xlsx', '*.xls']:
            excel_files.extend(glob.glob(f"{excel_dir}/{ext}"))

        logger.info(f"Found {len(excel_files)} Excel files")

        # Upload files
        upload_url = f"{self.kg_etl_url}/api/upload"
        files = []

        for excel_file in excel_files:
            file_path = Path(excel_file)
            logger.info(f"  - {file_path.name}")
            files.append(
                ('files', (file_path.name, open(excel_file, 'rb'),
                          'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))
            )

        logger.info("Uploading files to KG ETL...")
        upload_response = self.session.post(upload_url, files=files)
        upload_response.raise_for_status()
        upload_data = upload_response.json()

        upload_id = upload_data['upload_id']
        logger.info(f"Upload successful. Upload ID: {upload_id}")

        # Build knowledge graph
        build_url = f"{self.kg_etl_url}/api/build"
        build_payload = {
            "name": graph_name,
            "upload_id": upload_id,
            "min_confidence": 0.7
        }

        logger.info("Building knowledge graph (this may take a while)...")
        build_response = self.session.post(build_url, json=build_payload)
        build_response.raise_for_status()
        build_data = build_response.json()

        logger.info(f"Knowledge graph built successfully!")
        logger.info(f"  UUID: {build_data['uuid']}")
        logger.info(f"  Tables: {build_data['tables']}")
        logger.info(f"  Relationships: {build_data['relationships']}")
        logger.info(f"  Total rows: {build_data['total_rows']}")

        return build_data

    def fetch_kg_data(self, kg_uuid: str) -> Dict[str, Any]:
        """
        Fetch the complete knowledge graph data

        Args:
            kg_uuid: UUID of the knowledge graph

        Returns:
            Complete KG data including tables, relationships, and metadata
        """
        logger.info(f"Fetching knowledge graph data: {kg_uuid}")

        # Fetch full graph
        graph_url = f"{self.kg_etl_url}/api/graphs/{kg_uuid}"
        response = self.session.get(graph_url)
        response.raise_for_status()
        kg_data = response.json()

        # Fetch metadata
        metadata_url = f"{self.kg_etl_url}/api/graphs/{kg_uuid}/metadata"
        meta_response = self.session.get(metadata_url)
        meta_response.raise_for_status()
        metadata = meta_response.json()

        kg_data['metadata'] = metadata

        logger.info(f"Knowledge graph fetched successfully")
        return kg_data

    def transform_to_v4_format(self, kg_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform KG ETL format to Liases Foras v4 nested format

        KG ETL Format:
        {
          "tables": [{
            "name": "Annual_Sales_Data",
            "rows": [{column1: value1, ...}, ...],
            "columns": [{name, data_type}, ...]
          }],
          "relationships": [{source_table, target_table, ...}],
          "metadata": {principal_entity, ...}
        }

        Liases Foras v4 Format:
        {
          "metadata": {...},
          "page_2_projects": [{
            "projectId": str,
            "projectName": str,
            "developerName": str,
            "location": str,
            "micromarketId": str,
            "totalSupplyUnits": {value, unit, dimension, relationships},
            "unsoldUnits": {value, unit, dimension, relationships},
            ...
          }],
          "enrichment_metadata": {...}
        }

        Args:
            kg_data: Knowledge graph data from KG ETL

        Returns:
            v4 nested format data
        """
        logger.info("Transforming KG data to v4 nested format...")

        projects = []
        principal_entity = kg_data.get('metadata', {}).get('principal_entity', {})

        # Find the principal entity table (likely contains project data)
        principal_table_name = principal_entity.get('name')
        principal_table = None

        for table in kg_data.get('tables', []):
            if table['name'] == principal_table_name:
                principal_table = table
                break

        if not principal_table:
            # Fallback: use first table with project-like structure
            for table in kg_data.get('tables', []):
                if any(keyword in table['name'].lower() for keyword in ['project', 'supply', 'sales']):
                    principal_table = table
                    break

        if not principal_table:
            logger.warning("No principal table found, using first table")
            principal_table = kg_data['tables'][0] if kg_data.get('tables') else {'rows': []}

        logger.info(f"Using table '{principal_table.get('name')}' as principal entity")
        logger.info(f"Found {len(principal_table.get('rows', []))} projects")

        # Transform each row to v4 project
        for idx, row in enumerate(principal_table.get('rows', [])):
            project = self._transform_row_to_v4_project(row, idx, kg_data)
            projects.append(project)

        # Create v4 structure
        v4_data = {
            "metadata": {
                "dataVersion": "Q3_FY25",
                "city": "Kolkata",
                "extractionTimestamp": datetime.utcnow().isoformat(),
                "totalProjects": len(projects),
                "dataSource": "KG_ETL_Kolkata_R&D",
                "principal_entity": principal_entity,
                "kg_metadata": kg_data.get('metadata', {}),
                "schemaVersion": "v4_nested"
            },
            "page_2_projects": projects,
            "enrichment_metadata": {
                "enrichmentDate": datetime.utcnow().isoformat(),
                "enrichmentPipeline": "KG_ETL_Integration",
                "totalTables": len(kg_data.get('tables', [])),
                "totalRelationships": len(kg_data.get('relationships', [])),
                "totalRows": sum(len(t.get('rows', [])) for t in kg_data.get('tables', []))
            }
        }

        logger.info(f"Transformation complete: {len(projects)} projects")
        return v4_data

    def _transform_row_to_v4_project(self, row: Dict[str, Any], idx: int, kg_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a single row to v4 project format"""

        # Extract project identifiers
        project_name = self._extract_field(row, ['project_name', 'projectName', 'name', 'project'])
        developer_name = self._extract_field(row, ['developer', 'developerName', 'developer_name'])
        location = self._extract_field(row, ['location', 'micromarket', 'region', 'area'])

        # Generate IDs
        project_id = f"KOL_{idx+1:04d}"
        micromarket_id = f"KOLKATA_{location.upper().replace(' ', '_')}" if location else f"KOLKATA_UNKNOWN_{idx}"

        # Extract numeric fields with v4 nested structure
        project = {
            "projectId": project_id,
            "projectName": project_name or f"Kolkata_Project_{idx+1}",
            "developerName": developer_name or "Unknown Developer",
            "location": location or "Kolkata",
            "micromarketId": micromarket_id,
            "layer": 0,  # Raw data layer
            "nodeType": "project",

            # Core metrics (U dimension - Units)
            "totalSupplyUnits": self._create_v4_attribute(
                self._extract_numeric(row, ['total_supply', 'totalUnits', 'supply_units', 'units']),
                "count", "U", "Total supply units"
            ),
            "unsoldUnits": self._create_v4_attribute(
                self._extract_numeric(row, ['unsold', 'unsold_units', 'unsoldUnits']),
                "count", "U", "Unsold units"
            ),
            "soldUnits": self._create_v4_attribute(
                self._extract_numeric(row, ['sold', 'sold_units', 'soldUnits']),
                "count", "U", "Sold units"
            ),
            "annualSalesUnits": self._create_v4_attribute(
                self._extract_numeric(row, ['annual_sales', 'annualSales', 'annual_sales_units']),
                "count/year", "U/T", "Annual sales units"
            ),

            # Area metrics (L² dimension)
            "totalSaleableArea": self._create_v4_attribute(
                self._extract_numeric(row, ['saleable_area', 'saleableArea', 'total_area']),
                "sqft", "L2", "Total saleable area"
            ),
            "unsoldArea": self._create_v4_attribute(
                self._extract_numeric(row, ['unsold_area', 'unsoldArea']),
                "sqft", "L2", "Unsold area"
            ),
            "unitSaleableSize": self._create_v4_attribute(
                self._extract_numeric(row, ['avg_size', 'unit_size', 'average_size']),
                "sqft", "L2", "Average unit size"
            ),

            # Price metrics (C/L² dimension - Cash per Area)
            "launchPricePSF": self._create_v4_attribute(
                self._extract_numeric(row, ['launch_psf', 'launchPSF', 'launch_price_psf']),
                "INR/sqft", "C/L2", "Launch price per sqft"
            ),
            "currentPricePSF": self._create_v4_attribute(
                self._extract_numeric(row, ['current_psf', 'currentPSF', 'price_psf', 'carpet_psf', 'saleable_psf']),
                "INR/sqft", "C/L2", "Current price per sqft"
            ),

            # Value metrics (C dimension - Cash)
            "annualSalesValue": self._create_v4_attribute(
                self._extract_numeric(row, ['annual_value', 'annualValue', 'sales_value']),
                "INR_Cr", "C", "Annual sales value"
            ),

            # Time metrics (T dimension)
            "projectAgeMonths": self._create_v4_attribute(
                self._extract_numeric(row, ['age_months', 'project_age', 'ageMonths']),
                "months", "T", "Project age"
            ),
            "monthsOfInventory": self._create_v4_attribute(
                self._extract_numeric(row, ['months_inventory', 'monthsInventory', 'inventory_months']),
                "months", "T", "Months of inventory"
            ),

            # Derived metrics (Layer 1)
            "soldPercentage": (self._extract_numeric(row, ['sold_pct', 'soldPercentage']) or 0),
            "unsoldPercentage": (self._extract_numeric(row, ['unsold_pct', 'unsoldPercentage']) or 100),
            "monthlySalesVelocityPct": (self._extract_numeric(row, ['velocity', 'sales_velocity']) or 0),
            "priceGrowthPct": (self._extract_numeric(row, ['price_growth', 'priceGrowth']) or 0),

            # Metadata
            "launchDate": self._extract_field(row, ['launch_date', 'launchDate']),
            "possessionDate": self._extract_field(row, ['possession_date', 'possessionDate']),
            "reraRegistered": self._extract_field(row, ['rera', 'reraRegistered']) or "Unknown",
            "projectSize": self._extract_field(row, ['project_size', 'size']) or "Medium",
            "extractionTimestamp": datetime.utcnow().isoformat(),
            "schemaVersion": "v4_nested"
        }

        return project

    def _create_v4_attribute(self, value: Any, unit: str, dimension: str, description: str) -> Dict[str, Any]:
        """Create v4 nested attribute structure"""
        return {
            "value": value if value is not None else 0,
            "unit": unit,
            "dimension": dimension,
            "relationships": [{"type": "IS", "target": dimension}],
            "source": "KG_ETL_Kolkata_R&D",
            "isPure": True,
            "description": description
        }

    def _extract_field(self, row: Dict[str, Any], field_names: List[str]) -> Optional[str]:
        """Extract field trying multiple possible column names"""
        for field in field_names:
            if field in row and row[field] is not None:
                return str(row[field])
        return None

    def _extract_numeric(self, row: Dict[str, Any], field_names: List[str]) -> Optional[float]:
        """Extract numeric field trying multiple possible column names"""
        for field in field_names:
            if field in row:
                try:
                    value = row[field]
                    if value is None or value == '':
                        continue
                    return float(str(value).replace(',', ''))
                except (ValueError, TypeError):
                    continue
        return None

    def save_v4_data(self, v4_data: Dict[str, Any], output_path: str):
        """Save v4 format data to JSON file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Saving v4 data to: {output_file}")
        with open(output_file, 'w') as f:
            json.dump(v4_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Data saved successfully ({output_file.stat().st_size / 1024:.2f} KB)")

    def run_integration(self, excel_dir: str, graph_name: str, output_path: str) -> Dict[str, Any]:
        """Run complete integration pipeline"""
        logger.info("=" * 80)
        logger.info("KOLKATA DATA INTEGRATION VIA KG ETL PIPELINE")
        logger.info("=" * 80)

        try:
            # Step 1: Upload and build KG
            logger.info("\n[Step 1/4] Uploading Excel files and building Knowledge Graph...")
            build_data = self.upload_excel_files(excel_dir, graph_name)
            kg_uuid = build_data['uuid']

            # Step 2: Fetch KG data
            logger.info("\n[Step 2/4] Fetching Knowledge Graph data...")
            kg_data = self.fetch_kg_data(kg_uuid)

            # Step 3: Transform to v4
            logger.info("\n[Step 3/4] Transforming to Liases Foras v4 format...")
            v4_data = self.transform_to_v4_format(kg_data)

            # Step 4: Save
            logger.info("\n[Step 4/4] Saving transformed data...")
            self.save_v4_data(v4_data, output_path)

            logger.info("\n" + "=" * 80)
            logger.info("INTEGRATION COMPLETE!")
            logger.info("=" * 80)
            logger.info(f"Knowledge Graph UUID: {kg_uuid}")
            logger.info(f"Total Projects: {len(v4_data['page_2_projects'])}")
            logger.info(f"Output File: {output_path}")
            logger.info("=" * 80)

            return {
                "status": "success",
                "kg_uuid": kg_uuid,
                "projects_count": len(v4_data['page_2_projects']),
                "output_path": output_path,
                "v4_data": v4_data
            }

        except Exception as e:
            logger.error(f"Integration failed: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }


def main():
    """Main execution"""
    integrator = KGETLIntegrator(KG_ETL_BASE_URL)

    output_path = f"{OUTPUT_DIR}/kolkata_v4_format.json"

    result = integrator.run_integration(
        excel_dir=KOLKATA_DATA_DIR,
        graph_name=GRAPH_NAME,
        output_path=output_path
    )

    if result['status'] == 'success':
        print("\n✅ Integration successful!")
        print(f"   Knowledge Graph: {result['kg_uuid']}")
        print(f"   Projects: {result['projects_count']}")
        print(f"   Output: {result['output_path']}")
        print("\nNext steps:")
        print("1. Update CITY_DATA_CONFIG in app/config.py")
        print("2. Update LOCATION_TREE in frontend/components/searchable_tree_selector.py")
        print("3. Restart Liases Foras backend")
        print("4. Test Kolkata region in frontend")
    else:
        print(f"\n❌ Integration failed: {result['error']}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
