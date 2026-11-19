# Semantic Governance Workshop

**Govern once at the bottom. Expose only semantics at the top.**

A reproducible, hands-on workshop that shows end-to-end semantic layer governance on Databricks. It starts from physically governed Gold tables (ownership, governed tags, RLS/CLS with ABAC) and moves up through Unity Catalog Metric Views, domains, Pages and certification. From there the same governed semantics are served to internal consumers (AI/BI dashboards, Genie Agents, Genie One) and to external ones (Power BI, Tableau, Excel, Claude, ChatGPT and custom agents via MCP).

Everything is synthetic, parameterised and deployable into any workspace.

## The journey (Thesis + 8 steps)

| # | Step | What gets deployed |
|---|---|---|
| 0 | Thesis | Legacy vs certified net sales: the problem in one number |
| 1 | Identity | Account groups (workspace identity proxy), persona service principals |
| 2 | Gold | Catalog/schemas, synthetic retail data, ownership, governed tags |
| 3 | RLS / CLS | Two ABAC policies: row filter by region, PII mask |
| 4 | Metrics | Metric Views (18 measures in sales_metrics + 7 in sales_vs_budget); consumers get `SELECT` on the `semantic` schema (certified Metric Views + one deprecated legacy view kept to show the problem), nothing on gold |
| 5 | Context | Discover domain *Retail Sales*, Pages, certification |
| 6 | Internal | AI/BI dashboard, curated Genie Agent, Genie One |
| 7 | External | Companion app `sgw-companion`: an MCP client with each person's OAuth token (Genie One MCP, DBSQL MCP) |
| 8 | Operate | `ops` views over system tables: who queried what, blocked attempts, lineage, cost |

Build backlog and wave status: [`docs/BUILD_PLAN.md`](docs/BUILD_PLAN.md).

## Quick start

```bash
# 0. Prerequisites: Databricks CLI >= 0.270, Python 3.11+, uv
uv venv .venv && uv pip install -r scripts/requirements.txt

# 1. Authenticate (workspace only; no account console needed)
databricks auth login --host <workspace-url> --profile <ws-profile>

# 2. Preflight (read-only)
.venv/bin/python scripts/preflight.py --profile <ws-profile>

# 3. Deploy wave by wave (see docs/BUILD_PLAN.md)
databricks bundle validate -t sandbox --profile <ws-profile>
databricks bundle deploy   -t sandbox --profile <ws-profile>
```

Deploy order: preflight → w1 identity → `bundle deploy` → run jobs `w2` to `w7` → `python scripts/render_app_artifacts.py` → `bundle deploy` and `bundle run sgw_companion` → `python scripts/smoke_app.py --profile <ws-profile>`. To reset, run `python scripts/teardown.py --profile <ws-profile>` (dry run by default; add `--apply` to delete).

## Repository layout

`databricks.yml` + `resources/` (bundle) · `src/` (code per wave) · `scripts/` (account-level and utility scripts) · `runbooks/` (UI-only steps) · `app/` (companion app) · `docs/`.

## Disclaimer

Sample code for educational purposes. Some features used here are in Preview/Beta; check availability in your region and account.
