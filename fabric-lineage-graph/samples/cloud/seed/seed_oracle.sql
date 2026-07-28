-- ============================================================
-- samples/cloud/seed/seed_oracle.sql
-- Oracle SCM domain — BYO instance (Oracle XE container, Oracle DB@Azure,
-- or any reachable Oracle). Set ORACLE_DSN env var to point at it.
--
-- Lineage emitted by oracle_live harvester:
--   scm.suppliers  ---\
--                       --> scm.supplier_performance_v
--   scm.shipments  ---/
--   scm.supplier_performance_v --> scm.supplier_scorecard_v
-- ============================================================

-- Run as a user that owns the SCM schema (or grant CREATE TABLE/VIEW on SCM).

CREATE TABLE scm.suppliers (
    supplier_id   NUMBER(10) PRIMARY KEY,
    supplier_name VARCHAR2(200) NOT NULL,
    country       VARCHAR2(40),
    contact_email VARCHAR2(200)         -- PII (light)
);

CREATE TABLE scm.shipments (
    shipment_id   NUMBER(10) PRIMARY KEY,
    supplier_id   NUMBER(10) NOT NULL REFERENCES scm.suppliers(supplier_id),
    shipped_dt    DATE       NOT NULL,
    delivered_dt  DATE,
    units         NUMBER(10) NOT NULL,
    on_time_flag  CHAR(1)    NOT NULL
);

INSERT INTO scm.suppliers (supplier_id, supplier_name, country, contact_email) VALUES
  (1,'Globex Components','DE','ops@globex.example');
INSERT INTO scm.suppliers (supplier_id, supplier_name, country, contact_email) VALUES
  (2,'Initech Parts',    'US','ops@initech.example');
INSERT INTO scm.suppliers (supplier_id, supplier_name, country, contact_email) VALUES
  (3,'Hooli Logistics',  'US','ops@hooli.example');

INSERT INTO scm.shipments (shipment_id, supplier_id, shipped_dt, delivered_dt, units, on_time_flag) VALUES
  (1001, 1, DATE '2026-05-01', DATE '2026-05-05', 500, 'Y');
INSERT INTO scm.shipments (shipment_id, supplier_id, shipped_dt, delivered_dt, units, on_time_flag) VALUES
  (1002, 2, DATE '2026-05-02', DATE '2026-05-09', 250, 'N');
INSERT INTO scm.shipments (shipment_id, supplier_id, shipped_dt, delivered_dt, units, on_time_flag) VALUES
  (1003, 3, DATE '2026-05-03', DATE '2026-05-06', 800, 'Y');

COMMIT;

CREATE OR REPLACE VIEW scm.supplier_performance_v AS
SELECT s.supplier_id,
       s.supplier_name,
       s.country,
       COUNT(sh.shipment_id)                                        AS shipments_total,
       SUM(CASE WHEN sh.on_time_flag = 'Y' THEN 1 ELSE 0 END)       AS shipments_on_time,
       SUM(sh.units)                                                AS units_total
FROM scm.suppliers s
LEFT JOIN scm.shipments sh ON sh.supplier_id = s.supplier_id
GROUP BY s.supplier_id, s.supplier_name, s.country;

CREATE OR REPLACE VIEW scm.supplier_scorecard_v AS
SELECT country,
       COUNT(*)                                                AS supplier_count,
       AVG(shipments_on_time / NULLIF(shipments_total,0))      AS avg_on_time_ratio
FROM scm.supplier_performance_v
GROUP BY country;
