# Deployment Guide

This guide covers deployment options for the Twilio Conversations + OpenAI Agents integration, from local development to production environments.

## Deployment Overview

The application supports multiple deployment strategies:

- **Local Development**: Direct Python execution or Docker Compose
- **Container Orchestration**: Kubernetes, Docker Swarm
- **Platform-as-a-Service**: Heroku, Railway, Render
- **Cloud Providers**: AWS, Google Cloud, Azure
- **Serverless**: AWS Lambda, Google Cloud Functions (with adaptations)

## Pre-Deployment Checklist

### ✅ Configuration Verification

```bash
# Test all configurations
python -c "from config.settings import settings; print('✓ Settings loaded')"

# Test database connection
python -c "from src.services.session_service import SessionService; print('✓ Database OK')"

# Test Twilio integration
python -c "from src.services.twilio_service import TwilioConversationService; TwilioConversationService(); print('✓ Twilio OK')"

# Test OpenAI integration
python -c "from src.services.agent_service import CustomerServiceAgent; CustomerServiceAgent(); print('✓ OpenAI OK')"
```

### ✅ Security Checklist

- [ ] All API keys are stored as environment variables
- [ ] Webhook secret is configured and strong
- [ ] Database credentials are secure
- [ ] HTTPS is enabled for all webhook endpoints
- [ ] Rate limiting is configured appropriately
- [ ] CORS settings are restrictive
- [ ] No sensitive data in logs

### ✅ Performance Checklist

- [ ] Database connection pooling is configured
- [ ] Session storage (Redis) is set up for production
- [ ] Logging level is set to INFO or WARNING for production
- [ ] Health checks are enabled
- [ ] Resource limits are defined

## Docker Deployment

### Basic Docker Setup

#### 1. Build Image
```bash
# Build production image
docker build -t twilio-openai-conversations .

# Test the image locally
docker run -p 8000:8000 --env-file .env twilio-openai-conversations
```

#### 2. Multi-Stage Production Dockerfile

```dockerfile
# Production-optimized Dockerfile
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Set up application
WORKDIR /app
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

# Make sure scripts are in PATH
ENV PATH=/root/.local/bin:$PATH

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose for Production

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/conversations
      - REDIS_URL=redis://redis:6379
    env_file:
      - .env.production
    depends_on:
      - db
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: conversations
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

## Kubernetes Deployment

### Basic Kubernetes Manifests

#### 1. Namespace and ConfigMap

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: twilio-openai

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: twilio-openai
data:
  DEBUG: "false"
  LOG_LEVEL: "INFO"
  DATABASE_URL: "postgresql://postgres:password@postgres:5432/conversations"
  REDIS_URL: "redis://redis:6379"
```

#### 2. Secrets

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: twilio-openai
type: Opaque
data:
  TWILIO_ACCOUNT_SID: <base64-encoded-value>
  TWILIO_AUTH_TOKEN: <base64-encoded-value>
  TWILIO_CONVERSATIONS_SERVICE_SID: <base64-encoded-value>
  OPENAI_API_KEY: <base64-encoded-value>
  WEBHOOK_SECRET: <base64-encoded-value>
```

#### 3. Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: twilio-openai-app
  namespace: twilio-openai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: twilio-openai-app
  template:
    metadata:
      labels:
        app: twilio-openai-app
    spec:
      containers:
      - name: app
        image: twilio-openai-conversations:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: app-config
        - secretRef:
            name: app-secrets
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      imagePullSecrets:
      - name: registry-secret
```

#### 4. Service and Ingress

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: twilio-openai-service
  namespace: twilio-openai
spec:
  selector:
    app: twilio-openai-app
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: twilio-openai-ingress
  namespace: twilio-openai
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - your-domain.com
    secretName: twilio-openai-tls
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: twilio-openai-service
            port:
              number: 80
```

### Deploy to Kubernetes

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n twilio-openai
kubectl logs -f deployment/twilio-openai-app -n twilio-openai

# Scale deployment
kubectl scale deployment twilio-openai-app --replicas=5 -n twilio-openai
```

## Platform-as-a-Service Deployment

### Heroku Deployment

#### 1. Prepare for Heroku

```bash
# Install Heroku CLI
# macOS: brew install heroku/brew/heroku
# Other: https://devcenter.heroku.com/articles/heroku-cli

# Create Heroku app
heroku create your-app-name

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:hobby-dev

# Add Redis addon
heroku addons:create heroku-redis:hobby-dev
```

#### 2. Heroku Configuration

Create `Procfile`:
```
web: python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT
worker: python -m celery worker -A src.tasks:celery_app --loglevel=info
```

Create `runtime.txt`:
```
python-3.11.6
```

#### 3. Environment Variables

```bash
# Set environment variables
heroku config:set TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxx
heroku config:set TWILIO_AUTH_TOKEN=your_token
heroku config:set TWILIO_CONVERSATIONS_SERVICE_SID=ISxxxxxxxxxxxxx
heroku config:set OPENAI_API_KEY=sk-xxxxxxxxxxxxx
heroku config:set WEBHOOK_SECRET=your_secret

# Set production settings
heroku config:set DEBUG=false
heroku config:set LOG_LEVEL=INFO
```

#### 4. Deploy

```bash
# Deploy to Heroku
git push heroku main

# Run database migrations
heroku run python -c "from src.services.session_service import SessionService; import asyncio; asyncio.run(SessionService().create_tables())"

# Check logs
heroku logs --tail
```

### Railway Deployment

#### 1. Railway Setup

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and initialize
railway login
railway init

# Deploy
railway up
```

#### 2. Railway Configuration

Create `railway.toml`:
```toml
[build]
builder = "NIXPACKS"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"

[environments.production.variables]
DEBUG = "false"
LOG_LEVEL = "INFO"
```

## Cloud Provider Deployments

### AWS Deployment

#### 1. AWS ECS with Fargate

```yaml
# aws/task-definition.json
{
  "family": "twilio-openai-conversations",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "app",
      "image": "your-account.dkr.ecr.region.amazonaws.com/twilio-openai:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "DEBUG", "value": "false"},
        {"name": "LOG_LEVEL", "value": "INFO"}
      ],
      "secrets": [
        {"name": "TWILIO_ACCOUNT_SID", "valueFrom": "arn:aws:secretsmanager:region:account:secret:twilio-creds:ACCOUNT_SID::"},
        {"name": "OPENAI_API_KEY", "valueFrom": "arn:aws:secretsmanager:region:account:secret:openai-creds:API_KEY::"}
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      },
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/twilio-openai-conversations",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### 2. Deploy to ECS

```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-account.dkr.ecr.us-east-1.amazonaws.com
docker build -t twilio-openai-conversations .
docker tag twilio-openai-conversations:latest your-account.dkr.ecr.us-east-1.amazonaws.com/twilio-openai:latest
docker push your-account.dkr.ecr.us-east-1.amazonaws.com/twilio-openai:latest

# Register task definition
aws ecs register-task-definition --cli-input-json file://aws/task-definition.json

# Update service
aws ecs update-service --cluster your-cluster --service twilio-openai-service --task-definition twilio-openai-conversations
```

### Google Cloud Deployment

#### 1. Google Cloud Run

```yaml
# gcp/service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: twilio-openai-conversations
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "1"
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/cpu-throttling: "false"
    spec:
      containerConcurrency: 100
      timeoutSeconds: 300
      containers:
      - image: gcr.io/your-project/twilio-openai-conversations
        ports:
        - containerPort: 8000
        env:
        - name: DEBUG
          value: "false"
        - name: LOG_LEVEL
          value: "INFO"
        - name: TWILIO_ACCOUNT_SID
          valueFrom:
            secretKeyRef:
              name: twilio-secrets
              key: account-sid
        resources:
          limits:
            cpu: "1"
            memory: "512Mi"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
        startupProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          failureThreshold: 10
```

#### 2. Deploy to Cloud Run

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/your-project/twilio-openai-conversations

# Deploy service
gcloud run deploy twilio-openai-conversations \
  --image gcr.io/your-project/twilio-openai-conversations \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DEBUG=false,LOG_LEVEL=INFO \
  --set-secrets TWILIO_ACCOUNT_SID=twilio-secrets:account-sid \
  --max-instances 10 \
  --memory 512Mi \
  --cpu 1
```

## Production Configuration

### Environment Variables for Production

```env
# Production .env file
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:pass@prod-db:5432/conversations
REDIS_URL=redis://prod-redis:6379

# Twilio Production Credentials
TWILIO_ACCOUNT_SID=ACprod123456789012345678901234
TWILIO_AUTH_TOKEN=prod_auth_token
TWILIO_CONVERSATIONS_SERVICE_SID=ISprod123456789012345678901234
WEBHOOK_SECRET=production_webhook_secret_very_strong

# OpenAI Production Settings
OPENAI_API_KEY=sk-prod_key_here
OPENAI_MODEL=gpt-4o

# Performance Settings
RATE_LIMIT_PER_MINUTE=60
MAX_CONCURRENT_CONVERSATIONS=100
CONVERSATION_TIMEOUT_MINUTES=30

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
NEW_RELIC_LICENSE_KEY=your_new_relic_key
```

### Nginx Configuration

```nginx
# nginx.conf
upstream app {
    server app:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=webhook:10m rate=100r/s;

    location / {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /webhook/ {
        limit_req zone=webhook burst=200 nodelay;
        proxy_pass http://app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        access_log off;
        proxy_pass http://app;
    }
}
```

## Monitoring and Observability

### Application Monitoring

```python
# Add to requirements.txt
prometheus-client==0.17.1
sentry-sdk[fastapi]==1.38.0

# In main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

# Initialize Sentry
sentry_sdk.init(
    dsn=settings.sentry_dsn,
    integrations=[FastApiIntegration(auto_enable=True)],
    traces_sample_rate=1.0,
)

# Prometheus metrics endpoint
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('request_duration_seconds', 'Request latency')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Health Checks

The application includes comprehensive health checks:

```bash
# Basic health check
curl https://your-domain.com/health

# Detailed status
curl https://your-domain.com/health/status

# Readiness probe (for Kubernetes)
curl https://your-domain.com/health/ready

# Liveness probe (for Kubernetes)
curl https://your-domain.com/health/live
```

## Scaling Considerations

### Horizontal Scaling

The application is designed to be stateless and can be horizontally scaled:

- **Database**: Use connection pooling and read replicas
- **Session Storage**: Use Redis cluster for high availability
- **File Storage**: Use cloud storage (S3, GCS) for any file uploads
- **Caching**: Implement application-level caching for frequently accessed data

### Auto-Scaling Configuration

#### Kubernetes HPA

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: twilio-openai-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: twilio-openai-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Performance Tuning

```env
# Database connection tuning
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis connection tuning
REDIS_MAX_CONNECTIONS=50

# Application tuning
UVICORN_WORKERS=4
UVICORN_WORKER_CONNECTIONS=1000
UVICORN_BACKLOG=2048
```

## Rollback Strategy

### Blue-Green Deployment

```bash
# Deploy new version to "green" environment
kubectl apply -f k8s-green/

# Test green environment
curl https://green.your-domain.com/health

# Switch traffic to green
kubectl patch service twilio-openai-service -p '{"spec":{"selector":{"version":"green"}}}'

# If issues, rollback to blue
kubectl patch service twilio-openai-service -p '{"spec":{"selector":{"version":"blue"}}}'
```

### Canary Deployment

```yaml
# Istio VirtualService for canary
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: twilio-openai-canary
spec:
  hosts:
  - your-domain.com
  http:
  - match:
    - headers:
        canary:
          exact: "true"
    route:
    - destination:
        host: twilio-openai-service
        subset: canary
  - route:
    - destination:
        host: twilio-openai-service
        subset: stable
      weight: 90
    - destination:
        host: twilio-openai-service
        subset: canary
      weight: 10
```

## Troubleshooting Production Issues

### Common Issues and Solutions

1. **High Memory Usage**
   ```bash
   # Check memory usage
   kubectl top pods -n twilio-openai
   
   # Increase memory limits
   kubectl patch deployment twilio-openai-app -p '{"spec":{"template":{"spec":{"containers":[{"name":"app","resources":{"limits":{"memory":"1Gi"}}}]}}}}'
   ```

2. **Database Connection Issues**
   ```bash
   # Check database connectivity
   kubectl run -it --rm debug --image=postgres:15 --restart=Never -- psql -h postgres -U postgres -d conversations
   
   # Scale down app temporarily
   kubectl scale deployment twilio-openai-app --replicas=0
   ```

3. **High API Latency**
   ```bash
   # Check OpenAI API status
   curl https://status.openai.com/api/v2/status.json
   
   # Review application logs
   kubectl logs -f deployment/twilio-openai-app | grep "processing_time_ms"
   ```

### Emergency Procedures

```bash
# Emergency scale down
kubectl scale deployment twilio-openai-app --replicas=0

# Emergency rollback
kubectl rollout undo deployment/twilio-openai-app

# Check rollout status
kubectl rollout status deployment/twilio-openai-app
```

This deployment guide provides comprehensive coverage for deploying the Twilio-OpenAI integration across various platforms and environments. Choose the deployment method that best fits your infrastructure and requirements.