-- ============================================================
-- samples/cloud/seed/seed_mssql.sql
-- Azure SQL: CRM bronze + curated silver via views.
-- Lineage emitted by mssql_live harvester:
--   crm.customers  ---\
--                       --> silver.customer_360
--   crm.orders     ---/
--   silver.customer_360 --> gold.customer_revenue_mart
-- ============================================================

IF SCHEMA_ID('crm')    IS NULL EXEC('CREATE SCHEMA crm');
IF SCHEMA_ID('silver') IS NULL EXEC('CREATE SCHEMA silver');
IF SCHEMA_ID('gold')   IS NULL EXEC('CREATE SCHEMA gold');

-- ---------------- Bronze (raw) ----------------
IF OBJECT_ID('crm.customers') IS NULL
CREATE TABLE crm.customers (
    customer_id    INT          NOT NULL PRIMARY KEY,
    full_name      NVARCHAR(200) NOT NULL,
    email          NVARCHAR(200) NOT NULL,   -- PII
    phone          NVARCHAR(40),             -- PII
    ssn            CHAR(11),                 -- PII (Govt SSN)
    region         NVARCHAR(40)
);

IF OBJECT_ID('crm.orders') IS NULL
CREATE TABLE crm.orders (
    order_id       INT          NOT NULL PRIMARY KEY,
    customer_id    INT          NOT NULL REFERENCES crm.customers(customer_id),
    order_dt       DATETIME2    NOT NULL,
    amount_usd     DECIMAL(12,2) NOT NULL,
    payment_card   CHAR(16)              -- credit card (financial)
);

-- ---------------- Sample data (idempotent) ----------------
IF NOT EXISTS (SELECT 1 FROM crm.customers WHERE customer_id = 1)
INSERT INTO crm.customers (customer_id, full_name, email, phone, ssn, region) VALUES
  (1,'Alice Anderson','alice@contoso.com','+1-555-1001','111-22-3333','NA'),
  (2,'Bob Brown',     'bob@contoso.com',  '+1-555-1002','222-33-4444','NA'),
  (3,'Carla Cruz',    'carla@contoso.com','+1-555-1003','333-44-5555','EU');

IF NOT EXISTS (SELECT 1 FROM crm.orders WHERE order_id = 1)
INSERT INTO crm.orders (order_id, customer_id, order_dt, amount_usd, payment_card) VALUES
  (1,1,'2026-05-01 10:00:00', 199.99,'4111111111111111'),
  (2,2,'2026-05-02 11:00:00', 749.00,'4222222222222222'),
  (3,1,'2026-05-03 12:00:00',  49.50,'4111111111111111');

-- ---------------- Silver: customer_360 view ----------------
IF OBJECT_ID('silver.customer_360') IS NOT NULL DROP VIEW silver.customer_360;
GO
CREATE VIEW silver.customer_360 AS
SELECT c.customer_id,
       c.full_name,
       c.email,
       c.region,
       COUNT(o.order_id)        AS total_orders,
       ISNULL(SUM(o.amount_usd),0) AS lifetime_value_usd
FROM crm.customers c
LEFT JOIN crm.orders o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.full_name, c.email, c.region;
GO

-- ---------------- Gold: customer_revenue_mart view ----------------
IF OBJECT_ID('gold.customer_revenue_mart') IS NOT NULL DROP VIEW gold.customer_revenue_mart;
GO
CREATE VIEW gold.customer_revenue_mart AS
SELECT region,
       COUNT(*)                       AS customer_count,
       SUM(lifetime_value_usd)        AS region_revenue_usd,
       AVG(lifetime_value_usd)        AS avg_customer_value_usd
FROM silver.customer_360
GROUP BY region;
GO
