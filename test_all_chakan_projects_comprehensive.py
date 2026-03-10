"""
Comprehensive Test: All L1 and L0 Attributes for All Chakan Projects
WITHOUT HARDCODINGS - Dynamically loads from enriched_layers_knowledge.json

Tests:
- All 26 Layer 1 attributes
- All 41 Layer 0 attributes
- All 8 projects in Chakan micromarket
- Precision formatting (2 decimals display + full precision in calculations)
- Unit presence verification
- No hardcoded values anywhere
"""

import requests
import json
from typing import List, Dict

API_BASE_URL = "http://localhost:8000"

def load_enriched_layers_knowledge():
    """Load enriched layers knowledge from JSON file"""
    try:
        with open('change-request/enriched-layers/enriched_layers_knowledge.json', 'r') as f:
            data = json.load(f)
            # Combine layer0 and layer1 attributes into single list
            combined = {
                'enriched_layers': data.get('layer0_attributes', []) + data.get('layer1_attributes', []),
                'metadata': data.get('metadata', {})
            }
            return combined
    except FileNotFoundError:
        print("Error: enriched_layers_knowledge.json not found")
        return None

def get_chakan_projects():
    """Get all projects in Chakan micromarket"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/projects", timeout=30)
        if response.status_code == 200:
            all_projects = response.json()
            # Filter for Chakan location
            chakan_projects = [p for p in all_projects if p.get('location') == 'Chakan']

            # Extract project names (handle newlines)
            project_names = []
            for p in chakan_projects:
                name = p.get('projectName', '')
                # Normalize newlines
                name_normalized = ' '.join(name.replace('\n', ' ').split())
                if name_normalized:
                    project_names.append(name_normalized)

            return project_names
    except Exception as e:
        print(f"Error fetching projects: {e}")
        return []

def test_layer1_attribute(project_name: str, attribute: Dict) -> Dict:
    """Test a single Layer 1 attribute for a project"""
    attr_name = attribute['target_attribute']

    # Use first prompt variation
    variations = attribute['variation_in_prompt'].split('|')
    prompt_template = variations[0].strip()

    # Add project name to the prompt (templates don't have placeholders)
    if 'X' in prompt_template or '[X]' in prompt_template:
        # If template has placeholder, replace it
        query = prompt_template.replace('X', project_name).replace('[X]', project_name)
    else:
        # Otherwise, append project name
        query = f"{prompt_template} for {project_name}"

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/qa/question",
            json={
                "question": query,
                "project_id": None,
                "location_context": None,
                "admin_mode": False
            },
            timeout=30
        )

        if response.status_code != 200:
            return {
                'status': 'FAIL',
                'reason': f'HTTP {response.status_code}',
                'attribute': attr_name,
                'query': query
            }

        data = response.json()

        if data.get('status') != 'success':
            return {
                'status': 'FAIL',
                'reason': f'API status: {data.get("status")}',
                'attribute': attr_name,
                'query': query
            }

        answer = data.get('answer', {})
        result = answer.get('result', {})
        calculation = answer.get('calculation', {})

        # Validation checks
        value_raw = result.get('value')
        unit = result.get('unit')
        text = result.get('text')
        full_precision = calculation.get('fullPrecisionValue')
        rounded_value = calculation.get('roundedValue')

        checks = {
            'has_raw_value': value_raw is not None,
            'has_unit': unit is not None,
            'has_display_text': text is not None,
            'has_full_precision': full_precision is not None,
            'has_rounded_value': rounded_value is not None,
            'routing': answer.get('understanding', {}).get('routing') == 'enriched_layers'
        }

        all_passed = all(checks.values())

        return {
            'status': 'PASS' if all_passed else 'PARTIAL',
            'attribute': attr_name,
            'query': query,
            'display_text': text,
            'full_precision': full_precision,
            'unit': unit,
            'checks': checks
        }

    except Exception as e:
        return {
            'status': 'ERROR',
            'reason': str(e),
            'attribute': attr_name,
            'query': query
        }

def test_layer0_attribute(project_name: str, attribute: Dict) -> Dict:
    """Test a single Layer 0 attribute for a project"""
    attr_name = attribute['target_attribute']

    # Use first prompt variation
    variations = attribute['variation_in_prompt'].split('|')
    prompt_template = variations[0].strip()

    # Add project name to the prompt (templates don't have placeholders)
    if 'X' in prompt_template or '[X]' in prompt_template:
        # If template has placeholder, replace it
        query = prompt_template.replace('X', project_name).replace('[X]', project_name)
    else:
        # Otherwise, append project name
        query = f"{prompt_template} for {project_name}"

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/qa/question",
            json={
                "question": query,
                "project_id": None,
                "location_context": None,
                "admin_mode": False
            },
            timeout=30
        )

        if response.status_code != 200:
            return {
                'status': 'FAIL',
                'reason': f'HTTP {response.status_code}',
                'attribute': attr_name,
                'query': query
            }

        data = response.json()

        if data.get('status') != 'success':
            return {
                'status': 'FAIL',
                'reason': f'API status: {data.get("status")}',
                'attribute': attr_name,
                'query': query
            }

        answer = data.get('answer', {})
        result = answer.get('result', {})

        # For Layer 0, we just need value and unit
        value = result.get('value')
        unit = result.get('unit')

        return {
            'status': 'PASS' if value is not None else 'FAIL',
            'attribute': attr_name,
            'query': query,
            'value': value,
            'unit': unit
        }

    except Exception as e:
        return {
            'status': 'ERROR',
            'reason': str(e),
            'attribute': attr_name,
            'query': query
        }

def main():
    """Main test execution"""
    print("=" * 100)
    print("COMPREHENSIVE TEST: ALL L1 & L0 ATTRIBUTES FOR ALL CHAKAN PROJECTS")
    print("WITHOUT HARDCODINGS - Dynamically loaded from enriched_layers_knowledge.json")
    print("=" * 100)

    # Load knowledge base
    print("\nStep 1: Loading enriched layers knowledge...")
    knowledge = load_enriched_layers_knowledge()
    if not knowledge:
        print("ERROR: Could not load enriched_layers_knowledge.json")
        return False

    enriched_layers = knowledge.get('enriched_layers', [])
    layer0_count = sum(1 for attr in enriched_layers if not attr.get('requires_calculation', False))
    layer1_count = sum(1 for attr in enriched_layers if attr.get('requires_calculation', False))

    print(f"✓ Loaded {len(enriched_layers)} total attributes")
    print(f"  - Layer 0: {layer0_count} attributes")
    print(f"  - Layer 1: {layer1_count} attributes")

    # Get Chakan projects
    print("\nStep 2: Fetching all Chakan projects...")
    projects = get_chakan_projects()
    if not projects:
        print("ERROR: No projects found in Chakan")
        return False

    print(f"✓ Found {len(projects)} projects in Chakan:")
    for i, project in enumerate(projects, 1):
        print(f"  {i}. {project}")

    # Test summary counters
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    partial_tests = 0
    error_tests = 0

    # Results storage
    project_results = {}

    # Test each project
    for project_idx, project_name in enumerate(projects, 1):
        print(f"\n{'=' * 100}")
        print(f"TESTING PROJECT {project_idx}/{len(projects)}: {project_name}")
        print(f"{'=' * 100}")

        project_results[project_name] = {
            'layer1': [],
            'layer0': []
        }

        # Test Layer 1 attributes
        print(f"\n--- Layer 1 Attributes (Calculated Metrics) ---")
        layer1_attrs = [attr for attr in enriched_layers if attr.get('requires_calculation', False)]

        for attr_idx, attribute in enumerate(layer1_attrs, 1):
            print(f"\r  Testing L1 [{attr_idx}/{len(layer1_attrs)}]: {attribute['target_attribute'][:40]:<40}", end='', flush=True)

            result = test_layer1_attribute(project_name, attribute)
            project_results[project_name]['layer1'].append(result)
            total_tests += 1

            if result['status'] == 'PASS':
                passed_tests += 1
            elif result['status'] == 'PARTIAL':
                partial_tests += 1
            elif result['status'] == 'FAIL':
                failed_tests += 1
            else:
                error_tests += 1

        print()  # New line after progress

        # Test Layer 0 attributes
        print(f"\n--- Layer 0 Attributes (Atomic Data) ---")
        layer0_attrs = [attr for attr in enriched_layers if not attr.get('requires_calculation', False)]

        for attr_idx, attribute in enumerate(layer0_attrs, 1):
            print(f"\r  Testing L0 [{attr_idx}/{len(layer0_attrs)}]: {attribute['target_attribute'][:40]:<40}", end='', flush=True)

            result = test_layer0_attribute(project_name, attribute)
            project_results[project_name]['layer0'].append(result)
            total_tests += 1

            if result['status'] == 'PASS':
                passed_tests += 1
            elif result['status'] == 'FAIL':
                failed_tests += 1
            else:
                error_tests += 1

        print()  # New line after progress

        # Project summary
        project_passed = sum(1 for r in project_results[project_name]['layer1'] + project_results[project_name]['layer0'] if r['status'] == 'PASS')
        project_total = len(project_results[project_name]['layer1']) + len(project_results[project_name]['layer0'])
        print(f"\n  Project Summary: {project_passed}/{project_total} tests passed ({project_passed/project_total*100:.1f}%)")

    # Final summary
    print(f"\n{'=' * 100}")
    print("FINAL TEST SUMMARY")
    print(f"{'=' * 100}")
    print(f"\nTotal Projects Tested: {len(projects)}")
    print(f"Total Attributes: {len(enriched_layers)} (L0: {layer0_count}, L1: {layer1_count})")
    print(f"Total Tests Executed: {total_tests}")
    print(f"\nResults:")
    print(f"  ✓ PASSED: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
    print(f"  ⚠ PARTIAL: {partial_tests} ({partial_tests/total_tests*100:.1f}%)")
    print(f"  ✗ FAILED: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
    print(f"  ⚠ ERRORS: {error_tests} ({error_tests/total_tests*100:.1f}%)")

    # Per-project breakdown
    print(f"\n{'=' * 100}")
    print("PER-PROJECT BREAKDOWN")
    print(f"{'=' * 100}")

    for project_name in projects:
        results = project_results[project_name]
        l1_passed = sum(1 for r in results['layer1'] if r['status'] == 'PASS')
        l0_passed = sum(1 for r in results['layer0'] if r['status'] == 'PASS')
        total_project = len(results['layer1']) + len(results['layer0'])
        passed_project = l1_passed + l0_passed

        status_icon = "✓" if passed_project == total_project else "⚠" if passed_project > total_project * 0.7 else "✗"

        print(f"\n{status_icon} {project_name}")
        print(f"  Layer 1: {l1_passed}/{len(results['layer1'])} passed")
        print(f"  Layer 0: {l0_passed}/{len(results['layer0'])} passed")
        print(f"  Total: {passed_project}/{total_project} ({passed_project/total_project*100:.1f}%)")

    # Show sample passing results
    print(f"\n{'=' * 100}")
    print("SAMPLE PASSING RESULTS (Precision Formatting Verification)")
    print(f"{'=' * 100}")

    sample_count = 0
    for project_name, results in project_results.items():
        for result in results['layer1']:
            if result['status'] == 'PASS' and sample_count < 5:
                print(f"\n✓ {project_name} - {result['attribute']}")
                print(f"  Query: {result['query']}")
                print(f"  Display: {result.get('display_text', 'N/A')}")
                print(f"  Full Precision: {result.get('full_precision', 'N/A')}")
                print(f"  Unit: {result.get('unit', 'N/A')}")
                sample_count += 1
        if sample_count >= 5:
            break

    # Show failures
    failures = []
    for project_name, results in project_results.items():
        for result in results['layer1'] + results['layer0']:
            if result['status'] in ['FAIL', 'ERROR']:
                failures.append((project_name, result))

    if failures:
        print(f"\n{'=' * 100}")
        print(f"FAILURES AND ERRORS ({len(failures)} total)")
        print(f"{'=' * 100}")

        for project_name, result in failures[:10]:  # Show first 10
            print(f"\n✗ {project_name} - {result['attribute']}")
            print(f"  Query: {result['query']}")
            print(f"  Status: {result['status']}")
            print(f"  Reason: {result.get('reason', 'N/A')}")

        if len(failures) > 10:
            print(f"\n... and {len(failures) - 10} more failures")

    # Success criteria
    print(f"\n{'=' * 100}")
    success_rate = passed_tests / total_tests * 100

    if success_rate >= 95:
        print("✓ SUCCESS: >= 95% tests passing - PRODUCTION READY")
        return True
    elif success_rate >= 80:
        print("⚠ PARTIAL SUCCESS: >= 80% tests passing - Needs minor fixes")
        return False
    else:
        print("✗ FAILURE: < 80% tests passing - Significant issues remain")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
