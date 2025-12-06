# ZTNA Platform - Zero Trust Network Access System

A comprehensive Zero Trust Network Access (ZTNA) platform with device posture assessment, TPM-based device attestation, policy enforcement, and secure application access.

## 🎯 Overview

The ZTNA Platform provides secure, policy-driven remote access to internal resources with continuous device posture verification. It implements Zero Trust principles by:

- **Never trusting, always verifying** - Every access request is verified
- **Device attestation** - TPM-based hardware-bound device identity
- **Continuous posture assessment** - Real-time device compliance monitoring
- **Policy-based access control** - Role and compliance-based resource access
- **Audit logging** - Complete audit trail of all access decisions

## 🏗️ Architecture

### System Components

- **Backend**: FastAPI (Python 3.11+) with async SQLAlchemy
- **Frontend**: React with OIDC authentication
- **Database**: PostgreSQL
- **Identity Provider**: Keycloak (OIDC)
- **Reverse Proxy**: Nginx
- **Device Agent**: Python-based DPA (Device Posture Agent) with TPM signing

### Architecture Diagram

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
                  │   (Database)   │
                  │   Port: 5432   │
                  └─────────────────┘
                           │
                           │
                  ┌────────▼────────┐
                  │  DPA Agent      │
                  │  (Windows)      │
                  │  - TPM Signing  │
                  │  - Posture      │
                  │  - Reporting    │
                  └─────────────────┘
```

### Zero Trust Flow

1. **User Authentication**: User logs in via Keycloak (OIDC)
2. **Device Verification**: Backend checks device state (TPM key match, compliance, recent posture)
3. **Policy Evaluation**: Backend evaluates access policies based on user role and device state
4. **Resource Access**: Access granted only if user is authenticated AND device is compliant
5. **Continuous Monitoring**: DPA continuously reports device posture to backend

## 📋 Prerequisites

### Required
- Docker and Docker Compose
- Ports 80, 3000, 8000, 8080, 5432 available

### For DPA (Device Posture Agent)
- Windows 10/11 (64-bit)
- TPM 2.0 enabled
- .NET 8.0 Runtime (x64) - for TPMSigner
- Python 3.8+ (64-bit)

### Optional (for local development)
- Make (for convenience commands)
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ztna-project
```

### 2. Set Up Environment Variables

```bash
# Copy example environment file
cp backend/.env.example backend/.env

# Edit backend/.env with your configuration
# Default values work for local development
```

### 3. Start All Services

```bash
# Using Make (recommended)
make up

# Or using Docker Compose directly
cd infra && docker-compose up -d
```

### 4. Initialize Database

```bash
# Run migrations
make migrate

# Or manually
cd infra && docker-compose exec backend alembic upgrade head
```

### 5. Access the Application

- **Frontend**: http://localhost:3000 or http://localhost (via Nginx)
- **Backend API**: http://localhost:8000 or http://localhost/api
- **Keycloak Admin**: http://localhost:8080 or http://localhost/auth/admin
- **API Documentation**: http://localhost:8000/docs

### 6. Default Credentials

**Keycloak Admin Console:**
- Username: `admin`
- Password: `adminsecure123`

### 7. Generate Enrollment code
- Login as admin to the webpage
- Navigate to Enrollment Code Page
- Generate new Enrollment code

### 8. Add DPA device
```bash
 python -m dpa.cli.enroll_cli --backend-url <BACKEND URL> --enrollment-code <ENROLLMENT CODE>
```
- Post Adding device approve device from the Pending-Device Page
- Create new User
- To give user admin role:
  - Navigate to Keycloak Admin Panel
  - Go to Users page
  - Add Role Mapping Manually

### 9. Start Posture Scheduler
```bash
python -m dpa.start_posture_scheduler
```

### 10. Access Resource Page
- After a Successfull Posture report is submitted
- Gain Access to the Rescource Page
**⚠️ Note**: Change these credentials in production!

## 📁 Project Structure

```
ztna-project/
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── routers/          # API endpoints
│   │   ├── services/         # Business logic
│   │   ├── models/           # Database models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── security/         # Security utilities
│   │   └── main.py           # Application entry point
│   ├── alembic/              # Database migrations
│   ├── scripts/              # Utility scripts
│   └── requirements.txt      # Python dependencies
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── pages/            # Page components
│   │   ├── components/       # Reusable components
│   │   ├── services/         # API services
│   │   └── context/          # React context
│   └── package.json          # Node.js dependencies
├── dpa/                      # Device Posture Agent
│   ├── core/                 # Core DPA functionality
│   ├── modules/              # Posture collection modules
│   ├── cli/                  # CLI tools
│   ├── config/               # Configuration
│   └── scripts/              # Utility scripts
├── TPMSigner/                # C# TPM signing tool
├── infra/                    # Infrastructure configuration
│   ├── docker-compose.yml    # Docker Compose configuration
│   └── nginx/                # Nginx configuration
├── docs/                     # Documentation
└── README.md                 # This file
```

## 🛠️ Development Commands

### Using Make

```bash
make help              # Show all available commands
make up                # Start all services
make down              # Stop all services
make logs              # View logs from all services
make build             # Rebuild Docker images
make migrate           # Run database migrations
make test-backend      # Run backend tests
```

### Using Docker Compose

```bash
cd infra
docker-compose up -d           # Start services
docker-compose down             # Stop services
docker-compose logs -f          # View logs
docker-compose exec backend bash # Open backend shell
```

## 🔐 Authentication

The platform uses Keycloak for OIDC authentication with PKCE flow:

1. User clicks "Login with Keycloak" on the frontend
2. Redirected to Keycloak login page
3. After authentication, redirected back to `/callback`
4. Frontend exchanges authorization code for tokens
5. Access token is used for API requests

### Keycloak Configuration

The Keycloak realm is automatically imported from `realm-export.json` on first startup.

**Realm**: `master`

**Clients**:
- `admin-frontend`: Public client with PKCE (for frontend)
- `ZTNA-Platform-realm`: Confidential client (for backend)

## 📡 API Endpoints

### Public Endpoints (No Auth Required)
- `POST /api/devices/enroll` - Device enrollment
- `POST /api/posture/submit` - Posture data submission
- `GET /api/devices/status/{device_id}` - Device status check
- `GET /health` - Health check

### Authenticated Endpoints
All other endpoints require a valid JWT token:
```
Authorization: Bearer <access_token>
```

### Main Endpoints
- `GET /api/users` - List users (admin)
- `GET /api/devices` - List devices
- `GET /api/devices/pending` - Pending devices (admin)
- `GET /api/users/me/current-device-state` - Current device state
- `GET /api/policies` - List policies
- `GET /api/audit/logs` - Audit logs
- `GET /api/access/logs` - Access logs

See `/docs` for complete API documentation.

## 🧪 Testing

### End-to-End Testing

For complete DPA enrollment and posture reporting flow, see:
- **[End-to-End Testing Guide](docs/END_TO_END_TESTING_GUIDE.md)** - Step-by-step testing instructions

### Backend Tests

```bash
make test-backend
# Or
cd backend && docker-compose exec backend pytest
```

## 📚 Documentation

- **[Architecture](docs/ARCHITECTURE.md)** - Detailed system architecture
- **[Setup Guide](docs/QUICKSTART.md)** - Detailed setup instructions
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[DPA Deployment](docs/DPA_PRODUCTION_DEPLOYMENT.md)** - DPA deployment guide
- **[ZTNA Architecture](docs/ZTNA_ARCHITECTURE_REFACTOR.md)** - ZTNA principles implementation

## 🔧 Configuration

### Environment Variables

**Backend** (`backend/.env`):
- Database connection settings
- OIDC/Keycloak configuration
- CORS origins

**Frontend** (set in `docker-compose.yml` or `.env`):
- `REACT_APP_API_URL`: Backend API URL
- `REACT_APP_KEYCLOAK_URL`: Keycloak URL
- `REACT_APP_KEYCLOAK_REALM`: Keycloak realm name
- `REACT_APP_KEYCLOAK_CLIENT_ID`: Keycloak client ID

**DPA (Device Posture Agent)**:
- `DPA_BACKEND_URL`: Backend API URL
- `DPA_TPM_ENABLED`: Enable/disable TPM signing (default: `true`)
- `DPA_REPORTING_INTERVAL`: Posture reporting interval in seconds (default: `300`)

## 🐛 Troubleshooting

See **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)** for common issues and solutions.

Common issues:
- Device enrollment conflicts
- TPM key issues
- Database connection errors
- Authentication problems
- Posture reporting issues

## 🔒 Security Notes

⚠️ **This is a development setup. For production:**

1. Change all default passwords
2. Use proper TLS certificates
3. Configure Keycloak with proper SSL
4. Set up proper firewall rules
5. Use secrets management
6. Enable audit logging
7. Configure rate limiting
8. Review and harden Nginx configuration

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and linting
4. Submit a pull request

## 📄 License

[Specify your license here]

## 🆘 Support

For issues and questions, please open an issue in the repository.

---

**Built with ❤️ for Zero Trust Network Access**

