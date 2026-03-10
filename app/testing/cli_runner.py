#!/usr/bin/env python3
"""
QA Automation CLI Runner - Pure delegation to existing backend logic
Uses the exact same service calls as the Streamlit app.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import existing backend services (same as Streamlit app uses)
from app.testing.test_service import AutoHealingTestService
from app.testing.report_generator import HTMLReportGenerator


def main():
    """
    Pure delegation CLI wrapper - calls the exact same backend methods as Streamlit app:
    1. AutoHealingTestService.load_test_cases()
    2. AutoHealingTestService.run_test_cycle()
    3. HTMLReportGenerator.generate_email_report()
    4. AutoHealingTestService.get_summary_report()
    """
    parser = argparse.ArgumentParser(description="Run QA Automation tests from CLI")
    parser.add_argument("--excel-path", type=str, required=True, help="Path to test Excel sheet")
    parser.add_argument("--run-id", type=str, default=None, help="Run identifier (default: cli_run_TIMESTAMP)")
    parser.add_argument("--auto-heal", action="store_true", default=True, help="Enable auto-healing")
    parser.add_argument("--no-auto-heal", action="store_false", dest="auto_heal")
    parser.add_argument("--parallel", action="store_true", default=True, help="Parallel execution")
    parser.add_argument("--sequential", action="store_false", dest="parallel")
    parser.add_argument("--max-workers", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--rate-limit", type=int, default=60)
    parser.add_argument("--stop-on-inclusion-failure", action="store_true", default=False, help="Stop execution on first FAIL_INCLUSION")
    parser.add_argument("--output-dir", type=str, default="data/reports")
    args = parser.parse_args()

    # Validate and prepare
    excel_path = Path(args.excel_path)
    if not excel_path.exists():
        print(f"❌ Error: Excel file not found: {excel_path}")
        sys.exit(1)

    run_id = args.run_id or f"cli_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n🤖 QA Automation CLI - Run ID: {run_id}")
    print(f"Excel: {excel_path} | Auto-Heal: {args.auto_heal} | Mode: {'Parallel' if args.parallel else 'Sequential'}\n")

    try:
        # DELEGATION STEP 1: Initialize service (same as Streamlit app line ~107-113)
        service = AutoHealingTestService(
            excel_path=str(excel_path),
            max_workers=args.max_workers,
            batch_size=args.batch_size,
            rate_limit_per_minute=args.rate_limit
        )

        # DELEGATION STEP 2: Load test cases (same as Streamlit app initialization)
        test_cases = service.load_test_cases()
        print(f"✅ Loaded {len(test_cases)} test cases\n")

        # DELEGATION STEP 3: Run test cycle (same as Streamlit app line 190-194)
        test_run = service.run_test_cycle(
            run_id=run_id,
            auto_heal=args.auto_heal,
            use_parallel=args.parallel,
            stop_on_inclusion_failure=args.stop_on_inclusion_failure
        )

        # DELEGATION STEP 4: Generate HTML report (same as Streamlit app line 791-800)
        report_gen = HTMLReportGenerator()
        html_report = report_gen.generate_email_report(
            test_run=test_run,
            include_editable_grid=True,
            previous_run=None
        )

        # Save HTML report
        report_path = output_dir / f"qa_report_{run_id}.html"
        with open(report_path, 'w') as f:
            f.write(html_report)

        # DELEGATION STEP 5: Get text summary (same as Streamlit app uses this method)
        text_summary = service.get_summary_report(run_id)
        summary_path = output_dir / f"qa_summary_{run_id}.txt"
        with open(summary_path, 'w') as f:
            f.write(text_summary)

        # Display results
        print(f"\n{text_summary}")
        print(f"\n✅ HTML report: {report_path.absolute()}")
        print(f"✅ Text summary: {summary_path.absolute()}")
        print(f"\nTo view: open {report_path.absolute()}\n")

        sys.exit(0 if test_run.summary.failed == 0 else 1)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
