# Databricks notebook source
# MAGIC %md
# MAGIC # Step 6 · Unstructured knowledge, same governance
# MAGIC Business documents live in **Unity Catalog volumes**, with the same grants, lineage and audit as tables.
# MAGIC
# MAGIC | Volume | Documents | Who can read |
# MAGIC |---|---|---|
# MAGIC | `knowledge.docs` | KPI Handbook · Discount Policy | `wk_analysts` (everyone in sales) |
# MAGIC | `knowledge.restricted_docs` | Customer Privacy Policy | `wk_sales_leads` only |
# MAGIC
# MAGIC In step 7 both volumes are attached to the Genie Agent. It parses and indexes them, and it **always answers with the
# MAGIC permissions of the user who asks**.

# COMMAND ----------

# MAGIC %pip install -q reportlab
# MAGIC %restart_python

# COMMAND ----------

dbutils.widgets.text("catalog", "sgw_shop")
dbutils.widgets.text("group_prefix", "wk_")
catalog, gp = dbutils.widgets.get("catalog"), dbutils.widgets.get("group_prefix")
k = f"{catalog}.knowledge"

def sql(s):
    print(s)
    spark.sql(s)

readers = {"docs": f"{gp}analysts", "restricted_docs": f"{gp}sales_leads"}
for vol, grp in readers.items():
    sql(f"CREATE VOLUME IF NOT EXISTS {k}.{vol} COMMENT 'Governed business documents · readers: {grp}'")
    sql(f"ALTER VOLUME {k}.{vol} OWNER TO `{gp}sales_domain_owners`")
    sql(f"GRANT READ VOLUME ON VOLUME {k}.{vol} TO `{grp}`")
sql(f"GRANT USE SCHEMA ON SCHEMA {k} TO `{gp}analysts`")

# COMMAND ----------

# MAGIC %md ## Generate the documents (synthetic, reproducible)

# COMMAND ----------

from documents import DOCS
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

styles = getSampleStyleSheet()
for vol, files in DOCS.items():
    for fname, (title, meta, sections) in files.items():
        path = f"/Volumes/{catalog}/knowledge/{vol}/{fname}"
        story = [Paragraph(title, styles["Title"]), Paragraph(meta, styles["Italic"]), Spacer(1, 12)]
        for h, body in sections:
            story += [Paragraph(h, styles["Heading2"]), Paragraph(body, styles["BodyText"]), Spacer(1, 6)]
        SimpleDocTemplate(path, pagesize=A4).build(story)
        print("wrote", path)

display(spark.sql(f"LIST '/Volumes/{catalog}/knowledge/docs'"))
