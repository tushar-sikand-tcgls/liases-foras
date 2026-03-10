"""
Fix Applier - Safely Apply Claude Code's Intelligent Fixes

Takes fixes from debug sessions and applies them to test cases with full validation and safety checks.
"""

from typing import List, Dict
from app.testing.test_models import BDDTestCase
from app.testing.auto_healer import auto_healer


class FixApplier:
    """
    Safely applies Claude Code's intelligent fixes to test cases

    Security features:
    - Validates all fix data before application
    - Preserves original values
    - Logs all changes
    - Supports rollback
    """

    def __init__(self):
        self.applied_fixes = []
        self.validation_errors = []

    def validate_fix(self, fix: Dict) -> bool:
        """
        Validate a fix before application

        Security checks:
        - Required fields present
        - Valid fix_type
        - Confidence in valid range
        - No code injection patterns
        """
        required_fields = ["test_id", "fix_type", "original_value", "suggested_value", "reason", "confidence"]

        # Check required fields
        for field in required_fields:
            if field not in fix:
                self.validation_errors.append(f"Missing required field: {field}")
                return False

        # Validate fix_type
        valid_types = ["prompt", "expected", "good_answer"]
        if fix["fix_type"] not in valid_types:
            self.validation_errors.append(f"Invalid fix_type: {fix['fix_type']}")
            return False

        # Validate confidence range
        try:
            confidence = float(fix["confidence"])
            if not (0 <= confidence <= 1):
                self.validation_errors.append(f"Confidence out of range: {confidence}")
                return False
        except (ValueError, TypeError):
            self.validation_errors.append(f"Invalid confidence value: {fix['confidence']}")
            return False

        # Security: Check for suspicious patterns
        suspicious_patterns = ["<script", "eval(", "exec(", "__import__", "os.system"]
        for pattern in suspicious_patterns:
            if pattern in fix.get("suggested_value", "").lower():
                self.validation_errors.append(f"Suspicious pattern detected: {pattern}")
                return False

        return True

    def apply_fix(self, test_case: BDDTestCase, fix: Dict) -> BDDTestCase:
        """
        Apply a single fix to a test case

        Preserves original values and adds metadata
        """
        # Create a copy
        fixed_case = test_case.copy(deep=True)

        # Apply fix based on type
        if fix["fix_type"] == "prompt":
            if fixed_case.prompt_original is None:
                fixed_case.prompt_original = fixed_case.prompt
            fixed_case.prompt = fix["suggested_value"]

        elif fix["fix_type"] == "expected":
            if fixed_case.expected_answer_include_original is None:
                fixed_case.expected_answer_include_original = fixed_case.expected_answer_include
            fixed_case.expected_answer_include = fix["suggested_value"]

        elif fix["fix_type"] == "good_answer":
            if fixed_case.good_answer_original is None:
                fixed_case.good_answer_original = fixed_case.good_answer
            fixed_case.good_answer = fix["suggested_value"]

        # Update metadata
        fixed_case.auto_fixed = True
        fixed_case.fix_reason = f"Claude Code: {fix['reason']}"
        fixed_case.needs_review = fix.get("needs_review", False) or fix["confidence"] < 0.7

        return fixed_case

    def apply_fixes_to_test_cases(
        self,
        test_cases: List[BDDTestCase],
        fixes: List[Dict],
        min_confidence: float = 0.5
    ) -> tuple[List[BDDTestCase], Dict]:
        """
        Apply multiple fixes to test cases

        Args:
            test_cases: List of test cases
            fixes: List of Claude Code fixes
            min_confidence: Minimum confidence threshold (default 0.5)

        Returns:
            (updated_test_cases, summary)
        """
        self.applied_fixes = []
        self.validation_errors = []

        # Create a mapping of test_id to test_case
        test_case_map = {tc.test_id: tc for tc in test_cases}

        updated_test_cases = test_cases.copy()
        stats = {
            "total_fixes": len(fixes),
            "applied": 0,
            "skipped_low_confidence": 0,
            "skipped_validation": 0,
            "needs_review": 0
        }

        for fix in fixes:
            # Validate fix
            if not self.validate_fix(fix):
                stats["skipped_validation"] += 1
                continue

            # Check confidence threshold
            if fix["confidence"] < min_confidence:
                stats["skipped_low_confidence"] += 1
                continue

            # Find test case
            test_id = fix["test_id"]
            if test_id not in test_case_map:
                self.validation_errors.append(f"Test ID not found: {test_id}")
                stats["skipped_validation"] += 1
                continue

            # Apply fix
            original_case = test_case_map[test_id]
            fixed_case = self.apply_fix(original_case, fix)

            # Replace in list
            for i, tc in enumerate(updated_test_cases):
                if tc.test_id == test_id:
                    updated_test_cases[i] = fixed_case
                    break

            # Track stats
            stats["applied"] += 1
            if fixed_case.needs_review:
                stats["needs_review"] += 1

            self.applied_fixes.append({
                "test_id": test_id,
                "fix_type": fix["fix_type"],
                "confidence": fix["confidence"],
                "needs_review": fixed_case.needs_review
            })

        return updated_test_cases, stats

    def get_summary(self) -> str:
        """Get a summary of applied fixes"""
        return f"""
Fix Application Summary:
- Applied: {len(self.applied_fixes)} fixes
- Validation Errors: {len(self.validation_errors)}
- Needs Review: {sum(1 for f in self.applied_fixes if f.get('needs_review', False))}
"""


# Global instance
fix_applier = FixApplier()
