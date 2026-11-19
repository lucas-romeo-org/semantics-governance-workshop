"""The agent behind the step-7 chat: a generic MCP client, like Claude, ChatGPT or Cowork would be.

- Its tools come from the MCP servers the user connects (Genie One MCP, DBSQL MCP).
- The reasoning (LLM, Databricks Foundation Model API) runs as the app service principal: it never touches data.
- Every MCP tool call runs with the selected person's token (OBO), so Unity Catalog applies their grants,
  row filters and column masks, and audits the call under their name.

stream() yields small JSON-able events that the frontend renders as chat parts and as the OBO trace.
"""
import json
import os
import time

from sgw import mcp

ENDPOINT = os.environ.get("SERVING_ENDPOINT", "databricks-claude-sonnet-5-5")
CATALOG = os.environ.get("SGW_CATALOG", "sgw_shop")

BASE = f"""You are a data agent for the Retail Sales domain, connected to Databricks through MCP servers.
Unity Catalog enforces access for the signed-in person: never refuse on their behalf, try and report what happens.
Data ends 2026-10-31 ("last quarter" = 2026-07-01..2026-09-30). Answers: concise, 2-4 sentences, EUR with 2 decimals.
If values come back as '****' they are masked by policy: say so. If only some regions appear, say that the data is limited by
the person's permissions. Use markdown (short tables are fine)."""

SQL_GUIDE = f"""
Tool execute_sql (DBSQL MCP): you write the SQL. Prefer the CERTIFIED Metric Views:
- {CATALOG}.semantic.sales_metrics · dimensions: region (ES/PT/FR/IT), city, store_format, category, brand, order_date,
  month (date), year, customer_id, customer_name, customer_segment · measures: net_sales, gross_sales, discount_amount,
  gross_margin, gross_margin_pct, units, sales_lines, customers, promo_net_sales, discount_rate, promo_share_pct,
  sales_per_customer, net_sales_ly, net_sales_yoy_pct, net_sales_ytd, active_customers_90d, region_share_pct
- {CATALOG}.semantic.sales_vs_budget_metrics · dimensions: month, year, region, category · measures: net_sales, budget,
  budget_gap, budget_attainment_pct, ytd_attainment_pct
Wrap every measure in MEASURE(name); no SELECT *; for window measures (net_sales_ly, net_sales_yoy_pct) aggregate first
and filter months in an outer query. If the user asks for another table (e.g. gold), run it: access is decided by Unity
Catalog; if rejected, explain the error in one sentence and offer the certified alternative."""

GENIE_GUIDE = """
Tool genie_ask (Genie One MCP): Databricks' own data agent, grounded on the certified ontology (domains, Metric Views,
Pages, certification). Pass the user's question in natural language. The UI already shows Genie's full answer with its
table: after calling it, reply with ONE short sentence (the key number and any permission caveat). No tables, no lists."""

BOTH_GUIDE = """
Both tools are available: use genie_ask for business questions in natural language; use execute_sql when the user asks
for SQL, a specific table, raw rows, or a precise calculation."""

TOOL_DEFS = {
    "dbsql": {"type": "function", "function": {
        "name": "execute_sql",
        "description": "DBSQL MCP · Execute a SQL query against Unity Catalog (Databricks SQL) as the signed-in user.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    "genie_one": {"type": "function", "function": {
        "name": "genie_ask",
        "description": "Genie One MCP · Ask Databricks Genie a natural-language data question; returns a grounded answer.",
        "parameters": {"type": "object", "properties": {"question": {"type": "string"}}, "required": ["question"]}}},
}
SERVER_OF = {"execute_sql": mcp.DBSQL, "genie_ask": mcp.GENIE_ONE}


def _system(servers):
    s = BASE
    if "dbsql" in servers:
        s += SQL_GUIDE
    if "genie_one" in servers:
        s += GENIE_GUIDE
    if len(servers) > 1:
        s += BOTH_GUIDE
    return s


def stream(history, servers, w_user, w_app, warehouse_id, genie_conversation_id=None, max_turns=5):
    t0 = time.time()
    servers = [s for s in ("genie_one", "dbsql") if s in servers] or ["dbsql"]
    tools = [TOOL_DEFS[s] for s in servers]
    msgs = [{"role": "system", "content": _system(servers)}] + [m for m in history[-12:] if m.get("content")]
    conv = genie_conversation_id
    n_calls = 0
    for _ in range(max_turns):
        resp = w_app.api_client.do("POST", f"/serving-endpoints/{ENDPOINT}/invocations",
                                   body={"messages": msgs, "tools": tools, "max_tokens": 900})
        msg = resp["choices"][0]["message"]
        tool_calls = msg.get("tool_calls") or []
        text = msg.get("content") or ""
        if isinstance(text, list):  # some endpoints return content blocks
            text = "".join(b.get("text", "") for b in text if isinstance(b, dict))
        if not tool_calls:
            yield {"t": "text", "text": text}
            break
        if text.strip():
            yield {"t": "text", "text": text}
        msgs.append({"role": "assistant", "content": text, "tool_calls": tool_calls})
        for tc in tool_calls:
            n_calls += 1
            name = tc["function"]["name"]
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            server = SERVER_OF.get(name, "?")
            yield {"t": "tool_start", "id": tc["id"], "tool": name, "server": server, "args": args}
            try:
                if name == "execute_sql":
                    res = mcp.dbsql_execute(w_user, args.get("query", ""), warehouse_id)          # ← as the person
                    ok = res["state"] == "SUCCEEDED"
                    out = {"ok": ok, **res, "rows": res["rows"][:50]}
                    payload = {k: out[k] for k in ("state", "error", "columns")} | {"rows": res["rows"][:40]}
                elif name == "genie_ask":
                    out = None
                    for ev in mcp.genie_one_stream(w_user, args.get("question", ""), conv):        # ← as the person
                        if ev["final"]:
                            out = {"ok": ev["status"] == "completed", **ev}
                        else:
                            yield {"t": "tool_progress", "id": tc["id"], **ev}
                    conv = out.get("conversation_id") or conv
                    payload = {"status": out["status"], "answer": (out.get("answer") or "")[:5000], "sql": out.get("sql")}
                else:
                    out = {"ok": False, "error": f"unknown tool {name}"}
                    payload = out
            except Exception as e:  # noqa: BLE001 - surface MCP / permission errors to the model and the UI
                out = {"ok": False, "state": "FAILED", "error": str(e).splitlines()[0][:400]}
                payload = out
            yield {"t": "tool_end", "id": tc["id"], "tool": name, "server": server, **out}
            msgs.append({"role": "tool", "tool_call_id": tc["id"], "content": json.dumps(payload, default=str)[:7000]})
    else:
        yield {"t": "text", "text": "_(stopped after the maximum number of tool calls)_"}
    yield {"t": "done", "seconds": round(time.time() - t0, 1), "model": ENDPOINT, "calls": n_calls,
           "genie_conversation_id": conv}
