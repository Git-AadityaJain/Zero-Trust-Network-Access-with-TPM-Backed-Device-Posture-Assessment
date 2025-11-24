# ZTNA Platform - Zero Trust Network Access System

A comprehensive Zero Trust Network Access (ZTNA) platform with device posture assessment, policy enforcement, and secure application access.

## 🏗️ Architecture

### System Components

- **Backend**: FastAPI (Python) with async SQLAlchemy
- **Frontend**: React with OIDC authentication
- **Database**: PostgreSQL
- **Identity Provider**: Keycloak (OIDC)
- **Reverse Proxy**: Nginx
- **Device Agent**: Python-based DPA (Device Posture Agent)

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
                  │   (Database)    │
                  │   Port: 5432    │
                  └─────────────────┘
```

### Authentication Flow

1. User clicks "Login with Keycloak" on frontend
2. Frontend generates PKCE code verifier and challenge
3. Redirects to Keycloak authorization endpoint
4. User authenticates with Keycloak
5. Keycloak redirects back to `/callback` with authorization code
6. Frontend exchanges code for access token
7. Access token is used for API requests with Bearer authentication

## 📋 Prerequisites

### Required
- Docker and Docker Compose
- Ports 80, 3000, 8000, 8080, 5432 available

### Optional (for local development)
- Make (for convenience commands)
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### For DPA (Device Posture Agent)
- Windows 10/11 (64-bit)
- TPM 2.0 enabled
- .NET 6.0 Runtime (x64) - for TPMSigner
- Python 3.8+ (64-bit)

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

**Note**: Change these credentials in production!

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
│   │   ├── middleware/       # Custom middleware
│   │   └── main.py           # Application entry point
│   ├── alembic/              # Database migrations
│   ├── scripts/              # Utility scripts
│   ├── tests/                # Backend tests
│   └── requirements.txt      # Python dependencies
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── pages/            # Page components
│   │   ├── components/       # Reusable components
│   │   ├── services/         # API services
│   │   ├── context/          # React context
│   │   └── utils/            # Utility functions
│   ├── public/               # Static assets
│   └── package.json          # Node.js dependencies
├── dpa/                      # Device Posture Agent
│   ├── core/                 # Core DPA functionality
│   ├── modules/              # Posture collection modules
│   ├── cli/                  # CLI tools
│   ├── config/               # Configuration
│   ├── utils/                # Utility functions
│   └── tests/                # DPA tests
├── TPMSigner/                # C# TPM signing tool
├── infra/                    # Infrastructure configuration
│   ├── docker-compose.yml    # Docker Compose configuration
│   ├── nginx/                # Nginx configuration
│   │   ├── conf.d/           # Nginx site configs
│   │   └── nginx.conf        # Main Nginx config
│   └── keycloak-setup.sh     # Keycloak setup script
├── scripts/                  # Project-wide scripts
│   ├── setup_cloudflare_tunnel.ps1
│   ├── create_ngrok_config.ps1
│   └── update_ngrok_urls.ps1
├── tests/                    # Integration tests
├── realm-export.json         # Keycloak realm export
├── Makefile                  # Convenience commands
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
make lint-backend      # Lint backend code
make format-backend    # Format backend code
make clean             # Remove all containers and volumes
```

### Using Docker Compose

```bash
cd infra
docker-compose up -d           # Start services
docker-compose down             # Stop services
docker-compose logs -f          # View logs
docker-compose exec backend bash # Open backend shell
docker-compose exec postgres psql -U ztnauser -d ztna  # Database shell
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
- `security-admin-console`: Keycloak admin console client
- `ZTNA-Platform-realm`: Confidential client (for backend)

**Note**: When using external access (ngrok/Cloudflare), manually update client redirect URIs in Keycloak Admin Console.

## 📡 API Endpoints

### Authentication Required
All API endpoints (except health checks) require a valid JWT token in the Authorization header:

```
Authorization: Bearer <access_token>
```

### Main Endpoints

- `GET /api/users` - List users (admin)
- `GET /api/devices` - List devices
- `GET /api/devices/pending` - Pending devices (admin)
- `GET /api/policies` - List policies
- `GET /api/audit/logs` - Audit logs
- `GET /api/access/logs` - Access logs
- `POST /api/devices/enroll` - Device enrollment (public)
- `POST /api/posture/submit` - Submit posture data (public)

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

### Frontend Tests

```bash
make test-frontend
# Or
cd frontend && npm test
```

## 🌐 External Access (ngrok/Cloudflare)

The platform supports external access via tunneling services. Keycloak is accessible via the `/auth` path.

### ngrok Setup

1. **Create ngrok configuration:**
   ```powershell
   .\scripts\create_ngrok_config.ps1 -Authtoken "your-ngrok-token"
   ```

2. **Start ngrok tunnel:**
   ```bash
   ngrok start ztna
   ```

3. **Update application URLs:**
   ```powershell
   .\scripts\update_ngrok_urls.ps1 -NgrokUrl "https://your-ngrok-url.ngrok-free.app"
   ```

4. **Update Keycloak client redirect URIs manually:**
   - Access Keycloak Admin: `https://your-url.ngrok-free.app/auth/admin`
   - Go to **Clients** → **admin-frontend**
   - Add to **Valid Redirect URIs**: `https://your-url.ngrok-free.app/callback`
   - Add to **Web Origins**: `https://your-url.ngrok-free.app`
   - Go to **Clients** → **security-admin-console**
   - Add to **Valid Redirect URIs**: `https://your-url.ngrok-free.app/auth/admin/master/console/`
   - Add to **Web Origins**: `https://your-url.ngrok-free.app`

5. **Rebuild frontend** (environment variables are bundled at build time):
   ```bash
   cd infra && docker-compose build frontend && docker-compose up -d
   ```

**Note**: Keycloak is accessible via `/auth` path (e.g., `https://your-url.ngrok-free.app/auth/admin`)

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
- `DPA_BACKEND_URL`: Backend API URL (e.g., `https://your-domain.com` or `http://localhost:8000`)
- `DPA_TPM_ENABLED`: Enable/disable TPM signing (`true`/`false`, default: `true`)
- `DPA_REPORTING_INTERVAL`: Posture reporting interval in seconds (default: `300`)

### DPA Configuration

The DPA can be configured in multiple ways:

1. **Environment Variables** (recommended for remote access):
   ```bash
   set DPA_BACKEND_URL=https://your-domain.com
   python -m dpa.cli.enroll_cli --enrollment-code YOUR_CODE
   ```

2. **CLI Arguments**:
   ```bash
   python -m dpa.cli.enroll_cli --backend-url https://your-domain.com --enrollment-code YOUR_CODE
   ```

3. **Config File** (stored in `C:\ProgramData\ZTNA\config.json`):
   ```json
   {
     "backend_url": "https://your-domain.com",
     "tpm_enabled": true,
     "reporting_interval": 300
   }
   ```

**DPA API Endpoints** (must match backend):
- `POST /api/devices/enroll` - Device enrollment
- `POST /api/posture/submit` - Posture data submission
- `GET /api/devices/status/{device_id}` - Device status check

### Nginx Configuration

Nginx configuration is in `infra/nginx/conf.d/default.conf`. Modify as needed for your deployment.

## 🐛 Troubleshooting

### Services won't start

1. Check if ports are already in use:
   ```bash
   netstat -tulpn | grep -E ':(80|443|3000|8000|8080|5432)'
   ```

2. Check Docker logs:
   ```bash
   make logs
   ```

### Database connection errors

1. Ensure PostgreSQL is healthy:
   ```bash
   docker-compose exec postgres pg_isready
   ```

2. Check database credentials in `backend/.env`

### Keycloak not accessible

1. Wait for Keycloak to fully start (can take 30-60 seconds)
2. Check Keycloak logs:
   ```bash
   make logs-keycloak
   ```

### Frontend can't connect to backend

1. Check CORS configuration in `backend/.env`
2. Verify API URL in frontend environment variables
3. Check Nginx proxy configuration

### External access issues (ngrok/Cloudflare)

1. Ensure Keycloak client redirect URIs are updated with external URL
2. Rebuild frontend after changing environment variables
3. Verify Nginx is correctly routing `/auth` to Keycloak
4. Check that `X-Forwarded-Proto` header is set to `https` in Nginx config

## 📚 Additional Information

- **API Documentation**: http://localhost:8000/docs - Interactive Swagger UI
- **System Architecture**: See Architecture section below

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
