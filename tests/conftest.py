"""
Pytest configuration and shared fixtures for testing.
Provides common test fixtures, mock objects, and configuration.
"""

import asyncio
import pytest
import tempfile
from typing import Dict, Any, AsyncGenerator
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from fastapi.testclient import TestClient
from httpx import AsyncClient

# Import application components
from config.settings import ApplicationSettings, TwilioSettings, OpenAISettings
from src.main import app
from src.models.conversation import ConversationSession, ConversationContext, Message, MessageRole
from src.models.webhook import WebhookRequest
from src.services.agent_service import CustomerServiceAgent
from src.services.twilio_service import TwilioConversationService
from src.services.session_service import SessionService


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> ApplicationSettings:
    """
    Provide test settings with safe default values.
    
    Returns:
        ApplicationSettings configured for testing
    """
    return ApplicationSettings(
        debug=True,
        log_level="DEBUG",
        twilio=TwilioSettings(
            account_sid="ACtest123456789012345678901234",
            auth_token="test_auth_token",
            conversations_service_sid="IStest123456789012345678901234",
            webhook_secret="test_webhook_secret"
        ),
        openai=OpenAISettings(
            api_key="sk-test123456789012345678901234567890",
            model="gpt-4o-mini"
        )
    )


@pytest.fixture
def client() -> TestClient:
    """
    Provide FastAPI test client.
    
    Returns:
        TestClient for making HTTP requests to the application
    """
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Provide async HTTP client for testing.
    
    Yields:
        AsyncClient for making async HTTP requests
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_twilio_client():
    """
    Mock Twilio client for testing.
    
    Returns:
        Mock Twilio client with common methods
    """
    mock_client = Mock()
    
    # Mock conversations service
    mock_conversations = Mock()
    mock_client.conversations.v1.services.return_value = mock_conversations
    
    # Mock message creation
    mock_message = Mock()
    mock_message.sid = "IMtest123456789012345678901234"
    mock_message.body = "Test response message"
    mock_message.author = "assistant"
    mock_message.account_sid = "ACtest123456789012345678901234"
    mock_message.conversation_sid = "CHtest123456789012345678901234"
    mock_message.service_sid = "IStest123456789012345678901234"
    mock_message.participant_sid = "MBtest123456789012345678901234"
    mock_message.date_created = "2024-01-15T10:30:00Z"
    mock_message.date_updated = "2024-01-15T10:30:00Z"
    mock_message.index = 1
    
    mock_conversations.conversations.return_value.messages.create.return_value = mock_message
    
    # Mock conversation details
    mock_conversation = Mock()
    mock_conversation.sid = "CHtest123456789012345678901234"
    mock_conversation.state = "active"
    mock_conversation.friendly_name = "Test Conversation"
    mock_conversation.account_sid = "ACtest123456789012345678901234"
    mock_conversation.service_sid = "IStest123456789012345678901234"
    
    mock_conversations.conversations.return_value.fetch.return_value = mock_conversation
    
    # Mock participants
    mock_participant = Mock()
    mock_participant.sid = "MBtest123456789012345678901234"
    mock_participant.identity = "customer_12345"
    mock_participant.account_sid = "ACtest123456789012345678901234"
    mock_participant.conversation_sid = "CHtest123456789012345678901234"
    mock_participant.service_sid = "IStest123456789012345678901234"
    
    mock_conversations.conversations.return_value.participants.list.return_value = [mock_participant]
    
    return mock_client


@pytest.fixture
def mock_openai_client():
    """
    Mock OpenAI client for testing.
    
    Returns:
        Mock OpenAI client with chat completions
    """
    mock_client = Mock()
    
    # Mock chat completion response
    mock_choice = Mock()
    mock_choice.message.content = "I'd be happy to help you with that!"
    
    mock_usage = Mock()
    mock_usage.total_tokens = 45
    mock_usage.prompt_tokens = 25
    mock_usage.completion_tokens = 20
    
    mock_response = Mock()
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage
    
    mock_client.chat.completions.create.return_value = mock_response
    
    return mock_client


@pytest.fixture
def sample_webhook_data() -> Dict[str, Any]:
    """
    Provide sample webhook data for testing.
    
    Returns:
        Dictionary with sample Twilio webhook data
    """
    return {
        "EventType": "onMessageAdd",
        "AccountSid": "ACtest123456789012345678901234",
        "ServiceSid": "IStest123456789012345678901234",
        "ConversationSid": "CHtest123456789012345678901234",
        "MessageSid": "IMtest123456789012345678901234",
        "ParticipantSid": "MBtest123456789012345678901234",
        "Author": "customer_12345",
        "Body": "Hello, I need help with my order #12345",
        "MessageIndex": "1"
    }


@pytest.fixture
def sample_webhook_request(sample_webhook_data) -> WebhookRequest:
    """
    Provide sample WebhookRequest object.
    
    Returns:
        WebhookRequest instance for testing
    """
    return WebhookRequest(**sample_webhook_data)


@pytest.fixture
def sample_conversation_session() -> ConversationSession:
    """
    Provide sample conversation session for testing.
    
    Returns:
        ConversationSession instance with sample data
    """
    return ConversationSession(
        session_id="conv_CHtest123456789012345678901234",
        conversation_sid="CHtest123456789012345678901234",
        service_sid="IStest123456789012345678901234",
        participant_sid="MBtest123456789012345678901234",
        messages=[
            Message(
                role=MessageRole.USER,
                content="Hello, I need help with my order",
                author="customer_12345"
            )
        ],
        context=ConversationContext(
            customer_info={"name": "John Doe", "email": "john@example.com"},
            tags=["new_customer"]
        )
    )


@pytest.fixture
def temp_database():
    """
    Provide temporary database for testing.
    
    Returns:
        Path to temporary SQLite database
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    # Return SQLite URL
    yield f"sqlite:///{db_path}"
    
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
async def mock_agent_service():
    """
    Mock agent service for testing.
    
    Returns:
        Mock CustomerServiceAgent
    """
    mock_service = AsyncMock(spec=CustomerServiceAgent)
    
    # Mock process_message response
    from src.models.conversation import AgentResponse
    
    mock_response = AgentResponse(
        content="I'd be happy to help you with your order!",
        confidence=0.95,
        tools_used=["lookup_order_status"],
        processing_time_ms=1250,
        metadata={"model_used": "gpt-4o-mini"}
    )
    
    mock_service.process_message.return_value = mock_response
    
    return mock_service


@pytest.fixture
async def mock_twilio_service():
    """
    Mock Twilio service for testing.
    
    Returns:
        Mock TwilioConversationService
    """
    mock_service = AsyncMock(spec=TwilioConversationService)
    
    # Mock send_message response
    from src.models.webhook import TwilioMessage
    
    mock_message = TwilioMessage(
        sid="IMtest123456789012345678901234",
        account_sid="ACtest123456789012345678901234",
        conversation_sid="CHtest123456789012345678901234",
        service_sid="IStest123456789012345678901234",
        author="assistant",
        body="I'd be happy to help you with that!"
    )
    
    mock_service.send_message.return_value = mock_message
    
    # Mock conversation eligibility
    mock_service.check_conversation_eligibility.return_value = {
        "eligible": True,
        "reason": "eligible",
        "participant_count": 1,
        "has_human_agent": False
    }
    
    # Mock signature validation
    mock_service.validate_webhook_signature.return_value = True
    
    return mock_service


@pytest.fixture
async def mock_session_service(sample_conversation_session):
    """
    Mock session service for testing.
    
    Returns:
        Mock SessionService
    """
    mock_service = AsyncMock(spec=SessionService)
    
    # Mock session operations
    mock_service.get_or_create_session.return_value = sample_conversation_session
    mock_service.get_session.return_value = sample_conversation_session
    mock_service.save_session.return_value = True
    mock_service.add_message_to_session.return_value = True
    
    return mock_service


@pytest.fixture
def mock_signature_validation():
    """
    Mock webhook signature validation.
    
    Returns:
        Mock function that always returns True
    """
    with patch('src.utils.security.validate_webhook_signature', return_value=True) as mock:
        yield mock


class AsyncContextManager:
    """Helper class for creating async context managers in tests."""
    
    def __init__(self, return_value):
        self.return_value = return_value
    
    async def __aenter__(self):
        return self.return_value
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def mock_database_session():
    """
    Mock database session for testing.
    
    Returns:
        Mock database session
    """
    mock_session = AsyncMock()
    
    # Mock session operations
    mock_session.execute.return_value.scalar_one_or_none.return_value = None
    mock_session.execute.return_value.scalars.return_value.all.return_value = []
    mock_session.commit.return_value = None
    mock_session.rollback.return_value = None
    
    return AsyncContextManager(mock_session)


# Test data constants
TEST_CONVERSATION_SID = "CHtest123456789012345678901234"
TEST_SERVICE_SID = "IStest123456789012345678901234"
TEST_MESSAGE_SID = "IMtest123456789012345678901234"
TEST_PARTICIPANT_SID = "MBtest123456789012345678901234"
TEST_ACCOUNT_SID = "ACtest123456789012345678901234"