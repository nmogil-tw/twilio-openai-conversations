# Twilio Conversations + OpenAI Integration

> **⚠️ REFERENCE ARCHITECTURE ONLY**  
> This is a reference implementation demonstrating how to integrate Twilio Conversations with AI agents using OpenAI's Agents SDK. **This code is not production-ready** and is intended for educational and prototyping purposes. See the [Production Security Checklist](#production-security-checklist) for requirements before deploying to production.

Build AI-powered customer chatbots that work across SMS, WhatsApp, and messaging channels using Twilio Conversations API and OpenAI.

## What You Get

- **Intelligent AI Assistant** - Handles customer inquiries naturally with OpenAI
- **Multi-Channel Support** - Works on SMS, WhatsApp, Web Chat, and **Voice Calls**
- **Natural Voice Conversations** - Voice interstitials for smooth, human-like phone interactions
- **Built-in Tools** - Order lookup, product search, store hours, FAQ responses
- **Real-time Voice Streaming** - WebSocket-based voice communication with TwiML generation
- **Security Considerations** - Includes production security checklist and monitoring guidance
- **5-minute Setup** - Get started quickly with automated scripts

## Quick Start

### Step 1: Setup
```bash
git clone https://github.com/twilio/twilio-openai-conversations.git
cd twilio-openai-conversations
./scripts/setup.sh
```

### Step 2: Configure
Add your credentials to `.env`:
```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_CONVERSATIONS_SERVICE_SID=ISxxxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxx

# Voice Configuration (for voice call support)
NGROK_DOMAIN=your-ngrok-domain.ngrok.app
VOICE_WELCOME_GREETING="Hi! I am your voice assistant. Ask me anything!"
VOICE_INTERSTITIALS_ENABLED=true
```

### Step 3: Run
```bash
# Start the app
docker-compose up

# In another terminal, expose webhooks
ngrok http 8000
```

### Step 4: Configure Webhooks
Update your Conversations service to use the ngrok URL:

```bash
# Copy your ngrok URL (e.g., https://abc123.ngrok.app)
# Then configure the webhook:
twilio api:conversations:v1:services:configuration:webhooks:update \
    --path-sid ISxxxxxxxxxxxxx \
    --pre-webhook-url https://abc123.ngrok.app/webhook/message-added \
    --method POST \
    --filters onMessageAdded \
    --filters onParticipantAdded \
    --filters onConversationStateUpdated
```

**Done!** Text your Twilio number to chat with your AI assistant.

### Step 5: Configure Voice Calls (Optional)

For voice call support, configure your Twilio phone number:

```bash
# Set your phone number webhook to use TwiML endpoint
twilio phone-numbers:update +1234567890 \
    --voice-url https://abc123.ngrok.app/voice/twiml \
    --voice-method POST
```

**Test Voice:** Call your Twilio number and try:
- "What's my order status?"
- "Do you have iPhone cases?"

You'll hear natural interstitials like "Let me check on that order for you" before the AI response.

## Example Conversations

**Order Status:**
```
Customer: "Hi, can you check my order #12345?"
AI: "Your order shipped yesterday! Tracking: 1Z123456789. Expected delivery: Thursday."
```

**Product Info:**
```
Customer: "Do you have iPhone 15 cases?"
AI: "Yes! We have iPhone 15 cases in several styles. Most popular is the Clear MagSafe case for $29.99."
```

**Voice Call with Interstitials:**
```
Customer: "What's my order status?"
AI: "Let me check on that order for you." (plays immediately)
AI: "Your order shipped yesterday! Tracking: 1Z123456789. Expected delivery: Thursday."
```

## How It Works

```
┌─────────────────┐     ┌─────────────────────────┐     ┌──────────────────┐
│    Customer     │────►│  Twilio Conversations   │────►│   FastAPI App    │
│                 │     │        Service          │     │   (Webhooks)     │
│ • SMS Messages  │     │                         │     │                  │
│ • WhatsApp      │     │ • Message Routing       │     │ • Signature      │
│ • Web Chat      │     │ • Multi-Channel         │     │   Validation     │
│                 │     │ • Participant Mgmt      │     │ • Rate Limiting  │
└─────────────────┘     └─────────────────────────┘     └──────────────────┘
        │                                                         │
        │               ┌─────────────────────────┐               │
        └──────────────►│  Twilio Voice Calls     │──────────────►│
                        │                         │               │
                        │ • TwiML Generation      │               │
                        │ • ConversationRelay     │               │
                        │ • WebSocket Connection  │               │
                        │ • Voice Interstitials   │               │
                        └─────────────────────────┘               │
                                                                    │
                                                                    ▼
                        ┌────────────────────────────────────────────────────────┐
                        │                OpenAI Agents SDK                       │
                        │                                                        │
                        │  ┌──────────────────┐    ┌─────────────────────────┐  │
                        │  │   Triage Agent   │───►│    Specialist Agents    │  │
                        │  │                  │    │                         │  │
                        │  │ • Route Requests │    │ ┌─────────────────────┐ │  │
                        │  │ • Context Analysis│    │ │   Billing Agent     │ │  │
                        │  │ • Intent Detection│    │ │ • Invoice Lookup    │ │  │
                        │  │                  │    │ │ • Payment Issues    │ │  │
                        │  └──────────────────┘    │ └─────────────────────┘ │  │
                        │           │              │                         │  │
                        │           │              │ ┌─────────────────────┐ │  │
                        │           │              │ │  Technical Support  │ │  │
                        │           │              │ │ • Setup Help        │ │  │
                        │           ▼              │ │ • Troubleshooting   │ │  │
                        │  ┌──────────────────┐    │ └─────────────────────┘ │  │
                        │  │  Function Tools  │    │                         │  │
                        │  │                  │    │ ┌─────────────────────┐ │  │
                        │  │ • Order Lookup   │    │ │   General Helper    │ │  │
                        │  │ • Product Search │    │ │ • FAQ Responses     │ │  │
                        │  │ • Store Hours    │    │ │ • Information       │ │  │
                        │  │ • FAQ Database   │    │ └─────────────────────┘ │  │
                        │  └──────────────────┘    └─────────────────────────┘  │
                        └────────────────────────────────────────────────────────┘
                                                    │
                                                    ▼
                        ┌────────────────────────────────────────────────────────┐
                        │                 Persistent Storage                     │
                        │                                                        │
                        │  ┌─────────────────┐    ┌─────────────────────────────┐ │
                        │  │ Session Storage │    │      Database Storage       │ │
                        │  │                 │    │                             │ │
                        │  │ • Active Chats  │    │ • Conversation History      │ │
                        │  │ • User Context  │    │ • Agent Handoffs            │ │
                        │  │ • Agent State   │    │ • Performance Metrics       │ │
                        │  │ (Redis)         │    │ • Audit Logs                │ │
                        │  └─────────────────┘    │ (PostgreSQL)                │ │
                        │                         └─────────────────────────────┘ │
                        └────────────────────────────────────────────────────────┘
```

Advanced flow: Messages are processed by a **multi-agent system** using the OpenAI Agents SDK, with intelligent routing between specialized agents and persistent conversation memory. **Voice calls** include natural interstitials ("Let me check that for you") for smooth conversation flow.

## OpenAI Agents SDK Integration

This application leverages the [**OpenAI Agents Python SDK**](https://openai.github.io/openai-agents-python/) to provide:

### Multi-Agent Architecture
- **Triage Agent**: Routes conversations to appropriate specialists
- **Billing Specialist**: Handles payment, invoice, and billing questions  
- **Technical Support**: Manages product setup and troubleshooting
- **Smart Handoffs**: Seamless transitions between agents based on context

### Built-in Capabilities
- **Session Memory**: Persistent conversation storage across interactions
- **Function Tools**: Order lookup, product search, store hours, FAQ responses
- **Conversation Tracing**: Built-in monitoring and debugging with OpenAI Traces
- **Agent Orchestration**: Automatic workflow management and context sharing

### Key Benefits
- **Intelligent Routing**: Customers automatically reach the right specialist
- **Context Preservation**: Agents remember previous interactions  
- **Scalable Architecture**: Easy to add new specialist agents
- **Production Ready**: Built-in error handling, retries, and monitoring

## Customization

**Agent Behavior** - Edit `config/agent_config.yml`:
```yaml
customer_service_agent:
  name: "Your Assistant"
  instructions: "You are a helpful assistant for Acme Corp..."
```

**Environment Variables** - Essential settings in `.env`:
```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_CONVERSATIONS_SERVICE_SID=ISxxxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxx

# Voice Configuration
NGROK_DOMAIN=your-ngrok-domain.ngrok.app
VOICE_WELCOME_GREETING="Hi! I am your voice assistant. Ask me anything!"
VOICE_INTERSTITIALS_ENABLED=true
VOICE_SYSTEM_PROMPT="You are a helpful customer service assistant..."
```

## Testing & Development

**Run Tests:**
```bash
pytest
```

**View API Docs:**
Visit http://localhost:8000/docs when running locally.

**Voice API Endpoints:**
- `POST /voice/twiml` - Generate TwiML for incoming voice calls
- `WebSocket /voice/ws` - Real-time voice communication endpoint  
- `GET /voice/test` - Voice service health check

**Health Check:**
Visit http://localhost:8000/health to verify everything works.

**Voice Testing:**
```bash
# Test voice endpoint health
curl http://localhost:8000/voice/test

# Configure your Twilio phone number webhook to use:
# http://your-ngrok-domain.ngrok.app/voice/twiml
```

**Test Voice Calls:**
1. Call your Twilio phone number
2. Try these voice commands:
   - "What's my order status?" → Should hear: "Let me check on that order for you"
   - "Do you have iPhone cases?" → Should hear: "Let me pull up that product information"
   - "What are your store hours?" → Should hear: "Let me check our store information"

## Production Security Checklist

**CRITICAL: Complete this checklist before production deployment!**

### Before Deploying:
- [ ] **Database**: Replace SQLite with PostgreSQL/MySQL for production scaling
- [ ] **Session Storage**: Configure Redis for multi-instance session management  
- [ ] **Environment**: Set `DEBUG=false` to disable API docs and debug features
- [ ] **Secrets**: Use proper secrets management (K8s secrets, AWS Secrets Manager, not .env files)
- [ ] **CORS**: Configure restrictive origins (remove `*.ngrok.io` wildcards)
- [ ] **Webhooks**: Enable and verify webhook signature validation
- [ ] **SSL/TLS**: Set up HTTPS certificates and force HTTPS redirects
- [ ] **Rate Limiting**: Configure and test rate limiting (default: 30 req/min)
- [ ] **Input Validation**: Review all user inputs for XSS/injection prevention
- [ ] **Logging**: Audit logs to ensure no PII/secrets are logged
- [ ] **Database Encryption**: Enable encryption at rest for sensitive data
- [ ] **Network Security**: Configure firewalls and VPN access as needed

### Production Environment Variables:
```env
# Security
DEBUG=false
WEBHOOK_SECRET=your-strong-random-secret-here
RATE_LIMIT_PER_MINUTE=30
LOG_LEVEL=WARNING

# Database (replace SQLite)
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Session Storage  
REDIS_URL=redis://user:pass@host:6379

# API Keys (use secrets manager in production)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxx  
TWILIO_AUTH_TOKEN=your_auth_token
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxx

# Voice Configuration (production)
NGROK_DOMAIN=your-production-domain.com
VOICE_WELCOME_GREETING="Hi! Welcome to our customer service. How can I help you today?"
VOICE_INTERSTITIALS_ENABLED=true
```

### Security Architecture:
```
Internet ──► Load Balancer/CDN ──► HTTPS/TLS ──► Your App
                 ↓                    ↓             ↓
            DDoS Protection    Webhook Validation  Input Sanitization
                 ↓                    ↓             ↓  
            Rate Limiting      Signature Verify    Database Encryption
```

> **Warning**: The default configuration is for **development only**. Production deployments require additional security measures beyond this checklist.

## Production Monitoring & Observability

### Health Checks & Endpoints:
```bash
# Application health
curl https://your-domain.com/health

# API documentation (disabled in production)  
# https://your-domain.com/docs (only available when DEBUG=true)
```

### Logging Configuration:
```env
# Production logging setup
LOG_LEVEL=WARNING           # Reduce noise (DEBUG/INFO/WARNING/ERROR)
STRUCTLOG_LEVEL=WARNING     # Structured logging for analysis
```

### Metrics Collection:
- **Response Times**: Monitor webhook processing latency
- **Error Rates**: Track failed webhook validations and OpenAI API errors  
- **Agent Performance**: Measure conversation resolution times
- **Database Health**: Monitor connection pool usage and query performance

### Recommended Monitoring Stack:
```yaml
# docker-compose.monitoring.yml (example)
services:
  prometheus:
    image: prom/prometheus:latest
    # Configure metrics scraping
    
  grafana: 
    image: grafana/grafana:latest
    # Dashboard for visualizing metrics
    
  loki:
    image: grafana/loki:latest  
    # Log aggregation and analysis
```

### Alert Configuration Examples:
- **High Error Rate**: > 5% webhook failures in 5 minutes
- **Slow Response**: Average response time > 10 seconds  
- **Database Issues**: Connection pool exhaustion
- **OpenAI API**: Rate limit or quota exceeded
- **Memory Usage**: Container memory > 80% for 5 minutes

### OpenAI Agents SDK Tracing:
The SDK automatically sends traces to OpenAI for monitoring:
```python
# Built-in tracing (no setup required)
# View at: https://platform.openai.com/traces
```

## Troubleshooting

### Common Setup Issues:

**Setup Script Errors:**
```bash
# If you get "configure_credentials: command not found"
# Make sure you're running the script with: ./scripts/setup.sh
# (not: bash scripts/setup.sh or sh scripts/setup.sh)

# If database initialization fails with "No module named 'sqlalchemy'"
# The virtual environment may not be activated properly
# Run manually: source venv/bin/activate && python3 -c "from src.services.session_service import SessionService; import asyncio; asyncio.run(SessionService().create_tables())"
```

**Twilio CLI Issues:**
```bash
# If you get "Unexpected arguments: --webhook-filters"
# Use the correct command format:
twilio api:conversations:v1:services:configuration:webhooks:update \
    --path-sid ISxxxxxxxxxxxxx \
    --pre-webhook-url https://your-ngrok-url.ngrok.app/webhook/message-added \
    --method POST \
    --filters onMessageAdded
```

**Webhook Signature Validation Issues:**
```bash
# If webhooks fail with "Invalid webhook signature" during development:
# Option 1: Disable signature validation temporarily (NOT for production)
echo "VALIDATE_WEBHOOK_SIGNATURES=false" >> .env

# Option 2: Enable debug mode to see signature validation details
echo "DEBUG=true" >> .env

# For production: ensure ngrok URL exactly matches webhook configuration
# and that TWILIO_AUTH_TOKEN is correctly set
```

### Common Deployment Issues:

**Database Connection Errors:**
```bash
# Verify database connectivity
python -c "from src.services.session_service import SessionService; SessionService()"
# Check: DATABASE_URL format, network access, credentials
```

**Webhook Signature Validation Failures:**
```bash
# Test webhook endpoint
curl -X POST https://your-domain.com/webhook/message-added \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "X-Twilio-Signature: test" \
  -d "EventType=onMessageAdded&ConversationSid=CHtest&Body=test"
```

**OpenAI API Issues:**
- **Rate Limits**: Upgrade plan or implement request queuing
- **Invalid API Key**: Check key format and permissions  
- **Model Access**: Verify model availability for your account

**Performance Issues:**
```bash  
# Check resource usage
docker stats twilio-openai-conversations-app-1

# Monitor database queries
# Enable DATABASE_ECHO=true for query logging (dev only)
```

**Redis Connection Issues:**
```bash
# Test Redis connectivity
redis-cli -u $REDIS_URL ping
# Should return "PONG"
```

### Debug Mode (Development Only):
```env
DEBUG=true              # Enables /docs endpoint and verbose logging
DATABASE_ECHO=true      # Log all SQL queries
LOG_LEVEL=DEBUG         # Maximum logging detail
```

> **Warning**: Never enable debug mode in production - it exposes sensitive information and degrades performance.

## Learn More

- **[OpenAI Agents Python SDK](https://openai.github.io/openai-agents-python/)** - Official SDK documentation

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/twilio/twilio-openai-conversations/issues)
- **Twilio Docs**: [Conversations API](https://www.twilio.com/docs/conversations)
- **OpenAI Docs**: [OpenAI Platform](https://platform.openai.com/docs)

## Production Deployment

### Docker Compose Production Setup

Use the production configuration with Redis and PostgreSQL:

```bash
# Production deployment with external database
docker-compose -f docker-compose.yml -f docker-compose.production.yml up -d

# This includes:
# - PostgreSQL database (instead of SQLite)
# - Redis for session management
# - Production security settings
```

**Production docker-compose.production.yml features:**
- PostgreSQL database with persistent storage
- Redis for session caching and WebSocket state
- Production networking configuration
- Health checks and restart policies

### Environment Setup for Production

Create `.env.production`:
```env
DEBUG=false
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/conversations
REDIS_URL=redis://redis:6379
NGROK_DOMAIN=your-production-domain.com
VOICE_INTERSTITIALS_ENABLED=true
```

## Deploy with Temporal

For production deployments requiring durable execution and fault tolerance, you can deploy this application using [Temporal](https://temporal.io/blog/announcing-openai-agents-sdk-integration):

### Benefits:
- **Durable Execution**: Automatic retries on rate limits and network issues
- **Fault Tolerance**: Agents recover from crashes and continue execution
- **Scalability**: Each agent runs in its own process with dynamic capacity allocation
- **Built-in Monitoring**: Integrates with OpenAI tracing and Temporal's observability

### Quick Setup:
```python
# Install Temporal SDK
pip install temporalio

# Wrap your agents in a Temporal Workflow
from temporalio import workflow
from openai_agents import Runner

@workflow.defn
class ConversationWorkflow:
    @workflow.run
    async def run(self, message: str, conversation_sid: str) -> str:
        # Your existing agent setup from src/services/agent_service.py
        agent = Agent(name="Customer Service", instructions="...")
        result = await Runner.run(agent, input=message)
        return result.final_output
```

For complete setup instructions, see the [Temporal + OpenAI Agents integration guide](https://temporal.io/blog/announcing-openai-agents-sdk-integration).

---

## License

MIT License - see [LICENSE](LICENSE) file.

---