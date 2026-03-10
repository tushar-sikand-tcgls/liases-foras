"""
Test Models for Auto-Healing Testing System

Domain models representing BDD test cases, results, and test runs.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class TestType(str, Enum):
    """Type of test case"""
    OBJECTIVE = "Objective"
    SUBJECTIVE_PROJECT = "Subjective (Project)"
    SUBJECTIVE_DEVELOPER = "Subjective (Developer)"
    SUBJECTIVE_LOCATION = "Subjective (Location)"
    CALCULATED_FINANCIAL = "Calculated (Financial)"

    # Legacy values for backward compatibility
    SUBJECTIVE = "Subjective"  # Fallback for generic subjective
    CALCULATED = "Calculated"  # Fallback for generic calculated


class TestStatus(str, Enum):
    """Status of test execution"""
    PASS = "PASS"
    FAIL = "FAIL"
    FAIL_INCLUSION = "FAIL_INCLUSION"  # Failed inclusion check
    FAIL_SIMILARITY = "FAIL_SIMILARITY"  # Failed similarity check
    PENDING = "PENDING"
    SKIPPED = "SKIPPED"


class BDDTestCase(BaseModel):
    """Represents a single BDD test case from Excel"""

    # Identifiers
    test_id: int = Field(..., description="Row index in Excel (0-based)")
    row_number: int = Field(..., description="Excel row number (1-based, including header)")

    # Core test data
    type: TestType = Field(..., description="Type of test (Objective/Subjective/Calculated)")
    prompt: str = Field(..., description="Query to test")
    good_answer: str = Field(..., description="Reference answer for similarity comparison")
    expected_answer_include: str = Field(..., description="Required substring (hard constraint)")
    score_target: str = Field(..., description="Similarity threshold (e.g., '> 7/10')")

    # Original values (preserved before auto-fixes)
    prompt_original: Optional[str] = None
    good_answer_original: Optional[str] = None
    expected_answer_include_original: Optional[str] = None
    score_target_original: Optional[str] = None

    # Auto-fix metadata
    auto_fixed: bool = False
    fix_reason: Optional[str] = None
    needs_review: bool = False

    class Config:
        use_enum_values = False  # Keep as enum objects, not strings


class ValidationResult(BaseModel):
    """Result of validation checks"""

    # Inclusion check
    inclusion_passed: bool
    inclusion_explanation: str

    # Similarity check
    similarity_passed: bool
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="0-1 scale")
    similarity_threshold: float = Field(..., ge=0.0, le=1.0)
    similarity_explanation: str

    # Overall
    overall_status: TestStatus

    @property
    def passed(self) -> bool:
        """True if both checks passed"""
        return self.inclusion_passed and self.similarity_passed


class TestResult(BaseModel):
    """Result of executing a single test case"""

    # Test case reference
    test_case: BDDTestCase

    # Execution data
    run_id: str = Field(..., description="Identifier for this test run (e.g., 'initial', 'regression_1')")
    executed_at: datetime = Field(default_factory=datetime.utcnow)

    # Model response
    model_answer: str = Field(..., description="Actual response from model")
    execution_time_ms: Optional[float] = None

    # Validation
    validation: ValidationResult

    # Additional metadata
    error_message: Optional[str] = None
    remarks: Optional[str] = None

    @property
    def status(self) -> TestStatus:
        """Shortcut to validation status"""
        return self.validation.overall_status

    @property
    def passed(self) -> bool:
        """Shortcut to check if test passed"""
        return self.validation.passed


class TestRunSummary(BaseModel):
    """Summary statistics for a test run"""

    run_id: str
    total_tests: int
    passed: int
    failed: int
    fail_inclusion: int
    fail_similarity: int
    skipped: int = 0

    # By type
    objective_passed: int = 0
    objective_total: int = 0
    subjective_passed: int = 0
    subjective_total: int = 0
    calculated_passed: int = 0
    calculated_total: int = 0

    # Auto-fixing
    auto_fixed_count: int = 0
    needs_review_count: int = 0

    # Timing
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    @property
    def pass_rate(self) -> float:
        """Pass rate as percentage"""
        if self.total_tests == 0:
            return 0.0
        return (self.passed / self.total_tests) * 100

    @property
    def fail_rate(self) -> float:
        """Fail rate as percentage"""
        return 100.0 - self.pass_rate


class TestRun(BaseModel):
    """Complete test run with all results"""

    run_id: str
    excel_path: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # Test results
    results: List[TestResult] = []

    # Summary
    summary: Optional[TestRunSummary] = None

    # Comparison to previous run (for regression)
    previous_run_id: Optional[str] = None
    improved_tests: List[int] = []  # Test IDs that went from FAIL to PASS
    regressed_tests: List[int] = []  # Test IDs that went from PASS to FAIL

    def add_result(self, result: TestResult):
        """Add a test result"""
        self.results.append(result)

    def compute_summary(self):
        """Compute summary statistics"""
        if not self.results:
            return

        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        fail_inclusion = sum(1 for r in self.results if r.status == TestStatus.FAIL_INCLUSION)
        fail_similarity = sum(1 for r in self.results if r.status == TestStatus.FAIL_SIMILARITY)

        # By type (group subcategories)
        # Helper to get string value (handles both enum and string types)
        def get_type_str(test_case):
            return test_case.type.value if hasattr(test_case.type, 'value') else str(test_case.type)

        objective_results = [r for r in self.results if r.test_case.type == TestType.OBJECTIVE or get_type_str(r.test_case) == "Objective"]
        subjective_results = [r for r in self.results if get_type_str(r.test_case).startswith("Subjective")]
        calculated_results = [r for r in self.results if get_type_str(r.test_case).startswith("Calculated")]

        auto_fixed = sum(1 for r in self.results if r.test_case.auto_fixed)
        needs_review = sum(1 for r in self.results if r.test_case.needs_review)

        duration = None
        if self.completed_at:
            duration = (self.completed_at - self.started_at).total_seconds()

        self.summary = TestRunSummary(
            run_id=self.run_id,
            total_tests=len(self.results),
            passed=passed,
            failed=failed,
            fail_inclusion=fail_inclusion,
            fail_similarity=fail_similarity,
            objective_passed=sum(1 for r in objective_results if r.passed),
            objective_total=len(objective_results),
            subjective_passed=sum(1 for r in subjective_results if r.passed),
            subjective_total=len(subjective_results),
            calculated_passed=sum(1 for r in calculated_results if r.passed),
            calculated_total=len(calculated_results),
            auto_fixed_count=auto_fixed,
            needs_review_count=needs_review,
            started_at=self.started_at,
            completed_at=self.completed_at,
            duration_seconds=duration
        )

    def get_failed_tests(self) -> List[TestResult]:
        """Get all failed test results"""
        return [r for r in self.results if not r.passed]

    def get_passed_tests(self) -> List[TestResult]:
        """Get all passed test results"""
        return [r for r in self.results if r.passed]


class AutoFixSuggestion(BaseModel):
    """Suggestion for auto-fixing a failing test"""

    test_id: int
    fix_type: str = Field(..., description="'prompt' | 'expected' | 'good_answer'")
    original_value: str
    suggested_value: str
    reason: str
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in this fix (0-1)")
    needs_review: bool = False
