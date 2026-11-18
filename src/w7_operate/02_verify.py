# Databricks notebook source
# MAGIC %md
# MAGIC # Step 8 · Verify: everything is auditable

# COMMAND ----------

dbutils.widgets.text("catalog", "sgw_shop")
ops = f"{dbutils.widgets.get('catalog')}.ops"
checks = []

def check(name, ok, detail=""):
    checks.append((name, ok, detail))
    print(("✅" if ok else "❌"), name, detail)

act = spark.table(f"{ops}.semantic_activity")
who = {r.principal for r in act.where("layer = 'semantic' AND status = 'FINISHED'").select("principal").distinct().collect()}
for p in ("sgw-persona-ana", "sgw-persona-pedro", "sgw-persona-marta"):
    check(f"{p} queries on the semantic layer are attributed to them", p in who)

surfaces = {r.surface for r in act.select("surface").distinct().collect()}
check("activity captured from several surfaces (incl. Genie)", "Genie" in surfaces and len(surfaces) >= 2, str(sorted(surfaces)))

blocked = spark.table(f"{ops}.blocked_attempts").where("principal = 'sgw-persona-ana' AND layer = 'gold'").count()
check("Ana's attempts to read gold are recorded as blocked", blocked > 0, f"{blocked} attempts")

edges = {(r.source, r.target) for r in spark.table(f"{ops}.lineage").collect()}
cat = dbutils.widgets.get("catalog")
check("lineage gold.fact_sales → semantic.sales_metrics", (f"{cat}.gold.fact_sales", f"{cat}.semantic.sales_metrics") in edges)

dbus = spark.sql(f"SELECT coalesce(sum(dbus), 0) d FROM {ops}.workshop_cost").first().d
check("workshop cost is measured", float(dbus) > 0, f"{float(dbus):.2f} DBUs (30 days)")

failed = [c for c in checks if not c[1]]
assert not failed, f"{len(failed)} check(s) failed: {[c[0] for c in failed]}"
print(f"All {len(checks)} checks passed.")
