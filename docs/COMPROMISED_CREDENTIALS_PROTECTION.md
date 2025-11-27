# Compromised Credentials Protection

## Overview

This document explains how the ZTNA architecture protects against compromised credentials (stolen passwords, tokens, etc.).

## Threat Model

### Scenario: Attacker Steals User Credentials
1. Attacker obtains user's password (phishing, data breach, etc.)
2. Attacker logs into Keycloak with stolen credentials
3. Attacker receives valid OIDC token
4. **Question**: Can attacker access protected resources?

### Answer: **NO** - Without Physical Device Access

## Protection Mechanisms

### 1. Device Enrollment Requirement

**What it means:**
- Every user must enroll at least one physical device
- Enrollment requires:
  - TPM key initialization (`TPMSigner.exe init-key`)
  - TPM public key stored in backend database
  - Device linked to user account

**How it protects:**
- Attacker cannot enroll a new device without:
  - Physical access to user's machine
  - Admin privileges on that machine
  - Enrollment code (if required)

**Result:** Attacker has no enrolled devices → Access denied

### 2. TPM Key Verification

**What it means:**
- Every posture report is signed with TPM private key
- Backend verifies signature using stored TPM public key
- Signature verification proves:
  - Same TPM key is present on device
  - Report is authentic (not forged)
  - Device is the one that was enrolled

**How it protects:**
- Attacker cannot forge posture reports
- Attacker cannot use a different device (different TPM key)
- Backend detects signature mismatch → Access denied

### 3. Continuous Posture Reporting

**What it means:**
- DPA agent runs continuously on enrolled device
- Reports posture every 5 minutes
- Backend tracks `last_posture_check` timestamp

**How it protects:**
- If DPA stops reporting → Access denied
- If posture is stale (>15 minutes) → Access denied
- Attacker cannot fake posture reports (requires TPM signature)

### 4. Policy Decision Endpoint

**Endpoint:** `POST /api/access/decision`

**What it does:**
1. Verifies user identity (OIDC token)
2. Checks for enrolled devices
3. Verifies TPM key matches database
4. Checks device compliance
5. Evaluates risk factors
6. Returns access decision

**Risk Levels:**
- **Low**: Device verified, compliant, recent posture
- **Medium**: Stale posture, but device verified
- **High**: No device, non-compliant, or policy violation
- **Critical**: TPM key mismatch (possible compromise)

**Step-Up Authentication:**
- If risk level is medium/high/critical → `requires_step_up: true`
- Frontend can prompt for additional authentication
- Example: MFA, security questions, admin approval

## Attack Scenarios

### Scenario 1: Stolen Password Only
```
Attacker:
1. Logs into Keycloak ✅ (has password)
2. Gets OIDC token ✅
3. Calls /api/access/decision
4. Backend checks: No enrolled devices ❌
5. Result: Access denied, risk_level="high"
```

### Scenario 2: Stolen Password + Token
```
Attacker:
1. Steals OIDC refresh token
2. Gets new access token ✅
3. Calls /api/access/decision
4. Backend checks: No enrolled devices ❌
5. Result: Access denied, risk_level="high"
```

### Scenario 3: Stolen Password + Physical Device Access
```
Attacker:
1. Logs into Keycloak ✅
2. Has physical access to user's device ✅
3. Can run DPA agent ✅
4. Calls /api/access/decision
5. Backend checks:
   - Device enrolled ✅
   - TPM key matches ✅
   - Device compliant ✅
6. Result: Access granted ✅

Note: This is expected - if attacker has physical device access,
they can access resources. This is a physical security issue,
not a credential compromise issue.
```

### Scenario 4: Compromised Device (TPM Key Changed)
```
Attacker:
1. Logs into Keycloak ✅
2. Device was compromised, TPM key changed
3. DPA reports posture with new TPM key
4. Backend verifies signature:
   - Stored key: Old TPM public key
   - Signature: Signed with new TPM key
   - Verification: FAILS ❌
5. Result: Access denied, risk_level="critical", tpm_key_match=false
```

## Implementation

### Backend Verification Flow

```python
# POST /api/access/decision
1. Verify OIDC token (user identity)
2. Get user's devices from database
3. Check for active enrolled device
4. Get latest posture history
5. Verify TPM signature matches stored key
6. Check device compliance
7. Check posture freshness (<15 minutes)
8. Evaluate policies
9. Return decision with risk level
```

### Frontend Usage

```javascript
// After login
const decision = await apiClient.post('/access/decision', {
  resource: '*',
  context: {}
});

if (!decision.allowed) {
  // Show error message
  if (decision.risk_level === 'critical') {
    alert('TPM key verification failed. Device may be compromised.');
  } else if (decision.requires_step_up) {
    // Prompt for additional authentication
    promptStepUpAuth();
  }
} else {
  // Allow access to resources
  loadResources();
}
```

## Best Practices

### 1. Enforce MFA on Keycloak
- Even with device verification, MFA adds extra layer
- Prevents password-only attacks

### 2. Monitor Risk Levels
- Log all policy decisions
- Alert on critical risk levels
- Track failed access attempts

### 3. Device Quarantine
- Admin can quarantine devices via dashboard
- Quarantined devices cannot access resources
- Useful if device is lost/stolen

### 4. Session Management
- Short-lived OIDC tokens (15-30 minutes)
- Require re-authentication for sensitive operations
- Revoke sessions on suspicious activity

### 5. Audit Logging
- Log all access decisions
- Track device state changes
- Monitor TPM signature failures

## Summary

**Key Principle:** Credentials alone are not enough. Access requires:
1. ✅ Valid user identity (OIDC token)
2. ✅ Enrolled physical device
3. ✅ TPM key matches database
4. ✅ Device is compliant
5. ✅ Recent posture reports
6. ✅ Policy evaluation passes

**Result:** Even with stolen credentials, attacker cannot access resources without:
- Physical access to enrolled device
- Ability to run DPA agent
- Valid TPM key on that device

This is the core of Zero Trust Network Access (ZTNA).

