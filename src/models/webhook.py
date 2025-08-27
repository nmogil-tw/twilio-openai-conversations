"""
Data models for Twilio webhook payloads and requests.
Defines the structure for incoming webhook data from Twilio Conversations.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class WebhookEventType(str, Enum):
    """Enumeration of supported Twilio webhook event types."""
    ONMESSAGEADD = "onMessageAdd"
    ONPARTICIPANTADD = "onParticipantAdd"
    ONPARTICIPANTREMOVE = "onParticipantRemove"
    ONCONVERSATIONSTATEUPDATE = "onConversationStateUpdate"
    ONCONVERSATIONADD = "onConversationAdd"
    ONCONVERSATIONREMOVE = "onConversationRemove"


class MediaType(str, Enum):
    """Media types for message attachments."""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"


class ConversationState(str, Enum):
    """Conversation states from Twilio."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    CLOSED = "closed"


class TwilioParticipant(BaseModel):
    """
    Model for Twilio Conversation participants.
    """
    sid: str = Field(..., description="Participant SID")
    account_sid: str = Field(..., description="Account SID")
    conversation_sid: str = Field(..., description="Conversation SID")
    service_sid: str = Field(..., description="Service SID")
    identity: Optional[str] = Field(None, description="Participant identity")
    messaging_binding: Optional[Dict[str, Any]] = Field(None, description="Messaging binding details")
    role_sid: Optional[str] = Field(None, description="Role SID")
    date_created: Optional[str] = Field(None, description="Creation date")
    date_updated: Optional[str] = Field(None, description="Last update date")
    
    class Config:
        schema_extra = {
            "example": {
                "sid": "MBxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "account_sid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "conversation_sid": "CHxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "service_sid": "ISxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "identity": "customer_12345",
                "messaging_binding": {
                    "type": "sms",
                    "address": "+1234567890"
                }
            }
        }


class TwilioMessage(BaseModel):
    """
    Model for Twilio Conversation messages.
    """
    sid: str = Field(..., description="Message SID")
    account_sid: str = Field(..., description="Account SID")
    conversation_sid: str = Field(..., description="Conversation SID")
    service_sid: str = Field(..., description="Service SID")
    participant_sid: Optional[str] = Field(None, description="Participant SID")
    identity: Optional[str] = Field(None, description="Message author identity")
    author: Optional[str] = Field(None, description="Message author")
    body: Optional[str] = Field(None, description="Message body")
    media: Optional[List[Dict[str, Any]]] = Field(None, description="Media attachments")
    attributes: Optional[str] = Field(None, description="Custom attributes JSON")
    date_created: Optional[str] = Field(None, description="Creation date")
    date_updated: Optional[str] = Field(None, description="Last update date")
    index: Optional[int] = Field(None, description="Message index")
    
    @validator('body')
    def validate_body(cls, v):
        """Validate message body is not empty if provided."""
        if v is not None and v.strip() == "":
            return None
        return v
    
    def get_text_content(self) -> Optional[str]:
        """
        Extract text content from the message.
        
        Returns:
            Message body text or None if no text content
        """
        return self.body if self.body else None
    
    def has_media(self) -> bool:
        """
        Check if message has media attachments.
        
        Returns:
            True if message has media, False otherwise
        """
        return bool(self.media and len(self.media) > 0)
    
    class Config:
        schema_extra = {
            "example": {
                "sid": "IMxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "account_sid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "conversation_sid": "CHxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "service_sid": "ISxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "participant_sid": "MBxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "author": "customer_12345",
                "body": "Hello, I need help with my order",
                "date_created": "2024-01-15T10:30:00Z"
            }
        }


class TwilioConversation(BaseModel):
    """
    Model for Twilio Conversation details.
    """
    sid: str = Field(..., description="Conversation SID")
    account_sid: str = Field(..., description="Account SID")
    service_sid: str = Field(..., description="Service SID")
    friendly_name: Optional[str] = Field(None, description="Friendly name")
    unique_name: Optional[str] = Field(None, description="Unique name")
    state: Optional[ConversationState] = Field(None, description="Conversation state")
    date_created: Optional[str] = Field(None, description="Creation date")
    date_updated: Optional[str] = Field(None, description="Last update date")
    messaging_service_sid: Optional[str] = Field(None, description="Messaging Service SID")
    attributes: Optional[str] = Field(None, description="Custom attributes JSON")
    
    class Config:
        schema_extra = {
            "example": {
                "sid": "CHxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "account_sid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "service_sid": "ISxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "friendly_name": "Customer Support Chat",
                "state": "active"
            }
        }


class WebhookRequest(BaseModel):
    """
    Main webhook request model from Twilio.
    """
    # Common fields for all webhook types
    EventType: WebhookEventType = Field(..., description="Type of webhook event")
    AccountSid: str = Field(..., description="Twilio Account SID")
    ServiceSid: str = Field(..., description="Conversations Service SID")
    ConversationSid: str = Field(..., description="Conversation SID")
    
    # Message-specific fields (for onMessageAdd events)
    MessageSid: Optional[str] = Field(None, description="Message SID")
    ParticipantSid: Optional[str] = Field(None, description="Participant SID who sent the message")
    Author: Optional[str] = Field(None, description="Message author")
    Body: Optional[str] = Field(None, description="Message body")
    MessageIndex: Optional[int] = Field(None, description="Message index in conversation")
    
    # Participant-specific fields (for participant events)
    Identity: Optional[str] = Field(None, description="Participant identity")
    
    # Conversation state fields
    State: Optional[str] = Field(None, description="Conversation state")
    
    # Additional webhook metadata
    WebhookSid: Optional[str] = Field(None, description="Webhook configuration SID")
    Attributes: Optional[str] = Field(None, description="Custom attributes JSON")
    
    def is_message_event(self) -> bool:
        """
        Check if this is a message-related webhook event.
        
        Returns:
            True if this is a message event, False otherwise
        """
        return self.EventType == WebhookEventType.ONMESSAGEADD
    
    def is_participant_event(self) -> bool:
        """
        Check if this is a participant-related webhook event.
        
        Returns:
            True if this is a participant event, False otherwise
        """
        return self.EventType in [
            WebhookEventType.ONPARTICIPANTADD,
            WebhookEventType.ONPARTICIPANTREMOVE
        ]
    
    def should_process_with_agent(self) -> bool:
        """
        Determine if this webhook should be processed by the AI agent.
        
        Returns:
            True if should be processed by agent, False otherwise
        """
        # TODO: Implement business logic for when to engage the agent
        # For now, process all message events from customers
        return (
            self.is_message_event() and 
            self.Body is not None and 
            self.Body.strip() != "" and
            self.Author != "assistant"  # Don't respond to our own messages
        )
    
    class Config:
        # Allow field names to match Twilio's PascalCase convention
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "EventType": "onMessageAdd",
                "AccountSid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "ServiceSid": "ISxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "ConversationSid": "CHxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "MessageSid": "IMxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "ParticipantSid": "MBxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "Author": "customer_12345",
                "Body": "Hello, I need help with my order #12345",
                "MessageIndex": 1
            }
        }


class WebhookResponse(BaseModel):
    """
    Response model for webhook processing results.
    """
    success: bool = Field(..., description="Whether processing was successful")
    message: str = Field(..., description="Response message")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    agent_responded: bool = Field(default=False, description="Whether agent generated a response")
    error_code: Optional[str] = Field(None, description="Error code if processing failed")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Message processed successfully",
                "processing_time_ms": 1250,
                "agent_responded": True
            }
        }


class WebhookValidationError(BaseModel):
    """
    Model for webhook validation errors.
    """
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    field: Optional[str] = Field(None, description="Field that caused the error")
    
    class Config:
        schema_extra = {
            "example": {
                "error": "validation_error",
                "message": "Missing required field: ConversationSid",
                "field": "ConversationSid"
            }
        }