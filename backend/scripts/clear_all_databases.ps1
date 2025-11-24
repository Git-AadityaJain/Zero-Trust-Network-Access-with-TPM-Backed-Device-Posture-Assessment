# PowerShell script to clear all data from all databases
# This will truncate all tables but keep the schema intact

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Clearing All Database Data" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Clear ZTNA Platform Database
Write-Host ""
Write-Host "1. Clearing ZTNA Platform Database..." -ForegroundColor Yellow

$ztnaSql = @"
-- Disable foreign key checks temporarily
SET session_replication_role = 'replica';

-- Truncate all tables (cascade to handle foreign keys)
TRUNCATE TABLE 
  access_logs,
  audit_logs,
  devices,
  enrollment_codes,
  policies,
  posture_history,
  users
CASCADE;

-- Re-enable foreign key checks
SET session_replication_role = 'origin';

-- Reset sequences
SELECT setval('users_id_seq', 1, false);
SELECT setval('devices_id_seq', 1, false);
SELECT setval('policies_id_seq', 1, false);
SELECT setval('posture_history_id_seq', 1, false);
SELECT setval('access_logs_id_seq', 1, false);
SELECT setval('audit_logs_id_seq', 1, false);
SELECT setval('enrollment_codes_id_seq', 1, false);

SELECT 'ZTNA database cleared successfully' AS status;
"@

docker exec -i ztna-db psql -U ztnauser -d ztna -c $ztnaSql

# Clear Keycloak Database
Write-Host ""
Write-Host "2. Clearing Keycloak Database..." -ForegroundColor Yellow

$keycloakSql = @"
-- Truncate Keycloak tables (be careful - this will remove all Keycloak data)
TRUNCATE TABLE 
  realm_attribute,
  realm,
  client,
  client_attributes,
  client_auth_flow_bindings,
  client_default_roles,
  client_node_registrations,
  client_session,
  client_session_auth_status,
  client_session_note,
  client_session_prot_mapper,
  client_session_role,
  client_user_session_note,
  component_config,
  composite_role,
  credential,
  databasechangelog,
  databasechangeloglock,
  default_client_scope,
  event_entity,
  fed_credential,
  fed_identity_credential,
  fed_identity_provider,
  fed_identity_provider_config,
  fed_user_attribute,
  fed_user_consent,
  fed_user_consent_cl_scope,
  fed_user_credential,
  fed_user_group_membership,
  fed_user_required_action,
  fed_user_role_mapping,
  federated_identity,
  federated_user,
  group_attribute,
  group_role_mapping,
  groups,
  identity_provider,
  identity_provider_config,
  identity_provider_mapper,
  keycloak_group,
  keycloak_role,
  migration_model,
  offline_client_session,
  offline_user_session,
  protocol_mapper,
  protocol_mapper_config,
  realm_default_groups,
  realm_enabled_event_types,
  realm_events_listeners,
  realm_localizations,
  realm_required_credential,
  realm_supported_locales,
  redirect_uris,
  required_action_config,
  required_action_provider,
  resource_attribute,
  resource_policy,
  resource_scope,
  resource_server,
  resource_server_perm_ticket,
  resource_server_policy,
  resource_server_resource,
  resource_server_scope,
  role_attribute,
  user_attribute,
  user_consent,
  user_consent_client_scope,
  user_entity,
  user_federation_config,
  user_federation_mapper,
  user_federation_mapper_config,
  user_federation_provider,
  user_group_membership,
  user_required_action,
  user_role_mapping,
  user_session,
  user_session_note,
  web_origins
CASCADE;

SELECT 'Keycloak database cleared successfully' AS status;
"@

docker exec -i ztna-keycloak-db psql -U keycloak -d keycloak -c $keycloakSql

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "All databases cleared successfully!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Note: Keycloak will need to re-import the realm." -ForegroundColor Yellow
Write-Host "Restart Keycloak to re-import realm-export.json:" -ForegroundColor Yellow
Write-Host "  docker-compose restart keycloak" -ForegroundColor Yellow
Write-Host ""

