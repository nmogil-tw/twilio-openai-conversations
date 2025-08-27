# Twilio Conversations + OpenAI Integration

Build AI-powered customer service chatbots that work across SMS, WhatsApp, and messaging channels using Twilio Conversations API and OpenAI.

## ✨ What You Get

- 🤖 **Intelligent AI Assistant** - Handles customer inquiries naturally with OpenAI
- 📱 **Multi-Channel Support** - Works on SMS, WhatsApp, Web Chat
- 🔧 **Built-in Tools** - Order lookup, product search, store hours, FAQ responses
- 🚀 **Production Ready** - Security, monitoring, and scalability included
- ⚡ **5-minute Setup** - Get started quickly with automated scripts

## 🚀 Quick Start

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
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxx
```

### Step 3: Run
```bash
# Start the app
docker-compose up

# In another terminal, expose webhooks
ngrok http 8000
```

**🎉 Done!** Text your Twilio number to chat with your AI assistant.

> **Need help?** The setup script will guide you through Twilio configuration automatically.

## 💬 Example Conversations

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

## 🏗️ How It Works

```
Customer Text ──► Twilio Conversations ──► Your App ──► OpenAI ──► Response
```

Simple flow: Messages come in through Twilio, get processed by your AI agent, and responses are sent back automatically.

## ⚙️ Customization

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

## 🚀 Testing & Development

**Run Tests:**
```bash
pytest
```

**View API Docs:**
Visit http://localhost:8000/docs when running locally.

**Health Check:**
Visit http://localhost:8000/health to verify everything works.

## 📚 Learn More

- **[Setup Guide](docs/setup.md)** - Detailed installation help
- **[Configuration](docs/configuration.md)** - Advanced settings  
- **[Deployment](docs/deployment.md)** - Production tips

## 🤝 Getting Help

- **Issues**: [GitHub Issues](https://github.com/twilio/twilio-openai-conversations/issues)
- **Twilio Docs**: [Conversations API](https://www.twilio.com/docs/conversations)
- **OpenAI Docs**: [OpenAI Platform](https://platform.openai.com/docs)

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file.

---

Built with ❤️ by the Twilio team