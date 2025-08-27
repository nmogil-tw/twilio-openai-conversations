# Configuration Guide

This guide covers advanced configuration options for the Twilio Conversations + OpenAI Agents integration.

## Configuration Architecture

The application uses a layered configuration approach:

1. **Environment Variables** (`.env` file) - Runtime configuration
2. **YAML Configuration** (`config/agent_config.yml`) - Agent behavior
3. **Settings Classes** (`config/settings.py`) - Structured configuration with validation

## Environment Configuration

### Core Settings

#### Application Settings
```env
# Application behavior
DEBUG=false
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=sqlite:///./conversations.db
DATABASE_ECHO=false
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# Session Management
MAX_CONVERSATION_HISTORY=50
CONVERSATION_TIMEOUT_MINUTES=30
```

#### Twilio Settings
```env
# Required Twilio credentials
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_CONVERSATIONS_SERVICE_SID=ISxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Security (recommended for production)
WEBHOOK_SECRET=your_webhook_secret_for_signature_validation

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
MAX_CONCURRENT_CONVERSATIONS=100
```

#### OpenAI Settings
```env
# Required OpenAI configuration
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini

# Optional fine-tuning
OPENAI_MAX_TOKENS=1000
OPENAI_TEMPERATURE=0.7
```

#### Production Settings
```env
# Redis for session storage (production)
REDIS_URL=redis://localhost:6379
REDIS_MAX_CONNECTIONS=20

# PostgreSQL for production database
DATABASE_URL=postgresql://user:password@localhost:5432/conversations

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
NEW_RELIC_LICENSE_KEY=your_new_relic_key

# Security
WEBHOOK_SECRET=your_strong_webhook_secret
```

### Environment-Specific Configuration

#### Development (`.env.development`)
```env
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite:///./dev_conversations.db
OPENAI_MODEL=gpt-4o-mini
RATE_LIMIT_PER_MINUTE=100
```

#### Production (`.env.production`)
```env
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:pass@prod-db:5432/conversations
REDIS_URL=redis://prod-redis:6379
OPENAI_MODEL=gpt-4o
RATE_LIMIT_PER_MINUTE=60
WEBHOOK_SECRET=your_production_webhook_secret
```

## Agent Configuration

The agent behavior is configured in `config/agent_config.yml`:

### Basic Agent Settings

```yaml
customer_service_agent:
  name: "Customer Service Assistant"
  model: "gpt-4o-mini"
  
  # Core personality and instructions
  instructions: |
    You are a helpful customer service assistant for [Your Company].
    
    ## Your Capabilities:
    - Look up order status using order numbers
    - Provide product information from our catalog
    - Check store hours and locations
    - Answer frequently asked questions
    
    ## Guidelines:
    - Be friendly, professional, and concise
    - Always ask for order numbers when helping with orders
    - Keep responses under 160 characters when possible for SMS
    - If you don't know something, suggest contacting human support
  
  # Model parameters
  settings:
    max_tokens: 150          # Limit response length
    temperature: 0.7         # Creativity vs consistency (0.0-1.0)
    top_p: 0.9              # Nucleus sampling
    frequency_penalty: 0.0   # Reduce repetition
    presence_penalty: 0.0    # Encourage topic diversity
```

### Tool Configuration

```yaml
customer_service_agent:
  # Available tools/functions
  tools:
    - lookup_order_status
    - get_product_info
    - check_store_hours
    - get_store_locations
    - search_faq
    - escalate_to_human  # Custom tool for handoff
```

### Knowledge Base Configuration

```yaml
customer_service_agent:
  knowledge_base:
    # Store information
    store_hours:
      weekdays: "Monday-Friday: 9:00 AM - 9:00 PM"
      saturday: "Saturday: 9:00 AM - 8:00 PM"
      sunday: "Sunday: 11:00 AM - 6:00 PM"
      holidays: "Holiday hours: 11:00 AM - 5:00 PM"
    
    # Contact information
    contact_info:
      customer_service: "1-800-YOUR-HELP"
      billing: "1-800-YOUR-BILL"
      technical_support: "1-800-YOUR-TECH"
      email: "help@yourcompany.com"
      website: "yourcompany.com"
    
    # Business policies
    policies:
      shipping:
        free_threshold: 50
        standard_shipping: "3-5 business days"
        express_shipping: "1-2 business days"
        international: "7-14 business days"
      
      returns:
        window_days: 30
        condition: "original condition with tags"
        free_return_shipping: true
        exceptions: ["final sale items", "personalized items"]
    
    # Product categories (for demonstrations)
    product_categories:
      - "Electronics & Accessories"
      - "Clothing & Fashion"
      - "Home & Garden"
      - "Sports & Outdoors"
      - "Books & Media"
      - "Health & Beauty"
```

### Fallback & Error Responses

```yaml
customer_service_agent:
  # Predefined responses for common scenarios
  fallback_responses:
    unknown_query: "I'm not sure about that. For complex questions, please contact our customer service at 1-800-YOUR-HELP."
    billing_issues: "For billing questions, please contact our billing department at billing@yourcompany.com or 1-800-YOUR-BILL."
    returns_refunds: "For returns and refunds, please visit yourcompany.com/returns or contact customer service."
    technical_support: "For technical issues, please contact our tech team at support@yourcompany.com."
    escalation: "Let me connect you with a human agent who can better assist you."
    
  # Error handling responses
  error_responses:
    api_error: "I'm experiencing technical difficulties. Please try again in a moment."
    rate_limit: "I'm experiencing high volume right now. Please try again shortly."
    timeout: "I'm taking longer than usual to respond. Please try your question again."
    maintenance: "Our system is currently undergoing maintenance. Please contact customer service."
```

### Conversation Flow Settings

```yaml
customer_service_agent:
  conversation:
    max_history_length: 50      # Messages to keep in context
    context_window: 10          # Recent messages for immediate context
    session_timeout_minutes: 30 # Auto-timeout inactive sessions
    
    # Greeting variations
    greetings:
      - "Hi! I'm here to help with your questions. How can I assist you today?"
      - "Hello! Welcome to [Company] customer service. What can I help you with?"
      - "Hi there! I'm your AI assistant. How may I help you?"
    
    # Closing messages
    closings:
      - "Is there anything else I can help you with today?"
      - "Thank you for contacting [Company]! Have a great day!"
      - "I'm here if you need any other assistance. Have a wonderful day!"
```

## Advanced Configuration

### Multi-Agent Setup

```yaml
# Multiple specialized agents
agents:
  customer_service:
    name: "Customer Service Assistant"
    specializes_in: ["general", "orders", "products"]
    # ... configuration
  
  billing_specialist:
    name: "Billing Specialist"
    specializes_in: ["billing", "payments", "invoices", "refunds"]
    instructions: |
      You are a billing specialist focused on payment and invoice questions...
    tools:
      - lookup_billing_info
      - process_refund_request
      - update_payment_method
  
  technical_support:
    name: "Technical Support Agent"
    specializes_in: ["troubleshooting", "setup", "technical_issues"]
    instructions: |
      You are a technical support specialist...
    tools:
      - diagnostic_check
      - escalate_to_engineering
      - schedule_callback

# Agent routing rules
routing:
  keywords:
    billing: ["billing", "payment", "invoice", "charge", "refund"]
    technical: ["technical", "setup", "error", "bug", "not working"]
  
  escalation_triggers:
    - "talk to human"
    - "speak with manager"
    - "this isn't working"
```

### Database Configuration

#### SQLite (Development)
```env
DATABASE_URL=sqlite:///./conversations.db
DATABASE_ECHO=false  # Set to true to log SQL queries
```

#### PostgreSQL (Production)
```env
DATABASE_URL=postgresql://username:password@hostname:5432/database_name
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
DATABASE_ECHO=false
```

#### Connection Pool Settings
```env
# Pool settings for high-traffic applications
DATABASE_POOL_SIZE=20        # Number of connections to maintain
DATABASE_MAX_OVERFLOW=30     # Additional connections under load
DATABASE_POOL_TIMEOUT=30     # Seconds to wait for connection
DATABASE_POOL_RECYCLE=3600   # Seconds before recycling connections
```

### Redis Configuration

#### Basic Redis Setup
```env
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=20
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5
```

#### Redis Cluster
```env
REDIS_URL=redis://node1:6379,redis://node2:6379,redis://node3:6379
REDIS_CLUSTER=true
REDIS_MAX_CONNECTIONS=50
```

#### Redis Sentinel
```env
REDIS_SENTINELS=sentinel1:26379,sentinel2:26379,sentinel3:26379
REDIS_SENTINEL_SERVICE=mymaster
REDIS_MAX_CONNECTIONS=20
```

### Logging Configuration

#### Basic Logging
```env
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json             # json or text
LOG_FILE=logs/app.log
LOG_MAX_SIZE=10485760       # 10MB
LOG_BACKUP_COUNT=5
```

#### Structured Logging Fields
```python
# Custom log fields (configured in logging.py)
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "src.handlers.webhook_handler",
  "message": "Processing webhook",
  "conversation_sid": "CHxxxxx",
  "session_id": "conv_CHxxxxx",
  "processing_time_ms": 1250,
  "agent_response_length": 145,
  "tools_used": ["lookup_order_status"]
}
```

### Security Configuration

#### Webhook Security
```env
WEBHOOK_SECRET=your_strong_secret_key_here
```

#### Rate Limiting
```env
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_PER_DAY=10000
MAX_CONCURRENT_CONVERSATIONS=100
```

#### CORS Settings
```python
# In main.py
CORS_ORIGINS=["https://yourapp.com", "https://admin.yourapp.com"]
CORS_METHODS=["GET", "POST"]
CORS_HEADERS=["Content-Type", "Authorization"]
```

## Monitoring & Observability

### Health Check Configuration
```env
HEALTH_CHECK_TIMEOUT=30     # Seconds for dependency checks
HEALTH_CHECK_INTERVAL=60    # Seconds between checks
```

### Metrics Collection
```env
METRICS_ENABLED=true
METRICS_PORT=9090
METRICS_PATH=/metrics
```

### APM Integration
```env
# New Relic
NEW_RELIC_LICENSE_KEY=your_license_key
NEW_RELIC_APP_NAME=twilio-openai-conversations

# Datadog
DATADOG_API_KEY=your_datadog_key
DATADOG_SERVICE_NAME=twilio-openai-conversations

# Sentry
SENTRY_DSN=https://your-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=production
```

## Configuration Validation

The application validates configuration on startup. To test your configuration:

```bash
# Validate configuration
python -c "from config.settings import settings; print('Configuration valid!')"

# Test specific services
python -c "from src.services.twilio_service import TwilioConversationService; TwilioConversationService()"
python -c "from src.services.agent_service import CustomerServiceAgent; CustomerServiceAgent()"
```

## Configuration Management

### Environment-Specific Files
```bash
# Development
cp .env.example .env.development
# Edit development-specific settings

# Production  
cp .env.example .env.production
# Edit production-specific settings

# Load specific environment
export ENV=production
python src/main.py
```

### Docker Environment Files
```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    env_file:
      - .env
      - .env.${ENV:-development}
```

### Configuration Hot Reload

The agent configuration (`agent_config.yml`) can be reloaded without restarting:

```bash
# Send SIGUSR1 to reload configuration (Linux/macOS)
kill -USR1 $(pgrep -f "uvicorn")

# Or restart specific service in Docker
docker-compose restart app
```

## Best Practices

### Security
- Use strong, unique webhook secrets
- Rotate API keys regularly  
- Use environment-specific configurations
- Never commit secrets to version control
- Use encrypted storage for production secrets

### Performance
- Use connection pooling for databases
- Configure appropriate rate limits
- Use Redis for session storage in production
- Monitor memory usage and adjust pool sizes
- Use CDN for static assets if serving web UI

### Monitoring
- Enable structured logging
- Set up health checks for all dependencies
- Monitor key metrics (response time, error rate)
- Use APM tools for detailed performance tracking
- Set up alerts for critical errors

### Development
- Use debug logging for development
- Keep development and production configurations in sync
- Use feature flags for experimental features
- Document all configuration options
- Validate configuration changes in staging first