# app/routers/health.py

"""
Health check and system status endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db import get_db
from app.services.keycloak_service import keycloak_service
from app.config import settings

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "ZTNA Backend API",
        "version": "0.1.0"
    }


@router.get("/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """
    Detailed health check with dependency status
    Checks database and Keycloak connectivity
    """
    health_status = {
        "status": "healthy",
        "service": "ZTNA Backend API",
        "version": "0.1.0",
        "components": {}
    }
    
    # Check database
    try:
        await db.execute(text("SELECT 1"))
        health_status["components"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
        health_status["status"] = "degraded"
    
    # Check Keycloak
    try:
        keycloak_healthy = await keycloak_service.health_check()
        health_status["components"]["keycloak"] = {
            "status": "healthy" if keycloak_healthy else "unhealthy",
            "message": "Keycloak is accessible" if keycloak_healthy else "Keycloak is not accessible"
        }
        if not keycloak_healthy:
            health_status["status"] = "degraded"
    except Exception as e:
        logger.error(f"Keycloak health check failed: {e}")
        health_status["components"]["keycloak"] = {
            "status": "unhealthy",
            "message": f"Keycloak check failed: {str(e)}"
        }
        health_status["status"] = "degraded"
    
    return health_status


@router.get("/readiness")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Kubernetes readiness probe
    Returns 200 if service is ready to handle requests
    """
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"status": "not_ready", "error": str(e)}


@router.get("/liveness")
async def liveness_check():
    """
    Kubernetes liveness probe
    Returns 200 if service is alive
    """
    return {"status": "alive"}
