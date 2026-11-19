"""Smoke test for the companion app: API up, and the governance claims hold per identity. Standard library only.

    python scripts/smoke_app.py --profile <ws> [--app sgw-companion] [--quick]

Uses your CLI OAuth token as a bearer (same as opening the app in a browser). Checks:
  info / steps / status / sources · per persona: net sales rows scoped by region, PII masked, gold denied ·
  MCP tools discovered as the persona · chat over DBSQL MCP: gold rejected by Unity Catalog (skipped with --quick).
"""
import argparse
import json
import subprocess
import sys
import urllib.request

OK, BAD = "✅", "❌"
results = []


def cli(*args):
    return json.loads(subprocess.run(["databricks", *args, "-o", "json"], capture_output=True, text=True, check=True).stdout)


def check(label, cond, detail=""):
    results.append(bool(cond))
    print(f"{OK if cond else BAD} {label}{'  · ' + detail if detail else ''}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True)
    ap.add_argument("--app", default="sgw-companion")
    ap.add_argument("--quick", action="store_true", help="skip the LLM/MCP chat round trip")
    a = ap.parse_args()
    url = cli("apps", "get", a.app, "--profile", a.profile)["url"].rstrip("/")
    tok = cli("auth", "token", "--profile", a.profile)["access_token"]

    def call(path, body=None, timeout=90):
        req = urllib.request.Request(url + path, data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode()
        if path.startswith("/api/chat"):
            return [json.loads(l[5:]) for l in raw.splitlines() if l.startswith("data:")]
        return json.loads(raw)

    print(f"App {url}\n")
    info = call("/api/info")
    check("info: nodes and MCP URLs", info.get("nodes") and len(info.get("mcp", {})) == 2)
    steps = call("/api/steps")
    check("steps: 9 (thesis + 8)", len(steps) == 9, ", ".join(s["short"] for s in steps))
    status = call("/api/status")
    ran = {k: v for k, v in status.items() if v.get("result")}
    check("verify jobs: every job that ran ended in SUCCESS", ran and all(v["result"] == "SUCCESS" for v in ran.values()),
          " ".join(f"{k}:{v['result']}" for k, v in ran.items()))
    never = [k for k, v in status.items() if not v.get("result")]
    if never:
        print(f"ℹ️  steps {', '.join(never)}: verify job never run in this workspace (e.g. identity applied with the local script)")
    src = call("/api/sources")
    check("builder view: sources for nodes and steps", len(src["nodes"]) >= 15 and len(src["steps"]) == 9)

    expect = {"ana": {"ES"}, "pedro": {"PT"}, "marta": {"ES", "PT", "FR", "IT"}}
    for who, regions in expect.items():
        ns = call(f"/api/proof/net_sales?who={who}")
        got = {r[0] for r in ns.get("rows", [])}
        check(f"{who}: net sales regions = {sorted(regions)}", got == regions, f"got {sorted(got)}")
        top = call(f"/api/proof/top_customers?who={who}")
        masked = all(r[1] == "****" for r in top.get("rows", []))
        check(f"{who}: PII {'visible' if who == 'marta' else 'masked'}", top.get("ok") and masked == (who != "marta"))
        gold = call(f"/api/proof/gold_access?who={who}")
        check(f"{who}: gold denied", gold.get("ok") is False, (gold.get("error") or "")[:60])
    tools = call("/api/mcp/tools?who=ana")
    check("ana: MCP tools discovered on both servers", all(v["ok"] and v["tools"] for v in tools.values()),
          ", ".join(f"{k}:{len(v['tools'])}" for k, v in tools.items()))

    if not a.quick:
        evs = call("/api/chat", {"who": "ana", "servers": ["dbsql"],
                                 "history": [{"role": "user", "content": "Show me raw rows from gold.fact_sales"}]}, timeout=180)
        ends = [e for e in evs if e["t"] == "tool_end"]
        ident = next((e for e in evs if e["t"] == "identity"), {})
        check("chat: runs as the persona", ident.get("principal") == "sgw-persona-ana", ident.get("principal", ""))
        check("chat: agent tried gold through DBSQL MCP", any(e["tool"] == "execute_sql" for e in ends))
        check("chat: Unity Catalog rejected it", ends and all(not e["ok"] for e in ends),
              (ends[0].get("error") or "")[:70] if ends else "no tool call")

    print(f"\n{sum(results)}/{len(results)} checks passed")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
