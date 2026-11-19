"""Resolve the real artifact IDs of this workspace into app/content/artifacts.json (gitignored).

Run before deploying the app:
    python scripts/render_app_artifacts.py --profile <ws> [--target sandbox]
"""
import argparse
import json
import pathlib
import subprocess

from databricks.sdk import WorkspaceClient

ROOT = pathlib.Path(__file__).resolve().parents[1]


def bundle_ids(profile, target):
    out = subprocess.run(["databricks", "bundle", "summary", "-t", target, "--profile", profile, "-o", "json"],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout
    res = json.loads(out)["resources"]
    pick = lambda kind: {k: str(v.get("id", "")) for k, v in res.get(kind, {}).items()}
    return {"dashboards": pick("dashboards"), "genie_spaces": pick("genie_spaces"), "jobs": pick("jobs")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True)
    ap.add_argument("--target", default="sandbox")
    ap.add_argument("--catalog", default="sgw_shop")
    ap.add_argument("--domain", default="Retail Sales")
    ap.add_argument("--group-prefix", default="wk_")
    args = ap.parse_args()
    w = WorkspaceClient(profile=args.profile)

    ids = bundle_ids(args.profile, args.target)
    idp = w.workspace_iam_v2
    groups = {}
    for g in ("analysts", "analysts_es", "analysts_pt", "sales_leads", "pii_readers", "data_engineers",
              "security_admins", "sales_domain_owners", "platform_admins"):
        name = f"{args.group_prefix}{g}"
        hit = next((x for x in idp.list_groups_proxy(filter=f'group_name eq "{name}"') if x.group_name == name), None)
        if hit:
            groups[g] = hit.group_id

    doms = {d.tag_key: d for d in w.domains.list_domains(page_size=500)}
    domain_ids = {doms[k].name for k in doms if k == args.domain or k.startswith(args.domain + "/")}
    pages, token = [], None
    while True:
        r = w.api_client.do("GET", "/api/2.0/knowledge/pages", query={"page_size": 100, **({"page_token": token} if token else {})})
        pages += r.get("pages", [])
        token = r.get("next_page_token")
        if not token:
            break
    page_ids = {p["display_name"]: p["name"].split("/")[-1] for p in pages if p.get("domain") in domain_ids}

    art = {"catalog": args.catalog, "domain": args.domain, **ids, "groups": groups, "pages": page_ids,
           "repo": "https://github.com/lucas-romeo-org/semantics-governance-workshop"}
    out = ROOT / "app" / "content" / "artifacts.json"
    out.write_text(json.dumps(art, indent=2))
    print(f"wrote {out.relative_to(ROOT)}: {len(groups)} groups, {len(page_ids)} pages, "
          f"{len(ids['dashboards'])} dashboards, {len(ids['jobs'])} jobs")


if __name__ == "__main__":
    main()
