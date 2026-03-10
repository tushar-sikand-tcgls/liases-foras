"""
UltraThink Auto-Healing Test Runner

Demonstrates the complete testing system:
1. Load test cases from Excel
2. Run initial test cycle
3. Auto-heal failures
4. Run regression
5. Generate reports

Usage:
    python3 run_ultrathink_test.py
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.testing.test_service import AutoHealingTestService


def main():
    """Run complete auto-healing test cycle"""

    excel_path = "/Users/tusharsikand/Documents/Projects/liases-foras/change-request/BDD-test-cases/BDD_Test_Cases.xlsx"

    print("\n" + "="*80)
    print("ULTRATHINK AUTO-HEALING TESTING SYSTEM")
    print("="*80)

    # Initialize service
    print("\n1. Initializing test service...")
    service = AutoHealingTestService(excel_path=excel_path)

    # Load test cases
    print("\n2. Loading test cases from Excel...")
    test_cases = service.load_test_cases()
    print(f"   ✓ Loaded {len(test_cases)} test cases")
    print(f"   - Objective: {sum(1 for tc in test_cases if tc.type.value == 'Objective')}")
    print(f"   - Subjective: {sum(1 for tc in test_cases if tc.type.value == 'Subjective')}")
    print(f"   - Calculated: {sum(1 for tc in test_cases if tc.type.value == 'Calculated')}")

    # Run initial test cycle (with auto-healing)
    print("\n3. Running initial test cycle...")
    initial_run = service.run_test_cycle(
        run_id="initial",
        auto_heal=True
    )

    # Display initial results
    print("\n" + "="*80)
    print("INITIAL RUN RESULTS")
    print("="*80)
    print(service.get_summary_report("initial"))

    # Ask user if they want to run regression
    print("\n" + "="*80)
    response = input("Run regression test after auto-healing? (y/n): ")

    if response.lower() == 'y':
        print("\n4. Running regression test...")
        regression_run = service.run_regression(
            run_id="regression_1",
            previous_run_id="initial"
        )

        # Display regression results
        print("\n" + "="*80)
        print("REGRESSION RUN RESULTS")
        print("="*80)
        print(service.get_summary_report("regression_1"))

        if regression_run.improved_tests:
            print(f"\n✓ IMPROVED TESTS ({len(regression_run.improved_tests)}):")
            for test_id in regression_run.improved_tests[:10]:  # Show first 10
                result = next(r for r in regression_run.results if r.test_case.test_id == test_id)
                print(f"   [{test_id}] {result.test_case.prompt[:60]}...")

        if regression_run.regressed_tests:
            print(f"\n✗ REGRESSED TESTS ({len(regression_run.regressed_tests)}):")
            for test_id in regression_run.regressed_tests[:10]:
                result = next(r for r in regression_run.results if r.test_case.test_id == test_id)
                print(f"   [{test_id}] {result.test_case.prompt[:60]}...")

    print("\n" + "="*80)
    print("TEST CYCLE COMPLETE")
    print("="*80)
    print(f"\nExcel file updated: {excel_path}")
    print("Check the file for '_original' columns preserving pre-fix values.\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
