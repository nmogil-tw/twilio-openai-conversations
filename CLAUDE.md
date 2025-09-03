# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Development Notes

## Package Management
This project uses [UV](https://docs.astral.sh/uv/) for Python package management.

### Common Commands:
- `uv sync` - Install dependencies from pyproject.toml
- `uv sync --dev` - Install with development dependencies  
- `uv run <command>` - Run commands in the project environment
- `uv add <package>` - Add a new dependency
- `uv add --dev <package>` - Add a development dependency
- `uv remove <package>` - Remove a dependency

### Running the Application:
- Development: `uv run uvicorn src.main:app --reload`
- Production: `uv run uvicorn src.main:app --host 0.0.0.0 --port 8000`

### Running Tests:
- `uv run pytest tests/`

### Database Initialization:
- `uv run python3 -c "from src.services.session_service import SessionService; import asyncio; asyncio.run(SessionService().create_tables())"`

### Development and Quality Tools:
- Code formatting: `uv run black .`
- Import sorting: `uv run isort .`
- Linting: `uv run flake8`
- Type checking: `uv run mypy src/`

## Docker Development:
- `docker-compose up` - Start development environment
- `docker-compose -f docker-compose.yml -f docker-compose.production.yml up` - Start with production dependencies (PostgreSQL + Redis)

## Code Architecture

### High-Level Structure
This is a **FastAPI-based Twilio Conversations + OpenAI integration** that processes customer messages through multiple channels (SMS, WhatsApp, Voice) using the **OpenAI Agents SDK** for intelligent, multi-agent customer service.

### Core Components

#### 1. FastAPI Application (`src/main.py`)
- **Application Lifecycle**: Managed startup/shutdown with database initialization
- **Middleware Stack**: CORS, trusted hosts, security headers
- **Route Organization**: Health, webhooks, and voice endpoints
- **Error Handling**: Global exception handlers with structured logging

#### 2. Configuration Management (`config/settings.py`)
- **Pydantic Settings**: Environment-based configuration with validation
- **Grouped Settings**: Twilio, OpenAI, database, Redis, security, agent, and voice configs
- **Proxy Pattern**: Convenient dot-notation access (e.g., `settings.twilio.account_sid`)

#### 3. Multi-Agent System (`src/services/agent_service.py`)
- **OpenAI Agents SDK Integration**: Uses Agent, Runner, and function tools
- **Function Tools**: Order lookup, product search, store hours, FAQ responses
- **Agent Configuration**: YAML-based agent instructions and knowledge base
- **Session Management**: SQLite-based conversation persistence

#### 4. Webhook Processing (`src/handlers/webhook_handler.py`)
- **Signature Validation**: Twilio webhook security verification
- **Message Routing**: Determines when to engage AI vs. human agents
- **Typing Indicators**: Shows processing status to users
- **Response Coordination**: Manages AI response delivery via Twilio API

#### 5. Voice Integration (`src/handlers/voice_handler.py`)
- **TwiML Generation**: Creates ConversationRelay connections for voice calls
- **WebSocket Communication**: Real-time voice-to-text processing
- **Voice Interstitials**: Natural conversation flow ("Let me check that for you")
- **Speech Processing**: Text-to-speech optimization for phone conversations

#### 6. Twilio Service Layer (`src/services/twilio_service.py`)
- **Conversations API**: Message sending, participant management
- **Multi-Channel Support**: SMS, WhatsApp, web chat, voice
- **Rate Limiting**: Handles Twilio API constraints
- **Error Handling**: Retry logic and fallback mechanisms

#### 7. Session Management (`src/services/session_service.py`)
- **Database Layer**: SQLAlchemy models for conversations and messages
- **Session Persistence**: Maintains conversation context across interactions
- **History Management**: Configurable conversation history limits
- **Storage Backends**: SQLite (dev) / PostgreSQL + Redis (production)

### Key Design Patterns

#### Multi-Agent Architecture
- **Triage Agent**: Routes conversations to appropriate specialists
- **Specialist Agents**: Billing, technical support, general assistance
- **Function Tools**: External integrations (order systems, product catalogs)
- **Agent Handoffs**: Seamless transitions between agents based on context

#### Request Processing Flow
```
Twilio Webhook → Signature Validation → Message Parsing → Agent Selection → 
Function Tool Execution → Response Generation → Message Delivery → Session Storage
```

#### Voice Call Flow
```
Incoming Call → TwiML Generation → ConversationRelay WebSocket → 
Speech-to-Text → Agent Processing → Text-to-Speech → Voice Response
```

## Important Development Considerations

### Security
- Always validate webhook signatures in production (`VALIDATE_WEBHOOK_SIGNATURES=true`)
- Use proper secrets management for API keys (not .env files in production)
- Configure restrictive CORS origins for production deployments

### Performance
- Database connection pooling configured via `DATABASE_POOL_SIZE` and `DATABASE_MAX_OVERFLOW`
- Redis used for session caching in multi-instance deployments
- Rate limiting applied to prevent API abuse

### Testing Strategy
- Unit tests in `tests/` directory cover core services
- Mock external APIs (Twilio, OpenAI) for consistent testing
- Integration tests validate webhook processing end-to-end

### Configuration Management
- Environment-specific configs: `.env.local`, `.env.production`, etc.
- Agent behavior configured via YAML files in `config/`
- Feature flags available for voice, streaming, and other capabilities

### Deployment Notes
- Development uses SQLite + in-memory sessions
- Production requires PostgreSQL + Redis for scalability
- Voice features require ngrok or public domain for WebSocket connections
- OpenAI Agents SDK provides built-in tracing and monitoring

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.