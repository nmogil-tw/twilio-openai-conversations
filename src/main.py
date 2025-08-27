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
    
    # Validate configuration
    logger.info("Validating configuration...")
    if not settings.twilio.account_sid or not settings.twilio.auth_token:
        logger.error("Missing Twilio credentials")
    if not settings.openai.api_key:
        logger.error("Missing OpenAI API key")
    
    # Initialize services
    logger.info("Initializing services...")
    
    # Initialize database tables
    try:
        from src.services.session_service import SessionService
        session_service = SessionService()
        await session_service.create_tables()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # Don't fail startup for database issues in development
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    
    # Cleanup resources
    logger.info("Cleaning up resources...")
    
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
        allow_origins=["*"] if settings.debug else ["https://*.ngrok.io"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    
    # Trusted host middleware for security
    if not settings.debug:
        app.add_middleware(
            TrustedHostMiddleware, 
            allowed_hosts=["*"]  # Allow all hosts for development flexibility
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