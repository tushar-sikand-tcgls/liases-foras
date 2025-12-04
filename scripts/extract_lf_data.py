"""
Liases Foras HTML Data Extraction Script
Extracts project data from LF Micromarket Report HTML dashboard
Structures data into Layer 0 dimensions (U, L², T, CF) for knowledge graph
"""

import re
import json
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import html as html_module


class LFDataExtractor:
    """Extract real estate project data from Liases Foras HTML reports"""

    def __init__(self, html_file_path: str):
        self.html_file_path = html_file_path
        self.soup = None
        self.raw_data = {}
        self.layer0_data = []

    def load_html(self):
        """Load and parse HTML file"""
        print(f"Loading HTML file: {self.html_file_path}")
        with open(self.html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        self.soup = BeautifulSoup(html_content, 'html.parser')
        print(f"✓ HTML loaded successfully ({len(html_content)} characters)")

    def extract_angular_data(self):
        """Extract data from AngularJS ng-repeat directives and embedded JSON"""
        print("\nExtracting AngularJS embedded data...")

        # Method 1: Find all script tags with data assignments
        scripts = self.soup.find_all('script')
        for script in scripts:
            if script.string:
                # Look for variable assignments that might contain project data
                # Pattern: var projectData = [...]; or $scope.projects = [...];
                matches = re.findall(
                    r'(?:var\s+|scope\.)(\w+)\s*=\s*(\[.*?\]);',
                    script.string,
                    re.DOTALL
                )
                for var_name, data_str in matches:
                    if 'project' in var_name.lower() or 'market' in var_name.lower():
                        print(f"  Found variable: {var_name}")
                        self.raw_data[var_name] = data_str

        # Method 2: Extract from HTML table rows
        self.extract_from_tables()

    def extract_from_tables(self):
        """Extract data from HTML tables"""
        print("\nExtracting data from HTML tables...")

        # Find all tables
        tables = self.soup.find_all('table')
        print(f"  Found {len(tables)} tables")

        for idx, table in enumerate(tables):
            # Check if this is the "List of Marketable Projects" table
            headers = table.find_all('th')
            if headers:
                header_texts = [h.get_text(strip=True) for h in headers]
                print(f"  Table {idx + 1} headers: {header_texts[:5]}...")  # Show first 5 headers

                # Look for tables with project-related columns
                if any(keyword in ' '.join(header_texts).lower()
                       for keyword in ['project', 'units', 'supply', 'area', 'possession']):
                    print(f"    → Identified as project data table")
                    self.extract_project_table(table, header_texts)

    def extract_project_table(self, table, headers: List[str]):
        """Extract project data from a table"""
        rows = table.find_all('tr')
        print(f"    Processing {len(rows)} rows...")

        for row_idx, row in enumerate(rows[1:], 1):  # Skip header row
            cells = row.find_all(['td', 'th'])
            if len(cells) >= len(headers):
                row_data = {}
                for idx, cell in enumerate(cells):
                    if idx < len(headers):
                        # Priority 1: Check for title attribute (jqGrid stores data here)
                        title_value = cell.get('title')
                        if title_value:
                            row_data[headers[idx]] = title_value
                        else:
                            # Priority 2: Get text content
                            cell_text = cell.get_text(strip=True)
                            # Check for AngularJS bindings
                            ng_bind = cell.get('ng-bind')
                            if ng_bind:
                                row_data[headers[idx]] = {
                                    'value': cell_text,
                                    'binding': ng_bind
                                }
                            else:
                                row_data[headers[idx]] = cell_text

                if row_data:
                    project = self.map_to_layer0(row_data, headers)
                    if project:
                        self.layer0_data.append(project)
                        if row_idx <= 3:  # Show first 3 projects
                            print(f"      Row {row_idx}: {project.get('name', 'Unknown')}")

    def map_to_layer0(self, row_data: Dict, headers: List[str]) -> Optional[Dict]:
        """Map extracted data to Layer 0 dimensions (U, L², T, CF)"""

        # Initialize Layer 0 structure
        project = {
            'name': None,
            'developer': None,
            'location': None,
            'micromarket': None,

            # Layer 0: Raw Dimensions
            'layer0': {
                'U': {},  # Units (count of housing units)
                'L2': {},  # Area (square feet/meters)
                'T': {},  # Time (months/years)
                'CF': {}  # Cash Flow (INR)
            }
        }

        # Extract project name (various possible column names)
        for key, value in row_data.items():
            key_lower = key.lower()
            value_str = value['value'] if isinstance(value, dict) else value

            # Project name
            if any(k in key_lower for k in ['project', 'name']):
                project['name'] = value_str

            # Developer/Builder
            elif any(k in key_lower for k in ['developer', 'builder']):
                project['developer'] = value_str

            # Location
            elif 'location' in key_lower or 'address' in key_lower:
                project['location'] = value_str

            # Micromarket
            elif 'micromarket' in key_lower or 'micro' in key_lower:
                project['micromarket'] = value_str

            # U (Units) - Total Supply (Units)
            elif 'total supply' in key_lower and 'units' in key_lower:
                project['layer0']['U']['total_units'] = self.parse_number(value_str)

            # U (Units) - Unsold Units
            elif 'unsold' in key_lower and 'units' in key_lower:
                project['layer0']['U']['unsold_units'] = self.parse_number(value_str)

            # U (Units) - Configuration breakdown
            elif 'bhk' in key_lower or 'rk' in key_lower:
                # Extract BHK configuration (e.g., "1BHK", "2BHK", "3BHK")
                config = re.search(r'(\d+)\s*BHK', key, re.IGNORECASE)
                if config:
                    bhk_type = f"{config.group(1)}BHK"
                    project['layer0']['U'][bhk_type] = self.parse_number(value_str)

            # L² (Area) - Total area
            elif 'total' in key_lower and any(a in key_lower for a in ['area', 'sqft', 'sqm']):
                project['layer0']['L2']['total_area_sqft'] = self.parse_number(value_str)

            # L² (Area) - Average unit size
            elif 'average' in key_lower and any(a in key_lower for a in ['area', 'size', 'sqft']):
                project['layer0']['L2']['avg_unit_size_sqft'] = self.parse_number(value_str)

            # T (Time) - Possession date
            elif 'possession' in key_lower or 'completion' in key_lower:
                project['layer0']['T']['possession_date'] = value_str

            # T (Time) - Launch date
            elif 'launch' in key_lower:
                project['layer0']['T']['launch_date'] = value_str

            # CF (Cash Flow) - Average price
            elif 'average price' in key_lower or 'avg price' in key_lower:
                project['layer0']['CF']['avg_price_inr'] = self.parse_number(value_str)

            # CF (Cash Flow) - Price per sqft
            elif 'price' in key_lower and 'sqft' in key_lower:
                project['layer0']['CF']['price_per_sqft'] = self.parse_number(value_str)

        # Only return if we have at least a name and some dimension data
        if project['name'] and any(project['layer0'].values()):
            return project
        return None

    @staticmethod
    def parse_number(value_str: str) -> Optional[float]:
        """Parse number from string (handles commas, decimals)"""
        if not value_str:
            return None

        try:
            # Remove commas and whitespace
            cleaned = re.sub(r'[,\s]', '', str(value_str))
            # Extract first number
            match = re.search(r'[\d.]+', cleaned)
            if match:
                return float(match.group())
        except:
            pass

        return None

    def export_to_json(self, output_path: str):
        """Export extracted data to JSON"""
        print(f"\nExporting to JSON: {output_path}")

        output_data = {
            'metadata': {
                'source_file': self.html_file_path,
                'total_projects': len(self.layer0_data),
                'extraction_method': 'HTML + AngularJS parsing'
            },
            'projects': self.layer0_data
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"✓ Exported {len(self.layer0_data)} projects to {output_path}")

        # Print sample data
        if self.layer0_data:
            print(f"\n=== Sample Project Data ===")
            sample = self.layer0_data[0]
            print(f"Name: {sample['name']}")
            print(f"Total Units (U): {sample['layer0']['U'].get('total_units', 'N/A')}")
            print(f"Area (L²): {sample['layer0']['L2'].get('total_area_sqft', 'N/A')} sqft")
            print(f"Possession (T): {sample['layer0']['T'].get('possession_date', 'N/A')}")
            print(f"Avg Price (CF): ₹{sample['layer0']['CF'].get('avg_price_inr', 'N/A')}")

    def run(self, output_json: str = None):
        """Run complete extraction pipeline"""
        print("="*60)
        print("LIASES FORAS DATA EXTRACTION")
        print("="*60)

        self.load_html()
        self.extract_angular_data()

        if output_json:
            self.export_to_json(output_json)

        print(f"\n{'='*60}")
        print(f"EXTRACTION COMPLETE")
        print(f"Total projects extracted: {len(self.layer0_data)}")
        print(f"{'='*60}\n")

        return self.layer0_data


def main():
    """Main execution"""
    # Input and output paths
    html_file = "/Users/tusharsikand/Documents/Projects/liases-foras/docs/sample/Micromarket Report.html"
    output_json = "/Users/tusharsikand/Documents/Projects/liases-foras/data/extracted/lf_projects_layer0.json"

    # Run extraction
    extractor = LFDataExtractor(html_file)
    extractor.run(output_json)

    # Test query: "How many units are there in Sara City?"
    print("\n=== TEST QUERY ===")
    print("Q: How many units are there in Sara City?")

    for project in extractor.layer0_data:
        if project['name'] and 'sara city' in project['name'].lower():
            units = project['layer0']['U'].get('total_units')
            print(f"A: Sara City has {units} units")
            print(f"   (Expected: 1,109)")
            break
    else:
        print("A: Sara City not found in extracted data")


if __name__ == "__main__":
    main()
