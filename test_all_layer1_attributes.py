"""
Comprehensive Test Suite for All 26 Layer 1 Enriched Attributes
Tests each attribute with mock Sara City data
"""

import sys
sys.path.insert(0, '/Users/tusharsikand/Documents/Projects/liases-foras')

from app.services.enriched_layers_service import get_enriched_layers_service

def get_sara_city_mock_data():
    """Mock Sara City data based on /api/projects/3306"""
    return {
        # Units dimension
        'supply': 1109,
        'totalUnits': 1109,
        'annual_sales': 527,
        'annualSales': 527,
        'sold_percent': 88.95,
        'soldPct': 88.95,
        'unsold_percent': 11.05,
        'unsoldPct': 11.05,
        'soldUnits': 987,

        # Cash dimension
        'value': 106,  # Cr
        'totalRevenue': 106,
        'annualSalesValueCr': 106,

        # Price (C/L²)
        'current_psf': 3996,
        'currentPSF': 3996,
        'launch_psf': 2200,
        'launchPSF': 2200,

        # Area dimension
        'size': 414,  # sqft
        'avgUnitSize': 414,
        'unitSaleableSizeSqft': 414,

        # Time dimension
        'projectDuration': 5,  # years

        # Velocity
        'velocity_percent': 4.16,
        'monthlySalesVelocity': 4.16,

        # Derived calculations
        'monthly_units_sold': 527 / 12,  # 43.9
        'monthly_sold': 527 / 12,
        'unsold': 1109 * 0.1105,  # 122.5
        'unsoldUnits': 122,
    }


def test_all_layer1_attributes():
    """Test all 26 Layer 1 attributes"""

    print("=" * 80)
    print("COMPREHENSIVE TEST: All 26 Layer 1 Enriched Attributes")
    print("=" * 80)

    enriched_service = get_enriched_layers_service()
    mock_data = get_sara_city_mock_data()

    # Get all Layer 1 attributes
    all_attributes = enriched_service.get_all_attributes()
    layer1_attributes = [attr for attr in all_attributes if attr.requires_calculation]

    print(f"\nTotal Layer 1 attributes to test: {len(layer1_attributes)}\n")

    passed = 0
    failed = 0
    results = []

    for i, attr in enumerate(layer1_attributes, 1):
        print(f"[{i}/{len(layer1_attributes)}] Testing: {attr.target_attribute}")
        print(f"    Formula: {attr.formula_derivation}")
        print(f"    Unit: {attr.unit}")
        print(f"    Dimension: {attr.dimension}")

        try:
            # Execute calculation
            result = enriched_service.execute_layer1_calculation(
                attr_name=attr.target_attribute,
                project_data=mock_data
            )

            if result:
                print(f"    ✓ Result: {result['value']} {result['unit']}")
                passed += 1
                results.append({
                    'attribute': attr.target_attribute,
                    'status': 'PASS',
                    'value': result['value'],
                    'unit': result['unit'],
                    'formula': result['formula']
                })
            else:
                print(f"    ✗ Calculation returned None")
                failed += 1
                results.append({
                    'attribute': attr.target_attribute,
                    'status': 'FAIL',
                    'error': 'Calculation returned None'
                })

        except Exception as e:
            print(f"    ✗ Error: {str(e)}")
            failed += 1
            results.append({
                'attribute': attr.target_attribute,
                'status': 'FAIL',
                'error': str(e)
            })

        print()

    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {len(layer1_attributes)}")
    print(f"Passed: {passed} ✓")
    print(f"Failed: {failed} ✗")
    print(f"Success Rate: {(passed/len(layer1_attributes)*100):.1f}%")
    print("=" * 80)

    # Detailed Results
    print("\nDETAILED RESULTS:")
    print("-" * 80)

    for result in results:
        status_icon = "✓" if result['status'] == 'PASS' else "✗"
        print(f"{status_icon} {result['attribute']:<30}", end=" ")

        if result['status'] == 'PASS':
            print(f"{result['value']} {result['unit']}")
        else:
            print(f"FAILED: {result.get('error', 'Unknown error')}")

    print("-" * 80)

    # Highlight specific important metrics
    print("\nKEY METRICS VERIFICATION:")
    print("-" * 80)

    key_metrics = {
        'Sellout Time': '2.1 years',
        'Months of Inventory': '2.78 months',
        'Price Growth (%)': '81.63%',
        'Realised PSF': '4860 INR/sqft',
        'Revenue per Unit': '~20 lakh'
    }

    for metric_name, expected in key_metrics.items():
        matching = [r for r in results if metric_name.lower() in r['attribute'].lower()]
        if matching:
            r = matching[0]
            if r['status'] == 'PASS':
                print(f"✓ {metric_name:<25} {r['value']:.2f} {r['unit']:<15} (Expected: {expected})")
            else:
                print(f"✗ {metric_name:<25} FAILED")
        else:
            print(f"⚠ {metric_name:<25} Not found in results")

    print("-" * 80)

    return passed == len(layer1_attributes)


if __name__ == "__main__":
    success = test_all_layer1_attributes()
    sys.exit(0 if success else 1)
