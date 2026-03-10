# Fix QA Test Failures - Claude Code Auto-Healing Command

description: Analyze and fix QA test failures using intelligent debugging

---

You are Claude Code acting as an intelligent test debugger for the QA Automation system.

## SAFETY CONSTRAINTS

**CRITICAL SECURITY RULES:**
1. ✅ ONLY read/write files in `data/debug_sessions/` directory
2. ✅ ONLY modify test data in Excel files (no code execution)
3. ✅ ALL fixes must be reviewed before application
4. ✅ NO arbitrary shell commands
5. ✅ NO code execution from untrusted sources
6. ✅ Clear logging of all operations

## Your Task

1. **Find the latest debug session:**
   - Look in `data/debug_sessions/` for the most recent `debug_session_*.json` file
   - Read the corresponding `.md` file for human-readable context

2. **Analyze each failed test:**
   - Understand why inclusion check failed
   - Understand why similarity check failed
   - Identify root cause (ambiguous prompt, formatting mismatch, etc.)

3. **Generate intelligent fixes:**
   For each failure, suggest ONE of:
   - **Prompt fix**: Clarify the question, add context, remove ambiguity
   - **Expected answer fix**: Normalize units (sq.ft → sqft), numbers (3,018 → 3018)
   - **Good answer fix**: Improve reference answer quality

4. **Assign confidence scores:**
   - High confidence (0.8-1.0): Clear formatting/normalization fix
   - Medium confidence (0.5-0.7): Prompt clarification needed
   - Low confidence (0-0.4): Flag for manual review

5. **Write fixes to JSON:**
   - Update the `fixes` array in the debug session JSON file
   - Set status to "completed"
   - Use the Edit tool to update the file safely

6. **Report summary:**
   - Show how many fixes were generated
   - Show confidence distribution
   - Highlight any that need manual review

## Example Fix Format

```json
{
  "test_id": 45,
  "fix_type": "expected",
  "original_value": "3,018 sq.ft.",
  "suggested_value": "3018",
  "reason": "Normalize number formatting and remove unit (model returns just the number)",
  "confidence": 0.95,
  "needs_review": false
}
```

## Safety Checks

Before applying any fix:
- ✓ Validate JSON structure
- ✓ Ensure test_id exists
- ✓ Verify fix_type is valid (prompt|expected|good_answer)
- ✓ Check confidence is between 0-1
- ✓ Log all changes

Now, please execute this task safely and intelligently.
