# UltraThink Auto-Healing Testing System

## Overview
A comprehensive auto-healing, auto-correcting testing system that combines QA (behavioral/functional testing) and Developer (bug-fixing) roles.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Interface Layer                         │
│  - Streamlit UI (control panel)                                 │
│  - FastAPI endpoints (/api/testing/*)                           │
│  - Email-friendly reports (hideable HTML tables)                │
└─────────────────────────────────────────────────────────────────┘
                              ↓ ↑
┌─────────────────────────────────────────────────────────────────┐
│                 Auto-Healing Test Service                        │
│  - Test Execution Engine                                        │
│  - Validation Logic (Inclusion + Similarity)                    │
│  - Auto-Healing/Auto-Correction Logic                           │
│  - Regression Runner                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓ ↑
┌─────────────────────────────────────────────────────────────────┐
│                 QueryOrchestrator Integration                    │
│  (Uses hexagonal architecture we just built)                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓ ↑
┌─────────────────────────────────────────────────────────────────┐
│                Excel File (Source of Truth)                      │
│  /change-request/BDD-test-cases/BDD_Test_Cases.xlsx            │
│  - 121 test cases                                               │
│  - Schema: Type, Prompt, Good Answer, Expected Answer, Score    │
└─────────────────────────────────────────────────────────────────┘
```

## Excel Schema

**Detected Columns:**
1. **Type** - Test category (Objective, Subjective, Calculated)
2. **Prompt** - User query to test
3. **Good Answer** - Reference answer for similarity comparison
4. **Expected Answer Should Include** - Required substring (hard constraint)
5. **Score Target** - Similarity threshold (e.g., "> 7/10")

**Additional Columns (Auto-created during testing):**
- `Prompt_original` - Preserves original prompt before auto-fixes
- `Good Answer_original` - Preserves original good answer
- `Expected Answer Should Include_original` - Preserves original expectation
- `Model_Answer` - Actual model response
- `Status` - PASS/FAIL/FAIL_INCLUSION/FAIL_SIMILARITY
- `Similarity_Score` - Computed similarity (0-1 scale)
- `Auto_Fixed` - Boolean flag
- `Needs_Review` - Flag for contentious fixes
- `Run_Id` - Tracks test iterations (initial, regression_1, etc.)

## Test Execution Flow

### Phase 1: Initial Test Run
```
1. Load Excel file → Parse 121 test cases
2. For each test:
   a. Execute: Call model with Prompt
   b. Validate:
      - Inclusion Check: Does Model_Answer contain "Expected Answer Should Include"?
      - Similarity Check: Is similarity(Model_Answer, Good Answer) > Score Target?
   c. Mark: PASS (both pass) or FAIL (either fails)
3. Generate initial report with failure analysis
```

### Phase 2: Auto-Healing (Developer Role)
```
For each FAILING test:
1. Analyze root cause:
   - Prompt clarity issue?
   - Expected answer too strict?
   - Good answer needs refinement?

2. Apply targeted fixes (priority order):
   Priority 1: Fix Prompt (clarify, add context, specify units)
   Priority 2: Loosen "Expected Answer Should Include" (normalize units, allow variants)
   Priority 3: Refine "Good Answer" (enrich while keeping facts)

3. Preserve originals in _original columns
4. Mark contentious fixes with Needs_Review flag
```

### Phase 3: Regression Run
```
1. Re-run ENTIRE test suite (not just failures)
2. Track improvements: initial FAIL → regression PASS?
3. Generate delta report showing before/after
4. Ask user: "Continue to next cycle or stop?"
```

## Validation Logic Details

### 1. Inclusion Check (Hard Constraint)
```python
def inclusion_check(model_answer, expected_include):
    # Normalize both strings
    model_norm = normalize(model_answer)  # lowercase, trim, units
    expected_norm = normalize(expected_include)

    # Check if expected is substring of model answer
    if expected_norm in model_norm:
        return PASS

    # Allow numeric/unit flexibility:
    # "3018 Units" == "3,018 units" == "3018units"
    if fuzzy_numeric_match(model_norm, expected_norm):
        return PASS

    return FAIL_INCLUSION
```

### 2. Similarity Check (Soft but Thresholded)
```python
def similarity_check(model_answer, good_answer, score_target):
    # Parse threshold: "> 7/10" → 0.7
    threshold = parse_score_target(score_target)  # Returns 0.7

    # Compute semantic similarity using embeddings
    similarity_score = cosine_similarity(
        embed(model_answer),
        embed(good_answer)
    )

    # Must be STRICTLY GREATER than threshold
    if similarity_score > threshold:
        return PASS, similarity_score

    return FAIL_SIMILARITY, similarity_score
```

## Auto-Healing Strategies

### Strategy 1: Prompt Fixes
**Problem**: Ambiguous or unclear prompts
**Fix**: Add specificity

**Example:**
- Before: "What is the area?"
- After: "What is the Project Size in Units of Sara City?"

### Strategy 2: Expected Answer Normalization
**Problem**: Too strict matching, unit/format issues
**Fix**: Allow flexible matching

**Example:**
- Before: "3018 Units"
- After: "3018|3,018 Units|units"  (regex pattern)

### Strategy 3: Good Answer Refinement
**Problem**: Missing context or too terse
**Fix**: Enrich while preserving facts

**Example:**
- Before: "3018 Units"
- After: "The Project Size of Sara City is 3018 Units, launched in Nov 2007 in Chakan."

## Report Format

### Email-Friendly Summary
```
=======================================================================
AUTO-HEALING TEST REPORT - Run: initial
=======================================================================

SUMMARY:
--------
Total Tests: 121
Passed: 87 (71.9%)
Failed: 34 (28.1%)

BY TYPE:
- Objective:   45/60 passed (75.0%)
- Subjective:  25/35 passed (71.4%)
- Calculated:  17/26 passed (65.4%)

TOP FAILURE REASONS:
1. Missing numeric value in answer (12 cases)
2. Unit mismatch (sq.ft. vs sqft) (8 cases)
3. Below similarity threshold (7 cases)
4. Missing project context (7 cases)

NARRATIVE:
The model performs well on objective factual queries but struggles with:
- Unit normalization (need to standardize sq.ft., sqft, ft²)
- Providing complete context (project name, location, developer)
- Calculated metrics requiring formula evaluation

AUTO-FIXES APPLIED: 34 test cases modified
- 18 prompts clarified
- 10 expected answers normalized
- 6 good answers enriched

=======================================================================

Do you want another refinement cycle (further auto-fixing and regression run),
or are you satisfied with the current test outcomes?

[Click to view detailed test grid ▼]
```

### Hideable Test Grid (HTML)
```html
<details>
  <summary>Click to expand detailed test results (121 tests)</summary>

  <table border="1" style="border-collapse: collapse; width: 100%;">
    <thead>
      <tr>
        <th>ID</th>
        <th>Type</th>
        <th>Prompt</th>
        <th>Status</th>
        <th>Similarity</th>
        <th>Expected</th>
        <th>Remark</th>
        <th>Edit</th>
      </tr>
    </thead>
    <tbody>
      <!-- Each row is editable with inline forms -->
      <tr style="background-color: #ffcccc;">  <!-- Red for FAIL -->
        <td>1</td>
        <td>Objective</td>
        <td contenteditable="true">What is the Project Size of Sara City?</td>
        <td>FAIL_INCLUSION</td>
        <td>0.65</td>
        <td contenteditable="true">3018 Units</td>
        <td>Missing "Units" in response</td>
        <td><button onclick="saveEdit(1)">Save</button></td>
      </tr>
      <tr style="background-color: #ccffcc;">  <!-- Green for PASS -->
        <td>2</td>
        <td>Objective</td>
        <td contenteditable="true">What is the Total Supply of Sara City?</td>
        <td>PASS</td>
        <td>0.89</td>
        <td contenteditable="true">1109 Units</td>
        <td>OK</td>
        <td><button onclick="saveEdit(2)">Save</button></td>
      </tr>
      <!-- ... 119 more rows ... -->
    </tbody>
  </table>
</details>
```

## API Endpoints

### POST /api/testing/run
Execute full test cycle
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
  "auto_fixed_count": 34,
  "report_html": "<html>...</html>",
  "report_text": "..."
}
```

### POST /api/testing/heal
Apply auto-healing to failures
```json
{
  "excel_path": "/path/to/BDD_Test_Cases.xlsx",
  "failed_test_ids": [1, 5, 12, ...]
}
```

### POST /api/testing/regression
Run regression after heal
```json
{
  "excel_path": "/path/to/BDD_Test_Cases.xlsx",
  "run_id": "regression_1"
}
```

### POST /api/testing/save-edits
Write user edits back to Excel
```json
{
  "excel_path": "/path/to/BDD_Test_Cases.xlsx",
  "edits": [
    {
      "test_id": 1,
      "prompt": "new prompt text",
      "expected_answer": "new expected",
      "good_answer": "new good answer"
    }
  ]
}
```

### GET /api/testing/report/{run_id}
Retrieve report for a specific run

## Streamlit UI

Location: `frontend/pages/ultrathink_testing.py`

**Features:**
1. **Control Panel**
   - Load Excel file
   - Start initial test run
   - View real-time progress
   - Trigger auto-healing
   - Run regression

2. **Dashboard**
   - Pass/Fail pie chart
   - Breakdown by Type
   - Top failure reasons
   - Score distribution histogram

3. **Test Grid**
   - Sortable, filterable table
   - Inline editing
   - Status highlighting
   - Export to CSV

4. **Iteration Controls**
   - "Run Next Cycle" button
   - Comparison view (before/after)
   - History of runs

## Implementation Files

```
app/testing/
├── __init__.py
├── test_models.py          # BDDTestCase, TestResult, TestRun models
├── test_service.py         # AutoHealingTestService (main engine)
├── excel_handler.py        # Read/write Excel with openpyxl
├── validators.py           # Inclusion + similarity checks
├── auto_healer.py          # Auto-fix logic
└── report_generator.py     # Email-friendly reports

app/api/
└── testing.py              # FastAPI endpoints

frontend/pages/
└── ultrathink_testing.py   # Streamlit UI
```

## Next Steps

1. ✅ Create domain models (test_models.py)
2. ✅ Build test service (test_service.py)
3. ✅ Implement validators (validators.py)
4. ✅ Create auto-healer (auto_healer.py)
5. ✅ Build report generator (report_generator.py)
6. ✅ Create API endpoints (testing.py)
7. ✅ Build Streamlit UI

## Usage Example

```python
from app.testing import AutoHealingTestService

# Initialize service
service = AutoHealingTestService(
    excel_path="/path/to/BDD_Test_Cases.xlsx"
)

# Run initial test cycle
initial_results = service.run_test_cycle(
    run_id="initial",
    auto_heal=True
)

print(initial_results.summary_report)
# Shows: 87/121 passed, 34 auto-fixed

# Run regression after healing
regression_results = service.run_regression(
    run_id="regression_1"
)

print(regression_results.delta_report)
# Shows: 34 → 28 failures (6 fixed by auto-healing)

# Generate email report
email_html = service.generate_email_report(
    run_id="regression_1",
    include_editable_grid=True
)
```

## Key Design Principles

1. **Non-Destructive**: Always preserve originals in `_original` columns
2. **Auditable**: Every change tracked with run_id and timestamps
3. **Idempotent**: Can re-run on same Excel multiple times
4. **Conservative**: Never fabricate data, only normalize/clarify
5. **Transparent**: Clear explanations for every auto-fix
6. **User-Controlled**: User can approve/reject auto-fixes

## Status

**Current Phase:** Implementation in progress
- ✅ Schema detected and documented
- ✅ Architecture designed
- ⏳ Core services being built
- ⏳ API endpoints to be created
- ⏳ UI to be built

**Next Action:** Continue building core services (test_service.py, validators.py, auto_healer.py)
