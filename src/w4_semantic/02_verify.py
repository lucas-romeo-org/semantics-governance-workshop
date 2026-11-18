# Databricks notebook source
# MAGIC %md
# MAGIC # Step 4 · Verify: the core claim of the workshop
# MAGIC Ana, Pedro and Marta have **no privilege on `gold`**. Querying the Metric View, each one gets
# MAGIC **the same KPI definition, filtered by their own policies**.

# COMMAND ----------

# MAGIC %pip install -q "databricks-sdk>=0.168"
# MAGIC %restart_python

# COMMAND ----------

import os, sys
sys.path.append(os.path.abspath("../common"))
from personas import client, run_sql

for k, d in [("catalog", "sgw_shop"), ("secret_scope", "sgw"), ("warehouse_id", "")]:
    dbutils.widgets.text(k, d)
catalog, scope, wh = (dbutils.widgets.get(k) for k in ("catalog", "secret_scope", "warehouse_id"))
mv = f"{catalog}.semantic.sales_metrics"
checks = []

def check(name, ok, detail=""):
    checks.append((name, ok, detail))
    print(("✅" if ok else "❌"), name, detail)

# Baseline computed by a builder (sees every row) directly on gold
baseline = {r.store_region: round(float(r.ns), 2) for r in spark.sql(
    f"SELECT store_region, sum(gross_amount - discount) ns FROM {catalog}.gold.fact_sales GROUP BY 1").collect()}
print("baseline", baseline)

# COMMAND ----------

expected = {"ana": {"ES"}, "pedro": {"PT"}, "marta": {"ES", "PT", "FR", "IT"}}
for p, regions in expected.items():
    c = client(p, scope, dbutils)
    _, err = run_sql(c, wh, f"SELECT count(*) FROM {catalog}.gold.fact_sales")
    check(f"{p}: no access to gold", err is not None, (err or "query succeeded!")[:80])

    rows, err = run_sql(c, wh, f"SELECT region, MEASURE(net_sales) FROM {mv} GROUP BY region")
    got = {r[0]: round(float(r[1]), 2) for r in rows or []}
    check(f"{p}: sees only {sorted(regions)} through the Metric View", err is None and set(got) == regions, err or str(sorted(got)))
    check(f"{p}: same numbers as the governed baseline", err is None and all(abs(got[r] - baseline[r]) < 0.05 for r in got), str(got))

    rows, err = run_sql(c, wh, f"""SELECT customer_id, customer_name, MEASURE(net_sales) ns FROM {mv}
                                   GROUP BY customer_id, customer_name ORDER BY ns DESC LIMIT 5""")
    names = [r[1] for r in rows or []]
    masked = bool(names) and all(n == "****" for n in names)
    check(f"{p}: top-5 customer names {'visible' if p == 'marta' else 'masked'}", err is None and masked == (p != "marta"), err or str(names))

# COMMAND ----------

ana = client("ana", scope, dbutils)
rows, err = run_sql(ana, wh, f"""SELECT * FROM (SELECT month, MEASURE(net_sales_yoy_pct) yoy FROM {mv} GROUP BY month)
                                 WHERE month >= '2026-01-01' ORDER BY month""")
check("window measure (YoY) works for Ana", err is None and len(rows) == 10 and all(r[1] is not None for r in rows), err or f"{len(rows)} months")
rows, err = run_sql(ana, wh, f"SELECT MEASURE(region_share_pct) FROM {mv}")
check("share of total is relative to what Ana can see (100%)", err is None and abs(float(rows[0][0]) - 1) < 1e-6, err or str(rows))
rows, err = run_sql(ana, wh, f"""SELECT region, MEASURE(budget_attainment_pct) FROM {catalog}.semantic.sales_vs_budget_metrics
                                 WHERE year = 2026 GROUP BY region""")
check("budget metrics: Ana sees ES only", err is None and [r[0] for r in rows] == ["ES"], err or str(rows))

# The problem we solved: the legacy view uses a different definition of net sales
leg = spark.sql(f"SELECT sum(net_sales) v FROM {catalog}.semantic.v_sales_es_legacy WHERE year_month = '2026-09'").first().v
gov = spark.sql(f"SELECT MEASURE(net_sales) v FROM {mv} WHERE region = 'ES' AND month = '2026-09-01'").first().v
print(f"ℹ️ ES Sep-2026 net sales · legacy view: {leg:,.2f} · governed Metric View: {gov:,.2f} · difference {leg - gov:,.2f}")

# COMMAND ----------

failed = [c for c in checks if not c[1]]
assert not failed, f"{len(failed)} check(s) failed: {[c[0] for c in failed]}"
print(f"All {len(checks)} checks passed.")
