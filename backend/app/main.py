# app/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.db import Base, engine
from app.config import settings

# Import all models so they are registered with SQLAlchemy Base
# These imports are needed for Alembic migrations
import app.models.user
import app.models.device
import app.models.posture_history
import app.models.enrollment_code
import app.models.policy
import app.models.audit_log
import app.models.access_log

# Import routers directly (not from __init__.py)
from app.routers import user, device, enrollment, posture, policy, audit, access, health, token, role, resources, session

# Import error handlers
from app.middleware.error_handlers import (
    validation_exception_handler,
    database_exception_handler,
    general_exception_handler
)

import logging

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - create tables on startup using async engine"""
    logger.info("Starting ZTNA Backend API...")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database tables created/verified")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down ZTNA Backend API...")
    await engine.dispose()


# Create FastAPI app
app = FastAPI(
    title="ZTNA Platform Backend",
    version="0.1.0",
    description="Zero Trust Network Access Platform API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(health.router)
app.include_router(user.router, prefix="/api")
app.include_router(device.router, prefix="/api")
app.include_router(enrollment.router, prefix="/api")
app.include_router(posture.router, prefix="/api")
app.include_router(policy.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(access.router, prefix="/api")
app.include_router(token.router, prefix="/api")
app.include_router(role.router, prefix="/api")
app.include_router(resources.router, prefix="/api")
app.include_router(session.router, prefix="/api")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ZTNA Platform Backend API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs"
    }

# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "ZTNA Backend API",
        "version": "0.1.0"
    }

logger.info("ZTNA Backend API initialized successfully")
