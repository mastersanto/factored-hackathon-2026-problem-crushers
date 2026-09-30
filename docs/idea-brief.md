# Idea brief: Explain this charge

The team's pick for the Factored AI & Data Hackathon 2026, chosen on 2026-09-29 (rank 1 of 4 candidates, 84.4%). This brief condenses the assessment kept in the team's ideation repository (`factored-idea`, folder `.specify/assessments/explain-this-charge/`), which holds the full evidence, sources, and reviews. Where this brief and that assessment disagree, the assessment's latest dated section wins.

## Problem

In the supplied LATAM Bank data, unrecognized charges (12,297) and wrongful charges or fees (12,194) are **36.5% of all complaints**:

- they take a **median of 15-16 days** to resolve;
- about **20% breach their deadline**;
- complaint contacts are resolved at first contact only **43.6%** of the time.

Satisfaction depends on resolution, not speed: CSAT is 3.0 when a contact is resolved at first contact and 2.0 when it is not, for every contact reason.

Outside the data:

- unrecognized transactions were 39.8% of complaints to Colombia's financial regulator in 2025;
- Mexico recorded 2.48 million possible-fraud claims in the first half of 2025.

Customers in Mexico, Colombia, and Argentina wait days to learn whether a charge was theirs or correct, and some are pushed into disputes by contacts pretending to be the bank.

## The workflow

**One workflow: transaction-dispute intake**, following understand → decide → act → verify → escalate, in Spanish and Portuguese.

The assistant:

1. **Finds the questioned transaction** from the customer's description.
2. **Rules out harmless causes first.** A charge still pending is explained as pending, not disputed.
3. **Explains third-party charges** from the bank's records: merchant, amount, date and time, place, and category. Every statement is marked *known* (from a record) or *guessed*.
4. **Handles the bank's own charges** (fees, interest). For these it identifies the disputed charge but does not guess what the fee was. A clearly labelled synthetic fee schedule is optional.
5. **Checks "is this really my bank?"** Any message or call the customer mentions is looked up in the bank's own outbound record. There are three verdicts:
   - *yes, this was us*;
   - *no record, treat as a scam*;
   - *it asks for a code or PIN, so it is a scam*.

   A lookup and a fixed rule decide, never the model.
6. **Lets the customer confirm** the charge ("it was mine") **or file a complete claim**.
7. **Tells the customer their rights and the next step, never the outcome.** For example:
   - in Mexico, a provisional credit by the second business day in the cases the rules cover;
   - in Mexico and Argentina, no obligation to pay the disputed amount while the claim is open;
   - an unwanted recurring charge can be cancelled through the bank (Mexico: free, within 3 business days).
8. **Escalates** likely fraud, fake contacts, and fee disputes with a **structured handoff**. The handoff carries:
   - the request, the verified facts, and the actions taken;
   - the customer's statement, card status, whether a code was shared, and whether a police report exists;
   - the transaction's channel;
   - the legal deadline for the country (Mexico: 45 days to answer; Argentina: 15; Colombia: 15 business days to reverse a payment);
   - open questions.

**Never automated or explained:**

- charges under a suspicious-activity report or an open investigation, which go to a person without explanation;
- deciding claims, refunds, fee reversals, money movement, or merchant blocking;
- any request for codes, PINs, or passwords.

**Learned component:** an own-charge-versus-fraud estimate trained on `is_fraud` (4,316 labelled frauds in about 4.4 million transactions). Its baseline is the dataset's `fraud_score` at threshold 50, which catches 38.7% of fraud with no false positives, so a model must beat that without leaking the label.

## The three required cases

| Case | Example |
|------|---------|
| Normal | A customer does not recognize a charge; it is explained from the records and the customer confirms it was theirs. |
| Ambiguous or unsupported | The description matches several transactions, or the request is out of scope. The assistant clarifies or abstains. |
| Human required | Likely fraud, or a fake "fraud alert" that asked for a code, handed to a person with the full handoff and its legal deadline. |

## Success metrics (the organizers' outcome measures)

- **Safe automated resolution** over all in-scope cases, plus the share where automation was attempted.
- **Containment**, and **escalation quality** (missed and unnecessary transfers).
- **Unsafe outcomes** with counts and denominators:
  - fraudulent charges closed as "mine";
  - fake contacts confirmed as genuine;
  - fees described without a supporting record;
  - outcomes promised.
- **Operating efficiency**: p50/p95 latency, and cost per attempted case and per resolution, broken down by language and customer segment.
- **Baseline** from the data: 15-16 day median resolution, 43.6% first-contact resolution, about 20% SLA breaches.

## What the data cannot do (report these honestly)

- **No free text**: every complaint in a subcategory has the same description, and there is no link from a complaint to a transaction. Conversations must be team-generated and tied to real transactions.
- **Random fields**: response codes, SLA flags, credit repayment, and app-error timing are random with respect to the facts.
- **Little merchant variety**: only 24 merchant names, so "you have paid this merchant before" carries little weight.
- **Currencies follow the product, not the purchase**: there are no MXN transactions, and 52.8% of domestic purchases are in a foreign currency, so real exchange-rate explanations are out of reach.
- **Missing fields**: no installment field, no authentication method, no release dates for pending charges.
- **No Portuguese data**: Portuguese cases are team-generated and labelled.

## Still open with the financial specialist

- Whether Colombian banks may require a police report before processing a fraud claim, and Argentina's practice.
- Whether Mexico's recurring-charge cancellation covers every recurring card charge in practice.
- Typical fee values for the demo's synthetic fee schedule.
