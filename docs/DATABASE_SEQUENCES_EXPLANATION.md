# Database Sequences - Explanation

## What are Sequences?

Sequences in PostgreSQL are database objects that generate unique, sequential numbers. They are **automatically created** when you define a primary key column with auto-incrementing behavior.

## Why Do They Exist?

In your SQLAlchemy models, you have:
```python
id = Column(Integer, primary_key=True, index=True)
```

When SQLAlchemy creates these tables in PostgreSQL, it automatically:
1. Creates a sequence (e.g., `users_id_seq`)
2. Sets the column's default value to use that sequence
3. This allows auto-incrementing IDs: 1, 2, 3, 4, ...

## Your Sequences

Each table with an auto-incrementing primary key has a corresponding sequence:

| Table | Sequence | Purpose |
|-------|----------|---------|
| `users` | `users_id_seq` | Generates user IDs (1, 2, 3...) |
| `devices` | `devices_id_seq` | Generates device IDs |
| `policies` | `policies_id_seq` | Generates policy IDs |
| `posture_history` | `posture_history_id_seq` | Generates posture history IDs |
| `access_logs` | `access_logs_id_seq` | Generates access log IDs |
| `audit_logs` | `audit_logs_id_seq` | Generates audit log IDs |
| `enrollment_codes` | `enrollment_codes_id_seq` | Generates enrollment code IDs |

## Can They Be Dropped?

**Short answer: NO, you should NOT drop them.**

### Why Not?

1. **They're required** - Without sequences, your tables cannot auto-generate IDs
2. **They'll be recreated** - If you drop them, they'll be automatically recreated when you insert data
3. **They're harmless** - Sequences don't take up significant space or cause issues
4. **They're normal** - Every PostgreSQL database with auto-incrementing IDs has them

### What Happens If You Drop Them?

If you drop a sequence:
- The next INSERT will fail with an error
- PostgreSQL will try to recreate it automatically (in some cases)
- You may need to manually recreate it or run migrations again

## Checking Sequence Usage

You can check which sequences are being used by which columns:

```sql
-- See all sequences and their current values
SELECT 
    schemaname,
    sequencename,
    last_value,
    is_called
FROM pg_sequences
WHERE schemaname = 'public'
ORDER BY sequencename;

-- See which columns use which sequences
SELECT 
    t.table_name,
    c.column_name,
    c.column_default
FROM information_schema.tables t
JOIN information_schema.columns c ON t.table_name = c.table_name
WHERE t.table_schema = 'public'
  AND c.column_default LIKE 'nextval%'
ORDER BY t.table_name, c.column_name;
```

## Resetting Sequences

After truncating tables, you should reset sequences to start from 1:

```sql
-- Reset a sequence
SELECT setval('users_id_seq', 1, false);

-- Check current value
SELECT currval('users_id_seq');
```

This is already included in the clear database scripts.

## Summary

- ✅ **Sequences are normal** - They're automatically created and necessary
- ✅ **Keep them** - They're required for auto-incrementing IDs
- ✅ **Reset them** - After truncating tables, reset sequences to 1
- ❌ **Don't drop them** - They're needed for your application to work

The sequences you see are **expected and correct**. They're part of how PostgreSQL handles auto-incrementing primary keys.

