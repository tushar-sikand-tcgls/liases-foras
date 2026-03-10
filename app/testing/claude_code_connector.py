"""
Claude Code Connector for Auto-Healing

Enables QA Automation to invoke Claude Code for intelligent debugging and fixing.
Creates debug session files that Claude Code can analyze and respond to.
"""

import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from app.testing.test_models import TestRun, TestResult, BDDTestCase


class ClaudeCodeConnector:
    """
    Connector to enable QA Automation to communicate with Claude Code

    Creates structured debug session files that Claude Code can read and respond to.
    """

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.debug_sessions_dir = self.project_root / "data" / "debug_sessions"
        self.debug_sessions_dir.mkdir(parents=True, exist_ok=True)

    def create_debug_session(
        self,
        test_run: TestRun,
        session_name: Optional[str] = None
    ) -> Path:
        """
        Create a debug session file for Claude Code to analyze

        Args:
            test_run: Completed test run with failures
            session_name: Optional custom session name

        Returns:
            Path to the generated debug session file
        """
        if session_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_name = f"debug_session_{test_run.run_id}_{timestamp}"

        session_file = self.debug_sessions_dir / f"{session_name}.json"

        # Get failed tests
        failed_tests = test_run.get_failed_tests()

        # Create debug session data
        session_data = {
            "session_id": session_name,
            "run_id": test_run.run_id,
            "created_at": datetime.now().isoformat(),
            "summary": {
                "total_tests": test_run.summary.total_tests,
                "passed": test_run.summary.passed,
                "failed": test_run.summary.failed,
                "fail_inclusion": test_run.summary.fail_inclusion,
                "fail_similarity": test_run.summary.fail_similarity,
                "pass_rate": test_run.summary.pass_rate
            },
            "failed_tests": [
                self._serialize_failed_test(result)
                for result in failed_tests
            ],
            "claude_code_instructions": {
                "task": "analyze_and_fix_test_failures",
                "context": "BDD test automation with dual validation (inclusion + similarity)",
                "fix_priorities": [
                    "1. Prompt clarification (add context, remove ambiguity)",
                    "2. Expected answer normalization (handle units, numbers)",
                    "3. Good answer refinement (improve reference quality)"
                ],
                "constraints": [
                    "Preserve original values in _original columns",
                    "Only suggest high-confidence fixes",
                    "Flag low-confidence fixes for manual review"
                ],
                "output_format": "Generate fixes in the 'fixes' array below"
            },
            "fixes": [],  # Claude Code will populate this
            "status": "pending_review"  # pending_review | in_progress | completed
        }

        # Write session file
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)

        # Also create a human-readable markdown version
        self._create_markdown_summary(session_file.with_suffix('.md'), test_run, failed_tests)

        return session_file

    def _serialize_failed_test(self, result: TestResult) -> Dict:
        """Serialize a failed test result for Claude Code analysis"""
        tc = result.test_case

        # Handle both enum and string types
        type_value = tc.type.value if hasattr(tc.type, 'value') else str(tc.type)
        status_value = result.status.value if hasattr(result.status, 'value') else str(result.status)

        return {
            "test_id": tc.test_id,
            "row_number": tc.row_number,
            "type": type_value,
            "status": status_value,
            "failure_analysis": {
                "inclusion_passed": result.validation.inclusion_passed,
                "inclusion_explanation": result.validation.inclusion_explanation,
                "similarity_score": result.validation.similarity_score,
                "similarity_threshold": result.validation.similarity_threshold,
                "similarity_passed": result.validation.similarity_passed,
                "similarity_explanation": result.validation.similarity_explanation
            },
            "test_data": {
                "prompt": tc.prompt,
                "good_answer": tc.good_answer,
                "expected_answer_include": tc.expected_answer_include,
                "score_target": tc.score_target,
                "model_answer": result.model_answer
            },
            "current_state": {
                "auto_fixed": tc.auto_fixed,
                "fix_reason": tc.fix_reason,
                "needs_review": tc.needs_review,
                "has_original_prompt": tc.prompt_original is not None,
                "has_original_expected": tc.expected_answer_include_original is not None
            }
        }

    def _create_markdown_summary(self, md_file: Path, test_run: TestRun, failed_tests: List[TestResult]):
        """Create human-readable markdown summary for Claude Code"""

        md_content = f"""# QA Automation Debug Session

**Run ID:** {test_run.run_id}
**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Status:** 🔴 {test_run.summary.failed} failures need attention

---

## Summary

- **Total Tests:** {test_run.summary.total_tests}
- **Passed:** {test_run.summary.passed} ({test_run.summary.pass_rate:.1f}%)
- **Failed:** {test_run.summary.failed} ({test_run.summary.fail_rate:.1f}%)
  - Inclusion failures: {test_run.summary.fail_inclusion}
  - Similarity failures: {test_run.summary.fail_similarity}

---

## Failed Tests Analysis

"""

        for i, result in enumerate(failed_tests, 1):
            tc = result.test_case

            # Handle both enum and string types
            type_display = tc.type.value if hasattr(tc.type, 'value') else str(tc.type)
            status_display = result.status.value if hasattr(result.status, 'value') else str(result.status)

            md_content += f"""
### {i}. Test #{tc.test_id} ({tc.row_number}) - {type_display}

**Status:** {status_display}

**Prompt:**
```
{tc.prompt}
```

**Expected Answer Should Include:**
```
{tc.expected_answer_include}
```

**Model Answer:**
```
{result.model_answer}
```

**Good Answer (Reference):**
```
{tc.good_answer}
```

**Failure Analysis:**
- ✓/✗ Inclusion Check: {"PASS" if result.validation.inclusion_passed else "FAIL"}
  - {result.validation.inclusion_explanation}
- ✓/✗ Similarity Check: {"PASS" if result.validation.similarity_passed else "FAIL"}
  - Score: {result.validation.similarity_score:.3f} vs Threshold: {result.validation.similarity_threshold:.3f}
  - {result.validation.similarity_explanation}

**Fix Suggestions Needed:**
- [ ] Prompt improvement?
- [ ] Expected answer normalization?
- [ ] Good answer refinement?

---
"""

        md_content += f"""
## Claude Code Instructions

Please analyze the failures above and provide intelligent fixes:

1. **Analyze root causes:** Why did each test fail?
2. **Suggest fixes:** For each failure, suggest one of:
   - Prompt clarification (make the query clearer)
   - Expected answer normalization (handle units, numbers, formatting)
   - Good answer improvement (better reference answer)
3. **Provide confidence scores:** Rate each fix 0-1
4. **Flag for review:** Mark low-confidence fixes for manual review

**Output Format:**
Write your fixes to the corresponding `.json` file in the 'fixes' array:

```json
{{
  "test_id": 123,
  "fix_type": "prompt|expected|good_answer",
  "original_value": "...",
  "suggested_value": "...",
  "reason": "...",
  "confidence": 0.8,
  "needs_review": false
}}
```

---

**JSON Session File:** `{md_file.with_suffix('.json').name}`
"""

        with open(md_file, 'w') as f:
            f.write(md_content)

    def load_debug_session(self, session_name: str) -> Dict:
        """Load a debug session file"""
        session_file = self.debug_sessions_dir / f"{session_name}.json"

        if not session_file.exists():
            raise FileNotFoundError(f"Debug session not found: {session_name}")

        with open(session_file, 'r') as f:
            return json.load(f)

    def save_fixes(self, session_name: str, fixes: List[Dict]):
        """Save Claude Code's fixes to the session file"""
        session_file = self.debug_sessions_dir / f"{session_name}.json"

        with open(session_file, 'r') as f:
            session_data = json.load(f)

        session_data["fixes"] = fixes
        session_data["status"] = "completed"
        session_data["completed_at"] = datetime.now().isoformat()

        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)

    def get_pending_sessions(self) -> List[str]:
        """Get list of pending debug sessions"""
        pending = []
        for session_file in self.debug_sessions_dir.glob("*.json"):
            with open(session_file, 'r') as f:
                data = json.load(f)
                if data.get("status") == "pending_review":
                    pending.append(session_file.stem)
        return pending


# Global connector instance
claude_code_connector = ClaudeCodeConnector()
