-- Complex scenario, gold layer: marts + a view that intentionally LEAKS PII
-- into a "public_marketing" target. The DLP gate MUST flag this edge.

INSERT INTO gold.customer_revenue_mart (customer_id, email, total_revenue)
SELECT s.customer_id, s.email, SUM(i.amount) AS total_revenue
FROM   silver.customer_360   s
JOIN   silver.invoices_clean i ON i.customer_id = s.customer_id
GROUP BY s.customer_id, s.email;

-- Intentionally bad: writes email into a target whose seed label is "Public".
-- The label propagation engine will overwrite that to Confidential-PII and
-- the DLP gate will record a violation.
CREATE OR ALTER VIEW gold.public_marketing AS
SELECT customer_id, email, total_revenue
FROM   gold.customer_revenue_mart;
