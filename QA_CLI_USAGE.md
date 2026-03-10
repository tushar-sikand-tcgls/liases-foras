# QA Automation CLI Usage Guide

## Overview

Run QA Automation tests from the command line using the `/run-qa-tests` slash command or directly via Python.

## Architecture

The CLI uses **pure delegation** to existing backend services:
- `AutoHealingTestService` - same service the Streamlit app uses
- `HTMLReportGenerator` - same report generator the Streamlit app uses

No new logic - just a thin wrapper that calls the exact same methods.

## Usage

### Option 1: Via Claude Code Slash Command

```bash
/run-qa-tests
```

Claude Code will:
1. Ask for your Excel sheet path
2. Validate the file exists
3. Run the tests using the backend service
4. Show you the summary and report paths

### Option 2: Direct Python Invocation

**Basic usage** (auto-heal enabled, parallel mode):
```bash
python3 -m app.testing.cli_runner --excel-path change-request/BDD-test-cases/BDD_Test_Cases_Micro.xlsx
```

**With custom options**:
```bash
python3 -m app.testing.cli_runner \
  --excel-path change-request/BDD-test-cases/BDD_Test_Cases.xlsx \
  --run-id my_test_run \
  --parallel \
  --max-workers 10 \
  --batch-size 20 \
  --output-dir my_reports
```

**Sequential mode, no auto-healing**:
```bash
python3 -m app.testing.cli_runner \
  --excel-path change-request/BDD-test-cases/BDD_Test_Cases_Micro.xlsx \
  --sequential \
  --no-auto-heal
```

## Available Options

| Option | Default | Description |
|--------|---------|-------------|
| `--excel-path` | *required* | Path to test Excel sheet |
| `--run-id` | `cli_run_TIMESTAMP` | Custom run identifier |
| `--auto-heal` | enabled | Enable auto-healing of failures |
| `--no-auto-heal` | - | Disable auto-healing |
| `--parallel` | enabled | Use parallel execution with batches |
| `--sequential` | - | Use sequential execution |
| `--max-workers` | 5 | Number of parallel workers |
| `--batch-size` | 10 | Tests per batch (parallel mode) |
| `--rate-limit` | 60 | API calls per minute |
| `--output-dir` | `data/reports` | Directory for reports |

## Output Files

The CLI generates two files:

1. **HTML Report**: `qa_report_<run_id>.html`
   - Same format as Streamlit app generates
   - Email-friendly with collapsible sections
   - Includes expected vs actual answer comparison

2. **Text Summary**: `qa_summary_<run_id>.txt`
   - Quick text summary of results
   - Pass/fail breakdown by type
   - Auto-fix statistics

## Example Output

```
🤖 QA Automation CLI - Run ID: cli_run_20251210_143022
Excel: change-request/BDD-test-cases/BDD_Test_Cases_Micro.xlsx | Auto-Heal: True | Mode: Parallel

✅ Loaded 54 test cases

================================================================================
Starting Test Run: cli_run_20251210_143022
Total Tests: 54
Execution Mode: Parallel Batches
Batch Size: 10, Workers: 5
================================================================================

Processing batch 1 (1-10 of 54)
  [1/54] ✓ What is the price per sqft for Project X?...
  ...

================================================================================
AUTO-HEALING TEST REPORT - Run: cli_run_20251210_143022
================================================================================

SUMMARY:
--------
Total Tests: 54
Passed: 48 (88.9%)
Failed: 6 (11.1%)
  - Inclusion failures: 2
  - Similarity failures: 4

AUTO-FIXES:
-----------
Auto-fixed: 3 test cases
Needs review: 1 test cases

================================================================================

✅ HTML report: /path/to/data/reports/qa_report_cli_run_20251210_143022.html
✅ Text summary: /path/to/data/reports/qa_summary_cli_run_20251210_143022.txt

To view: open /path/to/data/reports/qa_report_cli_run_20251210_143022.html
```

## Exit Codes

- `0` - All tests passed
- `1` - One or more tests failed OR execution error

## Comparison with Streamlit App

| Feature | Streamlit App | CLI |
|---------|---------------|-----|
| Test Execution | ✅ `service.run_test_cycle()` | ✅ Same method |
| HTML Report | ✅ `report_gen.generate_email_report()` | ✅ Same method |
| Auto-Healing | ✅ Supported | ✅ Same logic |
| Parallel Mode | ✅ Batched execution | ✅ Same batching |
| Rate Limiting | ✅ 60 calls/min | ✅ Configurable |
| Progress Tracking | ✅ UI progress bar | ✅ Console output |
| Expected vs Actual | ✅ Grid + HTML | ✅ HTML report |

## Tips

1. **Use parallel mode for large test suites** (default): Faster execution with batching
2. **Adjust workers/batch-size** based on your system: More workers = faster but more memory
3. **Check the HTML report** for detailed failure analysis with tooltips
4. **Auto-healing is recommended** for first runs to fix common issues
5. **Run sequential mode** if debugging specific test failures

## Integration with CI/CD

```bash
# Example GitHub Actions / CI pipeline
python3 -m app.testing.cli_runner \
  --excel-path tests/bdd_suite.xlsx \
  --run-id "ci_build_${BUILD_ID}" \
  --parallel \
  --max-workers 10

# Check exit code
if [ $? -eq 0 ]; then
  echo "All tests passed!"
else
  echo "Tests failed - check reports"
  exit 1
fi
```
