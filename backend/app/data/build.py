"""Build the local Parquet warehouse from the organizers' dataset mirror.

Data minimization: only the fields the dispute workflow needs are kept. Identity documents,
emails, phone numbers, addresses, income, and credit scores are dropped here and never reach
the application or any model. Card and account numbers keep only their last four digits.

Usage:
    python -m app.data.build              # full warehouse from the mirror
    python -m app.data.build --customers 500   # demo subset: a sample of customers and their rows
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import duckdb

from app.config import settings
from app.data.quality import run_checks

# Organizer data mixes "Mexico" and "México"; everything downstream uses "México".
COUNTRY = "replace({col}, 'Mexico', 'México')"


def _src(mirror: Path, table: str) -> str:
    if (mirror / f"{table}.csv").exists():
        return f"read_csv('{mirror / table}.csv')"
    return f"read_csv('{mirror / table}/**/*.csv', union_by_name=true, hive_partitioning=false)"


def build(mirror: Path, out: Path, sample_customers: int | None = None, seed: float = 0.42) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    t0 = time.time()

    con.sql(f"""CREATE TEMP TABLE customers AS
        SELECT customer_id, first_name, {COUNTRY.format(col='country')} AS country, segment,
               customer_status, accepts_marketing, detected_accent
        FROM {_src(mirror, 'customers')}""")
    if sample_customers:
        con.sql(f"SELECT setseed({seed})")
        con.sql(f"CREATE TEMP TABLE keep AS SELECT customer_id FROM customers ORDER BY random() LIMIT {int(sample_customers)}")
        con.sql("DELETE FROM customers WHERE customer_id NOT IN (SELECT customer_id FROM keep)")
    keep = "WHERE customer_id IN (SELECT customer_id FROM customers)"

    con.sql(f"""CREATE TEMP TABLE products AS
        SELECT product_id, customer_id, product_type, right(CAST(product_number AS VARCHAR), 4) AS last4,
               currency, product_status, expiration_date, has_linked_app, days_past_due
        FROM {_src(mirror, 'products')} {keep}""")

    con.sql(f"""CREATE TEMP TABLE transactions AS
        SELECT transaction_id, transaction_date, product_id, customer_id, transaction_type,
               transaction_category, amount, currency, amount_usd, channel, merchant_name,
               merchant_category, {COUNTRY.format(col='transaction_country')} AS transaction_country,
               transaction_city, transaction_status, response_code, is_fraud, fraud_score
        FROM {_src(mirror, 'transactions')} {keep}""")

    # The bank's own outbound record: campaign messages plus outbound calls. This is what the
    # "is this really my bank?" check looks up. Transactional alerts and collections are not in
    # the dataset, so "no record" can never be read as proof on its own (docs/idea-brief.md).
    con.sql(f"""CREATE TEMP TABLE outbound_contacts AS
        SELECT send_id AS contact_id, send_date AS contact_ts, customer_id, send_channel AS channel,
               'campaign' AS kind, campaign_id AS topic, was_delivered AS delivered
        FROM {_src(mirror, 'campaign_sends')} {keep}
        UNION ALL
        SELECT interaction_id, interaction_date, customer_id, 'Voice', 'call', contact_reason, true
        FROM {_src(mirror, 'call_center_interactions')} {keep} AND interaction_type = 'Outbound Call'""")

    con.sql(f"""CREATE TEMP TABLE complaints AS
        SELECT complaint_id, creation_date, customer_id, case_type, category, subcategory,
               affected_product_id, status, closing_date
        FROM {_src(mirror, 'complaints')} {keep}""")

    counts = {}
    for t in ["customers", "products", "transactions", "outbound_contacts", "complaints"]:
        con.sql(f"COPY {t} TO '{out / t}.parquet' (FORMAT parquet)")
        counts[t] = con.sql(f"SELECT count(*) FROM {t}").fetchone()[0]

    report = run_checks(con)
    report["row_counts"] = counts
    report["sample_customers"] = sample_customers
    report["build_seconds"] = round(time.time() - t0, 1)
    (out / "quality_report.json").write_text(json.dumps(report, indent=2, default=str))
    return report


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--customers", type=int, default=None, help="build a demo subset of N random customers")
    ap.add_argument("--out", type=Path, default=settings.warehouse_dir)
    args = ap.parse_args()
    report = build(settings.mirror_dir, args.out, args.customers)
    print(json.dumps({"row_counts": report["row_counts"], "checks_failed": report["checks_failed"],
                      "build_seconds": report["build_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
