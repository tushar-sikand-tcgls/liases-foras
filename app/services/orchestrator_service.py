"""
Orchestrator Service: Main entry point for LLM-driven query processing

Implements the complete 5-step pipeline:
Step 0: System Prompt (sets expectations)
Step 1: Input Enrichment (spell check, context extraction)
Step 2: MCP/Gemini Routing (LLM decides which functions to call)
Step 3: Function Execution (deterministic calculations or GraphRAG)
Step 4: LLM Commentary (analysis, insights, recommendations)
Step 5: Update Chat History (with auto-compacting)
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import all required services
from app.services.gemini_function_calling_service import get_gemini_function_calling_service
from app.services.chat_history_service import get_chat_history_service
from app.config.system_prompts import get_prompt_for_query, detect_query_type
from spellchecker import SpellChecker


class OrchestratorService:
    """
    Main orchestration service for query processing

    Coordinates between:
    - Chat history management (short-term memory)
    - System prompt selection (query-type specific)
    - Gemini function calling (LLM routing + execution)
    - Response synthesis (commentary on results)
    """

    def __init__(self):
        """Initialize orchestrator with all required services"""
        # Get service instances
        self.gemini_service = get_gemini_function_calling_service()
        self.chat_history_service = get_chat_history_service()

        # Initialize spell checker for input enrichment
        self.spell_checker = SpellChecker()

        # Add real estate domain words
        real_estate_words = [
            'psf', 'bhk', 'sqft', 'rera', 'npv', 'irr', 'roi', 'asp',
            'crore', 'lakh', 'cr', 'lacs', 'saleable', 'possession',
            'absorption', 'velocity', 'units', 'unit', 'chakan', 'hinjewadi',
            'wakad', 'pune', 'mumbai', 'micromarket', 'micro', 'market'
        ]
        self.spell_checker.word_frequency.load_words(real_estate_words)

        # Session storage (in-memory for now)
        self._sessions: Dict[str, Dict] = {}

        print("✓ Orchestrator Service initialized")

    def process_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        project_id: Optional[int] = None,
        location: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process a user query through the complete pipeline

        Args:
            query: User query string
            session_id: Optional session ID (creates new if not provided)
            project_id: Optional project ID for context
            location: Optional location for context
            metadata: Optional metadata for this query

        Returns:
            Dict with:
                - response: Final LLM response
                - session_id: Session ID
                - function_calls: List of functions called
                - query_type: Detected query type
                - metadata: Processing metadata
        """
        # Step 0: Get or create session
        session_id, session = self._get_or_create_session(session_id)

        # Step 1: Input Enrichment
        enriched_query, enrichment_metadata = self._enrich_input(
            query=query,
            project_id=project_id,
            location=location
        )

        # Step 2: System Prompt Selection
        query_type = detect_query_type(enriched_query)
        system_prompt = get_prompt_for_query(enriched_query)

        # Step 3: LLM Routing & Function Execution (via Gemini Function Calling)
        chat_history = self.chat_history_service.get_history_for_llm(session, format="list")

        llm_result = self.gemini_service.process_query(
            query=enriched_query,
            chat_history=chat_history,
            system_prompt=system_prompt,
            max_function_calls=5
        )

        # Step 4: Extract Response & Function Results
        final_response = llm_result["response"]
        function_calls = llm_result["function_calls"]
        function_results = llm_result["function_results"]

        # Step 5: Update Chat History (with auto-compacting)
        session = self.chat_history_service.add_turn(
            session=session,
            user_message=query,
            assistant_response=final_response,
            function_calls=function_calls,
            metadata={
                "query_type": query_type,
                "enrichment": enrichment_metadata,
                "project_id": project_id,
                "location": location,
                **(metadata or {})
            }
        )

        # Update session storage
        self._sessions[session_id] = session

        # Build final result
        result = {
            "response": final_response,
            "session_id": session_id,
            "function_calls": function_calls,
            "function_results": function_results,
            "query_type": query_type,
            "metadata": {
                "original_query": query,
                "enriched_query": enriched_query,
                "enrichment": enrichment_metadata,
                "total_turns": len(session["turns"]),
                "session_tokens": session["total_tokens"],
                "session_compacted": session["compacted"],
                "project_id": project_id,
                "location": location,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }

        return result

    def _get_or_create_session(self, session_id: Optional[str]) -> tuple[str, Dict]:
        """
        Get existing session or create new one

        Args:
            session_id: Optional session ID

        Returns:
            Tuple of (session_id, session_dict)
        """
        if session_id and session_id in self._sessions:
            # Return existing session
            return session_id, self._sessions[session_id]
        else:
            # Create new session
            new_session = self.chat_history_service.create_session()
            new_session_id = new_session["session_id"]
            self._sessions[new_session_id] = new_session
            return new_session_id, new_session

    def _enrich_input(
        self,
        query: str,
        project_id: Optional[int],
        location: Optional[str]
    ) -> tuple[str, Dict]:
        """
        Enrich input query with spell check and context

        Args:
            query: Raw user query
            project_id: Optional project ID
            location: Optional location

        Returns:
            Tuple of (enriched_query, metadata)
        """
        enrichment_metadata = {}

        # Step 1.1: Spell check
        corrected_query, corrections = self._spell_check(query)
        if corrections:
            enrichment_metadata["spelling_corrections"] = corrections

        # Step 1.2: Add context if available
        context_parts = []

        if project_id:
            context_parts.append(f"[Context: Analyzing Project ID {project_id}]")
            enrichment_metadata["project_id"] = project_id

        if location:
            context_parts.append(f"[Context: Location is {location}]")
            enrichment_metadata["location"] = location

        # Build enriched query
        if context_parts:
            enriched_query = " ".join(context_parts) + " " + corrected_query
        else:
            enriched_query = corrected_query

        return enriched_query, enrichment_metadata

    def _spell_check(self, text: str) -> tuple[str, List[Dict]]:
        """
        Spell check and correct text

        Args:
            text: Input text

        Returns:
            Tuple of (corrected_text, list_of_corrections)
        """
        words = text.split()
        corrections = []
        corrected_words = []

        for word in words:
            # Skip words with special characters (likely acronyms, numbers, etc.)
            if not word.isalpha():
                corrected_words.append(word)
                continue

            # Check if misspelled
            if word.lower() not in self.spell_checker and len(word) > 2:
                # Get correction
                corrected = self.spell_checker.correction(word.lower())
                if corrected and corrected != word.lower():
                    corrections.append({
                        "original": word,
                        "corrected": corrected
                    })
                    # Preserve original case pattern
                    if word.isupper():
                        corrected_words.append(corrected.upper())
                    elif word[0].isupper():
                        corrected_words.append(corrected.capitalize())
                    else:
                        corrected_words.append(corrected)
                else:
                    corrected_words.append(word)
            else:
                corrected_words.append(word)

        corrected_text = " ".join(corrected_words)
        return corrected_text, corrections

    def get_session_summary(self, session_id: str) -> Optional[Dict]:
        """
        Get summary of a session

        Args:
            session_id: Session ID

        Returns:
            Session summary dict or None if not found
        """
        session = self._sessions.get(session_id)
        if not session:
            return None

        return self.chat_history_service.get_session_summary(session)

    def clear_session(self, session_id: str) -> bool:
        """
        Clear a session's history

        Args:
            session_id: Session ID

        Returns:
            True if successful, False if session not found
        """
        session = self._sessions.get(session_id)
        if not session:
            return False

        session = self.chat_history_service.clear_session(session)
        self._sessions[session_id] = session
        return True

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session entirely

        Args:
            session_id: Session ID

        Returns:
            True if successful, False if session not found
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def list_sessions(self) -> List[Dict]:
        """
        List all active sessions

        Returns:
            List of session summaries
        """
        summaries = []
        for session_id, session in self._sessions.items():
            summary = self.chat_history_service.get_session_summary(session)
            summaries.append(summary)
        return summaries

    def get_available_functions(self) -> Dict:
        """
        Get summary of available functions

        Returns:
            Function registry summary
        """
        return self.gemini_service.get_available_functions_summary()


# Global singleton instance
_orchestrator_instance = None

def get_orchestrator() -> OrchestratorService:
    """Get or create global orchestrator instance"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = OrchestratorService()
    return _orchestrator_instance
