"""
FastAPI application entry point.
Configures the web server, routes, middleware, and startup/shutdown events.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from config.settings import settings
from src.handlers import webhook_handler, health_handler
from src.utils.logging import setup_logging, get_logger

# Setup logging first
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting Twilio-OpenAI Conversations application")
    
    # TODO: Initialize database connections
    # TODO: Initialize Redis connections if configured  
    # TODO: Initialize OpenAI agent
    # TODO: Validate Twilio credentials
    # TODO: Load agent configuration
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    
    # TODO: Close database connections
    # TODO: Close Redis connections
    # TODO: Cleanup agent resources
    
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application
    """
    app = FastAPI(
        title="Twilio-OpenAI Conversations",
        description="AI-powered customer service using Twilio Conversations and OpenAI Agents",
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan
    )
    
    # Add middleware
    setup_middleware(app)
    
    # Add routes
    setup_routes(app)
    
    # Add error handlers
    setup_error_handlers(app)
    
    return app


def setup_middleware(app: FastAPI) -> None:
    """
    Configure application middleware.
    
    Args:
        app: FastAPI application instance
    """
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [],  # TODO: Configure proper origins
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    
    # Trusted host middleware for security
    if not settings.debug:
        app.add_middleware(
            TrustedHostMiddleware, 
            allowed_hosts=["*"]  # TODO: Configure proper allowed hosts
        )


def setup_routes(app: FastAPI) -> None:
    """
    Configure application routes.
    
    Args:
        app: FastAPI application instance
    """
    # Health check routes
    app.include_router(
        health_handler.router,
        prefix="/health",
        tags=["health"]
    )
    
    # Webhook routes
    app.include_router(
        webhook_handler.router,
        prefix="/webhook",
        tags=["webhooks"]
    )


def setup_error_handlers(app: FastAPI) -> None:
    """
    Configure global error handlers.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """
        Global exception handler for unhandled errors.
        """
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred. Please try again later.",
                "request_id": getattr(request.state, "request_id", "unknown")
            }
        )


# Create the FastAPI app instance
app = create_app()


if __name__ == "__main__":
    """
    Run the application directly with uvicorn.
    For development use only.
    """
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )