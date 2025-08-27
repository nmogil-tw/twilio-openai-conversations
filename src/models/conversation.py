"""
Data models for conversation management and session tracking.
Defines the structure for conversation data, messages, and session state.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, DateTime, Text, JSON, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


class ConversationState(str, Enum):
    """Enumeration of possible conversation states."""
    ACTIVE = "active"
    WAITING_FOR_AGENT = "waiting_for_agent"
    WAITING_FOR_HUMAN = "waiting_for_human"
    CLOSED = "closed"
    TIMEOUT = "timeout"


class MessageRole(str, Enum):
    """Enumeration of message roles in a conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ParticipantType(str, Enum):
    """Types of participants in a conversation."""
    CUSTOMER = "customer"
    AGENT = "agent"
    HUMAN_AGENT = "human_agent"


class Message(BaseModel):
    """
    Pydantic model for individual messages in a conversation.
    """
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole
    content: str = Field(..., min_length=1, max_length=4000)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    author: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('content')
    def validate_content(cls, v):
        """Validate message content is not empty."""
        if not v or v.strip() == "":
            raise ValueError("Message content cannot be empty")
        return v.strip()
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class ConversationContext(BaseModel):
    """
    Contextual information about a conversation.
    """
    customer_info: Optional[Dict[str, Any]] = Field(default_factory=dict)
    order_history: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tags: Optional[List[str]] = Field(default_factory=list)
    priority: Optional[str] = "normal"  # low, normal, high, urgent
    
    class Config:
        schema_extra = {
            "example": {
                "customer_info": {
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "phone": "+1234567890"
                },
                "order_history": [
                    {"order_id": "12345", "status": "shipped", "total": 99.99}
                ],
                "preferences": {
                    "communication_channel": "sms",
                    "language": "en"
                },
                "tags": ["vip", "returning_customer"],
                "priority": "normal"
            }
        }


class ConversationSession(BaseModel):
    """
    Pydantic model for conversation sessions.
    """
    session_id: str = Field(..., min_length=1)
    conversation_sid: str = Field(..., min_length=1)
    service_sid: str = Field(..., min_length=1)
    participant_sid: Optional[str] = None
    state: ConversationState = ConversationState.ACTIVE
    messages: List[Message] = Field(default_factory=list)
    context: ConversationContext = Field(default_factory=ConversationContext)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('messages')
    def validate_message_history(cls, v):
        """Validate message history doesn't exceed limits."""
        # TODO: Implement max message history validation
        return v
    
    def add_message(self, message: Message) -> None:
        """
        Add a new message to the conversation.
        
        Args:
            message: Message to add to the conversation
        """
        self.messages.append(message)
        self.last_activity_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """
        Get the most recent messages from the conversation.
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List of recent messages
        """
        return self.messages[-limit:] if self.messages else []
    
    def get_context_summary(self) -> str:
        """
        Generate a summary of the conversation context.
        
        Returns:
            String summary of the conversation context
        """
        # TODO: Implement intelligent context summarization
        summary_parts = []
        
        if self.context.customer_info:
            summary_parts.append(f"Customer: {self.context.customer_info.get('name', 'Unknown')}")
        
        if self.context.order_history:
            summary_parts.append(f"Recent orders: {len(self.context.order_history)}")
        
        if self.context.tags:
            summary_parts.append(f"Tags: {', '.join(self.context.tags)}")
        
        return " | ".join(summary_parts) if summary_parts else "No context available"
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


# SQLAlchemy models for database persistence

class ConversationSessionDB(Base):
    """
    SQLAlchemy model for persisting conversation sessions.
    """
    __tablename__ = "conversation_sessions"
    
    session_id = Column(String(255), primary_key=True)
    conversation_sid = Column(String(255), nullable=False, index=True)
    service_sid = Column(String(255), nullable=False)
    participant_sid = Column(String(255), nullable=True)
    state = Column(String(50), nullable=False, default="active")
    context = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    last_activity_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class MessageDB(Base):
    """
    SQLAlchemy model for persisting individual messages.
    """
    __tablename__ = "messages"
    
    id = Column(String(255), primary_key=True)
    session_id = Column(String(255), nullable=False, index=True)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String(255), nullable=True)
    metadata = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class AgentResponse(BaseModel):
    """
    Model for AI agent responses.
    """
    content: str = Field(..., min_length=1)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    tools_used: Optional[List[str]] = Field(default_factory=list)
    processing_time_ms: Optional[int] = Field(default=None, ge=0)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "content": "I'd be happy to help you with your order status!",
                "confidence": 0.95,
                "tools_used": ["lookup_order_status"],
                "processing_time_ms": 1250,
                "metadata": {
                    "model_used": "gpt-4o-mini",
                    "tokens_used": 45
                }
            }
        }