-- Easy scenario: single T-SQL file, single source -> single target.
-- Expected: TsqlHarvester emits exactly 1 edge.

INSERT INTO silver.customers (id, name, email)
SELECT id, full_name AS name, email
FROM   bronze.crm_customers;
