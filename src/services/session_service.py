"""
Session Management Service for conversation context and history.
Handles session persistence, context management, and conversation state tracking.
"""

import json
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, delete

from config.settings import settings
from src.models.conversation import (
    ConversationSession, ConversationContext, Message, MessageRole,
    ConversationSessionDB, MessageDB, Base
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


class SessionService:
    """
    Service for managing conversation sessions and context.
    
    Handles:
    - Session creation and retrieval
    - Message history persistence
    - Conversation context management
    - Session cleanup and timeout handling
    """
    
    def __init__(self):
        """Initialize session service with database connection."""
        self.engine = None
        self.async_session_factory = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database connection and session factory."""
        try:
            # Convert SQLite URL to async format if needed
            db_url = settings.database.url
            if db_url.startswith("sqlite:///"):
                db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///")
            elif db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
            
            self.engine = create_async_engine(
                db_url,
                echo=settings.database.echo,
                pool_size=settings.database.pool_size,
                max_overflow=settings.database.max_overflow
            )
            
            self.async_session_factory = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
            
            logger.info("Session service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize session service: {e}")
            raise
    
    async def create_tables(self):
        """Create database tables if they don't exist."""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    async def get_or_create_session(
        self,
        conversation_sid: str,
        service_sid: str,
        participant_sid: Optional[str] = None
    ) -> ConversationSession:
        """
        Get existing session or create a new one.
        
        Args:
            conversation_sid: Twilio conversation SID
            service_sid: Twilio service SID
            participant_sid: Twilio participant SID (optional)
            
        Returns:
            ConversationSession object
        """
        session_id = f"conv_{conversation_sid}"
        
        try:
            # Try to get existing session
            existing_session = await self.get_session(session_id)
            if existing_session:
                # Update last activity
                existing_session.last_activity_at = datetime.now(timezone.utc)
                await self.save_session(existing_session)
                return existing_session
            
            # Create new session
            logger.info(f"Creating new conversation session: {session_id}")
            
            session = ConversationSession(
                session_id=session_id,
                conversation_sid=conversation_sid,
                service_sid=service_sid,
                participant_sid=participant_sid
            )
            
            await self.save_session(session)
            return session
            
        except Exception as e:
            logger.error(f"Error getting/creating session {session_id}: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """
        Retrieve a session by ID.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            ConversationSession if found, None otherwise
        """
        try:
            async with self.async_session_factory() as db_session:
                # Get session record
                result = await db_session.execute(
                    select(ConversationSessionDB).where(
                        ConversationSessionDB.session_id == session_id
                    )
                )
                session_record = result.scalar_one_or_none()
                
                if not session_record:
                    return None
                
                # Get messages for this session
                messages_result = await db_session.execute(
                    select(MessageDB).where(
                        MessageDB.session_id == session_id
                    ).order_by(MessageDB.timestamp)
                )
                message_records = messages_result.scalars().all()
                
                # Convert to domain models
                messages = []
                for msg_record in message_records:
                    message = Message(
                        id=msg_record.id,
                        role=MessageRole(msg_record.role),
                        content=msg_record.content,
                        timestamp=msg_record.timestamp.replace(tzinfo=timezone.utc),
                        author=msg_record.author,
                        metadata=msg_record.message_metadata or {}
                    )
                    messages.append(message)
                
                # Parse context
                context = ConversationContext()
                if session_record.context:
                    try:
                        context_data = json.loads(session_record.context) if isinstance(session_record.context, str) else session_record.context
                        context = ConversationContext(**context_data)
                    except Exception as e:
                        logger.warning(f"Failed to parse context for session {session_id}: {e}")
                
                # Create session object
                session = ConversationSession(
                    session_id=session_record.session_id,
                    conversation_sid=session_record.conversation_sid,
                    service_sid=session_record.service_sid,
                    participant_sid=session_record.participant_sid,
                    state=session_record.state,
                    messages=messages,
                    context=context,
                    created_at=session_record.created_at.replace(tzinfo=timezone.utc),
                    updated_at=session_record.updated_at.replace(tzinfo=timezone.utc),
                    last_activity_at=session_record.last_activity_at.replace(tzinfo=timezone.utc)
                )
                
                return session
                
        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {e}")
            return None
    
    async def save_session(self, session: ConversationSession) -> bool:
        """
        Save or update a conversation session.
        
        Args:
            session: ConversationSession to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            async with self.async_session_factory() as db_session:
                # Save/update session record
                session_record = ConversationSessionDB(
                    session_id=session.session_id,
                    conversation_sid=session.conversation_sid,
                    service_sid=session.service_sid,
                    participant_sid=session.participant_sid,
                    state=session.state.value,
                    context=session.context.dict(),
                    created_at=session.created_at,
                    updated_at=session.updated_at,
                    last_activity_at=session.last_activity_at
                )
                
                await db_session.merge(session_record)
                
                # Save messages (only new ones)
                existing_message_ids = set()
                result = await db_session.execute(
                    select(MessageDB.id).where(MessageDB.session_id == session.session_id)
                )
                existing_message_ids = {row[0] for row in result.fetchall()}
                
                for message in session.messages:
                    if message.id not in existing_message_ids:
                        message_record = MessageDB(
                            id=message.id,
                            session_id=session.session_id,
                            role=message.role.value,
                            content=message.content,
                            author=message.author,
                            metadata=message.metadata,
                            timestamp=message.timestamp
                        )
                        db_session.add(message_record)
                
                await db_session.commit()
                logger.debug(f"Session saved successfully: {session.session_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving session {session.session_id}: {e}")
            return False
    
    async def add_message_to_session(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        author: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a message to an existing session.
        
        Args:
            session_id: Session identifier
            role: Message role (user, assistant, system)
            content: Message content
            author: Message author (optional)
            metadata: Additional message metadata (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session = await self.get_session(session_id)
            if not session:
                logger.error(f"Session not found: {session_id}")
                return False
            
            message = Message(
                role=role,
                content=content,
                author=author,
                message_metadata=metadata or {}
            )
            
            session.add_message(message)
            return await self.save_session(session)
            
        except Exception as e:
            logger.error(f"Error adding message to session {session_id}: {e}")
            return False
    
    async def update_session_context(
        self,
        session_id: str,
        context_updates: Dict[str, Any]
    ) -> bool:
        """
        Update session context with new information.
        
        Args:
            session_id: Session identifier
            context_updates: Dictionary of context updates
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session = await self.get_session(session_id)
            if not session:
                logger.error(f"Session not found: {session_id}")
                return False
            
            # Update context fields
            context_dict = session.context.dict()
            context_dict.update(context_updates)
            session.context = ConversationContext(**context_dict)
            session.updated_at = datetime.now(timezone.utc)
            
            return await self.save_session(session)
            
        except Exception as e:
            logger.error(f"Error updating session context {session_id}: {e}")
            return False
    
    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 50,
        include_system: bool = False
    ) -> List[Message]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return
            include_system: Whether to include system messages
            
        Returns:
            List of Message objects
        """
        try:
            session = await self.get_session(session_id)
            if not session:
                return []
            
            messages = session.messages
            
            if not include_system:
                messages = [msg for msg in messages if msg.role != MessageRole.SYSTEM]
            
            return messages[-limit:] if limit > 0 else messages
            
        except Exception as e:
            logger.error(f"Error getting conversation history for {session_id}: {e}")
            return []
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions based on configured timeout.
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            timeout_minutes = settings.agent.conversation_timeout_minutes
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)
            
            async with self.async_session_factory() as db_session:
                # Get expired session IDs
                result = await db_session.execute(
                    select(ConversationSessionDB.session_id).where(
                        ConversationSessionDB.last_activity_at < cutoff_time
                    )
                )
                expired_session_ids = [row[0] for row in result.fetchall()]
                
                if not expired_session_ids:
                    return 0
                
                # Delete messages for expired sessions
                await db_session.execute(
                    delete(MessageDB).where(
                        MessageDB.session_id.in_(expired_session_ids)
                    )
                )
                
                # Delete expired sessions
                await db_session.execute(
                    delete(ConversationSessionDB).where(
                        ConversationSessionDB.session_id.in_(expired_session_ids)
                    )
                )
                
                await db_session.commit()
                
                logger.info(f"Cleaned up {len(expired_session_ids)} expired sessions")
                return len(expired_session_ids)
                
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            return 0
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """
        Get statistics about sessions.
        
        Returns:
            Dictionary with session statistics
        """
        try:
            async with self.async_session_factory() as db_session:
                # Total sessions
                result = await db_session.execute(
                    select(ConversationSessionDB).count()
                )
                total_sessions = result.scalar()
                
                # Active sessions (activity within last hour)
                one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
                result = await db_session.execute(
                    select(ConversationSessionDB).where(
                        ConversationSessionDB.last_activity_at > one_hour_ago
                    ).count()
                )
                active_sessions = result.scalar()
                
                # Total messages
                result = await db_session.execute(
                    select(MessageDB).count()
                )
                total_messages = result.scalar()
                
                return {
                    "total_sessions": total_sessions,
                    "active_sessions": active_sessions,
                    "total_messages": total_messages,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting session stats: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def close(self):
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Session service closed")