# Data Model: Explain This Charge

Entities as built. The warehouse tables are built by `backend/app/data/build.py` and are read-only at runtime. Session, statement, and handoff live in the application.

## Warehouse (Parquet, minimized at build time)

### customers

| Field | Notes |
|-------|-------|
| customer_id | Key (`CLI-…`) |
| first_name | Used in greetings |
| country | `México` (normalized from two spellings), `Colombia`, or `Argentina` |
| segment | Premium, Plus, Basic, or Student; used for evaluation breakdowns |
| customer_status | Active, Inactive, Suspended, or Closed |
| accepts_marketing, detected_accent | Carried, not used by the workflow |

Dropped at build: document number and type, email, phones, address, date of birth, income, credit score, occupation.

### products

| Field | Notes |
|-------|-------|
| product_id, customer_id | Key; owner |
| product_type | For example `Tarjeta Crédito` or `Tarjeta Débito` |
| last4 | Last four digits of the account or card number. The full number is dropped. |
| currency, product_status, expiration_date, has_linked_app, days_past_due | Used for card status in handoffs |

### transactions

| Field | Notes |
|-------|-------|
| transaction_id, customer_id, product_id | Key; owner; product |
| transaction_date, transaction_type, transaction_category | Only Purchase, Payment, Withdrawal, Transfer, and Adjustment can be disputed |
| amount, currency, amount_usd | Currency follows the product; there is no MXN in the data |
| channel, merchant_name, merchant_category, transaction_country, transaction_city | Explained to the customer |
| transaction_status | Approved, Declined, Pending, or Reversed. Pending is explained as pending. |
| response_code | Carried; random in the synthetic data |
| is_fraud | Label for the learned component only; never shown |
| fraud_score | The existing detector's score, and the input to the risk estimate |

### outbound_contacts

| Field | Notes |
|-------|-------|
| contact_id, contact_ts, customer_id | Campaign messages and outbound calls |
| channel | SMS, WhatsApp, Email, Push, or Voice |
| kind, topic, delivered | `campaign` or `call`. There are no transactional alerts or collections, so "no record" is not proof. |

### complaints

Carried for context: case type, category and subcategory, affected product, status, and dates. The workflow does not read it yet.

## Application entities

### Session

- **Fields**:
  - id (random token) and customer;
  - created and last_seen;
  - stage and lang (`es` or `pt`);
  - candidates;
  - tx (the charge being discussed, with its risk estimate);
  - request_text;
  - pending_contact;
  - security_flags;
  - turns.
- **Expiry**: after 30 minutes without activity, the next turn returns `session_expired` and no data.

#### Stage transitions

```text
start ──describe a charge──▶ (1 match) confirm        (2–5) choose     (0 or >5) start (clarify)
choose ──pick option──▶ confirm
confirm ──clear yes (rules and model agree)──▶ closed           (no handoff)
confirm ──negation / "no fui yo"──▶ statement
confirm ──model says yes, rules do not──▶ confirm               (asks again: the close guard)
statement ──customer's account──▶ closed                        (handoff: unrecognized_charge or fraud_suspected)
start ──bank-contact check──▶ start                             (verdict: bank_contact / no_record)
start ──contact asked for a secret──▶ contact_shared            (asks: did you share it?)
contact_shared ──yes──▶ closed                                  (urgent handoff)
contact_shared ──no──▶ start
any ──data-service failure──▶ unchanged                         (technical_fallback handoff, no facts stated)
any ──another customer's id in the text──▶ unchanged            (refusal and security flag)
```

### Statement

- **Fields**: `text`, `basis` (`known`, `guessed`, or `rule`), and `source`.
- **Sources**:
  - known: `transaction:TRX-…`, `history:<merchant>`, or `outbound:<id>`;
  - guessed: `model:score_isotonic`;
  - rule: `rule:<id>`, `policy:<name>`, or `flow`.
- **Validation**:
  - a known or rule statement without a source is removed before display;
  - a model rewording is shown only if its numbers equal those of the statements it rewords, and it contains no promise.

### Understanding

- **Fields**: language, intent, amount, merchant (one of the dataset's merchants, or null), date, channel, asked_for_secret, shared_secret, option, other_customer_reference, injection_suspected, and source (`rules` or `llm`).
- **Intents**: dispute_charge, check_contact, confirm_mine, file_claim, choose_option, provide_statement, out_of_scope, greeting, and reconfirm (set by the guard).

### Handoff

- **Fields**:
  - case_id, created_at, and case_type (`unrecognized_charge`, `fraud_suspected`, `fake_contact_secret_shared`, or `technical_fallback`);
  - priority (`normal`, `high`, or `urgent`) and language;
  - customer (id, first name, country, segment) and request;
  - verified_facts (transaction id, date, amount, currency, merchant, city, country, channel, status, product, last4);
  - risk_estimate (probability, flagged, model);
  - actions_taken and security_flags;
  - customer_statement, shared_secret, and card;
  - rights (rule ids), answer_by, open_questions, and contact_channel.
- **Priority**:
  - urgent: a secret was shared with a fake contact;
  - high: a secret was shared during a claim, or the risk estimate is flagged;
  - normal: otherwise.

### Rule

- **Fields**: an `id` (for example `MX-LTOSF-23-deadline`, `CO-D587-reversal`, `AR-25065-no-block`, `MX-BANXICO-provisional-credit`) and text in `es` and `pt`.
- **Applicability**: by customer country. Mexico's provisional-credit rule also requires a debit card and a charge made within 48 hours of the claim.

### Evaluation case (git-ignored)

- **Fields**: id, category, language, kind, needs_human, customer_id, segment, country, turns, expected, and provenance.
- **Expected outcome**: fixed before the run, for example the transaction id, a verdict, whether a handoff is required, and its priority.
