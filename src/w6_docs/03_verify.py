# Databricks notebook source
# MAGIC %md
# MAGIC # Step 6 · Verify: documents follow the same rules as data

# COMMAND ----------

# MAGIC %pip install -q "databricks-sdk>=0.168"
# MAGIC %restart_python

# COMMAND ----------

import os, sys
sys.path.append(os.path.abspath("../common"))
from personas import client

for k_, d in [("catalog", "sgw_shop"), ("secret_scope", "sgw")]:
    dbutils.widgets.text(k_, d)
catalog, scope = dbutils.widgets.get("catalog"), dbutils.widgets.get("secret_scope")
checks = []

def check(name, ok, detail=""):
    checks.append((name, ok, detail))
    print(("✅" if ok else "❌"), name, detail)

def can_list(persona, vol):
    try:
        files = [f.name for f in client(persona, scope, dbutils).files.list_directory_contents(f"/Volumes/{catalog}/knowledge/{vol}")]
        return True, files
    except Exception as e:  # noqa: BLE001
        return False, str(e).split("\n")[0][:90]

# COMMAND ----------

for vol, n in [("docs", 2), ("restricted_docs", 1)]:
    files = [f.name for f in os.scandir(f"/Volumes/{catalog}/knowledge/{vol}") if f.name.endswith(".pdf")]
    check(f"{vol}: {n} PDF(s)", len(files) == n, str(files))

for persona, vol, allowed in [("ana", "docs", True), ("ana", "restricted_docs", False),
                              ("pedro", "docs", True), ("pedro", "restricted_docs", False),
                              ("marta", "docs", True), ("marta", "restricted_docs", True)]:
    ok, detail = can_list(persona, vol)
    check(f"{persona} {'can' if allowed else 'cannot'} read {vol}", ok == allowed, str(detail))

# COMMAND ----------

failed = [c for c in checks if not c[1]]
assert not failed, f"{len(failed)} check(s) failed: {[c[0] for c in failed]}"
print(f"All {len(checks)} checks passed.")
