"""
CloudWise AI — Main Application Factory
Enterprise-grade FastAPI application with CORS, error handling, and versioned API routes.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.exceptions import CloudWiseException
from app.database import init_db
from app.api.v1 import (
    auth,
    costs,
    budgets,
    recommendations,
    anomalies,
    forecasts,
    assistant,
    health,
    settings as settings_api,
    reports,
    audit_logs,
)

from app.core.logging import configure_logging
settings = get_settings()

# Configure logging
configure_logging(
    is_production=settings.ENVIRONMENT.lower() == "production", debug=settings.DEBUG
)
logger = logging.getLogger("cloudwise")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    # Initialize database tables
    init_db()
    logger.info("✅ Database initialized")

    if settings.SEED_DEV_ADMIN:
        from app.database import SessionLocal
        from app.core.seed import seed_development_admin
        db = SessionLocal()
        try:
            seed_development_admin(db)
        finally:
            db.close()

    # Security configuration checks
    if settings.ENVIRONMENT.lower() == "production":
        if settings.SECRET_KEY == "cloudwise-dev-secret-key-change-in-production":
            logger.critical(
                "FATAL: Default SECRET_KEY is used in production. Halting startup."
            )
            raise RuntimeError("Default SECRET_KEY used in production environment.")
        logger.info("✅ Security configuration validated")

    # Verify AI Provider Configuration (Google Gemini)
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.strip() == "" or "placeholder" in settings.GEMINI_API_KEY.lower() or "mock" in settings.GEMINI_API_KEY.lower():
        logger.critical(
            "FATAL: GEMINI_API_KEY is missing or invalid. The application requires a valid Gemini API key to start."
        )
        raise RuntimeError(
            "Missing required environment variable: GEMINI_API_KEY. "
            "Please configure a valid Google Gemini API key in your .env file."
        )
    logger.info("✅ Gemini AI configuration validated")

    yield

    logger.info("👋 Shutting down CloudWise AI")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        description="Intelligent AWS Cost Optimization and FinOps Analytics Platform",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Security Headers Middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.ENVIRONMENT.lower() == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global exception handler for CloudWise exceptions
    @app.exception_handler(CloudWiseException)
    async def cloudwise_exception_handler(request: Request, exc: CloudWiseException):
        status_map = {
            "NOT_FOUND": 404,
            "AUTH_FAILED": 401,
            "FORBIDDEN": 403,
            "DUPLICATE": 409,
            "VALIDATION_ERROR": 422,
            "AWS_ERROR": 502,
            "AI_ERROR": 503,
        }
        status_code = status_map.get(exc.code, 500)
        return JSONResponse(
            status_code=status_code,
            content={"detail": exc.message, "code": exc.code},
        )

    # Register API v1 routes
    prefix = settings.API_V1_PREFIX
    app.include_router(health.router, tags=["Health"])
    app.include_router(health.router, prefix=prefix, tags=["Health"])
    app.include_router(auth.router, prefix=f"{prefix}/auth", tags=["Authentication"])
    app.include_router(
        settings_api.router, prefix=f"{prefix}/settings", tags=["Settings"]
    )
    app.include_router(costs.router, prefix=f"{prefix}/costs", tags=["Costs"])
    app.include_router(budgets.router, prefix=f"{prefix}/budgets", tags=["Budgets"])
    app.include_router(
        recommendations.router,
        prefix=f"{prefix}/recommendations",
        tags=["Recommendations"],
    )
    app.include_router(
        anomalies.router, prefix=f"{prefix}/anomalies", tags=["Anomalies"]
    )
    app.include_router(
        forecasts.router, prefix=f"{prefix}/forecasts", tags=["Forecasts"]
    )
    app.include_router(
        assistant.router, prefix=f"{prefix}/assistant", tags=["AI Assistant"]
    )
    app.include_router(reports.router, prefix=f"{prefix}/reports", tags=["Reports"])
    app.include_router(
        audit_logs.router, prefix=f"{prefix}/audit-logs", tags=["Audit Logs"]
    )

    # Static files mounting
    import os

    os.makedirs("static/reports", exist_ok=True)
    app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.get("/")
    def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running",
            "docs": "/docs",
        }

    return app


# Application instance
app = create_app()
