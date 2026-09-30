"""Data-quality checks run at every warehouse build. Aggregates only.

Each check states what the workflow assumes and whether the data meets it. Known quirks of the
synthetic dataset are checked as expectations, so a change in the organizers' data shows up here.
"""
from __future__ import annotations

import duckdb

# (name, SQL returning one number, predicate on that number, what it protects)
CHECKS = [
    ("transaction_ids_unique",
     "SELECT count(*) - count(DISTINCT transaction_id) FROM transactions", lambda v: v == 0,
     "a claim must point at exactly one transaction"),
    ("transactions_link_to_products",
     "SELECT count(*) FROM transactions t LEFT JOIN products p USING (product_id) WHERE p.product_id IS NULL",
     lambda v: v == 0, "card status and currency come from the product"),
    ("transactions_have_amount_and_date",
     "SELECT count(*) FROM transactions WHERE amount IS NULL OR transaction_date IS NULL", lambda v: v == 0,
     "every explanation states amount and date"),
    ("country_spelling_normalized",
     "SELECT count(*) FROM customers WHERE country = 'Mexico'", lambda v: v == 0,
     "one spelling of México (the raw data has two)"),
    ("no_mxn_currency (known quirk)",
     "SELECT count(*) FROM transactions WHERE currency = 'MXN'", lambda v: v == 0,
     "currency follows the product; exchange-rate stories are not supported"),
    ("pending_share_pct",
     "SELECT round(100.0 * avg((transaction_status = 'Pending')::int), 2) FROM transactions",
     lambda v: 0 < v < 10, "pending charges are explained as pending, not disputed"),
    ("merchant_names_distinct (known quirk)",
     "SELECT count(DISTINCT merchant_name) FROM transactions WHERE merchant_name IS NOT NULL",
     lambda v: v < 100, "little merchant variety: history with a merchant carries little weight"),
    ("fraud_rate_pct",
     "SELECT round(100.0 * avg(is_fraud::int), 3) FROM transactions", lambda v: 0 < v < 1,
     "labels for the learned component exist and are rare"),
    ("outbound_contacts_present",
     "SELECT count(*) FROM outbound_contacts", lambda v: v > 0,
     "the 'is this really my bank?' check needs the outbound record"),
]


def run_checks(con: duckdb.DuckDBPyConnection) -> dict:
    results = []
    for name, sql, ok, why in CHECKS:
        value = con.sql(sql).fetchone()[0]
        results.append({"check": name, "value": value, "passed": bool(ok(value)), "protects": why})
    return {"checks": results, "checks_failed": sum(not r["passed"] for r in results)}
