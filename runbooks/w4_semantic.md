# Runbook · Wave 4 · Metric Views

```bash
databricks bundle run w4_semantic -t <target> --profile <ws>
python scripts/show_verify.py --profile <ws> --job "sgw · w4 semantic"
```

## What gets created
| Object | Notes |
|---|---|
| `semantic.sales_metrics` | `src/w4_semantic/sales_metrics.yaml`: 11 dimensions, 19 measures |
| `semantic.sales_vs_budget_metrics` | `src/w4_semantic/sales_vs_budget_metrics.yaml`, over the base view `gold.v_sales_budget_monthly` (consumers can't see it) |
| Grant | `wk_analysts`: `USE SCHEMA` + `SELECT` on `semantic` only |

### Measure catalogue (`sales_metrics`)
| Kind | Measures |
|---|---|
| Atomic | `gross_sales`, `discount_amount`, `net_sales`, `gross_margin`, `units`, `sales_lines`, `customers` |
| Filtered (`FILTER (WHERE …)`) | `promo_net_sales` |
| Composed (`MEASURE()`) | `gross_margin_pct`, `discount_rate`, `promo_share_pct`, `sales_per_customer` |
| Window | `net_sales_ly` (offset −12 months), `net_sales_yoy_pct` (composed), `net_sales_ytd` (cumulative + year), `active_customers_90d` (trailing 90 days) |
| Coarser LOD | `net_sales_all_regions` (range `all`), `region_share_pct` |

`sales_vs_budget_metrics`: `net_sales`, `budget`, `budget_gap`, `budget_attainment_pct`, `net_sales_ytd`, `budget_ytd`, `ytd_attainment_pct`.

## Verified result (sandbox): the core claim
```
✅ ana/pedro/marta: no access to gold (INSUFFICIENT_PERMISSIONS)
✅ ana sees ['ES'] · pedro ['PT'] · marta ['ES','FR','IT','PT'] through the Metric View
✅ same numbers as the governed baseline (ES 77,999,582.50 · PT 55,726,865.11 …)
✅ top-5 customer names masked for Ana/Pedro, visible for Marta
✅ YoY window works · share of total = 100% of what Ana can see · budget metrics ES only
ℹ️ ES Sep-2026 net sales · legacy view 3,867,151.99 vs governed 3,593,701.92 (+273k€, +7.6%)
```

## Teaching points
- **Filter outside window measures.** `WHERE year = 2026` removes last year's rows before the window runs, so `net_sales_ly` becomes NULL. Aggregate first, then filter in an outer query.
- **Shares are relative to what the reader can see.** For Ana, ES = 100%. Row-level security also shapes ratios, as it should.
- **Multi-fact KPIs need a pre-aggregated base view.** Keep it in `gold`, so consumers only see the Metric View.
- **The legacy view tells the story.** The duplicated "BI view" overstates ES net sales by 7.6% because it ignores discounts.
