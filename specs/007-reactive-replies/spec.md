# Feature Specification: Answers that react to what I ask

**Feature Branch**: `007-reactive-replies`

**Created**: 2026-10-01

**Status**: Draft

**Input**: User description: "as user, I'd like the app answer my question(s), not just a meer needless answer. e.g. if user say hello, it should response properly, or if user ask for user's last movements, it should retrieve at least las 5 movements from user's account. It should be more reactive based on user's input"

## Context

Measured in rules mode on 2026-10-01, before this feature:

| The customer writes | Today's reply |
|---|---|
| "Muéstrame mis últimos movimientos" / "show me my last transactions" | "To find the charge I need at least one more detail…" |
| "Quais são minhas últimas transações?" | "I can't help with that here…" (out of scope) |
| "gracias" / "obrigado" / "thanks!" | out of scope |
| "¿qué puedes hacer?" / "help" | out of scope |
| "boa tarde" / "good evening" / "how are you?" / "¿cómo estás?" | out of scope |
| "hola" while "was it you?" is pending | "To continue I need your answer…" and the question (specs/006). Correct, but it doesn't return the greeting |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - My last movements (Priority: P1)

The customer asks for their recent movements, and the assistant shows their last 5 from their own account. Each is a numbered card (date, amount, merchant, status), and the reply invites them to pick one to review.

**Why this priority**: it's the most common thing a customer asks before disputing a charge, and the customer who doesn't remember the amount or merchant has no other way to find it.

**Independent Test**: in each language, ask for the last movements. Five cards appear, the newest first, from the signed-in customer's account only. Replying with a number explains that charge.

**Acceptance Scenarios**:

1. **Given** a signed-in customer, **When** they ask for their last movements in English, Spanish, or Portuguese, **Then** the reply shows their 5 most recent movements of the last 90 days, newest first, as numbered cards, with every amount and date from their records.
2. **Given** the customer asks for a number of movements ("my last 8 movements"), **Then** that many are shown, from 1 up to 9. A larger number shows 9, and the reply says so.
3. **Given** the cards, **When** the customer replies with a number, **Then** that movement is explained and the usual "was it you?" follows (unchanged).
4. **Given** a customer with no movements in the last 90 days, **Then** the reply says so and asks for the details of the charge.
5. **Given** a request for another customer's movements, **Then** it is refused, exactly as today.
6. **Given** a request with details ("my last movements at Uber"), **Then** the details win: it's the usual charge search.

### User Story 2 - Courtesy and help get a proper answer (Priority: P1)

Greetings (any time of day, "how are you?"), thanks, and "what can you do?" / "help" each get a fitting reply in the customer's language.

- **A pending question** ("was it you?", "which one?", "did you share anything?"): the courtesy is answered briefly ("Hello, Sebastián." / "You're welcome."), and the question is asked again.
- **Otherwise**:
  - a greeting gets today's welcome;
  - thanks get "You're welcome", plus what else the assistant can do;
  - help gets what the assistant can do, with examples.

**Why this priority**: answering "thanks" with "I can't help with that here" is the clearest case of a reply that ignores the customer.

**Independent Test**: send each courtesy phrase in each language, with and without a pending question. Each gets its fitting reply, never the out-of-scope message.

**Acceptance Scenarios**:

1. **Given** no pending question, **When** the customer greets ("hola", "boa tarde", "good evening", "how are you?"), **Then** the reply greets them by name and says what the assistant can do.
2. **Given** no pending question, **When** the customer thanks, **Then** the reply is "You're welcome" plus an offer of further help.
3. **Given** any stage, **When** the customer asks "what can you do?" or "help", **Then** the reply lists what the assistant can do, with example phrasings including the new "show my last movements". At a pending question, the question follows.
4. **Given** a pending question, **When** the customer greets or thanks, **Then** the reply is the short courtesy plus the question again, and the quick replies stay.
5. **Given** a courtesy phrase together with a request ("hola, no reconozco un cargo de 40"), **Then** the request is handled as today.
6. **Given** a real out-of-scope request (a loan, the balance, a transfer), **Then** the out-of-scope reply is unchanged.

### Edge Cases

- **"últimos 8 movimientos"**: 8 is a count, not an amount of 8.
- **The progress panel** (specs/006):
  - the movement list is the charge path's stage 2 ("We find the charge"), and choosing one moves to stage 3;
  - a courtesy or help message never moves it.
- **A charge under compliance review** in the list: the card shows only what any card shows. Choosing it gets the existing compliance hold, with nothing disclosed.
- **Language switch** (specs/004): the list re-shows in the new language, like other candidate lists.
- **The PDF** (specs/002): records the list like any candidate list.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-701**: The assistant MUST recognise a request for recent movements in English, Spanish, and Portuguese, in the rules (no model needed). When the model is on, it may recognise it too.
- **FR-702**: It MUST then show the session customer's most recent movements of the last 90 days, newest first. The number shown is 5 by default, or the number asked for, from 1 up to 9.
  - Only the session's customer's movements are read (constitution II).
  - Every card value comes from a record (constitution III).
- **FR-703**: The cards MUST be choosable by number, as today's candidate lists are, and choosing one MUST lead to the usual explanation.
- **FR-704**: Greetings, thanks, and help requests MUST each get their own reply in the conversation's language, per US2. None MUST get the out-of-scope reply.
- **FR-705**: At a pending question, a courtesy or help message MUST be answered briefly and followed by the same question. The stage, the quick replies, and the progress MUST be unchanged.
- **FR-706**: Nothing changes for refusals, the guards, real out-of-scope requests, the claim flow, or the PDF format. Rules-mode evaluation MUST NOT get worse.
- **FR-707**: Demo example messages MUST include "show my last movements" in each language (specs/005 order kept: charge, contact, then the new one, then scam and other customer).

### Key Entities

- **Movement list**: up to 9 of the customer's own movements, newest first, each a numbered option like a candidate charge.

## Success Criteria *(mandatory)*

- **SC-701**: Every listed phrasing for recent movements, in all three languages, shows the customer's newest 5 movements (100%), and choosing one explains it.
- **SC-702**: Every listed courtesy and help phrasing, in all three languages, gets its own reply. Out-of-scope replies to them: 0.
- **SC-703**: Rules-mode evaluation: no metric gets worse, and unsafe answers stay at 0.

## Assumptions

- **"Movements"** are the charge-type movements the assistant already searches (purchases, payments, withdrawals, transfers, adjustments), from the last 90 days. Deposits and balances stay out of scope.
- **The cap of 9** keeps the existing one-digit option reply; asking for more shows 9 and says so.
- **The scope stays one workflow, dispute intake** (constitution, Hackathon Constraints). Listing movements serves it: it is how a customer finds the charge to dispute.
