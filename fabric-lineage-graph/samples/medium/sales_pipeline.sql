-- Medium scenario: multi-source SQL.
--   bronze.crm_customers  -+
--                          +-> silver.customer_orders --(curate)--> gold.customer_orders_view (view)
--   bronze.crm_orders     -+
--
-- Expected: 2 INSERT edges + 1 VIEW edge = 3 T-SQL edges total.

INSERT INTO silver.customer_orders (customer_id, customer_email, order_id, order_total)
SELECT c.id           AS customer_id,
       c.email        AS customer_email,
       o.id           AS order_id,
       o.total_amount AS order_total
FROM   bronze.crm_customers c
JOIN   bronze.crm_orders   o ON o.customer_id = c.id;

CREATE OR ALTER VIEW gold.customer_orders_view AS
SELECT customer_id, customer_email, COUNT(*) AS n_orders, SUM(order_total) AS revenue
FROM   silver.customer_orders
GROUP BY customer_id, customer_email;
