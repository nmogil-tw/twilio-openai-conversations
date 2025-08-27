#!/bin/bash

# Deployment script for Twilio Conversations + OpenAI Agents integration
# Supports multiple deployment targets: Docker, Kubernetes, Heroku, and more

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_NAME="twilio-openai-conversations"
VERSION="${VERSION:-latest}"
ENVIRONMENT="${ENVIRONMENT:-production}"

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
        return 0
    else
        return 1
    fi
}

show_help() {
    echo "Deployment script for Twilio + OpenAI Conversations"
    echo ""
    echo "Usage: $0 [TARGET] [OPTIONS]"
    echo ""
    echo "Deployment Targets:"
    echo "  docker        Build and run with Docker Compose"
    echo "  kubernetes    Deploy to Kubernetes cluster"
    echo "  heroku        Deploy to Heroku"
    echo "  railway       Deploy to Railway"
    echo "  gcp           Deploy to Google Cloud Run"
    echo "  aws           Deploy to AWS ECS"
    echo "  build         Build Docker image only"
    echo "  test          Run tests before deployment"
    echo ""
    echo "Options:"
    echo "  -e, --env ENV         Environment (development|staging|production)"
    echo "  -v, --version VER     Version tag for deployment"
    echo "  -h, --help           Show this help message"
    echo "  --no-build           Skip building Docker image"
    echo "  --no-test            Skip running tests"
    echo "  --dry-run            Show what would be deployed without executing"
    echo ""
    echo "Environment Variables:"
    echo "  VERSION               Version tag (default: latest)"
    echo "  ENVIRONMENT           Environment name (default: production)"
    echo "  DOCKER_REGISTRY       Docker registry URL"
    echo "  KUBE_CONTEXT          Kubernetes context to use"
    echo ""
    echo "Examples:"
    echo "  $0 docker --env development"
    echo "  $0 kubernetes --version v1.2.3"
    echo "  $0 heroku --env production"
}

# Parse command line arguments
TARGET=""
BUILD_IMAGE=true
RUN_TESTS=true
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        docker|kubernetes|heroku|railway|gcp|aws|build|test)
            TARGET="$1"
            shift
            ;;
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        --no-build)
            BUILD_IMAGE=false
            shift
            ;;
        --no-test)
            RUN_TESTS=false
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

if [ -z "$TARGET" ]; then
    print_error "No deployment target specified"
    show_help
    exit 1
fi

# Banner
echo -e "${BLUE}"
echo "================================================="
echo "  Twilio + OpenAI Conversations Deployment"
echo "================================================="
echo -e "${NC}"
echo "Target: $TARGET"
echo "Environment: $ENVIRONMENT"
echo "Version: $VERSION"
echo "Build Image: $BUILD_IMAGE"
echo "Run Tests: $RUN_TESTS"
echo "Dry Run: $DRY_RUN"
echo ""

cd "$PROJECT_DIR"

# Pre-deployment checks
pre_deployment_checks() {
    print_status "Running pre-deployment checks..."
    
    # Check if .env file exists for the environment
    ENV_FILE=".env"
    if [ "$ENVIRONMENT" != "production" ]; then
        ENV_FILE=".env.$ENVIRONMENT"
    fi
    
    if [ ! -f "$ENV_FILE" ]; then
        print_warning "Environment file $ENV_FILE not found"
        if [ -f ".env.example" ]; then
            print_status "You can create it from .env.example"
        fi
    fi
    
    # Check required files
    REQUIRED_FILES=("requirements.txt" "Dockerfile" "src/main.py")
    for file in "${REQUIRED_FILES[@]}"; do
        if [ ! -f "$file" ]; then
            print_error "Required file not found: $file"
            exit 1
        fi
    done
    
    print_success "Pre-deployment checks passed"
}

# Run tests
run_tests() {
    if [ "$RUN_TESTS" = false ]; then
        return 0
    fi
    
    print_status "Running tests..."
    
    if [ ! -f "requirements.txt" ] || ! grep -q pytest requirements.txt; then
        print_warning "pytest not found in requirements.txt, skipping tests"
        return 0
    fi
    
    # Set up test environment
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Run tests
    if $DRY_RUN; then
        print_status "[DRY RUN] Would run: pytest tests/"
    else
        pytest tests/ --tb=short -v || {
            print_error "Tests failed"
            exit 1
        }
        print_success "Tests passed"
    fi
}

# Build Docker image
build_docker_image() {
    if [ "$BUILD_IMAGE" = false ]; then
        return 0
    fi
    
    print_status "Building Docker image..."
    
    IMAGE_TAG="${DOCKER_REGISTRY:-}${APP_NAME}:${VERSION}"
    
    if $DRY_RUN; then
        print_status "[DRY RUN] Would build: docker build -t $IMAGE_TAG ."
    else
        docker build -t "$IMAGE_TAG" .
        print_success "Built Docker image: $IMAGE_TAG"
    fi
}

# Docker deployment
deploy_docker() {
    print_status "Deploying with Docker Compose..."
    
    COMPOSE_FILE="docker-compose.yml"
    if [ "$ENVIRONMENT" != "production" ]; then
        if [ -f "docker-compose.$ENVIRONMENT.yml" ]; then
            COMPOSE_FILE="docker-compose.$ENVIRONMENT.yml"
        fi
    fi
    
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "Docker Compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    if $DRY_RUN; then
        print_status "[DRY RUN] Would run: docker-compose -f $COMPOSE_FILE up -d"
    else
        # Set environment variables
        export VERSION
        export ENVIRONMENT
        
        # Deploy
        docker-compose -f "$COMPOSE_FILE" up -d
        
        # Wait for health check
        print_status "Waiting for application to be healthy..."
        sleep 10
        
        if curl -f http://localhost:8000/health >/dev/null 2>&1; then
            print_success "Application deployed and healthy"
            print_status "Access the application at: http://localhost:8000"
        else
            print_error "Application health check failed"
            docker-compose -f "$COMPOSE_FILE" logs app
            exit 1
        fi
    fi
}

# Kubernetes deployment
deploy_kubernetes() {
    print_status "Deploying to Kubernetes..."
    
    if ! check_command "kubectl"; then
        print_error "kubectl is required for Kubernetes deployment"
        exit 1
    fi
    
    # Check if k8s manifests exist
    K8S_DIR="k8s"
    if [ ! -d "$K8S_DIR" ]; then
        print_error "Kubernetes manifests directory not found: $K8S_DIR"
        exit 1
    fi
    
    # Set kubectl context if specified
    if [ -n "$KUBE_CONTEXT" ]; then
        kubectl config use-context "$KUBE_CONTEXT"
        print_status "Using Kubernetes context: $KUBE_CONTEXT"
    fi
    
    if $DRY_RUN; then
        print_status "[DRY RUN] Would apply Kubernetes manifests from $K8S_DIR/"
        kubectl apply --dry-run=client -f "$K8S_DIR/"
    else
        # Apply manifests
        kubectl apply -f "$K8S_DIR/"
        
        # Wait for deployment rollout
        kubectl rollout status deployment/${APP_NAME}-app -n twilio-openai --timeout=300s
        
        # Get service endpoint
        SERVICE_URL=$(kubectl get service ${APP_NAME}-service -n twilio-openai -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
        
        print_success "Deployed to Kubernetes"
        if [ "$SERVICE_URL" != "pending" ]; then
            print_status "Application URL: http://$SERVICE_URL"
        else
            print_status "Service URL pending - check 'kubectl get services -n twilio-openai'"
        fi
    fi
}

# Heroku deployment
deploy_heroku() {
    print_status "Deploying to Heroku..."
    
    if ! check_command "heroku"; then
        print_error "Heroku CLI is required for Heroku deployment"
        print_status "Install from: https://devcenter.heroku.com/articles/heroku-cli"
        exit 1
    fi
    
    # Check if Heroku app exists
    HEROKU_APP="${HEROKU_APP:-${APP_NAME}-${ENVIRONMENT}}"
    
    if $DRY_RUN; then
        print_status "[DRY RUN] Would deploy to Heroku app: $HEROKU_APP"
        print_status "[DRY RUN] Would run: git push heroku main"
    else
        # Create app if it doesn't exist
        if ! heroku apps:info "$HEROKU_APP" >/dev/null 2>&1; then
            print_status "Creating Heroku app: $HEROKU_APP"
            heroku create "$HEROKU_APP"
        fi
        
        # Set environment variables
        print_status "Setting environment variables..."
        if [ -f ".env.$ENVIRONMENT" ]; then
            # Parse .env file and set config vars
            while IFS='=' read -r key value; do
                # Skip comments and empty lines
                [[ $key =~ ^#.*$ ]] && continue
                [[ -z $key ]] && continue
                
                # Remove quotes from value
                value="${value%\"}"
                value="${value#\"}"
                
                heroku config:set "$key=$value" --app "$HEROKU_APP"
            done < ".env.$ENVIRONMENT"
        fi
        
        # Deploy
        git push heroku main
        
        # Run database migrations if needed
        heroku run python -c "from src.services.session_service import SessionService; import asyncio; asyncio.run(SessionService().create_tables())" --app "$HEROKU_APP"
        
        # Open app
        APP_URL=$(heroku info --app "$HEROKU_APP" -j | python3 -c "import sys, json; print(json.load(sys.stdin)['app']['web_url'])")
        print_success "Deployed to Heroku: $APP_URL"
    fi
}

# Railway deployment
deploy_railway() {
    print_status "Deploying to Railway..."
    
    if ! check_command "railway"; then
        print_error "Railway CLI is required for Railway deployment"
        print_status "Install from: https://docs.railway.app/develop/cli"
        exit 1
    fi
    
    if $DRY_RUN; then
        print_status "[DRY RUN] Would run: railway up"
    else
        railway up
        print_success "Deployed to Railway"
        
        # Get deployment URL
        RAILWAY_URL=$(railway status --json | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('deployments', [{}])[0].get('url', 'N/A'))")
        if [ "$RAILWAY_URL" != "N/A" ]; then
            print_status "Application URL: $RAILWAY_URL"
        fi
    fi
}

# Google Cloud Run deployment
deploy_gcp() {
    print_status "Deploying to Google Cloud Run..."
    
    if ! check_command "gcloud"; then
        print_error "Google Cloud CLI is required for GCP deployment"
        print_status "Install from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    # Configuration
    PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project)}"
    REGION="${GCP_REGION:-us-central1}"
    SERVICE_NAME="${GCP_SERVICE_NAME:-${APP_NAME}}"
    
    if [ -z "$PROJECT_ID" ]; then
        print_error "GCP project ID not set. Set GCP_PROJECT_ID environment variable or configure gcloud"
        exit 1
    fi
    
    if $DRY_RUN; then
        print_status "[DRY RUN] Would deploy to Cloud Run:"
        print_status "  Project: $PROJECT_ID"
        print_status "  Region: $REGION"
        print_status "  Service: $SERVICE_NAME"
    else
        # Build and submit to Cloud Build
        gcloud builds submit --tag "gcr.io/$PROJECT_ID/$SERVICE_NAME"
        
        # Deploy to Cloud Run
        gcloud run deploy "$SERVICE_NAME" \
            --image "gcr.io/$PROJECT_ID/$SERVICE_NAME" \
            --platform managed \
            --region "$REGION" \
            --allow-unauthenticated \
            --set-env-vars "ENVIRONMENT=$ENVIRONMENT" \
            --memory 512Mi \
            --cpu 1 \
            --max-instances 10
        
        # Get service URL
        SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")
        print_success "Deployed to Cloud Run: $SERVICE_URL"
    fi
}

# AWS ECS deployment
deploy_aws() {
    print_status "Deploying to AWS ECS..."
    
    if ! check_command "aws"; then
        print_error "AWS CLI is required for AWS deployment"
        print_status "Install from: https://aws.amazon.com/cli/"
        exit 1
    fi
    
    # Configuration
    AWS_REGION="${AWS_REGION:-us-east-1}"
    ECS_CLUSTER="${ECS_CLUSTER:-${APP_NAME}-cluster}"
    ECS_SERVICE="${ECS_SERVICE:-${APP_NAME}-service}"
    ECR_REPO="${ECR_REPO:-${APP_NAME}}"
    
    if $DRY_RUN; then
        print_status "[DRY RUN] Would deploy to AWS ECS:"
        print_status "  Region: $AWS_REGION"
        print_status "  Cluster: $ECS_CLUSTER"
        print_status "  Service: $ECS_SERVICE"
        print_status "  ECR Repo: $ECR_REPO"
    else
        # Get ECR login
        aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        
        # Build and push to ECR
        ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:${VERSION}"
        docker build -t "$ECR_URI" .
        docker push "$ECR_URI"
        
        # Update ECS service (assumes task definition exists)
        aws ecs update-service \
            --cluster "$ECS_CLUSTER" \
            --service "$ECS_SERVICE" \
            --force-new-deployment \
            --region "$AWS_REGION"
        
        print_success "Deployed to AWS ECS"
        print_status "Check deployment status in AWS Console"
    fi
}

# Main deployment logic
main() {
    pre_deployment_checks
    
    case $TARGET in
        build)
            build_docker_image
            ;;
        test)
            run_tests
            ;;
        docker)
            run_tests
            build_docker_image
            deploy_docker
            ;;
        kubernetes)
            run_tests
            build_docker_image
            deploy_kubernetes
            ;;
        heroku)
            run_tests
            deploy_heroku
            ;;
        railway)
            run_tests
            deploy_railway
            ;;
        gcp)
            run_tests
            build_docker_image
            deploy_gcp
            ;;
        aws)
            run_tests
            build_docker_image
            deploy_aws
            ;;
        *)
            print_error "Unknown deployment target: $TARGET"
            exit 1
            ;;
    esac
    
    print_success "Deployment completed successfully!"
    
    # Post-deployment checks
    if [ "$TARGET" != "build" ] && [ "$TARGET" != "test" ] && [ "$DRY_RUN" = false ]; then
        print_status "Running post-deployment verification..."
        
        # Wait a bit for service to start
        sleep 5
        
        # Try to check health endpoint (this is deployment-specific)
        case $TARGET in
            docker)
                if curl -f http://localhost:8000/health >/dev/null 2>&1; then
                    print_success "Health check passed"
                else
                    print_warning "Health check failed - service may still be starting"
                fi
                ;;
            *)
                print_status "Manual health check recommended for this deployment type"
                ;;
        esac
    fi
}

# Run main function
main