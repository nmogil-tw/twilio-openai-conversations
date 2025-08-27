"""
Twilio Conversations Service for managing conversations, messages, and participants.
Handles all interactions with the Twilio Conversations API.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from config.settings import settings
from src.models.conversation import ConversationState, ConversationSession
from src.models.webhook import TwilioMessage, TwilioConversation, TwilioParticipant
from src.utils.logging import get_logger

logger = get_logger(__name__)


class TwilioConversationService:
    """
    Service for managing Twilio Conversations API interactions.
    
    Handles:
    - Message sending and receiving
    - Conversation management
    - Participant management  
    - Typing indicators
    - Conversation state management
    """
    
    def __init__(self):
        """Initialize Twilio client with credentials from settings."""
        try:
            self.client = Client(
                settings.twilio.account_sid,
                settings.twilio.auth_token
            )
            self.service_sid = settings.twilio.conversations_service_sid
            logger.info("Twilio Conversations service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {e}")
            raise
    
    async def send_message(
        self,
        conversation_sid: str,
        message: str,
        author: str = "assistant",
        media_url: Optional[str] = None
    ) -> Optional[TwilioMessage]:
        """
        Send a message to a Twilio conversation.
        
        Args:
            conversation_sid: Conversation SID to send message to
            message: Message content to send
            author: Author of the message (default: "assistant")
            media_url: Optional media URL to include
            
        Returns:
            TwilioMessage object if successful, None otherwise
        """
        try:
            logger.info(f"Sending message to conversation {conversation_sid}: {message[:100]}...")
            
            # Prepare message parameters
            message_params = {
                "author": author,
                "body": message
            }
            
            if media_url:
                message_params["media_url"] = media_url
            
            # Send message using Twilio client (run in thread to avoid blocking)
            twilio_message = await asyncio.to_thread(
                self.client.conversations
                .v1.services(self.service_sid)
                .conversations(conversation_sid)
                .messages.create,
                **message_params
            )
            
            logger.info(f"Message sent successfully: {twilio_message.sid}")
            
            # Convert to our model
            return TwilioMessage(
                sid=twilio_message.sid,
                account_sid=twilio_message.account_sid,
                conversation_sid=twilio_message.conversation_sid,
                service_sid=self.service_sid,  # Use the service_sid from our client
                participant_sid=twilio_message.participant_sid,
                author=twilio_message.author,
                body=twilio_message.body,
                date_created=str(twilio_message.date_created) if twilio_message.date_created else None,
                date_updated=str(twilio_message.date_updated) if twilio_message.date_updated else None,
                index=twilio_message.index
            )
            
        except TwilioRestException as e:
            logger.error(f"Twilio API error sending message: {e.msg} (Code: {e.code})")
            return None
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            return None
    
    async def set_typing_indicator(
        self,
        conversation_sid: str,
        participant_sid: str,
        is_typing: bool = True
    ) -> bool:
        """
        Set or clear typing indicator for a participant.
        
        Args:
            conversation_sid: Conversation SID
            participant_sid: Participant SID  
            is_typing: True to show typing, False to clear
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if is_typing:
                logger.debug(f"Setting typing indicator for participant {participant_sid}")
                
                await asyncio.to_thread(
                    self.client.conversations
                    .v1.services(self.service_sid)
                    .conversations(conversation_sid)
                    .participants(participant_sid)
                    .update,
                    typing={"typing": True}
                )
            else:
                logger.debug(f"Clearing typing indicator for participant {participant_sid}")
                
                await asyncio.to_thread(
                    self.client.conversations
                    .v1.services(self.service_sid)
                    .conversations(conversation_sid)
                    .participants(participant_sid)
                    .update,
                    typing={"typing": False}
                )
            
            return True
            
        except TwilioRestException as e:
            logger.warning(f"Failed to set typing indicator: {e.msg} (Code: {e.code})")
            return False
        except Exception as e:
            logger.warning(f"Unexpected error setting typing indicator: {e}")
            return False
    
    async def get_conversation_details(
        self, 
        conversation_sid: str
    ) -> Optional[TwilioConversation]:
        """
        Get detailed information about a conversation.
        
        Args:
            conversation_sid: Conversation SID to fetch
            
        Returns:
            TwilioConversation object if found, None otherwise
        """
        try:
            logger.debug(f"Fetching conversation details: {conversation_sid}")
            
            conversation = await asyncio.to_thread(
                self.client.conversations
                .v1.services(self.service_sid)
                .conversations(conversation_sid)
                .fetch
            )
            
            return TwilioConversation(
                sid=conversation.sid,
                account_sid=conversation.account_sid,
                service_sid=self.service_sid,  # Use the service_sid from our client
                friendly_name=conversation.friendly_name,
                unique_name=conversation.unique_name,
                state=conversation.state,
                date_created=str(conversation.date_created) if conversation.date_created else None,
                date_updated=str(conversation.date_updated) if conversation.date_updated else None,
                messaging_service_sid=conversation.messaging_service_sid,
                attributes=conversation.attributes
            )
            
        except TwilioRestException as e:
            logger.error(f"Failed to fetch conversation: {e.msg} (Code: {e.code})")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching conversation: {e}")
            return None
    
    async def get_conversation_participants(
        self, 
        conversation_sid: str
    ) -> List[TwilioParticipant]:
        """
        Get all participants in a conversation.
        
        Args:
            conversation_sid: Conversation SID
            
        Returns:
            List of TwilioParticipant objects
        """
        try:
            logger.debug(f"Fetching participants for conversation: {conversation_sid}")
            
            participants = await asyncio.to_thread(
                self.client.conversations
                .v1.services(self.service_sid)
                .conversations(conversation_sid)
                .participants.list
            )
            
            result = []
            for participant in participants:
                result.append(TwilioParticipant(
                    sid=participant.sid,
                    account_sid=participant.account_sid,
                    conversation_sid=participant.conversation_sid,
                    service_sid=self.service_sid,  # Use the service_sid from our client
                    identity=participant.identity,
                    messaging_binding=participant.messaging_binding,
                    role_sid=participant.role_sid,
                    date_created=str(participant.date_created) if participant.date_created else None,
                    date_updated=str(participant.date_updated) if participant.date_updated else None
                ))
            
            logger.debug(f"Found {len(result)} participants in conversation")
            return result
            
        except TwilioRestException as e:
            logger.error(f"Failed to fetch participants: {e.msg} (Code: {e.code})")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching participants: {e}")
            return []
    
    async def check_conversation_eligibility(
        self, 
        conversation_sid: str
    ) -> Dict[str, Any]:
        """
        Check if a conversation should be handled by the AI agent.
        
        Args:
            conversation_sid: Conversation SID to check
            
        Returns:
            Dictionary with eligibility information
        """
        try:
            logger.debug(f"Checking conversation eligibility: {conversation_sid}")
            
            # Get conversation details and participants
            conversation = await self.get_conversation_details(conversation_sid)
            participants = await self.get_conversation_participants(conversation_sid)
            
            if not conversation:
                return {
                    "eligible": False,
                    "reason": "conversation_not_found",
                    "participant_count": 0,
                    "has_human_agent": False
                }
            
            # Check if conversation is active
            if conversation.state != "active":
                return {
                    "eligible": False,
                    "reason": "conversation_not_active",
                    "state": conversation.state,
                    "participant_count": len(participants),
                    "has_human_agent": False
                }
            
            # Check participant count and types
            customer_participants = [
                p for p in participants 
                if p.identity and not p.identity.startswith("agent_")
            ]
            
            agent_participants = [
                p for p in participants 
                if p.identity and p.identity.startswith("agent_")
            ]
            
            has_human_agent = any(
                p.identity and p.identity.startswith("human_agent_") 
                for p in participants
            )
            
            # Don't engage if human agent is present
            if has_human_agent:
                return {
                    "eligible": False,
                    "reason": "human_agent_present",
                    "participant_count": len(participants),
                    "customer_count": len(customer_participants),
                    "has_human_agent": True
                }
            
            # Engage if there's exactly one customer and no human agents
            eligible = len(customer_participants) == 1 and not has_human_agent
            
            return {
                "eligible": eligible,
                "reason": "eligible" if eligible else "multiple_customers_or_agents",
                "participant_count": len(participants),
                "customer_count": len(customer_participants),
                "agent_count": len(agent_participants),
                "has_human_agent": has_human_agent,
                "conversation_state": conversation.state
            }
            
        except Exception as e:
            logger.error(f"Error checking conversation eligibility: {e}")
            return {
                "eligible": False,
                "reason": "error_checking_eligibility",
                "error": str(e),
                "participant_count": 0,
                "has_human_agent": False
            }
    
    async def update_conversation_attributes(
        self,
        conversation_sid: str,
        attributes: Dict[str, Any]
    ) -> bool:
        """
        Update conversation attributes with custom metadata.
        
        Args:
            conversation_sid: Conversation SID
            attributes: Dictionary of attributes to set
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import json
            
            logger.debug(f"Updating conversation attributes: {conversation_sid}")
            
            await asyncio.to_thread(
                self.client.conversations
                .v1.services(self.service_sid)
                .conversations(conversation_sid)
                .update,
                attributes=json.dumps(attributes)
            )
            
            return True
            
        except TwilioRestException as e:
            logger.error(f"Failed to update conversation attributes: {e.msg} (Code: {e.code})")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating conversation attributes: {e}")
            return False
    
    async def add_agent_participant(
        self,
        conversation_sid: str,
        agent_identity: str = "ai_assistant"
    ) -> Optional[TwilioParticipant]:
        """
        Add AI agent as a participant to the conversation.
        
        Args:
            conversation_sid: Conversation SID
            agent_identity: Identity for the AI agent participant
            
        Returns:
            TwilioParticipant object if successful, None otherwise
        """
        try:
            logger.info(f"Adding agent participant to conversation: {conversation_sid}")
            
            participant = await asyncio.to_thread(
                self.client.conversations
                .v1.services(self.service_sid)
                .conversations(conversation_sid)
                .participants.create,
                identity=agent_identity
            )
            
            return TwilioParticipant(
                sid=participant.sid,
                account_sid=participant.account_sid,
                conversation_sid=participant.conversation_sid,
                service_sid=self.service_sid,  # Use the service_sid from our client
                identity=participant.identity,
                messaging_binding=participant.messaging_binding,
                role_sid=participant.role_sid,
                date_created=str(participant.date_created) if participant.date_created else None,
                date_updated=str(participant.date_updated) if participant.date_updated else None
            )
            
        except TwilioRestException as e:
            # Participant may already exist - that's ok
            if e.code == 50433:  # Participant already exists
                logger.info(f"Agent participant already exists in conversation: {conversation_sid}")
                return None
            else:
                logger.error(f"Failed to add agent participant: {e.msg} (Code: {e.code})")
                return None
        except Exception as e:
            logger.error(f"Unexpected error adding agent participant: {e}")
            return None
    
    async def validate_webhook_signature(
        self,
        request_body: str,
        signature: str,
        url: str
    ) -> bool:
        """
        Validate Twilio webhook signature for security.
        
        Args:
            request_body: Raw request body
            signature: X-Twilio-Signature header value
            url: Full webhook URL
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            if not settings.twilio.webhook_secret:
                logger.warning("Webhook secret not configured - skipping signature validation")
                return True
            
            from twilio.request_validator import RequestValidator
            
            validator = RequestValidator(settings.twilio.webhook_secret)
            is_valid = validator.validate(url, request_body, signature)
            
            if not is_valid:
                logger.warning("Invalid webhook signature received")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error validating webhook signature: {e}")
            return False