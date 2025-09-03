# =============================================================================
# Multi-stage Docker build for optimized production container
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build stage - Install dependencies and build tools
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS builder

# Set build-time environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_CACHE_DIR=/tmp/uv-cache

# Install build dependencies in a single layer
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install UV package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock* ./

# Install dependencies with UV (compile bytecode for faster startup)
RUN --mount=type=cache,target=/tmp/uv-cache \
    uv sync --frozen --no-dev --compile-bytecode

# -----------------------------------------------------------------------------
# Stage 2: Runtime stage - Minimal production container  
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# Install only runtime dependencies (curl for health checks, tini for init)
RUN apt-get update && apt-get install -y \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy UV from builder stage
COPY --from=builder /root/.local/bin/uv /usr/local/bin/uv

# Set runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PATH="/usr/local/bin:$PATH" \
    UV_PROJECT_ENVIRONMENT=/app/.venv

# Create non-root user early for security
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /bin/bash appuser

# Set working directory and create necessary directories
WORKDIR /app
RUN mkdir -p /app/data /app/.venv \
    && chown -R appuser:appuser /app

# Copy virtual environment from builder
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy application code with proper ownership
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Optimized health check with shorter intervals and faster timeout
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=2 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use tini as init system for proper signal handling
ENTRYPOINT ["tini", "--"]

# Run application with optimized settings
CMD ["uv", "run", "--no-dev", "uvicorn", "src.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--access-log", \
     "--no-server-header"]