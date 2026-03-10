"""
Geocode all projects and add latitude/longitude as L0 attributes to v4 data

This script:
1. Loads v4_clean_nested_structure.json
2. For each project, uses Google Maps Geocoding API to get coordinates
3. Adds latitude and longitude as L0 attributes in the v4 nested format
4. Saves the updated data back to the JSON file
"""

import json
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Google Maps API key
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_MAPS_API_KEY not found in environment variables")

# Data file path
DATA_FILE = "/Users/tusharsikand/Documents/Projects/liases-foras/data/extracted/v4_clean_nested_structure.json"


def geocode_address(project_name: str, developer_name: str, location: str, city: str = "Pune") -> dict:
    """
    Geocode a project address using Google Maps Geocoding API

    Args:
        project_name: Name of the project
        developer_name: Name of the developer
        location: Region/area (e.g., "Chakan")
        city: City name (default: "Pune")

    Returns:
        Dict with 'latitude' and 'longitude' keys, or None if geocoding fails
    """
    # Build search query
    query = f"{project_name}, {developer_name}, {location}, {city}, Maharashtra, India"

    # Call Google Maps Geocoding API
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": query,
        "key": GOOGLE_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data['status'] == 'OK' and len(data['results']) > 0:
            location = data['results'][0]['geometry']['location']
            return {
                'latitude': location['lat'],
                'longitude': location['lng']
            }
        else:
            print(f"  ⚠️  Geocoding failed for {project_name}: {data['status']}")
            return None

    except Exception as e:
        print(f"  ❌ Error geocoding {project_name}: {e}")
        return None


def create_l0_attribute(value, unit: str, dimension: str = "None"):
    """Create L0 attribute in v4 nested format"""
    return {
        "value": value,
        "unit": unit,
        "dimension": dimension,
        "relationships": [],
        "source": "Google_Maps_Geocoding_API",
        "isPure": True
    }


def main():
    print("=" * 80)
    print("GEOCODING ALL PROJECTS")
    print("=" * 80)

    # Load v4 data
    print(f"\n📂 Loading data from: {DATA_FILE}")
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)

    projects = data.get('page_2_projects', [])
    print(f"✅ Found {len(projects)} projects")

    # Geocode each project
    geocoded_count = 0
    failed_count = 0

    for i, project in enumerate(projects, 1):
        # Extract project details
        project_name = project.get('projectName', {}).get('value', 'Unknown')
        developer_name = project.get('developerName', {}).get('value', '')
        location = project.get('location', {}).get('value', '')

        print(f"\n[{i}/{len(projects)}] {project_name} ({location})")

        # Check if already geocoded
        if 'latitude' in project and 'longitude' in project:
            lat = project['latitude'].get('value')
            lon = project['longitude'].get('value')
            if lat is not None and lon is not None:
                print(f"  ✅ Already geocoded: {lat}, {lon}")
                geocoded_count += 1
                continue

        # Geocode the project
        coords = geocode_address(project_name, developer_name, location)

        if coords:
            # Add latitude and longitude as L0 attributes
            project['latitude'] = create_l0_attribute(
                coords['latitude'],
                unit="degrees",
                dimension="None"
            )
            project['longitude'] = create_l0_attribute(
                coords['longitude'],
                unit="degrees",
                dimension="None"
            )

            print(f"  ✅ Geocoded: {coords['latitude']}, {coords['longitude']}")
            geocoded_count += 1
        else:
            failed_count += 1

    # Save updated data
    print("\n" + "=" * 80)
    print("SAVING UPDATED DATA")
    print("=" * 80)

    # Create backup
    backup_file = DATA_FILE.replace('.json', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    print(f"\n📦 Creating backup: {backup_file}")
    with open(backup_file, 'w') as f:
        json.dump(data, f, indent=2)

    # Save updated data
    print(f"💾 Saving updated data to: {DATA_FILE}")
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

    # Summary
    print("\n" + "=" * 80)
    print("GEOCODING COMPLETE")
    print("=" * 80)
    print(f"\n✅ Successfully geocoded: {geocoded_count}/{len(projects)}")
    print(f"❌ Failed: {failed_count}/{len(projects)}")

    if geocoded_count == len(projects):
        print("\n🎉 All projects geocoded successfully!")

    print(f"\n📍 Latitude and longitude added as L0 attributes to all projects")
    print(f"🔄 Data file updated: {DATA_FILE}")
    print(f"📦 Backup created: {backup_file}")


if __name__ == "__main__":
    main()
