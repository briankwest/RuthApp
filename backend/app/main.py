"""
Main FastAPI application entry point
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.core.config import settings, derived_settings
from app.core.database import init_db, close_db

# Import API routers
from app.api import auth, representatives, letters, delivery

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Initialize Sentry for error tracking (production only)
if settings.sentry_dsn and derived_settings.is_production:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
        ],
        environment="production" if derived_settings.is_production else "development",
        traces_sample_rate=0.1,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle - startup and shutdown events
    """
    # Startup
    logger.info("Starting Ruth application...")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    # Initialize other services here (Redis, etc.)

    yield

    # Shutdown
    logger.info("Shutting down Ruth application...")

    # Close database connections
    await close_db()

    # Cleanup other resources here

    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="AI-powered civic engagement platform for writing letters to representatives",
    version="1.0.0",
    docs_url="/api/docs" if settings.debug else None,  # Disable docs in production
    redoc_url="/api/redoc" if settings.debug else None,
    openapi_url="/api/openapi.json" if settings.debug else None,
    lifespan=lifespan,
)


# Add middleware

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts
)

# Session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie="ruth_session",
    max_age=settings.session_cache_ttl,
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handle all unhandled exceptions
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    if settings.debug:
        # In debug mode, return detailed error information
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "type": type(exc).__name__,
                "path": str(request.url),
            },
        )
    else:
        # In production, return generic error message
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint - API information
    """
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "status": "healthy",
        "documentation": "/api/docs" if settings.debug else None,
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring
    """
    # TODO: Add database and Redis health checks
    return {
        "status": "healthy",
        "service": "ruth-backend",
    }


# Include API routers
app.include_router(auth.router, prefix="/api")
app.include_router(representatives.router, prefix="/api")
app.include_router(letters.router)
app.include_router(delivery.router)

# Placeholder routes for upcoming features
@app.get("/api/test")
async def test_endpoint():
    """
    Test endpoint to verify API is working
    """
    return {
        "message": "API is working",
        "debug": settings.debug,
        "features": {
            "fax": derived_settings.enable_fax,
            "email": derived_settings.enable_email,
            "registration": settings.enable_registration,
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )