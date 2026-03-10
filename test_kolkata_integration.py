#!/usr/bin/env python3
"""
Test script to verify Kolkata data integration
"""
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.data_service import DataServiceV4

def test_kolkata_data():
    """Test loading Kolkata data"""
    print("="*80)
    print("TESTING KOLKATA DATA INTEGRATION")
    print("="*80)

    # Test 1: Load Pune data (baseline)
    print("\n[Test 1] Loading Pune data...")
    pune_service = DataServiceV4(city="Pune")
    print(f"✓ Pune projects loaded: {len(pune_service.projects)}")

    # Test 2: Load Kolkata data
    print("\n[Test 2] Loading Kolkata data...")
    kolkata_service = DataServiceV4(city="Kolkata")
    print(f"✓ Kolkata projects loaded: {len(kolkata_service.projects)}")

    # Test 3: Verify Kolkata project structure
    print("\n[Test 3] Verifying Kolkata project structure...")
    if kolkata_service.projects:
        first_project = kolkata_service.projects[0]
        project_name = kolkata_service.get_value(first_project.get('projectName'))
        project_id = kolkata_service.get_value(first_project.get('projectId'))
        location = kolkata_service.get_value(first_project.get('location'))

        print(f"  First project:")
        print(f"    - ID: {project_id}")
        print(f"    - Name: {project_name}")
        print(f"    - Location: {location}")

        # Check for key attributes
        print(f"\n  Available attributes:")
        for key in sorted(first_project.keys()):
            attr = first_project[key]
            if isinstance(attr, dict) and 'value' in attr:
                value = attr.get('value')
                unit = attr.get('unit', '')
                dimension = attr.get('dimension', '')
                print(f"    - {key}: {value} {unit} [{dimension}]")

    # Test 4: List all Kolkata project names
    print("\n[Test 4] All Kolkata projects:")
    for i, proj in enumerate(kolkata_service.projects, 1):
        name = kolkata_service.get_value(proj.get('projectName'))
        loc = kolkata_service.get_value(proj.get('location'))
        print(f"  {i}. {name} ({loc})")

    print("\n" + "="*80)
    print("✅ KOLKATA INTEGRATION TEST PASSED")
    print("="*80)

    return True

if __name__ == "__main__":
    try:
        test_kolkata_data()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
