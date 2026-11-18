# Runbook · Wave 2 · Gold

## Before running
- **Default Storage metastores** (no metastore storage root): `CREATE CATALOG` from SQL or the API fails in non-serverless-only workspaces. Create the catalog once in **Catalog Explorer → Create catalog → `sgw_shop` → Use default storage**. The job reuses it.
- Metastores with a storage root: nothing to do. The job creates the catalog.

## Run
```bash
databricks bundle deploy -t <target> --profile <ws>
databricks bundle run w2_gold -t <target> --profile <ws>
```

## Result (sandbox reference)
| Region | Sales lines | Net sales (M€) |
|---|---|---|
| ES | 525,373 | 78.00 |
| PT | 374,873 | 55.73 |
| FR | 337,492 | 50.08 |
| IT | 262,262 | 38.84 |

Each customer is active during a 60–480 day window, so about half of them are active in any 90-day period. 2026 prices are 5% above 2025, which makes year-over-year growth visible.

Schema owners: `gold`, `semantic` → `wk_data_engineers` · `governance` → `wk_security_admins` · `ops` → `wk_platform_admins` · catalog → `wk_platform_admins`.

Governed tags: `sgw_pii`, `sgw_region_scope` and `sgw_sensitivity`, created from the workspace (no account console needed).

## Hands-on tip
Open `src/w2_gold/04_ownership_grants_tags.py` in the workspace. Every cell is one governance idea (ownership, segregation of duties, classification).
