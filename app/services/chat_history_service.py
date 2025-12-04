"""
Chat History Service: Short-term memory with auto-compacting

Manages conversation history for current session with intelligent compacting:
- Tracks token count for context window management
- Auto-compacts when history exceeds threshold (8000 tokens)
- Keeps first 2 + last 5 turns, summarizes middle turns
- Uses LLM to generate concise summaries
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import google.generativeai as genai


class ChatHistoryService:
    """
    Manages short-term conversation memory with auto-compacting

    Features:
    - Token counting for context window management
    - Auto-compacting when threshold exceeded
    - LLM-powered summarization of old turns
    - Preserve recent context (last 5 turns) and initial context (first 2 turns)
    """

    # Token threshold for auto-compacting (Gemini 2.5 has 32k context, use 8k as threshold)
    TOKEN_THRESHOLD = 8000

    # Keep first N turns (initial context) and last M turns (recent context)
    KEEP_FIRST_TURNS = 2
    KEEP_LAST_TURNS = 5

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Chat History Service

        Args:
            api_key: Gemini API key for summarization (defaults to env var)
        """
        # Get API key for summarization
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

        # Configure Gemini for summarization
        if self.api_key:
            genai.configure(api_key=self.api_key)
            # Use lightweight model for summarization
            self.summarization_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            self.summarization_model = None
            print("⚠️  No API key provided for summarization. Auto-compacting will use simple truncation.")

    def create_session(self) -> Dict:
        """
        Create a new chat session

        Returns:
            New session dict with empty history
        """
        return {
            "session_id": self._generate_session_id(),
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "turns": [],
            "total_tokens": 0,
            "compacted": False,
            "compaction_count": 0
        }

    def add_turn(
        self,
        session: Dict,
        user_message: str,
        assistant_response: str,
        function_calls: Optional[List[Dict]] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Add a new turn to chat history

        Args:
            session: Current session dict
            user_message: User's message
            assistant_response: Assistant's response
            function_calls: Optional list of function calls made
            metadata: Optional metadata for this turn

        Returns:
            Updated session dict
        """
        # Create turn record
        turn = {
            "turn_number": len(session["turns"]) + 1,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user": user_message,
            "assistant": assistant_response,
            "function_calls": function_calls or [],
            "metadata": metadata or {},
            "token_count": self._estimate_token_count(user_message + " " + assistant_response)
        }

        # Add to session
        session["turns"].append(turn)
        session["total_tokens"] += turn["token_count"]
        session["updated_at"] = datetime.utcnow().isoformat() + "Z"

        # Check if auto-compacting is needed
        if session["total_tokens"] > self.TOKEN_THRESHOLD:
            session = self._auto_compact(session)

        return session

    def get_history_for_llm(self, session: Dict, format: str = "list") -> Any:
        """
        Get chat history in format suitable for LLM

        Args:
            session: Session dict
            format: Output format ("list" or "string")

        Returns:
            Chat history in requested format
        """
        if format == "list":
            # Return as list of dicts (role, content)
            history = []
            for turn in session["turns"]:
                history.append({"role": "user", "content": turn["user"]})
                history.append({"role": "assistant", "content": turn["assistant"]})
            return history

        elif format == "string":
            # Return as formatted string
            history_str = ""
            for turn in session["turns"]:
                history_str += f"User: {turn['user']}\n"
                history_str += f"Assistant: {turn['assistant']}\n\n"
            return history_str.strip()

        else:
            raise ValueError(f"Unknown format: {format}")

    def _auto_compact(self, session: Dict) -> Dict:
        """
        Auto-compact chat history when token threshold exceeded

        Strategy:
        - Keep first N turns (initial context)
        - Keep last M turns (recent context)
        - Summarize middle turns using LLM

        Args:
            session: Session dict

        Returns:
            Compacted session dict
        """
        turns = session["turns"]

        # If not enough turns to compact, just return
        if len(turns) <= (self.KEEP_FIRST_TURNS + self.KEEP_LAST_TURNS):
            return session

        print(f"[ChatHistory] Auto-compacting: {len(turns)} turns → keeping first {self.KEEP_FIRST_TURNS} + last {self.KEEP_LAST_TURNS}, summarizing middle")

        # Split turns
        first_turns = turns[:self.KEEP_FIRST_TURNS]
        middle_turns = turns[self.KEEP_FIRST_TURNS:-self.KEEP_LAST_TURNS]
        last_turns = turns[-self.KEEP_LAST_TURNS:]

        # Summarize middle turns
        if self.summarization_model:
            summary_text = self._summarize_turns_with_llm(middle_turns)
        else:
            summary_text = self._summarize_turns_simple(middle_turns)

        # Create summary turn
        summary_turn = {
            "turn_number": self.KEEP_FIRST_TURNS + 1,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user": "[SUMMARIZED CONVERSATION HISTORY]",
            "assistant": summary_text,
            "function_calls": [],
            "metadata": {
                "is_summary": True,
                "summarized_turns": len(middle_turns),
                "turn_range": f"{middle_turns[0]['turn_number']}-{middle_turns[-1]['turn_number']}"
            },
            "token_count": self._estimate_token_count(summary_text)
        }

        # Rebuild turns list
        compacted_turns = first_turns + [summary_turn] + last_turns

        # Recalculate total tokens
        total_tokens = sum(turn["token_count"] for turn in compacted_turns)

        # Update session
        session["turns"] = compacted_turns
        session["total_tokens"] = total_tokens
        session["compacted"] = True
        session["compaction_count"] += 1
        session["last_compaction"] = datetime.utcnow().isoformat() + "Z"

        print(f"[ChatHistory] Compaction complete: {total_tokens} tokens remaining")

        return session

    def _summarize_turns_with_llm(self, turns: List[Dict]) -> str:
        """
        Summarize conversation turns using LLM

        Args:
            turns: List of turns to summarize

        Returns:
            Summary text
        """
        # Build prompt for summarization
        conversation_text = ""
        for turn in turns:
            conversation_text += f"User: {turn['user']}\n"
            conversation_text += f"Assistant: {turn['assistant']}\n\n"

        prompt = f"""Summarize the following conversation exchange concisely, preserving key information, numbers, and decisions:

{conversation_text}

Provide a concise summary (2-4 sentences) that captures:
1. Main topics discussed
2. Key data points or calculations mentioned
3. Important decisions or recommendations made

Summary:"""

        try:
            response = self.summarization_model.generate_content(prompt)
            summary = response.text.strip()
            return summary
        except Exception as e:
            print(f"[ChatHistory] LLM summarization failed: {e}. Falling back to simple summary.")
            return self._summarize_turns_simple(turns)

    def _summarize_turns_simple(self, turns: List[Dict]) -> str:
        """
        Simple summarization without LLM (fallback)

        Args:
            turns: List of turns to summarize

        Returns:
            Simple summary text
        """
        topics = []
        for turn in turns:
            # Extract key topics from user messages
            user_msg = turn["user"].lower()
            if "irr" in user_msg or "return" in user_msg:
                topics.append("IRR calculations")
            if "npv" in user_msg or "value" in user_msg:
                topics.append("NPV analysis")
            if "psf" in user_msg or "price" in user_msg:
                topics.append("pricing metrics")
            if "absorption" in user_msg or "sales" in user_msg:
                topics.append("sales velocity and absorption")
            if "project" in user_msg or "compare" in user_msg:
                topics.append("project comparisons")

        # Remove duplicates
        topics = list(set(topics))

        if topics:
            summary = f"[Previous conversation covered: {', '.join(topics)}. {len(turns)} turns summarized.]"
        else:
            summary = f"[Previous conversation: {len(turns)} turns summarized.]"

        return summary

    def _estimate_token_count(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation)

        Args:
            text: Text to count tokens for

        Returns:
            Estimated token count
        """
        # Rough estimate: 1 token ≈ 4 characters for English text
        # This is a conservative estimate (actual tokenization may vary)
        return len(text) // 4

    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        import uuid
        return f"session_{uuid.uuid4().hex[:16]}"

    def get_session_summary(self, session: Dict) -> Dict:
        """
        Get summary statistics for a session

        Args:
            session: Session dict

        Returns:
            Dict with summary statistics
        """
        return {
            "session_id": session["session_id"],
            "created_at": session["created_at"],
            "updated_at": session["updated_at"],
            "total_turns": len(session["turns"]),
            "total_tokens": session["total_tokens"],
            "compacted": session["compacted"],
            "compaction_count": session.get("compaction_count", 0),
            "within_threshold": session["total_tokens"] <= self.TOKEN_THRESHOLD
        }

    def clear_session(self, session: Dict) -> Dict:
        """
        Clear session history (reset to empty)

        Args:
            session: Session dict to clear

        Returns:
            Cleared session dict
        """
        session["turns"] = []
        session["total_tokens"] = 0
        session["compacted"] = False
        session["compaction_count"] = 0
        session["updated_at"] = datetime.utcnow().isoformat() + "Z"
        return session


# Global singleton instance
_chat_history_service_instance = None

def get_chat_history_service() -> ChatHistoryService:
    """Get or create global chat history service instance"""
    global _chat_history_service_instance
    if _chat_history_service_instance is None:
        _chat_history_service_instance = ChatHistoryService()
    return _chat_history_service_instance
