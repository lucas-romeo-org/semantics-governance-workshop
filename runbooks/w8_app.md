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
| Architecture diagram | One SVG on a fixed grid: corporate identity · Databricks (account groups, OAuth, Unity Catalog gold + semantic, surfaces, endpoints, the companion app, operate) · any external client. Orthogonal connectors in the direction of the request; the active step is drawn in ink, the rest dimmed, with a live packet in the colour of the selected identity. Every block opens the real artifact. |
| View as | **You** (OBO user token) · **Ana / Pedro / Marta** (persona service principals, from the `sgw` secrets). Every result shows a badge with the identity it ran as. |
| Live proof per step | 0 legacy vs certified (+273k€) · 1 identity + groups · 2 read gold (denied) · 3 top customers (PII masked) · 4 net sales by region · 5 certification · 6 Genie Agent question · 7 Agent console · 8 activity feed (`ops`, admins only) |
| Agent chat (step 7) | A real chat ([assistant-ui](https://www.assistant-ui.com) + markdown). The agent is a generic **MCP client**: connect Genie One MCP, DBSQL MCP or both (tools are discovered live with `tools/list`, as the user). Every tool call is a card: server, tool, identity, SQL or Genie's answer, rows or the Unity Catalog error. Streamed from `POST /api/chat` (server-sent events). |
| OBO trace (step 7) | The path of every call, lit live: person → client → token for that person → Unity Gateway MCP → Unity Catalog decides as that person → audited under that name. Plus the MCP URLs any client would use. |
| Verified ✓ | Step rail chips come from the last run of each verify job (app SP: job metadata only) |

## Identity rules (enforced in code)
- Business data is **always** read as the selected identity: OBO, or a persona SP.
- The app SP only reads job status and calls the LLM, which never touches data.

## Why this app is "external" although it runs inside Databricks
The app is deployed on Databricks Apps, but in step 7 it plays the role of any outside client: it calls the **same public
MCP endpoints** (`https://<workspace>/ai-gateway/mcp-services/system.ai.genie_one_mcp` and `…/system.ai.dbsql`) with
**the person's OAuth token** (OBO, forwarded by Databricks Apps; personas use their own M2M token). Claude, ChatGPT or
Cowork do exactly the same after the person signs in with Databricks OAuth (SSO through the corporate IdP). Nothing in the
client knows the rules: Unity Catalog evaluates grants, row filters and masks for that person, and audits the call.

## Demo script (step 7)
1. As **Ana**, pick *Top 5 customers*. The agent calls **Genie One MCP**; names come back `masked`, only ES is visible.
   The OBO trace on the right lights up stage by stage.
2. As **Ana**, pick *Try to read gold*. The agent calls **DBSQL MCP** with `SELECT * FROM gold.fact_sales`;
   **Unity Catalog rejects it** (`INSUFFICIENT_PERMISSIONS`), the trace turns red at the Unity Catalog stage.
3. As **Pedro**, disconnect Genie One and ask *Net sales by region*: the agent writes `MEASURE()` SQL on the Metric View
   and gets **PT only**.
4. Go to step 8: the attempts are in `system.query.history` under each persona's principal, blocked ones included.
   (Note: statements rejected at analysis time can be recorded with `client_application = unknown`, so the surface label
   may read *SQL API* instead of *MCP*.)
