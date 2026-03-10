"""
Direct test for Sellout Time calculation
Tests the enriched layer integration without going through API
"""

import sys
sys.path.insert(0, '/Users/tusharsikand/Documents/Projects/liases-foras')

from app.services.prompt_router import prompt_router
from app.services.enriched_calculator import get_enriched_calculator
from app.services.enriched_layers_service import get_enriched_layers_service

def test_sellout_time():
    """Test Sellout Time for Sara City"""

    print("=" * 80)
    print("TESTING: Sellout Time for Sara City")
    print("=" * 80)

    # Step 1: Test prompt routing
    print("\n[Step 1] Testing Prompt Router...")
    query = "What is sellout time for sara city"

    route_decision = prompt_router.analyze_prompt(query)
    print(f"  Query: '{query}'")
    print(f"  Layer: {route_decision.layer.name}")
    print(f"  Capability: {route_decision.capability}")
    print(f"  Confidence: {route_decision.confidence:.2%}")
    print(f"  Reason: {route_decision.reason}")

    # Step 2: Check enriched service recognition
    print("\n[Step 2] Checking Enriched Service...")
    enriched_service = get_enriched_layers_service()

    # Try to find by capability name
    attr_name = route_decision.capability.replace('calculate_', '').replace('_', ' ').title()
    attr = enriched_service.get_attribute(attr_name)

    if attr:
        print(f"  ✓ Found attribute: {attr.target_attribute}")
        print(f"  Formula: {attr.formula_derivation}")
        print(f"  Requires calculation: {attr.requires_calculation}")
        print(f"  Unit: {attr.unit}")
        print(f"  Dimension: {attr.dimension}")
    else:
        print(f"  ✗ Attribute '{attr_name}' not found")
        return False

    # Step 3: Test calculation
    print("\n[Step 3] Testing Calculator...")
    calculator = get_enriched_calculator()

    try:
        result = calculator.calculate(
            capability=route_decision.capability,
            project_name="Sara City",
            project_id=3306
        )

        print(f"  ✓ Calculation successful!")
        print(f"  Project: {result['project']}")
        print(f"  Attribute: {result['attribute']}")
        print(f"  Value: {result['value']}")
        print(f"  Unit: {result['unit']}")
        print(f"  Formula: {result['formula']}")
        print(f"  Calculation Details: {result['calculation_details']}")
        print(f"  Source: {result['source']}")

        # Step 4: Validate result
        print("\n[Step 4] Validating Result...")
        expected_value = 2.1  # years
        actual_value = result['value']

        if abs(actual_value - expected_value) < 0.1:
            print(f"  ✓ PASS: Value {actual_value} is close to expected {expected_value}")
            print(f"\n{'=' * 80}")
            print("SUCCESS: Sellout Time calculation is CORRECT")
            print(f"Expected: 2.1 years")
            print(f"Got: {actual_value} years")
            print(f"Formula: {result['formula']}")
            print(f"{'=' * 80}\n")
            return True
        else:
            print(f"  ✗ FAIL: Value {actual_value} differs from expected {expected_value}")
            return False

    except Exception as e:
        print(f"  ✗ Calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_sellout_time()
    sys.exit(0 if success else 1)
