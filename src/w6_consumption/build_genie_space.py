"""Builds resources/w6_genie.yml from the Retail Sales Genie Agent definition below.

Edit this file, then run:  python src/w6_consumption/build_genie_space.py
The bundle does not interpolate ${var.*} inside referenced JSON files, so the definition is inlined
into the resource YAML, where ${var.catalog} is resolved at deploy time.
"""
import json, pathlib

SPACE = {
  "version": 2,
  "config": {
    "sample_questions": [
      {
        "id": "a0000000000000000000000000000001",
        "question": [
          "What were net sales by region last quarter versus budget?"
        ]
      },
      {
        "id": "a0000000000000000000000000000002",
        "question": [
          "Who are our top 5 customers by net sales this year?"
        ]
      },
      {
        "id": "a0000000000000000000000000000003",
        "question": [
          "How did net sales grow year over year in 2026, month by month?"
        ]
      },
      {
        "id": "a0000000000000000000000000000004",
        "question": [
          "Which categories have the highest gross margin %?"
        ]
      },
      {
        "id": "a0000000000000000000000000000005",
        "question": [
          "What is our year-to-date budget attainment by region?"
        ]
      }
    ]
  },
  "data_sources": {
    "tables": [
      {
        "identifier": "${var.catalog}.semantic.sales_metrics"
      },
      {
        "identifier": "${var.catalog}.semantic.sales_vs_budget_metrics"
      }
    ]
  },
  "instructions": {
    "text_instructions": [
      {
        "id": "b0000000000000000000000000000001",
        "content": [
          "## PURPOSE\n- Answer questions about retail sales, margin, customers and budget for the Retail Sales domain (regions ES, PT, FR, IT).\n- Use ONLY the certified Metric Views sales_metrics and sales_vs_budget_metrics.\n\n## DISAMBIGUATION\n- \"Sales\" or \"revenue\" means the measure net_sales (gross minus discounts, VAT excluded).\n- \"Last quarter\" means the last complete calendar quarter in the data (data ends 2026-10-31, so last quarter = 2026-Q3).\n- \"Active customers\" means active_customers_90d.\n- \"Versus budget\" or \"attainment\" uses sales_vs_budget_metrics (budget_attainment_pct, ytd_attainment_pct).\n\n## CONSTRAINTS\n- Never compute ratios by averaging: use the governed measures (gross_margin_pct, discount_rate, budget_attainment_pct).\n- For last year or year-over-year measures, aggregate first and filter months in an outer query; do not filter the year in the same query as net_sales_ly.\n- Customer names may be masked as **** for some users: say that the data is masked by policy and do not try to work around it.\n- Users only see the regions their policies allow: never claim a region has no sales just because it is not visible.\n\n## Instructions you must follow when providing summaries\n- Format money in EUR with two decimals and percentages with one decimal.\n- Always state the period used.\n"
        ]
      }
    ],
    "example_question_sqls": [
      {
        "id": "c0000000000000000000000000000001",
        "question": [
          "Net sales and budget attainment by region for 2026-Q3"
        ],
        "sql": [
          "SELECT region, MEASURE(net_sales) AS net_sales, MEASURE(budget) AS budget, MEASURE(budget_attainment_pct) AS attainment FROM ${var.catalog}.semantic.sales_vs_budget_metrics WHERE month >= '2026-07-01' AND month < '2026-10-01' GROUP BY region ORDER BY net_sales DESC"
        ]
      },
      {
        "id": "c0000000000000000000000000000002",
        "question": [
          "Year-over-year net sales growth by month in 2026"
        ],
        "sql": [
          "SELECT * FROM (SELECT month, MEASURE(net_sales) AS net_sales, MEASURE(net_sales_ly) AS net_sales_ly, MEASURE(net_sales_yoy_pct) AS yoy FROM ${var.catalog}.semantic.sales_metrics GROUP BY month) WHERE month >= '2026-01-01' ORDER BY month"
        ]
      },
      {
        "id": "c0000000000000000000000000000003",
        "question": [
          "Top 5 customers by net sales in 2026"
        ],
        "sql": [
          "SELECT customer_id, customer_name, MEASURE(net_sales) AS net_sales FROM ${var.catalog}.semantic.sales_metrics WHERE year = 2026 GROUP BY customer_id, customer_name ORDER BY net_sales DESC LIMIT 5"
        ]
      },
      {
        "id": "c0000000000000000000000000000004",
        "question": [
          "Gross margin % by category"
        ],
        "sql": [
          "SELECT category, MEASURE(net_sales) AS net_sales, MEASURE(gross_margin_pct) AS gross_margin_pct FROM ${var.catalog}.semantic.sales_metrics GROUP BY category ORDER BY gross_margin_pct DESC"
        ]
      }
    ]
  },
  "benchmarks": {
    "questions": [
      {
        "id": "d0000000000000000000000000000001",
        "question": [
          "What were total net sales in 2026-Q3?"
        ],
        "answer": [
          {
            "format": "SQL",
            "content": [
              "SELECT MEASURE(net_sales) FROM ${var.catalog}.semantic.sales_metrics WHERE month >= '2026-07-01' AND month < '2026-10-01'"
            ]
          }
        ]
      },
      {
        "id": "d0000000000000000000000000000002",
        "question": [
          "Net sales by region in 2026-Q3"
        ],
        "answer": [
          {
            "format": "SQL",
            "content": [
              "SELECT region, MEASURE(net_sales) FROM ${var.catalog}.semantic.sales_metrics WHERE month >= '2026-07-01' AND month < '2026-10-01' GROUP BY region ORDER BY 2 DESC"
            ]
          }
        ]
      },
      {
        "id": "d0000000000000000000000000000003",
        "question": [
          "Show me revenue per region for the third quarter of 2026"
        ],
        "answer": [
          {
            "format": "SQL",
            "content": [
              "SELECT region, MEASURE(net_sales) FROM ${var.catalog}.semantic.sales_metrics WHERE month >= '2026-07-01' AND month < '2026-10-01' GROUP BY region ORDER BY 2 DESC"
            ]
          }
        ]
      },
      {
        "id": "d0000000000000000000000000000004",
        "question": [
          "What is the gross margin % overall?"
        ],
        "answer": [
          {
            "format": "SQL",
            "content": [
              "SELECT MEASURE(gross_margin_pct) FROM ${var.catalog}.semantic.sales_metrics"
            ]
          }
        ]
      },
      {
        "id": "d0000000000000000000000000000005",
        "question": [
          "Gross margin percentage by category"
        ],
        "answer": [
          {
            "format": "SQL",
            "content": [
              "SELECT category, MEASURE(gross_margin_pct) FROM ${var.catalog}.semantic.sales_metrics GROUP BY category ORDER BY 2 DESC"
            ]
          }
        ]
      },
      {
        "id": "d0000000000000000000000000000006",
        "question": [
          "How many active customers do we have?"
        ],
        "answer": [
          {
            "format": "SQL",
            "content": [
              "SELECT MEASURE(active_customers_90d) FROM ${var.catalog}.semantic.sales_metrics"
            ]
          }
        ]
      },
      {
        "id": "d0000000000000000000000000000007",
        "question": [
          "Budget attainment by region in 2026"
        ],
        "answer": [
          {
            "format": "SQL",
            "content": [
              "SELECT region, MEASURE(budget_attainment_pct) FROM ${var.catalog}.semantic.sales_vs_budget_metrics WHERE year = 2026 GROUP BY region ORDER BY 2 DESC"
            ]
          }
        ]
      },
      {
        "id": "d0000000000000000000000000000008",
        "question": [
          "What is our year-to-date budget attainment?"
        ],
        "answer": [
          {
            "format": "SQL",
            "content": [
              "SELECT MEASURE(ytd_attainment_pct) FROM ${var.catalog}.semantic.sales_vs_budget_metrics"
            ]
          }
        ]
      },
      {
        "id": "d0000000000000000000000000000009",
        "question": [
          "Top 5 customers by net sales in 2026"
        ],
        "answer": [
          {
            "format": "SQL",
            "content": [
              "SELECT customer_id, customer_name, MEASURE(net_sales) FROM ${var.catalog}.semantic.sales_metrics WHERE year = 2026 GROUP BY customer_id, customer_name ORDER BY 3 DESC LIMIT 5"
            ]
          }
        ]
      },
      {
        "id": "d0000000000000000000000000000010",
        "question": [
          "Discount rate by store format"
        ],
        "answer": [
          {
            "format": "SQL",
            "content": [
              "SELECT store_format, MEASURE(discount_rate) FROM ${var.catalog}.semantic.sales_metrics GROUP BY store_format ORDER BY 2 DESC"
            ]
          }
        ]
      }
    ]
  }
}

HEADER = """# GENERATED by src/w6_consumption/build_genie_space.py: do not edit by hand.
# Wave 6: Retail Sales Genie Agent (certified Metric Views only)
resources:
  genie_spaces:
    retail_sales_agent:
      title: Retail Sales
      description: >-
        Curated agent for the Retail Sales domain. Answers questions on certified sales, margin, customer
        and budget KPIs using only the certified Metric Views. Always answers with the permissions of the
        user who asks.
      warehouse_id: ${resources.sql_warehouses.sgw_warehouse.id}
      parent_path: /Workspace/Shared/semantics-governance-workshop
      permissions:
        - {group_name: "${var.group_prefix}analysts", level: CAN_RUN}
        - {group_name: "${var.group_prefix}sales_domain_owners", level: CAN_MANAGE}
      serialized_space: |
"""

if __name__ == "__main__":
    root = pathlib.Path(__file__).resolve().parents[2]
    body = json.dumps(SPACE, indent=2, ensure_ascii=False)
    out = HEADER + "\n".join("        " + line for line in body.splitlines()) + "\n"
    (root / "resources" / "w6_genie.yml").write_text(out)
    print("wrote resources/w6_genie.yml")
