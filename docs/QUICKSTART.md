# ZTNA Platform - Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Step 1: Prerequisites Check

Ensure you have:
- ✅ Docker Desktop installed and running
- ✅ Docker Compose installed
- ✅ Ports 80, 3000, 8000, 8080, 5432 available

### Step 2: Start the Platform

```bash
# Navigate to project root
cd ztna-project

# Start all services
make up

# Or if you don't have Make:
cd infra && docker-compose up -d
```

### Step 3: Wait for Services

Wait 30-60 seconds for all services to start, especially Keycloak.

Check status:
```bash
make status
# or
cd infra && docker-compose ps
```

### Step 4: Initialize Database

```bash
# Run migrations
make migrate

# Or manually:

```

### Step 5: Access the Application

Open your browser:

- **Frontend**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs
- **Keycloak Admin**: http://localhost:8080

### Step 6: First Login

1. Go to http://localhost:3000
2. Click "Login with Keycloak"
3. You'll be redirected to Keycloak
4. Login with:
   - **Username**: `admin`
   - **Password**: `adminsecure123`

### Step 7: Configure Keycloak Client (One-time setup)

After first login, you need to configure the frontend client in Keycloak:

1. Go to http://localhost:8080
2. Login as admin (admin/adminsecure123)
3. Navigate to: **Clients** → **Create Client**
4. Configure:
   - **Client ID**: `admin-frontend`
   - **Client authentication**: OFF (Public client)
   - **Valid redirect URIs**: `http://localhost:3000/callback`, `http://localhost/callback`
   - **Web origins**: `http://localhost:3000`, `http://localhost`
   - **Standard flow**: ON
   - **Direct access grants**: OFF
   - **PKCE Code Challenge Method**: S256

5. Save the client

### Step 8: Test the Platform

1. **View Dashboard**: http://localhost:3000/dashboard
2. **View Devices**: http://localhost:3000/devices
3. **View Policies**: http://localhost:3000/policies
4. **View Logs**: http://localhost:3000/audit

## 🔧 Common Issues

### Services won't start

```bash
# Check logs
make logs

# Restart services
make restart
```

### Can't connect to Keycloak

```bash
# Check Keycloak logs
make logs-keycloak

# Wait a bit longer (Keycloak takes time to start)
# Check if it's ready:
curl http://localhost:8080/health/ready
```

### Database connection errors

```bash
# Check if database is running
docker-compose exec postgres pg_isready

# Check backend logs
make logs-backend
```

### Frontend can't authenticate

1. Verify Keycloak client is configured (Step 7)
2. Check browser console for errors
3. Verify environment variables in `docker-compose.yml`

## 📝 Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Review [Project Plan](ZTNA%20Project%20Plan.md) for roadmap
- Check API documentation at http://localhost:8000/docs

## 🆘 Need Help?

- Check logs: `make logs`
- View service status: `make status`
- Open an issue in the repository

---

**Happy Zero Trust Networking! 🔒**

