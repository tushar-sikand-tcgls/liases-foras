"""
Test Sellout Time calculation with mock data (no API required)
"""

import sys
sys.path.insert(0, '/Users/tusharsikand/Documents/Projects/liases-foras')

from app.services.prompt_router import prompt_router
from app.services.enriched_layers_service import get_enriched_layers_service

def test_sellout_calculation():
    """Test the enriched layers service calculation logic with mock data"""

    print("=" * 80)
    print("TESTING: Enriched Layers - Sellout Time Calculation Logic")
    print("=" * 80)

    # Step 1: Verify prompt routing
    print("\n[Step 1] Testing Prompt Router...")
    query = "What is sellout time for sara city"

    route_decision = prompt_router.analyze_prompt(query)
    print(f"  Query: '{query}'")
    print(f"  ✓ Layer: {route_decision.layer.name}")
    print(f"  ✓ Capability: {route_decision.capability}")
    print(f"  ✓ Confidence: {route_decision.confidence:.2%}")

    # Step 2: Get attribute definition
    print("\n[Step 2] Getting Attribute Definition...")
    enriched_service = get_enriched_layers_service()

    attr_name = route_decision.capability.replace('calculate_', '').replace('_', ' ').title()
    attr = enriched_service.get_attribute(attr_name)

    if not attr:
        print(f"  ✗ FAIL: Attribute '{attr_name}' not found")
        return False

    print(f"  ✓ Attribute: {attr.target_attribute}")
    print(f"  ✓ Formula: {attr.formula_derivation}")
    print(f"  ✓ Unit: {attr.unit}")
    print(f"  ✓ Dimension: {attr.dimension}")

    # Step 3: Test calculation with mock Sara City data
    print("\n[Step 3] Testing Calculation with Sara City Data...")

    # Mock project data (from API: /api/projects/3306)
    mock_project_data = {
        'supply': 1109,          # Total Supply Units
        'annual_sales': 527,     # Annual Sales Units
        'totalUnits': 1109,      # Alternative field name
        'annualSales': 527       # Alternative field name
    }

    print(f"  Input data:")
    print(f"    Supply: {mock_project_data['supply']} units")
    print(f"    Annual Sales: {mock_project_data['annual_sales']} units/year")

    # Execute calculation using enriched_layers_service
    result = enriched_service.execute_layer1_calculation(
        attr_name=attr.target_attribute,
        project_data=mock_project_data
    )

    if not result:
        print("  ✗ FAIL: Calculation returned None")
        return False

    print(f"\n  ✓ Calculation successful!")
    print(f"    Value: {result['value']}")
    print(f"    Unit: {result['unit']}")
    print(f"    Formula: {result['formula']}")
    print(f"    Dimension: {result['dimension']}")

    # Step 4: Validate result
    print("\n[Step 4] Validating Result...")

    expected_value = 2.1  # years (1109 / 527 = 2.10...)
    actual_value = result['value']

    tolerance = 0.1
    is_correct = abs(actual_value - expected_value) < tolerance

    if is_correct:
        print(f"  ✓ PASS: Value {actual_value} is close to expected {expected_value}")
    else:
        print(f"  ✗ FAIL: Value {actual_value} differs from expected {expected_value}")
        return False

    # Step 5: Summary
    print("\n" + "=" * 80)
    print("TEST RESULT: SUCCESS ✓")
    print("=" * 80)
    print(f"Sellout Time for Sara City: {actual_value} {result['unit']}")
    print(f"Formula: {result['formula']}")
    print(f"Calculation: {mock_project_data['supply']} / {mock_project_data['annual_sales']} = {actual_value}")
    print("\nThe enriched layers service is correctly calculating Sellout Time!")
    print("=" * 80)

    return True


if __name__ == "__main__":
    success = test_sellout_calculation()
    sys.exit(0 if success else 1)
