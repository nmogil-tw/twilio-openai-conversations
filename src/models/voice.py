"""
Voice-specific data models for Twilio ConversationRelay integration.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class VoiceSessionStatus(str, Enum):
    """Voice session status enumeration."""
    SETUP = "setup"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class VoiceMessage(BaseModel):
    """Voice message from Twilio ConversationRelay."""
    type: str
    call_sid: Optional[str] = Field(None, alias="callSid")
    voice_prompt: Optional[str] = Field(None, alias="voicePrompt")
    sequence_id: Optional[int] = Field(None, alias="sequenceId")
    session_id: Optional[str] = Field(None, alias="sessionId")
    
    class Config:
        allow_population_by_field_name = True


class VoiceResponse(BaseModel):
    """Response to be sent back to Twilio ConversationRelay."""
    type: str = "text"
    token: str
    last: bool = False
    sequence_id: Optional[int] = Field(None, alias="sequenceId")
    
    class Config:
        allow_population_by_field_name = True


class VoiceSession(BaseModel):
    """Voice conversation session."""
    call_sid: str
    phone_number: Optional[str] = None
    status: VoiceSessionStatus = VoiceSessionStatus.SETUP
    started_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    session_id: Optional[str] = None  # Link to existing conversation session
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StreamingChunk(BaseModel):
    """Individual streaming chunk for voice response."""
    content: str
    is_final: bool = False
    sequence_id: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.now)