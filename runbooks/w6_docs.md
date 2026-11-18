# Runbook · Wave 6 · Unstructured knowledge

```bash
databricks bundle run w6_docs -t <target> --profile <ws>
python scripts/show_verify.py --profile <ws> --job "sgw · w6 docs"
```

## What gets created
| Volume | Documents | `READ VOLUME` |
|---|---|---|
| `knowledge.docs` | KPI_Handbook.pdf · Discount_Policy.pdf | `wk_analysts` |
| `knowledge.restricted_docs` | Customer_Privacy_Policy.pdf | `wk_sales_leads` |

The documents are generated from `src/w6_docs/documents.py`: reviewable text, no binaries in Git. Both volumes are owned by `wk_sales_domain_owners`.

## How it is consumed
In wave 7 both volumes are attached to the **Retail Sales Genie Agent** (Sources → Add). Content search parses and indexes the files with `ai_parse_document` and stays in sync. File questions run in **Agent mode**, and the agent always uses **the permissions of the user who asks**.

> The design no longer uses a separate parse → AI Search index → Knowledge Assistant pipeline: Genie Agents with attached volumes cover it.

`02_under_the_hood_parse.py` shows what `ai_parse_document` returns for one PDF (optional, for the hands-on).

## Verified result (sandbox)
```
✅ ana / pedro can read docs        ✅ ana / pedro cannot read restricted_docs (no READ VOLUME)
✅ marta can read docs + restricted_docs
```

## Notes
- Content search needs **managed** volumes (not external volumes).
- Limits: 10 volumes per Genie Agent · files ≤ 100 MB and ≤ 500 pages.
