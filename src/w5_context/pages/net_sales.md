---
title: Net Sales
domain: Retail Sales/Store Performance
description: Official sales KPI. Gross sales minus discounts, VAT excluded.
synonyms: [Revenue, Sales, Ventas netas, Vendas líquidas, Ventas sin descuento]
---
## Definition
**Net Sales** is the value of goods sold after discounts, **VAT excluded**. It is the official KPI for commercial reporting in every tool: Databricks, BI tools and AI agents.

## Formula
`Net Sales = SUM(gross_amount − discount)`

## Rules
- Returns and VAT are excluded.
- Always read it from the certified Metric View `${catalog}.semantic.sales_metrics` (measure `net_sales`).
- ⚠️ The legacy view `v_sales_es_legacy` reports *gross* sales as "net sales". It is **deprecated**: do not use it.

## Related
Gross Margin % · Discount Rate · Budget Attainment

**Owner:** Retail Sales domain owners · **Technical owner:** data engineering
