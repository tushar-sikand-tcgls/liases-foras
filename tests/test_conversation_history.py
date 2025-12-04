"""
Test Conversation History and Context Management

Tests the conversation history service for multi-turn dialogue
with context preservation and memory management.
"""

import pytest
from datetime import datetime
import uuid
import os
import shutil
from pathlib import Path

from app.models.conversation import (
    ConversationSession,
    ConversationMessage,
    MessageRole,
    QueryContext,
    ConversationIntent,
    ConversationMemory
)
from app.services.conversation_service import ConversationService


class TestConversationHistory:
    """Test suite for conversation history management"""

    def setup_method(self):
        """Set up test environment"""
        # Create temporary storage directory
        self.test_storage_path = "test_conversations"
        self.service = ConversationService(storage_path=self.test_storage_path)

        # Sample data
        self.sample_queries = [
            "What's the IRR for Project Skyline in Chakan?",
            "How does it compare to the market average?",
            "What's the NPV at 12% discount rate?",
            "Show me the absorption rate",
            "What factors affect this IRR?"
        ]

    def teardown_method(self):
        """Clean up test environment"""
        # Remove test storage directory
        if Path(self.test_storage_path).exists():
            shutil.rmtree(self.test_storage_path)

    def test_create_session(self):
        """Test creating a new conversation session"""
        session = self.service.create_session(user_id="test_user")

        assert session is not None
        assert session.session_id is not None
        assert session.user_id == "test_user"
        assert len(session.messages) == 0
        assert len(session.turns) == 0
        assert session.memory is not None

    def test_process_user_message(self):
        """Test processing user message with context extraction"""
        session = self.service.create_session()

        # Process first message
        message, context = self.service.process_user_message(
            session_id=session.session_id,
            content="What's the IRR for Project Skyline in Chakan?"
        )

        assert message.role == MessageRole.USER
        assert message.content == "What's the IRR for Project Skyline in Chakan?"
        assert message.query_context is not None

        # Check context extraction
        assert context.location == "Chakan"
        assert context.intent == ConversationIntent.FINANCIAL
        assert "irr" in message.capability.lower()

    def test_context_preservation(self):
        """Test that context is preserved across messages"""
        session = self.service.create_session()

        # First message establishes context
        msg1, ctx1 = self.service.process_user_message(
            session_id=session.session_id,
            content="What's the IRR for Project Skyline in Chakan?"
        )

        # Simulate assistant response
        self.service.add_assistant_response(
            session_id=session.session_id,
            content="The IRR is 24.5%",
            result_data={
                "value": 24.5,
                "unit": "%/year",
                "capability": "calculate_irr",
                "layer": 2
            }
        )

        # Second message should inherit context
        msg2, ctx2 = self.service.process_user_message(
            session_id=session.session_id,
            content="What's the NPV?"  # No explicit project/location
        )

        # Reload session to check memory
        session = self.service.get_session(session.session_id)

        # Check context preservation
        assert session.memory.current_location == "Chakan"
        assert "calculate_irr" in session.memory.calculated_metrics
        assert session.memory.calculated_metrics["calculate_irr"]["value"] == 24.5

    def test_conversation_memory_update(self):
        """Test that conversation memory is updated correctly"""
        session = self.service.create_session()

        # Process multiple messages
        locations = ["Chakan", "Hinjewadi", "Kharadi"]
        projects = ["Project A", "Project B", "Project C"]

        for i, (loc, proj) in enumerate(zip(locations, projects)):
            msg, ctx = self.service.process_user_message(
                session_id=session.session_id,
                content=f"Show me data for {proj} in {loc}",
                context_override={"project_id": proj}
            )

        session = self.service.get_session(session.session_id)

        # Check memory updates
        assert len(session.memory.mentioned_locations) == 3
        assert all(loc in session.memory.mentioned_locations for loc in locations)
        assert len(session.memory.mentioned_projects) == 3
        assert session.memory.current_project == "Project C"  # Last mentioned
        assert session.memory.current_location == "Kharadi"  # Last mentioned

    def test_conversation_turns(self):
        """Test conversation turn management"""
        session = self.service.create_session()

        # Create a complete turn
        user_msg, _ = self.service.process_user_message(
            session_id=session.session_id,
            content="Calculate IRR"
        )

        assistant_msg = self.service.add_assistant_response(
            session_id=session.session_id,
            content="The IRR is 25%",
            result_data={"value": 25, "unit": "%"}
        )

        session = self.service.get_session(session.session_id)

        # Check turn creation
        assert len(session.turns) == 1
        assert session.turns[0].turn_number == 1
        assert session.turns[0].user_message.content == "Calculate IRR"
        assert session.turns[0].assistant_message.content == "The IRR is 25%"

    def test_context_window_management(self):
        """Test context window limitation"""
        session = self.service.create_session()
        session.max_context_window = 3  # Small window for testing

        # Add more messages than window size
        for i in range(10):
            self.service.process_user_message(
                session_id=session.session_id,
                content=f"Query {i}"
            )
            self.service.add_assistant_response(
                session_id=session.session_id,
                content=f"Response {i}"
            )

        session = self.service.get_session(session.session_id)
        context_window = session.get_context_window()

        # Check window size (3 turns = 6 messages)
        assert len(context_window) == 6
        assert context_window[-2].content == "Query 9"
        assert context_window[-1].content == "Response 9"

    def test_intent_classification(self):
        """Test intent classification for queries"""
        test_cases = [
            ("What's the sales velocity?", ConversationIntent.VELOCITY),
            ("Calculate the price per sqft", ConversationIntent.PRICING),
            ("What's the IRR and NPV?", ConversationIntent.FINANCIAL),
            ("How's the demand in this area?", ConversationIntent.DEMAND),
            ("Compare with other projects", ConversationIntent.COMPARISON),
            ("What are the risk factors?", ConversationIntent.RISK),
            ("Show efficiency metrics", ConversationIntent.EFFICIENCY)
        ]

        for query, expected_intent in test_cases:
            intent = self.service._classify_intent(query.lower())
            assert intent == expected_intent

    def test_suggested_queries_generation(self):
        """Test generation of suggested follow-up queries"""
        session = self.service.create_session()

        # Set context
        session.memory.current_project = "Project Alpha"
        session.memory.current_location = "Chakan"
        session.memory.calculated_metrics = {
            "calculate_psf": {"value": 4500, "unit": "INR/sqft"}
        }

        suggestions = self.service._generate_suggested_queries(session)

        assert len(suggestions) > 0
        assert any("IRR" in s for s in suggestions)  # Should suggest IRR since not calculated
        assert any("Chakan" in s for s in suggestions)  # Should reference current location

    def test_session_persistence(self):
        """Test saving and loading sessions"""
        # Create and populate session
        session1 = self.service.create_session()
        session_id = session1.session_id

        self.service.process_user_message(
            session_id=session_id,
            content="Test query"
        )

        # Clear cache to force reload
        self.service.active_sessions.clear()

        # Load session
        session2 = self.service.get_session(session_id)

        assert session2 is not None
        assert session2.session_id == session_id
        assert len(session2.messages) == 1
        assert session2.messages[0].content == "Test query"

    def test_session_summarization(self):
        """Test automatic summarization at threshold"""
        session = self.service.create_session()
        session.summarization_threshold = 2  # Low threshold for testing

        # Add messages to trigger summarization
        for i in range(4):
            self.service.process_user_message(
                session_id=session.session_id,
                content=f"Query {i}"
            )
            self.service.add_assistant_response(
                session_id=session.session_id,
                content=f"Response {i}",
                result_data={"value": i, "capability": f"metric_{i}"}
            )

        session = self.service.get_session(session.session_id)

        # Check summarization occurred
        assert session.session_summary is not None
        assert len(session.key_insights) > 0

    def test_context_override(self):
        """Test context override functionality"""
        session = self.service.create_session()

        # Process with override
        msg, ctx = self.service.process_user_message(
            session_id=session.session_id,
            content="Show me the data",
            context_override={
                "project_id": "OVERRIDE_PROJECT",
                "location": "OVERRIDE_LOCATION"
            }
        )

        assert ctx.project_id == "OVERRIDE_PROJECT"
        assert ctx.location == "OVERRIDE_LOCATION"

    def test_multi_turn_dialogue_flow(self):
        """Test complete multi-turn dialogue flow"""
        session = self.service.create_session()

        # Simulate realistic conversation
        dialogue = [
            ("What's the IRR for Project Skyline in Chakan?", "The IRR is 24.5%", {"value": 24.5, "unit": "%/year"}),
            ("How does it compare to market average?", "It's 3% above market average of 21.5%", {"comparison": "+3%"}),
            ("What's the NPV?", "The NPV is ₹520 Cr", {"value": 520, "unit": "Cr"}),
            ("Run sensitivity analysis", "Sensitivity analysis complete", {"scenarios": 3})
        ]

        for user_query, assistant_response, result_data in dialogue:
            # User message
            user_msg, ctx = self.service.process_user_message(
                session_id=session.session_id,
                content=user_query
            )

            # Assistant response
            assistant_msg = self.service.add_assistant_response(
                session_id=session.session_id,
                content=assistant_response,
                result_data=result_data
            )

        session = self.service.get_session(session.session_id)

        # Verify conversation flow
        assert len(session.messages) == 8  # 4 user + 4 assistant
        assert len(session.turns) == 4
        assert session.memory.current_location == "Chakan"
        assert len(session.memory.calculated_metrics) > 0

    def test_session_cleanup(self):
        """Test cleaning old sessions"""
        # Create multiple sessions
        session_ids = []
        for i in range(5):
            session = self.service.create_session()
            session_ids.append(session.session_id)

        # Clean with 0 days retention (should remove all)
        cleaned = self.service.clean_old_sessions(days=0)

        # Verify cleanup
        assert cleaned >= 5

        # Try to load cleaned session
        session = self.service.get_session(session_ids[0])
        assert session is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])