"""
Auto-Healer for Test Cases

Implements the "Developer Role" - automatically fixes failing tests
by analyzing failures and applying targeted corrections.
"""

import re
from typing import List, Optional
from app.testing.test_models import BDDTestCase, TestResult, AutoFixSuggestion, TestStatus


class AutoHealer:
    """
    Auto-healing logic for failing test cases

    Applies fixes in priority order:
    1. Prompt fixes (clarify, add context)
    2. Expected answer fixes (normalize units, loosen constraints)
    3. Good answer refinement (enrich while preserving facts)
    """

    def analyze_failure(self, result: TestResult) -> List[AutoFixSuggestion]:
        """
        Analyze a failing test and suggest fixes

        Returns list of fix suggestions ranked by priority
        """
        suggestions = []

        if result.validation.inclusion_passed and not result.validation.similarity_passed:
            # Similarity issue - good answer may need enrichment
            suggestions.extend(self._suggest_good_answer_fixes(result))

        elif not result.validation.inclusion_passed:
            # Inclusion issue - could be prompt or expected answer problem
            suggestions.extend(self._suggest_prompt_fixes(result))
            suggestions.extend(self._suggest_expected_answer_fixes(result))

        return sorted(suggestions, key=lambda s: s.confidence, reverse=True)

    def _suggest_prompt_fixes(self, result: TestResult) -> List[AutoFixSuggestion]:
        """Suggest fixes to make prompt clearer"""
        suggestions = []
        test_case = result.test_case
        prompt = test_case.prompt

        # Check if prompt lacks context (project name, location, developer)
        if "sara city" in prompt.lower():
            # Already has project name
            pass
        else:
            # Might need project name
            if "project" in prompt.lower() and "what" in prompt.lower():
                # Try to add project name if we can infer it
                # For now, mark as needs review
                suggestions.append(AutoFixSuggestion(
                    test_id=test_case.test_id,
                    fix_type="prompt",
                    original_value=prompt,
                    suggested_value=prompt + " (Consider adding specific project name)",
                    reason="Prompt may lack project context",
                    confidence=0.5,
                    needs_review=True
                ))

        # Check if prompt lacks unit specification
        if any(keyword in prompt.lower() for keyword in ["size", "area", "supply"]):
            if "units" not in prompt.lower() and "sqft" not in prompt.lower():
                # May need unit clarification
                suggested_prompt = prompt.rstrip('?') + " in Units?"
                suggestions.append(AutoFixSuggestion(
                    test_id=test_case.test_id,
                    fix_type="prompt",
                    original_value=prompt,
                    suggested_value=suggested_prompt,
                    reason="Prompt lacks unit specification",
                    confidence=0.7,
                    needs_review=False
                ))

        return suggestions

    def _suggest_expected_answer_fixes(self, result: TestResult) -> List[AutoFixSuggestion]:
        """Suggest fixes to make expected answer more flexible"""
        suggestions = []
        test_case = result.test_case
        expected = test_case.expected_answer_include

        # Check for rigid unit formatting
        if "Units" in expected or "units" in expected:
            # Try to make units case-insensitive and spacing-flexible
            flexible_expected = expected.replace("Units", "units").replace("  ", " ").strip()
            if flexible_expected != expected:
                suggestions.append(AutoFixSuggestion(
                    test_id=test_case.test_id,
                    fix_type="expected",
                    original_value=expected,
                    suggested_value=flexible_expected,
                    reason="Normalize unit capitalization",
                    confidence=0.9,
                    needs_review=False
                ))

        # Check for number formatting issues (commas)
        if "," in expected:
            # Remove commas to make matching easier
            flexible_expected = expected.replace(",", "")
            suggestions.append(AutoFixSuggestion(
                test_id=test_case.test_id,
                fix_type="expected",
                original_value=expected,
                suggested_value=flexible_expected,
                reason="Remove comma from numbers for flexible matching",
                confidence=0.95,
                needs_review=False
            ))

        # Check for percentage formatting
        if "%" in expected:
            # Extract number
            num_match = re.search(r'(\d+\.?\d*)\s*%', expected)
            if num_match:
                num = num_match.group(1)
                # Make it flexible: "89%" or "89 %" or "89percent"
                flexible_expected = f"{num}%"
                suggestions.append(AutoFixSuggestion(
                    test_id=test_case.test_id,
                    fix_type="expected",
                    original_value=expected,
                    suggested_value=flexible_expected,
                    reason="Simplify percentage format",
                    confidence=0.85,
                    needs_review=False
                ))

        return suggestions

    def _suggest_good_answer_fixes(self, result: TestResult) -> List[AutoFixSuggestion]:
        """Suggest enrichments to good answer"""
        suggestions = []
        test_case = result.test_case
        good_answer = test_case.good_answer
        model_answer = result.model_answer

        # If model answer is much longer and includes the expected content,
        # the good answer might be too terse
        if len(model_answer) > len(good_answer) * 1.5:
            # Good answer might need enrichment
            # Check if model answer contains key facts from good answer
            good_words = set(good_answer.lower().split())
            model_words = set(model_answer.lower().split())
            overlap = good_words & model_words

            if len(overlap) >= len(good_words) * 0.6:
                # Model answer contains most of good answer
                # Suggest enriching good answer with model's style
                suggestions.append(AutoFixSuggestion(
                    test_id=test_case.test_id,
                    fix_type="good_answer",
                    original_value=good_answer,
                    suggested_value=good_answer + " (Consider enriching with more context)",
                    reason="Good answer may be too terse compared to model's response style",
                    confidence=0.6,
                    needs_review=True
                ))

        return suggestions

    def apply_fix(self, test_case: BDDTestCase, suggestion: AutoFixSuggestion) -> BDDTestCase:
        """
        Apply a fix suggestion to a test case

        Preserves original in _original columns
        """
        # Create a copy
        fixed_case = test_case.copy(deep=True)

        if suggestion.fix_type == "prompt":
            # Save original if not already saved
            if fixed_case.prompt_original is None:
                fixed_case.prompt_original = fixed_case.prompt
            # Apply fix
            fixed_case.prompt = suggestion.suggested_value

        elif suggestion.fix_type == "expected":
            # Save original
            if fixed_case.expected_answer_include_original is None:
                fixed_case.expected_answer_include_original = fixed_case.expected_answer_include
            # Apply fix
            fixed_case.expected_answer_include = suggestion.suggested_value

        elif suggestion.fix_type == "good_answer":
            # Save original
            if fixed_case.good_answer_original is None:
                fixed_case.good_answer_original = fixed_case.good_answer
            # Apply fix
            fixed_case.good_answer = suggestion.suggested_value

        # Mark as auto-fixed
        fixed_case.auto_fixed = True
        fixed_case.fix_reason = suggestion.reason
        fixed_case.needs_review = suggestion.needs_review

        return fixed_case

    def heal_test_cases(self, failed_results: List[TestResult]) -> List[BDDTestCase]:
        """
        Heal a list of failing test cases

        Returns list of healed test cases
        """
        healed_cases = []

        for result in failed_results:
            suggestions = self.analyze_failure(result)

            if suggestions:
                # Apply the highest confidence fix
                best_suggestion = suggestions[0]
                healed_case = self.apply_fix(result.test_case, best_suggestion)
                healed_cases.append(healed_case)
            else:
                # No fix suggestions - mark for manual review
                test_case = result.test_case.copy(deep=True)
                test_case.needs_review = True
                healed_cases.append(test_case)

        return healed_cases


# Global auto-healer instance
auto_healer = AutoHealer()
