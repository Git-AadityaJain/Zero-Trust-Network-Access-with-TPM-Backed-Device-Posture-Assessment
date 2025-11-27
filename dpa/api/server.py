"""
DPA Local API Server

Exposes a local HTTP API for the frontend to request TPM-signed challenges.
This allows the frontend to integrate with the DPA without direct TPM access.

The server runs on localhost and only accepts connections from localhost for security.
"""

import json
import base64
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from pathlib import Path
import sys
import os

# Add project root to path for imports
# Path structure: project_root/dpa/api/server.py
# So we need to go up 2 levels to get to project root
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dpa.core.signing import PostureSigner
from dpa.core.enrollment import DeviceEnrollment
from dpa.config.settings import config_manager
from dpa.utils.logger import setup_logger

# Setup logging
setup_logger()
logger = logging.getLogger("dpa.api")

# Create FastAPI app
app = FastAPI(
    title="DPA Local API",
    description="Device Posture Agent Local API for Challenge Signing",
    version="1.0.0"
)

# CORS middleware - allow all origins for local development API
# This is a local API server, so we allow all origins for development
# In production, you should restrict this to specific origins
allowed_origins_env = os.getenv("DPA_CORS_ORIGINS")
if allowed_origins_env:
    # Use specific origins from environment variable
    allowed_origins_list = [origin.strip() for origin in allowed_origins_env.split(",")]
else:
    # For development, allow all origins (local API server)
    allowed_origins_list = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins_list,
    allow_credentials=True if "*" not in allowed_origins_list else False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Global signer instance
signer: Optional[PostureSigner] = None
enrollment: Optional[DeviceEnrollment] = None


def get_signer() -> PostureSigner:
    """Get or create PostureSigner instance"""
    global signer
    if signer is None:
        # Allow TPM executable path to be specified via environment variable
        tpm_exe_path = os.getenv("TPM_SIGNER_EXE_PATH")
        signer = PostureSigner(tpm_exe_path=tpm_exe_path)
    return signer


def get_enrollment() -> DeviceEnrollment:
    """Get or create DeviceEnrollment instance"""
    global enrollment
    if enrollment is None:
        enrollment = DeviceEnrollment()
    return enrollment


# ==================== MODELS ====================

class ChallengeRequest(BaseModel):
    """Request to sign a challenge"""
    challenge: str = Field(..., description="Challenge string to sign")


class ChallengeResponse(BaseModel):
    """Response with signed challenge"""
    signature: str = Field(..., description="Base64-encoded TPM signature of the challenge")
    message: str = Field(..., description="Status message")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    enrolled: bool
    tpm_available: bool
    message: str


# ==================== ENDPOINTS ====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    Returns DPA status including enrollment and TPM availability
    """
    try:
        enrollment_check = get_enrollment()
        is_enrolled = enrollment_check.is_enrolled()
        
        # Check TPM availability
        signer_check = get_signer()
        tpm_available = False
        try:
            # Try to check TPM status
            tpm_available, key_exists, _ = signer_check.tpm.check_status()
        except Exception as e:
            logger.warning(f"Could not check TPM status: {e}")
            tpm_available = False
        
        return HealthResponse(
            status="healthy",
            enrolled=is_enrolled,
            tpm_available=tpm_available,
            message="DPA API is running"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


# DEPRECATED: This endpoint is no longer used in the new ZTNA architecture.
# The browser no longer communicates directly with the DPA API.
# Device verification is now done on the backend based on continuous posture reports.
# This endpoint is kept for backward compatibility but should not be used.
@app.post("/sign-challenge", response_model=ChallengeResponse, deprecated=True)
async def sign_challenge(request: ChallengeRequest):
    """
    [DEPRECATED] Sign a challenge string with the device's TPM
    
    ⚠️ This endpoint is deprecated and should not be used.
    
    The new ZTNA architecture does not require browser-to-DPA communication.
    Device verification is done on the backend based on continuous posture reports
    submitted by the DPA agent.
    
    This endpoint is kept for backward compatibility only.
    """
    logger.warning("DEPRECATED: /sign-challenge endpoint called. This should not be used in new ZTNA architecture.")
    raise HTTPException(
        status_code=410,  # Gone
        detail="This endpoint is deprecated. The new ZTNA architecture uses continuous posture reporting instead of challenge-response flow."
    )


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "DPA Local API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health"
        },
        "description": "Device Posture Agent Local API - Health check only. Challenge signing is deprecated."
    }


# ==================== STARTUP ====================

def start_server(host: str = "127.0.0.1", port: int = 8081, log_level: str = "info"):
    """
    Start the DPA API server
    
    Args:
        host: Host to bind to (default: 127.0.0.1 for localhost only)
        port: Port to bind to (default: 8081)
        log_level: Logging level (default: info)
    """
    logger.info(f"Starting DPA Local API server on {host}:{port}")
    
    # Check enrollment status
    enrollment_check = get_enrollment()
    if not enrollment_check.is_enrolled():
        logger.warning("Device is not enrolled. Some endpoints may not work.")
    else:
        logger.info("Device is enrolled and ready")
    
    # Start server
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level,
        access_log=True
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="DPA Local API Server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8081, help="Port to bind to")
    parser.add_argument("--log-level", type=str, default="info", choices=["debug", "info", "warning", "error"])
    
    args = parser.parse_args()
    
    start_server(host=args.host, port=args.port, log_level=args.log_level)

