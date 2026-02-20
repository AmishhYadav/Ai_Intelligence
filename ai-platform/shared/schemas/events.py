from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
import uuid

def generate_uuid() -> str:
    return str(uuid.uuid4())

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

class BaseEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    event_id: str = Field(default_factory=generate_uuid, description="Unique identifier for the event")
    timestamp: datetime = Field(default_factory=now_utc, description="Event generation timestamp")
    source: str = Field(..., description="Service that generated the event")

class UserEvent(BaseEvent):
    """Event emitted by the API Gateway when a user performs an action."""
    user_id: str
    session_id: str
    action: str
    payload: Dict[str, Any] = Field(default_factory=dict)

class IngestionEvent(BaseEvent):
    """Event emitted when new raw data needs processing."""
    raw_text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    document_type: str = "text"

class EmbeddingJob(BaseEvent):
    """Job definition for the embedding service."""
    document_id: str
    text_content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ReasoningTask(BaseEvent):
    """Task for the reasoning agent to process."""
    user_id: str
    session_id: str
    query: str
    context_keys: List[str] = Field(default_factory=list, description="Keys to fetch context from Redis if any")

class AlertEvent(BaseEvent):
    """Event emitted when an important state is detected."""
    severity: str = Field(..., description="INFO, WARNING, CRITICAL")
    message: str
    context: Dict[str, Any] = Field(default_factory=dict)
