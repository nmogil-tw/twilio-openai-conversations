"""
Voice service for handling Twilio ConversationRelay voice interactions.
Manages voice sessions, streaming responses, and integration with existing services.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, AsyncGenerator
from fastapi import WebSocket

from config.settings import settings
from src.models.voice import VoiceSession, VoiceSessionStatus, StreamingChunk
from src.services.agent_service import CustomerServiceAgent
from src.services.session_service import SessionService
from src.models.conversation import MessageRole
from src.utils.logging import get_logger

logger = get_logger(__name__)


class VoiceService:
    """Service for managing voice conversations and streaming responses."""
    
    def __init__(self):
        self.active_sessions: Dict[str, VoiceSession] = {}
        self.active_websockets: Dict[str, WebSocket] = {}
        self.agent_service = CustomerServiceAgent()
        self.session_service = SessionService()
    
    async def create_voice_session(
        self, 
        call_sid: str, 
        phone_number: Optional[str] = None
    ) -> VoiceSession:
        """Create a new voice session."""
        voice_session = VoiceSession(
            call_sid=call_sid,
            phone_number=phone_number,
            status=VoiceSessionStatus.SETUP
        )
        
        # Create or link to existing conversation session
        try:
            conversation_session = await self.session_service.get_or_create_session(
                conversation_sid=call_sid,  # Use call_sid as conversation_sid for voice
                service_sid="voice_service",
                participant_sid=phone_number or "unknown"
            )
            voice_session.session_id = conversation_session.session_id
            logger.info(f"Created voice session {call_sid} linked to conversation {conversation_session.session_id}")
        except Exception as e:
            logger.warning(f"Failed to create conversation session for voice call {call_sid}: {e}")
        
        self.active_sessions[call_sid] = voice_session
        return voice_session
    
    async def get_voice_session(self, call_sid: str) -> Optional[VoiceSession]:
        """Get existing voice session."""
        return self.active_sessions.get(call_sid)
    
    async def update_session_activity(self, call_sid: str) -> None:
        """Update last activity timestamp for session."""
        if call_sid in self.active_sessions:
            self.active_sessions[call_sid].last_activity = datetime.now()
    
    async def close_voice_session(self, call_sid: str) -> None:
        """Close and cleanup voice session."""
        if call_sid in self.active_sessions:
            session = self.active_sessions[call_sid]
            session.status = VoiceSessionStatus.COMPLETED
            
            # Remove from active sessions after delay to allow cleanup
            await asyncio.sleep(5)
            self.active_sessions.pop(call_sid, None)
            self.active_websockets.pop(call_sid, None)
            
            logger.info(f"Closed voice session {call_sid}")
    
    async def process_voice_message(
        self, 
        call_sid: str, 
        message: str,
        websocket: WebSocket
    ) -> None:
        """Process voice message and stream response."""
        session = await self.get_voice_session(call_sid)
        if not session:
            logger.error(f"No voice session found for call {call_sid}")
            return
        
        await self.update_session_activity(call_sid)
        
        try:
            # Add user message to conversation session if linked
            if session.session_id:
                await self.session_service.add_message_to_session(
                    session_id=session.session_id,
                    role=MessageRole.USER,
                    content=message,
                    author="user"
                )
            
            # Add to voice session messages for context
            session.messages.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat()
            })
            
            # Generate and stream response
            await self._stream_agent_response(call_sid, message, websocket)
            
        except Exception as e:
            logger.error(f"Error processing voice message for {call_sid}: {e}", exc_info=True)
            # Send error response
            error_response = {
                "type": "text",
                "token": "I apologize, but I'm experiencing technical difficulties. Please try again.",
                "last": True
            }
            await websocket.send_text(json.dumps(error_response))
    
    async def _stream_agent_response(
        self,
        call_sid: str,
        message: str,
        websocket: WebSocket
    ) -> None:
        """Generate agent response and stream it to the voice session."""
        session = self.active_sessions.get(call_sid)
        if not session:
            return
        
        # Build conversation context
        conversation_messages = [
            {"role": "system", "content": settings.voice_system_prompt}
        ]
        
        # Add recent message history for context
        recent_messages = session.messages[-10:]  # Last 10 messages for context
        conversation_messages.extend(recent_messages)
        conversation_messages.append({"role": "user", "content": message})
        
        try:
            # Get streaming response from agent
            full_response = ""
            chunk_buffer = ""
            
            async for chunk in self._get_streaming_response(conversation_messages, session.session_id):
                chunk_buffer += chunk.content
                full_response += chunk.content
                
                # Send chunks when buffer reaches target size or at end
                if len(chunk_buffer) >= settings.streaming_chunk_size or chunk.is_final:
                    response = {
                        "type": "text",
                        "token": chunk_buffer,
                        "last": chunk.is_final
                    }
                    
                    await websocket.send_text(json.dumps(response))
                    await asyncio.sleep(settings.streaming_delay_ms / 1000.0)
                    
                    chunk_buffer = ""
            
            # Add assistant response to session
            session.messages.append({
                "role": "assistant",
                "content": full_response,
                "timestamp": datetime.now().isoformat()
            })
            
            # Add to conversation session if linked
            if session.session_id:
                await self.session_service.add_message_to_session(
                    session_id=session.session_id,
                    role=MessageRole.ASSISTANT,
                    content=full_response,
                    author="assistant"
                )
            
            logger.info(f"Streamed response for call {call_sid}: {len(full_response)} characters")
            
        except Exception as e:
            logger.error(f"Error streaming response for {call_sid}: {e}", exc_info=True)
            # Send fallback response
            error_response = {
                "type": "text",
                "token": "I apologize, but I couldn't process your request. Please try again.",
                "last": True
            }
            await websocket.send_text(json.dumps(error_response))
    
    async def _get_streaming_response(
        self, 
        messages: list,
        session_id: Optional[str] = None
    ) -> AsyncGenerator[StreamingChunk, None]:
        """Get streaming response from the agent service."""
        # This will be implemented based on your agent service streaming capabilities
        # For now, simulate streaming by chunking a complete response
        
        try:
            # Get complete response from agent (modify agent_service to support streaming)
            response = await self.agent_service.process_message(
                message=messages[-1]["content"],
                session_id=session_id,
                context={"voice_mode": True}
            )
            
            # Simulate streaming by chunking the response
            content = response.content
            chunk_size = settings.streaming_chunk_size
            
            for i in range(0, len(content), chunk_size):
                chunk_content = content[i:i + chunk_size]
                is_final = i + chunk_size >= len(content)
                
                yield StreamingChunk(
                    content=chunk_content,
                    is_final=is_final
                )
                
                if not is_final:
                    await asyncio.sleep(settings.streaming_delay_ms / 1000.0)
                    
        except Exception as e:
            logger.error(f"Error getting streaming response: {e}")
            yield StreamingChunk(
                content="I apologize, but I'm experiencing technical difficulties.",
                is_final=True
            )
    
    async def cleanup_inactive_sessions(self) -> None:
        """Clean up inactive voice sessions."""
        cutoff_time = datetime.now() - timedelta(seconds=settings.voice_max_session_duration)
        
        inactive_sessions = [
            call_sid for call_sid, session in self.active_sessions.items()
            if session.last_activity < cutoff_time
        ]
        
        for call_sid in inactive_sessions:
            logger.info(f"Cleaning up inactive voice session: {call_sid}")
            await self.close_voice_session(call_sid)