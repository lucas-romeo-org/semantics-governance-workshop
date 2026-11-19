"""'Your own agent': an LLM (Databricks Foundation Model API) that writes SQL against the certified
Metric Views and executes it through the DBSQL MCP server.

Identity split (shown in the UI):
- the LLM call runs as the app service principal (it never touches data);
- every tool call (execute_sql via MCP) runs as the selected identity, so RLS/CLS apply.
"""
import json
import os
import time

from sgw import mcp

ENDPOINT = os.environ.get("SERVING_ENDPOINT", "databricks-claude-sonnet-5-5")
CATALOG = os.environ.get("SGW_CATALOG", "sgw_shop")

SYSTEM = f"""You are a data agent for the Retail Sales domain. Answer by calling the execute_sql tool. Prefer the CERTIFIED
Unity Catalog Metric Views below. If the user explicitly asks for another table, try the query: access is enforced by
Unity Catalog, not by you; if it is rejected, explain the error briefly and offer the certified alternative.

Metric view {CATALOG}.semantic.sales_metrics
- dimensions: region (ES/PT/FR/IT), city, store_format, category, brand, order_date, month (date), year, customer_id, customer_name, customer_segment
- measures: net_sales, gross_sales, discount_amount, gross_margin, gross_margin_pct, units, sales_lines, customers,
  promo_net_sales, discount_rate, promo_share_pct, sales_per_customer, net_sales_ly, net_sales_yoy_pct, net_sales_ytd,
  active_customers_90d, region_share_pct
Metric view {CATALOG}.semantic.sales_vs_budget_metrics
- dimensions: month, year, region, category · measures: net_sales, budget, budget_gap, budget_attainment_pct, ytd_attainment_pct

Rules: every measure must be wrapped in MEASURE(name); no SELECT *; data ends 2026-10-31 ("last quarter" = 2026-07-01..2026-09-30);
for window measures (net_sales_ly, net_sales_yoy_pct) aggregate first and filter months in an outer query.
If values come back as '****' they are masked by policy: say so. If the user only sees some regions, say the data is
limited by their permissions. Be concise: 2-4 sentences, EUR with 2 decimals."""

TOOLS = [{"type": "function", "function": {
    "name": "execute_sql", "description": "Run one SQL query on Databricks SQL through the DBSQL MCP server.",
    "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}}]


def run(question: str, w_user, w_app, warehouse_id: str, max_turns: int = 4) -> dict:
    t0 = time.time()
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]
    calls = []
    for _ in range(max_turns):
        resp = w_app.api_client.do("POST", f"/serving-endpoints/{ENDPOINT}/invocations",
                                   body={"messages": messages, "tools": TOOLS, "max_tokens": 800})
        msg = resp["choices"][0]["message"]
        tool_calls = msg.get("tool_calls") or []
        if not tool_calls:
            return {"ok": True, "answer": msg.get("content", ""), "calls": calls, "seconds": round(time.time() - t0, 1),
                    "model": ENDPOINT}
        messages.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": tool_calls})
        for tc in tool_calls:
            q = json.loads(tc["function"]["arguments"]).get("query", "")
            res = mcp.dbsql_execute(w_user, q, warehouse_id)            # ← runs as the selected identity
            calls.append({"sql": q, "state": res["state"], "error": res["error"], "columns": res["columns"], "rows": res["rows"][:20]})
            payload = {"state": res["state"], "error": res["error"], "columns": res["columns"], "rows": res["rows"][:50]}
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": json.dumps(payload)[:6000]})
    return {"ok": True, "answer": "(stopped after the maximum number of tool calls)", "calls": calls,
            "seconds": round(time.time() - t0, 1), "model": ENDPOINT}
