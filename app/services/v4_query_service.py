"""
V4 Query Service - Service wrapper for LangGraph orchestrator

This service wraps the v4 API endpoint logic for use by:
- QA testing infrastructure
- CLI tools
- Other internal services

It provides a clean Python interface without HTTP overhead.
"""

from typing import Dict, Optional, List, Any
from app.orchestration.langgraph_orchestrator import get_orchestrator


class V4QueryService:
    """
    Service wrapper for v4 LangGraph orchestrator

    Provides direct Python interface to the orchestrator without
    going through HTTP/FastAPI layer.
    """

    def __init__(self):
        """Initialize service with orchestrator"""
        self.orchestrator = get_orchestrator()

    def query(
        self,
        query: str,
        session_id: str = "default",
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Execute query through LangGraph orchestrator

        Args:
            query: Natural language query
            session_id: Session ID for multi-turn conversations
            conversation_history: Previous conversation turns

        Returns:
            Dict with:
            - answer: Natural language answer
            - intent: Classified intent
            - provenance: Full provenance trail
            - execution_path: Nodes executed
            - execution_time_ms: Performance metric
            - next_action: "answer" or "gather_parameters"
            - clarification_question: If parameters missing
            - session_id: Session identifier
        """
        return self.orchestrator.query(
            query=query,
            session_id=session_id,
            conversation_history=conversation_history
        )

    def get_answer_only(self, query: str) -> str:
        """
        Convenience method to get just the answer text

        Args:
            query: Natural language query

        Returns:
            Answer string
        """
        response = self.query(query)
        return response.get('answer', 'No answer generated')

    def get_intent(self, query: str) -> str:
        """
        Get classified intent for query

        Args:
            query: Natural language query

        Returns:
            Intent: "objective", "analytical", or "financial"
        """
        response = self.query(query)
        return response.get('intent', 'unknown')

    def health_check(self) -> Dict[str, str]:
        """
        Check health of all adapters

        Returns:
            Dict with status for each component
        """
        status = {
            "orchestrator": "unknown",
            "vector_db": "unknown",
            "knowledge_graph": "unknown",
            "llm": "unknown"
        }

        try:
            # Check orchestrator
            if self.orchestrator:
                status["orchestrator"] = "healthy"

            # Check Vector DB adapter
            try:
                self.orchestrator.vector_db.search_attributes("test", k=1)
                status["vector_db"] = "healthy"
            except:
                status["vector_db"] = "unhealthy"

            # Check KG adapter
            try:
                self.orchestrator.kg.get_all_projects()
                status["knowledge_graph"] = "healthy"
            except:
                status["knowledge_graph"] = "unhealthy"

            # Check LLM adapter
            try:
                self.orchestrator.llm.classify_intent("test query")
                status["llm"] = "healthy"
            except:
                status["llm"] = "unhealthy"

        except Exception as e:
            status["orchestrator"] = f"unhealthy: {str(e)}"

        return status


# Singleton instance
_v4_service_instance = None


def get_v4_service() -> V4QueryService:
    """
    Get or create singleton V4QueryService instance

    Returns:
        V4QueryService singleton
    """
    global _v4_service_instance

    if _v4_service_instance is None:
        _v4_service_instance = V4QueryService()

    return _v4_service_instance
