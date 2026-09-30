# Feature Specification: Explain This Charge (transaction-dispute intake)

**Feature Branch**: `main` (single-feature build; no feature branch)

**Created**: 2026-09-30

**Status**: Mostly built. See [Current Status](#current-status), which lists what is built and what remains.

**Input**: User description: "Transaction-dispute intake assistant for LATAM Bank customers in Mexico, Colombia, and Argentina, in Spanish and Portuguese.

- A customer who does not recognize a charge, or thinks it is wrong, gets it explained from the bank's own records, with every statement marked known, guessed, or rule. Pending charges are explained as pending.
- The customer confirms the charge was theirs, or files a complete claim.
- A customer who received a call or message claiming to be the bank can check it against the bank's outbound record, and escalates if they shared a code.
- Claims reach a human specialist through a structured handoff.
- The customer learns their rights but never a promised outcome.

Success is measured with the organizers' outcome measures on held-out cases, against the all-to-agent baseline." The source is the idea's go handoff in the ideation repository (`explain-this-charge/decision.md`).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand a charge I don't recognize (Priority: P1)

A customer sees a charge they don't recognize and describes it in their own words, in Spanish or Portuguese: an amount (exact, rounded, or in any format), a merchant, a day, or any mix.

The assistant finds the charge in the customer's own records. It explains it:

- merchant, amount and currency, date and time, city and country, channel, and the card or account ending;
- whether the customer has paid this merchant before;
- whether the charge is still pending.

Each statement is marked *verified* and cites its record. The assistant then asks whether the customer now recognizes the charge.

**Why this priority**: most doubts end when the customer sees the facts. This is the normal resolution path, and every other story builds on finding the right charge.

**Independent Test**: sign in as a test customer and describe one of their recent charges. The right charge is explained with sourced statements. Answer "sí, fui yo" and the case closes with no claim.

**Acceptance Scenarios**:

1. **Given** a signed-in customer with a matching charge, **When** they describe it by amount and merchant, **Then** the assistant explains that charge with each fact marked verified, and asks for confirmation.
2. **Given** the description matches several charges, **When** the assistant finds them, **Then** it lists them and asks which one, without asserting any of them as the disputed charge.
3. **Given** the charge is still pending, **When** it is explained, **Then** the customer is told it has not been applied yet and that holds are usually released on their own, without a release date the records do not hold.
4. **Given** an explained charge, **When** the customer says it was theirs, **Then** the case closes with no claim and no transfer to a person.

---

### User Story 2 - File a claim and reach a person with everything they need (Priority: P1)

After the explanation, the customer says the charge was not theirs. The assistant collects their account of what happened:

- whether they have the card;
- whether they shared a code or clicked a link;
- whether they filed a police report.

It then hands the case to a specialist. The customer gets:

- a case number;
- their rights while the claim is open, for their country (for example Mexico's provisional credit on qualifying debit-card charges, or no obligation to pay the disputed amount);
- the legal answer deadline;
- the next steps.

They never get a promised outcome.

**Why this priority**: this is the human-required case. The value is a complete, correct claim on first contact, because in the supplied data satisfaction follows resolution, not speed.

**Independent Test**: explain a charge, answer "no fui yo", then describe what happened. A handoff appears in the specialist view with the verified transaction, the customer's statement, card status, the country's rules and answer date, the risk estimate, and open questions. The customer's reply lists their rights and makes no promise.

**Acceptance Scenarios**:

1. **Given** an explained charge, **When** the customer says it was not theirs, **Then** the assistant asks for their account before transferring.
2. **Given** the customer's account, **When** the claim is filed, **Then** exactly one handoff is created, carrying the verified transaction and the rules of the customer's country.
3. **Given** the customer shared a code, or the charge looks like fraud, **When** the handoff is created, **Then** it is marked high priority.
4. **Given** any claim, **When** the assistant replies, **Then** it states rights and deadlines and never promises a refund or approval.

---

### User Story 3 - Check whether a call or message really came from my bank (Priority: P2)

A customer received a call, SMS, WhatsApp message, or email claiming to be the bank. They ask whether it was real. The assistant checks the bank's own record of contacts with that customer, and answers with one of three verdicts:

- **a real contact from the bank**, with the channel and date;
- **no record, so treat it as a possible scam**;
- **a scam**, because the contact asked for a code, PIN, or password, which the bank never does.

If the customer already shared a code, the case goes to a fraud specialist as urgent.

**Why this priority**: impersonation drives many unrecognized charges. Answering at once prevents fraud rather than processing it afterwards.

**Independent Test**: sign in as a customer who received a real bank SMS, and ask about it with the date. The verdict is "real contact". Ask about a call that requested a code, answer "yes, I shared it", and an urgent handoff appears.

**Acceptance Scenarios**:

1. **Given** the bank's record shows a contact on that channel around that date, **When** the customer asks, **Then** the verdict is "real contact".
2. **Given** the contact asked for a code or password, **When** the customer asks, **Then** the verdict is "scam", whatever the record shows.
3. **Given** a scam verdict, **When** the customer says they shared the code, **Then** an urgent handoff is created and the customer is told to freeze the card.
4. **Given** no matching contact, **When** the customer asks, **Then** the verdict is "no record, treat as a possible scam", worded as the absence of a record, not proof.

---

### User Story 4 - Get the same service in Portuguese (Priority: P2)

A Portuguese-speaking customer writes in Portuguese. Understanding, answers, quick replies, rights, and handoff notes all work in Portuguese.

**Why this priority**: the organizers require both languages. The dataset has no Portuguese, so the Portuguese cases are team-generated.

**Independent Test**: repeat Stories 1-3 in Portuguese. Replies and quick replies are in Portuguese, and outcomes match the Spanish runs.

**Acceptance Scenarios**:

1. **Given** a message in Portuguese, **When** the assistant replies, **Then** the reply is in Portuguese.
2. **Given** a Portuguese conversation, **When** the assistant asks a question, **Then** the suggested quick replies are in Portuguese.

---

### User Story 5 - Stay safe when the request is vague, unsupported, or hostile (Priority: P1)

The customer's message may be:

- vague ("hay un cargo raro");
- out of scope (a loan, a balance, a transfer);
- about data that does not exist;
- an attempt to see another customer's data;
- an attempt to override the assistant's instructions.

The assistant clarifies, abstains, or refuses. It never guesses a charge, discloses another customer's data, or follows injected instructions.

**Why this priority**: safety over autonomy is a judged requirement. A wrong answer about money or fraud is worse than a transfer.

**Independent Test**: send each kind of message. No transaction is asserted without a basis, another customer's data is refused, and injected instructions have no effect on permissions or promises.

**Acceptance Scenarios**:

1. **Given** a vague message, **When** the assistant replies, **Then** it asks for the amount, merchant, or day, and asserts no charge.
2. **Given** an out-of-scope request, **When** the assistant replies, **Then** it abstains and points to official channels.
3. **Given** a reference to another customer's ID, **When** the assistant replies, **Then** it refuses and records a security flag.
4. **Given** a message that tells the assistant to promise a refund, **When** it replies, **Then** it explains the charge normally and makes no promise.
5. **Given** the model misreads "no, no lo reconozco" as "it was mine", **When** the customer answers, **Then** the claim still proceeds. Closing requires an unambiguous affirmative.

---

### User Story 6 - Receive a complete, prioritized case as a specialist (Priority: P2)

A specialist opens a queue of handoffs, ordered by priority. Each handoff shows the customer and language, and the request and statement in the customer's words. It also shows:

- the verified transaction;
- card status;
- whether a code was shared;
- actions taken;
- the country's rules and answer date;
- the fraud-risk estimate;
- security flags;
- open questions, such as the authentication method, which is not in the data.

The specialist does not need to re-ask the customer anything the assistant already verified.

**Why this priority**: the handoff is where the saved time and the correct resolution happen. It is also the demo's human-required moment.

**Independent Test**: file a claim and a scam escalation. Both appear in the specialist view with every field above, urgent first.

**Acceptance Scenarios**:

1. **Given** several handoffs, **When** the specialist opens the queue, **Then** they are ordered urgent, high, normal.
2. **Given** a claim handoff, **When** the specialist reads it, **Then** the verified facts match the transaction the customer disputed.

---

### Edge Cases

- **The data service is unavailable.** The assistant says it could not check safely and hands the case to a person. It states no facts.
- **The session has expired.** The assistant refuses to continue and asks the customer to sign in again, returning no data.
- **The model is unavailable, refuses, or returns invalid output.** Rules and templates take over, with the same guarantees.
- **The model's rewording changes or adds a number, or promises something.** The rewording is discarded and the template text is shown.
- **The described amount matches nothing in the last 90 days.** The assistant says so and asks for the exact amount or the day.
- **The charge is in a different currency from the one the customer expects.** The currency in the records is reported as is. Exchange-rate stories are not supported.
- **The charge is under a suspicious-activity or anti-money-laundering review.** It is never explained, and it goes to a person.
- **The customer says "leave me alone" or answers ambiguously at the confirmation step.** The assistant asks again. It never closes on a guess.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST identify the customer from a trusted session. A customer ID, document number, or name typed in the conversation MUST NOT be accepted as identity.
- **FR-002**: The system MUST find candidate charges in the signed-in customer's own records from any combination of amount (exact, rounded within 1%, any common number format), merchant, and day (numeric, month-name, or relative, in Spanish or Portuguese), within the last 90 days.
- **FR-003**: The system MUST explain a single matched charge with merchant, amount and currency, date and time, city and country, channel, product and last four digits, and prior payments to the merchant. It MUST say when the charge is pending.
- **FR-004**: Every statement shown to the customer MUST be marked known (with the record it comes from), guessed (an estimate), or rule (with the rule it applies). A known statement without a record MUST NOT be shown.
- **FR-005**: When several charges match, the system MUST list up to five and ask the customer to choose. It MUST NOT assert any of them as the disputed charge.
- **FR-006**: The system MUST close a case as recognized only on an unambiguous affirmative. A negation MUST always proceed to a claim.
- **FR-007**: For a claim, the system MUST collect the customer's account and create one structured handoff containing:
  - the request and the customer's statement;
  - the verified transaction and the card status;
  - whether a code was shared;
  - the actions taken;
  - the applicable rights and legal answer date for the customer's country;
  - the fraud-risk estimate;
  - security flags;
  - open questions.
- **FR-008**: The system MUST tell the customer their rights and the deadlines for their country, and MUST NOT promise an outcome, refund, or approval.
- **FR-009**: The system MUST check a claimed bank contact against the bank's outbound record for that customer, channel, and date window, and return one of three verdicts: real contact, no record, or scam because it asked for a secret.
- **FR-010**: The system MUST treat any contact that asked for a code, PIN, password, or card data as a scam. If the customer shared one, it MUST escalate as urgent.
- **FR-011**: The system MUST never ask for codes, PINs, passwords, or card data.
- **FR-012**: The system MUST refuse any request involving another customer's data and record a security flag.
- **FR-013**: The system MUST ask a clarifying question for vague requests, and abstain for out-of-scope requests. In both cases it asserts no charge.
- **FR-014**: The system MUST hand the case to a person, stating no facts, when a data service fails. It MUST refuse to continue when the session has expired.
- **FR-015**: The system MUST converse in Spanish and Portuguese, following the customer's language, including quick replies that match the assistant's latest question.
- **FR-016**: The system MUST estimate fraud risk for a disputed charge. The estimate is used only for priority and one statement marked as an estimate, never to decide the claim.
- **FR-017**: The system MUST provide specialists with a queue of handoffs ordered by priority.
- **FR-018**: The system MUST NOT explain or discuss charges under an anti-money-laundering review.
- **FR-019**: The system MUST keep working, with the same safety guarantees, when the language model is unavailable.
- **FR-020**: The system MUST produce an evaluation report on held-out cases with the organizers' outcome measures, by language and customer segment, against the all-to-agent baseline.

### Key Entities

- **Customer**: a bank customer. Only first name, country, segment, status, and consent flags are used. Identity documents and contact details are excluded.
- **Product**: an account or card: type, currency, status, expiry, and last four digits.
- **Transaction**: a charge or movement: date, type, category, amount and currency, channel, merchant, place, status, and the existing detector's fraud score.
- **Outbound contact**: a message or call the bank sent to a customer: channel, date, and kind.
- **Session**: a signed-in customer's conversation: stage, language, the charge being discussed, and security flags. It expires after inactivity.
- **Statement**: one sentence shown to the customer, with its basis (known, guessed, or rule) and source.
- **Handoff**: the structured case a specialist receives (see FR-007).
- **Rule**: a country's consumer-protection or dispute rule, with an identifier, used for rights and deadlines.
- **Evaluation case**: a team-generated conversation tied to a real transaction or contact, with its expected outcome.

## Success Criteria *(mandatory)*

### Measurable Outcomes

The held-out test uses new customers and phrasings never used to tune the system. Numbers are for the model-assisted mode.

- **SC-001**: **Zero unsafe outcomes** on the held-out test sets: no wrong or unsupported charge asserted, no other customer's data, no promise, no request for a secret, no fake contact confirmed, no claim closed without a person, and no unsupported number. *Result so far: 0 of 168 on each set.*
- **SC-002**: At least **95%** of held-out cases reach their expected outcome. *Result so far: 95.2%.*
- **SC-003**: At most **5%** of cases that need a person fail to reach one (missed transfers), and **0%** of cases that don't need a person are transferred. *Result so far: 2.1% and 0%.*
- **SC-004**: At least **90%** of cases a machine may close are resolved safely without a person, against **0%** for the all-to-agent baseline. *Result so far: 94.2%.*
- **SC-005**: The same correct-outcome rate (within 5 points) in Spanish and Portuguese. *Result so far: 95.2% in each.*
- **SC-006**: Customers get an answer within **5 seconds** for 95% of turns, against a median of 120 seconds of waiting plus 431 seconds of handling for complaint contacts today. *Result so far: p95 3.7 s.*
- **SC-007**: The cost per case stays under **1 US cent**. *Result so far: $0.0033.*
- **SC-008**: The fraud-risk estimate catches more frauds than the bank's existing fixed threshold at the same precision, on months it never saw. *Result so far: 281 against 205 of 494, both at 100% precision.*

## Assumptions

- **Data**: the organizers' synthetic LATAM Bank dataset (June 2023 to June 2026) is the bank's record. "Today" is its last recorded transaction.
- **Conversations**: team-generated and labelled. The dataset holds no customer messages about disputes, and no Portuguese.
- **Identity**: sign-in is simulated by a test login standing in for the bank's identity service.
- **Legal rules** for Mexico, Colombia, and Argentina come from desk research. The financial specialist's validation is pending (see the ideation repository).
- **Outbound record**: the record lacks transactional alerts and collections, so "no record" is worded as absence of a record, not proof of a scam.
- **Excluded**:
  - deciding claims, refunds, money movement, and merchant blocking;
  - a real WhatsApp or phone channel;
  - installment and exchange-rate explanations, which the data cannot support;
  - any workflow other than dispute intake.
- **The fraud-risk estimate relies on the dataset's detector score**, which may be derived from the label. The model card states this plainly.

## Current Status

Built as of 2026-09-30, all verified by tests and by the evaluation:

- **Stories 1, 2, 3, 5, and 6** in Spanish, and **Story 4** in Portuguese.
- **The fraud-risk estimate** (FR-016, SC-008).
- **The evaluation report** (FR-020). It shows SC-001 to SC-007 met on the held-out test.
- **Quick replies** that match the assistant's question (FR-015).

Remaining:

- **Deployment**, for a public link to the running tool.
- **Repeated model-assisted runs** to report run-to-run variability.
- **A written limitations and future-work section.**
- **Slides and video** for the submission.
- **Folding in the specialist's validation** of the legal rules, when it arrives.
- **FR-018 is enforced as a policy but not exercised by the data**: the dataset flags no charge as under review. A synthetic test case would demonstrate it.
