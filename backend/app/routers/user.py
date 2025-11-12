from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserOut
from app.crud.user import create_user, get_users
from app.db import get_db

from app.security.oidc import verify_jwt_token, TokenPayload
from app.security.rbac import (
    require_admin,
    require_security_analyst,
    require_admin_or_analyst,
    check_device_posture,
    require_roles
)

# ============================================
# PROTECTED ENDPOINTS - RBAC & AUTHENTICATION
# ============================================

protected_router = APIRouter(
    prefix="/protected",
    tags=["Security & RBAC Demo"],
    responses={
        401: {"description": "Unauthorized - Missing or invalid JWT token"},
        403: {"description": "Forbidden - Insufficient permissions"}
    }
)

@protected_router.get("/resource")
async def protected_resource(current_user: TokenPayload = Depends(verify_jwt_token)):
    """
    **Basic JWT-protected endpoint**
    
    Anyone with a valid JWT token can access this.
    
    Security: JWT signature + expiry + issuer + audience validation
    """
    return {
        "message": "Secure access granted",
        "user_id": current_user.sub,
        "username": current_user.preferred_username or current_user.sub,
        "email": current_user.email or "N/A",
        "roles": current_user.roles,
        "token_issued_at": current_user.iat,
        "token_expires_at": current_user.exp
    }

@protected_router.get("/admin-only")
async def admin_only_endpoint(current_user: TokenPayload = Depends(require_admin)):
    """
    **Admin-only endpoint**
    
    Requires: Valid JWT token + 'admin' role
    
    Security: Full JWT validation + Role-based access control (RBAC)
    """
    return {
        "message": "Welcome, admin!",
        "user_id": current_user.sub,
        "username": current_user.preferred_username or current_user.sub,
        "email": current_user.email or "N/A",
        "roles": current_user.roles,
        "admin_data": {
            "system_health": "OK",
            "active_sessions": 42,
            "total_users": 156
        }
    }

@protected_router.get("/analyst-dashboard")
async def analyst_dashboard(current_user: TokenPayload = Depends(require_admin_or_analyst)):
    """
    **Security analyst dashboard**
    
    Requires: Valid JWT token + ('admin' OR 'security-analyst' role)
    
    Security: JWT validation + Multi-role RBAC
    """
    return {
        "message": "Security analyst dashboard access granted",
        "user_id": current_user.sub,
        "username": current_user.preferred_username or current_user.sub,
        "email": current_user.email or "N/A",
        "roles": current_user.roles,
        "dashboard_metrics": {
            "active_sessions": 42,
            "threats_detected": 3,
            "devices_monitored": 156,
            "policy_violations": 2,
            "authentication_failures": 5
        }
    }

@protected_router.get("/compliant-device-only")
async def compliant_device_endpoint(current_user: TokenPayload = Depends(check_device_posture)):
    """
    **Device Posture Enforcement (DPA - Device Posture Assessment)**
    
    Requires: Valid JWT token + Device passes security posture check
    
    Security: JWT validation + Device compliance verification
    """
    return {
        "message": "Access granted - device is compliant",
        "user_id": current_user.sub,
        "username": current_user.preferred_username or current_user.sub,
        "device_id": current_user.device_id,
        "posture_status": "PASSED",
        "device_checks": {
            "firewall_enabled": True,
            "antivirus_enabled": True,
            "disk_encryption": True,
            "os_up_to_date": True
        }
    }

@protected_router.get("/my-info")
async def get_current_user_info(current_user: TokenPayload = Depends(verify_jwt_token)):
    """
    **Get current authenticated user information**
    
    Requires: Valid JWT token
    
    Security: JWT signature validation + user context extraction
    """
    return {
        "user_id": current_user.sub,
        "username": current_user.preferred_username or current_user.sub,
        "email": current_user.email or "N/A",
        "full_name": current_user.name or current_user.preferred_username or "User",
        "first_name": current_user.given_name or "User",
        "last_name": current_user.family_name or "",
        "roles": current_user.roles,
        "email_verified": current_user.email_verified,
        "token_info": {
            "issued_at": current_user.iat,
            "expires_at": current_user.exp,
            "issuer": current_user.iss,
            "audience": current_user.aud
        }
    }

# ============================================
# USER MANAGEMENT ENDPOINTS
# ============================================

user_router = APIRouter(
    prefix="/users",
    tags=["User Management"],
    responses={
        400: {"description": "Bad request - Invalid user data"},
        401: {"description": "Unauthorized - Missing JWT token"},
        403: {"description": "Forbidden - Insufficient permissions"}
    }
)

@user_router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    **Register a new user**
    
    Open endpoint for user registration (can be protected later with RBAC)
    
    Request Body:
    - email: User email address
    - full_name: User's full name
    - username: Unique username ← ADDED
    - password: User password (will be hashed in database)
    
    Returns: Created user object with ID and metadata
    """
    try:
        return create_user(db, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Error creating user"
        )

@user_router.get("/", response_model=list[UserOut])
async def list_users(
    current_user: TokenPayload = Depends(require_admin_or_analyst),
    db: Session = Depends(get_db)
):
    """
    **List all users**
    
    Requires: Valid JWT token + ('admin' OR 'security-analyst' role)
    
    Security: Full JWT validation + Role-based access control
    Allowed Roles: admin, security-analyst
    
    Returns: List of all users in the system
    """
    return get_users(db)

@user_router.get("/search/{username}", response_model=UserOut)
async def search_user(
    username: str,
    current_user: TokenPayload = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    **Search for a specific user**
    
    Requires: Valid JWT token + 'admin' role
    
    Security: Full JWT validation + Admin-only role check
    
    Path Parameters:
    - username: Username/email to search for
    
    Returns: User object if found, 404 if not found
    """
    from app.crud.user import get_user_by_email
    
    user = get_user_by_email(db, username)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return user

@user_router.get("/me", response_model=dict)
async def get_my_profile(current_user: TokenPayload = Depends(verify_jwt_token)):
    """
    **Get authenticated user's profile from JWT**
    
    Requires: Valid JWT token
    
    Returns: Current user's profile information extracted from JWT claims
    """
    return {
        "user_id": current_user.sub,
        "username": current_user.preferred_username or current_user.sub,
        "email": current_user.email or "N/A",
        "full_name": current_user.name or "User",
        "roles": current_user.roles,
        "email_verified": current_user.email_verified,
        "account_status": "ACTIVE"
    }

@user_router.get("/admin/stats", response_model=dict)
async def admin_statistics(
    current_user: TokenPayload = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    **Admin user statistics and metrics**
    
    Requires: Valid JWT token + 'admin' role
    
    Security: Admin-only access
    
    Returns: User statistics, system metrics, and administrative data
    """
    try:
        users = get_users(db)
        user_list = users if users else []
        
        # Safe attribute access with getattr
        active_count = sum(1 for u in user_list if getattr(u, 'is_active', True))
        inactive_count = sum(1 for u in user_list if not getattr(u, 'is_active', True))
        
        return {
            "total_users": len(user_list),
            "active_users": active_count,
            "inactive_users": inactive_count,
            "admin_user": current_user.preferred_username or current_user.sub,
            "admin_email": current_user.email or "N/A",
            "query_timestamp": "2025-11-12T04:17:00Z"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching admin stats: {str(e)}"
        )

# ============================================
# HEALTH CHECK & INFO ENDPOINTS (No Auth)
# ============================================

info_router = APIRouter(
    prefix="/info",
    tags=["System Info"]
)

@info_router.get("/health")
async def health_check():
    """
    **System health check**
    
    No authentication required.
    Used for load balancers, monitoring, and readiness probes.
    """
    return {
        "status": "healthy",
        "service": "ZTNA Backend API",
        "version": "0.1.0"
    }

@info_router.get("/version")
async def get_version():
    """
    **Get API version and build info**
    
    No authentication required.
    """
    return {
        "version": "0.1.0",
        "api_name": "ZTNA Platform Backend",
        "build_date": "2025-11-12",
        "status": "development"
    }
