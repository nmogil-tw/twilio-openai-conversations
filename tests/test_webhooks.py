"""
Tests for webhook handling and FastAPI endpoints.
Tests webhook processing, validation, and response generation.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
import json

from src.main import app
from src.models.webhook import WebhookRequest, WebhookResponse
from tests.conftest import (
    TEST_CONVERSATION_SID, TEST_SERVICE_SID, TEST_MESSAGE_SID,
    TEST_PARTICIPANT_SID, TEST_ACCOUNT_SID
)


class TestWebhookHandlers:
    """Test cases for webhook endpoint handlers."""
    
    @pytest.fixture
    def client(self):
        """Provide test client for FastAPI app."""
        return TestClient(app)
    
    @pytest.fixture
    def valid_webhook_data(self):
        """Provide valid webhook form data."""
        return {
            "EventType": "onMessageAdd",
            "AccountSid": TEST_ACCOUNT_SID,
            "ServiceSid": TEST_SERVICE_SID,
            "ConversationSid": TEST_CONVERSATION_SID,
            "MessageSid": TEST_MESSAGE_SID,
            "ParticipantSid": TEST_PARTICIPANT_SID,
            "Author": "customer_12345",
            "Body": "Hello, I need help with my order #12345",
            "MessageIndex": "1"
        }
    
    @pytest.fixture
    def mock_services(self):
        """Mock all required services."""
        with patch('src.handlers.webhook_handler.agent_service') as mock_agent, \
             patch('src.handlers.webhook_handler.twilio_service') as mock_twilio, \
             patch('src.handlers.webhook_handler.session_service') as mock_session:
            
            # Mock agent service
            mock_agent_response = Mock()
            mock_agent_response.content = "I'd be happy to help with your order!"
            mock_agent_response.confidence = 0.95
            mock_agent_response.tools_used = ["lookup_order_status"]
            mock_agent_response.processing_time_ms = 1250
            mock_agent.process_message = AsyncMock(return_value=mock_agent_response)
            
            # Mock Twilio service
            mock_twilio_message = Mock()
            mock_twilio_message.sid = "IMresponse123456789012345678901234"
            mock_twilio.send_message = AsyncMock(return_value=mock_twilio_message)
            mock_twilio.check_conversation_eligibility = AsyncMock(return_value={
                "eligible": True,
                "reason": "eligible"
            })
            mock_twilio.set_typing_indicator = AsyncMock(return_value=True)
            mock_twilio.validate_webhook_signature = AsyncMock(return_value=True)
            
            # Mock session service
            mock_session_obj = Mock()
            mock_session_obj.session_id = f"conv_{TEST_CONVERSATION_SID}"
            mock_session_obj.context.dict.return_value = {}
            mock_session.get_or_create_session = AsyncMock(return_value=mock_session_obj)
            mock_session.add_message_to_session = AsyncMock(return_value=True)
            
            yield {
                'agent': mock_agent,
                'twilio': mock_twilio,
                'session': mock_session
            }
    
    def test_message_added_webhook_success(self, client, valid_webhook_data, mock_services):
        """Test successful message-added webhook processing."""
        response = client.post(
            "/webhook/message-added",
            data=valid_webhook_data,
            headers={
                "X-Twilio-Signature": "valid_signature",
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["agent_responded"] is True
        assert "processing_time_ms" in data
        
        # Verify services were called
        mock_services['twilio'].check_conversation_eligibility.assert_called_once()
        mock_services['agent'].process_message.assert_called_once()
        mock_services['twilio'].send_message.assert_called_once()
    
    def test_message_added_webhook_invalid_signature(self, client, valid_webhook_data):
        """Test webhook with invalid signature."""
        with patch('src.handlers.webhook_handler.twilio_service') as mock_twilio:
            mock_twilio.validate_webhook_signature = AsyncMock(return_value=False)
            
            response = client.post(
                "/webhook/message-added",
                data=valid_webhook_data,
                headers={
                    "X-Twilio-Signature": "invalid_signature",
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )
            
            assert response.status_code == 403
    
    def test_message_added_webhook_missing_data(self, client, mock_services):
        """Test webhook with missing required data."""
        incomplete_data = {
            "EventType": "onMessageAdd",
            "AccountSid": TEST_ACCOUNT_SID
            # Missing other required fields
        }
        
        response = client.post(
            "/webhook/message-added",
            data=incomplete_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200  # Still returns 200 but with error
        
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == "validation_error"
    
    def test_message_added_webhook_assistant_message(self, client, valid_webhook_data, mock_services):
        """Test webhook processing for assistant's own message (should skip)."""
        # Modify to be from assistant
        valid_webhook_data["Author"] = "assistant"
        
        response = client.post(
            "/webhook/message-added",
            data=valid_webhook_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["agent_responded"] is False
        assert "not processed by agent" in data["message"]
    
    def test_message_added_webhook_empty_body(self, client, valid_webhook_data, mock_services):
        """Test webhook processing for message with empty body."""
        valid_webhook_data["Body"] = ""
        
        response = client.post(
            "/webhook/message-added",
            data=valid_webhook_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["agent_responded"] is False
    
    def test_message_added_webhook_conversation_not_eligible(self, client, valid_webhook_data, mock_services):
        """Test webhook when conversation is not eligible for agent processing."""
        # Mock conversation as not eligible
        mock_services['twilio'].check_conversation_eligibility = AsyncMock(return_value={
            "eligible": False,
            "reason": "human_agent_present"
        })
        
        response = client.post(
            "/webhook/message-added",
            data=valid_webhook_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["agent_responded"] is False
        assert "not eligible" in data["message"]
    
    def test_message_added_webhook_twilio_send_error(self, client, valid_webhook_data, mock_services):
        """Test webhook when Twilio message sending fails."""
        # Mock Twilio send failure
        mock_services['twilio'].send_message = AsyncMock(return_value=None)
        
        response = client.post(
            "/webhook/message-added",
            data=valid_webhook_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert data["agent_responded"] is False
        assert data["error_code"] == "twilio_send_error"
    
    def test_message_added_webhook_agent_error(self, client, valid_webhook_data, mock_services):
        """Test webhook when agent processing fails."""
        # Mock agent failure
        mock_services['agent'].process_message = AsyncMock(side_effect=Exception("Agent error"))
        
        response = client.post(
            "/webhook/message-added",
            data=valid_webhook_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == "agent_processing_error"
    
    def test_participant_added_webhook(self, client):
        """Test participant-added webhook handling."""
        webhook_data = {
            "EventType": "onParticipantAdd",
            "AccountSid": TEST_ACCOUNT_SID,
            "ServiceSid": TEST_SERVICE_SID,
            "ConversationSid": TEST_CONVERSATION_SID,
            "ParticipantSid": TEST_PARTICIPANT_SID,
            "Identity": "customer_67890"
        }
        
        response = client.post(
            "/webhook/participant-added",
            data=webhook_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "Participant added" in data["message"]
    
    def test_participant_removed_webhook(self, client):
        """Test participant-removed webhook handling."""
        webhook_data = {
            "EventType": "onParticipantRemove",
            "AccountSid": TEST_ACCOUNT_SID,
            "ServiceSid": TEST_SERVICE_SID,
            "ConversationSid": TEST_CONVERSATION_SID,
            "ParticipantSid": TEST_PARTICIPANT_SID,
            "Identity": "customer_67890"
        }
        
        response = client.post(
            "/webhook/participant-removed",
            data=webhook_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "Participant removed" in data["message"]
    
    def test_conversation_state_updated_webhook(self, client):
        """Test conversation-state-updated webhook handling."""
        webhook_data = {
            "EventType": "onConversationStateUpdate",
            "AccountSid": TEST_ACCOUNT_SID,
            "ServiceSid": TEST_SERVICE_SID,
            "ConversationSid": TEST_CONVERSATION_SID,
            "State": "closed"
        }
        
        response = client.post(
            "/webhook/conversation-state-updated",
            data=webhook_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "Conversation state update" in data["message"]
    
    def test_webhook_test_endpoint(self, client):
        """Test webhook test endpoint."""
        response = client.get("/webhook/test")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "working" in data["message"]
        assert "timestamp" in data
        assert data["service"] == "twilio-openai-conversations"
    
    @pytest.mark.asyncio
    async def test_typing_indicator_timeout(self):
        """Test typing indicator timeout functionality."""
        from src.handlers.webhook_handler import set_typing_indicator_with_timeout
        
        with patch('src.handlers.webhook_handler.twilio_service') as mock_twilio:
            mock_twilio.set_typing_indicator = AsyncMock(return_value=True)
            
            # Test with very short timeout
            await set_typing_indicator_with_timeout(
                TEST_CONVERSATION_SID,
                TEST_PARTICIPANT_SID,
                0.01  # 10ms timeout
            )
            
            # Should have been called twice: once to set, once to clear
            assert mock_twilio.set_typing_indicator.call_count == 2
            
            # First call should set typing to True
            first_call = mock_twilio.set_typing_indicator.call_args_list[0]
            assert first_call[0][2] is True  # is_typing=True
            
            # Second call should set typing to False
            second_call = mock_twilio.set_typing_indicator.call_args_list[1]
            assert second_call[0][2] is False  # is_typing=False
    
    def test_webhook_request_model_validation(self):
        """Test WebhookRequest model validation."""
        # Valid webhook data
        valid_data = {
            "EventType": "onMessageAdd",
            "AccountSid": TEST_ACCOUNT_SID,
            "ServiceSid": TEST_SERVICE_SID,
            "ConversationSid": TEST_CONVERSATION_SID,
            "MessageSid": TEST_MESSAGE_SID,
            "Body": "Test message"
        }
        
        webhook = WebhookRequest(**valid_data)
        assert webhook.EventType == "onMessageAdd"
        assert webhook.should_process_with_agent() is True
    
    def test_webhook_request_should_not_process_assistant(self):
        """Test that assistant messages are not processed."""
        data = {
            "EventType": "onMessageAdd",
            "AccountSid": TEST_ACCOUNT_SID,
            "ServiceSid": TEST_SERVICE_SID,
            "ConversationSid": TEST_CONVERSATION_SID,
            "Author": "assistant",
            "Body": "Assistant response"
        }
        
        webhook = WebhookRequest(**data)
        assert webhook.should_process_with_agent() is False
    
    def test_webhook_request_should_not_process_empty_body(self):
        """Test that empty message bodies are not processed."""
        data = {
            "EventType": "onMessageAdd",
            "AccountSid": TEST_ACCOUNT_SID,
            "ServiceSid": TEST_SERVICE_SID,
            "ConversationSid": TEST_CONVERSATION_SID,
            "Body": ""
        }
        
        webhook = WebhookRequest(**data)
        assert webhook.should_process_with_agent() is False
    
    def test_webhook_request_participant_event(self):
        """Test participant event identification."""
        data = {
            "EventType": "onParticipantAdd",
            "AccountSid": TEST_ACCOUNT_SID,
            "ServiceSid": TEST_SERVICE_SID,
            "ConversationSid": TEST_CONVERSATION_SID,
            "Identity": "customer_123"
        }
        
        webhook = WebhookRequest(**data)
        assert webhook.is_participant_event() is True
        assert webhook.is_message_event() is False
    
    def test_webhook_response_model(self):
        """Test WebhookResponse model."""
        response = WebhookResponse(
            success=True,
            message="Webhook processed successfully",
            processing_time_ms=1250,
            agent_responded=True
        )
        
        assert response.success is True
        assert response.agent_responded is True
        assert response.processing_time_ms == 1250
        assert response.error_code is None