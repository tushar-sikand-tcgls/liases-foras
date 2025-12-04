"""
Conversation History Models

Data models for managing conversation history and context
to support multi-turn dialogue with memory.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum
import uuid


class MessageRole(str, Enum):
    """Message roles in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationIntent(str, Enum):
    """Intent categories from the enriched LF layers"""
    VELOCITY = "CATEGORY_VELOCITY"
    PRICING = "CATEGORY_PRICING"
    FINANCIAL = "CATEGORY_FINANCIAL"
    DEMAND = "CATEGORY_DEMAND"
    MARKET_POS = "CATEGORY_MARKET_POS"
    RISK = "CATEGORY_RISK"
    EFFICIENCY = "CATEGORY_EFFICIENCY"
    COMPARISON = "CATEGORY_COMPARISON"
    UNKNOWN = "UNKNOWN"


class QueryContext(BaseModel):
    """Context extracted from a query"""
    project_id: Optional[str] = Field(None, description="Project being discussed")
    location: Optional[str] = Field(None, description="Location/region context")
    city: Optional[str] = Field(None, description="City context")
    metric_type: Optional[str] = Field(None, description="Type of metric being queried")
    time_period: Optional[str] = Field(None, description="Time period reference")
    comparison_target: Optional[str] = Field(None, description="What's being compared to")

    # From enriched LF layers
    layer: Optional[int] = Field(None, description="Knowledge graph layer (0-4)")
    parameter_name: Optional[str] = Field(None, description="LF parameter being queried")
    intent: ConversationIntent = Field(ConversationIntent.UNKNOWN, description="Query intent category")


class ConversationMessage(BaseModel):
    """Individual message in a conversation"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Query metadata
    query_context: Optional[QueryContext] = None

    # Routing information
    routed_to: Optional[str] = Field(None, description="Which calculator/service handled this")
    layer: Optional[int] = Field(None, description="Knowledge graph layer")
    capability: Optional[str] = Field(None, description="Capability invoked")
    confidence: Optional[float] = Field(None, description="Routing confidence score")

    # Results metadata
    result_type: Optional[str] = Field(None, description="Type of result (single, table, chart)")
    result_value: Optional[Any] = Field(None, description="Computed result value")
    result_unit: Optional[str] = Field(None, description="Unit of the result")
    formula_used: Optional[str] = Field(None, description="Formula applied")

    # Enrichment data
    vector_search_used: bool = Field(False, description="Whether vector search was used")
    sources_referenced: List[str] = Field(default_factory=list, description="Data sources used")
    parameters_extracted: Dict[str, Any] = Field(default_factory=dict, description="Parameters from query")


class ConversationTurn(BaseModel):
    """A complete turn in conversation (user query + assistant response)"""
    turn_number: int
    user_message: ConversationMessage
    assistant_message: ConversationMessage

    # Metrics
    processing_time_ms: Optional[float] = None
    tokens_used: Optional[int] = None

    # Context carried forward
    context_summary: Optional[str] = Field(None, description="Summary of context at this turn")
    active_entities: List[str] = Field(default_factory=list, description="Entities being discussed")


class ConversationMemory(BaseModel):
    """Memory structure for maintaining conversation context"""

    # Key facts learned
    established_facts: Dict[str, Any] = Field(
        default_factory=dict,
        description="Facts established in conversation (e.g., project_id, location)"
    )

    # Metrics calculated
    calculated_metrics: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Metrics calculated with their values and timestamps"
    )

    # Entities mentioned
    mentioned_projects: List[str] = Field(default_factory=list)
    mentioned_locations: List[str] = Field(default_factory=list)
    mentioned_metrics: List[str] = Field(default_factory=list)

    # User preferences learned
    user_preferences: Dict[str, Any] = Field(
        default_factory=dict,
        description="Learned preferences (e.g., preferred units, comparison style)"
    )

    # Active context
    current_project: Optional[str] = None
    current_location: Optional[str] = None
    current_analysis_type: Optional[str] = None
    comparison_baseline: Optional[Dict[str, Any]] = None


class ConversationSession(BaseModel):
    """Complete conversation session with history"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Conversation flow
    messages: List[ConversationMessage] = Field(default_factory=list)
    turns: List[ConversationTurn] = Field(default_factory=list)

    # Memory and context
    memory: ConversationMemory = Field(default_factory=ConversationMemory)

    # Session metadata
    user_id: Optional[str] = None
    session_title: Optional[str] = Field(None, description="Auto-generated or user-provided title")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")

    # Configuration
    max_context_window: int = Field(10, description="Maximum number of turns to maintain in context")
    summarization_threshold: int = Field(5, description="Summarize after N turns")

    # Summary
    session_summary: Optional[str] = Field(None, description="Summary of the conversation")
    key_insights: List[str] = Field(default_factory=list, description="Key insights from conversation")

    def add_message(self, message: ConversationMessage) -> None:
        """Add a message to the conversation"""
        self.messages.append(message)
        self.updated_at = datetime.utcnow()

        # Update memory based on message
        self._update_memory(message)

    def _update_memory(self, message: ConversationMessage) -> None:
        """Update conversation memory based on new message"""
        if message.query_context:
            ctx = message.query_context

            # Update established facts
            if ctx.project_id:
                self.memory.established_facts["project_id"] = ctx.project_id
                self.memory.current_project = ctx.project_id
                if ctx.project_id not in self.memory.mentioned_projects:
                    self.memory.mentioned_projects.append(ctx.project_id)

            if ctx.location:
                self.memory.established_facts["location"] = ctx.location
                self.memory.current_location = ctx.location
                if ctx.location not in self.memory.mentioned_locations:
                    self.memory.mentioned_locations.append(ctx.location)

            if ctx.metric_type and ctx.metric_type not in self.memory.mentioned_metrics:
                self.memory.mentioned_metrics.append(ctx.metric_type)

        # Store calculated metrics
        if message.result_value is not None and message.capability:
            self.memory.calculated_metrics[message.capability] = {
                "value": message.result_value,
                "unit": message.result_unit,
                "timestamp": message.timestamp,
                "formula": message.formula_used
            }

    def get_context_window(self) -> List[ConversationMessage]:
        """Get the current context window of messages"""
        # Return last N messages based on max_context_window
        window_size = self.max_context_window * 2  # User + Assistant messages
        return self.messages[-window_size:] if len(self.messages) > window_size else self.messages

    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of the current context"""
        return {
            "session_id": self.session_id,
            "turn_count": len(self.turns),
            "current_project": self.memory.current_project,
            "current_location": self.memory.current_location,
            "established_facts": self.memory.established_facts,
            "recent_metrics": dict(list(self.memory.calculated_metrics.items())[-5:]),  # Last 5 metrics
            "mentioned_entities": {
                "projects": self.memory.mentioned_projects[-5:],  # Last 5
                "locations": self.memory.mentioned_locations[-5:],
                "metrics": self.memory.mentioned_metrics[-5:]
            }
        }

    def should_summarize(self) -> bool:
        """Check if conversation should be summarized"""
        return len(self.turns) >= self.summarization_threshold and len(self.turns) % self.summarization_threshold == 0

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "created_at": "2024-11-27T10:00:00Z",
                "messages": [
                    {
                        "role": "user",
                        "content": "What's the IRR for Project Skyline in Chakan?",
                        "query_context": {
                            "project_id": "P_SKYLINE_001",
                            "location": "Chakan",
                            "metric_type": "IRR",
                            "intent": "CATEGORY_FINANCIAL"
                        }
                    },
                    {
                        "role": "assistant",
                        "content": "The IRR for Project Skyline in Chakan is 24.5% per annum.",
                        "result_value": 24.5,
                        "result_unit": "%/year",
                        "capability": "calculate_irr",
                        "layer": 2
                    }
                ],
                "memory": {
                    "current_project": "P_SKYLINE_001",
                    "current_location": "Chakan",
                    "calculated_metrics": {
                        "calculate_irr": {
                            "value": 24.5,
                            "unit": "%/year",
                            "timestamp": "2024-11-27T10:00:30Z"
                        }
                    }
                }
            }
        }


class ConversationContextRequest(BaseModel):
    """Request to get conversation context"""
    session_id: str = Field(..., description="Session ID to get context for")
    include_full_history: bool = Field(False, description="Include full message history")
    include_memory: bool = Field(True, description="Include conversation memory")
    max_messages: int = Field(10, description="Maximum messages to return if not full history")


class ConversationContextResponse(BaseModel):
    """Response with conversation context"""
    session_id: str
    context_summary: Dict[str, Any]
    memory: Optional[ConversationMemory] = None
    recent_messages: List[ConversationMessage] = Field(default_factory=list)
    suggested_next_queries: List[str] = Field(default_factory=list, description="Suggested follow-up queries")