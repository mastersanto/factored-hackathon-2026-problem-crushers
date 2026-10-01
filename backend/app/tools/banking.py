"""Read-only banking tools. Every tool takes the session's customer, never a customer ID from
the conversation: permissions live here, not in any prompt."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.config import settings
from app.data.store import Store


class Unauthorized(Exception):
    """A request touched data that does not belong to the session's customer."""


@dataclass(frozen=True)
class Customer:
    customer_id: str
    first_name: str
    country: str
    segment: str
    status: str


def get_customer(store: Store, customer_id: str) -> Customer | None:
    rows = store.query("SELECT customer_id, first_name, country, segment, customer_status AS status "
                       "FROM customers WHERE customer_id = ?", [customer_id])
    return Customer(**rows[0]) if rows else None


TX_COLUMNS = ("t.transaction_id, t.transaction_date, t.transaction_type, t.transaction_category, t.amount, "
              "t.currency, t.amount_usd, t.channel, t.merchant_name, t.transaction_country, t.transaction_city, "
              "t.transaction_status, t.fraud_score, t.product_id, p.product_type, p.last4")


def find_transactions(store: Store, customer_id: str, *, amount: float | None = None,
                      merchant: str | None = None, date_from: datetime | None = None,
                      date_to: datetime | None = None, limit: int = 5) -> list[dict]:
    """Candidate charges for the customer's description. Amount matches within 1%."""
    since = store.as_of - timedelta(days=settings.lookback_days)
    where, params = ["t.customer_id = ?", "t.transaction_date >= ?",
                     "t.transaction_type IN ('Purchase', 'Payment', 'Withdrawal', 'Transfer', 'Adjustment')"], [customer_id, since]
    if amount is not None:
        where.append("abs(t.amount - ?) <= 0.01 * ?")
        params += [amount, amount]
    if merchant:
        where.append("lower(strip_accents(t.merchant_name)) LIKE '%' || lower(strip_accents(?)) || '%'")
        params.append(merchant)
    if date_from:
        where.append("t.transaction_date >= ?")
        params.append(date_from)
    if date_to:
        where.append("t.transaction_date < ?")
        params.append(date_to)
    sql = (f"SELECT {TX_COLUMNS} FROM transactions t JOIN products p USING (product_id) "
           f"WHERE {' AND '.join(where)} ORDER BY t.transaction_date DESC LIMIT {int(limit) + 1}")
    return store.query(sql, params)


MAX_RECENT = 9  # one-digit option replies (specs/007)


def recent_transactions(store: Store, customer_id: str, limit: int = 5) -> list[dict]:
    """The customer's most recent charge-type movements of the lookback window, newest first (specs/007).
    `limit` is clamped to 1-9. Only `customer_id`, the session's customer, is read."""
    n = max(1, min(int(limit), MAX_RECENT))
    return find_transactions(store, customer_id, limit=n)[:n]


def get_transaction(store: Store, customer_id: str, transaction_id: str) -> dict:
    rows = store.query(f"SELECT {TX_COLUMNS}, t.customer_id FROM transactions t JOIN products p USING (product_id) "
                       "WHERE t.transaction_id = ?", [transaction_id])
    if not rows:
        raise KeyError(transaction_id)
    if rows[0].pop("customer_id") != customer_id:
        raise Unauthorized(transaction_id)
    return rows[0]


def merchant_history(store: Store, customer_id: str, merchant: str, before: datetime) -> dict:
    row = store.query_one("SELECT count(*), max(transaction_date) FROM transactions "
                          "WHERE customer_id = ? AND merchant_name = ? AND transaction_date < ?",
                          [customer_id, merchant, before])
    return {"previous_count": row[0], "last_date": row[1]}


def card_status(store: Store, customer_id: str, product_id: str) -> dict:
    rows = store.query("SELECT product_type, last4, product_status, expiration_date, currency, customer_id "
                       "FROM products WHERE product_id = ?", [product_id])
    if not rows or rows[0].pop("customer_id") != customer_id:
        raise Unauthorized(product_id)
    return rows[0]


# Channels a customer may name, mapped to the outbound record's channels.
CHANNELS = {"sms": ["SMS"], "whatsapp": ["WhatsApp"], "email": ["Email"], "push": ["Push"],
            "call": ["Voice"], "any": ["SMS", "WhatsApp", "Email", "Push", "Voice"]}


def outbound_check(store: Store, customer_id: str, channel: str, around: datetime | None,
                   asked_for_secret: bool) -> dict:
    """The "is this really my bank?" check. A lookup and a fixed rule decide, never a model.

    Verdicts:
      scam_asks_secret : the contact asked for a code, PIN, or password (the bank never does)
      bank_contact     : the record shows a contact on that channel around that date
      no_record        : nothing in the record; treat as a scam (the record lacks alerts and
                         collections, so the wording says "no record", not "certainly fake")
    """
    if asked_for_secret:
        return {"verdict": "scam_asks_secret", "matches": []}
    around = around or store.as_of
    rows = store.query(
        "SELECT contact_id, contact_ts, channel, kind FROM outbound_contacts WHERE customer_id = ? "
        f"AND channel IN ({', '.join('?' * len(CHANNELS[channel]))}) AND contact_ts BETWEEN ? AND ? "
        "ORDER BY contact_ts DESC LIMIT 3",
        [customer_id, *CHANNELS[channel], around - timedelta(days=2), around + timedelta(days=1)])
    return {"verdict": "bank_contact" if rows else "no_record", "matches": rows}


def under_compliance_review(store: Store, customer_id: str, transaction_id: str) -> bool:
    """FR-018: charges under anti-money-laundering review are never explained. The list is synthetic in this
    dataset (see app.data.build); in production it would come from the compliance system."""
    row = store.query_one("SELECT count(*) FROM compliance_reviews WHERE transaction_id = ? AND customer_id = ?",
                          [transaction_id, customer_id])
    return bool(row and row[0])
