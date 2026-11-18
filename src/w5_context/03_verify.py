# Databricks notebook source
# MAGIC %md
# MAGIC # Step 5 · Verify
# MAGIC The domain is published, assets are in it, official assets are certified, the legacy view is deprecated,
# MAGIC the glossary is published, and **a consumer (Ana) can see the certification** of what she is allowed to read.

# COMMAND ----------

# MAGIC %pip install -q "databricks-sdk>=0.168"
# MAGIC %restart_python

# COMMAND ----------

import os, sys
sys.path.append(os.path.abspath("../common"))
from personas import client, run_sql
from databricks.sdk import WorkspaceClient

for k, d in [("catalog", "sgw_shop"), ("domain", "Retail Sales"), ("secret_scope", "sgw"), ("warehouse_id", "")]:
    dbutils.widgets.text(k, d)
catalog, root, scope, wh = (dbutils.widgets.get(k) for k in ("catalog", "domain", "secret_scope", "warehouse_id"))
w = WorkspaceClient()
checks = []

def check(name, ok, detail=""):
    checks.append((name, ok, detail))
    print(("✅" if ok else "❌"), name, detail)

# COMMAND ----------

doms = {d.tag_key: d for d in w.domains.list_domains(page_size=500)}
for key in (root, f"{root}/Store Performance", f"{root}/Budget"):
    d = doms.get(key)
    check(f"domain '{key}' published", d is not None and not d.effective_draft)

tags = {(r.table_name, r.tag_name): r.tag_value for r in spark.sql(
    f"SELECT table_name, tag_name, tag_value FROM {catalog}.information_schema.table_tags WHERE schema_name='semantic'").collect()}
check("sales_metrics certified + in Store Performance",
      tags.get(("sales_metrics", "system.certification_status")) == "certified" and ("sales_metrics", f"{root}/Store Performance") in tags)
check("sales_vs_budget_metrics certified + in Budget",
      tags.get(("sales_vs_budget_metrics", "system.certification_status")) == "certified" and ("sales_vs_budget_metrics", f"{root}/Budget") in tags)
check("legacy view deprecated", tags.get(("v_sales_es_legacy", "system.certification_status")) == "deprecated")

ids = {doms[k].name for k in doms if k == root or k.startswith(root + "/")}
def list_pages():  # shared accounts can have hundreds of Pages: paginate
    out, token = [], None
    while True:
        r = w.api_client.do("GET", "/api/2.0/knowledge/pages", query={"page_size": 100, **({"page_token": token} if token else {})})
        out += r.get("pages", [])
        token = r.get("next_page_token")
        if not token:
            return out
pages = [p for p in list_pages() if p.get("domain") in ids]
published = sorted(p["display_name"] for p in pages if p.get("state") == "PUBLISHED")
check("5 glossary Pages published", len(published) >= 5, str(published))

rows, err = run_sql(client("ana", scope, dbutils), wh, f"""SELECT table_name, tag_value FROM {catalog}.information_schema.table_tags
                                                          WHERE tag_name = 'system.certification_status' ORDER BY 1""")
check("Ana sees certification status of what she can read", err is None and ["sales_metrics", "certified"] in rows, err or str(rows))

# COMMAND ----------

failed = [c for c in checks if not c[1]]
assert not failed, f"{len(failed)} check(s) failed: {[c[0] for c in failed]}"
print(f"All {len(checks)} checks passed.")
