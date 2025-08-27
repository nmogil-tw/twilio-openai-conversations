# Setup Guide

This guide will help you set up the Twilio Conversations + OpenAI Agents integration for local development and testing.

## Prerequisites

Before you begin, ensure you have the following:

### Required Accounts & Services
- **Twilio Account**: [Sign up at twilio.com](https://twilio.com/try-twilio)
- **OpenAI Account**: [Sign up at platform.openai.com](https://platform.openai.com/)
- **Python 3.11+**: [Download from python.org](https://python.org/)
- **Docker** (optional): [Get Docker Desktop](https://docker.com/get-started)

### Development Tools
- **Git**: For cloning the repository
- **ngrok** (for local testing): [Download ngrok](https://ngrok.com/)
- **Twilio CLI** (recommended): [Install guide](https://www.twilio.com/docs/twilio-cli/quickstart)
- **Node.js** (for Twilio CLI): [Download Node.js](https://nodejs.org/)
- **jq** (for JSON parsing): `brew install jq` or [download jq](https://stedolan.github.io/jq/)
- **Code editor**: VS Code, PyCharm, or your preferred editor

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/twilio/twilio-openai-conversations.git
cd twilio-openai-conversations
```

### 2. Set Up Environment

#### Option A: Using Docker (Recommended)

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials (see Configuration section below)
nano .env

# Start services
docker-compose up -d
```

#### Option B: Local Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### 3. Configure Credentials

Edit your `.env` file with the following required values:

```env
# Twilio Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_CONVERSATIONS_SERVICE_SID=ISxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# OpenAI Configuration
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini

# Application Configuration
DEBUG=true
LOG_LEVEL=INFO
```

### 4. Initialize Database

```bash
# If using Docker
docker-compose exec app python -c "from src.services.session_service import SessionService; import asyncio; asyncio.run(SessionService().create_tables())"

# If using local environment
python -c "from src.services.session_service import SessionService; import asyncio; asyncio.run(SessionService().create_tables())"
```

### 5. Start the Application

#### Using Docker
```bash
docker-compose up
```

#### Using Local Environment
```bash
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Verify Installation

Open your browser and visit:
- **Application**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs (if DEBUG=true)

You should see the health check return a successful status.

## Detailed Configuration

### Twilio Setup

#### Option A: Using Twilio CLI (Recommended for Automation)

##### 1. Install and Configure Twilio CLI

```bash
# Install Twilio CLI
npm install -g twilio-cli

# Login to Twilio (opens browser for authentication)
twilio login

# Verify your account details
twilio profiles:list
```

##### 2. Set Up Local Development Environment

```bash
# Start ngrok first to get your webhook URL
ngrok http 8000

# In another terminal, save the ngrok URL
NGROK_URL="https://your-ngrok-url.ngrok.io"  # Replace with actual URL from ngrok
```

##### 3. Create and Configure Conversations Service

```bash
# Create Conversations service
CONVERSATIONS_SERVICE_SID=$(twilio api:conversations:v1:services:create \
  --friendly-name "AI Customer Service" \
  --query "sid" \
  --output json | jq -r .)

echo "Created Conversations Service: $CONVERSATIONS_SERVICE_SID"

# Configure webhooks for the service
twilio api:conversations:v1:services:configuration:webhooks:update \
  --path-sid $CONVERSATIONS_SERVICE_SID \
  --pre-webhook-url "${NGROK_URL}/webhook/message-added" \
  --post-webhook-url "${NGROK_URL}/webhook/participant-added" \
  --method POST \
  --filters "onMessageAdded" \
  --filters "onParticipantAdded" \
  --filters "onConversationStateUpdated"

echo "Configured webhooks for service"
```

##### 4. SMS Setup - Purchase Phone Number and Configure

```bash
# Search for available phone numbers
twilio phone-numbers:list:local --country-code US --sms-enabled --limit 5

# Purchase a phone number (replace with desired area code)
PHONE_NUMBER_SID=$(twilio phone-numbers:buy:local \
  --country-code US \
  --area-code 415 \
  --sms-enabled \
  --voice-enabled \
  --query "sid" \
  --output json | jq -r .)

# Get the actual phone number
PHONE_NUMBER=$(twilio phone-numbers:fetch $PHONE_NUMBER_SID \
  --query "phoneNumber" \
  --output json | jq -r .)

echo "Purchased phone number: $PHONE_NUMBER (SID: $PHONE_NUMBER_SID)"

# Create messaging service
MESSAGING_SERVICE_SID=$(twilio messaging:services:create \
  --friendly-name "AI Customer Service SMS" \
  --query "sid" \
  --output json | jq -r .)

# Add phone number to messaging service
twilio messaging:services:phone-numbers:create \
  --service-sid $MESSAGING_SERVICE_SID \
  --phone-number-sid $PHONE_NUMBER_SID

echo "Created messaging service: $MESSAGING_SERVICE_SID"
echo "Added phone number to messaging service"
```

##### 5. Configure Conversations Integration

```bash
# Configure the messaging service to use Conversations
twilio messaging:services:update \
  --sid $MESSAGING_SERVICE_SID \
  --use-inbound-webhook-on-number false \
  --inbound-method POST \
  --inbound-request-url "${NGROK_URL}/webhook/message-added"

# Create address configuration for Conversations
twilio conversations:v1:address-configurations:create \
  --type sms \
  --address $PHONE_NUMBER \
  --friendly-name "SMS Channel" \
  --address-sid $MESSAGING_SERVICE_SID

echo "Configured SMS integration with Conversations"
```

##### 6. WhatsApp Setup (Optional)

```bash
# Note: WhatsApp setup requires business verification
# This creates the configuration, but you'll need to complete WhatsApp Business verification

# Create WhatsApp sender (replace with your business phone number)
WHATSAPP_NUMBER="+14155551234"  # Your verified WhatsApp business number

# Configure WhatsApp for Conversations
twilio conversations:v1:address-configurations:create \
  --type whatsapp \
  --address "whatsapp:$WHATSAPP_NUMBER" \
  --friendly-name "WhatsApp Channel" \
  --inbound-webhook-url "${NGROK_URL}/webhook/message-added" \
  --inbound-method POST

echo "Configured WhatsApp integration (requires business verification)"
```

##### 7. Update Environment Configuration

```bash
# Add the service SID to your .env file
echo "TWILIO_CONVERSATIONS_SERVICE_SID=$CONVERSATIONS_SERVICE_SID" >> .env

# Optionally save other IDs for reference
echo "# Twilio Resource IDs (for reference)" >> .env
echo "# PHONE_NUMBER_SID=$PHONE_NUMBER_SID" >> .env
echo "# MESSAGING_SERVICE_SID=$MESSAGING_SERVICE_SID" >> .env
echo "# PHONE_NUMBER=$PHONE_NUMBER" >> .env

echo "Updated .env file with Conversations Service SID"
```

##### 8. Verify Configuration

```bash
# Test webhook endpoint
curl -X POST "$NGROK_URL/webhook/test"

# List all Conversations services
twilio conversations:v1:services:list

# Check service configuration
twilio conversations:v1:services:configuration:fetch --path-sid $CONVERSATIONS_SERVICE_SID

# Verify phone number configuration
twilio phone-numbers:fetch $PHONE_NUMBER_SID
```

#### Option B: Using Twilio Console (Manual Setup)

##### 1. Create a Conversations Service

1. Log into the [Twilio Console](https://console.twilio.com/)
2. Navigate to **Conversations > Services**
3. Click **Create new Service**
4. Give it a name like "AI Customer Service"
5. Copy the **Service SID** (starts with `IS`) to your `.env` file

##### 2. Configure Webhooks

1. In your Conversations Service, go to **Webhooks**
2. Add webhook URLs for these events:
   - **onMessageAdd**: `https://your-ngrok-url.ngrok.io/webhook/message-added`
   - **onParticipantAdd**: `https://your-ngrok-url.ngrok.io/webhook/participant-added`
   - **onConversationStateUpdate**: `https://your-ngrok-url.ngrok.io/webhook/conversation-state-updated`

##### 3. Set Up Phone Number or Channel

1. **For SMS**: Go to **Phone Numbers > Manage > Buy a number**
2. **For WhatsApp**: Go to **Messaging > WhatsApp > Senders**
3. Configure the messaging service to use your Conversations Service

##### 4. Local Development with ngrok

For local testing, use ngrok to expose your webhook endpoints:

```bash
# Install ngrok
# On macOS: brew install ngrok
# On other platforms: download from ngrok.com

# Expose local port 8000
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Use this as your webhook base URL in Twilio Console
```

### OpenAI Setup

#### 1. Get API Key

1. Log into [OpenAI Platform](https://platform.openai.com/)
2. Navigate to **API Keys**
3. Click **Create new secret key**
4. Copy the key (starts with `sk-`) to your `.env` file

#### 2. Configure Model

The default model is `gpt-4o-mini` which is cost-effective for development. For production, you might want to use `gpt-4o` for better performance.

### Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `TWILIO_ACCOUNT_SID` | ✅ | Your Twilio Account SID | `ACxxxxxxxxxxxxx` |
| `TWILIO_AUTH_TOKEN` | ✅ | Your Twilio Auth Token | `your_auth_token` |
| `TWILIO_CONVERSATIONS_SERVICE_SID` | ✅ | Conversations Service SID | `ISxxxxxxxxxxxxx` |
| `OPENAI_API_KEY` | ✅ | OpenAI API Key | `sk-xxxxxxxxxxxxx` |
| `OPENAI_MODEL` | ❌ | OpenAI Model to use | `gpt-4o-mini` |
| `DEBUG` | ❌ | Enable debug mode | `true` |
| `LOG_LEVEL` | ❌ | Logging level | `INFO` |
| `WEBHOOK_SECRET` | ❌ | Webhook signature validation | `your_secret` |
| `DATABASE_URL` | ❌ | Database connection string | `sqlite:///./conversations.db` |

### Agent Configuration

The AI agent behavior is configured in `config/agent_config.yml`. Key settings include:

```yaml
customer_service_agent:
  name: "Customer Service Assistant"
  model: "gpt-4o-mini"
  instructions: |
    You are a helpful customer service assistant...
  
  settings:
    max_tokens: 150
    temperature: 0.7
  
  knowledge_base:
    store_hours:
      weekdays: "9:00 AM - 9:00 PM"
      # ... more configuration
```

## Testing the Integration

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "checks": {
    "configuration": {"healthy": true},
    "twilio_api": {"healthy": true},
    "openai_api": {"healthy": true}
  }
}
```

### 2. Webhook Test

```bash
curl -X POST http://localhost:8000/webhook/test
```

### 3. Send Test Message

Using Twilio Console:
1. Go to **Conversations > Manage Conversations**
2. Create a new conversation
3. Add a participant (your phone number)
4. Send a message like "Hello, I need help with order #12345"
5. Check your application logs for processing

## Troubleshooting

### Common Issues

#### 1. "Module not found" errors
```bash
# Ensure you're in the right directory and virtual environment is activated
pwd
which python
pip list
```

#### 2. Database connection errors
```bash
# Check if database directory exists and is writable
ls -la data/
# Recreate database
rm -f data/conversations.db
python -c "from src.services.session_service import SessionService; import asyncio; asyncio.run(SessionService().create_tables())"
```

#### 3. Twilio webhook not receiving calls
- Verify ngrok is running: `curl https://your-ngrok-url.ngrok.io/webhook/test`
- Check Twilio webhook configuration
- Verify webhook URLs are HTTPS (required by Twilio)

#### 4. OpenAI API errors
- Verify API key is correct and has credits
- Check rate limits in OpenAI dashboard
- Ensure model name is correct (e.g., `gpt-4o-mini`)

#### 5. Twilio CLI Issues

**Authentication Problems:**
```bash
# Check current profile
twilio profiles:list

# Re-authenticate if needed
twilio login

# Switch between profiles
twilio profiles:use PROFILE_NAME
```

**Service Configuration Verification:**
```bash
# Check if Conversations service exists
twilio conversations:v1:services:list

# Verify service configuration
CONVERSATIONS_SERVICE_SID="ISxxxxxxxxxxxxx"  # Your service SID
twilio conversations:v1:services:configuration:fetch --path-sid $CONVERSATIONS_SERVICE_SID

# Check webhook configuration
twilio conversations:v1:services:configuration:webhooks:fetch --path-sid $CONVERSATIONS_SERVICE_SID
```

**Phone Number and Messaging Issues:**
```bash
# List all phone numbers
twilio phone-numbers:list

# Check phone number configuration
PHONE_NUMBER_SID="PNxxxxxxxxxxxxx"  # Your phone number SID
twilio phone-numbers:fetch $PHONE_NUMBER_SID

# List messaging services
twilio messaging:services:list

# Check messaging service configuration
MESSAGING_SERVICE_SID="MGxxxxxxxxxxxxx"  # Your messaging service SID
twilio messaging:services:fetch $MESSAGING_SERVICE_SID

# List phone numbers in messaging service
twilio messaging:services:phone-numbers:list --service-sid $MESSAGING_SERVICE_SID
```

**Address Configuration Debugging:**
```bash
# List all address configurations
twilio conversations:v1:address-configurations:list

# Check specific address configuration
ADDRESS_CONFIG_SID="IGxxxxxxxxxxxxx"  # Your address config SID
twilio conversations:v1:address-configurations:fetch --sid $ADDRESS_CONFIG_SID
```

**Testing Webhook Connectivity:**
```bash
# Test webhook endpoint directly
NGROK_URL="https://your-ngrok-url.ngrok.io"
curl -X POST "$NGROK_URL/webhook/test" \
  -H "Content-Type: application/json" \
  -d '{"test": true}'

# Check ngrok is running and accessible
curl -I "$NGROK_URL"

# Test from Twilio's perspective (replace with your service SID)
twilio conversations:v1:services:configuration:webhooks:update \
  --path-sid $CONVERSATIONS_SERVICE_SID \
  --pre-webhook-url "${NGROK_URL}/webhook/test" \
  --method POST
```

#### 6. Complete Setup Verification

```bash
# Run this complete verification script
#!/bin/bash

# Set your service SID
CONVERSATIONS_SERVICE_SID="ISxxxxxxxxxxxxx"  # Replace with your actual SID

echo "🔍 Verifying Twilio Setup..."

# 1. Check Conversations service
echo "1. Checking Conversations service..."
twilio conversations:v1:services:fetch --sid $CONVERSATIONS_SERVICE_SID

# 2. Check webhook configuration
echo "2. Checking webhook configuration..."
twilio conversations:v1:services:configuration:webhooks:fetch --path-sid $CONVERSATIONS_SERVICE_SID

# 3. Check address configurations
echo "3. Checking address configurations..."
twilio conversations:v1:address-configurations:list

# 4. Test webhook endpoint
echo "4. Testing webhook endpoint..."
NGROK_URL=$(curl -s localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url')
if [ "$NGROK_URL" != "null" ]; then
    curl -X POST "$NGROK_URL/webhook/test"
else
    echo "❌ ngrok not running or not accessible"
fi

echo "✅ Verification complete!"
```

### Logs and Debugging

#### View Application Logs
```bash
# Docker
docker-compose logs -f app

# Local
tail -f logs/application.log
```

#### Enable Debug Logging
Set `LOG_LEVEL=DEBUG` in your `.env` file and restart the application.

#### Test Individual Components
```bash
# Test Twilio connection
python -c "from src.services.twilio_service import TwilioConversationService; t = TwilioConversationService(); print('Twilio OK')"

# Test OpenAI connection
python -c "from src.services.agent_service import CustomerServiceAgent; a = CustomerServiceAgent(); print('OpenAI OK')"
```

## Next Steps

Once you have the basic setup working:

1. **Customize the Agent**: Edit `config/agent_config.yml` to match your business needs
2. **Add Tools**: Implement custom tools for order lookup, product search, etc.
3. **Configure Production**: See `deployment.md` for production deployment guide
4. **Monitor Performance**: Set up logging and monitoring (see `configuration.md`)

## Getting Help

- **Documentation**: Check other files in the `docs/` directory
- **Issues**: Report bugs at https://github.com/twilio/twilio-openai-conversations/issues
- **Twilio Support**: https://support.twilio.com/
- **OpenAI Support**: https://help.openai.com/