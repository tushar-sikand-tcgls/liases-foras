"""
Conversation History API Endpoints

Provides REST API endpoints for managing conversation history
and context for multi-turn dialogues.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from app.models.conversation import (
    ConversationSession,
    ConversationMessage,
    ConversationContextRequest,
    ConversationContextResponse,
    MessageRole
)
from app.models.requests import MCPQueryRequest
from app.models.responses import MCPQueryResponse
from app.services.conversation_service import conversation_service
from app.services.query_router import query_router
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/conversation", tags=["conversation"])


# Request/Response models
class CreateSessionRequest(BaseModel):
    """Request to create a new conversation session"""
    user_id: Optional[str] = Field(None, description="Optional user identifier")
    title: Optional[str] = Field(None, description="Optional session title")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    max_context_window: int = Field(10, description="Maximum context window size")


class CreateSessionResponse(BaseModel):
    """Response with new session details"""
    session_id: str
    created_at: datetime
    message: str = "Session created successfully"


class SendMessageRequest(BaseModel):
    """Request to send a message in conversation"""
    session_id: str = Field(..., description="Session identifier")
    content: str = Field(..., description="Message content")
    context_override: Optional[Dict[str, Any]] = Field(None, description="Optional context override")


class SendMessageResponse(BaseModel):
    """Response with assistant's reply"""
    session_id: str
    user_message_id: str
    assistant_message_id: str
    assistant_response: str
    result: Optional[Dict[str, Any]] = None
    suggested_queries: List[str] = Field(default_factory=list)
    context_summary: Dict[str, Any]


class QueryWithContextRequest(BaseModel):
    """Request for context-aware query execution"""
    session_id: str = Field(..., description="Session identifier")
    query: str = Field(..., description="Natural language query")
    use_conversation_context: bool = Field(True, description="Use conversation history for context")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Optional parameter override")


# API Endpoints

@router.post("/create", response_model=CreateSessionResponse)
def create_conversation_session(request: CreateSessionRequest):
    """
    Create a new conversation session

    Creates a new session for tracking conversation history
    and maintaining context across multiple queries.
    """
    try:
        session = conversation_service.create_session(user_id=request.user_id)

        if request.title:
            session.session_title = request.title
        if request.tags:
            session.tags = request.tags
        session.max_context_window = request.max_context_window

        return CreateSessionResponse(
            session_id=session.session_id,
            created_at=session.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/message", response_model=SendMessageResponse)
def send_message(request: SendMessageRequest):
    """
    Send a message and get response with context

    Processes user message, maintains context, and returns
    assistant response with suggested follow-up queries.
    """
    try:
        # Process user message
        user_msg, query_context = conversation_service.process_user_message(
            session_id=request.session_id,
            content=request.content,
            context_override=request.context_override
        )

        # Get session for context
        session = conversation_service.get_session(request.session_id)
        if not session:
            raise ValueError(f"Session {request.session_id} not found")

        # Build context for query execution
        execution_context = {
            "session_id": request.session_id,
            "project_id": session.memory.current_project,
            "location": session.memory.current_location,
            "lfDataVersion": None  # Will use default
        }

        # Route and execute query
        result = None
        assistant_response = "I understand your query"

        if user_msg.capability and user_msg.layer is not None:
            try:
                # Create MCP request from conversation context
                mcp_request = MCPQueryRequest(
                    queryType="calculation",
                    layer=user_msg.layer,
                    capability=user_msg.capability,
                    parameters=user_msg.parameters_extracted,
                    context=execution_context
                )

                # Route to appropriate handler
                result_data, provenance, lineage = query_router.route(mcp_request)

                # Format response
                if result_data:
                    result = result_data
                    if "value" in result_data:
                        value = result_data["value"]
                        unit = result_data.get("unit", "")
                        assistant_response = f"Based on the analysis, the {user_msg.capability.replace('_', ' ')} is {value} {unit}"
                    else:
                        assistant_response = f"I've completed the {user_msg.capability.replace('_', ' ')} analysis. {result_data.get('description', '')}"

            except Exception as e:
                assistant_response = f"I encountered an issue processing your request: {str(e)}"

        # Add assistant response
        assistant_msg = conversation_service.add_assistant_response(
            session_id=request.session_id,
            content=assistant_response,
            result_data=result
        )

        # Get context and suggestions
        context_req = ConversationContextRequest(
            session_id=request.session_id,
            include_full_history=False,
            max_messages=5
        )
        context_resp = conversation_service.get_conversation_context(context_req)

        return SendMessageResponse(
            session_id=request.session_id,
            user_message_id=user_msg.id,
            assistant_message_id=assistant_msg.id,
            assistant_response=assistant_response,
            result=result,
            suggested_queries=context_resp.suggested_next_queries,
            context_summary=context_resp.context_summary
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=MCPQueryResponse)
def query_with_context(request: QueryWithContextRequest):
    """
    Execute a query with conversation context

    Uses conversation history to provide context-aware responses
    and maintains state across queries.
    """
    try:
        # Get session
        session = conversation_service.get_session(request.session_id)
        if not session:
            raise ValueError(f"Session {request.session_id} not found")

        # Process as message
        user_msg, query_context = conversation_service.process_user_message(
            session_id=request.session_id,
            content=request.query
        )

        # Build enriched parameters from context
        enriched_params = request.parameters or {}

        # Add context from conversation memory
        if request.use_conversation_context:
            if session.memory.current_project and "projectId" not in enriched_params:
                enriched_params["projectId"] = session.memory.current_project
            if session.memory.current_location and "location" not in enriched_params:
                enriched_params["location"] = session.memory.current_location

            # Add previously calculated metrics as context
            for metric_name, metric_data in session.memory.calculated_metrics.items():
                if metric_name not in enriched_params:
                    enriched_params[f"previous_{metric_name}"] = metric_data["value"]

        # Create MCP request
        mcp_request = MCPQueryRequest(
            queryId=str(uuid.uuid4()),
            queryType="calculation",
            layer=user_msg.layer or 2,  # Default to layer 2
            capability=user_msg.capability or "calculate_statistics",
            parameters=enriched_params,
            context={
                "session_id": request.session_id,
                "has_context": True,
                "turn_number": len(session.turns) + 1
            }
        )

        # Execute query
        result_data, provenance, lineage = query_router.route(mcp_request)

        # Add to conversation
        assistant_content = f"Query executed: {user_msg.capability}"
        if "value" in result_data:
            assistant_content = f"Result: {result_data['value']} {result_data.get('unit', '')}"

        conversation_service.add_assistant_response(
            session_id=request.session_id,
            content=assistant_content,
            result_data=result_data
        )

        # Build response
        return MCPQueryResponse(
            queryId=mcp_request.queryId,
            status="success",
            layer=mcp_request.layer,
            capability=mcp_request.capability,
            result=result_data,
            provenance=provenance,
            relatedMetrics=[],
            executionTime_ms=0,  # Would need timing
            dataLineage=lineage
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context/{session_id}", response_model=ConversationContextResponse)
def get_conversation_context(
    session_id: str,
    include_full_history: bool = Query(False, description="Include full message history"),
    include_memory: bool = Query(True, description="Include conversation memory"),
    max_messages: int = Query(10, description="Maximum messages to return")
):
    """
    Get conversation context for a session

    Returns the current context, memory, and recent messages
    for a conversation session.
    """
    try:
        request = ConversationContextRequest(
            session_id=session_id,
            include_full_history=include_full_history,
            include_memory=include_memory,
            max_messages=max_messages
        )

        return conversation_service.get_conversation_context(request)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=List[Dict[str, Any]])
def list_sessions(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(10, description="Maximum sessions to return"),
    offset: int = Query(0, description="Offset for pagination")
):
    """
    List conversation sessions

    Returns a list of conversation sessions with summaries.
    """
    try:
        sessions = conversation_service.get_active_sessions(user_id=user_id)

        # Apply pagination
        paginated = sessions[offset:offset + limit]

        return paginated

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
def delete_session(session_id: str):
    """
    Delete a conversation session

    Removes a session and its history from storage.
    """
    try:
        session = conversation_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        # Remove from cache
        if session_id in conversation_service.active_sessions:
            del conversation_service.active_sessions[session_id]

        # Remove from disk
        file_path = conversation_service.storage_path / f"{session_id}.pkl"
        if file_path.exists():
            file_path.unlink()

        return {"message": f"Session {session_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
def cleanup_old_sessions(days: int = Query(30, description="Days to retain sessions")):
    """
    Clean up old conversation sessions

    Removes sessions older than specified number of days.
    """
    try:
        cleaned = conversation_service.clean_old_sessions(days=days)
        return {
            "message": f"Cleaned {cleaned} old sessions",
            "retention_days": days
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))