"""Minimal JSON-RPC client for Databricks Unity Gateway MCP services."""
import json
import time
from databricks.sdk import WorkspaceClient

HDR = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}


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
    return [t["name"] for t in _rpc(w, service, "tools/list", {}).get("tools", [])]


def call_tool(w, service, tool, args, meta=None):
    params = {"name": tool, "arguments": args}
    if meta:
        params["_meta"] = meta
    return _rpc(w, service, "tools/call", params)


def genie_one_ask(w, question: str, timeout_s: int = 100) -> dict:
    t0 = time.time()
    sc = call_tool(w, "system.ai.genie_one_mcp", "genie_ask", {"question": question}).get("structuredContent", {})
    cid, rid = sc.get("conversation_id"), sc.get("response_id")
    st = sc
    while time.time() - t0 < timeout_s and st.get("status") not in ("completed", "failed", "cancelled"):
        time.sleep(3)
        st = call_tool(w, "system.ai.genie_one_mcp", "genie_poll_response",
                       {"conversation_id": cid, "response_id": rid}).get("structuredContent", {})
    return {"status": st.get("status"), "answer": st.get("final_answer"), "deep_link": st.get("deep_link"),
            "seconds": round(time.time() - t0, 1)}


def dbsql_execute(w, query: str, warehouse_id: str, timeout_s: int = 60) -> dict:
    t0 = time.time()
    sc = call_tool(w, "system.ai.dbsql", "execute_sql", {"query": query}, {"warehouse_id": warehouse_id}).get("structuredContent", {})
    while sc.get("status", {}).get("state") in ("PENDING", "RUNNING") and time.time() - t0 < timeout_s:
        time.sleep(2)
        sc = call_tool(w, "system.ai.dbsql", "poll_sql_result", {"statement_id": sc["statement_id"]}).get("structuredContent", {})
    cols = [c["name"] for c in sc.get("manifest", {}).get("schema", {}).get("columns", [])]
    rows = (sc.get("result") or {}).get("data_array") or []
    return {"state": sc.get("status", {}).get("state"), "error": (sc.get("status", {}).get("error") or {}).get("message"),
            "columns": cols, "rows": rows, "seconds": round(time.time() - t0, 1)}
