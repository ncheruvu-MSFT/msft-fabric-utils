-- Complex scenario, bronze layer: 4 raw source tables from 3 different systems.
-- (Filenames are namespaced so the same harvester run covers all of them.)

-- CRM (Azure SQL)
INSERT INTO bronze.crm_customers (id, name, email, phone, ssn)
SELECT id, name, email, phone, social_security_number FROM raw.crm.customers;

-- ERP (Azure Postgres mirrored as bronze landing)
INSERT INTO bronze.erp_invoices (invoice_id, customer_id, amount, card_last4)
SELECT invoice_id, customer_id, amount, card_last4 FROM raw.erp.invoices;

-- Web events (Cosmos DB landing)
INSERT INTO bronze.web_sessions (session_id, customer_id, event_ts, page)
SELECT session_id, customer_id, event_ts, page FROM raw.web.sessions;

-- HR (restricted source — compensation data)
INSERT INTO bronze.hr_compensation (employee_id, base_salary, bonus)
SELECT employee_id, base_salary, bonus FROM raw.hr.compensation;
