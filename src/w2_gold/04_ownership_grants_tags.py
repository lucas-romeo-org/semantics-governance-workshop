# Databricks notebook source
# MAGIC %md
# MAGIC # Step 2 · Physical governance of Gold — 4. Ownership, grants and tags
# MAGIC - **Ownership belongs to groups, never to people.**
# MAGIC - **Segregation of duties**: whoever builds is not whoever secures, certifies or consumes.
# MAGIC - Consumers only get `USE CATALOG`. They have **no access to `gold`**. In step 4 they get the semantic schema.
# MAGIC - **Classify once**: tags on columns. Step 3 protects every tagged column automatically.

# COMMAND ----------

dbutils.widgets.text("catalog", "sgw_shop")
dbutils.widgets.text("group_prefix", "wk_")
dbutils.widgets.text("tag_prefix", "sgw_")
catalog, gp, tp = (dbutils.widgets.get(k) for k in ("catalog", "group_prefix", "tag_prefix"))

def sql(s):
    print(s)
    spark.sql(s)

# COMMAND ----------

# MAGIC %md ## Ownership and grants

# COMMAND ----------

owners = {"gold": "data_engineers", "semantic": "data_engineers", "knowledge": "sales_domain_owners",
          "governance": "security_admins", "ops": "platform_admins"}
for grp in ["data_engineers", "security_admins", "sales_domain_owners", "platform_admins", "analysts"]:
    sql(f"GRANT USE CATALOG ON CATALOG {catalog} TO `{gp}{grp}`")
for schema, grp in owners.items():
    sql(f"ALTER SCHEMA {catalog}.{schema} OWNER TO `{gp}{grp}`")
for t in [r.tableName for r in spark.sql(f"SHOW TABLES IN {catalog}.gold").collect()]:
    sql(f"ALTER TABLE {catalog}.gold.{t} OWNER TO `{gp}data_engineers`")
sql(f"ALTER VIEW {catalog}.semantic.v_sales_es_legacy OWNER TO `{gp}data_engineers`")
# Security admins need to read gold to test policies; they never own data.
sql(f"GRANT USE SCHEMA, SELECT ON SCHEMA {catalog}.gold TO `{gp}security_admins`")
sql(f"ALTER CATALOG {catalog} OWNER TO `{gp}platform_admins`")

# COMMAND ----------

# MAGIC %md ## Classification with governed tags

# COMMAND ----------

g = f"{catalog}.gold"
column_tags = [
    ("dim_customer", "full_name", f"{tp}pii", "name"),
    ("dim_customer", "email", f"{tp}pii", "email"),
    ("dim_customer", "phone", f"{tp}pii", "phone"),
    ("dim_customer", "tax_id", f"{tp}pii", "tax_id"),
    ("dim_customer", "country", f"{tp}region_scope", "region"),
    ("fact_sales", "store_region", f"{tp}region_scope", "region"),
    ("dim_store", "region", f"{tp}region_scope", "region"),
    ("fact_budget", "region", f"{tp}region_scope", "region"),
]
for t, c, k, v in column_tags:
    sql(f"ALTER TABLE {g}.{t} ALTER COLUMN {c} SET TAGS ('{k}' = '{v}')")
for t, v in [("dim_customer", "confidential"), ("fact_sales", "internal"), ("fact_budget", "internal"),
             ("dim_store", "internal"), ("dim_product", "internal"), ("dim_date", "public")]:
    sql(f"ALTER TABLE {g}.{t} SET TAGS ('{tp}sensitivity' = '{v}')")

display(spark.sql(f"""SELECT table_name, column_name, tag_name, tag_value
                      FROM {catalog}.information_schema.column_tags
                      WHERE schema_name = 'gold' ORDER BY ALL"""))
