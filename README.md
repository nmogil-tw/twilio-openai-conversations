# Twilio Conversations + OpenAI Agents Integration

## 🏛️ Reference Architecture & Implementation

**This is a complete reference architecture** demonstrating how to integrate [OpenAI Agents Python SDK](https://platform.openai.com/) with [Twilio's Conversations API](https://www.twilio.com/docs/conversations) to build intelligent customer service chatbots that operate across SMS, WhatsApp, and other messaging channels.

### 🎯 What is a Reference Architecture?

This repository provides:

- ✅ **Complete, production-ready codebase** - Not just examples or tutorials
- ✅ **Enterprise-grade patterns** - Security, monitoring, error handling, scaling
- ✅ **Best practices demonstration** - How to structure, test, and deploy AI-powered services
- ✅ **Extensible foundation** - Fork, customize, and build your specific solution
- ✅ **Real-world scenarios** - Customer service use cases with actual business logic
- ✅ **Multiple deployment options** - From local development to enterprise cloud platforms

**Perfect for:** Teams building conversational AI products, developers learning modern Python/AI patterns, organizations evaluating Twilio + OpenAI integrations, and anyone needing a solid foundation for production AI services.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Twilio Account ([Sign up free](https://twilio.com/try-twilio))
- OpenAI Account ([Sign up here](https://platform.openai.com/))

### 1. Clone and Setup
```bash
git clone https://github.com/twilio/twilio-openai-conversations.git
cd twilio-openai-conversations
./scripts/setup.sh
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your Twilio and OpenAI credentials
```

### 3. Set Up Twilio Service & Phone Number

**Option A: Automated CLI Setup (Recommended)**
```bash
# Use our automated setup script with Twilio CLI option
./scripts/setup.sh
# Then select option 6: "Twilio CLI setup"
# This will automatically:
# - Install/configure Twilio CLI
# - Create Conversations service
# - Configure webhooks
# - Purchase phone number
# - Set up messaging service
# - Update your .env file
```

**Option B: Manual CLI Commands**
```bash
# Install Twilio CLI if not already installed
npm install -g twilio-cli

# Login to Twilio (opens browser for authentication)
twilio login

# Create Conversations service
CONVERSATIONS_SERVICE_SID=$(twilio api:conversations:v1:services:create \
  --friendly-name "AI Customer Service" \
  --query "sid" --output json | jq -r .)

# Configure webhooks (replace YOUR_NGROK_URL with your ngrok URL from step 5)
twilio api:conversations:v1:services:configuration:webhooks:update \
  --path-sid $CONVERSATIONS_SERVICE_SID \
  --pre-webhook-url https://YOUR_NGROK_URL/webhook/message-added \
  --method POST

# Purchase a phone number and set up SMS
PHONE_NUMBER_SID=$(twilio phone-numbers:buy:local \
  --country-code US --sms-enabled \
  --query "sid" --output json | jq -r .)

# Create messaging service and add phone number
MESSAGING_SERVICE_SID=$(twilio messaging:services:create \
  --friendly-name "AI Customer Service SMS" \
  --query "sid" --output json | jq -r .)

twilio messaging:services:phone-numbers:create \
  --service-sid $MESSAGING_SERVICE_SID \
  --phone-number-sid $PHONE_NUMBER_SID

# Update your .env file with the service SID
echo "TWILIO_CONVERSATIONS_SERVICE_SID=$CONVERSATIONS_SERVICE_SID" >> .env
```

**Option C: Using Twilio Console (Manual)**
1. Go to [Twilio Console](https://console.twilio.com/)
2. Create Conversations Service: **Conversations > Services > Create new Service**
3. Configure webhooks in the service settings
4. Set up phone number: **Phone Numbers > Buy a number**
5. Copy Service SID to your `.env` file

### 4. Run the Application
```bash
# Using Docker (recommended)
docker-compose up

# Or run locally
source venv/bin/activate
python -m uvicorn src.main:app --reload
```

### 5. Expose Webhooks (for local development)
```bash
ngrok http 8000
# Copy the HTTPS URL and update YOUR_NGROK_URL in the CLI commands above
# Or configure webhooks manually in Twilio Console
```

🎉 **That's it!** Your AI-powered customer service agent is ready to handle conversations.

## 📋 What This Reference Architecture Provides

As a **complete reference implementation**, this codebase includes:

- **🤖 Intelligent AI Agent**: Powered by OpenAI's models, handles customer inquiries naturally
- **📱 Multi-Channel Support**: Works across SMS, WhatsApp, Web Chat, and other Twilio channels  
- **🔧 Built-in Tools**: Order lookup, product search, store hours, FAQ responses
- **💾 Session Management**: Maintains conversation context and history
- **🛡️ Production Ready**: Security, error handling, monitoring, and scalability built-in
- **📊 Health Monitoring**: Comprehensive health checks and observability
- **🔄 Easy Deployment**: Docker, Kubernetes, Heroku, and cloud platform support

## 🏗️ Reference Architecture

### System Overview
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Customer      │    │   Twilio         │    │   Python        │
│   (SMS/WhatsApp)│◄──►│   Conversations  │◄──►│   Application   │
└─────────────────┘    │   API            │    │                 │
                       └──────────────────┘    │   ┌─────────────┐
                                               │   │ FastAPI     │
                       ┌──────────────────┐    │   │ Server      │
                       │   OpenAI         │◄──►│   └─────────────┘
                       │   Agents SDK     │    │   ┌─────────────┐
                       └──────────────────┘    │   │ AI Agent    │
                                               │   │ Service     │
                                               │   └─────────────┘
                                               └─────────────────┘
```

### Architectural Patterns Demonstrated

- **🏗️ Layered Architecture**: Clean separation between handlers, services, models, and utilities
- **⚡ Async-First Design**: Non-blocking I/O for high concurrency and performance
- **🔧 Dependency Injection**: Configurable services with clear interfaces and testability
- **🛡️ Security by Design**: Input validation, webhook verification, and secure logging throughout
- **📊 Observability Built-In**: Health checks, structured logging, and monitoring from day one
- **🚀 Cloud-Native Ready**: Stateless design, containerized deployment, and horizontal scaling
- **🧪 Test-Driven Structure**: Comprehensive test suite with mocks, fixtures, and integration tests

## 🎯 Use Cases

Perfect for businesses wanting to:

- **Automate Customer Support**: Handle common inquiries 24/7
- **Scale Messaging Operations**: Support multiple channels from one codebase
- **Reduce Response Times**: Instant AI responses with human handoff when needed
- **Maintain Context**: Conversations remember previous interactions
- **Easy Integration**: Drop into existing Twilio workflows

### Example Conversations

**Order Status Inquiry:**
```
Customer: "Hi, can you check my order status? Order #12345"
AI Agent: "I'd be happy to help! Let me look up order #12345... 
          Your order shipped yesterday and should arrive by Thursday. 
          Tracking: 1Z123456789"
```

**Product Information:**
```
Customer: "Do you have iPhone 15 cases in stock?"
AI Agent: "Yes! We have iPhone 15 cases in several colors and styles. 
          Our most popular is the Clear MagSafe case for $29.99. 
          Would you like me to check availability at a specific store?"
```

## 🛠️ Technology Stack

- **Backend**: FastAPI (async-native, auto-documentation)
- **AI Framework**: OpenAI Agents Python SDK
- **Communication**: Twilio Conversations API
- **Database**: SQLite (local) / PostgreSQL (production)
- **Session Storage**: Redis (production)
- **Configuration**: Pydantic Settings with YAML
- **Testing**: pytest with async support
- **Deployment**: Docker + docker-compose
- **Monitoring**: Structured logging, health checks, metrics

## 🔧 Configuration

### Environment Variables

Create a `.env` file with your credentials:

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
WEBHOOK_SECRET=your_webhook_secret
```

### Agent Behavior

Customize the AI agent in `config/agent_config.yml`:

```yaml
customer_service_agent:
  name: "Customer Service Assistant"
  instructions: |
    You are a helpful customer service assistant for Acme Corp.
    Be friendly, professional, and concise.
    Always ask for order numbers when helping with orders.
  
  tools:
    - lookup_order_status
    - get_product_info
    - check_store_hours
    - get_store_locations
```

## 🚀 Deployment

### Docker (Recommended)
```bash
docker-compose up -d
```

### Kubernetes
```bash
kubectl apply -f k8s/
```

### Heroku
```bash
./scripts/deploy.sh heroku
```

### Other Platforms
```bash
./scripts/deploy.sh --help
```

See [docs/deployment.md](docs/deployment.md) for detailed deployment guides.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Test specific component
pytest tests/test_agent_service.py -v
```

## 📚 Documentation

- **[Setup Guide](docs/setup.md)** - Detailed installation and configuration
- **[Configuration Guide](docs/configuration.md)** - Advanced configuration options
- **[Deployment Guide](docs/deployment.md)** - Production deployment strategies

## 🔍 Monitoring

### Health Checks

- **Basic Health**: `GET /health` - Application status
- **Readiness**: `GET /health/ready` - Ready to serve requests  
- **Liveness**: `GET /health/live` - Application is alive
- **Detailed Status**: `GET /health/status` - Comprehensive system info

### API Documentation

When running with `DEBUG=true`, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🛡️ Security Features

- **Webhook Signature Validation**: Verifies requests are from Twilio
- **Rate Limiting**: Prevents abuse and ensures stability
- **Input Validation**: Pydantic models validate all inputs
- **Secure Logging**: Sensitive data is automatically sanitized
- **HTTPS Support**: TLS termination and secure communications

## 🎛️ Using as Reference Architecture

### 🚀 Getting Started with This Reference

**Option 1: Direct Fork & Customize**
```bash
# Fork this repository to your organization
# Clone and customize for your specific needs
git clone https://github.com/your-org/your-conversational-ai.git
cd your-conversational-ai
./scripts/setup.sh
# Customize agent behavior, add business logic, deploy
```

**Option 2: Learn & Apply Patterns**
- Study the code structure and apply patterns to your existing projects
- Use individual components (services, handlers, models) as reference
- Adapt the deployment and configuration strategies

**Option 3: Extend & Contribute Back**
- Add new features and improvements
- Share your enhancements with the community
- Help evolve this reference architecture

### 🔧 Customization Examples

#### Adding Custom Tools

```python
# In src/services/agent_service.py

def lookup_customer_info(self, customer_id: str) -> str:
    """Look up customer information by ID."""
    # Your custom business logic here
    return f"Customer {customer_id} information..."

# Add to agent tools list
self.tools = [
    self.lookup_order_status,
    self.get_product_info,
    self.lookup_customer_info,  # Your new tool
    # ... other tools
]
```

### Custom Business Logic

Extend the services in `src/services/` to integrate with your:
- **CRM Systems**: Salesforce, HubSpot, etc.
- **E-commerce Platforms**: Shopify, WooCommerce, etc.
- **Databases**: Customer data, inventory, orders
- **APIs**: Internal services, third-party integrations

## 📊 Performance & Scaling

- **Async Processing**: Non-blocking I/O for high concurrency
- **Connection Pooling**: Efficient database connections
- **Horizontal Scaling**: Stateless design supports multiple instances
- **Caching**: Redis for session storage and response caching
- **Resource Management**: Configurable limits and timeouts

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/twilio/twilio-openai-conversations.git
cd twilio-openai-conversations

# Set up development environment
./scripts/setup.sh

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Start development server
python -m uvicorn src.main:app --reload --log-level debug
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help

- **Documentation**: Check the [docs/](docs/) directory for detailed guides
- **Issues**: Report bugs at [GitHub Issues](https://github.com/twilio/twilio-openai-conversations/issues)
- **Twilio Support**: Visit [Twilio Support Center](https://support.twilio.com/)
- **Community**: Join the [Twilio Community](https://community.twilio.com/)

### Common Issues

**Webhook not receiving calls?**
- Verify your ngrok URL is HTTPS
- Check Twilio webhook configuration
- Ensure webhook signature validation is set up

**OpenAI API errors?**
- Verify your API key has sufficient credits
- Check rate limits in OpenAI dashboard  
- Ensure model name is correct (`gpt-4o-mini`)

**Database connection issues?**
- Check if data directory exists and is writable
- Verify DATABASE_URL format
- Ensure database tables are created

## 🎯 Roadmap

### Current Version (v1.0)
- ✅ Basic AI agent with OpenAI integration
- ✅ Twilio Conversations API support
- ✅ Multi-channel messaging (SMS, WhatsApp)
- ✅ Session management and context
- ✅ Production-ready deployment options

### Upcoming Features (v1.1)
- 🔄 Enhanced multi-agent support
- 🔄 Rich media responses (images, quick replies)
- 🔄 Advanced analytics and insights
- 🔄 CRM system integrations

### Future Roadmap (v2.0+)
- 🎯 Voice conversation support
- 🎯 Sentiment analysis and routing
- 🎯 Machine learning for response optimization
- 🎯 Advanced human handoff workflows

---

## 🌟 Show Your Support

If this project helps you build amazing customer experiences, please ⭐ star this repository!

**Built with ❤️ by the Twilio Developer Relations team**

[![Reference Architecture](https://img.shields.io/badge/Reference-Architecture-success?style=for-the-badge)](https://github.com/twilio/twilio-openai-conversations)
[![Production Ready](https://img.shields.io/badge/Production-Ready-brightgreen?style=for-the-badge)](https://github.com/twilio/twilio-openai-conversations)
[![Twilio](https://img.shields.io/badge/Twilio-F22F46?style=for-the-badge&logo=Twilio&logoColor=white)](https://twilio.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=OpenAI&logoColor=white)](https://openai.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)