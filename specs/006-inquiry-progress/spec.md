# Feature Specification: Replies and progress that follow my inquiry

**Feature Branch**: `006-inquiry-progress`

**Created**: 2026-10-01

**Status**: Draft

## Clarifications

### Session 2026-10-01

- Q: Which stage model should the panel show? → A: customer-facing stages, one ordered list per path (charge: 5 stages; contact check: 4), replacing the internal step names in the panel (FR-602).

**Input**: User description: "as user, while interacting with the chat, I'd like to receive answers or questions based on what I write, and the step (check attached image), should reflect the current status/progress of the inquiry/answer"

## Context

The chat has a "How we review your case" panel: a rail beside the chat on wide screens, and a closed drawer on phones whose header reads "Step N of 5 · name" (specs/003).

- **What the panel shows today**: the five internal workflow steps (Understand, Decide, Act, Verify, Escalate). The current step is the furthest step reached while producing the **latest reply**, not the state of the customer's inquiry.
  - Almost every reply goes through "Verify", so the panel reads "Step 4 of 5 · Verify" after a greeting, after "I need one more detail", after "was it you?", and after a closed case alike.
  - It only reaches "Escalate" on the turn a case is sent to a specialist. On the next message it falls back to step 4.
  - It never says what the customer is waiting for, or what is left.
- **What the replies do today**: they come from fixed wordings per situation.
  - **Missing details**: "I need at least one more detail: the amount, the merchant, or the approximate day", even when the customer already gave one of them. The reply doesn't say what was understood or what was searched for.
  - **No match**: "I didn't find a matching charge" doesn't say which amount, merchant, or day was searched.
  - **An off-topic or unclear message while a question is pending**: for example, at "was it you?" or "did you share a code?", the reply is the generic "I can't help with that here", and the pending question is not asked again. The quick replies stay on screen with no question above them.

This feature makes replies answer what the customer actually wrote, and makes the panel show where the customer's inquiry stands.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The step shows where my inquiry stands (Priority: P1)

At any moment, the panel shows the stage the customer's inquiry has reached, what has already happened, and what comes next. It moves forward as the inquiry progresses. It stays put when a message doesn't change the inquiry, and starts again only when a new inquiry starts.

**Why this priority**: the panel is the customer's sense of progress. Today it says "Step 4 of 5" whatever has happened, which reads as broken in the demo and tells the customer nothing.

**Independent Test**: follow the demo's claim path (charge found, "It wasn't me", the customer's account, case filed) and the contact-check path (scam verdict, "did you share it?", escalated). After each reply, compare the panel with the expected stage table (FR-602). Then send a greeting mid-inquiry: the panel doesn't move.

**Acceptance Scenarios**:

1. **Given** no message yet, **Then** the panel shows the inquiry not started, with the first stage as next.
2. **Given** a charge was found and the assistant asks "was it you?", **Then** the panel shows that the charge was found and that the customer's answer is awaited.
3. **Given** the customer answered "It wasn't me", **Then** the panel shows that the customer's account of what happened is awaited.
4. **Given** the case was sent to a specialist, **Then** the panel shows every stage done, with the case number. It stays that way on later turns until a new inquiry starts.
5. **Given** the customer recognized the charge ("Yes, it was me"), **Then** the panel shows the inquiry closed as recognized, not as escalated.
6. **Given** an inquiry in progress, **When** the customer sends a greeting, an off-topic message, or something unclear, **Then** the panel does not move backwards or forwards.
7. **Given** a closed inquiry, **When** the customer starts a new one (another charge, or a bank-contact check), **Then** the panel starts again from the first stage for that new inquiry.
8. **Given** a bank-contact check, **Then** the panel follows that path's stages (FR-602), not the charge path's.
9. **Given** a charge under compliance review, **Then** the panel shows the case sent to a specialist and nothing else about the charge, the same as the reply (constitution III, no tipping-off).
10. **Given** the phone drawer closed, **Then** its one-line summary names the current stage in plain words, in the app's language.

---

### User Story 2 - Replies answer what I wrote (Priority: P1)

Every reply responds to the customer's last message.

- **What was understood**: the reply repeats the details it understood (amount, merchant, day, channel), so the customer can see what was searched for.
- **Only what's missing**: it asks only for the details that are actually missing.
- **A pending question**: if a question is pending and the customer writes something that doesn't answer it, the reply says so briefly and asks the same question again.

**Why this priority**: a reply that ignores what the customer just wrote feels scripted and makes customers repeat themselves. This is the other half of what the owner asked for.

**Independent Test**: in rules mode (no model), send each message of the table in FR-605 at the stage shown. Each reply contains the details understood, asks only for what is missing, and, at a pending question, ends with that question again.

**Acceptance Scenarios**:

1. **Given** the customer writes "I don't recognize a charge at Cinépolis" and several charges match, **Then** the reply says it looked for charges at Cinépolis and lists the options.
2. **Given** the customer writes "I don't recognize a charge of 250" and nothing matches, **Then** the reply says it found no charge of 250 in the last 90 days and asks for the merchant or the day, not for the amount again.
3. **Given** the customer writes "there's a charge I don't recognize", with no detail, **Then** the reply asks for the amount, the merchant, or the day, as today.
4. **Given** the assistant asked "was it you?", **When** the customer writes something that is neither yes nor no (for example "what time is it?"), **Then** the reply says it can only help with this charge for now and asks "was it you?" again. The quick replies stay.
5. **Given** the assistant asked "did you share a code?", **When** the customer writes something unclear, **Then** the reply asks the same question again instead of the out-of-scope message.
6. **Given** a question is pending, **When** the customer asks about another charge ("actually it's a different charge, 1,200 at Oxxo"), **Then** the assistant leaves the pending question and searches for the new charge, as today.
7. **Given** any reply, **Then** every detail it repeats is what the customer wrote or what a record holds. Nothing is invented, and the reply is in the conversation's language.

---

### Edge Cases

- **The customer writes the same unclear thing twice at a pending question**: the question is asked again each time, until the turn limit. The panel doesn't move.
- **Details understood but the record doesn't match them** (amount understood, merchant not in the customer's history): the reply repeats only what was used to search, never a merchant the customer didn't name.
- **Masked text**: a detail repeated back never includes a code, PIN, card number, or anything masked (constitution, never ask for or echo secrets).
- **Injection attempts and other-customer requests**: the refusal is unchanged. Its wording is never built from the customer's text.
- **Language switch mid-inquiry** (specs/004): the panel and the repeated details are shown in the new language. The inquiry's stage doesn't change.
- **Re-shown conversation** (specs/004, switcher): the panel shows the same stage after the re-show as before it.
- **Technical fallback** (an error sends the case to a person): the panel shows the case sent to a specialist.
- **Session expired or turn limit reached**: the panel keeps the last stage, and the error message explains the rest.
- **The transcript PDF** (specs/002): unaffected. It records messages, not the panel. Byte-pinned renderers stay unchanged.

## Requirements *(mandatory)*

### Functional Requirements

**Inquiry progress (US1)**

- **FR-601**: The panel MUST show the current stage of the customer's **inquiry**: the charge being reviewed, or the contact being checked. It MUST NOT show the internal steps of the latest reply. The internal trace stays available under "Technical detail (demo)".
- **FR-602**: Each path MUST have a fixed, ordered list of customer-facing stages, named in plain words in English, Spanish, and Portuguese, each with a one-line description. One list per path (owner's choice, 2026-10-01: customer stages, option A):

  | # | Charge path | Contact-check path |
  |---|---|---|
  | 1 | Tell us what happened | Tell us about the contact |
  | 2 | We find the charge | We check the bank's records |
  | 3 | You confirm if it was you | You tell us if you shared anything |
  | 4 | You give your account | Done, or sent to a specialist |
  | 5 | Case closed or sent to a specialist | — |

  The final stage names the outcome: recognized, sent to a specialist with the case number, a genuine bank contact, no record found, or urgent.
- **FR-603**: The stage MUST come from the inquiry's state on the server, the same state that decides the next question. It MUST NOT come from guessing based on the reply text. It MUST be the same after a page re-show (specs/004) as before it.
- **FR-604**: The stage MUST move only when the inquiry changes. A greeting, an off-topic message, an unclear message, or a refused request leaves it where it was. A new inquiry after a closed one starts again at stage 1.

**Replies that follow the message (US2)**

- **FR-605**: Replies MUST respond to the customer's last message, as follows:

  | Situation | Today | Required |
  |---|---|---|
  | Search with some details, several matches | "I found several charges that could be it" | Also names the details searched for (amount, merchant, day) |
  | Search with some details, no match | "I didn't find a matching charge… confirm the exact amount or the day" | Names the details searched for, and asks only for details not yet given |
  | Too many matches | Asks for "another detail (amount, merchant, or day)" | Names the details given, and asks only for the missing ones |
  | No details at all | Asks for amount, merchant, or day | Unchanged |
  | A question is pending, and the message doesn't answer it and isn't a new charge or contact | Generic out-of-scope message | A short "I need your answer to continue", then the pending question again |
- **FR-606**: Every detail repeated back MUST be one the customer gave and the understanding extracted, or one a record returned. It MUST be formatted in the conversation's language (amounts and dates as in specs/004). It MUST never contain masked content.
- **FR-607**: The new wordings MUST be fixed templates filled with understood details, in English, Spanish, and Portuguese, available in rules mode (no model). When the model is on, it may phrase them, but only from those facts, under the existing faithfulness check (constitution I and III).
- **FR-608**: Quick replies MUST stay on screen while their question is pending, including after a re-asked question.

**Unchanged**

- **FR-609**: Nothing changes in how messages are understood, how charges are found, the guards (secrets, other customers, injection, compliance hold), case filing, or the PDF. Evaluation results in rules mode MUST NOT get worse on any existing metric.

### Key Entities

- **Inquiry**: what the customer is currently asking about: a charge or a bank contact. It has a path (charge or contact), a stage, and, once closed, an outcome (recognized, sent to a specialist with a case number, genuine contact, no record, urgent). One inquiry at a time per conversation; a new one replaces the closed one.
- **Inquiry stage**: one position in a path's ordered stage list (FR-602). It carries its name and description in each language.
- **Understood details**: the amount, merchant, day, and channel the understanding extracted from the customer's last message, used to search and repeated back in the reply.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-601**: Along the demo's claim path and contact-check path, the panel shows the expected stage after **every** reply in English, Spanish, and Portuguese (100% of checked replies).
- **SC-602**: In a greeting, off-topic, or unclear message sent mid-inquiry, the panel never moves (0 moves across the checked cases).
- **SC-603**: For every search reply in the evaluation sets, the reply names each detail the customer gave and that was used (100%), and asks again for none of them (0 repeated asks).
- **SC-604**: At every pending question, an unclear or off-topic message gets the same question asked again (100% of checked cases), in all three languages.
- **SC-605**: Rules-mode evaluation: no metric gets worse, and unsafe answers stay at 0.
- **SC-606**: In the owner's demo walkthrough, the panel's one-line summary on a phone matches what the customer is waiting for at each reply.

## Assumptions

- **"The step"** is the "How we review your case" panel: its rail on wide screens and the "Step N of 5" summary in the phone drawer. The image mentioned in the request was not received with it, so this spec relies on the panel as built (specs/003).
- **"Answers or questions based on what I write"** means the gaps listed in Context: generic wording that ignores the details given, and pending questions dropped after an off-topic message. It doesn't mean free-form answers to any question. The assistant's scope (charges and bank contacts) stays the same.
- The five internal steps stay in the technical trace for the demo and evaluation; only the customer-facing panel changes.
- The stage lists are the same for every country.
- This builds on specs/004 and 005 (three languages, the switcher, re-showing), all deployed.
- Redeploying needs the owner's approval, as usual.
