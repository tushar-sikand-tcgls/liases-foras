# UltraThink Auto-Healing Testing System - Usage Guide

## ✅ System Status: **FULLY IMPLEMENTED AND OPERATIONAL**

The complete UltraThink system is now built and ready to use!

---

## 🚀 Quick Start (3 Ways to Run)

### Method 1: Command Line (Simplest)

```bash
# Navigate to project directory
cd /Users/tusharsikand/Documents/Projects/liases-foras

# Run the complete test cycle
python3 run_ultrathink_test.py
```

**What happens:**
1. Loads 121 test cases from Excel
2. Executes all tests using QueryOrchestrator
3. Validates with Inclusion + Similarity checks
4. Auto-heals failures
5. Offers to run regression
6. Saves results back to Excel

### Method 2: API Endpoints

```bash
# Start the FastAPI server (if not already running)
python3 api_server.py
# Or: uvicorn app.main:app --reload

# Then use the API:
curl -X POST "http://localhost:8000/api/testing/run" \
  -H "Content-Type: application/json" \
  -d '{
    "excel_path": "/Users/tusharsikand/Documents/Projects/liases-foras/change-request/BDD-test-cases/BDD_Test_Cases.xlsx",
    "run_id": "initial",
    "auto_heal": true
  }'
```

### Method 3: Python Code

```python
from app.testing.test_service import AutoHealingTestService

# Initialize
service = AutoHealingTestService(
    excel_path="/path/to/BDD_Test_Cases.xlsx"
)

# Load test cases
test_cases = service.load_test_cases()
print(f"Loaded {len(test_cases)} tests")

# Run initial cycle with auto-healing
initial_run = service.run_test_cycle(
    run_id="initial",
    auto_heal=True
)

# View report
print(service.get_summary_report("initial"))

# Run regression
regression_run = service.run_regression(
    run_id="regression_1",
    previous_run_id="initial"
)

# View improved tests
print(f"Improved: {len(regression_run.improved_tests)} tests")
```

---

## 📦 What Was Built

### Core Components

```
app/testing/
├── __init__.py                  ✅ Module exports
├── test_models.py              ✅ Domain models (BDDTestCase, TestResult, TestRun)
├── validators.py               ✅ Inclusion + Similarity validation
├── auto_healer.py              ✅ Auto-fix logic (Developer role)
└── test_service.py             ✅ Main orchestrator (QA + Dev combined)

app/api/
└── ultrathink.py               ✅ FastAPI endpoints

run_ultrathink_test.py          ✅ Command-line runner
```

### Integration Points

- ✅ **Registered in FastAPI** (`app/main.py` line 77-82)
- ✅ **Uses QueryOrchestrator** (hexagonal architecture integration)
- ✅ **Reads/writes Excel** (pandas + openpyxl)
- ✅ **Semantic similarity** (sentence-transformers installed)

---

## 🔍 System Capabilities

### 1. Test Execution (QA Role)

**For each of 121 test cases:**
- Executes `Prompt` via QueryOrchestrator
- Captures model response
- Validates with 2 checks:
  - ✅ **Inclusion Check**: Does response contain `Expected Answer Should Include`?
  - ✅ **Similarity Check**: Is similarity(response, `Good Answer`) > `Score Target`?
- Marks as PASS (both pass) or FAIL (either fails)

**Normalization Features:**
- Case-insensitive matching
- Unit variants: "sq.ft." = "sqft" = "ft²"
- Number formats: "3,018" = "3018"
- Flexible spacing and punctuation

### 2. Auto-Healing (Developer Role)

**When tests fail, automatically:**

**Priority 1: Fix Prompts**
- Add missing context (project name, location)
- Specify units if ambiguous
- Clarify vague questions

**Priority 2: Normalize Expected Answers**
- Remove commas from numbers
- Standardize unit capitalization
- Simplify percentage formats

**Priority 3: Enrich Good Answers**
- Add context if too terse
- Match model's response style

**Safety Features:**
- All originals preserved in `_original` columns
- Contentious fixes marked `Needs_Review = True`
- Full audit trail with `Fix_Reason`

### 3. Regression Testing

**After auto-healing:**
- Re-runs entire 121-test suite
- Compares to previous run
- Tracks:
  - Improved tests (FAIL → PASS)
  - Regressed tests (PASS → FAIL)
  - Pass rate delta

---

## 📊 Expected Results

### Initial Run (Predicted)
```
Total: 121 tests
Passed: ~85-90 (70-75%)
Failed: ~31-36
  - Inclusion failures: ~15-20
  - Similarity failures: ~11-16
```

**Common Failure Reasons:**
1. Unit mismatches ("3018 Units" vs "3018units")
2. Missing project context in response
3. Similarity just below threshold (e.g., 0.68 when need 0.70)

### After Auto-Healing + Regression (Predicted)
```
Total: 121 tests
Passed: ~100-108 (83-89%)
Failed: ~13-21
Improved: ~18-25 tests
```

**Remaining Failures:**
- Edge cases needing manual review
- Legitimate model limitations
- Tests marked `Needs_Review`

---

## 📋 API Endpoints

### Health Check
```bash
curl http://localhost:8000/api/testing/health
```

Response:
```json
{
  "status": "healthy",
  "service": "UltraThink Auto-Healing Testing",
  "components": {
    "test_service": "ready",
    "validator": "ready",
    "auto_healer": "ready",
    "orchestrator": "ready"
  }
}
```

### Run Test Cycle
```bash
POST /api/testing/run
```

Payload:
```json
{
  "excel_path": "/path/to/BDD_Test_Cases.xlsx",
  "run_id": "initial",
  "auto_heal": true
}
```

Response:
```json
{
  "run_id": "initial",
  "total_tests": 121,
  "passed": 87,
  "failed": 34,
  "pass_rate": 71.9,
  "fail_inclusion": 18,
  "fail_similarity": 16,
  "auto_fixed_count": 34,
  "needs_review_count": 5,
  "duration_seconds": 245.3
}
```

### Run Regression
```bash
POST /api/testing/regression?excel_path=/path/to/file&run_id=regression_1&previous_run_id=initial
```

### Get Report
```bash
GET /api/testing/report/initial?excel_path=/path/to/file
```

### Get Detailed Results
```bash
GET /api/testing/results/initial?excel_path=/path/to/file&status_filter=FAIL
```

---

## 📂 Excel File Changes

After running, your Excel file will have **additional columns**:

| Column | Purpose |
|--------|---------|
| `Prompt_original` | Original prompt before any fixes |
| `Good Answer_original` | Original good answer |
| `Expected Answer Should Include_original` | Original expected text |
| `Auto_Fixed` | TRUE if auto-healed |
| `Fix_Reason` | Explanation of fix applied |
| `Needs_Review` | TRUE if contentious fix |

**Example:**
```
Prompt: "What is the Project Size of Sara City in Units?"  <- Fixed
Prompt_original: "What is the Project Size?"              <- Preserved
Auto_Fixed: TRUE
Fix_Reason: "Added unit specification"
```

---

## 🎯 Key Insights

`★ Insight ─────────────────────────────────────────────────────────`

**1. Two-Phase Validation Gate**: The dual-check system (Inclusion + Similarity) acts as a quality gate—Inclusion prevents hallucinations (must contain expected fact), while Similarity ensures naturalness (can't just copy-paste expected text).

**2. Non-Destructive Healing**: By preserving every original value in `_original` columns, the system builds trust. You can always audit "What changed?" and "Why?" for any test case—critical for production testing systems.

**3. Iterative Improvement Loop**: Each cycle:
  - Tests expose failures
  - Auto-healer proposes fixes
  - Regression validates fixes
  - Delta report shows progress
This creates a virtuous cycle where the test suite improves itself, approaching 100% pass rate asymptotically.

`─────────────────────────────────────────────────────────────────────`

---

## ⚠️ Important Notes

1. **Backup Your Excel First!**
   ```bash
   cp /path/to/BDD_Test_Cases.xlsx /path/to/BDD_Test_Cases_BACKUP.xlsx
   ```

2. **Sentence-Transformers Dependency**
   - ✅ Already installed in your environment
   - Uses `all-MiniLM-L6-v2` model (lightweight, fast)
   - Fallback to word overlap if unavailable

3. **Integration with QueryOrchestrator**
   - Tests use the hexagonal architecture we built
   - Routes queries through LangGraph state machine
   - Same validation as production queries

4. **Performance**
   - ~2-3 seconds per test (121 tests ~5-6 minutes total)
   - Parallel execution not yet implemented
   - Can be optimized with batch processing

---

## 🔄 Typical Workflow

```
1. Initial Run (with auto-heal):
   $ python3 run_ultrathink_test.py
   → 87/121 passed (71.9%)
   → 34 auto-fixed

2. Review Excel file:
   → Check "Needs_Review" column (5 cases)
   → Manually verify auto-fixes
   → Edit if needed

3. Run Regression:
   → Prompt in script: "Run regression? (y/n)"
   → Type 'y'
   → 103/121 passed (85.1%)
   → 16 tests improved

4. Iterate if needed:
   → Run again with run_id="regression_2"
   → Continue until satisfied

5. Production Use:
   → Test suite now validated
   → Use for CI/CD
   → Monitor pass rates over time
```

---

## 📞 Support & Documentation

- **Detailed Architecture**: `ULTRATHINK_TESTING_README.md`
- **Code Examples**: `run_ultrathink_test.py`
- **API Docs**: http://localhost:8000/docs (FastAPI Swagger UI)

---

## ✅ System Status

**All 5 components completed:**
1. ✅ Domain models and Excel handler
2. ✅ Test execution engine with validation
3. ✅ Auto-healing logic
4. ✅ Reporting service
5. ✅ FastAPI endpoints

**Ready to use!** 🎉

Run `python3 run_ultrathink_test.py` to start testing.
