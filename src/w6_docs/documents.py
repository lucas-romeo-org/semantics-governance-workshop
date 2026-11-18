"""Content of the three synthetic business documents (kept as code so they are reviewable and reproducible)."""

DOCS = {
    "docs": {
        "KPI_Handbook.pdf": ("Retail Sales · KPI Handbook", "Version 2.1 · Owner: Retail Sales domain owners · Internal", [
            ("1. Purpose", "This handbook explains how the commercial KPIs are defined and how they must be used in reports, dashboards and AI assistants. The certified source for every KPI is the metric view semantic.sales_metrics."),
            ("2. Net Sales", "Net Sales is gross sales minus discounts, VAT excluded. It is the only sales figure allowed in commercial reporting. Legacy reports that show gross sales as net sales must not be used."),
            ("3. Gross Margin %", "Gross margin divided by net sales. It is a ratio: never average it across stores or months; always recompute it from its components. The usual range is between 25% and 30%."),
            ("4. Active Customer", "A loyalty customer with at least one purchase in the previous 90 days. Active customers are a distinct count and must never be summed across periods or regions."),
            ("5. Budget Attainment", "Net sales divided by budget for the same month, region and category. Above 100% means above budget. The year-to-date attainment uses cumulative net sales and cumulative budget."),
            ("6. Reporting calendar", "Weeks start on Monday. The fiscal year equals the calendar year. Monthly figures are closed on the third working day of the following month."),
        ]),
        "Discount_Policy.pdf": ("Retail Sales · Commercial Discount Policy", "Version 3.0 · Owner: Commercial direction · Internal", [
            ("1. Scope", "This policy applies to every store format (hypermarket, supermarket, convenience and online) in all regions."),
            ("2. Discount levels", "Store managers can approve discounts of up to 15% without further approval. Discounts between 15% and 25% require approval from the regional manager. Discounts above 25% are not allowed, except for clearance of discontinued products authorised by the commercial director."),
            ("3. Promotions", "Promotional campaigns are planned quarterly. A product cannot be on promotion for more than 6 weeks in a quarter. Promotions are measured with the KPI Promo share %."),
            ("4. Monitoring", "The discount rate (discounts divided by gross sales) is reviewed monthly per region. A region with a discount rate above 8% for two consecutive months triggers a commercial review."),
        ]),
    },
    "restricted_docs": {
        "Customer_Privacy_Policy.pdf": ("Customer Data Privacy Policy", "Version 1.4 · Owner: Data Protection Officer · CONFIDENTIAL", [
            ("1. Personal data", "Customer name, e-mail, phone and tax identifier are personal data. They are masked for every user except members of the PII readers group."),
            ("2. Retention", "Customer personal data is retained for 5 years after the last purchase, then anonymised. Transactional data is kept for 10 years for legal reasons."),
            ("3. Access requests", "Access to personal data must be requested through the data catalog and approved by the Retail Sales domain owners and the Data Protection Officer."),
            ("4. Incidents", "Any suspected personal data breach must be reported to the Data Protection Officer within 24 hours."),
        ]),
    },
}
