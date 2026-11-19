# Runbook · Wave 8 · Companion app (`sgw-companion`)

FastAPI backend + React/Vite frontend. **No local npm needed:** Databricks Apps runs `npm install` → `pip install` → `npm run build` at deploy time.

## Deploy
```bash
python scripts/render_app_artifacts.py --profile <ws>      # real ids → app/content/artifacts.json (gitignored)
databricks bundle deploy -t <target> --profile <ws>
databricks bundle run sgw_companion -t <target> --profile <ws>
```
The first time you open the app, approve the requested permissions: `sql`, `dashboards.genie`, `ai-gateway`.

## What the app does
| Area | Detail |
|---|---|
| Architecture diagram | Zones (outside, Databricks, Unity Catalog with gold and semantic, consumers, external clients) with labelled connectors. The active step lights up its nodes and edges, and the flow is animated in the colour of the selected identity. Every node opens the real artifact. |
| View as | **You** (OBO user token) · **Ana / Pedro / Marta** (persona service principals, from the `sgw` secrets). Every result shows a badge with the identity it ran as. |
| Live proof per step | 0 legacy vs certified (+273k€) · 1 identity + groups · 2 read gold (denied) · 3 top customers (PII masked) · 4 net sales by region · 5 certification · 6 Genie Agent question · 7 Agent console · 8 activity feed (`ops`, admins only) |
| Agent console (step 7) | Same question through **Genie One MCP** and through **"your agent"**: an LLM (`databricks-claude-sonnet-5-5`, running as the app) that writes SQL on the certified Metric Views and runs it through **DBSQL MCP as the user**. |
| Verified ✓ | Step rail chips come from the last run of each verify job (app SP: job metadata only) |

## Identity rules (enforced in code)
- Business data is **always** read as the selected identity: OBO, or a persona SP.
- The app SP only reads job status and calls the LLM, which never touches data.

## Demo script (step 7)
1. As **Ana**, ask *"Who are the top 5 customers…"*. Both lanes answer, with names `•••• masked`.
2. As **Ana**, ask *"Show me raw rows from gold.fact_sales"*. The agent tries it and **Unity Catalog rejects it**: security lives in the platform, not in the prompt.
3. Go to step 8: the attempts show up attributed to Ana, surface *Genie* / *MCP*, marked **blocked**.
