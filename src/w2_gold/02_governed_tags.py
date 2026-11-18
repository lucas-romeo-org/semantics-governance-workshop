# Databricks notebook source
# MAGIC %md
# MAGIC # Step 2 · Physical governance of Gold — 2. Governed tags
# MAGIC A **small, fixed taxonomy**. Governed tags have allowed values, and only authorised principals can assign them.
# MAGIC In step 3 the ABAC policies will target these tags, not individual tables.
# MAGIC
# MAGIC | Tag | Values | Used for |
# MAGIC |---|---|---|
# MAGIC | `sgw_pii` | name, email, phone, tax_id | Column masks |
# MAGIC | `sgw_region_scope` | region | Row filters |
# MAGIC | `sgw_sensitivity` | public, internal, confidential | Classification |

# COMMAND ----------

# MAGIC %pip install -q "databricks-sdk>=0.168"
# MAGIC %restart_python

# COMMAND ----------

dbutils.widgets.text("tag_prefix", "sgw_")
p = dbutils.widgets.get("tag_prefix")

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.tags import TagPolicy, Value

w = WorkspaceClient()
taxonomy = {
    f"{p}pii": (["name", "email", "phone", "tax_id"], "Personally identifiable information. Masked unless the reader is allowed."),
    f"{p}region_scope": (["region"], "Column that scopes rows to a sales region (ES, PT, FR, IT)."),
    f"{p}sensitivity": (["public", "internal", "confidential"], "Data classification level."),
}
existing = {t.tag_key: t for t in w.tag_policies.list_tag_policies()}
for key, (values, desc) in taxonomy.items():
    if key in existing:
        print(f"= {key} exists: {[v.name for v in (existing[key].values or [])]}")
        continue
    w.tag_policies.create_tag_policy(TagPolicy(tag_key=key, description=desc, values=[Value(name=v) for v in values]))
    print(f"+ {key} created: {values}")
