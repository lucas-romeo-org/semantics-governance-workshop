# Companion App: Design

> **Status:** design for review (v0.2, 19 Nov 2026: no-npm stack, artifact navigation) · Build = wave 8 in [`BUILD_PLAN.md`](BUILD_PLAN.md)
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
| **Presenter** | The SA delivering the workshop | Keyboard shortcuts (`←/→` steps, `1–8` jump, `V` cycles "View as", `D` toggles depth), larger type |
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
│ Legend · identity colours · claims        ← → steps · 1–8 jump · V view as · D depth │
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
| 7 | **External · Agent console** | Consumers: MCP, App | See §6 | Same question through **Genie One MCP** and **DBSQL MCP**, side by side |
| 8 | **Operate** | Ops band | Audit, lineage, cost, change control | `ops.semantic_activity` for the last hour, including the queries just made from the app |

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
| DBSQL MCP + LLM | User (OBO) or persona SP | Python tool-calling loop with a Foundation Model endpoint; tool = Unity Gateway MCP `system.ai.dbsql` | "Your own agent" pattern |
| Read verify status, artifact metadata | **App service principal** | `CAN_VIEW` on jobs, dashboards and the Genie Agent | Metadata only, never business data |
| "Re-run verify" button | App SP | `CAN_MANAGE_RUN` on the verify jobs | The job itself runs as its owner |

**Hard rule:** no route returns business data queried as the app service principal.
**Grants the app SP needs:** `CAN_USE` warehouse · `READ` on secret scope `sgw` · `CAN_VIEW` / `CAN_MANAGE_RUN` on the `sgw ·` jobs. **No** data grants.

> **To validate first (wave 8a spike):** whether an Apps OBO token can call **Unity Gateway MCP** (`ai-gateway` scope as a `user_api_scope`). If not, the user-identity path for MCP falls back to the Genie Conversation API and the SQL warehouse (still OBO), and the MCP path is shown with persona SPs.

---

## 6. Agent console (step 7, external consumption)

```
┌ ASK ONCE · ANSWER TWICE ─────────────────────────────────────── as: Ana · simulated persona ┐
│ [ What were net sales by region in 2026-Q3 versus budget?        ] [Ask]  presets ▾          │
├────────────────────────────────────────┬────────────────────────────────────────────────────┤
│ GENIE ONE MCP · genie_ask              │ YOUR AGENT · LLM + DBSQL MCP · execute_sql         │
│ Genie reasons over the ontology        │ The agent discovers certified Metric Views,        │
│ (Metric Views, Pages, certification)   │ writes SQL, runs it through MCP                    │
│ ── Answer ─────────────────            │ ── Answer ─────────────────                        │
│ ES 10.97 M€ · 97.4% of budget …        │ ES 10.97 M€ · 97.4% …                              │
│ ── Evidence ── sources: ✓sales_vs_…    │ ── Evidence ── SQL: SELECT region, MEASURE(…)      │
│ ⏱ 7.8 s                                │ ⏱ 5.1 s · 3 tool calls                             │
└────────────────────────────────────────┴────────────────────────────────────────────────────┘
  ① same per-user OAuth  ② same certified semantics  ③ same RLS: Ana sees ES only  ④ audited (→ step 8)
  [Connect this from Claude / ChatGPT ↗]: MCP URL + OAuth steps (runbook)
```

- **Preset questions:** the workshop question, "top 5 customers" (shows masking), "YoY by month" (window measure) and one "trap": *"show me raw rows from gold.fact_sales"*, which gets denied.
- **Evidence first:** the SQL and the sources are always visible, because AI results must be inspectable.
- **Comparison criteria** shown under each answer: latency, tool calls, sources used. Cost is visible later in step 8.

---

## 7. Content model (no hand-copied content)
```
app/
├── content/steps.yaml        # per step: title, problem, concept, takeaway, artifacts[], code[] (repo paths), proof (query key)
├── content/snippets/         # copied at build time from src/** (YAML, SQL) by app/build_content.py
└── config/queries/*.sql      # one file per "live proof" query (Metric Views only)
```
- Artifact IDs (dashboards, Genie Agent, jobs) come from bundle resource references, injected as app env vars: no hard-coded IDs.
- `build_content.py` also inlines the selected Databricks icons, as the reference `build.py` does.

---

## 8. Stack and deployment
**Constraint:** no `npm` on the development machine, so there is **no Node build step anywhere**.

| Layer | Choice | Notes |
|---|---|---|
| Backend | **Python · FastAPI** (`uvicorn`) | `requirements.txt`, installed by Databricks Apps. Runs locally with `uv`. |
| Frontend | **Preact + htm, as native ES modules**: React-style components without JSX and without a bundler | `preact` and `htm` vendored in `app/static/vendor/` (~15 KB, no CDN at runtime). CSS tokens and components ported from the reference template. Charts and diagrams are hand-written SVG components. |
| Identity | OBO: `x-forwarded-access-token` header → `WorkspaceClient(token=…)` per request · Personas: M2M clients from the `sgw` secrets | See §5 |
| MCP | JSON-RPC over HTTPS to the Unity Gateway MCP services (`system.ai.genie_one_mcp`, `system.ai.dbsql`) | Already probed: `genie_ask`, `execute_sql`, `poll_sql_result` |
| "Your agent" | Small Python tool-calling loop: Foundation Model chat endpoint (OpenAI-compatible) + DBSQL MCP tools | ~150 lines, no framework |
| Resources | warehouse `sgw-warehouse` · secret scope `sgw` · Genie Agent · serving endpoint · verify jobs | Declared in the bundle `apps` resource |
| `user_api_scopes` | `sql`, `dashboards.genie`, `iam.current-user:read`, (+ `ai-gateway` if supported) | |
| Deploy | Bundle resource `resources/w8_app.yml` → `databricks bundle deploy` + `bundle run sgw_companion` | App name: `sgw-companion` |

```
app/
├── app.yaml                 # command: uvicorn main:app
├── requirements.txt
├── main.py                  # FastAPI: /api/steps, /api/proof/{step}, /api/ask/{surface}, /api/status
├── sgw/identity.py          # OBO and persona clients
├── sgw/mcp.py               # Unity Gateway MCP JSON-RPC client
├── sgw/agent.py             # LLM + DBSQL MCP loop
├── sgw/links.py             # deep links to real artifacts (built from env + bundle ids)
├── content/steps.yaml       # story per step (title, problem, concept, takeaway, artifacts, proof)
└── static/
    ├── index.html · app.js · styles.css   # Preact + htm components
    ├── vendor/preact.mjs · htm.mjs
    └── icons/                             # Databricks icons inlined by build_content.py
```

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
| 7 External | The Agent console itself · runbook for connecting Claude / ChatGPT |
| 8 Operate | *Governance in action* dashboard · `ops` views · verify job run history · GitHub repo and PRs |

Exact URL patterns (Catalog Explorer tabs, Discover domain, Pages) are confirmed in slice 8a and kept in `sgw/links.py`.

## 10. Build plan (wave 8, in slices)
| Slice | Deliverable | Done when |
|---|---|---|
| **8a · Spike** | Minimal FastAPI app: OBO query on `sales_metrics` + persona switch + one Genie One MCP call + one DBSQL MCP call + deep-link patterns | All four identities return the expected regions; the MCP OBO question is answered (§5) |
| **8b · Shell** | Design system, header, step tabs, persistent map, detail panel, keyboard nav, light/dark | Steps 0–8 navigable with static content from `steps.yaml` |
| **8c · Live proofs** | Proof queries per step, "View as" on steps 2–6, Genie Agent preset | Each step shows its proof for every persona |
| **8d · Agent console** | Step 7 side-by-side Genie One MCP vs agent + DBSQL MCP, evidence panel | Workshop question answered both ways, as Ana and as Marta |
| **8e · Operate + status** | Step 8 activity feed, verify status chips, "re-run verify" | Questions asked in the app appear in `ops.semantic_activity` |
| **8f · Polish** | Presenter mode, motion, empty/error states, smoke test script (Python) | A dry run of the full workshop works end to end |

---

## 11. Out of scope and risks
| Item | Note |
|---|---|
| Write-back / Lakebase | Not needed: read-only app |
| Real external clients (Claude, ChatGPT) inside the app | Covered by a runbook link from step 7 |
| No JS build tooling | Preact + htm as ES modules. Keep components small and plain. |
| OBO → Unity Gateway MCP | Validated in 8a (see §5) |
| Persona SP Genie / MCP usage is billed | Presets only, with a small number of calls |
| Genie One availability for SPs | Validated in 8a. If unsupported, Genie One runs only as *You* (OBO). |
