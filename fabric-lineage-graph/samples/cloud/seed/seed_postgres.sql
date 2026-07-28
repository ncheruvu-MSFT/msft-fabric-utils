-- ============================================================
-- samples/cloud/seed/seed_postgres.sql
-- Postgres HR domain — compensation drives Highly-Confidential propagation.
-- Lineage emitted by postgres_live harvester:
--   hr.employees           ---\
--                                --> hr.employee_compensation_v
--   hr.compensation         ---/
--   hr.employee_compensation_v --> hr.payroll_summary_v
-- ============================================================

CREATE SCHEMA IF NOT EXISTS hr;

CREATE TABLE IF NOT EXISTS hr.employees (
    employee_id  INT          PRIMARY KEY,
    full_name    TEXT         NOT NULL,
    email        TEXT         NOT NULL,    -- PII
    hire_date    DATE         NOT NULL,
    department   TEXT
);

CREATE TABLE IF NOT EXISTS hr.compensation (
    employee_id  INT          PRIMARY KEY REFERENCES hr.employees(employee_id),
    base_salary  NUMERIC(12,2) NOT NULL,   -- HR_COMPENSATION
    bonus_pct    NUMERIC(5,2)  NOT NULL,
    last_review  DATE
);

INSERT INTO hr.employees (employee_id, full_name, email, hire_date, department) VALUES
  (101,'Dana Davies','dana@contoso.com','2022-01-10','Engineering'),
  (102,'Evan Edwards','evan@contoso.com','2023-03-22','Sales'),
  (103,'Fay Fischer','fay@contoso.com','2024-07-01','HR')
ON CONFLICT (employee_id) DO NOTHING;

INSERT INTO hr.compensation (employee_id, base_salary, bonus_pct, last_review) VALUES
  (101,145000.00,12.0,'2025-12-15'),
  (102, 98000.00, 8.5,'2025-11-30'),
  (103,112000.00,10.0,'2025-12-20')
ON CONFLICT (employee_id) DO NOTHING;

-- View 1: employee_compensation_v  (joins both tables -> Highly-Confidential)
CREATE OR REPLACE VIEW hr.employee_compensation_v AS
SELECT e.employee_id,
       e.full_name,
       e.email,
       e.department,
       c.base_salary,
       c.bonus_pct,
       c.base_salary * (1 + c.bonus_pct/100.0) AS total_target_comp
FROM hr.employees e
JOIN hr.compensation c ON c.employee_id = e.employee_id;

-- View 2: payroll_summary_v  (department roll-up -- still Highly-Confidential)
CREATE OR REPLACE VIEW hr.payroll_summary_v AS
SELECT department,
       COUNT(*)                  AS headcount,
       SUM(total_target_comp)    AS total_target_comp_usd,
       AVG(total_target_comp)    AS avg_target_comp_usd
FROM hr.employee_compensation_v
GROUP BY department;
