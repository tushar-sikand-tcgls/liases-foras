"""
Auto-Healing Test Service

Core engine that orchestrates:
- Test execution
- Validation
- Auto-healing
- Regression runs
- Excel read/write
"""

import os
import pandas as pd
from typing import List, Optional, Dict, Callable
from datetime import datetime
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from app.testing.test_models import (
    BDDTestCase, TestResult, TestRun, TestType, TestStatus
)
from app.testing.validators import test_validator
from app.testing.auto_healer import auto_healer
from app.services.v4_query_service import get_v4_service


class RateLimiter:
    """Rate limiter for API calls to respect Gemini LLM limits"""

    def __init__(self, max_calls_per_minute: int = 60):
        self.max_calls_per_minute = max_calls_per_minute
        self.calls = []
        self.lock = threading.Lock()

    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        with self.lock:
            now = time.time()
            # Remove calls older than 1 minute
            self.calls = [call_time for call_time in self.calls if now - call_time < 60]

            # If we've hit the limit, wait
            if len(self.calls) >= self.max_calls_per_minute:
                sleep_time = 60 - (now - self.calls[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
                # Remove old calls again after sleeping
                now = time.time()
                self.calls = [call_time for call_time in self.calls if now - call_time < 60]

            # Record this call
            self.calls.append(time.time())


class AutoHealingTestService:
    """
    Complete auto-healing testing service

    Combines QA (test execution + validation) and Developer (auto-fixing) roles
    """

    def __init__(
        self,
        excel_path: str,
        max_workers: int = 5,
        batch_size: int = 10,
        rate_limit_per_minute: int = 60
    ):
        self.excel_path = excel_path
        self.v4_service = get_v4_service()  # Use new V4QueryService (LangGraph orchestrator)
        self.test_cases: List[BDDTestCase] = []
        self.runs: Dict[str, TestRun] = {}

        # Check if using Ollama (no rate limits needed, sequential execution recommended)
        self.using_ollama = os.getenv("LLM_PROVIDER", "").lower() == "ollama"

        if self.using_ollama:
            # Ollama: Sequential execution, no rate limiting
            self.max_workers = 1  # Force sequential
            self.batch_size = 1   # One at a time
            self.rate_limiter = RateLimiter(max_calls_per_minute=9999)  # Effectively unlimited
            print("🔧 QA Testing Mode: Sequential execution (Ollama has no rate limits)")
        else:
            # Gemini: Parallel execution with rate limiting
            self.max_workers = max_workers
            self.batch_size = batch_size
            self.rate_limiter = RateLimiter(max_calls_per_minute=rate_limit_per_minute)

        self.progress_callback: Optional[Callable[[int, int], None]] = None

    def load_test_cases(self) -> List[BDDTestCase]:
        """Load test cases from Excel"""
        df = pd.read_excel(self.excel_path)

        test_cases = []
        for idx, row in df.iterrows():
            test_case = BDDTestCase(
                test_id=idx + 1,  # Start IDs from 1, not 0
                row_number=idx + 2,  # +1 for 0-index, +1 for header
                type=TestType(row['Type']),
                prompt=str(row['Prompt']),
                good_answer=str(row['Good Answer']),
                expected_answer_include=str(row['Expected Answer Should Include']),
                score_target=str(row['Score Target'])
            )
            test_cases.append(test_case)

        self.test_cases = test_cases
        return test_cases

    def execute_test(self, test_case: BDDTestCase, run_id: str, use_rate_limiter: bool = True) -> TestResult:
        """Execute a single test case"""
        start_time = time.time()

        try:
            # Respect rate limits (skip if using Ollama)
            if use_rate_limiter and not self.using_ollama:
                self.rate_limiter.wait_if_needed()

            # Call model with prompt using V4QueryService (LangGraph orchestrator)
            response = self.v4_service.query(test_case.prompt)

            # Extract model answer from response
            if response.get('error'):
                model_answer = f"ERROR: {response['error']}"
            elif response.get('result'):
                result_data = response['result']
                # Handle different result formats
                if isinstance(result_data, dict):
                    if 'value' in result_data:
                        # Format with unit if available
                        value = result_data['value']
                        unit = result_data.get('unit', '')
                        if unit:
                            model_answer = f"{value} {unit}"
                        else:
                            model_answer = str(value)
                    elif 'attribute' in result_data:
                        model_answer = f"{result_data.get('attribute')}: {result_data.get('value')} {result_data.get('unit', '')}"
                    else:
                        model_answer = str(result_data)
                else:
                    model_answer = str(result_data)
            else:
                model_answer = "No result returned"

            execution_time = (time.time() - start_time) * 1000  # ms

            # Validate result
            validation = test_validator.validate(
                model_answer=model_answer,
                expected_include=test_case.expected_answer_include,
                good_answer=test_case.good_answer,
                score_target=test_case.score_target
            )

            return TestResult(
                test_case=test_case,
                run_id=run_id,
                model_answer=model_answer,
                execution_time_ms=execution_time,
                validation=validation
            )

        except Exception as e:
            return TestResult(
                test_case=test_case,
                run_id=run_id,
                model_answer="",
                validation=test_validator.validate("", "", "", "> 0/10"),
                error_message=str(e)
            )

    def execute_batch_parallel(
        self,
        test_cases: List[BDDTestCase],
        run_id: str,
        batch_size: Optional[int] = None,
        stop_on_inclusion_failure: bool = False
    ) -> List[TestResult]:
        """
        Execute test cases in parallel batches with rate limiting

        Args:
            test_cases: List of test cases to execute
            run_id: Run identifier
            batch_size: Override default batch size
            stop_on_inclusion_failure: Stop execution on first FAIL_INCLUSION

        Returns:
            List of test results in original order (may be incomplete if stopped early)
        """
        batch_size = batch_size or self.batch_size
        results = []
        total_tests = len(test_cases)

        # Process in batches
        for batch_start in range(0, total_tests, batch_size):
            batch_end = min(batch_start + batch_size, total_tests)
            batch = test_cases[batch_start:batch_end]

            print(f"Processing batch {batch_start//batch_size + 1} ({batch_start+1}-{batch_end} of {total_tests})")

            # Execute batch in parallel with fallback to sequential on error
            batch_results = [None] * len(batch)
            try:
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    # Submit all tests in batch
                    future_to_index = {
                        executor.submit(self.execute_test, test_case, run_id, True): i
                        for i, test_case in enumerate(batch)
                    }

                    # Collect results as they complete
                    for future in as_completed(future_to_index):
                        index = future_to_index[future]
                        try:
                            result = future.result()
                            batch_results[index] = result

                            # Update progress
                            completed = batch_start + index + 1
                            if self.progress_callback:
                                self.progress_callback(completed, total_tests)

                            status_symbol = "✓" if result.passed else "✗"
                            print(f"  [{completed}/{total_tests}] {status_symbol} {batch[index].prompt[:50]}...")

                        except Exception as e:
                            print(f"  Error executing test {index}: {e}")
                            # Create error result
                            batch_results[index] = TestResult(
                                test_case=batch[index],
                                run_id=run_id,
                                model_answer="",
                                validation=test_validator.validate("", "", "", "> 0/10"),
                                error_message=str(e)
                            )

            except (BrokenPipeError, OSError) as e:
                # Thread safety issue - fall back to sequential execution
                print(f"⚠️  Parallel execution failed ({type(e).__name__}), falling back to sequential...")
                for i, test_case in enumerate(batch):
                    result = self.execute_test(test_case, run_id, True)
                    batch_results[i] = result
                    completed = batch_start + i + 1
                    if self.progress_callback:
                        self.progress_callback(completed, total_tests)
                    status_symbol = "✓" if result.passed else "✗"
                    print(f"  [{completed}/{total_tests}] {status_symbol} {test_case.prompt[:50]}...")

            results.extend(batch_results)

            # Check for early exit on FAIL_INCLUSION
            if stop_on_inclusion_failure:
                for result in batch_results:
                    if not result.validation.inclusion_passed:
                        print(f"\n⛔ STOPPED: First FAIL_INCLUSION detected at test #{result.test_case.test_id}")
                        print(f"   Test: {result.test_case.prompt}")
                        print(f"   Expected to include: '{result.test_case.expected_answer_include}'")
                        print(f"   Model answer: '{result.model_answer}'")
                        return results  # Early exit

            # Small delay between batches
            if batch_end < total_tests:
                time.sleep(1)

        return results

    def run_test_cycle(
        self,
        run_id: str = "initial",
        test_cases: Optional[List[BDDTestCase]] = None,
        auto_heal: bool = True,
        use_parallel: bool = True,
        stop_on_inclusion_failure: bool = False
    ) -> TestRun:
        """
        Run complete test cycle

        1. Execute all tests (sequentially or in parallel batches)
        2. Validate results
        3. (Optional) Auto-heal failures
        4. Return test run

        Args:
            run_id: Unique identifier for this run
            test_cases: List of test cases (uses loaded cases if None)
            auto_heal: Apply auto-healing to failures
            use_parallel: Execute in parallel batches (recommended for large test suites)
            stop_on_inclusion_failure: Stop execution on first FAIL_INCLUSION (for debugging)
        """
        if test_cases is None:
            test_cases = self.test_cases

        if not test_cases:
            test_cases = self.load_test_cases()

        print(f"\n{'='*80}")
        print(f"Starting Test Run: {run_id}")
        print(f"Total Tests: {len(test_cases)}")
        print(f"Execution Mode: {'Parallel Batches' if use_parallel else 'Sequential'}")
        if use_parallel:
            print(f"Batch Size: {self.batch_size}, Workers: {self.max_workers}")
        print(f"{'='*80}\n")

        # Create test run
        test_run = TestRun(
            run_id=run_id,
            excel_path=self.excel_path
        )

        # Execute all tests
        if use_parallel:
            # Parallel batch execution
            results = self.execute_batch_parallel(test_cases, run_id, stop_on_inclusion_failure=stop_on_inclusion_failure)
            for result in results:
                test_run.add_result(result)
        else:
            # Sequential execution (legacy mode)
            for i, test_case in enumerate(test_cases, 1):
                print(f"[{i}/{len(test_cases)}] Testing: {test_case.prompt[:60]}...")
                result = self.execute_test(test_case, run_id)
                test_run.add_result(result)

                status_symbol = "✓" if result.passed else "✗"
                status_display = result.status.value if hasattr(result.status, 'value') else str(result.status)
                print(f"  {status_symbol} {status_display}")

                # Check for early exit on FAIL_INCLUSION
                if stop_on_inclusion_failure and not result.validation.inclusion_passed:
                    print(f"\n⛔ STOPPED: First FAIL_INCLUSION detected at test #{test_case.test_id}")
                    print(f"   Test: {test_case.prompt}")
                    print(f"   Expected to include: '{test_case.expected_answer_include}'")
                    print(f"   Model answer: '{result.model_answer}'")
                    break

        test_run.completed_at = datetime.utcnow()
        test_run.compute_summary()

        # Store run
        self.runs[run_id] = test_run

        print(f"\n{'='*80}")
        print(f"Test Run Complete: {run_id}")
        print(f"Passed: {test_run.summary.passed}/{test_run.summary.total_tests} ({test_run.summary.pass_rate:.1f}%)")
        print(f"{'='*80}\n")

        # Auto-heal if requested and there are failures
        if auto_heal and test_run.summary.failed > 0:
            print(f"\nAuto-healing {test_run.summary.failed} failures...")
            self.heal_failures(test_run)

        return test_run

    def heal_failures(self, test_run: TestRun):
        """Apply auto-healing to failures"""
        failed_results = test_run.get_failed_tests()

        print(f"Analyzing {len(failed_results)} failures...")
        healed_cases = auto_healer.heal_test_cases(failed_results)

        # Update test cases
        for healed_case in healed_cases:
            # Find and replace in master list
            for i, tc in enumerate(self.test_cases):
                if tc.test_id == healed_case.test_id:
                    self.test_cases[i] = healed_case
                    break

        # Update Excel file
        self.save_test_cases()

        print(f"✓ Auto-fixed {sum(1 for tc in healed_cases if tc.auto_fixed)} test cases")
        print(f"⚠ {sum(1 for tc in healed_cases if tc.needs_review)} cases need manual review")

    def run_regression(
        self,
        run_id: str = "regression_1",
        previous_run_id: str = "initial",
        use_parallel: bool = True
    ) -> TestRun:
        """
        Run regression test after auto-healing

        Compares results to previous run

        Args:
            run_id: Unique identifier for this regression run
            previous_run_id: ID of the run to compare against
            use_parallel: Execute in parallel batches
        """
        print(f"\n{'='*80}")
        print(f"Starting Regression Run: {run_id}")
        print(f"Comparing to: {previous_run_id}")
        print(f"{'='*80}\n")

        # Run tests with current (healed) test cases
        regression_run = self.run_test_cycle(run_id=run_id, auto_heal=False, use_parallel=use_parallel)

        # Compare to previous run
        if previous_run_id in self.runs:
            prev_run = self.runs[previous_run_id]
            regression_run.previous_run_id = previous_run_id

            # Find improvements and regressions
            for curr_result in regression_run.results:
                test_id = curr_result.test_case.test_id

                # Find corresponding previous result
                prev_result = next(
                    (r for r in prev_run.results if r.test_case.test_id == test_id),
                    None
                )

                if prev_result:
                    if not prev_result.passed and curr_result.passed:
                        regression_run.improved_tests.append(test_id)
                    elif prev_result.passed and not curr_result.passed:
                        regression_run.regressed_tests.append(test_id)

            print(f"\n{'='*80}")
            print(f"Regression Analysis:")
            print(f"  Improved: {len(regression_run.improved_tests)} tests")
            print(f"  Regressed: {len(regression_run.regressed_tests)} tests")
            print(f"  Pass Rate Change: {prev_run.summary.pass_rate:.1f}% → {regression_run.summary.pass_rate:.1f}%")
            print(f"{'='*80}\n")

        return regression_run

    def save_test_cases(self):
        """Save current test cases back to Excel"""
        # Convert test cases to DataFrame
        rows = []
        for tc in self.test_cases:
            # Handle both enum and string types
            type_value = tc.type.value if hasattr(tc.type, 'value') else str(tc.type)

            row = {
                'Type': type_value,
                'Prompt': tc.prompt,
                'Good Answer': tc.good_answer,
                'Expected Answer Should Include': tc.expected_answer_include,
                'Score Target': tc.score_target,
                # Originals
                'Prompt_original': tc.prompt_original or '',
                'Good Answer_original': tc.good_answer_original or '',
                'Expected Answer Should Include_original': tc.expected_answer_include_original or '',
                # Metadata
                'Auto_Fixed': tc.auto_fixed,
                'Fix_Reason': tc.fix_reason or '',
                'Needs_Review': tc.needs_review
            }
            rows.append(row)

        df = pd.DataFrame(rows)

        # Write to Excel
        df.to_excel(self.excel_path, index=False)
        print(f"✓ Saved {len(rows)} test cases to {self.excel_path}")

    def get_summary_report(self, run_id: str) -> str:
        """Generate text summary report"""
        if run_id not in self.runs:
            return f"Run '{run_id}' not found"

        run = self.runs[run_id]
        summary = run.summary

        report = f"""
{'='*80}
AUTO-HEALING TEST REPORT - Run: {run_id}
{'='*80}

SUMMARY:
--------
Total Tests: {summary.total_tests}
Passed: {summary.passed} ({summary.pass_rate:.1f}%)
Failed: {summary.failed} ({summary.fail_rate:.1f}%)
  - Inclusion failures: {summary.fail_inclusion}
  - Similarity failures: {summary.fail_similarity}

BY TYPE:
--------
Objective:   {summary.objective_passed}/{summary.objective_total} passed ({summary.objective_passed/summary.objective_total*100 if summary.objective_total > 0 else 0:.1f}%)
Subjective:  {summary.subjective_passed}/{summary.subjective_total} passed ({summary.subjective_passed/summary.subjective_total*100 if summary.subjective_total > 0 else 0:.1f}%)
Calculated:  {summary.calculated_passed}/{summary.calculated_total} passed ({summary.calculated_passed/summary.calculated_total*100 if summary.calculated_total > 0 else 0:.1f}%)

AUTO-FIXES:
-----------
Auto-fixed: {summary.auto_fixed_count} test cases
Needs review: {summary.needs_review_count} test cases

TIMING:
-------
Duration: {summary.duration_seconds:.1f}s
Started: {summary.started_at.strftime('%Y-%m-%d %H:%M:%S')}
Completed: {summary.completed_at.strftime('%Y-%m-%d %H:%M:%S') if summary.completed_at else 'N/A'}

{'='*80}

Do you want another refinement cycle (further auto-fixing and regression run),
or are you satisfied with the current test outcomes?

"""
        return report
