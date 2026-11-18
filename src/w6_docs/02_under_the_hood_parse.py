# Databricks notebook source
# MAGIC %md
# MAGIC # Step 6 · Under the hood (optional): what the Genie Agent does with a document
# MAGIC When a volume is attached to a Genie Agent, *content search* parses every file with `ai_parse_document` and indexes it.
# MAGIC This cell runs the same function on one PDF, so you can see the structured output.

# COMMAND ----------

dbutils.widgets.text("catalog", "sgw_shop")
catalog = dbutils.widgets.get("catalog")

display(spark.sql(f"""
SELECT path,
       ai_parse_document(content):document:elements[1]:content AS first_section_text,
       size(ai_parse_document(content):document:elements::ARRAY<STRING>) AS elements
FROM read_files('/Volumes/{catalog}/knowledge/docs/Discount_Policy.pdf', format => 'binaryFile')
"""))
