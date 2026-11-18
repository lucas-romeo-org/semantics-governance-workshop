"""Wave 0 preflight: checks what the target workspace/account supports before deploying.

Usage:
    python scripts/preflight.py --profile <workspace-profile> --account-profile <account-profile> [--out docs/preflight-sandbox.md]

Read-only: it never creates or changes anything.
"""
import argparse
import datetime as dt
import sys

from databricks.sdk import AccountClient, WorkspaceClient


def check(label, fn):
    try:
        detail = fn()
        return ("✅", label, detail or "")
    except Exception as e:  # noqa: BLE001 - we want to report any failure
        msg = str(e).split("\n")[0][:160]
        return ("❌", label, msg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True)
    ap.add_argument("--account-profile")
    ap.add_argument("--catalog", default="sgw_shop")
    ap.add_argument("--out")
    args = ap.parse_args()

    w = WorkspaceClient(profile=args.profile)
    rows = []

    me = w.current_user.me()
    rows.append(("ℹ️", "Caller", f"{me.user_name}"))
    rows.append(check("Workspace admin", lambda: "yes" if any(g.display == "admins" for g in (me.groups or [])) else (_ for _ in ()).throw(Exception("caller is not in the workspace 'admins' group"))))

    ms = None

    def _ms():
        nonlocal ms
        ms = w.metastores.summary()
        return f"{ms.name} · region {ms.region} · cloud {ms.cloud} · owner {ms.owner}"
    rows.append(check("Unity Catalog metastore", _ms))

    def _create_catalog():
        eff = w.grants.get_effective(securable_type="metastore", full_name=ms.metastore_id, principal=me.user_name)
        privs = {p.privilege.value if hasattr(p.privilege, "value") else str(p.privilege)
                 for a in (eff.privilege_assignments or []) for p in (a.privileges or [])}
        if "CREATE_CATALOG" in privs or ms.owner == me.user_name:
            return "CREATE CATALOG available"
        raise Exception(f"missing CREATE CATALOG (has: {sorted(privs) or 'none'})")
    rows.append(check("Can create catalog", _create_catalog))

    def _catalog_free():
        names = {c.name for c in w.catalogs.list()}
        return f"'{args.catalog}' already exists (will be reused)" if args.catalog in names else f"'{args.catalog}' is free"
    rows.append(check("Target catalog", _catalog_free))

    def _wh():
        whs = list(w.warehouses.list())
        sl = [x for x in whs if x.enable_serverless_compute]
        return f"{len(whs)} warehouses ({len(sl)} serverless)"
    rows.append(check("SQL warehouses / serverless", _wh))

    def _sql_serverless():
        # A trivial statement on any running-capable serverless warehouse proves serverless SQL works.
        whs = [x for x in w.warehouses.list() if x.enable_serverless_compute]
        if not whs:
            raise Exception("no serverless warehouse to test (the bundle will create one)")
        r = w.statement_execution.execute_statement(warehouse_id=whs[0].id, statement="SELECT current_version().dbsql_version AS v", wait_timeout="50s")
        return f"DBSQL {r.result.data_array[0][0] if r.result and r.result.data_array else '?'} on '{whs[0].name}'"
    rows.append(check("Serverless SQL execution", _sql_serverless))

    def _tag_policies():
        tps = list(w.tag_policies.list_tag_policies())
        return f"{len(tps)} governed tags defined"
    rows.append(check("Governed tags API", _tag_policies))

    def _apps():
        list(w.apps.list())
        return "Databricks Apps available"
    rows.append(check("Databricks Apps", _apps))

    def _vs():
        eps = list(w.vector_search_endpoints.list_endpoints())
        return f"{len(eps)} AI Search endpoints"
    rows.append(check("AI Search (Vector Search)", _vs))

    def _genie():
        r = w.genie.list_spaces()
        return f"{len(r.spaces or [])} Genie Agents visible"
    rows.append(check("Genie Agents API", _genie))

    if args.account_profile:
        a = AccountClient(profile=args.account_profile)

        def _acct():
            list(a.groups.list(count=1))
            return f"account {a.config.account_id}"
        rows.append(check("Account admin (groups API)", _acct))

        def _ws_in_acct():
            wid = w.get_workspace_id()
            ws = a.workspaces.get(wid)
            return f"{ws.workspace_name} ({wid}) · {ws.location}"
        rows.append(check("Workspace visible from account", _ws_in_acct))

    manual = [
        "Pages (Beta) enabled for the account",
        "Discover / Domains (Public Preview) enabled",
        "Managed MCP Servers enabled in the workspace (Genie Agent MCP, legacy DBSQL MCP)",
        "Enhanced Unity Gateway preview (system.ai.dbsql MCP)",
        "Data Classification enabled",
        "Agent Bricks / Knowledge Assistant available in region",
    ]

    lines = [f"# Preflight report · {dt.datetime.now():%Y-%m-%d %H:%M}", "",
             f"Workspace: `{w.config.host}`", "", "| | Check | Detail |", "|---|---|---|"]
    lines += [f"| {s} | {l} | {d} |" for s, l, d in rows]
    lines += ["", "## Manual checks (no public API)", ""] + [f"- [ ] {m}" for m in manual]
    report = "\n".join(lines)
    print(report)
    if args.out:
        with open(args.out, "w") as f:
            f.write(report + "\n")
    sys.exit(1 if any(s == "❌" for s, _, _ in rows) else 0)


if __name__ == "__main__":
    main()
