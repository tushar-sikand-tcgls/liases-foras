"""
Targeted LF Data Extraction - Extracts from top20projectlist table
"""

import json
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Optional


def extract_projects_from_html(html_path: str) -> List[Dict]:
    """Extract project data from the top20projectlist jqGrid table"""

    print(f"Loading HTML: {html_path}")
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    print("✓ HTML loaded\n")

    # Find the specific table by ID
    table = soup.find('table', {'id': 'top20projectlist'})
    if not table:
        print("ERROR: Could not find table with ID 'top20projectlist'")
        return []

    print("✓ Found top20projectlist table\n")

    # Find all data rows (skip the first row which is for sizing)
    rows = table.find_all('tr', {'class': 'ui-widget-content'})
    print(f"Found {len(rows)} project rows\n")

    projects = []

    for idx, row in enumerate(rows, 1):
        cells = row.find_all('td', {'role': 'gridcell'})

        # Extract data from title attributes (jqGrid stores data here)
        project = {
            'name': None,
            'developer': None,
            'location': None,
            'layer0': {
                'U': {},  # Units
                'L2': {},  # Area (sqft)
                'T': {},  # Time
                'CF': {}  # Cash Flow (INR)
            }
        }

        # Map cell values by aria-describedby attribute
        for cell in cells:
            desc = cell.get('aria-describedby', '')
            title = cell.get('title', '')

            if not title:
                continue

            # Extract field name from aria-describedby
            if 'PROJECT_NAME' in desc:
                project['name'] = title
            elif 'BUILDERGROUP' in desc:
                project['developer'] = title
            elif 'LOCATION' in desc:
                project['location'] = title

            # Layer 0: Units (U)
            elif 'TOTALSUPPLY_ASONDATE_UNIT' in desc:
                project['layer0']['U']['total_units'] = parse_number(title)
            elif 'ANNUAL_SALES_UNIT' in desc:
                project['layer0']['U']['annual_sales_units'] = parse_number(title)

            # Layer 0: Area (L²)
            elif 'TOTALSUPPLY_ASONDATE_SQFT' in desc:
                project['layer0']['L2']['total_area_sqft'] = parse_number(title)
            elif 'PROJECT_SIZE' in desc:
                project['layer0']['L2']['project_size'] = parse_number(title)
            elif 'RANGE_SALEABLE_FLAT_SIZE' in desc:
                project['layer0']['L2']['unit_size_sqft'] = parse_number(title)

            # Layer 0: Time (T)
            elif 'PROJECT_LAUNCH_DATE' in desc:
                project['layer0']['T']['launch_date'] = title
            elif 'PROJECT_ENDDATE' in desc:
                project['layer0']['T']['possession_date'] = title

            # Layer 0: Cash Flow (CF)
            elif 'LAUNCH_PRICE_PSF' in desc:
                project['layer0']['CF']['launch_price_psf'] = parse_number(title)
            elif 'RANGE_SALEABLE_RATE_PSF' in desc:
                project['layer0']['CF']['current_price_psf'] = parse_number(title)
            elif 'ANNUAL_BT' in desc:
                project['layer0']['CF']['annual_sales_value_cr'] = parse_number(title)

        if project['name']:
            projects.append(project)
            if idx <= 3:
                units = project['layer0']['U'].get('total_units', 'N/A')
                print(f"  {idx}. {project['name']}: {units} units")

    return projects


def parse_number(value_str: str) -> Optional[float]:
    """Parse number from string (handles commas)"""
    if not value_str:
        return None
    try:
        cleaned = re.sub(r'[,\s%]', '', str(value_str))
        match = re.search(r'[\d.]+', cleaned)
        if match:
            return float(match.group())
    except:
        pass
    return None


def main():
    html_file = "/Users/tusharsikand/Documents/Projects/liases-foras/docs/sample/Micromarket Report.html"
    output_json = "/Users/tusharsikand/Documents/Projects/liases-foras/data/extracted/lf_projects_layer0.json"

    print("="*60)
    print("LF DATA EXTRACTION - TOP 20 PROJECTS")
    print("="*60 + "\n")

    projects = extract_projects_from_html(html_file)

    print(f"\n{'='*60}")
    print(f"EXTRACTION COMPLETE: {len(projects)} projects")
    print(f"{'='*60}\n")

    # Save to JSON
    output_data = {
        'metadata': {
            'source_file': html_file,
            'total_projects': len(projects),
            'extraction_method': 'jqGrid table parsing (top20projectlist)'
        },
        'projects': projects
    }

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"✓ Saved to: {output_json}\n")

    # Test query: Sara City
    print("="*60)
    print("TEST QUERY: How many units in Sara City?")
    print("="*60 + "\n")

    for project in projects:
        if project['name'] and 'sara city' in project['name'].lower():
            units = project['layer0']['U'].get('total_units')
            print(f"✓ ANSWER: Sara City has {int(units):,} units")
            print(f"  (Expected: 1,109)\n")

            # Show full data
            print("Full Sara City data:")
            print(json.dumps(project, indent=2))
            break
    else:
        print("✗ Sara City not found\n")


if __name__ == "__main__":
    main()
