"""
Conversation State Manager - Redis-based Session Memory

Provides short-term conversation memory for multi-turn dialogues.
Tracks:
- Query history
- Previous responses
- Pending follow-up questions
- Session context

Enables:
- Yes/No follow-up handling
- Context-aware query processing
- Session continuity
"""

import json
import redis
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import os


@dataclass
class ConversationTurn:
    """Single conversation turn"""
    query: str
    response: str
    intent: str
    timestamp: str
    follow_up_question: Optional[str] = None
    follow_up_context: Optional[Dict] = None  # Context needed to answer follow-up


@dataclass
class SessionState:
    """Complete session state"""
    session_id: str
    turns: List[ConversationTurn]
    created_at: str
    last_activity: str
    pending_follow_up: Optional[Dict] = None  # Current pending follow-up


class ConversationStateManager:
    """
    Manages conversation state using Redis cache

    Features:
    - Session-based conversation history
    - Follow-up question tracking
    - Automatic session expiry (configurable TTL)
    - Yes/No intent detection for follow-ups
    """

    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        session_ttl_hours: int = 24
    ):
        """
        Initialize conversation state manager

        Args:
            redis_host: Redis server host
            redis_port: Redis server port
            redis_db: Redis database number
            session_ttl_hours: Session expiry time in hours
        """
        # Use environment variables if available
        self.redis_host = os.getenv("REDIS_HOST", redis_host)
        self.redis_port = int(os.getenv("REDIS_PORT", redis_port))
        self.redis_db = int(os.getenv("REDIS_DB", redis_db))
        self.session_ttl = session_ttl_hours * 3600  # Convert to seconds

        # Initialize Redis connection
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            print(f"✓ Redis connected: {self.redis_host}:{self.redis_port}")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            print(f"⚠ Redis connection failed: {e}")
            print("⚠ Falling back to in-memory state (not persistent)")
            self.redis_client = None
            self._memory_store = {}  # In-memory fallback

    def _get_session_key(self, session_id: str) -> str:
        """Generate Redis key for session"""
        return f"conversation:session:{session_id}"

    def get_session(self, session_id: str) -> Optional[SessionState]:
        """
        Retrieve session state

        Args:
            session_id: Session identifier

        Returns:
            SessionState if exists, None otherwise
        """
        key = self._get_session_key(session_id)

        if self.redis_client:
            data = self.redis_client.get(key)
            if data:
                session_dict = json.loads(data)
                # Reconstruct SessionState from dict
                session_dict['turns'] = [
                    ConversationTurn(**turn) for turn in session_dict['turns']
                ]
                return SessionState(**session_dict)
        else:
            # In-memory fallback
            return self._memory_store.get(session_id)

        return None

    def create_session(self, session_id: str) -> SessionState:
        """
        Create new session

        Args:
            session_id: Session identifier

        Returns:
            New SessionState
        """
        now = datetime.utcnow().isoformat() + 'Z'
        session = SessionState(
            session_id=session_id,
            turns=[],
            created_at=now,
            last_activity=now,
            pending_follow_up=None
        )

        self._save_session(session)
        return session

    def _save_session(self, session: SessionState):
        """Save session to Redis"""
        key = self._get_session_key(session.session_id)

        # Convert to dict for JSON serialization
        session_dict = asdict(session)

        if self.redis_client:
            self.redis_client.setex(
                key,
                self.session_ttl,
                json.dumps(session_dict)
            )
        else:
            # In-memory fallback
            self._memory_store[session.session_id] = session

    def add_turn(
        self,
        session_id: str,
        query: str,
        response: str,
        intent: str,
        follow_up_question: Optional[str] = None,
        follow_up_context: Optional[Dict] = None
    ) -> SessionState:
        """
        Add conversation turn to session

        Args:
            session_id: Session identifier
            query: User query
            response: System response
            intent: Classified intent
            follow_up_question: Optional follow-up question offered
            follow_up_context: Context needed to answer follow-up

        Returns:
            Updated SessionState
        """
        session = self.get_session(session_id)
        if not session:
            session = self.create_session(session_id)

        # Create turn
        turn = ConversationTurn(
            query=query,
            response=response,
            intent=intent,
            timestamp=datetime.utcnow().isoformat() + 'Z',
            follow_up_question=follow_up_question,
            follow_up_context=follow_up_context
        )

        session.turns.append(turn)
        session.last_activity = turn.timestamp

        # Update pending follow-up
        if follow_up_question:
            session.pending_follow_up = {
                'question': follow_up_question,
                'context': follow_up_context,
                'turn_index': len(session.turns) - 1
            }
        else:
            session.pending_follow_up = None

        self._save_session(session)
        return session

    def get_conversation_history(
        self,
        session_id: str,
        max_turns: int = 5
    ) -> List[Dict]:
        """
        Get recent conversation history for LLM context

        Args:
            session_id: Session identifier
            max_turns: Maximum number of recent turns to return

        Returns:
            List of conversation turns as dicts
        """
        session = self.get_session(session_id)
        if not session or not session.turns:
            return []

        # Get last N turns
        recent_turns = session.turns[-max_turns:]

        return [
            {
                'query': turn.query,
                'response': turn.response,
                'intent': turn.intent,
                'timestamp': turn.timestamp
            }
            for turn in recent_turns
        ]

    def get_pending_follow_up(self, session_id: str) -> Optional[Dict]:
        """
        Get pending follow-up question if any

        Args:
            session_id: Session identifier

        Returns:
            Dict with follow-up question and context, or None
        """
        session = self.get_session(session_id)
        if session:
            return session.pending_follow_up
        return None

    def clear_pending_follow_up(self, session_id: str):
        """Clear pending follow-up after it's been answered"""
        session = self.get_session(session_id)
        if session:
            session.pending_follow_up = None
            self._save_session(session)

    def is_yes_no_response(self, query: str) -> Optional[bool]:
        """
        Detect if query is a yes/no response

        Args:
            query: User query

        Returns:
            True if yes, False if no, None if neither
        """
        query_lower = query.lower().strip()

        # Yes variations
        yes_patterns = [
            'yes', 'yeah', 'yep', 'sure', 'ok', 'okay', 'of course',
            'definitely', 'absolutely', 'please', 'go ahead', 'proceed',
            'affirmative', 'correct', 'right', 'indeed'
        ]

        # No variations
        no_patterns = [
            'no', 'nope', 'nah', 'not', 'never', 'negative',
            'don\'t', 'dont', 'skip', 'cancel', 'stop'
        ]

        # Check for yes
        for pattern in yes_patterns:
            if pattern in query_lower:
                return True

        # Check for no
        for pattern in no_patterns:
            if pattern in query_lower:
                return False

        return None

    def delete_session(self, session_id: str):
        """Delete session (for cleanup or user logout)"""
        key = self._get_session_key(session_id)

        if self.redis_client:
            self.redis_client.delete(key)
        else:
            self._memory_store.pop(session_id, None)

    def get_session_stats(self, session_id: str) -> Optional[Dict]:
        """Get session statistics"""
        session = self.get_session(session_id)
        if not session:
            return None

        return {
            'session_id': session.session_id,
            'total_turns': len(session.turns),
            'created_at': session.created_at,
            'last_activity': session.last_activity,
            'has_pending_follow_up': session.pending_follow_up is not None,
            'intents': [turn.intent for turn in session.turns]
        }


# Singleton instance
_state_manager = None


def get_conversation_state_manager() -> ConversationStateManager:
    """Get singleton conversation state manager instance"""
    global _state_manager
    if _state_manager is None:
        _state_manager = ConversationStateManager()
    return _state_manager
