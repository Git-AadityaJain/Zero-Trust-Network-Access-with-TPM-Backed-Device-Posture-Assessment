# ZTNA Project Plan (Local Development)

## Objective

Develop a Zero Trust Network Access (ZTNA) system for secure, policy-driven remote access to internal resources, leveraging a hardware-bound posture agent and continuous policy enforcement.

---

## Technology Stack Summary
- **Backend:** Python (FastAPI), PostgreSQL, SQLAlchemy
- **Device Agent:** Python (main logic), C# CLI (TPM key), DPAPI integration (pywin32) for Windows
- **Admin Dashboard:** React, Material UI, Axios/React Query
- **Authentication:** Keycloak (OIDC), python-jose for validation
- **Reverse Proxy:** Nginx (local deployment)
- **Orchestration:** Docker Compose or Minikube (for local)
- **Demo Exposure:** ngrok
- **CI/CD:** GitHub Actions, pytest/Jest
- **Documentation:** Markdown, OpenAPI/Swagger

---
## Phased Approach & Sprints (6 Sprints, 2 Weeks Each)

---
## **Sprint 1: Foundation & Authentication**

- Scaffold FastAPI backend
- Setup PostgreSQL and configure migrations
- Deploy local Keycloak via Docker
- Scaffold React dashboard and OIDC login integration
- Local Nginx reverse proxy setup (routing to /api and /admin)
- Compose/Minikube manifests for all services
- Basic container health checks
---
## **Sprint 2: Device Posture Agent (DPA) Development**

- Python agent for posture checks (OS, firewall, disk encryption, AV/EDR)
- Windows DPAPI integration for secret storage
- C# CLI for TPM key generation/signing
- Agent enrollment workflow with one-time secure code
- DPA packaging and Windows installer creation
---
## **Sprint 3: Policy Engine & Token Management**

- Policy schema and CRUD API (user, device, context attributes)
- Admin UI for policy creation/edit
- Implementation of policy evaluation (role, posture, geo, time)
- JWT token issuance, revocation and renewal logic
- Audit logging for all policy decisions
---
## **Sprint 4: Gateway/Proxy Integration**

- Nginx JWT validation (vanilla or via FastAPI /validate endpoint)
- TLS certificate setup for demo/localhost
- Routing to protected resources behind Nginx
- Enforcement of policy compliance mid-session
- Simulate compliant and non-compliant access for demo
---
## **Sprint 5: Admin Dashboard Features & Monitoring**

- Full device CRUD & management features (dashboard)
- Policy editor UI and preview evaluator
- Logs and alerts tables (with filters/export)
- Integration of real-time updates (websocket/polling)
- Admin actions: quarantine, approve, manual override
---
## **Sprint 6: Test, Harden, Document, Demo**

- Integration, negative, and security testing
- Manual tests for device copy/replay/token tamper
- CI/CD setup for build/test pipeline
- Finalize docs: setup, user guide, OpenAPI spec
- Prepare and script demo (using ngrok for remote access)
- Sprint retrospective and future work outline
---
## Sprint Deliverables & Acceptance Criteria

| Sprint   | Key Deliverables                      | Acceptance Criteria                                 |
| -------- | ------------------------------------- | --------------------------------------------------- |
| Sprint 1 | Working backend, OIDC, frontend       | Admin login via OIDC; routes up; services healthy   |
| Sprint 2 | DPA enrolls, submits posture          | Device registration, posture reported in backend    |
| Sprint 3 | Policy CRUD & evaluation, JWT issuing | Policy pass → token issued, fail → denial logged    |
| Sprint 4 | Nginx enforces JWT/policy             | Only compliant users/devices can access resources   |
| Sprint 5 | Complete dashboard & monitoring       | Devices/policies/logs/alerts visible & updatable    |
| Sprint 6 | All tests pass, docs & demo ready     | End-to-end demo with good doc coverage, CI/CD green |

---
## Risks & Mitigations
- **Windows TPM developer access:** Use DPAPI as fallback, C# CLI as stretch
- **Networking:** Use ngrok for demo exposure if public IP unavailable
- **Component integration delays:** Modularize, test API contracts early
- **Security audit:** Pen-test and run security scanners regularly
---
## Demo Setup Notes

- All components run locally, one machine (or local cluster)
- No cloud required; can be exposed for remote participants via ngrok
- Demo covers compliant/non-compliant device, policy flip, admin quarantine