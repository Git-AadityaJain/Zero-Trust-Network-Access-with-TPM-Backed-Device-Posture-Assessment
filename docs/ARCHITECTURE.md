# ZTNA Platform Architecture

## System Overview

The ZTNA Platform is a comprehensive Zero Trust Network Access system that provides secure, policy-driven remote access to internal resources with continuous device posture verification.

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Browser                        │
│                    (React Frontend)                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ HTTPS/HTTP
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                         Nginx                                │
│                    Reverse Proxy                             │
│  - Routes / → Frontend                                       │
│  - Routes /api → Backend                                     │
│  - Routes /auth → Keycloak                                   │
└──────┬──────────────────┬──────────────────┬────────────────┘
       │                  │                  │
       │                  │                  │
┌──────▼──────┐  ┌────────▼────────┐  ┌─────▼─────────┐
│  Frontend   │  │    Backend       │  │   Keycloak    │
│   (React)   │  │   (FastAPI)      │  │   (OIDC)      │
│             │  │                  │  │               │
│ Port: 3000  │  │  Port: 8000      │  │  Port: 8080   │
└─────────────┘  └────────┬─────────┘  └───────────────┘
                           │
                           │
                  ┌────────▼────────┐
                  │   PostgreSQL    │
                  │   (Database)    │
                  │   Port: 5432    │
                  └─────────────────┘
```

## Zero Trust Architecture

The platform implements Zero Trust principles where:
- **Never trust, always verify** - Every access request is verified
- **Device attestation** - TPM-based hardware-bound device identity
- **Continuous posture assessment** - Real-time device compliance monitoring
- **Policy-based access control** - Role and compliance-based resource access

### Zero Trust Flow

```
┌─────────────┐                    ┌──────────────┐                    ┌─────────────┐
│   Browser   │                    │   Backend    │                    │  DPA Agent  │
│  (Webapp)   │                    │   Server     │                    │  (Windows)  │
└──────┬──────┘                    └──────┬───────┘                    └──────┬──────┘
       │                                   │                                   │
       │ 1. Login (OIDC/JWT)              │                                   │
       ├──────────────────────────────────>│                                   │
       │                                   │                                   │
       │ 2. GET /api/user/current-device-state                              │
       ├──────────────────────────────────>│                                   │
       │                                   │                                   │
       │                                   │ 3. Check DB:                      │
       │                                   │    - User's devices               │
       │                                   │    - Latest posture               │
       │                                   │    - TPM key match                │
       │                                   │    - Compliance status            │
       │                                   │                                   │
       │ 4. Response: {hasDpa, tpmKeyMatch, compliant, ...}                 │
       │<──────────────────────────────────┤                                   │
       │                                   │                                   │
       │                                   │                                   │
       │                                   │ 5. POST /api/posture/submit       │
       │                                   │<───────────────────────────────────┤
       │                                   │                                   │
       │                                   │ 6. Verify TPM signature           │
       │                                   │    Update device state             │
       │                                   │                                   │
       │                                   │ 7. Response: {status, compliant}   │
       │                                   │───────────────────────────────────>│
       │                                   │                                   │
       │                                   │ (Continuous - every 5 min)       │
```

## Data Flow

### Authentication Flow

1. **User Login**:
   - User clicks "Login with Keycloak" on frontend
   - Frontend generates PKCE code verifier and challenge
   - Redirects to Keycloak authorization endpoint
   - User authenticates with Keycloak

2. **Token Exchange**:
   - Keycloak redirects back to frontend with authorization code
   - Frontend exchanges code for access token (using PKCE)
   - Access token stored in localStorage

3. **API Requests**:
   - Frontend includes access token in Authorization header
   - Backend validates token with Keycloak JWKS
   - Backend extracts user info and roles from token

### Device State Verification

1. **Frontend Checks Device State**:
   - Frontend calls `GET /api/users/me/current-device-state`
   - Backend checks:
     - User's enrolled devices
     - Latest posture report (within threshold)
     - TPM key verification status
     - Device compliance status

2. **Access Decision**:
   - If device is compliant and verified → Allow access
   - If device is non-compliant → Deny access or require step-up
   - If no device enrolled → Prompt for enrollment

### Device Enrollment Flow

1. **DPA Agent Enrollment**:
   - DPA agent collects device fingerprint and posture data
   - Submits enrollment request with enrollment code
   - Backend creates device record in "pending" status

2. **Admin Approval**:
   - Admin reviews pending device in frontend
   - Admin approves device and creates user account
   - Device status changes to "active"
   - User account created in Keycloak and local database

3. **Posture Submission**:
   - DPA agent periodically submits posture data
   - Backend validates signature and evaluates compliance
   - Compliance status updated in database

### Policy Enforcement Flow

1. **Access Request**:
   - User/device requests access to resource
   - Backend evaluates policies based on:
     - User roles
     - Device compliance status
     - Posture data
     - Context (time, location, etc.)

2. **Decision**:
   - Policy engine evaluates all active policies
   - Access granted or denied
   - Decision logged in access_logs table

3. **Enforcement**:
   - Nginx validates JWT token
   - Routes request to appropriate backend service
   - Access logs recorded

## Database Schema

### Core Tables

- **users**: User accounts linked to Keycloak
- **devices**: Device records with posture data
- **policies**: Security policies with rules
- **posture_history**: Historical posture check results
- **enrollment_codes**: One-time enrollment codes
- **audit_logs**: Administrative action logs
- **access_logs**: Resource access attempt logs

### Relationships

```
users (1) ────< (many) devices
devices (1) ────< (many) posture_history
devices (1) ────< (many) access_logs
users (1) ────< (many) audit_logs
```

## Security Features

### Authentication & Authorization

- **OIDC/OAuth2** with PKCE for frontend
- **JWT tokens** for API authentication
- **Role-based access control** (RBAC)
- **Keycloak** as identity provider

### Device Security

- **Hardware fingerprinting** (SHA256 hash of motherboard serial, BIOS serial, system UUID)
- **Fallback identifiers** (hostname, MAC address, Machine GUID) when hardware IDs unavailable
- **TPM-based signing** for posture data (RSA-PSS with SHA256)
- **HMAC signatures** as fallback (if TPM unavailable)
- **Enrollment code** validation (one-time use codes)
- **Continuous posture reporting** (default: every 5 minutes)
- **Signature verification** on every posture submission

### Network Security

- **TLS/HTTPS** (configurable)
- **CORS** protection
- **Security headers** in Nginx
- **Request size limits**

## Deployment Architecture

### Development

- All services run in Docker containers
- Docker Compose orchestrates services
- Local development with hot-reload
- Self-signed certificates for HTTPS (optional)

### Production Considerations

- Use managed PostgreSQL or external database
- Keycloak in HA mode or managed service
- Nginx with proper TLS certificates
- Container orchestration (Kubernetes)
- Secrets management
- Monitoring and logging
- Backup and disaster recovery

## API Architecture

### RESTful Endpoints

- `/api/users` - User management
- `/api/devices` - Device management
- `/api/policies` - Policy management
- `/api/posture` - Posture submission
- `/api/audit` - Audit logs
- `/api/access` - Access logs
- `/api/enrollment` - Enrollment codes

### Public Endpoints (No Auth)

- `POST /api/devices/enroll` - Device enrollment
- `GET /api/devices/status/{device_id}` - Device status check
- `POST /api/posture/submit` - Posture data submission

### Protected Endpoints

- All other endpoints require valid JWT token
- Admin endpoints require "admin" role

## Frontend Architecture

### Component Structure

```
src/
├── pages/          # Page components
├── components/     # Reusable components
├── services/       # API services (OIDC, API client)
├── context/        # React context (Auth)
├── hooks/          # Custom React hooks
└── api/            # API service modules
```

### State Management

- **React Context** for authentication state
- **React Hooks** for data fetching
- **Local Storage** for token persistence
- **Axios** for HTTP requests

## Integration Points

### Keycloak Integration

- **Realm**: `master` (configurable)
- **Frontend Client**: `admin-frontend` (public, PKCE)
- **Backend Client**: `ZTNA-Platform-realm` (confidential)
- **Roles**: `admin`, `user`, `dpa-device`

### DPA Agent Integration

- **Enrollment**: `POST /api/devices/enroll`
- **Status Check**: `GET /api/devices/status/{device_id}`
- **Posture Submit**: `POST /api/posture/submit`
- **Authentication**: Device signature validation

## Monitoring & Logging

### Logging

- **Backend**: Python logging to stdout
- **Frontend**: Console logging
- **Nginx**: Access and error logs
- **Keycloak**: Built-in logging

### Health Checks

- `/health` - Basic health check
- `/health/detailed` - Component health status
- `/health/readiness` - Kubernetes readiness probe
- `/health/liveness` - Kubernetes liveness probe

## Scalability Considerations

### Horizontal Scaling

- **Backend**: Stateless, can scale horizontally
- **Frontend**: Static files, can use CDN
- **Database**: Read replicas for read-heavy workloads
- **Keycloak**: HA mode with shared database

### Performance Optimization

- **Database indexing** on frequently queried fields
- **Connection pooling** for database
- **Caching** for JWKS and user info
- **CDN** for frontend static assets

---

**Last Updated**: 2024

