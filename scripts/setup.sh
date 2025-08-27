#!/bin/bash

# Setup script for Twilio Conversations + OpenAI Agents integration
# This script helps with initial setup and configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if command -v "$1" >/dev/null 2>&1; then
        print_success "$1 is installed"
        return 0
    else
        print_error "$1 is not installed"
        return 1
    fi
}

# Banner
echo -e "${BLUE}"
echo "================================================="
echo "  Twilio + OpenAI Conversations Setup Script"
echo "================================================="
echo -e "${NC}"

# Check prerequisites
print_status "Checking prerequisites..."

MISSING_DEPS=()

if ! check_command "python3"; then
    MISSING_DEPS+=("python3")
fi

if ! check_command "pip3"; then
    MISSING_DEPS+=("pip3")
fi

if ! check_command "git"; then
    MISSING_DEPS+=("git")
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    print_error "Python 3.11+ is required. Current version: $PYTHON_VERSION"
    MISSING_DEPS+=("python3.11+")
else
    print_success "Python version $PYTHON_VERSION meets requirements"
fi

if [ ${#MISSING_DEPS[@]} -ne 0 ]; then
    print_error "Missing dependencies: ${MISSING_DEPS[*]}"
    print_status "Please install the missing dependencies and run this script again"
    exit 1
fi

# Check optional tools
print_status "Checking optional tools..."
check_command "docker" || print_warning "Docker not found - Docker deployment won't be available"
check_command "docker-compose" || print_warning "Docker Compose not found - Docker deployment won't be available"
check_command "ngrok" || print_warning "ngrok not found - local webhook testing will require manual tunneling"

# Setup options
echo ""
print_status "Setup Options:"
echo "1. Full setup (virtual environment, dependencies, configuration)"
echo "2. Dependencies only (install Python packages)"
echo "3. Configuration only (setup .env file)"
echo "4. Database initialization"
echo "5. Docker setup"
echo "6. Twilio CLI setup (configure Conversations service)"

read -p "Choose an option (1-6): " SETUP_OPTION

case $SETUP_OPTION in
    1)
        SETUP_VENV=true
        SETUP_DEPS=true
        SETUP_CONFIG=true
        SETUP_DB=true
        ;;
    2)
        SETUP_VENV=false
        SETUP_DEPS=true
        SETUP_CONFIG=false
        SETUP_DB=false
        ;;
    3)
        SETUP_VENV=false
        SETUP_DEPS=false
        SETUP_CONFIG=true
        SETUP_DB=false
        ;;
    4)
        SETUP_VENV=false
        SETUP_DEPS=false
        SETUP_CONFIG=false
        SETUP_DB=true
        ;;
    5)
        print_status "Setting up Docker environment..."
        if [ -f "docker-compose.yml" ]; then
            docker-compose up -d
            print_success "Docker environment started"
            print_status "Access the application at http://localhost:8000"
            print_status "API documentation at http://localhost:8000/docs"
            exit 0
        else
            print_error "docker-compose.yml not found"
            exit 1
        fi
        ;;
    6)
        print_status "Setting up Twilio CLI configuration..."
        setup_twilio_cli
        exit 0
        ;;
    *)
        print_error "Invalid option selected"
        exit 1
        ;;
esac

# Virtual environment setup
if [ "$SETUP_VENV" = true ]; then
    print_status "Setting up Python virtual environment..."
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists"
        read -p "Do you want to recreate it? (y/N): " RECREATE_VENV
        if [ "$RECREATE_VENV" = "y" ] || [ "$RECREATE_VENV" = "Y" ]; then
            rm -rf venv
            print_status "Removed existing virtual environment"
        else
            print_status "Using existing virtual environment"
        fi
    fi
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Created virtual environment"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    print_success "Activated virtual environment"
    
    # Upgrade pip
    pip install --upgrade pip
    print_success "Upgraded pip"
fi

# Dependencies installation
if [ "$SETUP_DEPS" = true ]; then
    print_status "Installing Python dependencies..."
    
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found"
        exit 1
    fi
    
    # If virtual environment wasn't set up in this run, try to activate existing one
    if [ "$SETUP_VENV" = false ] && [ -d "venv" ]; then
        source venv/bin/activate
        print_status "Activated existing virtual environment"
    fi
    
    pip install -r requirements.txt
    print_success "Installed Python dependencies"
    
    # Install development dependencies if they exist
    if [ -f "requirements-dev.txt" ]; then
        pip install -r requirements-dev.txt
        print_success "Installed development dependencies"
    fi
fi

# Configuration setup
if [ "$SETUP_CONFIG" = true ]; then
    print_status "Setting up configuration..."
    
    if [ ! -f ".env.example" ]; then
        print_error ".env.example not found"
        exit 1
    fi
    
    if [ -f ".env" ]; then
        print_warning ".env file already exists"
        read -p "Do you want to overwrite it? (y/N): " OVERWRITE_ENV
        if [ "$OVERWRITE_ENV" != "y" ] && [ "$OVERWRITE_ENV" != "Y" ]; then
            print_status "Keeping existing .env file"
        else
            cp .env.example .env
            print_success "Created .env file from template"
        fi
    else
        cp .env.example .env
        print_success "Created .env file from template"
    fi
    
    print_status "Please configure the following in your .env file:"
    echo "  - TWILIO_ACCOUNT_SID (from Twilio Console)"
    echo "  - TWILIO_AUTH_TOKEN (from Twilio Console)"
    echo "  - TWILIO_CONVERSATIONS_SERVICE_SID (from Twilio Console > Conversations)"
    echo "  - OPENAI_API_KEY (from OpenAI Platform > API Keys)"
    echo ""
    
    read -p "Do you want to configure these now? (y/N): " CONFIGURE_NOW
    if [ "$CONFIGURE_NOW" = "y" ] || [ "$CONFIGURE_NOW" = "Y" ]; then
        configure_credentials
    else
        print_warning "Remember to configure your .env file before running the application"
    fi
fi

# Database initialization
if [ "$SETUP_DB" = true ]; then
    print_status "Initializing database..."
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Create data directory
    mkdir -p data
    
    # Initialize database tables
    python3 -c "
import asyncio
from src.services.session_service import SessionService

async def init_db():
    service = SessionService()
    await service.create_tables()
    print('Database tables created successfully')

asyncio.run(init_db())
" 2>/dev/null || {
        print_warning "Database initialization failed - make sure dependencies are installed"
        print_status "You can run database initialization later with:"
        echo "  python3 -c \"from src.services.session_service import SessionService; import asyncio; asyncio.run(SessionService().create_tables())\""
    }
fi

# Function to setup Twilio CLI and create services
setup_twilio_cli() {
    print_status "Setting up Twilio CLI and creating services..."
    
    # Check if Twilio CLI is installed
    if ! check_command "twilio"; then
        print_status "Installing Twilio CLI..."
        if check_command "npm"; then
            npm install -g twilio-cli
        else
            print_error "npm is required to install Twilio CLI"
            print_status "Please install Node.js and npm, then run: npm install -g twilio-cli"
            return 1
        fi
    fi
    
    # Check if jq is available
    if ! check_command "jq"; then
        print_warning "jq is not installed - some commands may not work properly"
        print_status "Install jq with: brew install jq (macOS) or apt-get install jq (Linux)"
    fi
    
    # Login to Twilio
    print_status "Logging into Twilio..."
    if ! twilio profiles:list >/dev/null 2>&1; then
        print_status "Please authenticate with Twilio..."
        twilio login
    else
        print_success "Already logged into Twilio"
    fi
    
    # Check if ngrok is running
    NGROK_URL=""
    if check_command "curl" && curl -s localhost:4040/api/tunnels >/dev/null 2>&1; then
        if check_command "jq"; then
            NGROK_URL=$(curl -s localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url // empty')
        fi
    fi
    
    if [ -z "$NGROK_URL" ]; then
        print_warning "ngrok doesn't appear to be running"
        print_status "Please start ngrok in another terminal: ngrok http 8000"
        read -p "Enter your ngrok HTTPS URL (e.g., https://abc123.ngrok.io): " NGROK_URL
        
        if [[ ! "$NGROK_URL" =~ ^https:// ]]; then
            print_error "Webhook URL must be HTTPS"
            return 1
        fi
    else
        print_success "Detected ngrok URL: $NGROK_URL"
    fi
    
    # Create Conversations service
    print_status "Creating Twilio Conversations service..."
    
    if check_command "jq"; then
        CONVERSATIONS_SERVICE_SID=$(twilio api:conversations:v1:services:create \
            --friendly-name "AI Customer Service" \
            --query "sid" \
            --output json | jq -r .)
    else
        # Fallback without jq
        print_status "Creating service (manual SID extraction needed)..."
        twilio api:conversations:v1:services:create --friendly-name "AI Customer Service"
        print_status "Please copy the Service SID from the output above"
        read -p "Enter the Conversations Service SID (starts with IS): " CONVERSATIONS_SERVICE_SID
    fi
    
    if [ -z "$CONVERSATIONS_SERVICE_SID" ] || [ "$CONVERSATIONS_SERVICE_SID" = "null" ]; then
        print_error "Failed to create Conversations service"
        return 1
    fi
    
    print_success "Created Conversations service: $CONVERSATIONS_SERVICE_SID"
    
    # Configure webhooks
    print_status "Configuring webhooks..."
    twilio api:conversations:v1:services:configuration:webhooks:update \
        --path-sid "$CONVERSATIONS_SERVICE_SID" \
        --pre-webhook-url "${NGROK_URL}/webhook/message-added" \
        --method POST \
        --filters "onMessageAdded" \
        --filters "onParticipantAdded" \
        --filters "onConversationStateUpdated"
    
    print_success "Configured webhooks"
    
    # Ask about phone number setup
    echo ""
    read -p "Do you want to set up SMS with a phone number? (y/N): " SETUP_SMS
    
    if [ "$SETUP_SMS" = "y" ] || [ "$SETUP_SMS" = "Y" ]; then
        setup_sms_service "$CONVERSATIONS_SERVICE_SID" "$NGROK_URL"
    fi
    
    # Update .env file
    print_status "Updating .env file..."
    if [ ! -f ".env" ]; then
        cp .env.example .env
    fi
    
    # Update or add the Conversations Service SID
    if grep -q "TWILIO_CONVERSATIONS_SERVICE_SID=" .env; then
        sed -i.bak "s/TWILIO_CONVERSATIONS_SERVICE_SID=.*/TWILIO_CONVERSATIONS_SERVICE_SID=$CONVERSATIONS_SERVICE_SID/" .env
    else
        echo "TWILIO_CONVERSATIONS_SERVICE_SID=$CONVERSATIONS_SERVICE_SID" >> .env
    fi
    
    rm -f .env.bak
    
    print_success "Twilio CLI setup completed!"
    print_status "Next steps:"
    echo "1. Configure your OpenAI API key in .env"
    echo "2. Start your application: python -m uvicorn src.main:app --reload"
    echo "3. Test by sending an SMS to your phone number (if configured)"
}

# Function to setup SMS service
setup_sms_service() {
    local conversations_service_sid="$1"
    local ngrok_url="$2"
    
    print_status "Setting up SMS service..."
    
    # Search for available numbers
    print_status "Searching for available phone numbers..."
    twilio phone-numbers:list:local --country-code US --sms-enabled --limit 5
    
    echo ""
    read -p "Enter area code for phone number (e.g., 415): " AREA_CODE
    AREA_CODE=${AREA_CODE:-415}
    
    # Purchase phone number
    print_status "Purchasing phone number with area code $AREA_CODE..."
    
    if check_command "jq"; then
        PHONE_NUMBER_SID=$(twilio phone-numbers:buy:local \
            --country-code US \
            --area-code "$AREA_CODE" \
            --sms-enabled \
            --query "sid" \
            --output json | jq -r .)
        
        PHONE_NUMBER=$(twilio phone-numbers:fetch "$PHONE_NUMBER_SID" \
            --query "phoneNumber" \
            --output json | jq -r .)
    else
        # Fallback without jq
        twilio phone-numbers:buy:local --country-code US --area-code "$AREA_CODE" --sms-enabled
        print_status "Please copy the Phone Number SID and number from the output above"
        read -p "Enter the Phone Number SID (starts with PN): " PHONE_NUMBER_SID
        read -p "Enter the phone number (e.g., +14155551234): " PHONE_NUMBER
    fi
    
    if [ -z "$PHONE_NUMBER_SID" ] || [ "$PHONE_NUMBER_SID" = "null" ]; then
        print_error "Failed to purchase phone number"
        return 1
    fi
    
    print_success "Purchased phone number: $PHONE_NUMBER (SID: $PHONE_NUMBER_SID)"
    
    # Create messaging service
    print_status "Creating messaging service..."
    
    if check_command "jq"; then
        MESSAGING_SERVICE_SID=$(twilio messaging:services:create \
            --friendly-name "AI Customer Service SMS" \
            --query "sid" \
            --output json | jq -r .)
    else
        twilio messaging:services:create --friendly-name "AI Customer Service SMS"
        read -p "Enter the Messaging Service SID (starts with MG): " MESSAGING_SERVICE_SID
    fi
    
    # Add phone number to messaging service
    twilio messaging:services:phone-numbers:create \
        --service-sid "$MESSAGING_SERVICE_SID" \
        --phone-number-sid "$PHONE_NUMBER_SID"
    
    # Create address configuration for Conversations
    twilio conversations:v1:address-configurations:create \
        --type sms \
        --address "$PHONE_NUMBER" \
        --friendly-name "SMS Channel" \
        --address-sid "$MESSAGING_SERVICE_SID"
    
    print_success "SMS service configured successfully!"
    print_status "You can now send SMS messages to $PHONE_NUMBER"
    
    # Save IDs to .env for reference
    echo "" >> .env
    echo "# Twilio Resource IDs (for reference)" >> .env
    echo "# PHONE_NUMBER_SID=$PHONE_NUMBER_SID" >> .env
    echo "# MESSAGING_SERVICE_SID=$MESSAGING_SERVICE_SID" >> .env
    echo "# PHONE_NUMBER=$PHONE_NUMBER" >> .env
}

# Function to configure credentials interactively
configure_credentials() {
    print_status "Interactive credential configuration:"
    
    # Twilio credentials
    echo ""
    echo -e "${YELLOW}Twilio Configuration:${NC}"
    read -p "Enter your Twilio Account SID (AC...): " TWILIO_ACCOUNT_SID
    read -p "Enter your Twilio Auth Token: " TWILIO_AUTH_TOKEN
    read -p "Enter your Twilio Conversations Service SID (IS...): " TWILIO_SERVICE_SID
    
    # OpenAI credentials
    echo ""
    echo -e "${YELLOW}OpenAI Configuration:${NC}"
    read -p "Enter your OpenAI API Key (sk-...): " OPENAI_API_KEY
    read -p "Enter OpenAI Model (default: gpt-4o-mini): " OPENAI_MODEL
    OPENAI_MODEL=${OPENAI_MODEL:-gpt-4o-mini}
    
    # Optional webhook secret
    echo ""
    echo -e "${YELLOW}Security (Optional):${NC}"
    read -p "Enter webhook secret (leave empty to generate): " WEBHOOK_SECRET
    if [ -z "$WEBHOOK_SECRET" ]; then
        WEBHOOK_SECRET=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))")
        print_status "Generated webhook secret: $WEBHOOK_SECRET"
    fi
    
    # Update .env file
    sed -i.bak "s/TWILIO_ACCOUNT_SID=.*/TWILIO_ACCOUNT_SID=$TWILIO_ACCOUNT_SID/" .env
    sed -i.bak "s/TWILIO_AUTH_TOKEN=.*/TWILIO_AUTH_TOKEN=$TWILIO_AUTH_TOKEN/" .env
    sed -i.bak "s/TWILIO_CONVERSATIONS_SERVICE_SID=.*/TWILIO_CONVERSATIONS_SERVICE_SID=$TWILIO_SERVICE_SID/" .env
    sed -i.bak "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$OPENAI_API_KEY/" .env
    sed -i.bak "s/OPENAI_MODEL=.*/OPENAI_MODEL=$OPENAI_MODEL/" .env
    sed -i.bak "s/WEBHOOK_SECRET=.*/WEBHOOK_SECRET=$WEBHOOK_SECRET/" .env
    
    rm .env.bak 2>/dev/null || true
    
    print_success "Configuration saved to .env file"
}

# Test installation
test_installation() {
    print_status "Testing installation..."
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Test imports
    python3 -c "
try:
    from config.settings import settings
    print('✓ Settings loaded successfully')
    
    from src.services.twilio_service import TwilioConversationService
    print('✓ Twilio service imported successfully')
    
    from src.services.agent_service import CustomerServiceAgent
    print('✓ Agent service imported successfully')
    
    print('\\n✅ All core components loaded successfully!')
    
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
except Exception as e:
    print(f'❌ Configuration error: {e}')
    exit(1)
" || {
        print_error "Installation test failed"
        return 1
    }
    
    return 0
}

# Final steps
echo ""
print_status "Setup completed!"

if test_installation; then
    print_success "Installation test passed"
    
    echo ""
    print_status "Next steps:"
    echo "1. Configure your Twilio webhooks to point to your application"
    echo "2. For local development, use ngrok to expose your webhook endpoints:"
    echo "   ngrok http 8000"
    echo "3. Start the application:"
    if [ -d "venv" ]; then
        echo "   source venv/bin/activate"
    fi
    echo "   python -m uvicorn src.main:app --reload"
    echo "4. Visit http://localhost:8000/health to verify the application is running"
    echo "5. Visit http://localhost:8000/docs for API documentation"
    
    echo ""
    print_status "For more information, see:"
    echo "  - docs/setup.md for detailed setup instructions"
    echo "  - docs/configuration.md for advanced configuration options"
    echo "  - docs/deployment.md for production deployment"
else
    print_warning "Installation test failed - please check your configuration"
fi

echo ""
print_success "Setup script completed successfully!"