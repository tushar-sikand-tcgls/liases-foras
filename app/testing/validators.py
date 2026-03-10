"""
Validators for Auto-Healing Testing System

Implements two validation checks:
1. Inclusion Check (Hard Constraint) - Must contain expected substring
2. Similarity Check (Soft but Thresholded) - Must exceed similarity score target
"""

import re
from typing import Tuple
from app.testing.test_models import ValidationResult, TestStatus


class TestValidator:
    """Validates test results using inclusion and similarity checks"""

    def __init__(self):
        # We'll use sentence-transformers for semantic similarity
        # Lazy load to avoid startup overhead
        self._similarity_model = None

    def _get_similarity_model(self):
        """Lazy load sentence transformer model"""
        if self._similarity_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                # Use a lightweight but effective model
                self._similarity_model = SentenceTransformer('all-MiniLM-L6-v2')
            except ImportError:
                # Fallback: use simple word overlap if sentence-transformers not available
                print("Warning: sentence-transformers not installed. Using fallback similarity.")
                self._similarity_model = "fallback"
        return self._similarity_model

    def normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison

        - Lowercase
        - Trim whitespace
        - Normalize units (sq.ft., sqft, ft² → sqft)
        - Normalize numbers (remove commas: 3,018 → 3018)
        - Normalize percentage symbols (42%, 42 % → 42%)
        - Normalize unit suffixes (31 % units, 31 % → 31%)
        """
        if not text:
            return ""

        normalized = text.lower().strip()

        # Normalize units
        unit_mappings = {
            'sq.ft.': 'sqft',
            'sq. ft.': 'sqft',
            'sq ft': 'sqft',
            'square feet': 'sqft',
            'ft²': 'sqft',
            'ft2': 'sqft',
        }

        for old_unit, new_unit in unit_mappings.items():
            normalized = normalized.replace(old_unit, new_unit)

        # Remove commas from numbers
        normalized = re.sub(r'(\d),(\d)', r'\1\2', normalized)

        # Normalize percentage formatting: "42 %" or "42 % " → "42%"
        # Also handles "42 % units" → "42%"
        normalized = re.sub(r'(\d+\.?\d*)\s*%\s*(units?)?', r'\1%', normalized)

        # Normalize unit suffixes: "3018 units" → "3018units", "527 units/year" → "527units/year"
        # But keep the suffix for context
        normalized = re.sub(r'(\d+\.?\d*)\s+(units?)', r'\1\2', normalized)

        # Normalize multiple spaces to single space
        normalized = re.sub(r'\s+', ' ', normalized)

        return normalized

    def extract_numbers(self, text: str) -> set:
        """Extract all numbers from text for flexible matching"""
        # Find all numbers (including decimals)
        numbers = re.findall(r'\d+\.?\d*', text)
        return set(numbers)

    def inclusion_check(self, model_answer: str, expected_include: str) -> Tuple[bool, str]:
        """
        Check if model_answer contains expected_include (with normalization)

        Returns:
            (passed, explanation)
        """
        if not expected_include:
            return True, "No expected text to check"

        model_norm = self.normalize_text(model_answer)
        expected_norm = self.normalize_text(expected_include)

        # Direct substring match
        if expected_norm in model_norm:
            return True, f"Found exact match: '{expected_include}'"

        # Check if all numbers from expected are present in model answer
        expected_numbers = self.extract_numbers(expected_include)
        model_numbers = self.extract_numbers(model_answer)

        if expected_numbers and expected_numbers.issubset(model_numbers):
            # Numbers match, check if text is roughly there
            expected_words = set(expected_norm.split())
            model_words = set(model_norm.split())

            # At least 50% of expected words should be present
            overlap = expected_words & model_words
            if len(overlap) >= len(expected_words) * 0.5:
                return True, f"Found numeric match with partial text match: {overlap}"

        # Check for flexible unit matching (e.g., "3018 Units" vs "3018units")
        # Extract the main numeric value
        expected_num_match = re.search(r'(\d+\.?\d*)', expected_include)
        if expected_num_match:
            expected_num = expected_num_match.group(1)
            if expected_num in model_answer or expected_num.replace('.', '') in model_answer:
                return True, f"Found primary numeric value: {expected_num}"

        return False, f"Expected text '{expected_include}' not found in model answer"

    def parse_score_target(self, score_target: str) -> float:
        """
        Parse score target string to numeric threshold

        Examples:
            "> 7/10" → 0.7
            ">= 8/10" → 0.8
            "> 0.75" → 0.75

        Returns:
            Threshold as float (0-1 scale)
        """
        if not score_target:
            return 0.7  # Default threshold

        # Remove spaces and convert to lowercase
        target = score_target.strip().lower()

        # Extract numeric part
        # Pattern: optional ">=" or ">", followed by number, optionally "/10"
        match = re.search(r'[>=]*\s*(\d+\.?\d*)\s*(?:/\s*(\d+))?', target)

        if not match:
            return 0.7  # Default if can't parse

        numerator = float(match.group(1))
        denominator = float(match.group(2)) if match.group(2) else 1.0

        # If denominator is 10, treat as x/10 scale
        if denominator == 10.0:
            threshold = numerator / 10.0
        elif denominator == 1.0:
            # Already a decimal
            threshold = numerator
        else:
            threshold = numerator / denominator

        # Clamp to [0, 1]
        return max(0.0, min(1.0, threshold))

    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute semantic similarity between two texts

        Returns:
            Similarity score (0-1 scale)
        """
        if not text1 or not text2:
            return 0.0

        model = self._get_similarity_model()

        if model == "fallback":
            # Fallback: use Jaccard similarity on words
            words1 = set(self.normalize_text(text1).split())
            words2 = set(self.normalize_text(text2).split())

            if not words1 or not words2:
                return 0.0

            intersection = words1 & words2
            union = words1 | words2

            return len(intersection) / len(union) if union else 0.0

        else:
            # Use sentence-transformers
            try:
                from sklearn.metrics.pairwise import cosine_similarity
                import numpy as np

                # Encode both texts
                embedding1 = model.encode([text1])[0]
                embedding2 = model.encode([text2])[0]

                # Compute cosine similarity
                similarity = cosine_similarity(
                    embedding1.reshape(1, -1),
                    embedding2.reshape(1, -1)
                )[0][0]

                return float(similarity)

            except Exception as e:
                print(f"Similarity computation error: {e}")
                # Fallback to word overlap
                return self.compute_similarity_fallback(text1, text2)

    def compute_similarity_fallback(self, text1: str, text2: str) -> float:
        """Fallback similarity using word overlap"""
        words1 = set(self.normalize_text(text1).split())
        words2 = set(self.normalize_text(text2).split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def similarity_check(
        self,
        model_answer: str,
        good_answer: str,
        score_target: str
    ) -> Tuple[bool, float, str]:
        """
        Check if similarity between model_answer and good_answer exceeds threshold

        Returns:
            (passed, similarity_score, explanation)
        """
        threshold = self.parse_score_target(score_target)
        similarity_score = self.compute_similarity(model_answer, good_answer)

        # Must be STRICTLY GREATER than threshold
        passed = similarity_score > threshold

        if passed:
            explanation = f"Similarity {similarity_score:.3f} > threshold {threshold:.3f}"
        else:
            explanation = f"Similarity {similarity_score:.3f} ≤ threshold {threshold:.3f}"

        return passed, similarity_score, explanation

    def validate(
        self,
        model_answer: str,
        expected_include: str,
        good_answer: str,
        score_target: str
    ) -> ValidationResult:
        """
        Run full validation (inclusion + similarity)

        Both checks must pass for overall PASS status.
        """
        # Run inclusion check
        inclusion_passed, inclusion_explanation = self.inclusion_check(
            model_answer, expected_include
        )

        # Run similarity check
        similarity_passed, similarity_score, similarity_explanation = self.similarity_check(
            model_answer, good_answer, score_target
        )

        # Parse threshold for reporting
        threshold = self.parse_score_target(score_target)

        # Determine overall status
        if inclusion_passed and similarity_passed:
            status = TestStatus.PASS
        elif not inclusion_passed:
            status = TestStatus.FAIL_INCLUSION
        else:  # similarity failed
            status = TestStatus.FAIL_SIMILARITY

        return ValidationResult(
            inclusion_passed=inclusion_passed,
            inclusion_explanation=inclusion_explanation,
            similarity_passed=similarity_passed,
            similarity_score=similarity_score,
            similarity_threshold=threshold,
            similarity_explanation=similarity_explanation,
            overall_status=status
        )


# Global validator instance
test_validator = TestValidator()
