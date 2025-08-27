"""
Webhook Handler for processing Twilio Conversations webhooks.
Handles incoming webhook events, validates signatures, and coordinates responses.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from config.settings import settings
from src.models.webhook import WebhookRequest, WebhookResponse, WebhookValidationError
from src.models.conversation import MessageRole
from src.services.agent_service import CustomerServiceAgent
from src.services.twilio_service import TwilioConversationService
from src.services.session_service import SessionService
from src.utils.logging import get_logger
from src.utils.security import validate_webhook_signature

logger = get_logger(__name__)

# Create FastAPI router
router = APIRouter()

# Initialize services (TODO: Move to dependency injection)
agent_service = CustomerServiceAgent()
twilio_service = TwilioConversationService()
session_service = SessionService()


@router.post("/message-added", response_model=WebhookResponse)
async def handle_message_added(
    request: Request,
    x_twilio_signature: str = Header(None, alias="X-Twilio-Signature")
):
    """
    Handle incoming message webhooks from Twilio Conversations.
    
    Processing Flow:
    1. Validate webhook signature for security
    2. Parse and validate webhook payload
    3. Check if conversation should be handled by AI
    4. Set typing indicator while processing
    5. Generate AI response using agent
    6. Send response via Twilio API
    7. Clear typing indicator
    8. Return processing results
    """
    start_time = datetime.now()
    processing_context = {
        "webhook_type": "message_added",
        "timestamp": start_time.isoformat(),
        "request_id": getattr(request.state, "request_id", "unknown")
    }
    
    try:
        # Get raw request body for signature validation
        raw_body = await request.body()
        form_data = await request.form()
        
        logger.info("Processing message-added webhook", extra=processing_context)
        
        # Validate webhook signature
        if settings.twilio.webhook_secret and x_twilio_signature:
            url = str(request.url)
            is_valid_signature = await twilio_service.validate_webhook_signature(
                raw_body.decode(), x_twilio_signature, url
            )
            if not is_valid_signature:
                logger.warning("Invalid webhook signature", extra=processing_context)
                raise HTTPException(status_code=403, detail="Invalid webhook signature")
        
        # Parse webhook data
        try:
            webhook_data = WebhookRequest(**dict(form_data))
            processing_context.update({
                "conversation_sid": webhook_data.ConversationSid,
                "message_sid": webhook_data.MessageSid,
                "author": webhook_data.Author
            })
        except ValidationError as e:
            logger.error(f"Invalid webhook payload: {e}", extra=processing_context)
            return WebhookResponse(
                success=False,
                message="Invalid webhook payload",
                error_code="validation_error"
            )
        
        # Check if we should process this message
        if not webhook_data.should_process_with_agent():
            logger.info("Webhook not eligible for agent processing", extra=processing_context)
            return WebhookResponse(
                success=True,
                message="Webhook received but not processed by agent",
                agent_responded=False
            )
        
        # Check conversation eligibility
        eligibility = await twilio_service.check_conversation_eligibility(
            webhook_data.ConversationSid
        )
        
        if not eligibility["eligible"]:
            logger.info(
                f"Conversation not eligible for agent: {eligibility['reason']}", 
                extra=processing_context
            )
            return WebhookResponse(
                success=True,
                message=f"Conversation not eligible: {eligibility['reason']}",
                agent_responded=False
            )
        
        # Process the message with the agent
        response = await process_message_with_agent(webhook_data, processing_context)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        response.processing_time_ms = int(processing_time)
        
        logger.info(
            f"Webhook processed successfully in {processing_time:.0f}ms", 
            extra=processing_context
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing webhook: {e}", extra=processing_context, exc_info=True)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        return WebhookResponse(
            success=False,
            message="Internal server error processing webhook",
            processing_time_ms=int(processing_time),
            error_code="internal_error"
        )


async def process_message_with_agent(
    webhook_data: WebhookRequest,
    context: Dict[str, Any]
) -> WebhookResponse:
    """
    Process a message through the AI agent and send response.
    
    Args:
        webhook_data: Parsed webhook request
        context: Processing context for logging
        
    Returns:
        WebhookResponse with processing results
    """
    try:
        # Get or create conversation session
        session = await session_service.get_or_create_session(
            conversation_sid=webhook_data.ConversationSid,
            service_sid=webhook_data.ServiceSid,
            participant_sid=webhook_data.ParticipantSid
        )
        
        # Add customer message to session
        await session_service.add_message_to_session(
            session_id=session.session_id,
            role=MessageRole.USER,
            content=webhook_data.Body,
            author=webhook_data.Author
        )
        
        # Set typing indicator while processing
        typing_task = None
        if webhook_data.ParticipantSid:
            typing_task = asyncio.create_task(
                set_typing_indicator_with_timeout(
                    webhook_data.ConversationSid,
                    webhook_data.ParticipantSid,
                    settings.agent.typing_indicator_timeout_seconds
                )
            )
        
        try:
            # Generate response using AI agent
            agent_response = await agent_service.process_message(
                message=webhook_data.Body,
                session_id=session.session_id,
                context=session.context.dict()
            )
            
            # Send response via Twilio
            twilio_message = await twilio_service.send_message(
                conversation_sid=webhook_data.ConversationSid,
                message=agent_response.content,
                author="assistant"
            )
            
            if twilio_message:
                # Add assistant response to session
                await session_service.add_message_to_session(
                    session_id=session.session_id,
                    role=MessageRole.ASSISTANT,
                    content=agent_response.content,
                    author="assistant",
                    metadata={
                        "twilio_message_sid": twilio_message.sid,
                        "confidence": agent_response.confidence,
                        "tools_used": agent_response.tools_used,
                        "processing_time_ms": agent_response.processing_time_ms
                    }
                )
                
                logger.info(
                    f"Agent response sent successfully: {twilio_message.sid}",
                    extra=context
                )
                
                return WebhookResponse(
                    success=True,
                    message="Message processed and response sent",
                    agent_responded=True
                )
            else:
                logger.error("Failed to send agent response via Twilio", extra=context)
                return WebhookResponse(
                    success=False,
                    message="Failed to send agent response",
                    agent_responded=False,
                    error_code="twilio_send_error"
                )
                
        finally:
            # Cancel typing indicator
            if typing_task and not typing_task.done():
                typing_task.cancel()
                try:
                    await typing_task
                except asyncio.CancelledError:
                    pass
            
            # Clear typing indicator
            if webhook_data.ParticipantSid:
                await twilio_service.set_typing_indicator(
                    webhook_data.ConversationSid,
                    webhook_data.ParticipantSid,
                    is_typing=False
                )
    
    except Exception as e:
        logger.error(f"Error processing message with agent: {e}", extra=context, exc_info=True)
        return WebhookResponse(
            success=False,
            message="Error processing message with agent",
            agent_responded=False,
            error_code="agent_processing_error"
        )


async def set_typing_indicator_with_timeout(
    conversation_sid: str,
    participant_sid: str,
    timeout_seconds: int
):
    """
    Set typing indicator and automatically clear it after timeout.
    
    Args:
        conversation_sid: Conversation SID
        participant_sid: Participant SID
        timeout_seconds: Timeout in seconds
    """
    try:
        # Set typing indicator
        await twilio_service.set_typing_indicator(
            conversation_sid, participant_sid, is_typing=True
        )
        
        # Wait for timeout
        await asyncio.sleep(timeout_seconds)
        
        # Clear typing indicator
        await twilio_service.set_typing_indicator(
            conversation_sid, participant_sid, is_typing=False
        )
        
    except asyncio.CancelledError:
        # Task was cancelled - clear typing indicator
        await twilio_service.set_typing_indicator(
            conversation_sid, participant_sid, is_typing=False
        )
    except Exception as e:
        logger.warning(f"Error managing typing indicator: {e}")


@router.post("/participant-added")
async def handle_participant_added(request: Request):
    """
    Handle participant added webhooks.
    
    Currently logs the event but doesn't take specific action.
    Future enhancement: Could be used to detect when human agents join.
    """
    try:
        form_data = await request.form()
        webhook_data = dict(form_data)
        
        logger.info(
            f"Participant added to conversation {webhook_data.get('ConversationSid')}: "
            f"{webhook_data.get('Identity', 'Unknown')}"
        )
        
        return {"success": True, "message": "Participant added event processed"}
        
    except Exception as e:
        logger.error(f"Error processing participant-added webhook: {e}")
        return {"success": False, "message": "Error processing participant added event"}


@router.post("/participant-removed")
async def handle_participant_removed(request: Request):
    """
    Handle participant removed webhooks.
    
    Currently logs the event but doesn't take specific action.
    Future enhancement: Could be used to clean up sessions when participants leave.
    """
    try:
        form_data = await request.form()
        webhook_data = dict(form_data)
        
        logger.info(
            f"Participant removed from conversation {webhook_data.get('ConversationSid')}: "
            f"{webhook_data.get('Identity', 'Unknown')}"
        )
        
        return {"success": True, "message": "Participant removed event processed"}
        
    except Exception as e:
        logger.error(f"Error processing participant-removed webhook: {e}")
        return {"success": False, "message": "Error processing participant removed event"}


@router.post("/conversation-state-updated")
async def handle_conversation_state_updated(request: Request):
    """
    Handle conversation state update webhooks.
    
    Could be used to pause/resume agent processing based on conversation state.
    """
    try:
        form_data = await request.form()
        webhook_data = dict(form_data)
        
        logger.info(
            f"Conversation state updated {webhook_data.get('ConversationSid')}: "
            f"{webhook_data.get('State', 'Unknown')}"
        )
        
        # TODO: Update session state in database if needed
        
        return {"success": True, "message": "Conversation state update processed"}
        
    except Exception as e:
        logger.error(f"Error processing conversation-state-updated webhook: {e}")
        return {"success": False, "message": "Error processing conversation state update"}


@router.get("/test")
async def test_webhook_endpoint():
    """
    Test endpoint for webhook configuration validation.
    """
    return {
        "success": True,
        "message": "Webhook endpoint is working",
        "timestamp": datetime.now().isoformat(),
        "service": "twilio-openai-conversations"
    }