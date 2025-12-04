"""
Conversation History Service

Manages conversation sessions, context, and memory for multi-turn dialogues.
Provides context-aware responses and maintains conversation state.
"""

import json
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import pickle

from app.models.conversation import (
    ConversationSession,
    ConversationMessage,
    ConversationTurn,
    ConversationMemory,
    QueryContext,
    MessageRole,
    ConversationIntent,
    ConversationContextRequest,
    ConversationContextResponse
)
from app.services.prompt_router import prompt_router
from app.config.defaults import defaults


class ConversationService:
    """
    Service for managing conversation history and context.
    Implements memory management for multi-turn dialogues.
    """

    def __init__(self, storage_path: str = "data/conversations"):
        """
        Initialize conversation service

        Args:
            storage_path: Directory to store conversation sessions
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Active sessions cache
        self.active_sessions: Dict[str, ConversationSession] = {}

        # Intent patterns for classification
        self.intent_patterns = {
            ConversationIntent.VELOCITY: ["velocity", "speed", "absorption", "sales rate", "how fast"],
            ConversationIntent.PRICING: ["price", "psf", "asp", "cost", "revenue", "pricing"],
            ConversationIntent.FINANCIAL: ["irr", "npv", "roi", "payback", "return", "investment"],
            ConversationIntent.DEMAND: ["demand", "buyers", "interest", "bookings", "inquiries"],
            ConversationIntent.MARKET_POS: ["market share", "competition", "position", "ranking", "compare"],
            ConversationIntent.RISK: ["risk", "variance", "volatility", "uncertainty", "deviation"],
            ConversationIntent.EFFICIENCY: ["efficiency", "utilization", "productivity", "optimization"],
            ConversationIntent.COMPARISON: ["compare", "versus", "vs", "difference", "better", "benchmark"]
        }

        # Load parameter mappings from enriched LF layers
        self.parameter_mappings = self._load_parameter_mappings()

    def _load_parameter_mappings(self) -> Dict[str, Dict[str, Any]]:
        """
        Load parameter mappings from the enriched LF layers.
        Maps parameter names to their metadata.
        """
        # This would be loaded from the LF-Layers-Enriched.xlsx
        # For now, creating a sample mapping
        return {
            # Layer 0 parameters
            "project_name": {"layer": 0, "dimension": "Text", "category": "identity"},
            "total_units": {"layer": 0, "dimension": "U", "category": "supply"},
            "project_duration": {"layer": 0, "dimension": "T", "category": "timeline"},
            "total_revenue": {"layer": 0, "dimension": "C", "category": "financial"},

            # Layer 1 parameters
            "psf": {"layer": 1, "dimension": "C/L²", "category": "pricing"},
            "absorption_rate": {"layer": 1, "dimension": "%", "category": "velocity"},
            "sales_velocity": {"layer": 1, "dimension": "U/T", "category": "velocity"},
            "gross_margin": {"layer": 1, "dimension": "%", "category": "profitability"},

            # Add more mappings as needed from the 55 parameters
        }

    def create_session(self, user_id: Optional[str] = None) -> ConversationSession:
        """
        Create a new conversation session

        Args:
            user_id: Optional user identifier

        Returns:
            New conversation session
        """
        session = ConversationSession(user_id=user_id)
        self.active_sessions[session.session_id] = session
        self._save_session(session)
        return session

    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """
        Get an existing session

        Args:
            session_id: Session identifier

        Returns:
            Session if found, None otherwise
        """
        # Check cache first
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]

        # Try loading from disk
        session = self._load_session(session_id)
        if session:
            self.active_sessions[session_id] = session
        return session

    def process_user_message(
        self,
        session_id: str,
        content: str,
        context_override: Optional[Dict[str, Any]] = None
    ) -> Tuple[ConversationMessage, QueryContext]:
        """
        Process a user message and extract context

        Args:
            session_id: Session identifier
            content: User message content
            context_override: Optional context to override extraction

        Returns:
            Tuple of (message, extracted_context)
        """
        session = self.get_session(session_id)
        if not session:
            session = self.create_session()

        # Extract context from message
        query_context = self._extract_query_context(content, session)

        # Override with provided context if any
        if context_override:
            for key, value in context_override.items():
                if hasattr(query_context, key):
                    setattr(query_context, key, value)

        # Create message
        message = ConversationMessage(
            role=MessageRole.USER,
            content=content,
            query_context=query_context
        )

        # Analyze routing
        route_decision = prompt_router.analyze_prompt(content)
        message.routed_to = route_decision.capability
        message.layer = route_decision.layer.value
        message.capability = route_decision.capability
        message.confidence = route_decision.confidence
        message.parameters_extracted = dict(zip(
            route_decision.parameters_needed,
            [None] * len(route_decision.parameters_needed)
        ))

        # Add to session
        session.add_message(message)
        self._save_session(session)

        return message, query_context

    def add_assistant_response(
        self,
        session_id: str,
        content: str,
        result_data: Optional[Dict[str, Any]] = None
    ) -> ConversationMessage:
        """
        Add assistant response to conversation

        Args:
            session_id: Session identifier
            content: Response content
            result_data: Optional computation results

        Returns:
            Assistant message
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Create assistant message
        message = ConversationMessage(
            role=MessageRole.ASSISTANT,
            content=content
        )

        # Add result data if provided
        if result_data:
            message.result_type = result_data.get("type", "single")
            message.result_value = result_data.get("value")
            message.result_unit = result_data.get("unit")
            message.formula_used = result_data.get("formula")
            message.capability = result_data.get("capability")
            message.layer = result_data.get("layer")
            message.sources_referenced = result_data.get("sources", [])

        # Add to session
        session.add_message(message)

        # Create turn if we have a user-assistant pair
        if len(session.messages) >= 2:
            user_msg = session.messages[-2]
            if user_msg.role == MessageRole.USER:
                turn = ConversationTurn(
                    turn_number=len(session.turns) + 1,
                    user_message=user_msg,
                    assistant_message=message
                )
                session.turns.append(turn)

        # Check if summarization needed
        if session.should_summarize():
            self._summarize_conversation(session)

        self._save_session(session)
        return message

    def get_conversation_context(
        self,
        request: ConversationContextRequest
    ) -> ConversationContextResponse:
        """
        Get conversation context for a session

        Args:
            request: Context request parameters

        Returns:
            Conversation context response
        """
        session = self.get_session(request.session_id)
        if not session:
            raise ValueError(f"Session {request.session_id} not found")

        # Get context summary
        context_summary = session.get_context_summary()

        # Get recent messages
        if request.include_full_history:
            recent_messages = session.messages
        else:
            recent_messages = session.messages[-request.max_messages:]

        # Generate suggested queries
        suggested_queries = self._generate_suggested_queries(session)

        return ConversationContextResponse(
            session_id=request.session_id,
            context_summary=context_summary,
            memory=session.memory if request.include_memory else None,
            recent_messages=recent_messages,
            suggested_next_queries=suggested_queries
        )

    def _extract_query_context(
        self,
        content: str,
        session: ConversationSession
    ) -> QueryContext:
        """
        Extract context from user query

        Args:
            content: User message content
            session: Current session

        Returns:
            Extracted query context
        """
        context = QueryContext()
        content_lower = content.lower()

        # Check for project references
        if "project" in content_lower:
            # Look for project name/ID in content
            # Could use NER or pattern matching here
            context.project_id = session.memory.current_project

        # Check for location references
        location_keywords = ["chakan", "pune", "mumbai", "bangalore", "delhi"]
        for location in location_keywords:
            if location in content_lower:
                context.location = location.title()
                if location in ["chakan", "hinjewadi", "kharadi"]:
                    context.city = "Pune"
                break

        # Inherit from session if not found
        if not context.location:
            context.location = session.memory.current_location

        # Classify intent
        context.intent = self._classify_intent(content_lower)

        # Extract metric type
        for param_name, metadata in self.parameter_mappings.items():
            if param_name.replace("_", " ") in content_lower:
                context.metric_type = param_name
                context.layer = metadata["layer"]
                context.parameter_name = param_name
                break

        # Check for time period references
        if "month" in content_lower:
            context.time_period = "monthly"
        elif "year" in content_lower or "annual" in content_lower:
            context.time_period = "yearly"
        elif "quarter" in content_lower:
            context.time_period = "quarterly"

        # Check for comparison
        if any(word in content_lower for word in ["compare", "vs", "versus", "against"]):
            # Extract comparison target
            # This would need more sophisticated NER
            pass

        return context

    def _classify_intent(self, content: str) -> ConversationIntent:
        """
        Classify the intent of a query

        Args:
            content: Query content (lowercase)

        Returns:
            Classified intent
        """
        best_match = ConversationIntent.UNKNOWN
        best_score = 0

        for intent, keywords in self.intent_patterns.items():
            score = sum(1 for keyword in keywords if keyword in content)
            if score > best_score:
                best_score = score
                best_match = intent

        return best_match

    def _generate_suggested_queries(self, session: ConversationSession) -> List[str]:
        """
        Generate suggested follow-up queries based on context

        Args:
            session: Current session

        Returns:
            List of suggested queries
        """
        suggestions = []

        # Based on current project
        if session.memory.current_project:
            project = session.memory.current_project
            if "irr" not in session.memory.calculated_metrics:
                suggestions.append(f"What's the IRR for {project}?")
            if "npv" not in session.memory.calculated_metrics:
                suggestions.append(f"Calculate NPV for {project}")
            suggestions.append(f"How does {project} compare to market average?")

        # Based on current location
        if session.memory.current_location:
            location = session.memory.current_location
            suggestions.append(f"Show me top projects in {location}")
            suggestions.append(f"What's the average PSF in {location}?")

        # Based on recent metrics
        if session.memory.calculated_metrics:
            last_metric = list(session.memory.calculated_metrics.keys())[-1]
            if "irr" in last_metric.lower():
                suggestions.append("What factors affect this IRR?")
                suggestions.append("Run sensitivity analysis on the IRR")
            elif "psf" in last_metric.lower():
                suggestions.append("How does this PSF compare to competition?")

        # General suggestions
        if not suggestions:
            suggestions = [
                "Show me market insights for this location",
                "What are the key risk factors?",
                "Optimize the product mix for better returns"
            ]

        return suggestions[:5]  # Return top 5 suggestions

    def _summarize_conversation(self, session: ConversationSession) -> None:
        """
        Summarize conversation when threshold is reached

        Args:
            session: Session to summarize
        """
        # Extract key points from recent turns
        recent_turns = session.turns[-session.summarization_threshold:]

        key_points = []
        for turn in recent_turns:
            if turn.assistant_message.result_value:
                key_points.append(
                    f"{turn.assistant_message.capability}: {turn.assistant_message.result_value} {turn.assistant_message.result_unit or ''}"
                )

        # Create summary
        summary_parts = []
        if session.memory.current_project:
            summary_parts.append(f"Analyzing {session.memory.current_project}")
        if session.memory.current_location:
            summary_parts.append(f"in {session.memory.current_location}")
        if key_points:
            summary_parts.append(f"Key metrics: {', '.join(key_points[:3])}")

        session.session_summary = ". ".join(summary_parts)

        # Extract key insights
        if session.memory.calculated_metrics:
            for metric, data in list(session.memory.calculated_metrics.items())[-3:]:
                insight = f"{metric}: {data['value']} {data.get('unit', '')}"
                if insight not in session.key_insights:
                    session.key_insights.append(insight)

    def _save_session(self, session: ConversationSession) -> None:
        """Save session to disk"""
        file_path = self.storage_path / f"{session.session_id}.pkl"
        with open(file_path, "wb") as f:
            pickle.dump(session, f)

    def _load_session(self, session_id: str) -> Optional[ConversationSession]:
        """Load session from disk"""
        file_path = self.storage_path / f"{session_id}.pkl"
        if file_path.exists():
            with open(file_path, "rb") as f:
                return pickle.load(f)
        return None

    def clean_old_sessions(self, days: int = 30) -> int:
        """
        Clean sessions older than specified days

        Args:
            days: Number of days to retain sessions

        Returns:
            Number of sessions cleaned
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        cleaned = 0

        for file_path in self.storage_path.glob("*.pkl"):
            try:
                with open(file_path, "rb") as f:
                    session = pickle.load(f)
                if session.updated_at < cutoff_date:
                    file_path.unlink()
                    cleaned += 1
            except:
                # Skip corrupted files
                pass

        return cleaned

    def get_active_sessions(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of active sessions

        Args:
            user_id: Optional filter by user

        Returns:
            List of session summaries
        """
        sessions = []

        for file_path in self.storage_path.glob("*.pkl"):
            try:
                with open(file_path, "rb") as f:
                    session = pickle.load(f)

                if user_id and session.user_id != user_id:
                    continue

                sessions.append({
                    "session_id": session.session_id,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                    "turn_count": len(session.turns),
                    "title": session.session_title or f"Session {session.session_id[:8]}",
                    "summary": session.session_summary
                })
            except:
                pass

        return sorted(sessions, key=lambda x: x["updated_at"], reverse=True)


# Singleton instance
conversation_service = ConversationService()