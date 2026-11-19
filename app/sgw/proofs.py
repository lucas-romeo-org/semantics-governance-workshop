"""Live proofs per step. Always executed with the selected identity (never the app SP)."""
import os

CATALOG = os.environ.get("SGW_CATALOG", "sgw_shop")
WH = os.environ.get("WAREHOUSE_ID", "")


def sql(w, stmt):
    r = w.statement_execution.execute_statement(warehouse_id=WH, statement=stmt, wait_timeout="50s")
    if r.status.error:
        return {"ok": False, "error": r.status.error.message.splitlines()[0][:220]}
    cols = [c.name for c in (r.manifest.schema.columns or [])] if r.manifest and r.manifest.schema else []
    return {"ok": True, "columns": cols, "rows": (r.result.data_array or []) if r.result else []}


S = f"{CATALOG}.semantic"
GENIE_SPACE = os.environ.get("GENIE_SPACE_ID", "")


def _whoami(w):
    me = w.current_user.me()
    groups = sorted(g.display for g in (me.groups or []) if (g.display or "").startswith("wk_"))
    return {"ok": True, "columns": ["identity", "groups"], "rows": [[me.display_name or me.user_name, groups]]}


def _genie_agent(w):
    q = "What were net sales by region in 2026-Q3?"
    m = w.genie.start_conversation_and_wait(GENIE_SPACE, q)
    out = {"ok": m.status.value == "COMPLETED", "question": q, "status": m.status.value, "sql": None, "answer": None,
           "columns": [], "rows": []}
    for a in m.attachments or []:
        if a.text and a.text.content:
            out["answer"] = a.text.content
        if a.query:
            out["sql"] = a.query.query
            r = w.genie.get_message_attachment_query_result(GENIE_SPACE, m.conversation_id, m.id, a.attachment_id)
            sr = r.statement_response
            out["columns"] = [c.name for c in (sr.manifest.schema.columns or [])] if sr and sr.manifest else []
            out["rows"] = (sr.result.data_array or []) if sr and sr.result else []
    if not out["ok"]:
        out["error"] = (m.error.error if m.error else m.status.value)
    return out

PROOFS = {
    "whoami": lambda w: _whoami(w),
    "genie_agent": lambda w: _genie_agent(w),
    "activity": lambda w: sql(w, f"SELECT date_format(start_time, 'HH:mm:ss') AS at, principal, surface, layer, object, status "
                                 f"FROM {CATALOG}.ops.semantic_activity ORDER BY start_time DESC LIMIT 12"),
    "gold_access": lambda w: sql(w, f"SELECT count(*) AS lines FROM {CATALOG}.gold.fact_sales"),
    "top_customers": lambda w: sql(w, f"SELECT customer_id, customer_name, MEASURE(net_sales) AS net_sales FROM {S}.sales_metrics "
                                      f"WHERE year = 2026 GROUP BY customer_id, customer_name ORDER BY net_sales DESC LIMIT 5"),
    "net_sales": lambda w: sql(w, f"SELECT region, MEASURE(net_sales) AS net_sales, MEASURE(gross_margin_pct) AS margin, "
                                  f"MEASURE(region_share_pct) AS share FROM {S}.sales_metrics GROUP BY region ORDER BY net_sales DESC"),
    "legacy": lambda w: sql(w, f"SELECT 'legacy view' AS source, sum(net_sales) AS net_sales FROM {S}.v_sales_es_legacy WHERE year_month = '2026-09' "
                               f"UNION ALL SELECT 'certified metric view', MEASURE(net_sales) FROM {S}.sales_metrics WHERE region = 'ES' AND month = '2026-09-01'"),
    "certification": lambda w: sql(w, f"SELECT table_name, tag_value AS status FROM {CATALOG}.information_schema.table_tags "
                                      f"WHERE tag_name = 'system.certification_status' ORDER BY table_name"),
}
