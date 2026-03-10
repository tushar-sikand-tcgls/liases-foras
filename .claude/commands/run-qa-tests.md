# Run QA Automation Tests from CLI

description: Run QA tests from command line using existing backend logic with HTML reports

---

You are helping the user run QA Automation tests from the command line.

## Pure Delegation Approach

This command uses `app/testing/cli_runner.py` which **purely delegates** to the same backend services that the Streamlit app uses:
- `AutoHealingTestService` (test execution)
- `HTMLReportGenerator` (HTML report generation)

No new logic - just calls the existing service methods.

## Your Task

1. **Ask for Excel sheet path** if not already provided by the user
2. **Validate** the path exists (use ls or check if file exists)
3. **Execute** the CLI runner with appropriate arguments
4. **Display** the summary output to the user
5. **Show** the path to generated HTML report

## Command Format

```bash
python3 -m app.testing.cli_runner --excel-path <path> [options]
```

**Options**:
- `--run-id <name>` - Custom run identifier (default: cli_run_TIMESTAMP)
- `--auto-heal` / `--no-auto-heal` - Enable/disable auto-healing (default: enabled)
- `--parallel` / `--sequential` - Execution mode (default: parallel)
- `--max-workers <N>` - Parallel workers (default: 5)
- `--batch-size <N>` - Batch size (default: 10)
- `--rate-limit <N>` - API calls/min (default: 60)
- `--output-dir <path>` - Report directory (default: data/reports)

## Typical Usage Examples

**Basic run** (auto-heal enabled, parallel mode):
```bash
python3 -m app.testing.cli_runner --excel-path data/bdd_tests.xlsx
```

**Sequential mode, no auto-heal**:
```bash
python3 -m app.testing.cli_runner --excel-path data/bdd_tests.xlsx --sequential --no-auto-heal
```

**Custom run ID and output directory**:
```bash
python3 -m app.testing.cli_runner --excel-path data/bdd_tests.xlsx --run-id my_test --output-dir reports
```

## Output Files

The CLI runner generates two files in the output directory:
1. `qa_report_<run_id>.html` - HTML report (same as Streamlit generates)
2. `qa_summary_<run_id>.txt` - Text summary

## What You Should Do

1. Check if user provided Excel path, if not ask: "Please provide the path to your test Excel sheet"
2. Verify path exists with: `ls <path>`
3. Run: `python3 -m app.testing.cli_runner --excel-path <path>`
4. After completion, tell the user:
   - Pass/fail summary
   - Path to HTML report
   - Suggest: `open <report_path>` to view in browser
