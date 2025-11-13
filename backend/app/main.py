# main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import Base, engine
from app.config import settings

# Import all models so they are registered with SQLAlchemy Base
from app.models import User, Device, PostureHistory, EnrollmentCode, Policy, AuditLog, AccessLog

# Import routers
from app.routers import user, device, enrollment, posture, policy, audit, access

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - create tables on startup using async engine"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

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
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

# Include all routers
app.include_router(user.router, prefix="/api")
app.include_router(device.router, prefix="/api")
app.include_router(enrollment.router, prefix="/api")
app.include_router(posture.router, prefix="/api")
app.include_router(policy.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(access.router, prefix="/api")

@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "ZTNA Backend",
        "version": "0.1.0"
    }

@app.get("/", tags=["root"])
async def root():
    """Root endpoint"""
    return {
        "message": "ZTNA Platform API",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "version": "0.1.0"
    }
