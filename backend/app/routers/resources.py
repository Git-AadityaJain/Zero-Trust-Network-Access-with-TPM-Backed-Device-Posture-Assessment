# routers/resources.py

"""
Protected Resource Endpoint
Serves resources/files that require JWT token validation
Used for demo: enrolled users can access, unenrolled users are blocked
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta
import os
import logging

from app.db import get_db
from app.services.device_service import DeviceService
from app.services.access_service import AccessService
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.security.oidc import verify_jwt_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resources", tags=["resources"])

# Mock resource storage (in production, use actual file storage)
MOCK_RESOURCES = {
    # Admin-only resources
    "company-policy.pdf": {
        "name": "Company Policy Document.pdf",
        "type": "document",
        "size": "2.5 MB",
        "role": "admin"
    },
    "confidential-report.docx": {
        "name": "Confidential Report.docx",
        "type": "document",
        "size": "850 KB",
        "role": "admin"
    },
    "executive-summary.xlsx": {
        "name": "Executive Summary Q4 2024.xlsx",
        "type": "document",
        "size": "3.2 MB",
        "role": "admin"
    },
    "security-audit.pdf": {
        "name": "Security Audit Report 2024.pdf",
        "type": "document",
        "size": "5.1 MB",
        "role": "admin"
    },
    "admin-documentation.zip": {
        "name": "Administrator Documentation.zip",
        "type": "archive",
        "size": "12.5 MB",
        "role": "admin"
    },
    
    # User-accessible resources
    "employee-handbook.pdf": {
        "name": "Employee Handbook.pdf",
        "type": "document",
        "size": "1.8 MB",
        "role": "user"
    },
    "training-materials.zip": {
        "name": "Training Materials.zip",
        "type": "archive",
        "size": "45 MB",
        "role": "user"
    },
    "onboarding-guide.pdf": {
        "name": "New Employee Onboarding Guide.pdf",
        "type": "document",
        "size": "2.1 MB",
        "role": "user"
    },
    "benefits-overview.docx": {
        "name": "Employee Benefits Overview.docx",
        "type": "document",
        "size": "1.2 MB",
        "role": "user"
    },
    "it-support-guide.pdf": {
        "name": "IT Support Guide.pdf",
        "type": "document",
        "size": "950 KB",
        "role": "user"
    },
    "software-installers": {
        "name": "Software Installers",
        "type": "folder",
        "size": "-",
        "role": "user"
    },
    "project-templates.zip": {
        "name": "Project Templates.zip",
        "type": "archive",
        "size": "8.3 MB",
        "role": "user"
    },
    "meeting-notes-2024": {
        "name": "Meeting Notes 2024",
        "type": "folder",
        "size": "-",
        "role": "user"
    },
    
    # Public resources (accessible to all)
    "welcome-package.pdf": {
        "name": "Welcome Package.pdf",
        "type": "document",
        "size": "1.5 MB",
        "role": "public"
    },
    "company-overview.pptx": {
        "name": "Company Overview Presentation.pptx",
        "type": "document",
        "size": "4.7 MB",
        "role": "public"
    },
    "faq-document.pdf": {
        "name": "Frequently Asked Questions.pdf",
        "type": "document",
        "size": "680 KB",
        "role": "public"
    }
}


class ResourceListResponse(BaseModel):
    """Response for resource list"""
    resources: list
    message: str


@router.get("/list")
async def list_resources(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List available resources (requires OIDC JWT token from Keycloak)
    
    Proper ZTNA flow:
    1. User authenticates with Keycloak (OIDC)
    2. Backend verifies user has enrolled, compliant device
    3. Device state is checked from latest posture reports (not browser-to-DPA)
    4. Resources are filtered based on user role and device compliance
    """
    from app.models.posture_history import PostureHistory
    
    # Get user's devices
    devices = await DeviceService.get_devices_by_user(db, current_user.id)
    
    if not devices:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No devices found. Please enroll a device to access resources."
        )
    
    # Find active enrolled device with recent posture
    active_device = None
    for device in devices:
        if device.is_enrolled and device.status == "active":
            # Check if device has recent posture (within last 15 minutes)
            if device.last_posture_check:
                time_since_posture = datetime.now(timezone.utc) - device.last_posture_check.replace(tzinfo=timezone.utc)
                if time_since_posture < timedelta(minutes=15):
                    active_device = device
                    break
    
    # If no recent device, use most recently seen enrolled device
    if not active_device:
        enrolled_devices = [d for d in devices if d.is_enrolled and d.status == "active"]
        if enrolled_devices:
            active_device = max(enrolled_devices, key=lambda d: d.last_seen_at or datetime.min.replace(tzinfo=timezone.utc))
    
    if not active_device:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No active enrolled device found. Please ensure your device is enrolled and reporting posture."
        )
    
    # Check TPM key match from latest posture history
    tpm_key_match = False
    if active_device.tpm_public_key:
        result = await db.execute(
            select(PostureHistory)
            .where(PostureHistory.device_id == active_device.id)
            .order_by(desc(PostureHistory.checked_at))
            .limit(1)
        )
        latest_posture = result.scalar_one_or_none()
        if latest_posture:
            tpm_key_match = latest_posture.signature_valid
    
    # Verify device state (ZTNA requirements)
    if not active_device.is_compliant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device is not compliant. Please ensure your device meets security requirements."
        )
    
    if not tpm_key_match:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="TPM key verification failed. Device may have been compromised."
        )
    
    # Check if DPA is actively reporting
    if not active_device.last_posture_check:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="DPA agent not reporting. Please ensure the DPA agent is running on your device."
        )
    
    time_since_posture = datetime.now(timezone.utc) - active_device.last_posture_check.replace(tzinfo=timezone.utc)
    if time_since_posture > timedelta(minutes=15):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="DPA agent not reporting recently. Last posture check was too long ago."
        )
    
    # Get user roles from OIDC token
    auth_header = request.headers.get("Authorization")
    token = auth_header.replace("Bearer ", "") if auth_header and auth_header.startswith("Bearer ") else None
    token_payload = verify_jwt_token(token) if token else None
    user_roles = token_payload.roles if token_payload else []
    is_admin = "admin" in user_roles
    
    available_resources = []
    for resource_id, resource_info in MOCK_RESOURCES.items():
        resource_role = resource_info["role"]
        
        # Public resources: accessible to all enrolled users
        if resource_role == "public":
            available_resources.append({
                "id": resource_id,
                **resource_info
            })
        # Admin resources: only accessible to admins
        elif resource_role == "admin":
            if is_admin:
                available_resources.append({
                    "id": resource_id,
                    **resource_info
                })
        # User resources: accessible to all enrolled users (not just those with "user" role)
        # Since all enrolled users should have access, we allow it for any enrolled device
        elif resource_role == "user":
            available_resources.append({
                "id": resource_id,
                **resource_info
            })
        # If role matches user's roles (for custom roles)
        elif resource_role in user_roles:
            available_resources.append({
                "id": resource_id,
                **resource_info
            })
    
    # Log access
    await AccessService.log_access(
        db=db,
        device_id=active_device.id,
        resource_accessed="/resources/list",
        access_type="list",
        access_granted=True,
        source_ip=request.client.host if request.client else None
    )
    
    return ResourceListResponse(
        resources=available_resources,
        message="Resources retrieved successfully"
    )


@router.get("/download/{resource_id}")
async def download_resource(
    resource_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Download a resource (requires OIDC JWT token from Keycloak)
    
    Proper ZTNA flow:
    1. User authenticates with Keycloak (OIDC)
    2. Backend verifies user has enrolled, compliant device with valid TPM key
    3. Resource access is granted based on device state and user role
    """
    from app.models.posture_history import PostureHistory
    
    # Get user's devices
    devices = await DeviceService.get_devices_by_user(db, current_user.id)
    
    if not devices:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No devices found. Please enroll a device to access resources."
        )
    
    # Find active enrolled device with recent posture
    active_device = None
    for device in devices:
        if device.is_enrolled and device.status == "active":
            if device.last_posture_check:
                time_since_posture = datetime.now(timezone.utc) - device.last_posture_check.replace(tzinfo=timezone.utc)
                if time_since_posture < timedelta(minutes=15):
                    active_device = device
                    break
    
    if not active_device:
        enrolled_devices = [d for d in devices if d.is_enrolled and d.status == "active"]
        if enrolled_devices:
            active_device = max(enrolled_devices, key=lambda d: d.last_seen_at or datetime.min.replace(tzinfo=timezone.utc))
    
    if not active_device:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No active enrolled device found."
        )
    
    # Verify device state
    tpm_key_match = False
    if active_device.tpm_public_key:
        result = await db.execute(
            select(PostureHistory)
            .where(PostureHistory.device_id == active_device.id)
            .order_by(desc(PostureHistory.checked_at))
            .limit(1)
        )
        latest_posture = result.scalar_one_or_none()
        if latest_posture:
            tpm_key_match = latest_posture.signature_valid
    
    if not active_device.is_compliant or not tpm_key_match:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device is not compliant or TPM key verification failed."
        )
    
    # Check if resource exists
    if resource_id not in MOCK_RESOURCES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )
    
    resource_info = MOCK_RESOURCES[resource_id]
    
    # Get user roles from OIDC token
    auth_header = request.headers.get("Authorization")
    token = auth_header.replace("Bearer ", "") if auth_header and auth_header.startswith("Bearer ") else None
    token_payload = verify_jwt_token(token) if token else None
    user_roles = token_payload.roles if token_payload else []
    is_admin = "admin" in user_roles
    resource_role = resource_info["role"]
    
    # Check role-based access
    access_denied = False
    if resource_role == "admin" and not is_admin:
        access_denied = True
    elif resource_role not in ["public", "user", "admin"] and resource_role not in user_roles:
        access_denied = True
    
    if access_denied:
        # Log denied access
        await AccessService.log_access(
            db=db,
            device_id=active_device.id,
            resource_accessed=f"/resources/download/{resource_id}",
            access_type="download",
            access_granted=False,
            denial_reason=f"Insufficient permissions. Required role: {resource_info['role']}",
            source_ip=request.client.host if request.client else None
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. This resource requires '{resource_info['role']}' role."
        )
    
    # Log successful access
    await AccessService.log_access(
        db=db,
        device_id=active_device.id,
        resource_accessed=f"/resources/download/{resource_id}",
        access_type="download",
        access_granted=True,
        source_ip=request.client.host if request.client else None
    )
    
    # For demo, return a mock file response
    # In production, serve actual files
    return JSONResponse(
        content={
            "message": f"Download initiated for {resource_info['name']}",
            "resource": resource_info,
            "device_id": active_device.device_unique_id,
            "device_name": active_device.device_name,
            "user": current_user.username,
            "note": "This is a demo response. In production, this would serve the actual file."
        },
        headers={
            "Content-Disposition": f'attachment; filename="{resource_info["name"]}"'
        }
    )

