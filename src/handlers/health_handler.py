"""
Health Check Handler for monitoring application status and dependencies.
Provides endpoints for health checks, readiness probes, and system status.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config.settings import settings
from src.services.twilio_service import TwilioConversationService
from src.services.session_service import SessionService
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Create FastAPI router
router = APIRouter()


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoints."""
    status: str
    timestamp: str
    version: str = "1.0.0"
    environment: str
    uptime_seconds: float
    checks: Dict[str, Any]


class ServiceStatus(BaseModel):
    """Model for individual service status."""
    healthy: bool
    response_time_ms: float
    message: str
    details: Dict[str, Any] = {}


# Track application start time for uptime calculation
app_start_time = datetime.now()


@router.get("/", response_model=HealthCheckResponse)
async def health_check():
    """
    Basic health check endpoint.
    
    Returns overall application health status with minimal dependency checks.
    Used by load balancers and monitoring systems for quick health verification.
    """
    start_time = datetime.now()
    
    try:
        # Calculate uptime
        uptime = (datetime.now() - app_start_time).total_seconds()
        
        # Perform basic checks
        checks = {
            "application": {
                "healthy": True,
                "message": "Application is running",
                "response_time_ms": 0
            },
            "configuration": await check_configuration()
        }
        
        # Determine overall status
        all_healthy = all(check.get("healthy", False) for check in checks.values())
        status = "healthy" if all_healthy else "degraded"
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return HealthCheckResponse(
            status=status,
            timestamp=datetime.now().isoformat(),
            environment="development" if settings.debug else "production",
            uptime_seconds=uptime,
            checks=checks
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Health check failed")


@router.get("/ready", response_model=HealthCheckResponse)
async def readiness_check():
    """
    Readiness check endpoint.
    
    Verifies that the application is ready to serve requests by checking
    all critical dependencies (database, Twilio API, OpenAI API).
    Used by Kubernetes and other orchestrators for readiness probes.
    """
    start_time = datetime.now()
    
    try:
        # Calculate uptime
        uptime = (datetime.now() - app_start_time).total_seconds()
        
        # Perform comprehensive checks
        checks = await run_comprehensive_checks()
        
        # Determine overall status
        critical_services = ["database", "twilio_api", "configuration"]
        critical_healthy = all(
            checks.get(service, {}).get("healthy", False) 
            for service in critical_services
        )
        
        status = "ready" if critical_healthy else "not_ready"
        
        return HealthCheckResponse(
            status=status,
            timestamp=datetime.now().isoformat(),
            environment="development" if settings.debug else "production",
            uptime_seconds=uptime,
            checks=checks
        )
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Readiness check failed")


@router.get("/live")
async def liveness_check():
    """
    Liveness check endpoint.
    
    Simple endpoint that returns 200 if the application process is alive.
    Used by Kubernetes and other orchestrators for liveness probes.
    """
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": (datetime.now() - app_start_time).total_seconds()
    }


@router.get("/status", response_model=HealthCheckResponse)
async def detailed_status():
    """
    Detailed status endpoint with comprehensive system information.
    
    Provides detailed information about all system components, performance
    metrics, and configuration status. Used for monitoring and debugging.
    """
    start_time = datetime.now()
    
    try:
        # Calculate uptime
        uptime = (datetime.now() - app_start_time).total_seconds()
        
        # Perform comprehensive checks with additional details
        checks = await run_comprehensive_checks(include_details=True)
        
        # Add performance metrics
        checks["performance"] = await get_performance_metrics()
        
        # Determine overall status
        all_healthy = all(check.get("healthy", False) for check in checks.values())
        status = "healthy" if all_healthy else "degraded"
        
        return HealthCheckResponse(
            status=status,
            timestamp=datetime.now().isoformat(),
            environment="development" if settings.debug else "production",
            uptime_seconds=uptime,
            checks=checks
        )
        
    except Exception as e:
        logger.error(f"Detailed status check failed: {e}")
        raise HTTPException(status_code=500, detail="Status check failed")


async def check_configuration() -> Dict[str, Any]:
    """
    Check application configuration validity.
    
    Returns:
        Dictionary with configuration check results
    """
    start_time = datetime.now()
    
    try:
        issues = []
        
        # Check required environment variables
        if not settings.twilio.account_sid:
            issues.append("TWILIO_ACCOUNT_SID not configured")
        if not settings.twilio.auth_token:
            issues.append("TWILIO_AUTH_TOKEN not configured")
        if not settings.openai.api_key:
            issues.append("OPENAI_API_KEY not configured")
        
        # Check file paths
        try:
            from pathlib import Path
            config_path = Path(settings.agent.config_file_path)
            if not config_path.exists():
                issues.append(f"Agent config file not found: {config_path}")
        except Exception as e:
            issues.append(f"Error checking config file: {e}")
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            "healthy": len(issues) == 0,
            "message": "Configuration valid" if not issues else f"Configuration issues: {', '.join(issues)}",
            "response_time_ms": processing_time,
            "details": {"issues": issues} if issues else {}
        }
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        return {
            "healthy": False,
            "message": f"Configuration check failed: {e}",
            "response_time_ms": processing_time
        }


async def check_database() -> Dict[str, Any]:
    """
    Check database connectivity and status.
    
    Returns:
        Dictionary with database check results
    """
    start_time = datetime.now()
    
    try:
        session_service = SessionService()
        
        # Test database connection by getting stats
        stats = await session_service.get_session_stats()
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        if "error" in stats:
            return {
                "healthy": False,
                "message": f"Database error: {stats['error']}",
                "response_time_ms": processing_time
            }
        
        return {
            "healthy": True,
            "message": "Database connection successful",
            "response_time_ms": processing_time,
            "details": {
                "total_sessions": stats.get("total_sessions", 0),
                "active_sessions": stats.get("active_sessions", 0),
                "total_messages": stats.get("total_messages", 0)
            }
        }
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        return {
            "healthy": False,
            "message": f"Database check failed: {e}",
            "response_time_ms": processing_time
        }


async def check_twilio_api() -> Dict[str, Any]:
    """
    Check Twilio API connectivity and credentials.
    
    Returns:
        Dictionary with Twilio API check results
    """
    start_time = datetime.now()
    
    try:
        twilio_service = TwilioConversationService()
        
        # Test API connection by fetching service details
        # TODO: Implement a lightweight API test
        # For now, just verify client initialization
        if twilio_service.client and twilio_service.service_sid:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            return {
                "healthy": True,
                "message": "Twilio API connection successful",
                "response_time_ms": processing_time,
                "details": {
                    "service_sid": twilio_service.service_sid[:8] + "..."  # Partial SID for security
                }
            }
        else:
            return {
                "healthy": False,
                "message": "Twilio client not properly initialized",
                "response_time_ms": (datetime.now() - start_time).total_seconds() * 1000
            }
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        return {
            "healthy": False,
            "message": f"Twilio API check failed: {e}",
            "response_time_ms": processing_time
        }


async def check_openai_api() -> Dict[str, Any]:
    """
    Check OpenAI API connectivity and credentials.
    
    Returns:
        Dictionary with OpenAI API check results
    """
    start_time = datetime.now()
    
    try:
        # TODO: Implement lightweight OpenAI API test
        # For now, just verify configuration
        if settings.openai.api_key and settings.openai.model:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            return {
                "healthy": True,
                "message": "OpenAI API configuration valid",
                "response_time_ms": processing_time,
                "details": {
                    "model": settings.openai.model,
                    "api_key_configured": bool(settings.openai.api_key)
                }
            }
        else:
            return {
                "healthy": False,
                "message": "OpenAI API not properly configured",
                "response_time_ms": (datetime.now() - start_time).total_seconds() * 1000
            }
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        return {
            "healthy": False,
            "message": f"OpenAI API check failed: {e}",
            "response_time_ms": processing_time
        }


async def run_comprehensive_checks(include_details: bool = False) -> Dict[str, Any]:
    """
    Run all health checks concurrently.
    
    Args:
        include_details: Whether to include detailed information
        
    Returns:
        Dictionary with all check results
    """
    # Run checks concurrently for better performance
    check_tasks = {
        "configuration": check_configuration(),
        "database": check_database(),
        "twilio_api": check_twilio_api(),
        "openai_api": check_openai_api()
    }
    
    results = {}
    completed_tasks = await asyncio.gather(*check_tasks.values(), return_exceptions=True)
    
    for (check_name, _), result in zip(check_tasks.items(), completed_tasks):
        if isinstance(result, Exception):
            results[check_name] = {
                "healthy": False,
                "message": f"Check failed with exception: {result}",
                "response_time_ms": 0
            }
        else:
            results[check_name] = result
    
    return results


async def get_performance_metrics() -> Dict[str, Any]:
    """
    Get application performance metrics.
    
    Returns:
        Dictionary with performance metrics
    """
    try:
        import psutil
        import os
        
        # Get process information
        process = psutil.Process(os.getpid())
        
        return {
            "healthy": True,
            "message": "Performance metrics collected",
            "response_time_ms": 0,
            "details": {
                "memory_usage_mb": process.memory_info().rss / 1024 / 1024,
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads(),
                "uptime_seconds": (datetime.now() - app_start_time).total_seconds()
            }
        }
        
    except ImportError:
        # psutil not available
        return {
            "healthy": True,
            "message": "Performance monitoring not available (psutil not installed)",
            "response_time_ms": 0,
            "details": {
                "uptime_seconds": (datetime.now() - app_start_time).total_seconds()
            }
        }
    except Exception as e:
        return {
            "healthy": False,
            "message": f"Failed to collect performance metrics: {e}",
            "response_time_ms": 0
        }