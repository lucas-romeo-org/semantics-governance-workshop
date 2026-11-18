"""Wave 1 · Identity: account-level groups, persona service principals, secret scope.

Runs with ONE workspace profile (workspace admin). No account console access is needed.

Why the "identity proxy" API: Unity Catalog grants and ABAC policies only accept ACCOUNT-level
identities. The classic workspace SCIM API (/api/2.0/preview/scim/v2/Groups) can create
workspace-local groups ('WorkspaceGroup') that Unity Catalog cannot see. The workspace identity
proxy API (/api/2.0/identity/...) creates the group in the account that contains this workspace,
makes the caller its manager and assigns it to this workspace, all from the workspace itself.

Dry-run by default (prints the plan). Use --apply to make changes. Idempotent.

    python scripts/w1_identity.py --profile <ws>                     # plan
    python scripts/w1_identity.py --profile <ws> --apply --verify    # apply + verify

--migrate-local-groups deletes workspace-local groups with the same names (left by an earlier run).
OAuth secrets for persona SPs are written straight into the secret scope, never printed.
"""
import argparse

from databricks.sdk import WorkspaceClient
from databricks.sdk.service import iamv2
from databricks.sdk.service.workspace import AclPermission

ENTS = [iamv2.Entitlement.WORKSPACE_ACCESS, iamv2.Entitlement.DATABRICKS_SQL_ACCESS]


def spec(gp: str, sp: str):
    groups = [f"{gp}platform_admins", f"{gp}data_engineers", f"{gp}security_admins", f"{gp}sales_domain_owners",
              f"{gp}analysts_es", f"{gp}analysts_pt", f"{gp}sales_leads", f"{gp}pii_readers", f"{gp}analysts"]
    nested = {f"{gp}analysts": [f"{gp}analysts_es", f"{gp}analysts_pt", f"{gp}sales_leads"]}
    sps = {
        f"{sp}persona-ana": [f"{gp}analysts_es"],
        f"{sp}persona-pedro": [f"{gp}analysts_pt"],
        f"{sp}persona-marta": [f"{gp}sales_leads", f"{gp}pii_readers"],
        f"{sp}cicd": [f"{gp}data_engineers"],
    }
    caller_groups = [f"{gp}platform_admins", f"{gp}data_engineers", f"{gp}security_admins", f"{gp}sales_domain_owners"]
    personas = [k for k in sps if "persona" in k]
    return groups, nested, sps, caller_groups, personas


def one(it):
    r = list(it)
    return r[0] if r else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", help="workspace CLI profile (workspace admin). Omit when running as a Databricks job.")
    ap.add_argument("--group-prefix", default="wk_")
    ap.add_argument("--sp-prefix", default="sgw-")
    ap.add_argument("--secret-scope", default="sgw")
    ap.add_argument("--migrate-local-groups", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()

    w = WorkspaceClient(profile=args.profile) if args.profile else WorkspaceClient()
    idp = w.workspace_iam_v2
    me = w.current_user.me()
    groups, nested, sps, caller_groups, personas = spec(args.group_prefix, args.sp_prefix)
    do = args.apply
    tag = "APPLY" if do else "PLAN "
    print(f"Workspace {w.get_workspace_id()} · caller {me.user_name}\n")

    # 0. legacy workspace-local groups with the same names
    for name in groups:
        local = one(w.groups.list(filter=f'displayName eq "{name}"', attributes="id,displayName,meta"))
        if local and local.meta and local.meta.resource_type == "WorkspaceGroup":
            print(f"[{tag}] - workspace-local group {name} (invisible to Unity Catalog)"
                  + ("" if args.migrate_local_groups else "  [kept: pass --migrate-local-groups]"))
            if do and args.migrate_local_groups:
                w.groups.delete(local.id)

    # 1. account groups via the workspace identity proxy
    gids = {}
    for name in groups:
        g = next((x for x in idp.list_groups_proxy(filter=f'group_name eq "{name}"') if x.group_name == name), None)
        if g:
            gids[name] = int(g.group_id)
            print(f"  = account group {name} exists ({g.group_id})")
        else:
            print(f"[{tag}] + account group {name}")
            if do:
                gids[name] = int(idp.create_group_proxy(iamv2.Group(group_name=name)).group_id)

    # 2. workspace assignment + entitlements for every group
    for name in groups:
        gid = gids.get(name)
        current = None
        if gid:
            try:
                current = idp.get_workspace_assignment_proxy(f"workspace-assignments/{gid}")
            except Exception:  # noqa: BLE001 - not assigned yet
                current = None
        if current:
            print(f"  = {name} assigned to workspace")
            continue
        print(f"[{tag}] + assign {name} to workspace (workspace-access, databricks-sql-access)")
        if do:
            try:
                idp.create_workspace_assignment_proxy(iamv2.WorkspaceAssignment(principal_id=gid, entitlements=ENTS))
            except Exception as e:  # noqa: BLE001 - the get above can be eventually consistent
                if "already" not in str(e).lower():
                    raise
                print(f"    (already assigned)")

    # 3. service principals (account-level identities when created from an identity-federated workspace)
    spids, spapp = {}, {}
    for name in sps:
        s = one(w.service_principals.list(filter=f'displayName eq "{name}"'))
        if s:
            spids[name], spapp[name] = int(s.id), s.application_id
            print(f"  = service principal {name} exists ({s.application_id})")
        else:
            print(f"[{tag}] + service principal {name}")
            if do:
                s = w.service_principals.create(display_name=name, active=True)
                spids[name], spapp[name] = int(s.id), s.application_id

    # 4. memberships
    def ensure_member(group, member_id, label):
        gid = gids.get(group)
        if gid and member_id:
            have = {m.principal_id for m in idp.list_direct_group_members_proxy(f"groups/{gid}")}
            if member_id in have:
                print(f"  = {label} already in {group}")
                return
        print(f"[{tag}] + {label} -> {group}")
        if do:
            idp.create_direct_group_member_proxy(f"groups/{gids[group]}", iamv2.DirectGroupMember(principal_id=member_id))

    for parent, children in nested.items():
        for c in children:
            ensure_member(parent, gids.get(c), f"group {c}")
    for name, gs in sps.items():
        for g in gs:
            ensure_member(g, spids.get(name), f"sp {name}")
    for g in caller_groups:
        ensure_member(g, int(me.id), f"user {me.user_name}")

    # 5. secret scope + persona OAuth secrets (values never printed)
    scopes = {s.name for s in w.secrets.list_scopes()}
    if args.secret_scope not in scopes:
        print(f"[{tag}] + secret scope {args.secret_scope}")
        if do:
            w.secrets.create_scope(scope=args.secret_scope)
            scopes.add(args.secret_scope)
    else:
        print(f"  = secret scope {args.secret_scope} exists")
    existing = {k.key for k in w.secrets.list_secrets(args.secret_scope)} if args.secret_scope in scopes else set()
    for name in personas:
        short = name.replace(args.sp_prefix, "")
        k_id, k_sec = f"{short}-client-id", f"{short}-client-secret"
        if k_sec in existing:
            print(f"  = secret {args.secret_scope}/{k_sec} exists")
            continue
        print(f"[{tag}] + OAuth secret for {name} -> {args.secret_scope}/{k_id}, {k_sec}")
        if do:
            sec = w.service_principal_secrets_proxy.create(service_principal_id=str(spids[name]))
            w.secrets.put_secret(args.secret_scope, k_id, string_value=spapp[name])
            w.secrets.put_secret(args.secret_scope, k_sec, string_value=sec.secret)
    print(f"[{tag}] ~ ACL MANAGE on scope {args.secret_scope} -> {args.group_prefix}platform_admins")
    if do and gids.get(f"{args.group_prefix}platform_admins"):
        w.secrets.put_acl(args.secret_scope, f"{args.group_prefix}platform_admins", AclPermission.MANAGE)

    if args.verify:
        print("\nVERIFY (Unity Catalog must resolve every principal)")
        wh = next((x.id for x in w.warehouses.list() if x.enable_serverless_compute), None)
        principals = list(groups) + [spapp[n] for n in sps if n in spapp]
        for p in principals:
            r = w.statement_execution.execute_statement(warehouse_id=wh, statement=f"SHOW GRANTS `{p}` ON METASTORE", wait_timeout="50s")
            ok = r.status.error is None
            print(f"  {'✓' if ok else '✗'} {p}" + ("" if ok else f": {r.status.error.message[:90]}"))
        for name in groups:
            if name in gids:
                mem = [m.display_name or str(m.principal_id) for m in idp.list_direct_group_members_proxy(f"groups/{gids[name]}")]
                print(f"    {name}: {', '.join(sorted(mem)) or '(no members)'}")

    print("\nDone." if do else "\nDry run only. Re-run with --apply to make these changes.")


if __name__ == "__main__":
    main()
