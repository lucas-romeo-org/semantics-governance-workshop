# Databricks notebook source
# MAGIC %md
# MAGIC # Step 3 · Row and column security, once, with ABAC
# MAGIC Two functions and two policies, attached to the **whole `gold` schema**.
# MAGIC The policies target **tags**, not tables. Any table that is (or will be) tagged is protected automatically.
# MAGIC
# MAGIC | Policy | Targets | Effect |
# MAGIC |---|---|---|
# MAGIC | `region_rls` | columns tagged `sgw_region_scope` | ES analysts see ES, PT analysts see PT, leads and builders see all |
# MAGIC | `pii_mask` | columns tagged `sgw_pii` | Masked for everyone except `wk_pii_readers` |
# MAGIC
# MAGIC Policies are evaluated with the identity of **whoever queries**, also when the query arrives through a view.

# COMMAND ----------

dbutils.widgets.text("catalog", "sgw_shop")
dbutils.widgets.text("group_prefix", "wk_")
dbutils.widgets.text("tag_prefix", "sgw_")
catalog, gp, tp = (dbutils.widgets.get(k) for k in ("catalog", "group_prefix", "tag_prefix"))
gov, gold = f"{catalog}.governance", f"{catalog}.gold"

def sql(s):
    print(s.strip(), "\n")
    spark.sql(s)

# COMMAND ----------

# MAGIC %md ## 1 · Security functions (owned by the security team)

# COMMAND ----------

sql(f"""
CREATE OR REPLACE FUNCTION {gov}.region_filter(region STRING)
RETURNS BOOLEAN
COMMENT 'Row filter: which sales regions the current user can see'
RETURN is_account_group_member('{gp}sales_leads')
    OR is_account_group_member('{gp}data_engineers')
    OR is_account_group_member('{gp}security_admins')
    OR (region = 'ES' AND is_account_group_member('{gp}analysts_es'))
    OR (region = 'PT' AND is_account_group_member('{gp}analysts_pt'))
""")
sql(f"""
CREATE OR REPLACE FUNCTION {gov}.mask_pii(value STRING)
RETURNS STRING
COMMENT 'Column mask for personally identifiable information'
RETURN '****'
""")
for f in ("region_filter", "mask_pii"):
    sql(f"ALTER FUNCTION {gov}.{f} OWNER TO `{gp}security_admins`")
# The security team manages access control on gold, without owning the data
sql(f"GRANT MANAGE ON SCHEMA {gold} TO `{gp}security_admins`")

# COMMAND ----------

# MAGIC %md ## 2 · ABAC policies on the gold schema

# COMMAND ----------

existing = {r[0] for r in spark.sql(f"SHOW POLICIES ON SCHEMA {gold}").collect()}
def drop_if_exists(name):  # DROP POLICY has no IF EXISTS
    if name in existing:
        sql(f"DROP POLICY {name} ON SCHEMA {gold}")

drop_if_exists("region_rls")
sql(f"""
CREATE POLICY region_rls
ON SCHEMA {gold}
COMMENT 'Rows scoped by sales region'
ROW FILTER {gov}.region_filter
TO `account users`
FOR TABLES
MATCH COLUMNS has_tag_value('{tp}region_scope', 'region') AS r
USING COLUMNS (r)
""")
drop_if_exists("pii_mask")
sql(f"""
CREATE POLICY pii_mask
ON SCHEMA {gold}
COMMENT 'PII masked unless the reader is allowed'
COLUMN MASK {gov}.mask_pii
TO `account users`
EXCEPT `{gp}pii_readers`
FOR TABLES
MATCH COLUMNS has_tag('{tp}pii') AS c
ON COLUMN c
""")

display(spark.sql(f"SHOW POLICIES ON SCHEMA {gold}"))
