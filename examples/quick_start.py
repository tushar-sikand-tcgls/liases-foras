#!/usr/bin/env python3
"""
Quick Start Examples - Clean JSON Data Store
Simple examples to get started with dimensional queries

Author: Claude Code
Date: 2025-11-30
"""

import sys
from pathlib import Path

# Add app directory to path
sys.path.append(str(Path(__file__).parent.parent))
from app.services.json_data_store import JSONDataStore

def main():
    print("="*70)
    print("QUICK START - CLEAN JSON DATA STORE")
    print("="*70)

    # Initialize data store
    store = JSONDataStore()
    print("\n✓ Data loaded successfully!")

    # Example 1: Get a project
    print("\n" + "-"*70)
    print("Example 1: Get Sara City Project")
    print("-"*70)

    sara_city = store.get_project_by_name("Sara City")

    # Show a few key attributes
    attrs_to_show = ['projectName', 'totalSupplyUnits', 'currentPricePSF', 'annualSalesValueCr']

    for attr in attrs_to_show:
        if attr in sara_city:
            data = sara_city[attr]
            print(f"\n{attr}:")
            print(f"  Value: {data['value']}")
            print(f"  Unit: {data['unit']}")
            print(f"  Dimension: {data['dimension']}")

    # Example 2: Find all price attributes
    print("\n" + "-"*70)
    print("Example 2: Find All Price Attributes (C/L² dimension)")
    print("-"*70)

    price_attrs = store.find_attributes_by_dimension("C/L²", node_type="project")

    print(f"\nFound {len(price_attrs)} price attributes:")
    for attr in price_attrs[:5]:  # Show first 5
        print(f"  • {attr['nodeName']:20s} | {attr['attribute']:20s} | {attr['value']:8.0f} {attr['unit']}")

    # Example 3: Dimensional profile
    print("\n" + "-"*70)
    print("Example 3: Sara City Dimensional Profile")
    print("-"*70)

    profile = store.get_dimensional_profile("Sara City")

    print("\nUnits (U) Dimension:")
    for attr in profile['U']:
        print(f"  • {attr['attribute']:25s}: {attr['value']:8.0f} {attr['unit']}")

    print("\nCash Flow (C) Dimension:")
    for attr in profile['C']:
        print(f"  • {attr['attribute']:25s}: {attr['value']:8.0f} {attr['unit']}")

    print("\nComposite Dimensions:")
    for attr in profile['Composite'][:5]:  # Show first 5
        print(f"  • {attr['attribute']:25s}: {attr['value']:8.2f} {attr['unit']:15s} ({attr['dimension']})")

    # Example 4: Compare projects
    print("\n" + "-"*70)
    print("Example 4: Compare Top 3 Projects")
    print("-"*70)

    comparison = store.compare_projects(
        project_names=["Sara City", "The Urbana", "Gulmohar\nCity"],
        attributes=["totalSupplyUnits", "currentPricePSF", "annualSalesUnits"]
    )

    for attr, projects in comparison.items():
        print(f"\n{attr}:")
        for project_name, data in projects.items():
            print(f"  {project_name:20s}: {data['value']:8.2f} {data['unit']}")

    # Example 5: Find velocity metrics
    print("\n" + "-"*70)
    print("Example 5: Find All Velocity Metrics (Fraction/T dimension)")
    print("-"*70)

    velocity_attrs = store.find_attributes_by_dimension("Fraction/T", node_type="project")

    print(f"\nFound {len(velocity_attrs)} velocity metrics:")
    for attr in velocity_attrs[:5]:
        value_pct = attr['value'] * 100  # Convert fraction to percentage
        print(f"  • {attr['nodeName']:20s} | {attr['attribute']:25s} | {value_pct:6.2f}%/month")

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    stats = store.get_stats()
    print(f"\nTotal Projects: {stats['projects']}")
    print(f"Total Unit Types: {stats['unit_types']}")
    print(f"Total Quarterly Summaries: {stats['quarterly_summaries']}")
    print(f"\nData Version: {stats['data_version']}")
    print(f"Extraction Timestamp: {stats['extraction_timestamp']}")

    print("\n" + "="*70)
    print("That's it! Clean, simple, fast.")
    print("No Neo4j complexity, no wobbly graphs, just pure Python + JSON.")
    print("="*70)


if __name__ == "__main__":
    main()
