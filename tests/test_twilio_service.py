"""
Tests for TwilioConversationService and Twilio API integration.
Tests message sending, conversation management, and participant handling.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from twilio.base.exceptions import TwilioRestException

from src.services.twilio_service import TwilioConversationService
from src.models.webhook import TwilioMessage, TwilioConversation, TwilioParticipant
from tests.conftest import (
    TEST_CONVERSATION_SID, TEST_SERVICE_SID, TEST_MESSAGE_SID,
    TEST_PARTICIPANT_SID, TEST_ACCOUNT_SID
)


class TestTwilioConversationService:
    """Test cases for TwilioConversationService class."""
    
    @pytest.fixture
    def mock_twilio_client(self):
        """Mock Twilio client for testing."""
        with patch('src.services.twilio_service.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock service structure
            mock_service = Mock()
            mock_client.conversations.v1.services.return_value = mock_service
            
            # Mock conversation operations
            mock_conversation = Mock()
            mock_service.conversations.return_value = mock_conversation
            
            yield mock_client, mock_service, mock_conversation
    
    def test_service_initialization(self, mock_twilio_client):
        """Test Twilio service initialization."""
        mock_client, _, _ = mock_twilio_client
        
        service = TwilioConversationService()
        
        assert service.client is not None
        assert service.service_sid == "IStest123456789012345678901234"  # From test settings
    
    @pytest.mark.asyncio
    async def test_send_message_success(self, mock_twilio_client):
        """Test successful message sending."""
        mock_client, _, mock_conversation = mock_twilio_client
        
        # Mock message creation response
        mock_message = Mock()
        mock_message.sid = TEST_MESSAGE_SID
        mock_message.body = "Test response"
        mock_message.author = "assistant"
        mock_message.account_sid = TEST_ACCOUNT_SID
        mock_message.conversation_sid = TEST_CONVERSATION_SID
        mock_message.service_sid = TEST_SERVICE_SID
        mock_message.participant_sid = TEST_PARTICIPANT_SID
        mock_message.date_created = "2024-01-15T10:30:00Z"
        mock_message.date_updated = "2024-01-15T10:30:00Z"
        mock_message.index = 1
        
        mock_conversation.messages.create.return_value = mock_message
        
        service = TwilioConversationService()
        
        result = await service.send_message(
            conversation_sid=TEST_CONVERSATION_SID,
            message="Test response",
            author="assistant"
        )
        
        assert isinstance(result, TwilioMessage)
        assert result.sid == TEST_MESSAGE_SID
        assert result.body == "Test response"
        assert result.author == "assistant"
        
        # Verify the Twilio API was called correctly
        mock_conversation.messages.create.assert_called_once_with(
            author="assistant",
            body="Test response"
        )
    
    @pytest.mark.asyncio
    async def test_send_message_with_media(self, mock_twilio_client):
        """Test message sending with media attachment."""
        mock_client, _, mock_conversation = mock_twilio_client
        
        # Mock message creation response
        mock_message = Mock()
        mock_message.sid = TEST_MESSAGE_SID
        mock_conversation.messages.create.return_value = mock_message
        
        service = TwilioConversationService()
        
        await service.send_message(
            conversation_sid=TEST_CONVERSATION_SID,
            message="Check out this image",
            author="assistant",
            media_url="https://example.com/image.jpg"
        )
        
        # Verify media URL was included
        mock_conversation.messages.create.assert_called_once_with(
            author="assistant",
            body="Check out this image",
            media_url="https://example.com/image.jpg"
        )
    
    @pytest.mark.asyncio
    async def test_send_message_twilio_error(self, mock_twilio_client):
        """Test message sending with Twilio API error."""
        mock_client, _, mock_conversation = mock_twilio_client
        
        # Mock Twilio REST exception
        mock_conversation.messages.create.side_effect = TwilioRestException(
            status=400,
            uri="test",
            msg="Invalid request"
        )
        
        service = TwilioConversationService()
        
        result = await service.send_message(
            conversation_sid=TEST_CONVERSATION_SID,
            message="Test message"
        )
        
        assert result is None  # Should return None on error
    
    @pytest.mark.asyncio
    async def test_set_typing_indicator_on(self, mock_twilio_client):
        """Test setting typing indicator to on."""
        mock_client, _, mock_conversation = mock_twilio_client
        
        service = TwilioConversationService()
        
        result = await service.set_typing_indicator(
            conversation_sid=TEST_CONVERSATION_SID,
            participant_sid=TEST_PARTICIPANT_SID,
            is_typing=True
        )
        
        assert result is True
        mock_conversation.participants.return_value.update.assert_called_once_with(
            typing={"typing": True}
        )
    
    @pytest.mark.asyncio
    async def test_set_typing_indicator_off(self, mock_twilio_client):
        """Test setting typing indicator to off."""
        mock_client, _, mock_conversation = mock_twilio_client
        
        service = TwilioConversationService()
        
        result = await service.set_typing_indicator(
            conversation_sid=TEST_CONVERSATION_SID,
            participant_sid=TEST_PARTICIPANT_SID,
            is_typing=False
        )
        
        assert result is True
        mock_conversation.participants.return_value.update.assert_called_once_with(
            typing={"typing": False}
        )
    
    @pytest.mark.asyncio
    async def test_set_typing_indicator_error(self, mock_twilio_client):
        """Test typing indicator with API error."""
        mock_client, _, mock_conversation = mock_twilio_client
        
        # Mock Twilio REST exception
        mock_conversation.participants.return_value.update.side_effect = TwilioRestException(
            status=404,
            uri="test",
            msg="Participant not found"
        )
        
        service = TwilioConversationService()
        
        result = await service.set_typing_indicator(
            conversation_sid=TEST_CONVERSATION_SID,
            participant_sid=TEST_PARTICIPANT_SID,
            is_typing=True
        )
        
        assert result is False  # Should return False on error
    
    @pytest.mark.asyncio
    async def test_get_conversation_details_success(self, mock_twilio_client):
        """Test successful conversation details retrieval."""
        mock_client, _, mock_conversation = mock_twilio_client
        
        # Mock conversation fetch response
        mock_conv = Mock()
        mock_conv.sid = TEST_CONVERSATION_SID
        mock_conv.account_sid = TEST_ACCOUNT_SID
        mock_conv.service_sid = TEST_SERVICE_SID
        mock_conv.friendly_name = "Test Conversation"
        mock_conv.unique_name = "test_conv_123"
        mock_conv.state = "active"
        mock_conv.date_created = "2024-01-15T10:30:00Z"
        mock_conv.date_updated = "2024-01-15T10:30:00Z"
        mock_conv.messaging_service_sid = None
        mock_conv.attributes = "{}"
        
        mock_conversation.fetch.return_value = mock_conv
        
        service = TwilioConversationService()
        
        result = await service.get_conversation_details(TEST_CONVERSATION_SID)
        
        assert isinstance(result, TwilioConversation)
        assert result.sid == TEST_CONVERSATION_SID
        assert result.friendly_name == "Test Conversation"
        assert result.state == "active"
    
    @pytest.mark.asyncio
    async def test_get_conversation_details_not_found(self, mock_twilio_client):
        """Test conversation details retrieval when conversation not found."""
        mock_client, _, mock_conversation = mock_twilio_client
        
        # Mock Twilio REST exception for not found
        mock_conversation.fetch.side_effect = TwilioRestException(
            status=404,
            uri="test",
            msg="Conversation not found"
        )
        
        service = TwilioConversationService()
        
        result = await service.get_conversation_details(TEST_CONVERSATION_SID)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_conversation_participants_success(self, mock_twilio_client):
        """Test successful participant retrieval."""
        mock_client, _, mock_conversation = mock_twilio_client
        
        # Mock participant list response
        mock_participant = Mock()
        mock_participant.sid = TEST_PARTICIPANT_SID
        mock_participant.account_sid = TEST_ACCOUNT_SID
        mock_participant.conversation_sid = TEST_CONVERSATION_SID
        mock_participant.service_sid = TEST_SERVICE_SID
        mock_participant.identity = "customer_12345"
        mock_participant.messaging_binding = {"type": "sms", "address": "+1234567890"}
        mock_participant.role_sid = None
        mock_participant.date_created = "2024-01-15T10:30:00Z"
        mock_participant.date_updated = "2024-01-15T10:30:00Z"
        
        mock_conversation.participants.list.return_value = [mock_participant]
        
        service = TwilioConversationService()
        
        result = await service.get_conversation_participants(TEST_CONVERSATION_SID)
        
        assert len(result) == 1
        assert isinstance(result[0], TwilioParticipant)
        assert result[0].sid == TEST_PARTICIPANT_SID
        assert result[0].identity == "customer_12345"
    
    @pytest.mark.asyncio
    async def test_get_conversation_participants_empty(self, mock_twilio_client):
        """Test participant retrieval with no participants."""
        mock_client, _, mock_conversation = mock_twilio_client
        
        mock_conversation.participants.list.return_value = []
        
        service = TwilioConversationService()
        
        result = await service.get_conversation_participants(TEST_CONVERSATION_SID)
        
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_check_conversation_eligibility_eligible(self, mock_twilio_client):
        """Test conversation eligibility check for eligible conversation."""
        mock_client, _, mock_conversation = mock_twilio_client
        
        service = TwilioConversationService()
        
        # Mock conversation details
        with patch.object(service, 'get_conversation_details') as mock_get_conv, \
             patch.object(service, 'get_conversation_participants') as mock_get_participants:
            
            # Mock active conversation
            mock_conversation_obj = Mock()
            mock_conversation_obj.state = "active"
            mock_get_conv.return_value = mock_conversation_obj
            
            # Mock single customer participant
            mock_participant = Mock()
            mock_participant.identity = "customer_12345"
            mock_get_participants.return_value = [mock_participant]
            
            result = await service.check_conversation_eligibility(TEST_CONVERSATION_SID)
            
            assert result["eligible"] is True
            assert result["reason"] == "eligible"
            assert result["customer_count"] == 1
            assert result["has_human_agent"] is False
    
    @pytest.mark.asyncio
    async def test_check_conversation_eligibility_human_agent_present(self, mock_twilio_client):
        """Test conversation eligibility when human agent is present."""
        mock_client, _, mock_conversation = mock_twilio_client
        
        service = TwilioConversationService()
        
        with patch.object(service, 'get_conversation_details') as mock_get_conv, \
             patch.object(service, 'get_conversation_participants') as mock_get_participants:
            
            # Mock active conversation
            mock_conversation_obj = Mock()
            mock_conversation_obj.state = "active"
            mock_get_conv.return_value = mock_conversation_obj
            
            # Mock participants with human agent
            mock_customer = Mock()
            mock_customer.identity = "customer_12345"
            mock_human_agent = Mock()
            mock_human_agent.identity = "human_agent_jane"
            mock_get_participants.return_value = [mock_customer, mock_human_agent]
            
            result = await service.check_conversation_eligibility(TEST_CONVERSATION_SID)
            
            assert result["eligible"] is False
            assert result["reason"] == "human_agent_present"
            assert result["has_human_agent"] is True
    
    @pytest.mark.asyncio
    async def test_check_conversation_eligibility_not_active(self, mock_twilio_client):
        """Test conversation eligibility for inactive conversation."""
        mock_client, _, mock_conversation = mock_twilio_client
        
        service = TwilioConversationService()
        
        with patch.object(service, 'get_conversation_details') as mock_get_conv:
            # Mock inactive conversation
            mock_conversation_obj = Mock()
            mock_conversation_obj.state = "closed"
            mock_get_conv.return_value = mock_conversation_obj
            
            result = await service.check_conversation_eligibility(TEST_CONVERSATION_SID)
            
            assert result["eligible"] is False
            assert result["reason"] == "conversation_not_active"
            assert result["state"] == "closed"
    
    @pytest.mark.asyncio
    async def test_update_conversation_attributes_success(self, mock_twilio_client):
        """Test successful conversation attributes update."""
        mock_client, _, mock_conversation = mock_twilio_client
        
        service = TwilioConversationService()
        
        attributes = {"customer_id": "12345", "priority": "high"}
        
        result = await service.update_conversation_attributes(
            TEST_CONVERSATION_SID, attributes
        )
        
        assert result is True
        mock_conversation.update.assert_called_once()
        
        # Check that JSON was passed to update
        call_args = mock_conversation.update.call_args
        assert "attributes" in call_args.kwargs
        import json
        passed_attrs = json.loads(call_args.kwargs["attributes"])
        assert passed_attrs == attributes
    
    @pytest.mark.asyncio
    async def test_add_agent_participant_success(self, mock_twilio_client):
        """Test successful agent participant addition."""
        mock_client, _, mock_conversation = mock_twilio_client
        
        # Mock participant creation response
        mock_participant = Mock()
        mock_participant.sid = "MBagent123456789012345678901234"
        mock_participant.account_sid = TEST_ACCOUNT_SID
        mock_participant.conversation_sid = TEST_CONVERSATION_SID
        mock_participant.service_sid = TEST_SERVICE_SID
        mock_participant.identity = "ai_assistant"
        mock_participant.messaging_binding = None
        mock_participant.role_sid = None
        mock_participant.date_created = "2024-01-15T10:30:00Z"
        mock_participant.date_updated = "2024-01-15T10:30:00Z"
        
        mock_conversation.participants.create.return_value = mock_participant
        
        service = TwilioConversationService()
        
        result = await service.add_agent_participant(TEST_CONVERSATION_SID)
        
        assert isinstance(result, TwilioParticipant)
        assert result.identity == "ai_assistant"
        mock_conversation.participants.create.assert_called_once_with(
            identity="ai_assistant"
        )
    
    @pytest.mark.asyncio
    async def test_add_agent_participant_already_exists(self, mock_twilio_client):
        """Test agent participant addition when participant already exists."""
        mock_client, _, mock_conversation = mock_twilio_client
        
        # Mock "participant already exists" error (code 50433)
        error = TwilioRestException(status=400, uri="test", msg="Participant already exists")
        error.code = 50433
        mock_conversation.participants.create.side_effect = error
        
        service = TwilioConversationService()
        
        result = await service.add_agent_participant(TEST_CONVERSATION_SID)
        
        assert result is None  # Should return None when participant exists
    
    @pytest.mark.asyncio
    async def test_validate_webhook_signature_success(self):
        """Test successful webhook signature validation."""
        with patch('src.services.twilio_service.settings') as mock_settings:
            mock_settings.twilio.webhook_secret = "test_secret"
            
            service = TwilioConversationService()
            
            with patch('twilio.request_validator.RequestValidator') as mock_validator_class:
                mock_validator = Mock()
                mock_validator.validate.return_value = True
                mock_validator_class.return_value = mock_validator
                
                result = await service.validate_webhook_signature(
                    request_body="test=body",
                    signature="test_signature",
                    url="https://example.com/webhook"
                )
                
                assert result is True
                mock_validator.validate.assert_called_once_with(
                    "https://example.com/webhook",
                    "test=body",
                    "test_signature"
                )
    
    @pytest.mark.asyncio
    async def test_validate_webhook_signature_no_secret(self):
        """Test webhook signature validation when no secret is configured."""
        with patch('src.services.twilio_service.settings') as mock_settings:
            mock_settings.twilio.webhook_secret = None
            
            service = TwilioConversationService()
            
            result = await service.validate_webhook_signature(
                request_body="test=body",
                signature="test_signature",
                url="https://example.com/webhook"
            )
            
            assert result is True  # Should pass when no secret configured