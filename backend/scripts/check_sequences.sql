-- Check all sequences and their usage
-- Run with: docker exec -i ztna-db psql -U ztnauser -d ztna < check_sequences.sql

-- Show all sequences with their current values
SELECT 
    schemaname,
    sequencename,
    last_value,
    is_called,
    CASE 
        WHEN is_called THEN last_value
        ELSE last_value - 1
    END AS next_value
FROM pg_sequences
WHERE schemaname = 'public'
ORDER BY sequencename;

-- Show which columns use which sequences
SELECT 
    t.table_name,
    c.column_name,
    c.column_default,
    CASE 
        WHEN c.column_default LIKE 'nextval%' THEN 
            regexp_replace(
                regexp_replace(c.column_default, '.*nextval\(''([^'']+)''.*', '\1'),
                '::.*', ''
            )
        ELSE NULL
    END AS sequence_name
FROM information_schema.tables t
JOIN information_schema.columns c ON t.table_name = c.table_name
WHERE t.table_schema = 'public'
  AND t.table_type = 'BASE TABLE'
  AND c.column_default LIKE 'nextval%'
ORDER BY t.table_name, c.column_name;

-- Show unused sequences (if any)
SELECT 
    s.sequencename,
    s.last_value
FROM pg_sequences s
WHERE s.schemaname = 'public'
  AND NOT EXISTS (
    SELECT 1
    FROM information_schema.columns c
    WHERE c.column_default LIKE '%' || s.sequencename || '%'
  )
ORDER BY s.sequencename;

