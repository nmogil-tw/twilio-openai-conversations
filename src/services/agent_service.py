"""
OpenAI Agents SDK Service for customer service interactions.
Handles agent initialization, message processing, and multi-agent workflows.
"""

import yaml
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from agents import Agent, Runner, function_tool, SQLiteSession
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions

from config.settings import settings
from src.models.conversation import AgentResponse, MessageRole
from src.utils.logging import get_logger

logger = get_logger(__name__)


# Function tools for customer service capabilities
@function_tool
def lookup_order_status(order_id: str) -> str:
    """Look up order status by ID.
    
    Args:
        order_id: The order ID to look up
        
    Returns:
        Order status information
    """
    logger.info(f"Looking up order status for: {order_id}")
    
    # Demo implementation - replace with your order management system
    # Example integrations: Shopify, WooCommerce, custom database
    mock_orders = {
        "12345": {
            "status": "shipped",
            "tracking": "1Z123456789",
            "estimated_delivery": "Thursday"
        },
        "67890": {
            "status": "processing",
            "tracking": None,
            "estimated_delivery": "3-5 business days"
        }
    }
    
    if order_id in mock_orders:
        order = mock_orders[order_id]
        if order["status"] == "shipped":
            return f"Your order #{order_id} has shipped! Tracking: {order['tracking']}. Expected delivery: {order['estimated_delivery']}."
        else:
            return f"Your order #{order_id} is currently {order['status']}. Estimated delivery: {order['estimated_delivery']}."
    else:
        return f"I couldn't find order #{order_id}. Please check the order number and try again, or contact customer service for assistance."


@function_tool
def get_product_info(product_name: str) -> str:
    """Get product information from catalog.
    
    Args:
        product_name: Name of the product to search for
        
    Returns:
        Product information
    """
    logger.info(f"Looking up product info for: {product_name}")
    
    # Demo implementation - replace with your product catalog system
    
    # Mock product data
    if "iphone" in product_name.lower() and "case" in product_name.lower():
        return "iPhone cases available: Clear MagSafe ($29.99), Leather ($49.99), Silicone ($39.99). All cases compatible with wireless charging."
    elif "laptop" in product_name.lower() or "macbook" in product_name.lower():
        return "MacBook models: MacBook Air M3 (from $1,099), MacBook Pro 14\" (from $1,599), MacBook Pro 16\" (from $2,499). All include 1-year warranty."
    else:
        return f"For detailed information about '{product_name}', please visit our website or contact customer service at 1-800-ACME-HELP."


@function_tool
def check_store_hours(day: Optional[str] = None) -> str:
    """Check store hours.
    
    Args:
        day: Specific day to check (optional)
        
    Returns:
        Store hours information
    """
    logger.info(f"Checking store hours for: {day or 'general'}")
    
    hours = {
        "weekdays": "9:00 AM - 9:00 PM",
        "saturday": "9:00 AM - 8:00 PM", 
        "sunday": "11:00 AM - 6:00 PM"
    }
    
    if day and day.lower() in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
        return f"We're open weekdays from {hours['weekdays']}."
    elif day and day.lower() == "saturday":
        return f"We're open Saturday from {hours['saturday']}."
    elif day and day.lower() == "sunday":
        return f"We're open Sunday from {hours['sunday']}."
    else:
        return f"Store hours: Weekdays {hours['weekdays']}, Saturday {hours['saturday']}, Sunday {hours['sunday']}."


@function_tool
def get_store_locations(city: Optional[str] = None) -> str:
    """Get store locations.
    
    Args:
        city: City to search for stores (optional)
        
    Returns:
        Store location information
    """
    logger.info(f"Looking up store locations for: {city or 'all locations'}")
    
    if city:
        return f"We have several locations in {city}. For specific addresses and directions, please visit our website store locator or call 1-800-ACME-HELP."
    else:
        return "We have stores nationwide in major cities. Use our website store locator or call 1-800-ACME-HELP to find the nearest location."


@function_tool
def search_faq(query: str) -> str:
    """Search frequently asked questions.
    
    Args:
        query: The question or topic to search for
        
    Returns:
        FAQ response
    """
    logger.info(f"Searching FAQ for: {query}")
    
    query_lower = query.lower()
    
    if "shipping" in query_lower or "delivery" in query_lower:
        return "Shipping: Free standard shipping on orders over $50. Standard delivery: 3-5 business days. Express shipping available for $9.99 (1-2 days)."
    elif "return" in query_lower or "refund" in query_lower:
        return "Returns: 30-day return policy for unused items in original packaging. Free returns by mail or at any store location. Refunds processed within 5-7 business days."
    elif "warranty" in query_lower:
        return "All products come with manufacturer warranty. Extended warranty options available at purchase. For warranty claims, contact customer service."
    else:
        return "For more information, please contact our customer service team at 1-800-ACME-HELP or visit our FAQ section on the website."


class CustomerServiceAgentManager:
    """
    Manager for OpenAI Agents SDK based customer service system.
    
    Provides multi-agent architecture with:
    - Main triage agent for general inquiries
    - Specialized agents for billing, technical support, etc.
    - Built-in tool integration and handoffs
    - Session management for conversation memory
    """
    
    def __init__(self):
        """Initialize the agent system with multi-agent architecture."""
        self.config = self._load_agent_config()
        
        # Create specialized agents
        self.billing_agent = self._create_billing_agent()
        self.technical_agent = self._create_technical_agent()
        self.main_agent = self._create_main_agent()
        
        logger.info("Customer service agent system initialized successfully")
    
    def _create_main_agent(self) -> Agent:
        """Create the main customer service agent."""
        instructions = self.config.get("instructions", 
            "You are a helpful customer service assistant. Be friendly, professional, and concise. "
            "Use your tools to help customers with orders, products, and general questions. "
            "If you need specialized help, you can handoff to billing or technical support agents."
        )
        
        return Agent(
            name="Customer Service Assistant",
            instructions=prompt_with_handoff_instructions(instructions),
            model=settings.openai.model,
            tools=[
                lookup_order_status,
                get_product_info,
                check_store_hours,
                get_store_locations,
                search_faq
            ],
            handoffs=[self.billing_agent, self.technical_agent]
        )
    
    def _create_billing_agent(self) -> Agent:
        """Create a specialized billing agent."""
        return Agent(
            name="Billing Support",
            handoff_description="Specialist for billing, payment, and invoice questions",
            instructions=prompt_with_handoff_instructions(
                "You are a billing specialist. Help with payment issues, invoices, billing questions, "
                "refunds, and payment method problems. Be clear about billing policies and next steps."
            ),
            model=settings.openai.model,
            tools=[lookup_order_status, search_faq]  # Billing-relevant tools
        )
    
    def _create_technical_agent(self) -> Agent:
        """Create a specialized technical support agent."""
        return Agent(
            name="Technical Support",
            handoff_description="Specialist for technical issues, troubleshooting, and product setup",
            instructions=prompt_with_handoff_instructions(
                "You are a technical support specialist. Help with product setup, troubleshooting, "
                "technical issues, and product usage questions. Provide step-by-step guidance."
            ),
            model=settings.openai.model,
            tools=[get_product_info, search_faq]  # Tech-relevant tools
        )
    
    def _load_agent_config(self) -> Dict[str, Any]:
        """Load agent configuration from YAML file."""
        try:
            config_path = Path(settings.agent.config_file_path)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                return config.get('customer_service_agent', {})
            else:
                logger.warning(f"Agent config file not found: {config_path}")
                return {}
        except Exception as e:
            logger.error(f"Failed to load agent config: {e}")
            return {}
    
    async def process_message(
        self, 
        message: str, 
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Process a customer message using the OpenAI Agents SDK.
        
        Args:
            message: Customer message text
            session_id: Unique session identifier  
            context: Additional conversation context
            
        Returns:
            AgentResponse with generated content and metadata
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Processing message for session {session_id}: {message[:100]}...")
            
            # Create or get existing session for conversation memory
            session = SQLiteSession(session_id, "data/conversations.db")
            
            # Run the main agent with the message
            result = await Runner.run(
                self.main_agent,
                input=message,
                session=session
            )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Extract tools used from result metadata if available
            tools_used = []
            if hasattr(result, 'tool_calls'):
                tools_used = [call.get('function', {}).get('name', 'unknown') 
                             for call in result.tool_calls or []]
            
            agent_response = AgentResponse(
                content=str(result.final_output),
                confidence=0.8,  # SDK doesn't provide confidence scores by default
                tools_used=tools_used,
                processing_time_ms=int(processing_time),
                metadata={
                    "model_used": settings.openai.model,
                    "session_id": session_id,
                    "timestamp": start_time.isoformat(),
                    "agent_used": getattr(result, 'agent_name', 'Customer Service Assistant')
                }
            )
            
            logger.info(f"Generated response for session {session_id} in {processing_time:.0f}ms")
            return agent_response
            
        except Exception as e:
            logger.error(f"Error processing message for session {session_id}: {e}")
            
            # Return fallback response
            fallback_content = (
                "I'm experiencing some technical difficulties right now. "
                "Please try again in a moment or contact customer service at 1-800-ACME-HELP."
            )
            
            return AgentResponse(
                content=fallback_content,
                confidence=0.1,
                tools_used=[],
                processing_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                metadata={"error": str(e), "fallback_used": True}
            )


# Backward compatibility - this matches the original class name expected by webhook handler
CustomerServiceAgent = CustomerServiceAgentManager