#!/usr/bin/env python3
"""
Test Proximity Search - Direct Data Store Layer

Tests the geospatial proximity search functionality at the data store level
before wiring it into the full LangGraph orchestrator.
"""

from app.services.json_data_store import JSONDataStore

print("=" * 80)
print("PROXIMITY SEARCH TEST - Direct Data Store Layer")
print("=" * 80)

# Initialize data store
store = JSONDataStore()

# Test 1: Find projects within 2 KM of Sara City
print("\n" + "=" * 80)
print("TEST 1: Projects within 2 KM of Sara City")
print("=" * 80)

try:
    results = store.find_projects_near("Sara City", radius_km=2.0)

    print(f"\n✓ Found {len(results)} projects within 2 KM of Sara City:")
    print()

    for i, project in enumerate(results, 1):
        # Extract values from nested structure
        proj_name_obj = project.get('projectName', {})
        if isinstance(proj_name_obj, dict):
            project_name = proj_name_obj.get('value', 'Unknown')
        else:
            project_name = proj_name_obj

        distance = project.get('distance_km', 0)

        loc_obj = project.get('location', {})
        if isinstance(loc_obj, dict):
            location = loc_obj.get('value', 'Unknown')
        else:
            location = loc_obj

        print(f"{i}. {project_name}")
        print(f"   Distance: {distance:.3f} km")
        print(f"   Location: {location}")
        print()

except ValueError as e:
    print(f"\n✗ Error: {e}")
except Exception as e:
    print(f"\n✗ Unexpected error: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Find projects within 5 KM of Sara City
print("=" * 80)
print("TEST 2: Projects within 5 KM of Sara City")
print("=" * 80)

try:
    results = store.find_projects_near("Sara City", radius_km=5.0)

    print(f"\n✓ Found {len(results)} projects within 5 KM of Sara City:")
    print()

    for i, project in enumerate(results, 1):
        # Extract values from nested structure
        proj_name_obj = project.get('projectName', {})
        if isinstance(proj_name_obj, dict):
            project_name = proj_name_obj.get('value', 'Unknown')
        else:
            project_name = proj_name_obj

        distance = project.get('distance_km', 0)

        print(f"{i}. {project_name}: {distance:.3f} km")

except ValueError as e:
    print(f"\n✗ Error: {e}")

# Test 3: Try with a non-existent project
print("\n" + "=" * 80)
print("TEST 3: Non-existent project (should error)")
print("=" * 80)

try:
    results = store.find_projects_near("Nonexistent Project", radius_km=2.0)
    print(f"\n✗ Should have raised ValueError but got {len(results)} results")
except ValueError as e:
    print(f"\n✓ Correctly raised ValueError: {e}")

print("\n" + "=" * 80)
print("PROXIMITY SEARCH TESTS COMPLETE")
print("=" * 80)
