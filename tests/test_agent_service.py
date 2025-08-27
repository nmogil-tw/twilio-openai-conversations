"""
Tests for the CustomerServiceAgent and AI agent functionality.
Tests agent initialization, message processing, tool usage, and error handling.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from src.services.agent_service import CustomerServiceAgent
from src.models.conversation import AgentResponse, MessageRole


class TestCustomerServiceAgent:
    """Test cases for CustomerServiceAgent class."""
    
    @pytest.fixture
    def mock_runner(self):
        """Mock Agents SDK Runner for testing."""
        with patch('src.services.agent_service.Runner') as mock_runner:
            mock_result = Mock()
            mock_result.final_output = "I'd be happy to help with your order!"
            mock_runner.run = AsyncMock(return_value=mock_result)
            yield mock_runner
    
    @pytest.fixture
    def mock_agent_config(self):
        """Mock agent configuration loading."""
        config = {
            "name": "Test Customer Service Assistant",
            "instructions": "You are a helpful test assistant",
            "knowledge_base": {
                "store_hours": {
                    "weekdays": "9:00 AM - 9:00 PM",
                    "saturday": "9:00 AM - 8:00 PM",
                    "sunday": "11:00 AM - 6:00 PM"
                },
                "contact_info": {
                    "customer_service": "1-800-TEST-HELP",
                    "email": "help@test.com"
                }
            },
            "fallback_responses": {
                "unknown_query": "I'm not sure about that test query."
            }
        }
        
        with patch.object(CustomerServiceAgent, '_load_agent_config', return_value=config):
            yield config
    
    def test_agent_initialization(self, mock_runner, mock_agent_config):
        """Test agent initialization with configuration."""
        agent = CustomerServiceAgent()
        
        assert agent is not None
        assert agent.config == mock_agent_config
        assert agent.main_agent is not None
        assert agent.billing_agent is not None
        assert agent.technical_agent is not None
    
    @pytest.mark.asyncio
    async def test_process_message_success(self, mock_runner, mock_agent_config):
        """Test successful message processing."""
        agent = CustomerServiceAgent()
        
        message = "Hello, I need help with my order"
        session_id = "test_session_123"
        
        response = await agent.process_message(message, session_id)
        
        assert isinstance(response, AgentResponse)
        assert response.content == "I'd be happy to help with your order!"
        assert response.confidence > 0
        assert response.processing_time_ms >= 0
        assert "model_used" in response.metadata
    
    @pytest.mark.asyncio
    async def test_process_message_with_context(self, mock_runner, mock_agent_config):
        """Test message processing with conversation context."""
        agent = CustomerServiceAgent()
        
        message = "What's my order status?"
        session_id = "test_session_123"
        context = {
            "customer_name": "John Doe",
            "recent_orders": [{"order_id": "12345", "status": "shipped"}]
        }
        
        response = await agent.process_message(message, session_id, context)
        
        assert isinstance(response, AgentResponse)
        assert response.content is not None
        assert response.metadata["session_id"] == session_id
    
    @pytest.mark.asyncio
    async def test_process_message_openai_error(self, mock_agent_config):
        """Test message processing when OpenAI API fails."""
        with patch('src.services.agent_service.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
            
            agent = CustomerServiceAgent()
            
            message = "Hello"
            session_id = "test_session_123"
            
            response = await agent.process_message(message, session_id)
            
            assert isinstance(response, AgentResponse)
            assert "fallback_used" in response.metadata
            assert response.confidence < 0.5  # Low confidence for fallback
    
    def test_lookup_order_status_found(self, mock_openai_client, mock_agent_config):
        """Test order status lookup with existing order."""
        agent = CustomerServiceAgent()
        
        # Test with mock order ID that exists in the mock data
        result = agent.lookup_order_status("12345")
        
        assert "shipped" in result.lower()
        assert "tracking" in result.lower()
        assert "thursday" in result.lower()
    
    def test_lookup_order_status_not_found(self, mock_openai_client, mock_agent_config):
        """Test order status lookup with non-existent order."""
        agent = CustomerServiceAgent()
        
        result = agent.lookup_order_status("99999")
        
        assert "couldn't find" in result.lower()
        assert "99999" in result
    
    def test_get_product_info_iphone_case(self, mock_openai_client, mock_agent_config):
        """Test product information lookup for iPhone cases."""
        agent = CustomerServiceAgent()
        
        result = agent.get_product_info("iPhone case")
        
        assert "iphone cases" in result.lower()
        assert "magsafe" in result.lower()
        assert "$29.99" in result
    
    def test_get_product_info_laptop(self, mock_openai_client, mock_agent_config):
        """Test product information lookup for laptops."""
        agent = CustomerServiceAgent()
        
        result = agent.get_product_info("laptop")
        
        assert "macbook" in result.lower()
        assert "warranty" in result.lower()
        assert "$" in result  # Contains pricing
    
    def test_get_product_info_generic(self, mock_openai_client, mock_agent_config):
        """Test product information lookup for generic product."""
        agent = CustomerServiceAgent()
        
        result = agent.get_product_info("random product")
        
        assert "website" in result.lower() or "customer service" in result.lower()
    
    def test_check_store_hours_weekday(self, mock_openai_client, mock_agent_config):
        """Test store hours lookup for weekdays."""
        agent = CustomerServiceAgent()
        
        result = agent.check_store_hours("monday")
        
        assert "9:00 AM - 9:00 PM" in result
        assert "weekdays" in result.lower()
    
    def test_check_store_hours_saturday(self, mock_openai_client, mock_agent_config):
        """Test store hours lookup for Saturday."""
        agent = CustomerServiceAgent()
        
        result = agent.check_store_hours("saturday")
        
        assert "9:00 AM - 8:00 PM" in result
        assert "saturday" in result.lower()
    
    def test_check_store_hours_general(self, mock_openai_client, mock_agent_config):
        """Test general store hours lookup."""
        agent = CustomerServiceAgent()
        
        result = agent.check_store_hours()
        
        assert "weekdays" in result.lower()
        assert "saturday" in result.lower()
        assert "sunday" in result.lower()
    
    def test_get_store_locations_specific_city(self, mock_openai_client, mock_agent_config):
        """Test store locations lookup for specific city."""
        agent = CustomerServiceAgent()
        
        result = agent.get_store_locations("San Francisco")
        
        assert "san francisco" in result.lower()
        assert "locations" in result.lower()
    
    def test_get_store_locations_general(self, mock_openai_client, mock_agent_config):
        """Test general store locations lookup."""
        agent = CustomerServiceAgent()
        
        result = agent.get_store_locations()
        
        assert "nationwide" in result.lower()
        assert "stores" in result.lower()
    
    def test_search_faq_shipping(self, mock_openai_client, mock_agent_config):
        """Test FAQ search for shipping information."""
        agent = CustomerServiceAgent()
        
        result = agent.search_faq("shipping policy")
        
        assert "shipping" in result.lower()
        assert "free" in result.lower()
        assert "$50" in result
    
    def test_search_faq_returns(self, mock_openai_client, mock_agent_config):
        """Test FAQ search for return information."""
        agent = CustomerServiceAgent()
        
        result = agent.search_faq("return policy")
        
        assert "return" in result.lower()
        assert "30-day" in result.lower()
    
    def test_search_faq_unknown(self, mock_openai_client, mock_agent_config):
        """Test FAQ search for unknown topic."""
        agent = CustomerServiceAgent()
        
        result = agent.search_faq("unknown topic")
        
        assert "customer service" in result.lower()
        assert "1-800" in result or "help" in result.lower()
    
    def test_build_system_message_basic(self, mock_openai_client, mock_agent_config):
        """Test building system message with basic instructions."""
        agent = CustomerServiceAgent()
        
        system_message = agent._build_system_message()
        
        assert mock_agent_config["instructions"] in system_message
        assert "Store Information:" in system_message
        assert "9:00 AM - 9:00 PM" in system_message  # Store hours
        assert "1-800-TEST-HELP" in system_message    # Contact info
    
    def test_build_system_message_with_context(self, mock_openai_client, mock_agent_config):
        """Test building system message with conversation context."""
        agent = CustomerServiceAgent()
        
        context = {
            "customer_name": "John Doe",
            "recent_orders": [{"order_id": "12345"}]
        }
        
        system_message = agent._build_system_message(context)
        
        assert mock_agent_config["instructions"] in system_message
        assert "Conversation Context:" in system_message
        assert "John Doe" in system_message
        assert "Recent orders: 1" in system_message
    
    @pytest.mark.asyncio
    async def test_generate_response_with_openai(self, mock_openai_client, mock_agent_config):
        """Test response generation using OpenAI API."""
        agent = CustomerServiceAgent()
        
        message = "Hello, how are you?"
        
        response = await agent._generate_response_with_openai(message)
        
        assert response["content"] == "I'd be happy to help with your order!"
        assert response["confidence"] == 0.8
        assert response["tokens_used"] == 45
        assert response["tools_used"] == []
    
    def test_load_agent_config_file_not_found(self, mock_openai_client):
        """Test agent config loading when file doesn't exist."""
        with patch('pathlib.Path.exists', return_value=False):
            agent = CustomerServiceAgent()
            
            # Should handle missing config gracefully
            assert agent.config == {}
    
    def test_load_agent_config_invalid_yaml(self, mock_openai_client):
        """Test agent config loading with invalid YAML."""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open_yaml_error()):
            
            agent = CustomerServiceAgent()
            
            # Should handle invalid YAML gracefully
            assert agent.config == {}


def mock_open_yaml_error():
    """Helper to mock YAML loading error."""
    from unittest.mock import mock_open
    import yaml
    
    def side_effect(*args, **kwargs):
        raise yaml.YAMLError("Invalid YAML")
    
    return mock_open(side_effect=side_effect)