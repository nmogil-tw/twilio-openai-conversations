# Product Requirements Document: Twilio Conversations + OpenAI Agents SDK Integration

## 1. Overview

### 1.1 Purpose
Create a reference implementation demonstrating how Twilio customers can integrate the OpenAI Agents Python SDK with Twilio's Conversations API to build intelligent customer service chatbots that operate across SMS, WhatsApp, and other channels.

### 1.2 Goals
- **Primary**: Provide a production-ready template for AI-powered customer service
- **Secondary**: Demonstrate best practices for Twilio Conversations API integration
- **Tertiary**: Showcase OpenAI Agents SDK capabilities in a real-world scenario

### 1.3 Success Criteria
- Handles customer inquiries across multiple channels seamlessly
- Maintains conversation context and history
- Provides clear, helpful responses for common customer inquiries
- Easy to deploy and configure for Twilio customers
- Well-documented with clear setup instructions

## 2. Architecture Overview

### 2.1 System Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Customer      │    │   Twilio         │    │   Python        │
│   (SMS/WhatsApp)│◄──►│   Conversations  │◄──►│   Application   │
└─────────────────┘    │   API            │    │                 │
                       └──────────────────┘    │   ┌─────────────┐
                                               │   │ Webhook     │
                       ┌──────────────────┐    │   │ Handler     │
                       │   OpenAI         │◄──►│   └─────────────┘
                       │   Agents SDK     │    │   ┌─────────────┐
                       └──────────────────┘    │   │ Agent       │
                                               │   │ Service     │
                                               │   └─────────────┘
                                               │   ┌─────────────┐
                                               │   │ Twilio      │
                                               │   │ Service     │
                                               │   └─────────────┘
                                               └─────────────────┘
```

### 2.2 Technology Stack
- **Backend Framework**: FastAPI (async-native, auto-documentation)
- **AI Framework**: OpenAI Agents Python SDK
- **Communication**: Twilio Conversations API
- **Session Storage**: SQLite (local) / PostgreSQL (production)
- **Configuration**: Environment variables + YAML
- **Logging**: Structured logging with JSON output
- **Testing**: pytest with async support
- **Deployment**: Docker + docker-compose

## 3. Detailed Design

### 3.1 Project Structure
```
twilio-openai-conversations/
├── README.md
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── agent_config.yml
├── src/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── models/
│   │   ├── __init__.py
│   │   ├── conversation.py     # Data models
│   │   └── webhook.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── agent_service.py    # OpenAI Agent logic
│   │   ├── twilio_service.py   # Twilio API interactions
│   │   └── session_service.py  # Session management
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── webhook_handler.py  # Webhook endpoints
│   │   └── health_handler.py   # Health checks
│   └── utils/
│       ├── __init__.py
│       ├── logging.py
│       └── security.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_agent_service.py
│   ├── test_twilio_service.py
│   └── test_webhooks.py
├── docs/
│   ├── setup.md
│   ├── configuration.md
│   └── deployment.md
└── scripts/
    ├── setup.sh
    └── deploy.sh
```

### 3.2 Core Components

#### 3.2.1 Agent Service (`src/services/agent_service.py`)
```python
class CustomerServiceAgent:
    """
    Intelligent customer service agent with:
    - Product knowledge base
    - Order status lookup
    - Store information
    - FAQ responses
    """
    
    def __init__(self):
        self.agent = Agent(
            name="Customer Service Assistant",
            instructions=self._load_instructions(),
            tools=[
                self.lookup_order_status,
                self.check_store_hours,
                self.get_product_info,
                self.get_store_locations
            ]
        )
    
    async def process_message(self, message: str, session_id: str) -> AgentResponse:
        """Process customer message and return response"""
        
    @function_tool
    def lookup_order_status(self, order_id: str) -> str:
        """Look up order status by ID"""
        
    @function_tool  
    def get_store_locations(self, city: str = None) -> str:
        """Get store locations, optionally filtered by city"""
```

#### 3.2.2 Twilio Service (`src/services/twilio_service.py`)
```python
class TwilioConversationService:
    """
    Handles all Twilio Conversations API interactions:
    - Message sending/receiving
    - Conversation management
    - Participant management
    - Typing indicators
    """
    
    async def send_message(self, service_sid: str, conversation_sid: str, 
                          message: str, author: str = "assistant"):
        """Send message via Conversations API"""
        
    async def set_typing_indicator(self, service_sid: str, conversation_sid: str, 
                                 is_typing: bool):
        """Set/clear typing indicator"""
        
    async def check_conversation_state(self, service_sid: str, conversation_sid: str) -> ConversationState:
        """Check if conversation should be handled by AI"""
```

#### 3.2.3 Webhook Handler (`src/handlers/webhook_handler.py`)
```python
@router.post("/webhook/message-added")
async def handle_message_added(request: WebhookRequest):
    """
    Handle incoming messages from Twilio Conversations
    
    Flow:
    1. Validate webhook signature
    2. Check conversation eligibility (single participant)
    3. Set typing indicator
    4. Process through AI agent
    5. Send response
    6. Clear typing indicator
    """
```

### 3.3 Configuration Management

#### 3.3.1 Environment Configuration (`.env`)
```env
# Twilio Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_CONVERSATIONS_SERVICE_SID=ISxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# OpenAI Configuration  
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini

# Application Configuration
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./conversations.db

# Security
WEBHOOK_SECRET=your_webhook_secret_for_signature_validation
```

#### 3.3.2 Agent Configuration (`config/agent_config.yml`)
```yaml
customer_service_agent:
  name: "Customer Service Assistant"
  model: "gpt-4o-mini"
  instructions: |
    You are a helpful customer service assistant for Acme Corp.
    
    ## Your Capabilities:
    - Look up order status using order numbers
    - Provide product information
    - Check store hours and locations
    - Answer frequently asked questions
    
    ## Guidelines:
    - Be friendly, professional, and concise
    - Always ask for order numbers when helping with orders
    - If you don't know something, politely say so and suggest contacting customer service
    - Keep responses under 160 characters when possible for SMS
    
  tools:
    - lookup_order_status
    - get_product_info
    - check_store_hours
    - get_store_locations
    
  fallback_responses:
    - unknown_query: "I'm not sure about that. For more complex questions, please contact our customer service at 1-800-ACME-HELP."
    - billing_issues: "For billing questions, please contact our billing department at billing@acme.com or 1-800-ACME-BILL."
    - returns_refunds: "For returns and refunds, please visit acme.com/returns or contact customer service at 1-800-ACME-HELP."
```

## 4. Implementation Details

### 4.1 Customer Service Use Cases

#### 4.1.1 Primary Use Cases
1. **Order Status Inquiries**
   - Customer provides order number
   - Agent looks up status in mock database
   - Provides tracking information and estimated delivery

2. **Product Information**
   - Customer asks about products
   - Agent provides details from knowledge base
   - Can suggest alternatives or related products

3. **Store Information**
   - Hours of operation
   - Location details
   - Contact information

4. **General FAQ**
   - Shipping policies
   - Return policies
   - Contact information
   - Business hours

#### 4.1.2 Conversation Flow Examples

**Example 1: Order Status**
```
Customer: "Hi, can you check my order status? Order #12345"
Agent: "I'd be happy to help! Let me look up order #12345... Your order shipped yesterday and should arrive by Thursday. Tracking: 1Z123456789"

Customer: "Great, thank you!"
Agent: "You're welcome! Is there anything else I can help you with today?"
```

**Example 2: Product Information**
```
Customer: "Do you have the new iPhone cases in stock?"
Agent: "Yes! We have iPhone 15 cases in several colors and styles. Our most popular is the Clear MagSafe case for $29.99. Would you like me to check availability at a specific store?"

Customer: "What about the leather ones?"
Agent: "We have premium leather cases in black, brown, and navy for $49.99. They're available at most locations. Would you like me to find the nearest store?"
```

### 4.2 Session Management

```python
class ConversationSession:
    """
    Manages conversation context and history
    """
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.sqlite_session = SQLiteSession(session_id)
        self.conversation_context = {}
    
    async def add_context(self, key: str, value: any):
        """Add contextual information (customer info, order history, etc.)"""
        
    async def get_history(self) -> List[Message]:
        """Retrieve conversation history"""
        
    async def get_context_summary(self) -> str:
        """Get a summary of the conversation context for better responses"""
```

### 4.3 Error Handling & Resilience

#### 4.3.1 Error Categories
1. **Twilio API Errors**: Rate limits, authentication, service unavailable
2. **OpenAI API Errors**: Rate limits, model unavailable, token limits  
3. **Application Errors**: Database connectivity, configuration issues
4. **Webhook Validation**: Invalid signatures, malformed payloads

#### 4.3.2 Fallback Strategies
```python
class ErrorHandler:
    async def handle_agent_error(self, error: Exception, context: ConversationContext):
        """Handle OpenAI Agent failures with graceful fallbacks"""
        fallback_responses = {
            RateLimitError: "I'm experiencing high volume right now. Please try again in a moment.",
            ModelUnavailableError: "I'm temporarily unavailable. Please contact customer service at 1-800-ACME-HELP.",
            TokenLimitError: "This conversation has gotten quite long. For complex issues, please contact customer service at 1-800-ACME-HELP."
        }
        
    async def handle_twilio_error(self, error: Exception, context: ConversationContext):
        """Handle Twilio API failures with retry logic"""
```

### 4.4 Monitoring & Observability

#### 4.4.1 Metrics to Track
- Message processing latency
- Agent response accuracy (customer satisfaction)
- Query resolution rates
- Error rates by type
- API usage and costs

#### 4.4.2 Logging Structure
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "event": "message_processed",
  "conversation_sid": "CHxxxxxxxxxxxxx",
  "service_sid": "ISxxxxxxxxxxxxx", 
  "processing_time_ms": 1250,
  "agent_response_length": 145,
  "query_resolved": true,
  "tools_used": ["lookup_order_status"]
}
```

## 5. Security Considerations

### 5.1 Webhook Security
- Validate Twilio webhook signatures
- Use HTTPS for all webhook endpoints
- Implement rate limiting

### 5.2 Data Protection
- Don't log sensitive customer information
- Encrypt session data at rest
- Implement data retention policies
- Comply with privacy regulations (GDPR, CCPA)

### 5.3 API Security
- Secure API key storage (environment variables)
- Implement proper authentication for admin endpoints
- Use least-privilege access principles

## 6. Testing Strategy

### 6.1 Unit Tests
- Agent response generation
- Twilio service methods
- Session management
- Error handling

### 6.2 Integration Tests  
- End-to-end webhook flow
- Twilio API integration
- OpenAI Agent integration
- Database operations

### 6.3 Performance Tests
- Message processing latency
- Concurrent conversation handling
- Memory usage under load

## 7. Deployment & Operations

### 7.1 Local Development
```bash
# Setup
git clone https://github.com/twilio/twilio-openai-conversations
cd twilio-openai-conversations
cp .env.example .env
# Edit .env with your credentials

# Run
docker-compose up -d
# Or
python -m uvicorn src.main:app --reload

# Expose webhook with ngrok
ngrok http 8000
```

### 7.2 Production Deployment
- Docker containerization
- Environment-specific configuration
- Health checks and monitoring
- Horizontal scaling considerations
- Database migration strategy

### 7.3 Configuration Management
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  app:
    build: .
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/conversations
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: conversations
      
  redis:
    image: redis:7-alpine
```

## 8. Documentation Requirements

### 8.1 Setup Guide (`docs/setup.md`)
- Prerequisites and dependencies
- Environment setup
- Twilio configuration steps
- OpenAI API key setup
- Testing the integration

### 8.2 Configuration Guide (`docs/configuration.md`)
- Environment variables reference
- Agent customization
- Adding new tools/capabilities
- Webhook configuration

### 8.3 Deployment Guide (`docs/deployment.md`)
- Local development setup
- Production deployment options
- Monitoring and logging setup
- Troubleshooting common issues

## 9. Success Metrics

### 9.1 Technical Metrics
- 99.9% webhook processing success rate
- <2 second average response time
- >90% query resolution rate for supported use cases
- Zero data security incidents

### 9.2 Business Metrics
- Customer satisfaction scores
- Resolution rate for common inquiries
- Self-service adoption rates
- Cost per conversation

## 10. Future Enhancements

### 10.1 Short Term (Next 3 months)
- Multi-language support
- Rich media responses (images, quick replies)
- Integration with CRM systems
- Advanced analytics dashboard

### 10.2 Long Term (6-12 months)
- Voice conversation support
- Sentiment analysis and routing
- Machine learning for response optimization
- Integration with human handoff systems for complex scenarios

---

This PRD provides a comprehensive blueprint for implementing a production-ready integration between Twilio's Conversations API and OpenAI's Agents Python SDK, specifically designed to help Twilio customers build intelligent customer service solutions.