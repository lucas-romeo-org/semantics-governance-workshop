# Databricks notebook source
# MAGIC %md
# MAGIC # Step 5 · Business context: Pages (the governed glossary)
# MAGIC Pages hold the **exact** business definitions: definition, formula, rules, synonyms and owner.
# MAGIC They are the authoritative source for people and for Genie One.
# MAGIC
# MAGIC **Glossary as code:** each Page is a Markdown file in `pages/`, reviewed in Git and published through the Pages API.
# MAGIC Re-running this notebook updates the Pages in place.

# COMMAND ----------

# MAGIC %pip install -q "databricks-sdk>=0.168"
# MAGIC %restart_python

# COMMAND ----------

import glob, os, re
from databricks.sdk import WorkspaceClient

dbutils.widgets.text("catalog", "sgw_shop")
dbutils.widgets.text("domain", "Retail Sales")
catalog, root = dbutils.widgets.get("catalog"), dbutils.widgets.get("domain")
w = WorkspaceClient()
doms = {d.tag_key: d for d in w.domains.list_domains(page_size=500)}

def parse(path):
    """Tiny front-matter parser: key: value and key: [a, b]."""
    raw = open(path).read()
    _, fm, body = raw.split("---", 2)
    meta = {}
    for line in fm.strip().splitlines():
        k, v = line.split(":", 1)
        v = v.strip()
        meta[k.strip()] = [x.strip() for x in v.strip("[]").split(",")] if v.startswith("[") else v
    return meta, body.strip().replace("${catalog}", catalog)

def list_pages():
    out, token = [], None
    while True:
        r = w.api_client.do("GET", "/api/2.0/knowledge/pages", query={"page_size": 100, **({"page_token": token} if token else {})})
        out += r.get("pages", [])
        token = r.get("next_page_token")
        if not token:
            return out

# COMMAND ----------

existing = {(p.get("domain"), p.get("display_name")): p for p in list_pages()}
for path in sorted(glob.glob("pages/*.md")):
    meta, body = parse(path)
    domain = doms[meta["domain"].replace("Retail Sales", root, 1)].name
    page = {"domain": domain, "display_name": meta["title"], "description": meta["description"],
            "synonyms": meta["synonyms"], "body": body, "state": "PUBLISHED"}
    current = existing.get((domain, meta["title"]))
    if current:
        w.api_client.do("PATCH", f"/api/2.0/knowledge/{current['name']}",
                        query={"update_mask": "description,synonyms,body,state"}, body=page)
        print(f"~ updated  {meta['title']}  ({meta['domain']})")
    else:
        w.api_client.do("POST", "/api/2.0/knowledge/pages", body=page)
        print(f"+ published {meta['title']}  ({meta['domain']})")
