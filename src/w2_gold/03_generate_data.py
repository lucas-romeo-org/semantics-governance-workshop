# Databricks notebook source
# MAGIC %md
# MAGIC # Step 2 · Physical governance of Gold — 3. Synthetic retail data
# MAGIC Deterministic (hash-based) so every workspace gets **the same numbers**.
# MAGIC Four regions: ES, PT, FR, IT. Sales from Jan 2025 to Oct 2026. Customers carry PII.
# MAGIC
# MAGIC We also create `semantic.v_sales_es_legacy`, the kind of duplicated "BI view" every company has,
# MAGIC with its own (wrong) definition of net sales. Step 5 deprecates it.

# COMMAND ----------

dbutils.widgets.text("catalog", "sgw_shop")
dbutils.widgets.text("sales_rows", "1500000")
catalog = dbutils.widgets.get("catalog")
n_sales = int(dbutils.widgets.get("sales_rows"))
g = f"{catalog}.gold"

# COMMAND ----------

# MAGIC %md ## Dimensions

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE TABLE {g}.dim_date COMMENT 'Calendar (fiscal year = calendar year)' AS
SELECT d AS date_key, year(d) AS year, quarter(d) AS quarter, month(d) AS month,
       date_format(d, 'yyyy-MM') AS year_month, weekofyear(d) AS week, date_format(d, 'EEEE') AS day_name
FROM (SELECT explode(sequence(DATE'2024-01-01', DATE'2026-12-31', INTERVAL 1 DAY)) AS d)
""")

# 40 stores: ES 1-14, PT 15-24, FR 25-33, IT 34-40
spark.sql(f"""
CREATE OR REPLACE TABLE {g}.dim_store COMMENT 'Physical stores' AS
WITH s AS (SELECT id AS store_id FROM range(1, 41))
SELECT store_id,
       CASE WHEN store_id <= 14 THEN 'ES' WHEN store_id <= 24 THEN 'PT' WHEN store_id <= 33 THEN 'FR' ELSE 'IT' END AS region,
       element_at(CASE WHEN store_id <= 14 THEN array('Madrid','Barcelona','Valencia','Sevilla','Bilbao')
                       WHEN store_id <= 24 THEN array('Lisboa','Porto','Braga','Coimbra','Faro')
                       WHEN store_id <= 33 THEN array('Paris','Lyon','Marseille','Lille','Toulouse')
                       ELSE array('Milano','Roma','Torino','Napoli','Bologna') END,
                  CAST(pmod(store_id, 5) + 1 AS INT)) AS city,
       element_at(array('Hypermarket','Supermarket','Convenience','Online'), CAST(pmod(store_id * 7, 4) + 1 AS INT)) AS store_format,
       concat('Store ', lpad(CAST(store_id AS STRING), 3, '0')) AS store_name
FROM s
""")

spark.sql(f"""
CREATE OR REPLACE TABLE {g}.dim_product COMMENT 'Product catalogue' AS
WITH p AS (SELECT id AS product_id FROM range(1, 301))
SELECT product_id,
       concat('Product ', lpad(CAST(product_id AS STRING), 4, '0')) AS product_name,
       element_at(array('Fresh food','Grocery','Beverages','Household','Personal care','Electronics','Textile','Home & garden'),
                  CAST(pmod(product_id, 8) + 1 AS INT)) AS category,
       element_at(array('Aurora','Brisa','Cumbre','Delta','Estrella','Faro'), CAST(pmod(product_id * 3, 6) + 1 AS INT)) AS brand,
       round(2 + pmod(abs(hash(product_id, 'price')), 9800) / 100.0, 2) AS list_price,
       round(0.55 + pmod(abs(hash(product_id, 'cost')), 25) / 100.0, 2) AS cost_ratio
FROM p
""")

# 20,000 customers in contiguous id ranges per region: ES 1-7000, PT 7001-12000, FR 12001-16500, IT 16501-20000
spark.sql(f"""
CREATE OR REPLACE TABLE {g}.dim_customer COMMENT 'Loyalty customers (contains PII)' AS
WITH c AS (SELECT id AS customer_id FROM range(1, 20001)),
n AS (
  SELECT customer_id,
         CASE WHEN customer_id <= 7000 THEN 'ES' WHEN customer_id <= 12000 THEN 'PT' WHEN customer_id <= 16500 THEN 'FR' ELSE 'IT' END AS country,
         element_at(array('Ana','Pedro','Marta','João','Lucía','Pierre','Giulia','Carlos','Sofia','Marco','Inês','Hugo','Elena','Rui','Clara','Luca'),
                    CAST(pmod(abs(hash(customer_id, 'fn')), 16) + 1 AS INT)) AS first_name,
         element_at(array('García','Silva','Martin','Rossi','López','Santos','Bernard','Bianchi','Sánchez','Ferreira','Dubois','Romano'),
                    CAST(pmod(abs(hash(customer_id, 'ln')), 12) + 1 AS INT)) AS last_name
  FROM c)
SELECT customer_id, country,
       concat(first_name, ' ', last_name) AS full_name,
       lower(concat(translate(first_name, 'áéíóúãçêôÉ', 'aeiouaceoe'), '.', translate(last_name, 'áéíóúãçêôÉ', 'aeiouaceoe'), customer_id, '@example.com')) AS email,
       concat('+', CASE country WHEN 'ES' THEN '34' WHEN 'PT' THEN '351' WHEN 'FR' THEN '33' ELSE '39' END, ' 6', lpad(CAST(pmod(abs(hash(customer_id, 'ph')), 100000000) AS STRING), 8, '0')) AS phone,
       concat(country, lpad(CAST(pmod(abs(hash(customer_id, 'tax')), 100000000) AS STRING), 8, '0'), 'X') AS tax_id,
       element_at(array('Gold','Silver','Bronze'), CAST(pmod(abs(hash(customer_id, 'seg')), 3) + 1 AS INT)) AS segment
FROM n
""")
print("dimensions ok")

# COMMAND ----------

# MAGIC %md ## Facts

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE TABLE {g}.fact_sales COMMENT 'Sales lines. Grain: one product line in one ticket.' AS
WITH b AS (
  SELECT id AS sale_id,
         date_add(DATE'2025-01-01', CAST(pmod(abs(hash(id, 'd')), 669) AS INT)) AS date_key,      -- 2025-01-01 .. 2026-10-31
         CAST(pmod(abs(hash(id, 's')), 40) + 1 AS INT) AS store_id,
         CAST(pmod(abs(hash(id, 'p')), 300) + 1 AS INT) AS product_id,
         CAST(pmod(abs(hash(id, 'q')), 5) + 1 AS INT) AS quantity,
         element_at(array(0.0, 0.0, 0.0, 0.05, 0.10, 0.15, 0.20), CAST(pmod(abs(hash(id, 'disc')), 7) + 1 AS INT)) AS discount_rate,
         pmod(abs(hash(id, 'c')), 100000) AS c_rand
  FROM range(0, {n_sales})),
r AS (
  SELECT b.*, s.region AS store_region,
         CASE s.region WHEN 'ES' THEN 1 + pmod(c_rand, 7000) WHEN 'PT' THEN 7001 + pmod(c_rand, 5000)
                       WHEN 'FR' THEN 12001 + pmod(c_rand, 4500) ELSE 16501 + pmod(c_rand, 3500) END AS customer_id
  FROM b JOIN {g}.dim_store s USING (store_id))
SELECT sale_id, date_key, store_id, store_region, product_id, CAST(customer_id AS BIGINT) AS customer_id, quantity,
       round(quantity * p.list_price, 2) AS gross_amount,
       round(quantity * p.list_price * discount_rate, 2) AS discount,
       round(quantity * p.list_price * (1 - discount_rate) - quantity * p.list_price * p.cost_ratio, 2) AS margin
FROM r JOIN {g}.dim_product p USING (product_id)
""")

spark.sql(f"""
CREATE OR REPLACE TABLE {g}.fact_budget COMMENT 'Monthly sales budget by region and category' AS
SELECT date_trunc('MONTH', f.date_key) AS month, f.store_region AS region, p.category,
       round(sum(f.gross_amount - f.discount) * (0.95 + pmod(abs(hash(f.store_region, p.category, date_trunc('MONTH', f.date_key))), 16) / 100.0), 0) AS budget_amount
FROM {g}.fact_sales f JOIN {g}.dim_product p USING (product_id)
GROUP BY ALL
""")
print("facts ok")

# COMMAND ----------

# MAGIC %md ## The legacy "BI view" (the problem we are solving)

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE VIEW {catalog}.semantic.v_sales_es_legacy
COMMENT 'LEGACY view built for one BI tool. Hard-coded region filter, and net_sales ignores discounts. Do not use.' AS
SELECT d.year_month, sum(f.gross_amount) AS net_sales
FROM {g}.fact_sales f JOIN {g}.dim_date d USING (date_key)
WHERE f.store_region = 'ES'
GROUP BY d.year_month
""")

display(spark.sql(f"""
SELECT 'fact_sales' t, count(*) n FROM {g}.fact_sales UNION ALL SELECT 'fact_budget', count(*) FROM {g}.fact_budget
UNION ALL SELECT 'dim_customer', count(*) FROM {g}.dim_customer UNION ALL SELECT 'dim_store', count(*) FROM {g}.dim_store
UNION ALL SELECT 'dim_product', count(*) FROM {g}.dim_product UNION ALL SELECT 'dim_date', count(*) FROM {g}.dim_date"""))
