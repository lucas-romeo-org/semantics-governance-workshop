# Runbook · Wave 5 · Business context

```bash
databricks bundle run w5_context -t <target> --profile <ws>
python scripts/show_verify.py --profile <ws> --job "sgw · w5 context"
```

## What the automation does
| Item | How |
|---|---|
| Domain **Retail Sales** with subdomains **Store Performance** and **Budget** (published, business owner `wk_sales_domain_owners`, technical owner `wk_data_engineers`) | Domains API. Each domain is backed by a governed tag with the same name, created first. |
| `sales_metrics` → Store Performance · `sales_vs_budget_metrics` → Budget | `ALTER VIEW … SET TAGS ('Retail Sales/…')` |
| Certified: both Metric Views · Deprecated: `v_sales_es_legacy` | `SET TAGS ('system.certification_status' = 'certified' / 'deprecated')` |
| 5 glossary Pages: Net Sales, Gross Margin %, Active Customer, Discount Rate, Budget Attainment | Markdown in `src/w5_context/pages/` → Pages API (`/api/2.0/knowledge/pages`), updated in place on re-run |

## Manual steps (no API)
1. **Curate Discover** (≈ 3 min): Discover → Retail Sales → *Edit sections*. Pin `sales_metrics`, `sales_vs_budget_metrics` and the *Net Sales* Page in a "Start here" section, then **Publish**.
2. **Delegate curation** to the domain owners: Retail Sales → *Permissions* → grant `MANAGE DOMAIN` to `wk_sales_domain_owners`.
3. **Access requests**: configure the request destination of the `semantic` schema to `wk_sales_domain_owners` (Catalog Explorer → schema → *Access request settings*).

## Live demo: Genie Code drafts a Page
In Discover → Retail Sales → *New Page*, ask Genie Code:
> "Draft a glossary page for *Sales per Customer* using the metric view sgw_shop.semantic.sales_metrics"

Review it, add synonyms and publish it. This is the "documentation without developer effort" moment.

## Gotchas
- The domain's governed tag must exist before the domain is created ("Tag policy … not found").
- Shared accounts can hold hundreds of Pages: always paginate the list call.
- Subdomain assets appear under their direct parent only.
