"""Semantic Governance Workshop · companion app (wave 8a spike)."""
import os
import traceback

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from sgw import mcp
from sgw.identity import PERSONAS, client_for, host

CATALOG = os.environ.get("SGW_CATALOG", "sgw_shop")
WH = os.environ.get("WAREHOUSE_ID", "")
app = FastAPI(title="sgw-companion")
HERE = os.path.dirname(os.path.abspath(__file__))


def _try(fn):
    try:
        return {"ok": True, **fn()}
    except Exception as e:  # noqa: BLE001 - the spike reports every failure
        return {"ok": False, "error": str(e).splitlines()[0][:400]}


def _sql(w, stmt):
    r = w.statement_execution.execute_statement(warehouse_id=WH, statement=stmt, wait_timeout="50s")
    if r.status.error:
        raise RuntimeError(r.status.error.message)
    return r.result.data_array or [] if r.result else []


@app.get("/api/spike/{who}")
def spike(who: str, request: Request, mcp_calls: bool = True):
    out = {"who": who}
    try:
        w = client_for(who, request)
    except Exception as e:  # noqa: BLE001
        return {"who": who, "identity": {"ok": False, "error": str(getattr(e, "detail", e))}}
    out["identity"] = _try(lambda: {"user": w.current_user.me().user_name})
    out["metric_view"] = _try(lambda: {"rows": _sql(w, f"SELECT region, MEASURE(net_sales) FROM {CATALOG}.semantic.sales_metrics GROUP BY region ORDER BY region")})
    out["gold_denied"] = _try(lambda: {"rows": _sql(w, f"SELECT count(*) FROM {CATALOG}.gold.fact_sales")})
    if mcp_calls:
        out["dbsql_mcp"] = _try(lambda: mcp.dbsql_execute(w, f"SELECT region, MEASURE(net_sales) AS net_sales FROM {CATALOG}.semantic.sales_metrics GROUP BY region ORDER BY region", WH))
        out["genie_one_mcp"] = _try(lambda: mcp.genie_one_ask(w, "What were net sales by region in 2026-Q3?"))
    import json as _json
    print("SPIKE_DETAIL", _json.dumps(out, default=str)[:6000], flush=True)
    return out


@app.get("/api/info")
def info(request: Request):
    return {"host": host(), "workspace_id": os.environ.get("DATABRICKS_WORKSPACE_ID"), "catalog": CATALOG,
            "has_user_token": bool(request.headers.get("x-forwarded-access-token")),
            "user": request.headers.get("x-forwarded-email"), "personas": PERSONAS}


app.mount("/static", StaticFiles(directory=os.path.join(HERE, "static")), name="static")


@app.get("/")
def index():
    return FileResponse(os.path.join(HERE, "static", "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("DATABRICKS_APP_PORT", 8000)))
