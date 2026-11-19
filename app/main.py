"""Semantic Governance Workshop · companion app (FastAPI backend + React frontend built at deploy)."""
import json
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from sgw import agent, links, mcp
from sgw.identity import PERSONAS, app_client, client_for
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
    "agents": {"kind": "repo", "ref": "runbooks"},
}


@app.get("/api/info")
def info(request: Request):
    return {"catalog": CATALOG, "user": request.headers.get("x-forwarded-email"),
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


@app.get("/api/ask/{surface}")
def ask(surface: str, q: str, request: Request, who: str = "me"):
    w = client_for(who, request)
    try:
        if surface == "genie_one":
            return {"who": who, "surface": surface, "ok": True, **mcp.genie_one_ask(w, q)}
        if surface == "dbsql":
            return {"who": who, "surface": surface, "ok": True, **mcp.dbsql_execute(w, q, WH)}
    except Exception as e:  # noqa: BLE001
        return {"who": who, "surface": surface, "ok": False, "error": str(e).splitlines()[0][:300]}
    raise HTTPException(404, surface)


@app.get("/api/agent")
def run_agent(q: str, request: Request, who: str = "me"):
    """LLM as the app SP; every SQL tool call through DBSQL MCP as the selected identity."""
    try:
        return {"who": who, **agent.run(q, client_for(who, request), app_client(), WH)}
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        return {"who": who, "ok": False, "error": str(e).splitlines()[0][:300]}


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
