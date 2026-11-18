# Runbook · Wave 1 · Identity

## What the automation does
`scripts/w1_identity.py` (or the bundle job **sgw · w1 identity setup**) creates, from the workspace and with workspace-admin rights only:

- 9 **account-level** groups `wk_*`, through the workspace identity proxy API (`/api/2.0/identity/groups`), assigned to the workspace with `workspace-access` and `databricks-sql-access`.
- 4 service principals: `sgw-persona-ana`, `sgw-persona-pedro`, `sgw-persona-marta`, `sgw-cicd`.
- Group memberships, the secret scope `sgw` and the persona OAuth secrets.

> ⚠️ Do **not** create the groups through the classic workspace SCIM API or the legacy "workspace-local" option. Unity Catalog cannot resolve workspace-local groups (`PRINCIPAL_DOES_NOT_EXIST`).

```bash
python scripts/w1_identity.py --profile <ws> --apply --verify
# or, from the workspace:
databricks bundle run w1_identity_setup -t <target> --profile <ws>
```

## Optional: real users for live UI demos
Persona service principals cover every automated check. For live demos in Genie One, Discover or access requests, use real identities:

1. Pick 2–3 existing test users from your IdP (Entra ID / Okta), already synced to the account.
2. Add them as direct members: Ana-like → `wk_analysts_es`, Pedro-like → `wk_analysts_pt`, Marta-like → `wk_sales_leads` + `wk_pii_readers`.
3. Alternative for a single presenter: add yourself to `wk_analysts_es`, show the result, move to `wk_analysts_pt`, and repeat. Group changes apply to new queries within about a minute.

## In production
Groups come from the IdP (SCIM or automatic identity management). Never grant to individual users.
