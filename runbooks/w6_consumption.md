# Runbook · Wave 6 · Internal consumption

```bash
python src/w6_consumption/build_genie_space.py      # only after editing the Genie Agent definition
databricks bundle deploy -t <target> --profile <ws>
databricks bundle run w6_consumption_verify -t <target> --profile <ws>
python scripts/show_verify.py --profile <ws> --job "sgw · w6 consumption verify"
```

## What gets deployed (bundle-managed)
| Asset | Notes |
|---|---|
| AI/BI dashboard **Retail Sales Performance** | `src/w6_consumption/retail_sales.lvdash.json`. 4 KPIs (net sales, gross margin %, active customers 90d, budget attainment YTD), monthly trend, region, category margin, attainment by region. Every widget uses `MEASURE()` on the certified Metric Views. `embed_credentials: false`: viewers query with their own identity. `CAN_READ` for `wk_analysts`. |
| Genie Agent **Retail Sales** | Defined in `src/w6_consumption/build_genie_space.py` (rendered into `resources/w6_genie.yml`). Sources: the 2 certified Metric Views. Includes instructions, 5 sample questions, 4 example SQL queries (one per query shape) and 10 benchmarks. `CAN_RUN` for `wk_analysts`. |

> The bundle does not interpolate `${var.*}` inside referenced JSON files, so the Genie definition is rendered into the resource YAML by a small builder script.

## Verified result (sandbox)
```
✅ dashboard published with viewer credentials
✅ "Net sales by region in 2026-Q3?" → Ana ['ES'] · Pedro ['PT'] · Marta ['ES','FR','IT','PT']
✅ every answer used MEASURE() on semantic.sales_metrics, never gold
✅ "Top 5 customers" → names masked (****) for Ana
```

## Manual checks (live demo)
1. **Dashboard as two people**: open the published dashboard as yourself (all regions), then as an ES analyst (real user in `wk_analysts_es`, or toggle your own membership). Same dashboard, different numbers.
2. **Genie One**: ask *"What is net sales and how is it calculated?"*. Expect the answer to cite the **Net Sales Page** and the **certified** `sales_metrics`, with the legacy view ignored.
3. **Run benchmarks**: Genie Agent → *Benchmarks* → *Run all*, and record the score in the PR.

## Notes
- Unstructured documents were removed from scope. Genie Agent volume content search is blocked in accounts enrolled in the legacy *Serverless Access Controls* preview (`USAGE_POLICY_PREVIEW_ENABLED`).
- Persona service principals are billed for Genie usage (the named-user promotion doesn't apply). The verify job asks 4 questions.
