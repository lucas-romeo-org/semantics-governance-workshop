# Databricks notebook source
# MAGIC %md
# MAGIC # Step 6 · Verify: internal consumption inherits everything
# MAGIC - The dashboard runs with the **viewer's** credentials (no embedded identity).
# MAGIC - The Genie Agent answers each persona with **their own** permissions: same question, different rows,
# MAGIC   always through the certified Metric Views and never through `gold`.

# COMMAND ----------

# MAGIC %pip install -q "databricks-sdk>=0.168"
# MAGIC %restart_python

# COMMAND ----------

import os, sys
sys.path.append(os.path.abspath("../common"))
from personas import client
from databricks.sdk import WorkspaceClient

for k, d in [("secret_scope", "sgw"), ("space_id", ""), ("dashboard_id", "")]:
    dbutils.widgets.text(k, d)
scope, space_id, dashboard_id = (dbutils.widgets.get(k) for k in ("secret_scope", "space_id", "dashboard_id"))
checks = []

def check(name, ok, detail=""):
    checks.append((name, ok, detail))
    print(("✅" if ok else "❌"), name, detail)

# COMMAND ----------

pub = WorkspaceClient().lakeview.get_published(dashboard_id)
check("dashboard published with viewer credentials", pub.embed_credentials is False, f"embed_credentials={pub.embed_credentials}")

# COMMAND ----------

def ask(persona, question):
    c = client(persona, scope, dbutils)
    m = c.genie.start_conversation_and_wait(space_id, question)
    sql, rows = None, []
    for a in m.attachments or []:
        if a.query:
            sql = a.query.query
            r = c.genie.get_message_attachment_query_result(space_id, m.conversation_id, m.id, a.attachment_id)
            rows = r.statement_response.result.data_array or []
    return m.status.value, sql or "", rows

q = "What were net sales by region in 2026-Q3?"
for persona, expected in [("ana", {"ES"}), ("pedro", {"PT"}), ("marta", {"ES", "PT", "FR", "IT"})]:
    status, sql, rows = ask(persona, q)
    regions = {r[0] for r in rows}
    check(f"{persona}: Genie answers with {sorted(expected)} only", status == "COMPLETED" and regions == expected, f"{status} {sorted(regions)}")
    check(f"{persona}: Genie used the certified Metric View, not gold",
          "semantic" in sql and "MEASURE(" in sql.upper() and ".gold." not in sql, sql.replace("\n", " ")[:110])

status, sql, rows = ask("ana", "Who are the top 5 customers by net sales in 2026?")
names = [x for r in rows for x in r if isinstance(x, str) and not x.replace(".", "").isdigit()]
check("ana: customer names masked in Genie answers", status == "COMPLETED" and names and all(n == "****" for n in names), str(rows[:5]))

# COMMAND ----------

failed = [c for c in checks if not c[1]]
assert not failed, f"{len(failed)} check(s) failed: {[c[0] for c in failed]}"
print(f"All {len(checks)} checks passed.")
