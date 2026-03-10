"""
UltraThink Testing API Endpoints

FastAPI endpoints for auto-healing testing system
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.testing.test_service import AutoHealingTestService

# Create router
router = APIRouter(prefix="/api/testing", tags=["UltraThink Testing"])

# Global service instance (cached)
_service_cache: Dict[str, AutoHealingTestService] = {}


def get_service(excel_path: str) -> AutoHealingTestService:
    """Get or create test service for given Excel file"""
    if excel_path not in _service_cache:
        _service_cache[excel_path] = AutoHealingTestService(excel_path)
    return _service_cache[excel_path]


# Request/Response models
class RunTestRequest(BaseModel):
    """Request to run test cycle"""
    excel_path: str = "/Users/tusharsikand/Documents/Projects/liases-foras/change-request/BDD-test-cases/BDD_Test_Cases.xlsx"
    run_id: str = "initial"
    auto_heal: bool = True


class TestSummaryResponse(BaseModel):
    """Test run summary"""
    run_id: str
    total_tests: int
    passed: int
    failed: int
    pass_rate: float
    fail_inclusion: int
    fail_similarity: int
    auto_fixed_count: int
    needs_review_count: int
    duration_seconds: Optional[float]
    started_at: datetime
    completed_at: Optional[datetime]


class TestResultResponse(BaseModel):
    """Individual test result"""
    test_id: int
    type: str
    prompt: str
    status: str
    model_answer: str
    similarity_score: float
    expected_answer: str
    auto_fixed: bool
    needs_review: bool


# Endpoints

@router.post("/run", response_model=TestSummaryResponse)
async def run_tests(request: RunTestRequest, background_tasks: BackgroundTasks):
    """
    Run complete test cycle

    1. Load test cases from Excel
    2. Execute all tests
    3. Validate results
    4. (Optional) Auto-heal failures
    5. Save results back to Excel

    Returns summary of test run
    """
    try:
        service = get_service(request.excel_path)

        # Load test cases if not already loaded
        if not service.test_cases:
            service.load_test_cases()

        # Run test cycle
        test_run = service.run_test_cycle(
            run_id=request.run_id,
            auto_heal=request.auto_heal
        )

        # Return summary
        return TestSummaryResponse(
            run_id=test_run.run_id,
            total_tests=test_run.summary.total_tests,
            passed=test_run.summary.passed,
            failed=test_run.summary.failed,
            pass_rate=test_run.summary.pass_rate,
            fail_inclusion=test_run.summary.fail_inclusion,
            fail_similarity=test_run.summary.fail_similarity,
            auto_fixed_count=test_run.summary.auto_fixed_count,
            needs_review_count=test_run.summary.needs_review_count,
            duration_seconds=test_run.summary.duration_seconds,
            started_at=test_run.summary.started_at,
            completed_at=test_run.summary.completed_at
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regression")
async def run_regression(
    excel_path: str,
    run_id: str = "regression_1",
    previous_run_id: str = "initial"
):
    """
    Run regression test after auto-healing

    Compares results to previous run and shows improvements/regressions
    """
    try:
        service = get_service(excel_path)

        # Run regression
        regression_run = service.run_regression(
            run_id=run_id,
            previous_run_id=previous_run_id
        )

        return {
            "run_id": regression_run.run_id,
            "summary": TestSummaryResponse(
                run_id=regression_run.run_id,
                total_tests=regression_run.summary.total_tests,
                passed=regression_run.summary.passed,
                failed=regression_run.summary.failed,
                pass_rate=regression_run.summary.pass_rate,
                fail_inclusion=regression_run.summary.fail_inclusion,
                fail_similarity=regression_run.summary.fail_similarity,
                auto_fixed_count=regression_run.summary.auto_fixed_count,
                needs_review_count=regression_run.summary.needs_review_count,
                duration_seconds=regression_run.summary.duration_seconds,
                started_at=regression_run.summary.started_at,
                completed_at=regression_run.summary.completed_at
            ),
            "previous_run_id": regression_run.previous_run_id,
            "improved_tests": regression_run.improved_tests,
            "regressed_tests": regression_run.regressed_tests
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/{run_id}")
async def get_report(run_id: str, excel_path: str):
    """Get text report for a test run"""
    try:
        service = get_service(excel_path)

        if run_id not in service.runs:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

        report = service.get_summary_report(run_id)

        return {
            "run_id": run_id,
            "report": report
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/{run_id}", response_model=List[TestResultResponse])
async def get_results(run_id: str, excel_path: str, status_filter: Optional[str] = None):
    """
    Get detailed test results for a run

    Optional status_filter: "PASS", "FAIL", "FAIL_INCLUSION", "FAIL_SIMILARITY"
    """
    try:
        service = get_service(excel_path)

        if run_id not in service.runs:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

        test_run = service.runs[run_id]
        results = test_run.results

        # Apply filter if specified
        if status_filter:
            results = [r for r in results if r.status.value == status_filter]

        # Convert to response format
        response_data = []
        for result in results:
            response_data.append(TestResultResponse(
                test_id=result.test_case.test_id,
                type=result.test_case.type.value,
                prompt=result.test_case.prompt,
                status=result.status.value,
                model_answer=result.model_answer,
                similarity_score=result.validation.similarity_score,
                expected_answer=result.test_case.expected_answer_include,
                auto_fixed=result.test_case.auto_fixed,
                needs_review=result.test_case.needs_review
            ))

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "UltraThink Auto-Healing Testing",
        "components": {
            "test_service": "ready",
            "validator": "ready",
            "auto_healer": "ready",
            "orchestrator": "ready"
        }
    }
