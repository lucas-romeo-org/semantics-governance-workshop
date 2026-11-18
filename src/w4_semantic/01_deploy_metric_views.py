# Databricks notebook source
# MAGIC %md
# MAGIC # Step 4 · Metric Views: the semantic contract
# MAGIC KPIs are defined **once**, as code (`*.yaml` next to this notebook), and consumers only ever see this layer.
# MAGIC
# MAGIC | Metric View | Showcases |
# MAGIC |---|---|
# MAGIC | `semantic.sales_metrics` | star-schema joins · atomic, **filtered** and **composed** measures · **window** measures (YTD, last year, trailing 90 days) · **share of total** |
# MAGIC | `semantic.sales_vs_budget_metrics` | two facts combined through a pre-aggregated base view · composed **YTD attainment** |
# MAGIC
# MAGIC **Exposure pattern:** consumers get `SELECT` on the `semantic` schema only. The Metric View reads `gold` with its
# MAGIC **owner's** rights, while the ABAC policies on `gold` are evaluated as the **querying user**.

# COMMAND ----------

dbutils.widgets.text("catalog", "sgw_shop")
dbutils.widgets.text("group_prefix", "wk_")
catalog, gp = dbutils.widgets.get("catalog"), dbutils.widgets.get("group_prefix")

def sql(s):
    print(s.strip()[:400], "\n")
    spark.sql(s)

# COMMAND ----------

# MAGIC %md ## Base view for the multi-fact KPI (lives in `gold`: consumers can't see it)

# COMMAND ----------

sql(f"""
CREATE OR REPLACE VIEW {catalog}.gold.v_sales_budget_monthly
COMMENT 'Base view: monthly net sales and budget by region and category (pre-aggregated to avoid fan-out)' AS
WITH s AS (
  SELECT date_trunc('MONTH', f.date_key) AS month, f.store_region AS region, p.category,
         sum(f.gross_amount - f.discount) AS net_sales
  FROM {catalog}.gold.fact_sales f JOIN {catalog}.gold.dim_product p USING (product_id)
  GROUP BY ALL)
SELECT CAST(b.month AS DATE) AS month, b.region, b.category, coalesce(s.net_sales, 0) AS net_sales, b.budget_amount
FROM {catalog}.gold.fact_budget b
LEFT JOIN s ON CAST(s.month AS DATE) = CAST(b.month AS DATE) AND s.region = b.region AND s.category = b.category
""")
sql(f"ALTER VIEW {catalog}.gold.v_sales_budget_monthly OWNER TO `{gp}data_engineers`")

# COMMAND ----------

# MAGIC %md ## Metric Views from YAML

# COMMAND ----------

for name in ["sales_metrics", "sales_vs_budget_metrics"]:
    yaml_def = open(f"{name}.yaml").read().replace("${catalog}", catalog)
    sql(f"CREATE OR REPLACE VIEW {catalog}.semantic.{name} WITH METRICS LANGUAGE YAML AS $$\n{yaml_def}\n$$")
    sql(f"ALTER VIEW {catalog}.semantic.{name} OWNER TO `{gp}data_engineers`")

# COMMAND ----------

# MAGIC %md ## Expose only the semantic layer

# COMMAND ----------

sql(f"GRANT USE SCHEMA, SELECT ON SCHEMA {catalog}.semantic TO `{gp}analysts`")
display(spark.sql(f"SHOW GRANTS ON SCHEMA {catalog}.semantic"))

# COMMAND ----------

# MAGIC %md ## Try it

# COMMAND ----------

display(spark.sql(f"""
SELECT region, MEASURE(net_sales) AS net_sales, MEASURE(gross_margin_pct) AS margin_pct, MEASURE(region_share_pct) AS share
FROM {catalog}.semantic.sales_metrics GROUP BY region ORDER BY net_sales DESC"""))

# Window measures: filter OUTSIDE the aggregation, otherwise last year's rows are excluded before the window runs
display(spark.sql(f"""
SELECT * FROM (
  SELECT month, MEASURE(net_sales) AS net_sales, MEASURE(net_sales_ly) AS net_sales_ly,
         MEASURE(net_sales_yoy_pct) AS yoy, MEASURE(net_sales_ytd) AS ytd, MEASURE(active_customers_90d) AS active_90d
  FROM {catalog}.semantic.sales_metrics GROUP BY month)
WHERE month >= '2026-01-01' ORDER BY month"""))
