-- Complex scenario, silver layer: cleansed + joined.
--   bronze.crm_customers + bronze.web_sessions -> silver.customer_360
--   bronze.erp_invoices                        -> silver.invoices_clean

INSERT INTO silver.customer_360 (customer_id, email, phone, last_session_ts, page_views)
SELECT c.id          AS customer_id,
       c.email       AS email,
       c.phone       AS phone,
       MAX(s.event_ts) AS last_session_ts,
       COUNT(*)        AS page_views
FROM   bronze.crm_customers c
JOIN   bronze.web_sessions  s ON s.customer_id = c.id
GROUP BY c.id, c.email, c.phone;

INSERT INTO silver.invoices_clean (invoice_id, customer_id, amount, card_last4)
SELECT invoice_id, customer_id, amount, card_last4
FROM   bronze.erp_invoices
WHERE  amount > 0;
