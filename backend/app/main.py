from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db import Base, engine
from app.routers import user
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title=settings.app_name,
    version="0.1",
    docs_url="/docs",
    redoc_url=None,
    lifespan=lifespan,
)

# Secure CORS: allow only local frontend during dev, restrict in prod!
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Register modular routers
app.include_router(user.router)

@app.get("/health", tags=["info"])
def health():
    return {"status": "ok"}
