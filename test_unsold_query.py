#!/usr/bin/env python3
"""
Test unsold/sold query handling with dimensional validation
"""

from app.services.simple_query_handler import SimpleQueryHandler
from app.services.data_service import DataServiceV4

# Initialize services
data_service = DataServiceV4()
handler = SimpleQueryHandler(data_service)

print("=" * 100)
print("TESTING UNSOLD/SOLD QUERY HANDLING WITH DIMENSIONAL VALIDATION")
print("=" * 100)
print()

# Test Case 1: Unsold query (should return calculated units)
print("Test 1: What is the unsold for 'The Urbana'")
print("-" * 100)

result1 = handler.handle_query("What is the unsold for 'The Urbana'")

if result1.status == 'success':
    result_data = result1.result
    provenance = result1.provenance or {}

    print(f"Result Value: {result_data.get('value')}")
    print(f"Result Unit: {result_data.get('unit')}")
    print(f"Result Text: {result_data.get('text')}")
    print(f"Dimension: {result1.dimension}")
    print(f"Target Attribute: {provenance.get('targetAttribute', 'N/A')}")

    # Manual verification
    project = data_service.get_project_by_name("The Urbana")
    if project:
        print("\nManual Verification:")
        project_size = data_service.get_value(project.get('projectSizeUnits'))
        unsold_pct = data_service.get_value(project.get('unsoldPct'))
        print(f"  projectSizeUnits: {project_size}")
        print(f"  unsoldPct: {unsold_pct}%")
        if project_size and unsold_pct is not None:
            expected_unsold_units = round(project_size * (unsold_pct / 100))
            print(f"  Expected unsold_units: {expected_unsold_units} (calculated: {project_size} × {unsold_pct/100})")

            # Check if result matches
            if result_data.get('value') == expected_unsold_units:
                print(f"  ✅ PASS: Result matches expected value")
            else:
                print(f"  ❌ FAIL: Result {result_data.get('value')} doesn't match expected {expected_unsold_units}")
else:
    print(f"❌ Query failed: Status={result1.status}")

print()
print()

# Test Case 2: Sold query (should return calculated units)
print("Test 2: What is the sold for 'The Urbana'")
print("-" * 100)

result2 = handler.handle_query("What is the sold for 'The Urbana'")

if result2.status == 'success':
    result_data = result2.result
    provenance = result2.provenance or {}

    print(f"Result Value: {result_data.get('value')}")
    print(f"Result Unit: {result_data.get('unit')}")
    print(f"Result Text: {result_data.get('text')}")
    print(f"Dimension: {result2.dimension}")
    print(f"Target Attribute: {provenance.get('targetAttribute', 'N/A')}")

    # Manual verification
    project = data_service.get_project_by_name("The Urbana")
    if project:
        print("\nManual Verification:")
        project_size = data_service.get_value(project.get('projectSizeUnits'))
        sold_pct = data_service.get_value(project.get('soldPct'))
        print(f"  projectSizeUnits: {project_size}")
        print(f"  soldPct: {sold_pct}%")
        if project_size and sold_pct is not None:
            expected_sold_units = round(project_size * (sold_pct / 100))
            print(f"  Expected sold_units: {expected_sold_units} (calculated: {project_size} × {sold_pct/100})")

            # Check if result matches
            if result_data.get('value') == expected_sold_units:
                print(f"  ✅ PASS: Result matches expected value")
            else:
                print(f"  ❌ FAIL: Result {result_data.get('value')} doesn't match expected {expected_sold_units}")
else:
    print(f"❌ Query failed: Status={result2.status}")

print()
print()

# Test Case 3: Unsold percentage query (should return percentage)
print("Test 3: What is the unsold percentage for 'The Urbana'")
print("-" * 100)

result3 = handler.handle_query("What is the unsold percentage for 'The Urbana'")

if result3.status == 'success':
    result_data = result3.result
    provenance = result3.provenance or {}

    print(f"Result Value: {result_data.get('value')}")
    print(f"Result Unit: {result_data.get('unit')}")
    print(f"Result Text: {result_data.get('text')}")
    print(f"Dimension: {result3.dimension}")
    print(f"Target Attribute: {provenance.get('targetAttribute', 'N/A')}")

    # Manual verification
    project = data_service.get_project_by_name("The Urbana")
    if project:
        print("\nManual Verification:")
        unsold_pct = data_service.get_value(project.get('unsoldPct'))
        print(f"  unsoldPct: {unsold_pct}%")

        # Check if result matches and dimension is Dimensionless
        if result_data.get('value') == unsold_pct and result_data.get('unit') == '%':
            print(f"  ✅ PASS: Result matches expected percentage value")
        else:
            print(f"  ❌ FAIL: Result doesn't match expected percentage")
else:
    print(f"❌ Query failed: Status={result3.status}")

print()
print("=" * 100)
print("TEST COMPLETE")
print("=" * 100)
