"""
Voice Handler for Twilio ConversationRelay integration.
Handles TwiML generation and WebSocket communication for voice calls.
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import Response

from config.settings import settings
from src.models.voice import VoiceMessage
from src.services.voice_service import VoiceService
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Create FastAPI router
router = APIRouter()

# Initialize voice service
voice_service = VoiceService()


@router.post("/twiml")
async def voice_twiml_endpoint():
    """
    Generate TwiML for incoming voice calls to connect to ConversationRelay WebSocket.
    """
    try:
        # Construct WebSocket URL
        domain = settings.ngrok_domain
        if not domain:
            logger.error("NGROK_DOMAIN not configured for voice TwiML")
            raise HTTPException(status_code=500, detail="Voice service not properly configured")
        
        ws_url = f"wss://{domain}/voice/ws"
        welcome_greeting = settings.voice_welcome_greeting
        
        twiml_response = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <ConversationRelay url="{ws_url}" welcomeGreeting="{welcome_greeting}" />
    </Connect>
</Response>'''
        
        logger.info(f"Generated TwiML for voice call with WebSocket URL: {ws_url}")
        
        return Response(content=twiml_response, media_type="text/xml")
        
    except Exception as e:
        logger.error(f"Error generating voice TwiML: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate TwiML")


@router.websocket("/ws")
async def voice_websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time voice communication with Twilio ConversationRelay.
    
    Message Flow:
    1. Receive 'setup' message with call_sid
    2. Process 'prompt' messages with voice input
    3. Stream responses back as 'text' messages
    4. Handle 'interrupt' messages for conversation control
    """
    await websocket.accept()
    call_sid = None
    
    processing_context = {
        "handler": "voice_websocket",
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        logger.info("Voice WebSocket connection established", extra=processing_context)
        
        while True:
            # Receive message from Twilio
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Parse voice message
            try:
                logger.info(f"Received message data: {message_data}", extra=processing_context)
                voice_message = VoiceMessage(**message_data)
            except Exception as e:
                logger.error(f"Invalid voice message format: {e}", extra=processing_context)
                logger.error(f"Message data was: {message_data}", extra=processing_context)
                continue
            
            processing_context["message_type"] = voice_message.type
            
            if voice_message.type == "setup":
                call_sid = voice_message.call_sid
                processing_context["call_sid"] = call_sid
                
                if not call_sid:
                    logger.error("Setup message missing call_sid", extra=processing_context)
                    continue
                
                logger.info(f"Setting up voice session for call: {call_sid}", extra=processing_context)
                
                # Create voice session
                await voice_service.create_voice_session(call_sid)
                
                # Store WebSocket connection
                voice_service.active_websockets[call_sid] = websocket
                
                logger.info(f"Voice session created for call: {call_sid}", extra=processing_context)
                
            elif voice_message.type == "prompt":
                if not call_sid:
                    logger.warning("Received prompt without setup", extra=processing_context)
                    continue
                
                user_input = voice_message.voice_prompt
                if not user_input:
                    logger.warning("Received empty voice prompt", extra=processing_context)
                    continue
                
                logger.info(f"Processing voice prompt: {user_input[:100]}...", extra=processing_context)
                
                # Process message and stream response
                await voice_service.process_voice_message(call_sid, user_input, websocket)
                
            elif voice_message.type == "interrupt":
                logger.info("Handling voice interruption", extra=processing_context)
                # Handle interruption - could implement logic to stop current streaming
                
            else:
                logger.warning(f"Unknown voice message type: {voice_message.type}", extra=processing_context)
                
    except WebSocketDisconnect:
        logger.info("Voice WebSocket connection closed", extra=processing_context)
        
    except Exception as e:
        logger.error(f"Unexpected error in voice WebSocket: {e}", extra=processing_context, exc_info=True)
        
    finally:
        # Cleanup
        if call_sid:
            logger.info(f"Cleaning up voice session: {call_sid}", extra=processing_context)
            await voice_service.close_voice_session(call_sid)


@router.get("/test")
async def test_voice_endpoint():
    """
    Test endpoint for voice service health check.
    """
    return {
        "success": True,
        "message": "Voice service is operational",
        "timestamp": datetime.now().isoformat(),
        "service": "twilio-voice-integration",
        "websocket_url": f"wss://{settings.ngrok_domain}/voice/ws" if settings.ngrok_domain else "Not configured"
    }


# Background task for session cleanup
async def cleanup_inactive_sessions():
    """Background task to clean up inactive voice sessions."""
    while True:
        try:
            await voice_service.cleanup_inactive_sessions()
            await asyncio.sleep(300)  # Check every 5 minutes
        except Exception as e:
            logger.error(f"Error in session cleanup task: {e}", exc_info=True)
            await asyncio.sleep(60)  # Wait 1 minute before retry


# Start cleanup task
@router.on_event("startup")
async def start_cleanup_task():
    """Start the session cleanup background task."""
    asyncio.create_task(cleanup_inactive_sessions())