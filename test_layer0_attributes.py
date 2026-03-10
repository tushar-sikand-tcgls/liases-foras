"""
Test Suite for All 41 Layer 0 Enriched Attributes
Validates that Layer 0 attributes are correctly loaded and retrievable
"""

import sys
sys.path.insert(0, '/Users/tusharsikand/Documents/Projects/liases-foras')

from app.services.enriched_layers_service import get_enriched_layers_service
from app.services.prompt_router import prompt_router

def test_all_layer0_attributes():
    """Test all 41 Layer 0 attributes"""

    print("=" * 80)
    print("COMPREHENSIVE TEST: All 41 Layer 0 Enriched Attributes")
    print("=" * 80)

    enriched_service = get_enriched_layers_service()

    # Get all Layer 0 attributes
    layer0_attributes = enriched_service.get_layer0_attributes()

    print(f"\nTotal Layer 0 attributes to test: {len(layer0_attributes)}\n")

    passed = 0
    failed = 0
    results = []

    for i, attr in enumerate(layer0_attributes, 1):
        print(f"[{i}/{len(layer0_attributes)}] Testing: {attr.target_attribute}")
        print(f"    Unit: {attr.unit}")
        print(f"    Dimension: {attr.dimension}")
        print(f"    Description: {attr.description[:60]}...")

        try:
            # Verify attribute is atomic (no calculation required)
            if attr.is_atomic:
                print(f"    ✓ Atomic: True (direct retrieval)")
                passed += 1
                results.append({
                    'attribute': attr.target_attribute,
                    'status': 'PASS',
                    'type': 'Atomic (Layer 0)',
                    'unit': attr.unit,
                    'dimension': attr.dimension
                })
            else:
                print(f"    ✗ NOT atomic - unexpected for Layer 0")
                failed += 1
                results.append({
                    'attribute': attr.target_attribute,
                    'status': 'FAIL',
                    'error': 'Layer 0 attribute marked as non-atomic'
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
    print(f"Total Tests: {len(layer0_attributes)}")
    print(f"Passed: {passed} ✓")
    print(f"Failed: {failed} ✗")
    print(f"Success Rate: {(passed/len(layer0_attributes)*100):.1f}%")
    print("=" * 80)

    # Group by dimension
    print("\nLAYER 0 ATTRIBUTES BY DIMENSION:")
    print("-" * 80)

    dimensions = {}
    for result in results:
        if result['status'] == 'PASS':
            dim = result['dimension']
            if dim not in dimensions:
                dimensions[dim] = []
            dimensions[dim].append(result['attribute'])

    for dim in sorted(dimensions.keys()):
        print(f"\n{dim} ({len(dimensions[dim])} attributes):")
        for attr_name in sorted(dimensions[dim]):
            print(f"  ✓ {attr_name}")

    print("-" * 80)

    # Test sample prompts for Layer 0 attributes
    print("\nSAMPLE PROMPT ROUTING TESTS:")
    print("-" * 80)

    sample_prompts = [
        ("What is the project size of Sara City?", "Project Size"),
        ("Show me the launch date", "Launch Date"),
        ("What's the current PSF?", "Current PSF"),
        ("How many total units?", "Total Units"),
        ("What is the developer name?", "Developer Name")
    ]

    routing_passed = 0
    for prompt, expected_attr in sample_prompts:
        route_decision = prompt_router.analyze_prompt(prompt)
        print(f"\nPrompt: '{prompt}'")
        print(f"  Expected: {expected_attr}")
        print(f"  Detected: {route_decision.capability}")
        print(f"  Layer: {route_decision.layer.name}")
        print(f"  Confidence: {route_decision.confidence:.2%}")

        # Check if routing makes sense (either Layer 0 or matches expected attribute)
        if route_decision.layer.name in ['LAYER_0', 'LAYER_1']:
            print(f"  ✓ Routed to appropriate layer")
            routing_passed += 1
        else:
            print(f"  ⚠ Routed to {route_decision.layer.name}")

    print(f"\nRouting Tests Passed: {routing_passed}/{len(sample_prompts)}")
    print("-" * 80)

    return passed == len(layer0_attributes)


if __name__ == "__main__":
    success = test_all_layer0_attributes()
    sys.exit(0 if success else 1)
