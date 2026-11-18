---
title: Active Customer
domain: Retail Sales/Store Performance
description: A loyalty customer with at least one purchase in the previous 90 days.
synonyms: [Active customers, Clientes activos, Clientes ativos, Active buyers]
---
## Definition
A customer is **active** on a given day if they bought at least once in the **90 days before** that day.

## How to measure it
Measure `active_customers_90d` in `${catalog}.semantic.sales_metrics`: a trailing 90-day window, semi-additive (the last day of the period is used).

## Rules
- Distinct counts are **not additive**: never sum active customers across months or regions.
- "Customers" (distinct buyers in the period) is a different KPI.

## Related
Net Sales · Sales per Customer
