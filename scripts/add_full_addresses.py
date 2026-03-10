"""
Add full addresses (street, pin code, area, city, state) to all projects

This script:
1. Uses existing coordinates to do REVERSE GEOCODING
2. Extracts formatted address from Google Maps Geocoding API
3. Adds 'address' as L0 attribute in v4 nested format
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


def reverse_geocode(lat: float, lon: float) -> dict:
    """
    Reverse geocode coordinates to get full address

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        Dict with address components or None if fails
    """
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "latlng": f"{lat},{lon}",
        "key": GOOGLE_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data['status'] == 'OK' and len(data['results']) > 0:
            result = data['results'][0]

            # Extract address components
            address_components = {}
            for component in result.get('address_components', []):
                types = component.get('types', [])
                if 'postal_code' in types:
                    address_components['postal_code'] = component.get('long_name')
                elif 'sublocality_level_1' in types or 'sublocality' in types:
                    address_components['area'] = component.get('long_name')
                elif 'locality' in types:
                    address_components['city'] = component.get('long_name')
                elif 'administrative_area_level_1' in types:
                    address_components['state'] = component.get('long_name')
                elif 'country' in types:
                    address_components['country'] = component.get('long_name')
                elif 'route' in types:
                    address_components['street'] = component.get('long_name')

            return {
                'formatted_address': result.get('formatted_address'),
                'components': address_components
            }
        else:
            print(f"  ⚠️  Reverse geocoding failed: {data['status']}")
            return None

    except Exception as e:
        print(f"  ❌ Error reverse geocoding: {e}")
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
    print("ADDING FULL ADDRESSES TO ALL PROJECTS")
    print("=" * 80)

    # Load v4 data
    print(f"\n📂 Loading data from: {DATA_FILE}")
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)

    projects = data.get('page_2_projects', [])
    print(f"✅ Found {len(projects)} projects")

    # Add addresses
    success_count = 0
    failed_count = 0

    for i, project in enumerate(projects, 1):
        # Extract project details
        project_name = project.get('projectName', {}).get('value', 'Unknown')
        lat_attr = project.get('latitude', {})
        lon_attr = project.get('longitude', {})

        lat = lat_attr.get('value') if isinstance(lat_attr, dict) else None
        lon = lon_attr.get('value') if isinstance(lon_attr, dict) else None

        print(f"\n[{i}/{len(projects)}] {project_name}")

        if not lat or not lon:
            print(f"  ⚠️  No coordinates found - skipping")
            failed_count += 1
            continue

        # Check if already has address
        if 'address' in project:
            existing_address = project['address'].get('value')
            if existing_address:
                print(f"  ✅ Already has address: {existing_address[:60]}...")
                success_count += 1
                continue

        # Reverse geocode
        print(f"  🔍 Reverse geocoding: {lat}, {lon}")
        address_data = reverse_geocode(lat, lon)

        if address_data:
            formatted_address = address_data['formatted_address']
            components = address_data['components']

            # Add address as L0 attribute
            project['address'] = create_l0_attribute(
                formatted_address,
                unit="Text",
                dimension="None"
            )

            # Add individual components as L0 attributes
            if 'postal_code' in components:
                project['postalCode'] = create_l0_attribute(
                    components['postal_code'],
                    unit="Text",
                    dimension="None"
                )

            if 'area' in components:
                project['area'] = create_l0_attribute(
                    components['area'],
                    unit="Text",
                    dimension="None"
                )

            if 'city' in components:
                project['city'] = create_l0_attribute(
                    components['city'],
                    unit="Text",
                    dimension="None"
                )

            if 'state' in components:
                project['state'] = create_l0_attribute(
                    components['state'],
                    unit="Text",
                    dimension="None"
                )

            if 'street' in components:
                project['street'] = create_l0_attribute(
                    components['street'],
                    unit="Text",
                    dimension="None"
                )

            print(f"  ✅ Added address: {formatted_address[:80]}...")
            if components.get('postal_code'):
                print(f"     Pin Code: {components['postal_code']}")
            success_count += 1
        else:
            failed_count += 1

    # Save updated data
    print("\n" + "=" * 80)
    print("SAVING UPDATED DATA")
    print("=" * 80)

    # Create backup
    backup_file = DATA_FILE.replace('.json', f'_backup_addresses_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    print(f"\n📦 Creating backup: {backup_file}")
    with open(backup_file, 'w') as f:
        json.dump(data, f, indent=2)

    # Save updated data
    print(f"💾 Saving updated data to: {DATA_FILE}")
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

    # Summary
    print("\n" + "=" * 80)
    print("ADDRESS ADDITION COMPLETE")
    print("=" * 80)
    print(f"\n✅ Successfully added addresses: {success_count}/{len(projects)}")
    print(f"❌ Failed: {failed_count}/{len(projects)}")

    if success_count == len(projects):
        print("\n🎉 All projects now have full addresses!")

    print(f"\n📍 Full addresses added as L0 attributes to all projects")
    print(f"🔄 Data file updated: {DATA_FILE}")
    print(f"📦 Backup created: {backup_file}")


if __name__ == "__main__":
    main()
