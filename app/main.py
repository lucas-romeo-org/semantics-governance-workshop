"""Semantic Governance Workshop · companion app (FastAPI backend + React frontend built at deploy)."""
import json
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from sgw import agent, links, mcp
from sgw.identity import PERSONAS, app_client, client_for, describe, host
from sgw.proofs import PROOFS, CATALOG, WH

HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(HERE, "dist")
app = FastAPI(title="sgw-companion")


def _load(name, default):
    p = os.path.join(HERE, "content", name)
    return json.load(open(p)) if os.path.exists(p) else default


STEPS = _load("steps.json", [])
ART = _load("artifacts.json", {"catalog": CATALOG, "domain": "Retail Sales"})


def resolve(a: dict) -> dict:
    """Turn an artifact reference from steps.json into a real deep link."""
    kind, ref, cat = a["kind"], a.get("ref", ""), ART.get("catalog", CATALOG)
    url = None
    if kind in ("table", "table_tab"):
        obj, _, tab = ref.partition(":")
        schema, _, name = obj.partition("/")
        url = links.table(cat, schema, name or None, tab or None)
    elif kind == "job" and ART.get("jobs", {}).get(ref):
        url = links.job(ART["jobs"][ref])
    elif kind == "group" and ART.get("groups", {}).get(ref):
        url = links.group(ART["groups"][ref])
    elif kind == "dashboard" and ART.get("dashboards", {}).get(ref):
        url = links.dashboard(ART["dashboards"][ref])
    elif kind == "genie" and ART.get("genie_spaces", {}).get(ref):
        url = links.genie(ART["genie_spaces"][ref])
    elif kind == "domain":
        url = links.domain(ART.get("domain", "Retail Sales"))
    elif kind == "page" and ART.get("pages", {}).get(ref):
        url = links.page(ART["pages"][ref])
    elif kind == "genie_one":
        url = f"{links._base()}/one?{links._o()}"
    elif kind == "warehouse" and WH:
        url = f"{links._base()}/sql/warehouses/{WH}?{links._o()}"
    elif kind == "repo":
        base = ART.get("repo", "https://github.com/lucas-romeo-org/semantics-governance-workshop")
        url = f"{base}/tree/main/{ref}" if ref else base
    return {**a, "url": url}


# Map nodes → the real artifact each one opens
NODE_LINKS = {
    "groups": {"kind": "group", "ref": "analysts"}, "personas": {"kind": "group", "ref": "analysts_es"},
    "gold": {"kind": "table", "ref": "gold"}, "tags": {"kind": "table", "ref": "gold/dim_customer"},
    "policies": {"kind": "table_tab", "ref": "gold:policies"}, "mv": {"kind": "table", "ref": "semantic/sales_metrics"},
    "context": {"kind": "domain", "ref": ""}, "dash": {"kind": "dashboard", "ref": "retail_sales_dashboard"},
    "genie": {"kind": "genie", "ref": "retail_sales_agent"}, "mcp": {"kind": "repo", "ref": "app"},
    "bi": {"kind": "repo", "ref": "runbooks"}, "ops": {"kind": "dashboard", "ref": "governance_in_action"},
    "people": {"kind": "group", "ref": "analysts"}, "genieone": {"kind": "genie_one", "ref": ""},
    "agents": {"kind": "repo", "ref": "runbooks"}, "gateway": {"kind": "repo", "ref": "app/sgw/mcp.py"},
    "app": {"kind": "repo", "ref": "app"}, "oauth": {"kind": "repo", "ref": "runbooks/w8_app.md"},
    "warehouse": {"kind": "warehouse", "ref": ""}, "idp": {"kind": "repo", "ref": "runbooks/w1_identity.md"},
}


@app.get("/api/info")
def info(request: Request):
    return {"catalog": CATALOG, "user": request.headers.get("x-forwarded-email"), "host": host(),
            "mcp": {k: f"{host()}/ai-gateway/mcp-services/{v}" for k, v in mcp.SERVICES.items()},
            "has_user_token": bool(request.headers.get("x-forwarded-access-token")),
            "personas": PERSONAS, "nodes": {k: resolve(v)["url"] for k, v in NODE_LINKS.items()}}


@app.get("/api/steps")
def steps():
    return [{**s, "artifacts": [resolve(a) for a in s.get("artifacts", [])]} for s in STEPS]


@app.get("/api/proof/{key}")
def proof(key: str, request: Request, who: str = "me"):
    fn = PROOFS.get(key)
    if not fn:
        raise HTTPException(404, f"no proof '{key}'")
    try:
        res = fn(client_for(who, request))
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        res = {"ok": False, "error": str(e).splitlines()[0][:220]}
    return JSONResponse({"who": who, "key": key, **res})


@app.get("/api/mcp/tools")
def mcp_tools(request: Request, who: str = "me"):
    """tools/list on both MCP servers, as the selected identity (discovery is itself an MCP call)."""
    w, out = client_for(who, request), {}
    for key, service in mcp.SERVICES.items():
        try:
            out[key] = {"service": service, "ok": True, "tools": mcp.list_tools(w, service)}
        except Exception as e:  # noqa: BLE001
            out[key] = {"service": service, "ok": False, "error": str(e).splitlines()[0][:200], "tools": []}
    return out


@app.post("/api/chat")
async def chat(request: Request):
    """Server-sent events: the agent (LLM as the app SP) calling MCP tools as the selected identity."""
    body = await request.json()
    who = body.get("who", "me")
    w_user = client_for(who, request)            # fails fast (401/400) before the stream starts
    ident = describe(who, request)
    history = [{"role": m.get("role"), "content": str(m.get("content", ""))[:4000]} for m in body.get("history", [])
               if m.get("role") in ("user", "assistant")]

    def events():
        yield _sse({"t": "identity", **ident, "servers": body.get("servers", [])})
        try:
            for ev in agent.stream(history, body.get("servers", ["genie_one", "dbsql"]), w_user, app_client(), WH,
                                   body.get("genie_conversation_id")):
                yield _sse(ev)
        except Exception as e:  # noqa: BLE001
            yield _sse({"t": "error", "message": str(e).splitlines()[0][:300]})
            yield _sse({"t": "done"})

    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


def _sse(ev: dict) -> str:
    return f"data: {json.dumps(ev, default=str)}\n\n"


STEP_JOBS = {1: "w1_identity_setup", 2: "w2_gold", 3: "w3_security", 4: "w4_semantic", 5: "w5_context",
             6: "w6_consumption_verify", 8: "w7_operate"}


@app.get("/api/status")
def status():
    """Last verify run per step (app SP: job metadata only, never data)."""
    w, out = app_client(), {}
    for step, key in STEP_JOBS.items():
        job_id = ART.get("jobs", {}).get(key)
        if not job_id:
            continue
        try:
            run = next(iter(w.jobs.list_runs(job_id=int(job_id), limit=1, completed_only=True)), None)
            out[step] = {"result": run.state.result_state.value if run and run.state and run.state.result_state else None,
                         "at": run.end_time if run else None, "url": links.job(job_id)}
        except Exception as e:  # noqa: BLE001
            out[step] = {"result": None, "error": str(e).splitlines()[0][:120]}
    return out


# ── frontend (built by Databricks Apps: npm install → npm run build → dist/) ──
if os.path.isdir(os.path.join(DIST, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST, "assets")), name="assets")


@app.get("/{path:path}")
def spa(path: str):
    index = os.path.join(DIST, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return JSONResponse({"error": "frontend not built: dist/ missing"}, status_code=503)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("DATABRICKS_APP_PORT", 8000)))
