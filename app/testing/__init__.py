"""
Auto-Healing Testing System

A comprehensive BDD testing framework that combines:
- QA role: Behavioral and functional testing
- Developer role: Auto-fixing and auto-correction
"""

from app.testing.test_models import BDDTestCase, TestResult, TestRun
from app.testing.test_service import AutoHealingTestService

__all__ = [
    'BDDTestCase',
    'TestResult',
    'TestRun',
    'AutoHealingTestService',
]
