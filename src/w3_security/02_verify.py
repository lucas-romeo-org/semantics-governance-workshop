# Databricks notebook source
# MAGIC %md
# MAGIC # Step 3 · Verify: same query, three results
# MAGIC For this test only, analysts get `SELECT` on `gold` (revoked at the end).
# MAGIC In the final design they never touch `gold`: they read the semantic layer (step 4).

# COMMAND ----------

# MAGIC %pip install -q "databricks-sdk>=0.168"
# MAGIC %restart_python

# COMMAND ----------

import os, sys
sys.path.append(os.path.abspath("../common"))
from personas import client, run_sql

for k, d in [("catalog", "sgw_shop"), ("group_prefix", "wk_"), ("tag_prefix", "sgw_"), ("secret_scope", "sgw"), ("warehouse_id", "")]:
    dbutils.widgets.text(k, d)
catalog, gp, tp, scope, wh = (dbutils.widgets.get(k) for k in ("catalog", "group_prefix", "tag_prefix", "secret_scope", "warehouse_id"))
gold = f"{catalog}.gold"
checks = []

def check(name, ok, detail=""):
    checks.append((name, ok, detail))
    print(("✅" if ok else "❌"), name, detail)

# COMMAND ----------

spark.sql(f"GRANT USE SCHEMA, SELECT ON SCHEMA {gold} TO `{gp}analysts`")  # temporary, test only
try:
    regions_q = f"SELECT store_region, count(*) FROM {gold}.fact_sales GROUP BY 1 ORDER BY 1"
    pii_q = f"SELECT customer_id, country, email FROM {gold}.dim_customer ORDER BY customer_id LIMIT 3"
    expected = {"ana": ({"ES"}, False), "pedro": ({"PT"}, False), "marta": ({"ES", "PT", "FR", "IT"}, True)}
    for p, (exp_regions, pii_clear) in expected.items():
        c = client(p, scope, dbutils)
        rows, err = run_sql(c, wh, regions_q)
        got = {r[0] for r in rows or []}
        check(f"{p}: regions", err is None and got == exp_regions, err or str(sorted(got)))
        rows, err = run_sql(c, wh, pii_q)
        emails = [r[2] for r in rows or []]
        clear = bool(emails) and all("@" in (e or "") for e in emails)
        check(f"{p}: PII {'clear' if pii_clear else 'masked'}", err is None and clear == pii_clear, err or str(emails))

    # Governance by tagging: a NEW table, tagged once, is protected with no extra policy work
    spark.sql(f"CREATE OR REPLACE TABLE {gold}.tag_demo AS SELECT * FROM VALUES ('ES', 1), ('PT', 2), ('FR', 3) AS t(region, v)")
    spark.sql(f"ALTER TABLE {gold}.tag_demo ALTER COLUMN region SET TAGS ('{tp}region_scope' = 'region')")
    rows, err = run_sql(client("ana", scope, dbutils), wh, f"SELECT region FROM {gold}.tag_demo")
    check("new tagged table is filtered for Ana", err is None and {r[0] for r in rows} == {"ES"}, err or str(rows))
finally:
    spark.sql(f"DROP TABLE IF EXISTS {gold}.tag_demo")
    spark.sql(f"REVOKE USE SCHEMA, SELECT ON SCHEMA {gold} FROM `{gp}analysts`")
    print("temporary grant revoked")

# COMMAND ----------

failed = [c for c in checks if not c[1]]
assert not failed, f"{len(failed)} check(s) failed: {[c[0] for c in failed]}"
print(f"All {len(checks)} checks passed.")
