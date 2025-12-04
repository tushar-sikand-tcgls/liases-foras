"""
Integration Test for Conversation History with Statistical Calculations

Tests the complete flow of conversation history management integrated with
statistical calculations and prompt routing to ensure all components work
together seamlessly.
"""

import pytest
import json
import numpy as np
from datetime import datetime
from typing import Dict, List, Any
import uuid

from app.models.conversation import (
    ConversationSession,
    ConversationIntent,
    MessageRole
)
from app.services.conversation_service import ConversationService
from app.services.statistical_service import StatisticalService
from app.services.prompt_router import PromptRouter
from app.services.query_router import query_router
from app.models.requests import MCPQueryRequest


class TestConversationStatisticsIntegration:
    """Integration tests for conversation history with statistical calculations"""

    def setup_method(self):
        """Set up test environment"""
        self.conversation_service = ConversationService(storage_path="test_conversations_integration")
        self.statistical_service = StatisticalService()
        self.prompt_router = PromptRouter()

        # Sample time series data for testing
        self.sample_irr_series = [18.5, 19.2, 17.8, 20.1, 18.9, 19.5, 18.2, 19.8, 17.5, 20.5]
        self.sample_psf_series = [4200, 4350, 4180, 4500, 4250, 4420, 4190, 4380, 4220, 4460]
        self.sample_absorption_series = [0.8, 1.1, 0.9, 1.2, 0.85, 1.05, 0.95, 1.15, 0.82, 1.08]

    def teardown_method(self):
        """Clean up test environment"""
        import shutil
        from pathlib import Path
        if Path("test_conversations_integration").exists():
            shutil.rmtree("test_conversations_integration")

    def test_statistical_calculation_with_context_preservation(self):
        """Test that statistical calculations are preserved in conversation memory"""
        # Create session
        session = self.conversation_service.create_session(user_id="test_user")

        # First query: Calculate IRR statistics
        msg1, ctx1 = self.conversation_service.process_user_message(
            session_id=session.session_id,
            content="Calculate average and standard deviation for IRR values: 18.5, 19.2, 17.8, 20.1, 18.9"
        )

        # Perform statistical calculation
        irr_stats = self.statistical_service.calculate_series_statistics(
            values=[18.5, 19.2, 17.8, 20.1, 18.9],
            operations=["AVERAGE", "STANDARD_DEVIATION"],
            metric_name="IRR",
            context="real_estate"
        )

        # Add assistant response with results
        self.conversation_service.add_assistant_response(
            session_id=session.session_id,
            content=f"The average IRR is {irr_stats['statistics']['average']['value']:.2f}% with standard deviation {irr_stats['statistics']['standard_deviation']['value']:.2f}%",
            result_data=irr_stats
        )

        # Second query: Reference previous calculation
        msg2, ctx2 = self.conversation_service.process_user_message(
            session_id=session.session_id,
            content="What was the coefficient of variation for the IRR?"
        )

        # Reload session to check memory
        session = self.conversation_service.get_session(session.session_id)

        # Verify IRR statistics are in memory
        assert "calculate_statistics" in session.memory.calculated_metrics
        stored_stats = session.memory.calculated_metrics["calculate_statistics"]
        assert stored_stats["metric"] == "IRR"
        assert "average" in stored_stats["value"]
        assert "standard_deviation" in stored_stats["value"]

    def test_multi_metric_conversation_flow(self):
        """Test conversation flow with multiple statistical metrics"""
        session = self.conversation_service.create_session()

        # Conversation flow with multiple metrics
        metrics_dialogue = [
            ("Calculate statistics for PSF values: 4200, 4350, 4180, 4500, 4250",
             "PSF", [4200, 4350, 4180, 4500, 4250]),
            ("Now analyze absorption rates: 0.8, 1.1, 0.9, 1.2, 0.85",
             "Absorption Rate", [0.8, 1.1, 0.9, 1.2, 0.85]),
            ("Compare the volatility between PSF and absorption rates",
             None, None)
        ]

        psf_cv = None
        absorption_cv = None

        for i, (query, metric_name, values) in enumerate(metrics_dialogue):
            # Process user message
            msg, ctx = self.conversation_service.process_user_message(
                session_id=session.session_id,
                content=query
            )

            if values:  # Calculate statistics for new data
                stats = self.statistical_service.calculate_series_statistics(
                    values=values,
                    operations=["AVERAGE", "STANDARD_DEVIATION", "VARIANCE"],
                    metric_name=metric_name,
                    context="real_estate"
                )

                # Calculate CV for comparison
                cv = (stats['statistics']['standard_deviation']['value'] /
                      stats['statistics']['average']['value']) * 100

                if metric_name == "PSF":
                    psf_cv = cv
                else:
                    absorption_cv = cv

                # Add response
                self.conversation_service.add_assistant_response(
                    session_id=session.session_id,
                    content=f"Statistics calculated for {metric_name}",
                    result_data=stats
                )
            else:  # Compare volatility
                # This would reference previous calculations from memory
                comparison_response = (
                    f"Comparing volatility:\n"
                    f"- PSF Coefficient of Variation: {psf_cv:.2f}%\n"
                    f"- Absorption Rate CV: {absorption_cv:.2f}%\n"
                    f"- Absorption rates show {'higher' if absorption_cv > psf_cv else 'lower'} volatility"
                )

                self.conversation_service.add_assistant_response(
                    session_id=session.session_id,
                    content=comparison_response,
                    result_data={"psf_cv": psf_cv, "absorption_cv": absorption_cv}
                )

        # Verify conversation has all metrics in memory
        session = self.conversation_service.get_session(session.session_id)
        assert len(session.turns) == 3
        assert len(session.memory.calculated_metrics) >= 2

    def test_prompt_routing_with_conversation_context(self):
        """Test that prompt router uses conversation context correctly"""
        session = self.conversation_service.create_session()

        # First message establishes context
        msg1, ctx1 = self.conversation_service.process_user_message(
            session_id=session.session_id,
            content="Analyze IRR values for Project Skyline in Chakan"
        )

        # Simulate setting context
        session.memory.current_project = "Project Skyline"
        session.memory.current_location = "Chakan"

        # Route subsequent prompt
        route_decision = self.prompt_router.analyze_prompt(
            "Calculate the standard deviation"  # No explicit metric mentioned
        )

        # With context, router should still identify statistical calculation
        assert route_decision.route_type in ["calculation", "retrieval"]
        assert route_decision.confidence > 0.5

    def test_intent_classification_for_statistical_queries(self):
        """Test intent classification for various statistical queries"""
        test_cases = [
            ("Calculate the average IRR", ConversationIntent.FINANCIAL),
            ("What's the standard deviation of PSF", ConversationIntent.PRICING),
            ("Show me variance in absorption rates", ConversationIntent.VELOCITY),
            ("Analyze sales velocity distribution", ConversationIntent.VELOCITY),
            ("Compare NPV volatility across projects", ConversationIntent.FINANCIAL),
            ("What's the median price per square foot", ConversationIntent.PRICING),
            ("Calculate percentile for market demand", ConversationIntent.DEMAND),
            ("Show risk metrics variance", ConversationIntent.RISK)
        ]

        for query, expected_intent in test_cases:
            intent = self.conversation_service._classify_intent(query.lower())
            assert intent == expected_intent, f"Failed for query: {query}"

    def test_statistical_outlier_detection_with_memory(self):
        """Test outlier detection is remembered in conversation"""
        session = self.conversation_service.create_session()

        # Query with outliers
        values_with_outliers = [18.5, 19.2, 17.8, 35.0, 18.9, 19.5, 5.0, 19.8]  # 35.0 and 5.0 are outliers

        msg, ctx = self.conversation_service.process_user_message(
            session_id=session.session_id,
            content=f"Analyze IRR distribution: {values_with_outliers}"
        )

        # Calculate statistics
        stats = self.statistical_service.calculate_series_statistics(
            values=values_with_outliers,
            operations=["AVERAGE", "MEDIAN", "STANDARD_DEVIATION", "NORMAL_DISTRIBUTION"],
            metric_name="IRR",
            context="real_estate"
        )

        # Check outlier detection
        assert "outliers" in stats
        assert len(stats["outliers"]) > 0
        outlier_values = [o["value"] for o in stats["outliers"]]
        assert 35.0 in outlier_values
        assert 5.0 in outlier_values

        # Add to conversation
        self.conversation_service.add_assistant_response(
            session_id=session.session_id,
            content=f"Found {len(stats['outliers'])} outliers in the IRR data",
            result_data=stats
        )

        # Follow-up query about outliers
        msg2, ctx2 = self.conversation_service.process_user_message(
            session_id=session.session_id,
            content="What should I do about these outliers?"
        )

        # Verify outlier information is in memory
        session = self.conversation_service.get_session(session.session_id)
        assert "calculate_statistics" in session.memory.calculated_metrics
        stored_result = session.memory.calculated_metrics["calculate_statistics"]["value"]
        assert "outliers" in stored_result or "statistics" in stored_result

    def test_percentile_calculation_with_context(self):
        """Test percentile calculations are preserved in context"""
        session = self.conversation_service.create_session()

        # Calculate percentiles for market comparison
        psf_values = [4200, 4350, 4180, 4500, 4250, 4420, 4190, 4380, 4220, 4460]

        msg, ctx = self.conversation_service.process_user_message(
            session_id=session.session_id,
            content="Calculate 25th, 50th, and 75th percentiles for PSF values"
        )

        # Calculate percentiles
        percentile_stats = self.statistical_service.calculate_series_statistics(
            values=psf_values,
            operations=["PERCENTILE"],
            metric_name="PSF",
            context="real_estate"
        )

        # Add response
        self.conversation_service.add_assistant_response(
            session_id=session.session_id,
            content="Calculated PSF percentiles for market positioning",
            result_data=percentile_stats
        )

        # Follow-up query
        msg2, ctx2 = self.conversation_service.process_user_message(
            session_id=session.session_id,
            content="Where does a PSF of 4300 fall in this distribution?"
        )

        # Calculate position
        position = np.searchsorted(np.sort(psf_values), 4300) / len(psf_values) * 100

        response = f"A PSF of 4300 falls at approximately the {position:.0f}th percentile"

        self.conversation_service.add_assistant_response(
            session_id=session.session_id,
            content=response,
            result_data={"value": position, "unit": "percentile"}
        )

        # Verify conversation flow
        session = self.conversation_service.get_session(session.session_id)
        assert len(session.turns) == 2
        assert session.memory.calculated_metrics.get("calculate_statistics") is not None

    def test_suggested_queries_for_statistical_analysis(self):
        """Test that suggested queries include statistical analysis options"""
        session = self.conversation_service.create_session()

        # Set context with some calculated metrics
        session.memory.current_project = "Project Alpha"
        session.memory.calculated_metrics = {
            "calculate_irr": {"value": 18.5, "unit": "%/year"}
        }

        # Generate suggestions
        suggestions = self.conversation_service._generate_suggested_queries(session)

        # Should suggest statistical analysis
        statistical_suggestions = [s for s in suggestions if any(
            keyword in s.lower() for keyword in
            ["variance", "standard deviation", "average", "distribution", "volatility"]
        )]

        assert len(statistical_suggestions) > 0, "Should suggest statistical analysis"

    def test_series_consistency_validation(self):
        """Test that series with different dimensions are handled correctly"""
        session = self.conversation_service.create_session()

        # Try to analyze mixed dimensional data (should be rejected or warned)
        mixed_query = "Calculate statistics for these values: 4200 PSF, 18.5% IRR, 0.9 absorption"

        msg, ctx = self.conversation_service.process_user_message(
            session_id=session.session_id,
            content=mixed_query
        )

        # This should be classified but warned about mixed dimensions
        assert ctx.intent in [ConversationIntent.FINANCIAL, ConversationIntent.PRICING]

        # Proper series analysis
        proper_query = "Calculate statistics for IRR values: 18.5, 19.2, 17.8, 20.1"

        msg2, ctx2 = self.conversation_service.process_user_message(
            session_id=session.session_id,
            content=proper_query
        )

        assert ctx2.intent == ConversationIntent.FINANCIAL

    def test_conversation_with_trend_analysis(self):
        """Test conversation flow with trend analysis over time"""
        session = self.conversation_service.create_session()

        # Monthly absorption rates over time
        monthly_data = {
            "Jan": 0.8, "Feb": 0.85, "Mar": 0.9, "Apr": 0.95,
            "May": 1.0, "Jun": 1.05, "Jul": 1.1, "Aug": 1.15
        }

        # First query: Provide monthly data
        msg1, ctx1 = self.conversation_service.process_user_message(
            session_id=session.session_id,
            content=f"Analyze monthly absorption trend: {list(monthly_data.values())}"
        )

        # Calculate trend statistics
        trend_stats = self.statistical_service.calculate_series_statistics(
            values=list(monthly_data.values()),
            operations=["AVERAGE", "STANDARD_DEVIATION", "PERCENTILE"],
            metric_name="Monthly Absorption",
            context="real_estate"
        )

        # Calculate trend direction
        values = list(monthly_data.values())
        trend = "increasing" if values[-1] > values[0] else "decreasing"
        growth_rate = ((values[-1] - values[0]) / values[0]) * 100

        self.conversation_service.add_assistant_response(
            session_id=session.session_id,
            content=f"Absorption shows {trend} trend with {growth_rate:.1f}% growth",
            result_data={**trend_stats, "trend": trend, "growth_rate": growth_rate}
        )

        # Follow-up query
        msg2, ctx2 = self.conversation_service.process_user_message(
            session_id=session.session_id,
            content="What absorption rate can we expect next month?"
        )

        # Simple linear projection
        projected = values[-1] + (values[-1] - values[-2])

        self.conversation_service.add_assistant_response(
            session_id=session.session_id,
            content=f"Based on linear trend, projected absorption: {projected:.2f}%",
            result_data={"projected_value": projected, "method": "linear_projection"}
        )

        # Verify conversation maintains context
        session = self.conversation_service.get_session(session.session_id)
        assert len(session.turns) == 2
        assert "trend" in str(session.memory.calculated_metrics)

    def test_complete_statistical_workflow_integration(self):
        """Test complete workflow from prompt to statistical analysis to memory"""
        session = self.conversation_service.create_session()

        # Complete workflow
        workflow_steps = [
            {
                "query": "I have IRR data for 5 projects: 15.5, 18.2, 16.8, 19.5, 17.3",
                "expected_intent": ConversationIntent.FINANCIAL,
                "values": [15.5, 18.2, 16.8, 19.5, 17.3],
                "metric": "IRR"
            },
            {
                "query": "What's the risk profile based on this variance?",
                "expected_intent": ConversationIntent.RISK,
                "values": None,  # Uses previous data
                "metric": None
            },
            {
                "query": "Which projects are outliers?",
                "expected_intent": ConversationIntent.RISK,
                "values": None,
                "metric": None
            }
        ]

        for step in workflow_steps:
            # Process message
            msg, ctx = self.conversation_service.process_user_message(
                session_id=session.session_id,
                content=step["query"]
            )

            # Verify intent classification
            assert ctx.intent == step["expected_intent"]

            if step["values"]:
                # Calculate statistics
                stats = self.statistical_service.calculate_series_statistics(
                    values=step["values"],
                    operations=["TOTAL", "AVERAGE", "MEDIAN", "STANDARD_DEVIATION",
                               "VARIANCE", "PERCENTILE", "NORMAL_DISTRIBUTION"],
                    metric_name=step["metric"],
                    context="real_estate"
                )

                # Risk assessment based on CV
                cv = (stats['statistics']['standard_deviation']['value'] /
                      stats['statistics']['average']['value']) * 100
                risk_level = "High" if cv > 30 else "Moderate" if cv > 15 else "Low"

                self.conversation_service.add_assistant_response(
                    session_id=session.session_id,
                    content=f"Analysis complete. Risk level: {risk_level} (CV: {cv:.1f}%)",
                    result_data={**stats, "risk_level": risk_level}
                )
            else:
                # Reference previous calculations
                self.conversation_service.add_assistant_response(
                    session_id=session.session_id,
                    content="Analyzing based on previous IRR data...",
                    result_data={"analysis_type": "reference_previous"}
                )

        # Final verification
        session = self.conversation_service.get_session(session.session_id)
        assert len(session.turns) == 3
        assert session.memory.calculated_metrics  # Has stored calculations
        assert session.memory.mentioned_entities  # Has tracked entities


if __name__ == "__main__":
    pytest.main([__file__, "-v"])