from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db import Base, engine
from app.routers import user
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.models.user import User  # Ensure model is imported for migrations
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - create tables on startup"""
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title=settings.app_name,
    version="0.1",
    docs_url="/docs",
    redoc_url=None,
    lifespan=lifespan,
)

# Secure CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Register all routers
app.include_router(user.protected_router)
app.include_router(user.user_router)
app.include_router(user.info_router)  # ← ADDED

@app.get("/health", tags=["info"])
def health():
    """Quick health check"""
    return {"status": "ok"}
