# ZTNA Architecture Refactor - Proper Implementation

## Overview

This document outlines the refactoring from browser-to-DPA communication to proper ZTNA architecture where:
- **Browser/Webapp** only communicates with **Backend**
- **DPA Agent** continuously reports posture to **Backend**
- **Backend** verifies TPM signatures and maintains device state
- **Webapp** checks device state from backend (never directly with DPA)

## Architecture Flow

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

## Key Changes

### 1. Remove Browser-to-DPA Communication
- ❌ Remove: `POST http://localhost:8081/sign-challenge`
- ❌ Remove: Challenge/response flow from frontend
- ❌ Remove: DPA API server challenge signing endpoint
- ✅ Keep: DPA API server for health checks (optional, can be removed)

### 2. New Backend Endpoint
- ✅ Add: `GET /api/user/current-device-state`
- Returns: Device posture state based on latest verified posture reports

### 3. Frontend Changes
- ✅ Use: Standard OIDC tokens (already have)
- ✅ Check: Device state from backend endpoint
- ✅ Remove: Challenge signing flow
- ✅ Remove: Device token issuance flow

### 4. Resource Access
- ✅ Use: OIDC tokens for authentication
- ✅ Check: Device state before allowing resource access
- ✅ Enforce: Policy based on device compliance

## Implementation Steps

1. Create `/api/user/current-device-state` endpoint
2. Track TPM key verification status in device model
3. Update frontend to use new endpoint
4. Remove challenge/response flow
5. Update resource access to use OIDC + device state
6. Create policy decision endpoint for login verification

