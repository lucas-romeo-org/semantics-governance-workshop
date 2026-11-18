# Databricks notebook source
# MAGIC %md
# MAGIC # Step 2 · Physical governance of Gold — 1. Catalog and schemas
# MAGIC One catalog, **segregated by purpose**: physical data (`gold`), the semantic contract (`semantic`),
# MAGIC security functions (`governance`) and observability (`ops`).
# MAGIC
# MAGIC > If the metastore uses **Default Storage**, create the catalog once in Catalog Explorer
# MAGIC > (*Create catalog → Use default storage*). This notebook then reuses it.

# COMMAND ----------

dbutils.widgets.text("catalog", "sgw_shop")
catalog = dbutils.widgets.get("catalog")

# COMMAND ----------

exists = spark.sql(f"SHOW CATALOGS LIKE '{catalog}'").count() > 0
try:
    if not exists:  # CREATE ... IF NOT EXISTS still validates storage, so check first
        spark.sql(f"CREATE CATALOG {catalog} COMMENT 'Semantic Governance Workshop'")
    print(f"catalog {catalog}: {'reused' if exists else 'created'}")
except Exception as e:
    if "DEFAULT_STORAGE" in str(e):
        raise RuntimeError(f"Create catalog '{catalog}' in Catalog Explorer with 'Use default storage', then re-run.") from e
    raise

schemas = {
    "gold": "Physical Gold tables. Closed to consumers.",
    "semantic": "Semantic contract: Metric Views. The only schema consumers can read.",
    "governance": "Security functions used by ABAC policies.",
    "ops": "Observability views over system tables.",
}
for s, c in schemas.items():
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{s} COMMENT '{c}'")

# Keep the structure clean: drop the auto-created empty 'default' schema
if spark.sql(f"SHOW SCHEMAS IN {catalog} LIKE 'default'").count() > 0 and spark.sql(f"SHOW TABLES IN {catalog}.default").count() == 0:
    spark.sql(f"DROP SCHEMA IF EXISTS {catalog}.default")

display(spark.sql(f"SHOW SCHEMAS IN {catalog}"))
