#!/usr/bin/env python3
"""
Comprehensive verification of all numeric columns for aggregation functions
Tests: Total, Average (Mean), and validates column selection
"""

from app.services.data_service import DataServiceV4
import statistics

data_service = DataServiceV4()
projects = data_service.get_all_projects()

# Get all numeric columns from first project
numeric_columns = []
if projects:
    first_project = projects[0]
    for key in first_project.keys():
        value = data_service.get_value(first_project.get(key))
        if isinstance(value, (int, float)) and key not in ['projectId', 'priorityWeight']:
            numeric_columns.append(key)

print("=" * 100)
print("COMPREHENSIVE AGGREGATION VERIFICATION FOR ALL NUMERIC COLUMNS")
print("=" * 100)
print()

for column in sorted(numeric_columns):
    print(f"Column: {column}")
    print("-" * 100)

    # Collect values
    values = []
    project_names = []
    for project in projects:
        value = data_service.get_value(project.get(column))
        if value is not None and isinstance(value, (int, float)):
            values.append(value)
            project_names.append(data_service.get_value(project.get('projectName'))[:30])

    if values:
        # Calculate aggregations
        total = sum(values)
        average = total / len(values)
        median = statistics.median(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0

        print(f"  Projects analyzed: {len(values)}")
        print(f"  Total:   {total:15,.2f}")
        print(f"  Average: {average:15,.2f}")
        print(f"  Median:  {median:15,.2f}")
        print(f"  Std Dev: {std_dev:15,.2f}")
        print(f"  Min:     {min(values):15,.2f} ({project_names[values.index(min(values))]})")
        print(f"  Max:     {max(values):15,.2f} ({project_names[values.index(max(values))]})")

        # Show first 5 values for verification
        print(f"  First 5 values: {[f'{v:.0f}' for v in values[:5]]}")

    else:
        print(f"  ❌ No numeric values found")

    print()

print("=" * 100)
print("VERIFICATION COMPLETE")
print("=" * 100)
print()
print("Key Findings:")
print("- project SizeUnits: Should be used for 'Project Size' queries")
print("- totalSupplyUnits: Should be used for 'Supply/Inventory' queries only")
print("- Verify that averages match expected calculations")
