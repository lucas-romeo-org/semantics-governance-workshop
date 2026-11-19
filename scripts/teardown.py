"""Reset the workshop: remove everything waves 1-8 created, in reverse order. Workspace-level APIs only.

Dry run by default (lists what it would delete). Nothing is removed without --apply and typing the catalog name.

    python scripts/teardown.py --profile <ws>                       # dry run
    python scripts/teardown.py --profile <ws> --apply                # delete (asks for confirmation)
    python scripts/teardown.py --profile <ws> --apply --keep-identity --keep-catalog   # only the semantic/consumption layer

Order: Pages → Discover domains → catalog (DROP … CASCADE: tables, Metric Views, ABAC policies) → governed tags →
bundle resources (jobs, dashboards, Genie space, app, warehouse) → secret scope → persona service principals → groups.
Groups and service principals were created through the workspace identity proxy; this removes exactly those, by name.
"""
import argparse
import pathlib
import subprocess
import sys

from databricks.sdk import WorkspaceClient

ROOT = pathlib.Path(__file__).resolve().parents[1]
GROUPS = ["platform_admins", "data_engineers", "security_admins", "sales_domain_owners", "analysts_es", "analysts_pt",
          "sales_leads", "pii_readers", "analysts"]
SPS = ["persona-ana", "persona-pedro", "persona-marta", "cicd"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True)
    ap.add_argument("--target", default="sandbox")
    ap.add_argument("--catalog", default="sgw_shop")
    ap.add_argument("--domain", default="Retail Sales")
    ap.add_argument("--tag-prefix", default="sgw_")
    ap.add_argument("--group-prefix", default="wk_")
    ap.add_argument("--sp-prefix", default="sgw-")
    ap.add_argument("--secret-scope", default="sgw")
    ap.add_argument("--keep-catalog", action="store_true", help="keep the catalog (it may have been created in the UI)")
    ap.add_argument("--keep-identity", action="store_true", help="keep groups, service principals and the secret scope")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    w = WorkspaceClient(profile=a.profile)
    plan = []  # (label, callable)

    # 1. Pages and 2. domains (children first)
    doms = [d for d in w.domains.list_domains(page_size=500) if d.tag_key == a.domain or d.tag_key.startswith(a.domain + "/")]
    dom_names = {d.name for d in doms}
    pages, token = [], None
    while True:
        r = w.api_client.do("GET", "/api/2.0/knowledge/pages", query={"page_size": 100, **({"page_token": token} if token else {})})
        pages += r.get("pages", [])
        token = r.get("next_page_token")
        if not token:
            break
    for p in (p for p in pages if p.get("domain") in dom_names):
        name = p["name"]
        path = f"/api/2.0/{name}" if name.startswith("knowledge/") else f"/api/2.0/knowledge/{name}"
        plan.append((f"page      {p.get('display_name')}", lambda path=path: w.api_client.do("DELETE", path)))
    for d in sorted(doms, key=lambda d: -d.tag_key.count("/")):
        plan.append((f"domain    {d.tag_key}", lambda d=d: w.domains.delete_domain(d.name, force=True)))

    # 3. catalog (needs a warehouse, so before the bundle removes it)
    if not a.keep_catalog and any(c.name == a.catalog for c in w.catalogs.list()):
        wh = next((x.id for x in w.warehouses.list() if x.name and "sgw" in x.name.lower()), None) or \
             next((x.id for x in w.warehouses.list() if x.enable_serverless_compute), None)
        plan.append((f"catalog   {a.catalog} (CASCADE: gold, semantic, governance, ops, ABAC policies)",
                     lambda: w.statement_execution.execute_statement(warehouse_id=wh, statement=f"DROP CATALOG `{a.catalog}` CASCADE",
                                                                     wait_timeout="50s")))

    # 4. governed tags: workshop taxonomy + the tags that back the domains
    tag_keys = [t.tag_key for t in w.tag_policies.list_tag_policies()
                if t.tag_key.startswith(a.tag_prefix) or t.tag_key == a.domain or t.tag_key.startswith(a.domain + "/")]
    for k in sorted(tag_keys, key=lambda k: -k.count("/")):
        plan.append((f"tag       {k}", lambda k=k: w.tag_policies.delete_tag_policy(k)))

    # 5. bundle resources
    plan.append((f"bundle    destroy -t {a.target} (jobs, dashboards, Genie space, app, warehouse)",
                 lambda: subprocess.run(["databricks", "bundle", "destroy", "-t", a.target, "--profile", a.profile, "--auto-approve"],
                                        cwd=ROOT, check=True)))

    # 6. identity
    if not a.keep_identity:
        if a.secret_scope in {s.name for s in w.secrets.list_scopes()}:
            plan.append((f"secrets   scope {a.secret_scope}", lambda: w.secrets.delete_scope(a.secret_scope)))
        for sp in SPS:
            name = f"{a.sp_prefix}{sp}"
            for s in w.service_principals.list(filter=f'displayName eq "{name}"'):
                plan.append((f"sp        {name}", lambda s=s: w.service_principals.delete(s.id)))
        idp = w.workspace_iam_v2
        for g in GROUPS:  # nested parent (analysts) last is fine: membership goes with the child
            name = f"{a.group_prefix}{g}"
            for x in idp.list_groups_proxy(filter=f'group_name eq "{name}"'):
                if x.group_name == name:
                    plan.append((f"group     {name}", lambda x=x: idp.delete_group_proxy(f"groups/{x.group_id}")))

    print(f"{'DELETE' if a.apply else 'Would delete'} ({len(plan)}):")
    for label, _ in plan:
        print(f"  · {label}")
    if not a.apply:
        print("\nDry run. Re-run with --apply to delete.")
        return
    if input(f"\nType the catalog name ({a.catalog}) to confirm: ").strip() != a.catalog:
        sys.exit("Aborted.")
    for label, fn in plan:
        try:
            fn()
            print(f"  ✓ {label}")
        except Exception as e:  # noqa: BLE001 - keep going, report at the end
            print(f"  ✗ {label}: {str(e).splitlines()[0][:160]}")


if __name__ == "__main__":
    main()
