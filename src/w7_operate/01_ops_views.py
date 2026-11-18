# Databricks notebook source
# MAGIC %md
# MAGIC # Step 8 · Operate: audit, lineage and cost from system tables
# MAGIC Governance you can't observe is a statement, not a control. These views answer four questions:
# MAGIC
# MAGIC | View | Question |
# MAGIC |---|---|
# MAGIC | `ops.semantic_activity` | **Who** queried **what**, from **which tool**, and did it succeed? |
# MAGIC | `ops.blocked_attempts` | Who tried to go around the semantic layer, and was blocked? |
# MAGIC | `ops.lineage` | What depends on what (Gold → Metric Views → dashboards and agents)? |
# MAGIC | `ops.workshop_cost` | What does it cost? |
# MAGIC
# MAGIC The views read system tables with their **owner's** rights (`wk_platform_admins`). Readers only need `SELECT` on `ops`.

# COMMAND ----------

# MAGIC %pip install -q "databricks-sdk>=0.168"
# MAGIC %restart_python

# COMMAND ----------

for k, d in [("catalog", "sgw_shop"), ("group_prefix", "wk_"), ("warehouse_id", "")]:
    dbutils.widgets.text(k, d)
catalog, gp, wh = (dbutils.widgets.get(k) for k in ("catalog", "group_prefix", "warehouse_id"))
ops = f"{catalog}.ops"

def sql(s):
    print(s.strip()[:300], "\n")
    spark.sql(s)

# COMMAND ----------

# MAGIC %md ## Principal directory: turn service principal ids into readable names

# COMMAND ----------

from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
rows = [(sp.application_id, sp.display_name, "service principal") for sp in w.service_principals.list(filter='displayName sw "sgw-"')]
me = w.current_user.me()
rows.append((me.user_name, me.display_name or me.user_name, "user"))
spark.createDataFrame(rows, "principal_id STRING, display_name STRING, kind STRING").write.mode("overwrite").saveAsTable(f"{ops}.principals")
display(spark.table(f"{ops}.principals"))

# COMMAND ----------

# MAGIC %md ## Views

# COMMAND ----------

sql(f"""
CREATE OR REPLACE VIEW {ops}.semantic_activity
COMMENT 'Every query on the workshop catalog (last 30 days): who, from which tool, which layer, result' AS
WITH q AS (
  SELECT start_time, executed_by, client_application, execution_status, error_message,
         lower(replace(statement_text, '`', '')) AS stmt, total_duration_ms
  FROM system.query.history
  WHERE start_time >= current_timestamp() - INTERVAL 30 DAYS
    AND lower(replace(statement_text, '`', '')) LIKE '%{catalog}.%'
    AND statement_type IN ('SELECT', 'OTHER'))
SELECT q.start_time,
       coalesce(p.display_name, q.executed_by) AS principal,
       CASE WHEN q.client_application ILIKE '%genie%' THEN 'Genie'
            WHEN q.client_application ILIKE '%dashboard%' OR q.client_application ILIKE '%lakeview%' THEN 'AI/BI Dashboard'
            WHEN q.client_application ILIKE '%app%' THEN 'Databricks App'
            WHEN q.client_application ILIKE '%mcp%' OR q.client_application ILIKE '%gateway%' THEN 'MCP'
            WHEN q.client_application ILIKE '%CLI%' THEN 'CLI'
            WHEN q.client_application = 'unknown' THEN 'SQL API'
            ELSE coalesce(q.client_application, 'Other') END AS surface,
       CASE WHEN q.stmt LIKE '%{catalog}.semantic.%' THEN 'semantic'
            WHEN q.stmt LIKE '%{catalog}.gold.%' THEN 'gold'
            ELSE 'other' END AS layer,
       coalesce(nullif(regexp_extract(q.stmt, '{catalog}\\\\.semantic\\\\.([a-z_]+)', 1), ''),
                nullif(regexp_extract(q.stmt, '{catalog}\\\\.gold\\\\.([a-z_]+)', 1), '')) AS object,
       q.execution_status AS status,
       regexp_extract(q.error_message, '\\\\[([A-Z_]+)\\\\]', 1) AS error_class,
       q.total_duration_ms
FROM q LEFT JOIN {ops}.principals p ON p.principal_id = q.executed_by
""")

sql(f"""
CREATE OR REPLACE VIEW {ops}.blocked_attempts
COMMENT 'Queries rejected by Unity Catalog permissions (e.g. a consumer trying to read gold)' AS
SELECT start_time, principal, surface, layer, object, error_class
FROM {ops}.semantic_activity
WHERE status = 'FAILED' AND error_class IN ('INSUFFICIENT_PERMISSIONS', 'PERMISSION_DENIED')
""")

sql(f"""
CREATE OR REPLACE VIEW {ops}.lineage
COMMENT 'Table-level lineage edges inside the workshop catalog' AS
SELECT source_table_full_name AS source,
       coalesce(nullif(target_table_full_name, ''), concat('→ consumer (', coalesce(nullif(entity_type, ''), 'query'), ')')) AS target,
       count(*) AS events, max(event_time) AS last_seen
FROM system.access.table_lineage
WHERE event_time >= current_timestamp() - INTERVAL 30 DAYS
  AND source_table_full_name LIKE '{catalog}.%'
  AND (target_table_full_name LIKE '{catalog}.%' OR coalesce(target_table_full_name, '') = '')
GROUP BY ALL
""")

sql(f"""
CREATE OR REPLACE VIEW {ops}.workshop_cost
COMMENT 'DBUs consumed by the workshop warehouse and jobs, per day and SKU' AS
SELECT u.usage_date, u.sku_name,
       CASE WHEN u.usage_metadata.warehouse_id IS NOT NULL THEN 'SQL warehouse' ELSE 'Jobs / notebooks' END AS workload,
       sum(u.usage_quantity) AS dbus
FROM system.billing.usage u
WHERE u.usage_date >= current_date() - 30
  AND (u.usage_metadata.warehouse_id = '{wh}' OR u.custom_tags['project'] = 'semantics-governance-workshop')
GROUP BY ALL
""")

for t in ("principals", "semantic_activity", "blocked_attempts", "lineage", "workshop_cost"):
    sql(f"ALTER {'TABLE' if t == 'principals' else 'VIEW'} {ops}.{t} OWNER TO `{gp}platform_admins`")
sql(f"GRANT USE SCHEMA, SELECT ON SCHEMA {ops} TO `{gp}security_admins`")

# COMMAND ----------

display(spark.sql(f"SELECT surface, principal, layer, status, count(*) n FROM {ops}.semantic_activity GROUP BY ALL ORDER BY n DESC"))
