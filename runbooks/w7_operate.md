# Runbook · Wave 7 · Operate (workshop step 8)

```bash
databricks bundle run w7_operate -t <target> --profile <ws>
python scripts/show_verify.py --profile <ws> --job "sgw · w7 operate"
```

## What gets created (schema `ops`, owned by `wk_platform_admins`)
| Object | Answers |
|---|---|
| `ops.principals` | Readable names for service principal ids (`sgw-persona-ana` instead of a UUID) |
| `ops.semantic_activity` | Who queried what, from which surface (Genie, dashboard, app, MCP, SQL API, CLI) and which layer (semantic / gold), with the result |
| `ops.blocked_attempts` | Queries rejected by Unity Catalog permissions (consumers trying to read `gold`) |
| `ops.lineage` | Gold → Metric Views → consumers (from `system.access.table_lineage`) |
| `ops.workshop_cost` | DBUs of the workshop warehouse and jobs (tag `project = semantics-governance-workshop`) |
| Dashboard **Governance in action** | KPIs, queries by surface × layer, who-queried-what, blocked attempts, lineage |

The views read system tables with the owner's rights. `wk_security_admins` gets `SELECT` on `ops`.

## Verified result (sandbox)
```
✅ ana / pedro / marta queries on the semantic layer are attributed to them
✅ activity from several surfaces: CLI, Genie, SQL API
✅ Ana's attempts to read gold are recorded as blocked (INSUFFICIENT_PERMISSIONS)
✅ lineage gold.fact_sales → semantic.sales_metrics
✅ workshop cost measured
```
`query.history` takes a few minutes to show new queries, and `billing.usage` can take a few hours.

## Change control: "changing a KPI = a pull request" (live demo)
1. Create a branch and edit `src/w4_semantic/sales_metrics.yaml`, for example add a synonym or a new measure.
2. Open a PR. CI runs `bundle validate` (`.github/workflows/validate.yml`).
3. A builder and the domain owner review it, then it is merged.
4. Deploy with `databricks bundle deploy` + `databricks bundle run w4_semantic`, then `w5_context` to re-certify.

> **Future (not in this workshop):** CD from GitHub Actions without secrets, through workload identity federation. It needs an *account-level* service principal federation policy, which is out of scope here on purpose (no account-console access).
