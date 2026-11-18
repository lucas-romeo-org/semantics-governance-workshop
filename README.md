# Semantic Governance Workshop

**Govern once at the bottom. Expose only semantics at the top.**

A reproducible, hands-on workshop that shows end-to-end semantic layer governance on Databricks. It starts from physically governed Gold tables (ownership, governed tags, RLS/CLS with ABAC) and moves up through Unity Catalog Metric Views, domains, Pages and certification. From there the same governed semantics are served to internal consumers (AI/BI dashboards, Genie Agents, Genie One) and to external ones (Power BI, Tableau, Excel, Claude, ChatGPT and custom agents via MCP).

Everything is synthetic, parameterised and deployable into any workspace.

## The journey (9 steps)

| # | Step | What gets deployed |
|---|---|---|
| 1 | Identity | Account groups, persona service principals |
| 2 | Gold | Catalog/schemas, synthetic retail data, ownership, governed tags |
| 3 | RLS / CLS | ABAC row filter and column mask policies |
| 4 | Metrics | Metric Views; consumers get `SELECT` on the semantic schema only |
| 5 | Context | Domains, Pages, certification |
| 6 | Docs | Governed documents, AI Search index, Knowledge Assistant |
| 7 | Internal | AI/BI dashboard, Genie Agent, Genie One |
| 8 | External | Managed MCP, BI connectors, external agents |
| 9 | Operate | Audit / lineage views, CI/CD with workload identity federation |

Build backlog and wave status: [`docs/BUILD_PLAN.md`](docs/BUILD_PLAN.md).

## Quick start

```bash
# 0. Prerequisites: Databricks CLI >= 0.270, Python 3.11+, uv
uv venv .venv && uv pip install -r scripts/requirements.txt

# 1. Authenticate (workspace + account)
databricks auth login --host <workspace-url> --profile <ws-profile>
databricks auth login --host https://accounts.azuredatabricks.net --account-id <account-id> --profile <account-profile>

# 2. Preflight (read-only)
.venv/bin/python scripts/preflight.py --profile <ws-profile>

# 3. Deploy wave by wave (see docs/BUILD_PLAN.md)
databricks bundle validate -t sandbox --profile <ws-profile>
databricks bundle deploy   -t sandbox --profile <ws-profile>
```

## Repository layout

`databricks.yml` + `resources/` (bundle) · `src/` (code per wave) · `scripts/` (account-level and utility scripts) · `runbooks/` (UI-only steps) · `app/` (companion app) · `docs/`.

## Disclaimer

Sample code for educational purposes. Some features used here are in Preview/Beta; check availability in your region and account.
