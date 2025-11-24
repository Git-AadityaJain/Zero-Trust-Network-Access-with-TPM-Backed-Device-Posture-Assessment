-- SQL script to clear all data from ZTNA Platform Database
-- Run with: docker exec -i ztna-db psql -U ztnauser -d ztna < clear_ztna_db.sql

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

-- Verify tables are empty
SELECT 
  'access_logs' AS table_name, COUNT(*) AS row_count FROM access_logs
UNION ALL
SELECT 'audit_logs', COUNT(*) FROM audit_logs
UNION ALL
SELECT 'devices', COUNT(*) FROM devices
UNION ALL
SELECT 'enrollment_codes', COUNT(*) FROM enrollment_codes
UNION ALL
SELECT 'policies', COUNT(*) FROM policies
UNION ALL
SELECT 'posture_history', COUNT(*) FROM posture_history
UNION ALL
SELECT 'users', COUNT(*) FROM users;

SELECT 'ZTNA database cleared successfully!' AS status;

