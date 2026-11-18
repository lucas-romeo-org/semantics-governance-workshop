# Databricks notebook source
# MAGIC %md
# MAGIC # Step 2 · Verify
# MAGIC 1. Data is there, with the expected shape.
# MAGIC 2. Tags are in place.
# MAGIC 3. **Ana (a consumer) cannot read `gold`.**

# COMMAND ----------

# MAGIC %pip install -q "databricks-sdk>=0.168"
# MAGIC %restart_python

# COMMAND ----------

import os, sys
sys.path.append(os.path.abspath("../common"))
from personas import client, run_sql

for k, d in [("catalog", "sgw_shop"), ("tag_prefix", "sgw_"), ("secret_scope", "sgw"), ("warehouse_id", "")]:
    dbutils.widgets.text(k, d)
catalog, tp, scope, wh = (dbutils.widgets.get(k) for k in ("catalog", "tag_prefix", "secret_scope", "warehouse_id"))
checks = []

def check(name, ok, detail=""):
    checks.append((name, ok, detail))
    print(("✅" if ok else "❌"), name, detail)

# COMMAND ----------

counts = {r.t: r.n for r in spark.sql(f"""
  SELECT 'fact_sales' t, count(*) n FROM {catalog}.gold.fact_sales UNION ALL
  SELECT 'dim_customer', count(*) FROM {catalog}.gold.dim_customer UNION ALL
  SELECT 'dim_store', count(*) FROM {catalog}.gold.dim_store UNION ALL
  SELECT 'fact_budget', count(*) FROM {catalog}.gold.fact_budget""").collect()}
check("fact_sales has rows", counts["fact_sales"] > 1_000_000, f"{counts['fact_sales']:,}")
check("40 stores", counts["dim_store"] == 40)
check("20,000 customers", counts["dim_customer"] == 20000)
check("budget rows", counts["fact_budget"] > 0, f"{counts['fact_budget']:,}")

regions = {r.store_region for r in spark.sql(f"SELECT DISTINCT store_region FROM {catalog}.gold.fact_sales").collect()}
check("4 regions in sales", regions == {"ES", "PT", "FR", "IT"}, str(sorted(regions)))

tags = spark.sql(f"""SELECT count(*) n FROM {catalog}.information_schema.column_tags
                     WHERE schema_name='gold' AND tag_name IN ('{tp}pii','{tp}region_scope')""").first().n
check("8 governed column tags", tags == 8, str(tags))

# COMMAND ----------

ana = client("ana", scope, dbutils)
rows, err = run_sql(ana, wh, f"SELECT count(*) FROM {catalog}.gold.fact_sales")
check("Ana is denied on gold", err is not None and ("PERMISSION" in err.upper() or "INSUFFICIENT" in err.upper() or "USE SCHEMA" in err.upper()),
      (err or "query succeeded!")[:120])

# COMMAND ----------

failed = [c for c in checks if not c[1]]
assert not failed, f"{len(failed)} check(s) failed: {[c[0] for c in failed]}"
print(f"All {len(checks)} checks passed.")
