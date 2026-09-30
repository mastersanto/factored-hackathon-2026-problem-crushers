"""Build the local Parquet warehouse from the organizers' dataset mirror.

Data minimization: only the fields the dispute workflow needs are kept. Identity documents,
emails, phone numbers, addresses, income, and credit scores are dropped here and never reach
the application or any model. Card and account numbers keep only their last four digits.

Usage:
    python -m app.data.build              # full warehouse from the mirror
    python -m app.data.build --customers 500   # sample of customers and their rows, from the mirror
    python -m app.data.build --from-warehouse data/warehouse --customers 500 --out data/demo-warehouse
                                               # deployment subset: covers every workflow path
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import duckdb

from app.config import settings
from app.data.quality import run_checks

TABLES = ["customers", "products", "transactions", "outbound_contacts", "complaints", "compliance_reviews"]

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

    # SYNTHETIC: the dataset flags no charge as under anti-money-laundering review, so FR-018 could not
    # be exercised. A seeded 0.05% sample of transactions stands in for such a list. It is labelled
    # synthetic and is used only to show that the assistant never explains these charges.
    con.sql(f"SELECT setseed({seed})")
    con.sql("""CREATE TEMP TABLE compliance_reviews AS
        SELECT transaction_id, customer_id, true AS synthetic FROM transactions
        WHERE hash(transaction_id || 'compliance-review') % 2000 = 0""")

    counts = {}
    for t in TABLES:
        con.sql(f"COPY {t} TO '{out / t}.parquet' (FORMAT parquet)")
        counts[t] = con.sql(f"SELECT count(*) FROM {t}").fetchone()[0]

    report = run_checks(con)
    report["row_counts"] = counts
    report["sample_customers"] = sample_customers
    report["build_seconds"] = round(time.time() - t0, 1)
    (out / "quality_report.json").write_text(json.dumps(report, indent=2, default=str))
    return report


# Workflow paths the demo must be able to show, as conditions on the recent data (last 30 days).
DEMO_PATHS = {
    "pending_charge": "t.transaction_status = 'Pending' AND t.merchant_name IS NOT NULL",
    "flagged_fraud_score": "t.fraud_score > 30 AND t.merchant_name IS NOT NULL",
    "mexico_debit_48h": "c.country = 'México' AND p.product_type = 'Tarjeta Débito' AND t.transaction_date >= (SELECT max(transaction_date) FROM tx_all) - INTERVAL 48 HOUR",
    "colombia_purchase": "c.country = 'Colombia' AND t.transaction_type = 'Purchase' AND t.merchant_name IS NOT NULL",
    "argentina_purchase": "c.country = 'Argentina' AND t.transaction_type = 'Purchase' AND t.merchant_name IS NOT NULL",
}
DISPUTABLE = "('Purchase', 'Payment', 'Withdrawal', 'Transfer', 'Adjustment')"


def build_demo(src: Path, out: Path, n: int = 500, per_path: int = 5, seed: float = 0.42) -> dict:
    """Demo subset for deployment, from the already-minimized warehouse: a few customers per workflow
    path, then random customers up to n. Only these customers' rows are kept."""
    out.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    for t in TABLES:
        con.sql(f"CREATE VIEW {t}_all AS SELECT * FROM read_parquet('{src / t}.parquet')")
    con.sql("CREATE VIEW tx_all AS SELECT * FROM transactions_all")
    con.sql(f"SELECT setseed({seed})")
    recent = "t.transaction_date >= (SELECT max(transaction_date) FROM tx_all) - INTERVAL 30 DAY"
    picks = []
    for name, cond in DEMO_PATHS.items():
        picks.append(f"""(SELECT DISTINCT t.customer_id FROM transactions_all t JOIN customers_all c USING (customer_id)
            JOIN products_all p USING (product_id) WHERE {recent} AND c.customer_status = 'Active'
            AND t.transaction_type IN {DISPUTABLE} AND {cond} ORDER BY t.customer_id LIMIT {per_path})""")
    picks.append(f"""(SELECT DISTINCT t.customer_id FROM compliance_reviews_all r JOIN transactions_all t USING (transaction_id)
        JOIN customers_all c ON c.customer_id = t.customer_id WHERE {recent} AND c.customer_status = 'Active'
        AND t.merchant_name IS NOT NULL AND t.transaction_type IN ('Purchase', 'Payment') ORDER BY t.customer_id LIMIT {per_path})""")
    picks.append(f"""(SELECT DISTINCT o.customer_id FROM outbound_contacts_all o JOIN customers_all c USING (customer_id)
        WHERE o.contact_ts >= (SELECT max(transaction_date) FROM tx_all) - INTERVAL 30 DAY AND o.channel IN ('SMS', 'WhatsApp')
        AND c.customer_status = 'Active' ORDER BY o.customer_id LIMIT {per_path})""")
    con.sql(f"CREATE TEMP TABLE keep AS SELECT DISTINCT customer_id FROM ({' UNION '.join(picks)})")
    have = con.sql("SELECT count(*) FROM keep").fetchone()[0]
    con.sql(f"INSERT INTO keep SELECT customer_id FROM customers_all WHERE customer_id NOT IN (SELECT customer_id FROM keep) "
            f"ORDER BY random() LIMIT {max(0, n - have)}")
    keep = "WHERE customer_id IN (SELECT customer_id FROM keep)"
    counts = {}
    for t in TABLES:
        con.sql(f"CREATE TEMP TABLE {t} AS SELECT * FROM {t}_all {keep}")
        con.sql(f"COPY {t} TO '{out / t}.parquet' (FORMAT parquet)")
        counts[t] = con.sql(f"SELECT count(*) FROM {t}").fetchone()[0]
    report = run_checks(con)
    # Coverage: every path still has a customer in the subset (the subset's "today" is the full data's).
    coverage = {}
    for name, cond in DEMO_PATHS.items():
        coverage[name] = con.sql(f"""SELECT count(DISTINCT t.customer_id) FROM transactions t JOIN customers c USING (customer_id)
            JOIN products p USING (product_id) WHERE {recent} AND t.transaction_type IN {DISPUTABLE} AND {cond}""").fetchone()[0]
    coverage["compliance_review_charge"] = con.sql(f"""SELECT count(DISTINCT t.customer_id) FROM compliance_reviews r
        JOIN transactions t USING (transaction_id) WHERE {recent} AND t.merchant_name IS NOT NULL""").fetchone()[0]
    coverage["recent_bank_sms_or_whatsapp"] = con.sql("""SELECT count(DISTINCT customer_id) FROM outbound_contacts
        WHERE contact_ts >= (SELECT max(transaction_date) FROM tx_all) - INTERVAL 30 DAY AND channel IN ('SMS', 'WhatsApp')""").fetchone()[0]
    report.update({"row_counts": counts, "demo_path_coverage": coverage,
                   "demo_paths_missing": [k for k, v in coverage.items() if v == 0], "source": str(src), "customers": n})
    (out / "quality_report.json").write_text(json.dumps(report, indent=2, default=str))
    return report


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--customers", type=int, default=None, help="build a demo subset of N random customers")
    ap.add_argument("--out", type=Path, default=settings.warehouse_dir)
    ap.add_argument("--from-warehouse", type=Path, default=None,
                    help="build the demo subset from an existing (minimized) warehouse instead of the mirror")
    args = ap.parse_args()
    if args.from_warehouse:
        report = build_demo(args.from_warehouse, args.out, args.customers or 500)
        print(json.dumps({k: report[k] for k in ("row_counts", "checks_failed", "demo_path_coverage", "demo_paths_missing")}, indent=2))
        return
    report = build(settings.mirror_dir, args.out, args.customers)
    print(json.dumps({"row_counts": report["row_counts"], "checks_failed": report["checks_failed"],
                      "build_seconds": report["build_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
