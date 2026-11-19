# Companion App: Design

> **Status:** v0.4 (19 Nov 2026): built and deployed (wave 8, slices 8a–8f). FastAPI backend + React/Vite frontend built by Databricks Apps at deploy time; app-first UX (visual, little text) · Build = wave 8 in [`BUILD_PLAN.md`](BUILD_PLAN.md)
> **Working name:** `sgw-companion` (Databricks App)

---

## 1. Purpose

One place to **deliver and follow the workshop linearly**: every step's idea, its artifacts, its code and its live proof. No more jumping between Catalog Explorer, notebooks, dashboards and Genie.

The app is also **the external consumer of step 7**. It reaches the governed semantics through the **same MCP endpoints and the same per-user OAuth** that Claude, ChatGPT or a custom agent would use.

### Design principles
| Principle | Consequence |
|---|---|
| **One map, eight steps** | The same layer map and step tracker as the executive deck. The current step is always highlighted. |
| **Explain first, then prove** | Each step shows the concept, then the *live* evidence (query results, verify status) from the real workspace. |
| **Identity is always visible** | Every result carries a badge saying who it ran as (*you* / *Ana* / *Pedro* / *Marta*). The app never shows data queried with its own service principal. |
| **Navigate the real thing** | Every node of the map and every artifact chip opens the **real object** in the workspace (Catalog Explorer, Discover, dashboards, Genie, jobs, notebooks) or the file in GitHub |
| **The repo is the source of truth** | Step text, code snippets and artifact IDs come from the repo and the bundle. Nothing is duplicated by hand. |
| **Presenter-friendly** | Keyboard navigation, large type, and works without network detours. Every screen still makes sense when read alone. |

---

## 2. Audiences and modes
| Mode | Who | What changes |
|---|---|---|
| **Presenter** (`P`) | The SA delivering the workshop | Larger type and keyboard navigation (`←/→` steps, `0–8` jump, `V` cycles "View as", `D` toggles depth) |
| **Builder** (`B`, off by default) | Attendees who want the code behind each step | A `</>` tab per block; "Built with" per step: notebooks, scripts, bundle YAML and runbooks (GitHub and workspace), plus the step's job |
| **Self-guided** | Attendees after the session, or customer teams | Same content. "Open in workspace" links are emphasised. |

**Depth toggle** (from the reference template): **Basic** shows the story and the result. **Deep** adds code, grants, policy SQL and system-table evidence.

---

## 3. Information architecture

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ ▣ Databricks · SEMANTIC GOVERNANCE WORKSHOP      View as: [You][Ana][Pedro][Marta]  ◐ │
├──────────────────────────────────────────────────────────────────────────────────────┤
│ [0 Thesis][1 Identity][2 Gold][3 RLS/CLS][4 Metrics][5 Context][6 Internal][7 External][8 Operate] │
├───────────────────────────────────────────────┬──────────────────────────────────────┤
│  MAP (persistent, current layer highlighted)  │  DETAIL PANEL                        │
│  ┌ IDENTITY ┐ ┌ GOLD · locked ┐ ┌ SEMANTIC ┐   │  STEP 3 · RLS / CLS                  │
│  │ groups   │→│ tags · ABAC  │→│ metric   │→ ┌ CONSUMERS ┐   │  Problem · Concept · Takeaway        │
│  │ personas │ │ policies     │ │ views    │  │ dash·genie│   │  ── Live proof ──                    │
│  └──────────┘ └──────────────┘ └──────────┘  │ app · MCP │   │  [same query → result as Ana]        │
│                                               └───────────┘   │  ── Artifacts ──  (open ↗)           │
│                                                               │  ── Code ── (Deep)                   │
├───────────────────────────────────────────────┴──────────────────────────────────────┤
│ Legend · identity colours · claims        ← → steps · 0–8 jump · V view as · D depth │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Screens
| # | Screen | Map highlight | Detail panel content | Live proof |
|---|---|---|---|---|
| 0 | **Thesis** | whole map | The problem (N tools × logic × security), "govern once, expose semantics", the question and the 3 people | Legacy vs governed net sales, ES Sep-2026: +273k€ difference |
| 1 | **Identity** | Identity zone | Account groups by role, personas, "grant to groups" | Group membership of the selected persona |
| 2 | **Gold** | Gold zone | Catalog layout, owners, governed tags, segregation of duties | "View as" persona → `SELECT` on `gold` → **denied** |
| 3 | **RLS / CLS** | Gold → policies | The 2 ABAC policies (SQL in Deep) | Same query on the region-scoped data: rows and masks change with "View as" (via Metric View; see §5) |
| 4 | **Metrics** | Semantic zone | YAML excerpt, measure catalogue (atomic / filtered / composed / window / LOD), exposure pattern | KPI tiles + YoY chart from `sales_metrics` as the selected identity |
| 5 | **Context** | Semantic → Discover | Domain, certification, Pages | Certification badges + the *Net Sales* Page (read live) |
| 6 | **Internal** | Consumers: Dashboard, Genie | Dashboard + Genie Agent | Embedded links. "Ask the Genie Agent" with one preset question as the selected identity |
| 7 | **External · Agent chat** | Consumers: MCP, App | See §6 | Chat over **Genie One MCP** and/or **DBSQL MCP**, as the selected identity; tool-call cards and a live OBO trace |
| 8 | **Operate** | Ops band | Who queried what and from which surface, blocked attempts, lineage, cost | `ops` views: `semantic_activity` for the last hour, including the queries just made from the app |

The **closing moment** on screen 8: the questions asked in the app a minute ago show up attributed to the real person, from surface *Databricks App* / *MCP*.

---

## 4. Visual language
Based on the *Built-on Apps Architecture* reference (`src/template.html`). It is the same family, not a copy.

| Element | Spec |
|---|---|
| Tokens | `--bg #F9F7F4` · `--surface #FFF` · `--zone #F3F1EC` · `--zone-dbx #FBEFEC` · `--ink #0B2026` · `--muted #5A6F77` · `--line #DCE0E2` · `--accent #FF3621`. Dark theme: `--bg #0B2026`, `--surface #122A31`. |
| Identity colours | **You** `--id-user #2272B4` · **Ana / Pedro** `--id-entry #AB4057` · **Marta** `--id-exec #00875C` · app SP `--id-cred #618794` (status only) |
| Type | DM Sans (UI) · DM Mono (eyebrows, labels on connectors, code, chips) · eyebrow = 11px mono, uppercase, letter-spaced |
| Building blocks | **Zones** (rounded panels with a mono caption) · **node cards** (icon + title + mono subtitle) · **connectors** with mono labels (`SELECT`, `owner rights`, `as user`) · **chips** · **detail panel** with key/value rows |
| Status chips | `VERIFIED` (green, the last verify run is green) · `MANUAL` (amber, runbook step) · `DENIED` (red, shown for blocked attempts) |
| Icons | Inlined at build time from `Databricks-selected-assets` (navy → `currentColor`), as in the reference `build.py`: Unity Catalog, Genie, Apps, Unity Gateway, Domains, Certified, Users, Key, Dashboard |
| Motion | Only on step change: the active zone fades in, and connectors draw left → right (≤ 400 ms). Respects `prefers-reduced-motion`. |

---

## 5. Identity model (critical)

Every server call has **exactly one** identity, decided per route:

| Action | Runs as | Mechanism | Why |
|---|---|---|---|
| Query data, **View as = You** | **Logged-in user** | Apps user authorization (OBO), scope `sql` | RLS/CLS follow the real person |
| Query data, **View as = Ana/Pedro/Marta** | **Persona service principal** | App reads `sgw/persona-*` secrets (secret resource) → M2M client | Reproducible demo without real test users. Labelled **"simulated persona"**. |
| Genie Agent question | User (OBO, `dashboards.genie`) or persona SP | Genie Conversation API | Same rule |
| Genie One MCP | User (OBO) or persona SP | Unity Gateway MCP `system.ai.genie_one_mcp`, `genie_ask` | External-consumer pattern |
| Agent chat (step 7) | User (OBO) or persona SP, per tool call | Tool-calling loop: the LLM (Foundation Model, runs as the app SP) picks tools discovered with `tools/list` on Unity Gateway MCP `system.ai.genie_one_mcp` and/or `system.ai.dbsql` | "Your own agent" pattern; the LLM never reads data |
| Read verify status, artifact metadata | **App service principal** | `CAN_VIEW` on jobs, dashboards and the Genie Agent | Metadata only, never business data |
| "Re-run verify" button | App SP | `CAN_MANAGE_RUN` on the verify jobs | The job itself runs as its owner |

**Hard rule:** no route returns business data queried as the app service principal.
**Grants the app SP needs:** `CAN_USE` warehouse · `READ` on secret scope `sgw` · `CAN_VIEW` / `CAN_MANAGE_RUN` on the `sgw ·` jobs · `CAN_QUERY` on the LLM endpoint. **No** data grants.

> ✅ **Validated in spike 8a** ([results](spike-8a.md)): OBO → Unity Gateway MCP works with the user scope `ai-gateway` (`user_api_scopes: [sql, dashboards.genie, ai-gateway]`). Users consent once. `iam.current-user:read` and `iam.access-control:read` are default scopes and must not be declared.

---

## 6. Agent chat (step 7, external consumption)

The app is a generic **MCP client**, the same kind of client as Claude or ChatGPT. It discovers the tools of each MCP server live (`tools/list`) and runs every call as the selected identity. The app implements no rules: Unity Catalog decides.

```
┌ AGENT CHAT · as: Ana · simulated persona ─────────────────────────────┐
│ [ question …                                        ] [Send]          │
│ presets: Net sales by region · Top 5 customers · Year over year · Try to read gold │
│ MCP: ☑ Genie One MCP   ☑ DBSQL MCP            (tools via tools/list)    │
├──────────────────────────────────────────────────────────────────────┤
│ ▣ tool call card · server · tool · identity · SQL or Genie answer · rows or UC error │
├──────────────────────────────────────────────────────────────────────┤
│ ON BEHALF OF THE USER: person → client → token for that person →      │
│ Unity Gateway MCP → Unity Catalog decides → audited under that name   │
└──────────────────────────────────────────────────────────────────────┘
```

- **Transport:** the answer streams from `POST /api/chat` (server-sent events). Each tool call becomes a card: server, tool, identity, the SQL or Genie's answer, and the rows or the Unity Catalog error.
- **Presets:** *Net sales by region* (certified Metric View), *Top 5 customers* (masking decided by the policy), *Year over year* (window measure) and the trap *Try to read gold* (`SELECT * FROM gold.fact_sales`, rejected with `INSUFFICIENT_PERMISSIONS`).
- **Evidence first:** the SQL and the sources are always visible, because AI results must be inspectable.
- **Agent LLM:** Foundation Model `databricks-claude-sonnet-5-5`, running as the app service principal. It chooses tools and writes the answer; it never reads data. Only MCP tool calls reach data, and they run as the person.
- **OBO trace panel:** lights up stage by stage for each call, and shows the MCP URLs that any client would use.

## 7. Content model (no hand-copied content)
```
app/
├── content/steps.json      # the 9 steps (0–8): title, problem, concept, takeaway, artifacts, proof key
├── content/sources.json    # "Built with" sources per step: notebooks, scripts, bundle YAML, runbooks
└── content/artifacts.json  # generated before deploy by scripts/render_app_artifacts.py (gitignored)
```
- Artifact IDs (dashboards, Genie Agent, jobs, groups, domains, Pages) come from the workspace, resolved into `artifacts.json`, and from bundle resource references injected as app env vars (`valueFrom` in `app/app.yaml`). No hard-coded IDs.
- `render_app_artifacts.py` also records the workspace object ids of the bundle files, so the builder view can link each file. GitHub links point to the public repo.

## 8. Stack and deployment
**Constraint:** no `npm` on the development machine. **Solution:** Databricks Apps builds the frontend at deploy time. With a `package.json` present, the runtime runs `npm install` → `pip install -r requirements.txt` → `npm run build` → the `app.yaml` command (`python main.py`).

| Layer | Choice | Notes |
|---|---|---|
| Frontend | **React 18 + Vite (JSX)** · `lucide-react` icons · `@assistant-ui/react` chat with `react-markdown` | Built in the Apps container. Output goes to `app/dist/`, served by FastAPI. |
| Backend | **Python · FastAPI** | `/api/info`, `/api/steps`, `/api/proof/{key}`, `/api/status`, `/api/sources`, `/api/mcp/tools`, `/api/chat` (SSE). Serves `dist/` for every other path. |
| Identity | OBO (`x-forwarded-access-token`) · persona service principals (M2M from `sgw` secrets) | Validated in spike 8a |
| MCP client | Unity Gateway `system.ai.genie_one_mcp` and `system.ai.dbsql` (JSON-RPC: `tools/list`, `tools/call`) | User scope `ai-gateway`; warehouse passed as `_meta.warehouse_id` |
| Agent LLM | Foundation Model `databricks-claude-sonnet-5-5` (`CAN_QUERY` for the app SP) | Runs as the app SP. Never reads data. |
| Artifact IDs | `scripts/render_app_artifacts.py` resolves them into `app/content/artifacts.json` before deploy | gitignored: workspace-specific, kept out of the public repo |

```
app/
├── app.yaml · requirements.txt · package.json · vite.config.js · index.html
├── main.py                      # FastAPI (API + serves dist/)
├── sgw/  identity.py · mcp.py · agent.py · proofs.py · links.py
├── content/  steps.json · sources.json · artifacts.json (generated)
└── frontend/  main.jsx · App.jsx · api.js · trace.js · styles.css
    └── components/  TopBar · StepRail · StepPanel · Diagram (SVG) · Proof · AgentChat · ExternalStage · OboTrace · ErrorBoundary
```

### UX rules (it's an app, not a document)
- **One step = one visual + one sentence + max 3 short points.** Everything else lives behind **Deep**.
- **Step rail and map are always visible.** Each step has one SVG architecture diagram on a fixed grid: the active block is drawn in ink, the rest dimmed, and a live packet takes the colour of the selected identity. Every block opens the real artifact.
- **Proof before prose:** every step shows a live result as the selected identity; the step rail shows ✓ chips from the last run of each step's verify job.
- **Navigation:** step rail (click), `←/→`, `0–8`, `V` (view as), `D` (deep), `T` (theme), `B` (builder view), `P` (presenter mode).
- **Builder view** (`B`, off by default): a `</>` tab per block, and a "Built with" section per step linking notebooks, scripts, bundle YAML and runbooks on GitHub and in the workspace, plus the step's job.
- **Error boundaries** per step and per panel: a failing block shows its error without taking the page down.

## 9. Artifact navigation (the real objects, per step)
Every map node and every artifact chip is a deep link. URLs are built from the workspace host plus IDs injected from the bundle (dashboards, Genie Agent, jobs) or from UC names.

| Step | Opens |
|---|---|
| 1 Identity | Groups `wk_*` and service principals (*Settings → Identity and access*) · job *sgw · w1 identity setup* |
| 2 Gold | `sgw_shop` and each table in Catalog Explorer (*Overview*, *Permissions*, tags) · wave 2 notebooks |
| 3 RLS/CLS | Schema `gold` → *Policies* · functions in `governance` · policy notebook |
| 4 Metrics | `sales_metrics`, `sales_vs_budget_metrics` (definition, *Lineage*) · YAML on GitHub |
| 5 Context | Domain *Retail Sales* in Discover · the 5 Pages · the deprecated legacy view |
| 6 Internal | Published *Retail Sales Performance* dashboard · *Retail Sales* Genie Agent |
| 7 External | The agent chat itself · the MCP endpoints shown in the trace panel |
| 8 Operate | *Governance in action* dashboard · `ops` views · verify job run history · GitHub repo and PRs |

URL patterns were validated in spike 8a ([results](spike-8a.md)) and live in `app/sgw/links.py`.

## 10. Build plan (wave 8, in slices)
All slices are done.

| Slice | Deliverable | Status |
|---|---|---|
| **8a · Spike** | FastAPI app: OBO query on `sales_metrics`, persona switch, one Genie One MCP call, one DBSQL MCP call, deep-link patterns | ✅ Done. All four identities returned the expected regions; OBO → Unity Gateway MCP confirmed (§5, [results](spike-8a.md)) |
| **8b · Shell** | Design system, header, step tabs, persistent map, detail panel, keyboard nav, light/dark | ✅ Done |
| **8c · Live proofs** | Proof per step, "View as" on every step, each proof run as the selected identity | ✅ Done |
| **8d · Agent chat** | Step 7: chat over Genie One MCP and/or DBSQL MCP as the selected identity, tool-call cards, live OBO trace | ✅ Done (replaces the side-by-side console planned in v0.3) |
| **8e · Operate + status** | Step 8 activity feed from the `ops` views, verify chips per step | ✅ Done |
| **8f · Polish** | Presenter mode, builder view, one SVG architecture diagram per step, error boundaries, `scripts/smoke_app.py` | ✅ Done |

Smoke test: `python scripts/smoke_app.py --profile <ws>` checks the API, the per-persona governance results and the chat over DBSQL MCP.

## 11. Out of scope and risks
| Item | Note |
|---|---|
| Write-back / Lakebase | Not needed: read-only app |
| Claude / ChatGPT inside the app | Not embedded. They are external MCP clients of the same endpoints; the MCP URLs are shown in the trace panel |
| Local npm | Not needed: the frontend is built by Databricks Apps at deploy time |
| OBO → Unity Gateway MCP | Validated in 8a (see §5) |
| Persona SP usage is billed | Persona SPs run SQL and Genie calls; keep demo usage small |
| Genie One availability for SPs | Validated in 8a. If unsupported, Genie One runs only as *You* (OBO). |
| Unstructured documents | Removed from scope: the *Serverless Access Controls* preview (`USAGE_POLICY_PREVIEW_ENABLED`) blocks volumes for Genie Agents |
| Operate labels | Statements rejected at analysis time can be recorded with `client_application = unknown`, so step 8 may show *SQL API* instead of *MCP* |
