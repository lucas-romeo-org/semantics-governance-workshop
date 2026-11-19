# Build Plan — Semantic Governance Workshop

> What we deploy, concretely, and in which order. Each **wave** is developed, deployed and verified on its own before the next one starts.
> Companion docs: [`design/WORKSHOP_DESIGN.es.md`](design/WORKSHOP_DESIGN.es.md) (workshop narrative) · this file (build backlog).

---

## 1. Principles

| Principle | What it means in practice |
|---|---|
| **Everything is code** | Workspace objects go through a Declarative Automation Bundle (DAB). Account groups go through the workspace identity proxy, with no account console. Other idempotent Python scripts use the SDK. Anything that has no API goes into `runbooks/`. |
| **Idempotent and re-runnable** | `CREATE … IF NOT EXISTS` / `CREATE OR REPLACE`, and "ensure" semantics in the scripts. Running a wave twice changes nothing. |
| **Parameterised for any workspace** | Catalog, group prefix, warehouse and region values are bundle variables. Nothing is hard-coded to the sandbox. |
| **Verifiable** | Every wave ships a `verify` job or script with explicit assertions. A wave is done only when verify is green. |
| **Reversible** | `scripts/teardown.py` removes everything in reverse wave order, so a workshop can be reset in minutes. Built: dry run by default; `--apply` deletes pages, domains, catalog (CASCADE), governed tags, bundle, secret scope, persona SPs and groups. Flags: `--keep-catalog`, `--keep-identity`. ✅ |
| **Public-safe** | Synthetic data only. No customer names, no secrets in the repo. Secrets live in a Databricks secret scope. |

---

## 2. Environment and conventions

| Item | Value (sandbox default) | Variable |
|---|---|---|
| Workspace | Azure Databricks sandbox (host from the CLI profile) | bundle target `sandbox` |
| CLI profiles | workspace profile (workspace admin). The current waves need no account profile; future CD federation would. | `--profile` |
| Catalog | `sgw_shop` | `var.catalog` |
| Schemas | `gold` · `semantic` · `governance` · `ops` | fixed |
| Group prefix | `wk_` | `var.group_prefix` |
| Governed tag prefix | `sgw_` (the sandbox account already has `pii` / `sensitivity` with other values) | `var.tag_prefix` |
| SQL warehouse | serverless, created by the bundle (`sgw-warehouse`) or an existing one | `var.warehouse_id` |
| Regions in data | `ES`, `PT`, `FR`, `IT` | — |

> The executive deck uses `shop` as the catalog name to keep snippets short. The hands-on deck uses the real `sgw_shop`.

### Personas: how we demo "who asks"
Azure Databricks signs users in through Entra ID, so we cannot invent human users. We use two complementary mechanisms:

| Mechanism | Used for | How |
|---|---|---|
| **Persona service principals**: `sgw-persona-ana`, `sgw-persona-pedro`, `sgw-persona-marta` | Deterministic, automatable "same query, three results" (verify jobs + the companion app's "View as…" panel) | Created at account level, added to the persona groups. Their OAuth secrets are stored in the secret scope `sgw`. |
| **Real users (optional)** | Live UI demos: Genie One, Discover, access requests | Runbook: map existing Entra ID test users to the persona groups, or the presenter toggles their own group membership. |

---

## 3. Repository layout

```
semantics-governance-workshop/
├── databricks.yml                  # bundle: variables + targets (sandbox)
├── resources/                      # one YAML per wave (w0_warehouse … w8_app)
├── src/
│   ├── common/                     # persona helper
│   ├── w2_gold/                    # synthetic data, catalog/schemas, ownership, grants, governed tags
│   ├── w3_security/                # UDFs + ABAC policies
│   ├── w4_semantic/                # Metric Views (YAML) + deploy notebook + verify
│   ├── w5_context/                 # domains, certification, pages/*.md
│   ├── w6_consumption/             # AI/BI dashboard (.lvdash.json), Genie Agent builder, verify
│   └── w7_operate/                 # ops views, "Governance in action" dashboard, verify
├── scripts/                        # w1_identity, preflight, render_app_artifacts, smoke_app, show_verify, teardown
├── app/                            # companion Databricks App (wave 8)
├── runbooks/                       # manual steps (UI-only features), one file per wave
├── docs/
│   ├── BUILD_PLAN.md               # this file
│   ├── APP_DESIGN.md · spike-8a.md · preflight-sandbox.md
│   └── design/WORKSHOP_DESIGN.es.md
└── .github/workflows/              # validate on PR (deploy on main = future)
```

---

## 4. Waves at a glance

> **Scope change (19 Nov 2026):** the unstructured-documents step was removed to keep the workshop focused and straightforward. In accounts enrolled in the legacy *Serverless Access Controls* preview, Genie Agent volume content search is blocked (`USAGE_POLICY_PREVIEW_ENABLED`). The journey now has **8 steps**.

| Wave | Workshop step | Deliverable | Mechanism | Needs account admin | Status |
|---|---|---|---|---|---|
| **0** | — | Repo skeleton, bundle, preflight, CI validate | DAB + script | No | ✅ |
| **1** | 1 · Identity | Account groups (via workspace identity proxy), persona SPs, entitlements, secret scope | Script / job `w1_identity_setup` (workspace admin) | No | ✅ |
| **2** | 2 · Gold | Catalog/schemas, synthetic data, ownership, grants, governed tags + assignments | DAB job `w2_gold` (5 notebooks) | No | ✅ |
| **3** | 3 · RLS/CLS | UDFs + ABAC row filter and column mask policies | DAB job `w3_security` (2 notebooks) | No | ✅ |
| **4** | 4 · Metrics | Metric Views (YAML), consumer grants, "SELECT only on semantic" | DAB job `w4_semantic` (2 notebooks + YAML) | No | ✅ |
| **5** | 5 · Context | Domain + subdomains, Pages, certification/deprecation, Discover curation | DAB job `w5_context` (3 notebooks) + runbook | No | ✅ |
| **6** | 6 · Internal | AI/BI dashboard, Retail Sales Genie Agent (certified Metric Views), Genie One check | DAB (`dashboards`, `genie_spaces`) + verify job | No | ✅ |
| **7** | 8 · Operate | `ops` views over system tables, "Governance in action" dashboard, CI validate on PRs (CD with OIDC federation = future, needs account-level policy) | DAB job `w7_operate` + dashboard | No | ✅ |
| **8** | All + 7 · External | Companion app: step navigation, artifact links, live proofs, "View as…" panel, step-7 **agent chat** over Genie One MCP and DBSQL MCP as the user, live OBO trace, builder view | Databricks App (DAB): React + Vite frontend built at deploy, FastAPI | No | ✅ 8a–8f done · `smoke_app.py` and `teardown.py` in place |

---

## 5. Wave details

### Wave 0 · Foundations
**Goal:** an empty but deployable bundle, plus a preflight that tells us what the workspace supports.

| Artifact | Path |
|---|---|
| Bundle config with variables and targets `sandbox` / `customer` | `databricks.yml` |
| Serverless SQL warehouse (optional, if `var.warehouse_id` is empty) | `resources/w0_warehouse.yml` |
| Preflight: metastore, serverless, DBR ≥ 16.4 / serverless for ABAC, previews (Pages, Domains, Managed MCP, Unity Gateway), caller is metastore admin / account admin | `scripts/preflight.py` |
| CI: `bundle validate` on every PR | `.github/workflows/validate.yml` |
| README with quick start | `README.md` |

**Verify:** `databricks bundle validate -t sandbox` passes · the preflight report is saved to `docs/preflight-sandbox.md`.

---

### Wave 1 · Identity (Step 1)
| Artifact | Detail |
|---|---|
| Account groups | `wk_platform_admins`, `wk_data_engineers`, `wk_security_admins`, `wk_sales_domain_owners`, `wk_analysts_es`, `wk_analysts_pt`, `wk_sales_leads`, `wk_pii_readers`, plus the umbrella group `wk_analysts` (contains es/pt/leads) |
| Persona SPs | `sgw-persona-ana` → `wk_analysts_es` · `sgw-persona-pedro` → `wk_analysts_pt` · `sgw-persona-marta` → `wk_sales_leads` + `wk_pii_readers` |
| CI/CD SP | `sgw-cicd` → `wk_data_engineers` (for future CD) |
| Workspace assignment | Automatic: in an identity-federated workspace, groups and SPs created by a workspace admin are account-level identities assigned to the workspace. Entitlements: `workspace-access` + `databricks-sql-access` for consumers. |
| Secret scope `sgw` | OAuth client secrets of the persona SPs (read: admins + the app SP) |
| Runbook | `runbooks/w1_identity.md`: mapping real Entra ID users and SCIM / automatic identity management |

**Verify:** `scripts/w1_identity.py --verify` lists the groups, members and workspace assignment. Each persona SP can authenticate (M2M) and call `current_user()`.

---

### Wave 2 · Data and physical governance (Step 2)
**Synthetic dataset** (seeded and deterministic, generated by a serverless job):

| Table | Rows (approx.) | Governance notes |
|---|---|---|
| `gold.dim_date` | 1,096 (2024–2026) | Fiscal calendar |
| `gold.dim_store` | 40 | `region` (ES/PT/FR/IT) → tag `sgw_region_scope` |
| `gold.dim_product` | 300 | category, brand |
| `gold.dim_customer` | 20,000 | `email`, `phone`, `tax_id`, `full_name` → tag `sgw_pii`; `country` → tag `sgw_region_scope` |
| `gold.fact_sales` | ~1.5M | `store_region` denormalised → tag `sgw_region_scope`; `gross_amount`, `discount`, `margin` |
| `gold.fact_budget` | ~1,700 | month × region × category |
| `semantic.v_sales_es_legacy` | view | Duplicated "BI tool" view for ES, deprecated in wave 5 |

| Artifact | Detail |
|---|---|
| Catalog + schemas + ownership | `gold` → `wk_data_engineers` · `governance` → `wk_security_admins` · `semantic` → `wk_data_engineers` · `ops` → `wk_platform_admins` |
| Grants | Consumers: `USE CATALOG` only (no `USE SCHEMA` on `gold`). Optional `BROWSE` on the catalog, for discovery. |
| Governed tags (prefixed, created from the workspace) | `sgw_sensitivity` {public, internal, confidential} · `sgw_pii` {name, email, phone, tax_id} · `sgw_region_scope` {region} — assignable by `wk_security_admins` / `wk_data_engineers` |
| Tag assignments | SQL `SET TAGS` on columns and tables |
| Data classification | Runbook: enable it and review its suggestions against our manual tags |

**Verify:** row counts · tags present in `information_schema.column_tags` · `sgw-persona-ana` gets `PERMISSION_DENIED` on `gold.fact_sales`.

> Open question (resolved in wave 5): Discover domains are built on governed tags. We deliberately don't create a `domain` tag in wave 2, to avoid clashing with the one the Domains feature creates.

---

### Wave 3 · Row and column security with ABAC (Step 3)
| Artifact | Detail |
|---|---|
| UDF `governance.region_filter(region)` | `wk_sales_leads` sees all regions. `wk_analysts_es` → ES, `wk_analysts_pt` → PT. |
| UDF `governance.mask_pii(value)` | Returns `****` (partial mask for email) |
| Policy `region_rls` on schema `gold` | `ROW FILTER … TO account users FOR TABLES MATCH COLUMNS has_tag('sgw_region_scope') AS r USING COLUMNS (r)` |
| Policy `pii_mask` on schema `gold` | `COLUMN MASK … TO account users EXCEPT wk_pii_readers … MATCH COLUMNS has_tag('sgw_pii')` |
| Grants on UDFs | `EXECUTE` as required by the policy model |

**Verify job (runs as each persona SP):** the same query on `gold` (through a temporary grant in the verify step only) returns: Ana = ES rows with masked PII · Pedro = PT rows with masked PII · Marta = all rows with clear PII. A new table tagged `region_scope` is filtered automatically.

---

### Wave 4 · Metric Views (Step 4)
| Artifact | Detail |
|---|---|
| `semantic.sales_metrics` | source `gold.fact_sales`, joins `dim_store`, `dim_product`, `dim_date`, `dim_customer`. Measures: `net_sales`, `gross_sales`, `discount_amount`, `gross_margin`, `gross_margin_pct`, `orders`, `customers` (distinct), `avg_ticket`, `net_sales_ly` (window). Synonyms ES/PT/EN, formats, comments at every level. |
| `semantic.budget_metrics` | source `gold.fact_budget`: `budget_amount` |
| `semantic.sales_vs_budget_metrics` | Base view (pre-aggregated, multi-fact) → metric view with `budget_attainment_pct` |
| Deploy | YAML in `src/w4_semantic/*.metric_view.yaml` → SQL task `CREATE OR REPLACE VIEW … WITH METRICS LANGUAGE YAML AS $$…$$` |
| Grants | `wk_analysts`: `USE SCHEMA` + `SELECT` on `semantic` |

**Verify (the core assertion of the workshop):** each persona runs `SELECT region, MEASURE(net_sales) FROM semantic.sales_metrics GROUP BY region` and gets **only its own region(s)**, while having **no privilege on `gold`**. PII masked in any dimension that exposes `email`. Expected totals are asserted against an admin-computed baseline.

---

### Wave 5 · Business context (Step 5)
| Artifact | Mechanism | Detail |
|---|---|---|
| Domain `Retail Sales` with subdomains `Store Performance` and `Budget` | Domains API (Public Preview) | Business owner `wk_sales_domain_owners`, technical owner `wk_data_engineers`. Each domain is backed by a governed tag with the same name |
| Pages | REST API from `src/w5_context/pages/*.md` | `Net Sales`, `Gross Margin %`, `Budget Attainment`, `Active Customer`, `Discount Rate`. Each with definition, synonyms, formula, owner and related assets. |
| Genie Code-drafted Page | Runbook (live demo) | Generate the "Sales per Customer" Page from the YAML during the workshop |
| Certification | SQL `SET TAG system.certification_status` | `sales_metrics`, `sales_vs_budget_metrics` → certified · `v_sales_es_legacy` → deprecated |
| Permissions | Grants | Only `wk_sales_domain_owners` can assign certification and manage the domain and its Pages |
| Discover sections, access-request destinations | Runbook | No API for these |

**Verify:** the Pages API lists 5 published Pages · certification tags present · runbook checklist done.

---

### Wave 6 · Internal consumption (Step 6)
| Artifact | Detail |
|---|---|
| AI/BI dashboard `Retail Sales Performance` | On the certified Metric Views, with viewer credentials so RLS applies (`embed_credentials: false`) |
| Genie Agent `Retail Sales` | The 2 certified Metric Views only, plus instructions, 5 sample questions, 4 example SQL queries and 10 benchmarks |
| Genie One | No artifact. Runbook check that it cites the Page and the certified metric view. |

**Verify:** the dashboard is published and renders · the Genie benchmark score is recorded · Genie Agent answers for persona users (real-user runbook).

---

### Step 7 · External consumption (delivered in wave 8)
> Delivered by the companion app (wave 8 below): the app is an MCP client of Unity Gateway, with each person's OAuth token. The runbooks, BI files and orchestrator sample listed here are not in the repo yet.
| Artifact | Detail |
|---|---|
| Managed MCP / Unity Gateway | Runbook: enable previews, grant the `wk_analysts` group on the Genie Agent MCP / DBSQL MCP, capture URLs |
| Claude (Cowork / Desktop) and ChatGPT | Runbooks with screenshots: custom connector, OAuth per user |
| BI | `src/w8_external/powerbi/sgw.pbids` · Tableau BI-compatibility-mode notes · Excel connector steps |
| Orchestrator sample | `src/w8_external/orchestrator/`: a small Python agent that calls the Genie Agent MCP as a sub-agent |

**Verify:** an MCP `tools/list` call succeeds with a persona token · the sample orchestrator answers the business question.

---

### Wave 7 · Operate (Step 8)
| Artifact | Detail |
|---|---|
| `ops` views | `ops.principals` (readable names for persona SPs), `ops.semantic_activity` (who queried what, from which surface and layer), `ops.blocked_attempts`, `ops.lineage` (Gold → Metric Views → consumers), `ops.workshop_cost` |
| Observability dashboard | "Governance in action" |
| CI | `.github/workflows/validate.yml`: `bundle validate` on every PR. CD (`bundle deploy` as `sgw-cicd` with GitHub OIDC federation, no secrets) is future work |
| Federation policy | Not in the repo: it needs an account-level policy, out of scope |

**Verify:** `ops` views return data from the earlier waves · a PR is validated in CI.

---

### Wave 8 · Companion app (+ workshop step 7 · External)
> Full design: [`APP_DESIGN.md`](APP_DESIGN.md).
| Feature | Detail |
|---|---|
| Linear navigation | Step 0 → 8 with the same tracker bar as the deck |
| Per step | Concept · artifacts with deep links · live proof as the selected identity · ✓ chips from the verify job |
| "View as…" | You / Ana / Pedro / Marta. You uses OBO; personas use their service principal credentials from the secret scope |
| Agent chat (step 7) | Chat over Genie One MCP and/or DBSQL MCP as the selected identity; tool-call cards; live OBO trace |
| Smoke test | `python scripts/smoke_app.py --profile <ws>`: API, per-persona governance checks, chat over DBSQL MCP |
| Deploy | `resources/w8_app.yml` (`sgw_companion`) |

---

## 6. Risks and open items

| # | Item | Wave | Mitigation |
|---|---|---|---|
| 1 | ABAC row filter / mask behaviour **through a metric view** (expected: evaluated as the querying user) | 4 | It is the main assertion of the wave 4 verify. If it fails, fall back to table-level row filters and column masks. |
| 2 | Previews not enabled in the sandbox: Pages, Domains, Managed MCP, Enhanced Unity Gateway | 0 | Preflight detects them. The account admin enables them beforehand; the repo never uses the account console. |
| 3 | Domain ↔ governed tag naming | 5 | Create the domain first and inspect the tag it creates |
| 4 | Persona SPs and the Genie promotion (SPs are billed) | 7–8 | Persona SPs only run SQL. Genie demos use real users. |
| 5 | Unstructured documents (Knowledge Assistant over volumes) | 6 | **Removed from scope (19 Nov 2026).** The legacy *Serverless Access Controls* preview (`USAGE_POLICY_PREVIEW_ENABLED`) blocks volume attachment, with no workaround in this account. |
| 6 | Pages content is replicated globally | 5 | Synthetic content only |
| 7 | GitHub org permissions for Actions and OIDC | CD (future) | Confirm repo admin access before CD is enabled |
| 8 | Statements rejected at analysis time can be recorded with `client_application = unknown` | 7 | The Operate feed may label a blocked MCP attempt as *SQL API* |

---

## 7. Definition of done (per wave)
1. Code merged to `main` through a PR.
2. `bundle validate` green in CI.
3. Wave deployed to the sandbox.
4. Verify job/script green, with its output pasted into the PR.
5. Runbook updated for any manual step.
6. Teardown covers the new objects.
