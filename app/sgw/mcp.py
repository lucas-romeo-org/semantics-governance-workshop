"""Minimal JSON-RPC client for the Databricks Unity Gateway MCP services.

These are the same endpoints any external MCP client (Claude, ChatGPT, Cowork, a custom agent) calls:
    POST https://<workspace>/ai-gateway/mcp-services/<service>
    Authorization: Bearer <OAuth token of the person>      ← on behalf of the user (OBO)
"""
import json
import time
from databricks.sdk import WorkspaceClient

HDR = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
GENIE_ONE = "system.ai.genie_one_mcp"
DBSQL = "system.ai.dbsql"
SERVICES = {"genie_one": GENIE_ONE, "dbsql": DBSQL}


def _rpc(w: WorkspaceClient, service: str, method: str, params: dict) -> dict:
    r = w.api_client.do("POST", f"/ai-gateway/mcp-services/{service}",
                        body={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, headers=HDR, raw=True)
    txt = r["contents"].read().decode()
    try:
        msg = json.loads(txt)
    except json.JSONDecodeError:
        msg = next(json.loads(l[5:]) for l in txt.splitlines() if l.startswith("data:"))
    if "error" in msg:
        raise RuntimeError(msg["error"].get("message", str(msg["error"])))
    return msg["result"]


def list_tools(w, service):
    return [{"name": t["name"], "description": (t.get("description") or "").split("\n")[0][:240]}
            for t in _rpc(w, service, "tools/list", {}).get("tools", [])]


def call_tool(w, service, tool, args, meta=None):
    params = {"name": tool, "arguments": args}
    if meta:
        params["_meta"] = meta
    return _rpc(w, service, "tools/call", params)


def genie_one_stream(w, question: str, conversation_id: str | None = None, timeout_s: int = 150):
    """genie_ask, then genie_poll_response until completed. Yields progress dicts; the last one has final=True."""
    t0 = time.time()
    args = {"question": question}
    if conversation_id:
        args["conversation_id"] = conversation_id
    sc = call_tool(w, GENIE_ONE, "genie_ask", args).get("structuredContent", {})
    cid, rid, polls = sc.get("conversation_id"), sc.get("response_id"), 0
    while time.time() - t0 < timeout_s and sc.get("status") not in ("completed", "failed", "cancelled"):
        time.sleep(3)
        polls += 1
        sc = call_tool(w, GENIE_ONE, "genie_poll_response", {"conversation_id": cid, "response_id": rid}).get("structuredContent", {})
        yield {"final": False, "polls": polls, "seconds": round(time.time() - t0, 1), "status": sc.get("status")}
    qi = sc.get("query_items") or []
    yield {"final": True, "status": sc.get("status") or "timeout", "answer": sc.get("final_answer"),
           "deep_link": sc.get("deep_link"), "conversation_id": cid, "polls": polls,
           "sql": qi[0].get("sql") if qi else None, "seconds": round(time.time() - t0, 1)}


def genie_one_ask(w, question: str, timeout_s: int = 100) -> dict:
    *_, last = genie_one_stream(w, question, timeout_s=timeout_s)
    return last


def dbsql_execute(w, query: str, warehouse_id: str, timeout_s: int = 60) -> dict:
    t0 = time.time()
    sc = call_tool(w, DBSQL, "execute_sql", {"query": query}, {"warehouse_id": warehouse_id}).get("structuredContent", {})
    polls = 0
    while sc.get("status", {}).get("state") in ("PENDING", "RUNNING") and time.time() - t0 < timeout_s:
        time.sleep(2)
        polls += 1
        sc = call_tool(w, DBSQL, "poll_sql_result", {"statement_id": sc["statement_id"]}).get("structuredContent", {})
    cols = [c["name"] for c in sc.get("manifest", {}).get("schema", {}).get("columns", [])]
    res = sc.get("result") or {}
    rows = res.get("data_array") or [[next(iter(v.values()), None) if isinstance(v, dict) else v for v in r.get("values", [])]
                                     for r in res.get("data_typed_array", [])]
    return {"state": sc.get("status", {}).get("state"), "error": (sc.get("status", {}).get("error") or {}).get("message"),
            "columns": cols, "rows": rows, "polls": polls, "seconds": round(time.time() - t0, 1)}
