# Clear All Databases - Manual Commands

This document provides commands to clear all data from all databases in the ZTNA project.

## Quick Commands

### Option 1: Using Scripts (Recommended)

**Linux/Mac:**
```bash
cd backend/scripts
chmod +x clear_all_databases.sh
./clear_all_databases.sh
```

**Windows (PowerShell):**
```powershell
cd backend/scripts
.\clear_all_databases.ps1
```

### Option 2: Manual Commands

#### Clear ZTNA Platform Database

```bash
docker exec -it ztna-db psql -U ztnauser -d ztna -c "
SET session_replication_role = 'replica';
TRUNCATE TABLE access_logs, audit_logs, devices, enrollment_codes, policies, posture_history, users CASCADE;
SET session_replication_role = 'origin';
SELECT setval('users_id_seq', 1, false);
SELECT setval('devices_id_seq', 1, false);
SELECT setval('policies_id_seq', 1, false);
SELECT setval('posture_history_id_seq', 1, false);
SELECT setval('access_logs_id_seq', 1, false);
SELECT setval('audit_logs_id_seq', 1, false);
SELECT setval('enrollment_codes_id_seq', 1, false);
"
```

#### Clear Keycloak Database

```bash
docker exec -it ztna-keycloak-db psql -U keycloak -d keycloak -c "
TRUNCATE TABLE realm, client, user_entity, keycloak_role, keycloak_group, 
  user_role_mapping, user_group_membership, user_session, client_session,
  credential, user_attribute, group_attribute, role_attribute,
  federated_identity, federated_user, identity_provider, event_entity
CASCADE;
"
```

### Option 3: Drop and Recreate Databases (Nuclear Option)

⚠️ **WARNING**: This will completely remove the databases and all data. You'll need to run migrations again.

#### ZTNA Database:
```bash
# Stop services
docker-compose -f infra/docker-compose.yml down

# Remove volume
docker volume rm ztna-project_pgdata

# Start services (will recreate database)
docker-compose -f infra/docker-compose.yml up -d postgres

# Wait for database to be ready, then run migrations
docker exec -it ztna-backend alembic upgrade head
```

#### Keycloak Database:
```bash
# Stop services
docker-compose -f infra/docker-compose.yml down

# Remove volume
docker volume rm ztna-project_keycloak_db_data

# Start services (will recreate database and re-import realm)
docker-compose -f infra/docker-compose.yml up -d keycloak-db keycloak
```

## After Clearing Databases

1. **Restart Keycloak** to re-import the realm:
   ```bash
   docker-compose -f infra/docker-compose.yml restart keycloak
   ```

2. **Verify Keycloak** is accessible:
   ```bash
   curl http://localhost:8080/health
   ```

3. **Check Backend** is working:
   ```bash
   curl http://localhost:8000/health
   ```

## Database Credentials

### ZTNA Platform Database
- **Container**: `ztna-db`
- **Database**: `ztna`
- **User**: `ztnauser`
- **Password**: `supersecret`

### Keycloak Database
- **Container**: `ztna-keycloak-db`
- **Database**: `keycloak`
- **User**: `keycloak`
- **Password**: `keycloakpass`

## Notes

- Truncating tables preserves the schema but removes all data
- Sequences are reset to start from 1
- Keycloak will automatically re-import the realm from `realm-export.json` on restart
- Foreign key constraints are handled with CASCADE
- All user sessions, devices, policies, and logs will be removed

