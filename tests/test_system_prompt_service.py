"""
Test System Prompt Service

Tests the multi-dimensional insight engine with grounding mechanisms
and anti-hallucination guards.
"""

import pytest
import json
from datetime import datetime
from typing import Dict, Any

from app.services.system_prompt_service import (
    SystemPromptService,
    InsightLayer,
    InsightType,
    StrategicType,
    DimensionalUnit,
    DimensionalFormula
)
from app.services.insight_generation_service import InsightGenerationService


class TestSystemPromptService:
    """Test suite for system prompt service"""

    def setup_method(self):
        """Set up test environment"""
        self.service = SystemPromptService()
        self.insight_service = InsightGenerationService()

        # Sample Layer 0 data (atomic dimensions)
        self.sample_layer_0 = {
            "project_id": "PROJ001",
            "name": "Phoenix Heights",
            "developer": "Phoenix Developers",
            "location": "Chakan, Pune",
            "total_units": 240,  # U dimension
            "sold_units": 72,
            "unsold_units": 168,
            "total_saleable_area_sqft": 180000,  # L² dimension
            "total_revenue_inr": 1200000000,  # C dimension (12 Cr)
            "total_cost_inr": 850000000,  # C dimension (8.5 Cr)
            "project_duration_months": 36,  # T dimension
            "elapsed_months": 12,
            "launch_date": "2024-01-15",
            "data_version": "Q3_FY25"
        }

    def test_dimensional_formula_validation(self):
        """Test dimensional formula validation"""
        # Valid formulas
        valid_psf = DimensionalFormula(
            name="PSF",
            formula="C ÷ L²",
            dimensional_units="INR/sqft",
            calculation_method="revenue ÷ area"
        )
        assert valid_psf.is_dimensionally_valid() is True

        # Invalid formula (mixing incompatible dimensions)
        invalid = DimensionalFormula(
            name="Invalid",
            formula="C + U",
            dimensional_units="Invalid",
            calculation_method="cashflow + units"
        )
        assert invalid.is_dimensionally_valid() is False

    def test_layer_1_calculation_from_layer_0(self):
        """Test Layer 1 metrics calculation from Layer 0 data"""
        metrics = self.service.calculate_layer_1_metrics(self.sample_layer_0)

        assert metrics["layer"] == 1
        assert "metrics" in metrics
        assert "data_lineage" in metrics

        # Check PSF calculation
        psf = metrics["metrics"].get("price_per_sqft")
        assert psf is not None
        expected_psf = 1200000000 / 180000  # 6666.67
        assert abs(psf["value"] - expected_psf) < 1
        assert psf["unit"] == "INR/sqft"
        assert psf["formula"] == "C ÷ L²"
        assert psf["confidence"] == 95

        # Check Absorption Rate calculation
        ar = metrics["metrics"].get("absorption_rate")
        assert ar is not None
        expected_ar = 72 / (240 * 12)  # 0.025
        assert abs(ar["value"] - expected_ar) < 0.001
        assert ar["unit"] == "1/month"
        assert "2.5%/month" in ar["percentage"]

        # Check dimensional analysis is present
        assert "dimensional_analysis" in psf
        assert "Valid" in psf["dimensional_analysis"]

    def test_layer_2_insight_generation(self):
        """Test Layer 2 insight generation from Layer 1 metrics"""
        # First calculate Layer 1
        layer_1_metrics = self.service.calculate_layer_1_metrics(self.sample_layer_0)

        # Generate Layer 2 insight
        insight = self.service.generate_layer_2_insight(
            layer_1_metrics=layer_1_metrics["metrics"],
            insight_type=InsightType.ABSORPTION_STATUS,
            market_benchmarks={"market_absorption_rate": 0.032}
        )

        assert insight["insight_metadata"]["insight_layer"] == 2
        assert insight["insight_metadata"]["insight_type"] == "absorption_status"

        # Check insight content
        assert "insight_content" in insight
        assert "summary" in insight["insight_content"]
        assert "reasoning" in insight["insight_content"]

        # Check Layer 1 data citation (Layer 2 must reference Layer 1)
        assert "layer_1_data_used" in insight
        assert len(insight["layer_1_data_used"]) > 0
        assert insight["layer_1_data_used"][0]["metric"] == "absorption_rate"

        # Check confidence and limitations
        assert "confidence" in insight
        assert insight["confidence"]["score"] == 85
        assert "limitations" in insight["confidence"]

    def test_grounding_compliance_check(self):
        """Test grounding compliance validation"""
        # Valid response with all required elements
        valid_response = {
            "data_lineage": {
                "layer_0_inputs": {"total_units": 240}
            },
            "calculations": {
                "psf": {
                    "calculation": "1200000000 ÷ 180000"
                }
            },
            "confidence": {
                "score": 95,
                "limitations": "Assumes linear relationships"
            },
            "layer_1_data_used": [
                {"metric": "absorption_rate", "value": 0.025}
            ],
            "insight_content": {
                "dimensional_analysis": "Valid: C/L² = INR/sqft"
            }
        }

        checks = self.service.check_grounding_compliance(valid_response)

        assert checks["has_data_source"] is True
        assert checks["has_calculation"] is True
        assert checks["has_confidence"] is True
        assert checks["has_limitations"] is True
        assert checks["cites_layer_1"] is True
        assert checks["dimensional_valid"] is True
        assert checks["no_hallucination"] is True

    def test_anti_hallucination_filters(self):
        """Test anti-hallucination filtering"""
        # Text with hallucination phrases
        hallucinated_text = (
            "The PSF is probably around 6500. I estimate the absorption rate "
            "might be 2.5%. It seems like the project could be viable."
        )

        filtered = self.service.apply_anti_hallucination_filters(hallucinated_text)

        assert "[DATA REQUIRED]" in filtered
        assert "probably" not in filtered
        assert "estimate" not in filtered
        assert "might be" not in filtered
        assert "seems like" not in filtered
        assert "Note: Some data points were not available" in filtered

    def test_system_prompt_generation(self):
        """Test system prompt generation for different query types"""
        # Calculation prompt
        calc_prompt = self.service.generate_system_prompt(
            query_type="calculation",
            context={"project_id": "PROJ001", "location": "Chakan"}
        )

        assert "Layer 1 metrics from Layer 0" in calc_prompt
        assert "Never invent data points" in calc_prompt
        assert "dimensional consistency" in calc_prompt

        # Insight prompt
        insight_prompt = self.service.generate_system_prompt(
            query_type="insight",
            context={"project_id": "PROJ001"}
        )

        assert "Layer 2 insights" in insight_prompt
        assert "analyzing Layer 1 data" in insight_prompt
        assert "Never cite Layer 0 directly" in insight_prompt

        # Optimization prompt
        opt_prompt = self.service.generate_system_prompt(
            query_type="optimization",
            context={"project_id": "PROJ001"}
        )

        assert "Layer 3" in opt_prompt
        assert "optimization algorithms" in opt_prompt
        assert "SLSQP" in opt_prompt

    def test_traceability_chain(self):
        """Test complete traceability from Layer 2 to Layer 0"""
        # Calculate Layer 1
        layer_1 = self.service.calculate_layer_1_metrics(self.sample_layer_0)

        # Generate Layer 2 insight
        layer_2 = self.service.generate_layer_2_insight(
            layer_1_metrics=layer_1["metrics"],
            insight_type=InsightType.FINANCIAL_VIABILITY
        )

        # Check traceability chain
        assert "data_lineage" in layer_2

        # Layer 2 cites Layer 1
        assert "layer_1_data_used" in layer_2
        l1_metrics = [item["metric"] for item in layer_2["layer_1_data_used"]]
        assert "gross_margin" in l1_metrics

        # Layer 1 cites Layer 0
        assert "data_lineage" in layer_1
        assert "layer_0_inputs" in layer_1["data_lineage"]
        assert layer_1["data_lineage"]["layer_0_inputs"]["total_revenue_inr"] == 1200000000

    def test_confidence_scoring_by_layer(self):
        """Test confidence scores decrease with layer abstraction"""
        # Layer 0: 100% (given data)
        assert self.service.confidence_thresholds[InsightLayer.LAYER_0] == 100

        # Layer 1: 95% (calculation)
        assert self.service.confidence_thresholds[InsightLayer.LAYER_1] == 95

        # Layer 2: 85% (analysis)
        assert self.service.confidence_thresholds[InsightLayer.LAYER_2] == 85

        # Layer 3: 70% (optimization)
        assert self.service.confidence_thresholds[InsightLayer.LAYER_3] == 70

    def test_prompt_templates(self):
        """Test prompt template generation"""
        templates = self.service.generate_prompt_template("metric_calculation")

        assert "prompt" in templates
        assert "instructions" in templates
        assert "output_format" in templates
        assert "formula" in templates["instructions"]

        # Test comparative template
        comp_template = self.service.generate_prompt_template("comparative_insight")
        assert "benchmark" in comp_template["prompt"]
        assert "Layer 1 metrics" in comp_template["instructions"]

    def test_no_data_fabrication_principle(self):
        """Test that system never invents data points"""
        # Empty Layer 0 data
        empty_data = {}

        metrics = self.service.calculate_layer_1_metrics(empty_data)

        # Should not create metrics without data
        assert len(metrics["metrics"]) == 0

        # With partial data
        partial_data = {
            "total_units": 100,
            "total_saleable_area_sqft": 0  # Missing area
        }

        metrics = self.service.calculate_layer_1_metrics(partial_data)

        # Should not calculate PSF without area
        assert "price_per_sqft" not in metrics["metrics"]


class TestInsightGenerationService:
    """Test suite for insight generation service"""

    def setup_method(self):
        """Set up test environment"""
        self.service = InsightGenerationService()

        self.sample_layer_0 = {
            "project_id": "PROJ001",
            "name": "Phoenix Heights",
            "location": "Chakan, Pune",
            "total_units": 240,
            "sold_units": 72,
            "unsold_units": 168,
            "total_saleable_area_sqft": 180000,
            "total_revenue_inr": 1200000000,
            "total_cost_inr": 850000000,
            "elapsed_months": 12,
            "data_version": "Q3_FY25"
        }

    def test_query_analysis(self):
        """Test query analysis for layer determination"""
        # Layer 1 query
        calc_query = "Calculate the PSF for this project"
        analysis = self.service._analyze_query(calc_query)
        assert analysis["layer"] == "layer_1"
        assert analysis["type"] == "calculation"
        assert "price_per_sqft" in analysis["requested_metrics"]

        # Layer 2 query
        insight_query = "How does absorption compare to market average?"
        analysis = self.service._analyze_query(insight_query)
        assert analysis["layer"] == "layer_2"
        assert analysis["type"] == "insight"

        # Layer 3 query
        strategy_query = "Optimize the product mix for maximum IRR"
        analysis = self.service._analyze_query(strategy_query)
        assert analysis["layer"] == "layer_3"
        assert analysis["type"] == "optimization"

    def test_insight_generation_with_grounding(self):
        """Test complete insight generation with grounding"""
        query = "What is the absorption rate and how does it compare to market?"

        insight = self.service.generate_insight(
            query=query,
            layer_0_data=self.sample_layer_0,
            context={"location": "Chakan, Pune"}
        )

        # Check response structure
        assert "response_metadata" in insight
        assert "grounding" in insight
        assert insight["grounding"]["no_estimation"] is True

        # Check grounding compliance
        assert "grounding_compliance" in insight
        compliance = insight["grounding_compliance"]
        assert compliance["checks_passed"] > 0

    def test_contextual_response_generation(self):
        """Test natural language response generation"""
        query = "Calculate gross margin"

        # Detailed response
        detailed = self.service.generate_contextual_response(
            query=query,
            data=self.sample_layer_0,
            response_style="detailed"
        )

        assert "Calculated Metrics" in detailed
        assert "Formula:" in detailed
        assert "Confidence Level:" in detailed

        # Concise response
        concise = self.service.generate_contextual_response(
            query=query,
            data=self.sample_layer_0,
            response_style="concise"
        )

        assert len(concise) < len(detailed)

        # Executive response
        executive = self.service.generate_contextual_response(
            query=query,
            data=self.sample_layer_0,
            response_style="executive"
        )

        assert "Executive Summary" in executive

    def test_risk_analysis_with_thresholds(self):
        """Test risk indicator analysis"""
        # Create Layer 1 metrics with risk indicators
        layer_1_metrics = {
            "metrics": {
                "absorption_rate": {"value": 0.015},  # Below threshold
                "months_of_inventory": {"value": 40},  # High inventory
                "gross_margin": {"value": 0.12}  # Low margin
            }
        }

        benchmarks = {
            "market_absorption_rate": 0.03,
            "market_moi": 20
        }

        risks = self.service._analyze_risk_indicators(
            layer_1_metrics["metrics"],
            benchmarks
        )

        assert risks["overall_risk_level"] == "high"
        assert len(risks["risk_details"]) > 0
        assert any(r["risk"] == "low_absorption" for r in risks["risk_details"])

    def test_layer_3_optimization(self):
        """Test Layer 3 strategic optimization"""
        query = "Optimize product mix for maximum IRR"

        insight = self.service.generate_insight(
            query=query,
            layer_0_data=self.sample_layer_0
        )

        assert insight["response_metadata"]["layer"] == 3
        assert "strategy" in insight
        assert "optimization_details" in insight

        strategy = insight["strategy"]
        assert "base_case" in strategy
        assert "optimized_case" in strategy
        assert "constraints" in strategy
        assert "assumptions" in strategy

    def test_no_hallucination_in_responses(self):
        """Test that responses don't contain hallucinated data"""
        query = "What will be the future absorption rate?"

        insight = self.service.generate_insight(
            query=query,
            layer_0_data=self.sample_layer_0
        )

        # Check that response acknowledges limitations
        if "grounding" in insight:
            assert insight["grounding"].get("no_estimation") is True

        # Should not contain estimation phrases
        response_str = json.dumps(insight)
        assert "will be" not in response_str.lower() or "[DATA REQUIRED]" in response_str

    def test_dimensional_consistency_in_calculations(self):
        """Test dimensional consistency is maintained"""
        query = "Calculate all metrics"

        insight = self.service.generate_insight(
            query=query,
            layer_0_data=self.sample_layer_0
        )

        if "calculations" in insight:
            for metric, data in insight["calculations"].items():
                if "dimensional_analysis" in data:
                    assert "Valid" in data["dimensional_analysis"] or \
                           "dimensionless" in data["dimensional_analysis"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])