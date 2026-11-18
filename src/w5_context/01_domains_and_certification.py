# Databricks notebook source
# MAGIC %md
# MAGIC # Step 5 · Business context: domains and certification
# MAGIC - A **domain** organises assets by business area in **Discover**. Domains are built on governed tags.
# MAGIC - Assets join a domain through **its tag**. Tag once, and the asset shows up in Discover.
# MAGIC - **Certification** tells people *and agents* which assets are official. Genie prioritises certified assets.
# MAGIC
# MAGIC | Domain | Assets |
# MAGIC |---|---|
# MAGIC | Retail Sales › Store Performance | `semantic.sales_metrics` ✓ certified |
# MAGIC | Retail Sales › Budget | `semantic.sales_vs_budget_metrics` ✓ certified |
# MAGIC | — | `semantic.v_sales_es_legacy` ⚠ deprecated |

# COMMAND ----------

# MAGIC %pip install -q "databricks-sdk>=0.168"
# MAGIC %restart_python

# COMMAND ----------

dbutils.widgets.text("catalog", "sgw_shop")
dbutils.widgets.text("group_prefix", "wk_")
dbutils.widgets.text("domain", "Retail Sales")
catalog, gp, root = (dbutils.widgets.get(k) for k in ("catalog", "group_prefix", "domain"))

from databricks.sdk import WorkspaceClient
from databricks.sdk.service import domains as D
from databricks.sdk.service.tags import TagPolicy

w = WorkspaceClient()
idp = w.workspace_iam_v2
gid = lambda n: int(next(x for x in idp.list_groups_proxy(filter=f'group_name eq "{n}"') if x.group_name == n).group_id)
business, technical = gid(f"{gp}sales_domain_owners"), gid(f"{gp}data_engineers")

# COMMAND ----------

# MAGIC %md ## Domain and subdomains (published, with business and technical owners)

# COMMAND ----------

spec = [
    (root, None, "Retail sales KPIs, budget and the business glossary", D.DomainIconName.BASKET),
    (f"{root}/Store Performance", root, "Certified sales, margin and customer KPIs", D.DomainIconName.CHART_PIE_SLICE),
    (f"{root}/Budget", root, "Budget and attainment KPIs", D.DomainIconName.BANK),
]
tags = {t.tag_key for t in w.tag_policies.list_tag_policies()}
doms = {d.tag_key: d for d in w.domains.list_domains(page_size=500)}
for key, parent, sub, icon in spec:
    if key not in tags:  # a domain is backed by a governed tag with the same name
        w.tag_policies.create_tag_policy(TagPolicy(tag_key=key, description=f"Discover business domain: {key}"))
    if key in doms:
        print(f"= domain {key}")
        continue
    doms[key] = w.domains.create_domain(D.Domain(
        tag_key=key, subtitle=sub, description=sub, draft=False, icon=D.DomainIcon(name=icon),
        business_owner_ids=[business], technical_owner_ids=[technical],
        parent_domain_id=doms[parent].domain_id if parent else None))
    print(f"+ domain {key}")

# COMMAND ----------

# MAGIC %md ## Put assets in their domain, certify the official ones, deprecate the legacy view

# COMMAND ----------

def sql(s):
    print(s)
    spark.sql(s)

s = f"{catalog}.semantic"
sql(f"ALTER VIEW {s}.sales_metrics SET TAGS ('{root}/Store Performance')")
sql(f"ALTER VIEW {s}.sales_vs_budget_metrics SET TAGS ('{root}/Budget')")
for mv in ("sales_metrics", "sales_vs_budget_metrics"):
    sql(f"ALTER VIEW {s}.{mv} SET TAGS ('system.certification_status' = 'certified')")
sql(f"ALTER VIEW {s}.v_sales_es_legacy SET TAGS ('system.certification_status' = 'deprecated')")

display(spark.sql(f"""SELECT table_name, tag_name, tag_value FROM {catalog}.information_schema.table_tags
                      WHERE schema_name = 'semantic' ORDER BY ALL"""))
