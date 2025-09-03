FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create and set working directory
WORKDIR /app

# Install system dependencies and UV
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

# Add UV to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy pyproject.toml and uv.lock for better caching
COPY pyproject.toml uv.lock* ./

# Install Python dependencies with UV
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Create data directory and non-root user for security
RUN mkdir -p /app/data \
    && adduser --disabled-password --gecos '' --shell /bin/bash user \
    && chown -R user:user /app
USER user

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application with UV
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]