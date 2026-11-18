"""Wave 1 · Identity: groups, persona service principals, secret scope.

Uses ONLY a workspace profile with workspace-admin rights. In an identity-federated workspace,
groups and service principals created by a workspace admin are account-level identities
(usable in Unity Catalog grants and ABAC policies) and are assigned to this workspace.

Dry-run by default (prints the plan). Use --apply to make changes. Idempotent.

    python scripts/w1_identity.py --profile <ws>            # plan
    python scripts/w1_identity.py --profile <ws> --apply    # apply
    python scripts/w1_identity.py --profile <ws> --verify   # report

Secrets: OAuth secrets for persona SPs are created through the workspace proxy API and written
straight into the secret scope. They are never printed or written to disk.
"""
import argparse

from databricks.sdk import WorkspaceClient
from databricks.sdk.service import iam
from databricks.sdk.service.workspace import AclPermission


def spec(gp: str, sp: str):
    groups = {
        f"{gp}platform_admins": "Platform team: identity, previews, warehouses, Unity Gateway",
        f"{gp}data_engineers": "Builders: own Gold and the Metric Views",
        f"{gp}security_admins": "Own governed tags and ABAC policies",
        f"{gp}sales_domain_owners": "Sales domain owners / stewards: certify, curate, approve access",
        f"{gp}analysts_es": "Analysts · Spain",
        f"{gp}analysts_pt": "Analysts · Portugal",
        f"{gp}sales_leads": "Global sales leads · all regions",
        f"{gp}pii_readers": "Allowed to see customer PII in clear",
        f"{gp}analysts": "Umbrella consumer group (es + pt + leads)",
    }
    nested = {f"{gp}analysts": [f"{gp}analysts_es", f"{gp}analysts_pt", f"{gp}sales_leads"]}
    sps = {
        f"{sp}persona-ana": [f"{gp}analysts_es"],
        f"{sp}persona-pedro": [f"{gp}analysts_pt"],
        f"{sp}persona-marta": [f"{gp}sales_leads", f"{gp}pii_readers"],
        f"{sp}cicd": [f"{gp}data_engineers"],
    }
    caller_groups = [f"{gp}platform_admins", f"{gp}data_engineers", f"{gp}security_admins", f"{gp}sales_domain_owners"]
    consumer_groups = [f"{gp}analysts_es", f"{gp}analysts_pt", f"{gp}sales_leads", f"{gp}pii_readers", f"{gp}analysts"]
    personas = [k for k in sps if "persona" in k]
    return groups, nested, sps, caller_groups, consumer_groups, personas


def one(it):
    r = list(it)
    return r[0] if r else None


def members_of(w, gid):
    return {m.value for m in (w.groups.get(gid).members or [])}


def add_member(w, gid, member_id):
    w.groups.patch(gid, operations=[iam.Patch(op=iam.PatchOp.ADD, path="members", value=[{"value": member_id}])],
                   schemas=[iam.PatchSchema.URN_IETF_PARAMS_SCIM_API_MESSAGES_2_0_PATCH_OP])


def add_entitlements(w, gid, ents):
    w.groups.patch(gid, operations=[iam.Patch(op=iam.PatchOp.ADD, path="entitlements", value=[{"value": e} for e in ents])],
                   schemas=[iam.PatchSchema.URN_IETF_PARAMS_SCIM_API_MESSAGES_2_0_PATCH_OP])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True, help="workspace CLI profile (workspace admin)")
    ap.add_argument("--group-prefix", default="wk_")
    ap.add_argument("--sp-prefix", default="sgw-")
    ap.add_argument("--secret-scope", default="sgw")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()

    w = WorkspaceClient(profile=args.profile)
    me = w.current_user.me()
    groups, nested, sps, caller_groups, consumer_groups, personas = spec(args.group_prefix, args.sp_prefix)
    do = args.apply
    tag = "APPLY" if do else "PLAN "
    print(f"Workspace {w.get_workspace_id()} · caller {me.user_name}\n")

    # 1. groups
    gids = {}
    for name, desc in groups.items():
        g = one(w.groups.list(filter=f'displayName eq "{name}"', attributes="id,displayName,meta"))
        if g:
            gids[name] = g.id
            kind = getattr(g.meta, "resource_type", "?") if g.meta else "?"
            print(f"  = group {name} exists ({kind})")
        else:
            print(f"[{tag}] + group {name}  ({desc})")
            if do:
                gids[name] = w.groups.create(display_name=name).id

    # 2. service principals
    spids, spapp = {}, {}
    for name in sps:
        s = one(w.service_principals.list(filter=f'displayName eq "{name}"'))
        if s:
            spids[name], spapp[name] = s.id, s.application_id
            print(f"  = service principal {name} exists ({s.application_id})")
        else:
            print(f"[{tag}] + service principal {name}")
            if do:
                s = w.service_principals.create(display_name=name, active=True)
                spids[name], spapp[name] = s.id, s.application_id

    # 3. memberships
    def ensure_member(group, member_id, label):
        gid = gids.get(group)
        if gid and member_id and member_id in members_of(w, gid):
            print(f"  = {label} already in {group}")
            return
        print(f"[{tag}] + {label} -> {group}")
        if do:
            add_member(w, gids[group], member_id)

    for parent, children in nested.items():
        for c in children:
            ensure_member(parent, gids.get(c), f"group {c}")
    for name, gs in sps.items():
        for g in gs:
            ensure_member(g, spids.get(name), f"sp {name}")
    for g in caller_groups:
        ensure_member(g, me.id, f"user {me.user_name}")

    # 4. entitlements for consumers (Databricks SQL + workspace access)
    for g in consumer_groups:
        print(f"[{tag}] ~ entitlements workspace-access, databricks-sql-access -> {g}")
        if do:
            add_entitlements(w, gids[g], ["workspace-access", "databricks-sql-access"])

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
            sec = w.service_principal_secrets_proxy.create(service_principal_id=spids[name])
            w.secrets.put_secret(args.secret_scope, k_id, string_value=spapp[name])
            w.secrets.put_secret(args.secret_scope, k_sec, string_value=sec.secret)
    print(f"[{tag}] ~ ACL MANAGE on scope {args.secret_scope} -> {args.group_prefix}platform_admins")
    if do:
        w.secrets.put_acl(args.secret_scope, f"{args.group_prefix}platform_admins", AclPermission.MANAGE)

    if args.verify:
        print("\nVERIFY")
        for name in groups:
            g = one(w.groups.list(filter=f'displayName eq "{name}"', attributes="id,displayName,meta,members,entitlements"))
            if not g:
                print(f"  ✗ {name} missing")
                continue
            full = w.groups.get(g.id)
            mem = ", ".join(sorted(m.display or m.value for m in (full.members or []))) or "(no members)"
            ents = ",".join(e.value for e in (full.entitlements or []))
            kind = getattr(full.meta, "resource_type", "?") if full.meta else "?"
            print(f"  ✓ {name} [{kind}] members: {mem}" + (f" · entitlements: {ents}" if ents else ""))
        keys = sorted(k.key for k in w.secrets.list_secrets(args.secret_scope)) if args.secret_scope in scopes else []
        print(f"  ✓ secret scope {args.secret_scope}: {keys}")

    print("\nDone." if do else "\nDry run only. Re-run with --apply to make these changes.")


if __name__ == "__main__":
    main()
