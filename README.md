# Twilio Conversations + OpenAI Integration

> **⚠️ REFERENCE ARCHITECTURE ONLY**  
> This is a reference implementation demonstrating how to integrate Twilio Conversations with AI agents using OpenAI's Agents SDK. **This code is not production-ready** and is intended for educational and prototyping purposes. See the [Production Security Checklist](#production-security-checklist) for requirements before deploying to production.

Build AI-powered customer chatbots that work across SMS, WhatsApp, and messaging channels using Twilio Conversations API and OpenAI.

## What You Get

- **Intelligent AI Assistant** - Handles customer inquiries naturally with OpenAI
- **Multi-Channel Support** - Works on SMS, WhatsApp, Web Chat
- **Built-in Tools** - Order lookup, product search, store hours, FAQ responses
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
    --chat-service-sid ISxxxxxxxxxxxxx \
    --post-webhook-url https://abc123.ngrok.app/webhook/message-added \
    --webhook-filters onMessageAdded
```

**Done!** Text your Twilio number to chat with your AI assistant.

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

Advanced flow: Messages are processed by a **multi-agent system** using the OpenAI Agents SDK, with intelligent routing between specialized agents and persistent conversation memory.

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
```

## Testing & Development

**Run Tests:**
```bash
pytest
```

**View API Docs:**
Visit http://localhost:8000/docs when running locally.

**Health Check:**
Visit http://localhost:8000/health to verify everything works.

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

---

## License

MIT License - see [LICENSE](LICENSE) file.

---