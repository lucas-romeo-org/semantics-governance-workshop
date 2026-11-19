# Spike 8a · Results (19 Nov 2026)

## Identity × access path
| Identity | Metric View (OBO / M2M) | `gold` | DBSQL MCP (Unity Gateway) | Genie One MCP (Unity Gateway) |
|---|---|---|---|---|
| **You** (OBO user token) | ✅ ES, FR, IT, PT | readable (builder) | ✅ 4 regions · 1.2 s | ✅ completed · 28.6 s |
| **Ana** (persona SP) | ✅ ES | ✅ denied | ✅ ES · 1.3 s | ✅ *"the only region you have access to is ES"* · 38.7 s |
| **Pedro** (persona SP) | ✅ PT | ✅ denied | ✅ PT · 1.6 s | ✅ PT only · 43.9 s |
| **Marta** (persona SP) | ✅ 4 regions | ✅ denied | ✅ 4 regions · 1.2 s | ✅ 4 regions · 34.8 s |

## Findings
- **OBO → Unity Gateway MCP works** once the app declares the user scope **`ai-gateway`** (`user_api_scopes: [sql, dashboards.genie, ai-gateway]`). Users re-consent once.
- `iam.current-user:read` and `iam.access-control:read` are default scopes: declaring them explicitly is rejected.
- **DBSQL MCP**: pass `_meta.warehouse_id`. Rows come in `structuredContent.result.data_typed_array[].values[].str`, and column metadata includes the Metric View semantics (display name, synonyms, EUR format).
- **Genie One MCP**: `genie_ask` is asynchronous. Poll `genie_poll_response` (~30–45 s). It found the curated *Retail Sales* Genie Agent by itself and respects the caller's permissions.
- App resources: persona secrets as 6 `secret` resources. The app SP must be added to the warehouse permissions so the bundle doesn't override them.

## Deep-link patterns (validated by clicking)
| Artifact | Pattern |
|---|---|
| Catalog Explorer object | `/explore/data/{catalog}/{schema}/{object}?o={ws}` |
| … tab | `&activeTab=permissions` · `policies` (schema) · `lineage` |
| Discover domain | `/search/discover?q=domain:"{domain}"&o={ws}` |
| Page | `/discover/pages/{page_id}?o={ws}` |
| Genie Agent | `/genie/rooms/{space_id}?o={ws}` |
| Dashboard | `/dashboardsv3/{id}/published?o={ws}` |
| Job | `/jobs/{job_id}?o={ws}` |
| Group | `/settings/workspace/identity-and-access/groups/{id}?o={ws}` |
| ✗ not valid | `/discover/domains/{id}`, `/explore/discover/domains/{id}`, `/pages/{id}` |
