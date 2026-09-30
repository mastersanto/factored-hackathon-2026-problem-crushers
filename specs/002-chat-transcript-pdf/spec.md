# Feature Specification: Chat transcript as a PDF, for the customer's records

**Feature Branch**: `main` (single-builder repository; no feature branch)

**Created**: 2026-09-30

**Status**: Draft (clarified 2026-09-30)

**Input**: User description: "as bank's customer I'd like to import current chat as pdf as evidence". "Import" is read as **export**: the customer downloads the current conversation as a PDF to keep as evidence.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Download my conversation as a PDF (Priority: P1)

A customer has talked to the assistant about a charge. They might have confirmed it, filed a claim, or checked a suspicious call. They want a copy of what was said, to keep or to show later: for example to the bank's specialist, a regulator, the police, or a merchant. From the chat they choose "Descargar conversación (PDF)" (Portuguese: "Baixar conversa (PDF)") and get a PDF of the conversation up to that moment.

**Why this priority**: this is the whole feature. A claim often takes weeks (a median of 15 days in the bank's data), and customers are routinely asked what they were told and when. Without a copy they rely on memory.

**Independent Test**: have a conversation that files a claim, download the PDF, and check it against the chat on screen. It holds every customer message and every assistant message in order, with timestamps, the case number, and the rights and deadlines stated.

**Acceptance Scenarios**:

1. **Given** a signed-in customer with at least one exchange in the conversation, **When** they choose the download action, **Then** they receive a PDF that contains every message shown in the chat, in order, each with its author (customer or assistant) and time.
2. **Given** a conversation in which a claim was filed, **When** the customer downloads the PDF, **Then** the PDF shows the case number and the deadline stated in the chat, exactly as the chat showed them.
3. **Given** assistant messages whose statements carry sources (*verificado*, *estimación*, *política*), **When** the PDF is produced, **Then** each statement keeps its label and source reference, so the reader can tell a verified fact from an estimate or a rule.
4. **Given** a conversation with no exchange yet, **When** the customer looks for the download action, **Then** it is unavailable.

---

### User Story 2 - A document that is identifiable and honest about what it is (Priority: P1)

Whoever reads the PDF later (the customer, a specialist, a regulator) can tell what it is: which bank service produced it, for which customer, which conversation, when, and in which country. It also says plainly what it is not: it is not a claim decision, not a promise of a refund, and not a legal certification.

**Why this priority**: evidence is only useful if a third party can place it. An unlabeled document, or one that reads like a promise, would harm the customer or the bank (Principle III).

**Independent Test**: download a PDF and have someone who didn't see the chat identify the conversation, date, country, and case number, and state what the document does and does not commit the bank to.

**Acceptance Scenarios**:

1. **Given** any downloaded PDF, **Then** it carries a header with the service name, the customer's first name and country, the conversation reference, the case number if one exists, the generation date and time with its time zone, and page numbers ("page X of Y").
2. **Given** any downloaded PDF, **Then** it carries a fixed notice, in the conversation's language: it is a copy of the conversation for the customer's records, it does not decide the claim, and it does not promise any outcome.
3. **Given** the same conversation downloaded twice with no new messages between, **Then** both PDFs hold the same conversation content and the same check code (only the generation time may differ).
4. **Given** a downloaded PDF and its check code, **When** a reader checks the code against the case number, **Then** the check confirms a match. **Given** a PDF whose messages were edited, **Then** the check fails.

---

### User Story 3 - The PDF in my language (Priority: P2)

A customer who talked in Portuguese gets the headings, labels, and notice in Portuguese; a Spanish conversation gets them in Spanish.

**Why this priority**: both languages are required, but the core value (the messages themselves) is already in the customer's language.

**Independent Test**: download a PDF from a Portuguese conversation and from a Spanish one, and check that every fixed text is in the conversation's language.

**Acceptance Scenarios**:

1. **Given** a conversation whose latest assistant message is in Portuguese, **When** the customer downloads the PDF, **Then** headings, source labels, and the notice are in Portuguese.
2. **Given** a conversation that switched language partway, **Then** messages appear as they were written, and fixed texts follow the language of the latest assistant message.

---

### Edge Cases

- **The charge is under compliance review.** The PDF shows only what the customer saw: the neutral message and the case number. It never reveals the review, case type, priority, fraud-risk estimate, or internal trace.
- **The customer typed a full card number, code, or PIN in the chat**, even though the assistant never asks for one. Card numbers are masked to their last four digits and codes or PINs are masked in the PDF, with a note that masking was applied. The rest of the customer's words appear verbatim.
- **A message is still streaming** when the customer asks for the PDF. The PDF includes only completed messages, or the action waits until the reply is complete.
- **The session has expired.** No PDF is produced, as with any other data (Principle II), and the customer is told to sign in again. The chat also reminds the customer, when a claim is filed, that they can download a copy before leaving.
- **A request names another customer's conversation.** It is refused and recorded as a security flag. A customer can only ever export their own current conversation.
- **The conversation hit the turn limit.** The PDF is still available and includes the turn-limit message.
- **The assistant ran in rules mode**, without the model. The PDF is identical in structure; it records what was shown.
- **A long conversation** (up to the 40-turn limit) breaks across pages without cutting a message's source labels from its text.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-101**: A signed-in customer MUST be able to download their current conversation as a PDF from the chat, once the conversation has at least one exchange.
- **FR-102**: The PDF MUST contain exactly the messages the customer saw, in order: customer messages verbatim (except FR-107 masking) and assistant messages as displayed, including any rewording that passed the faithfulness check, each with author and time.
- **FR-103**: Assistant statements MUST keep their basis label (known / guessed / rule, shown as *verificado* / *estimación* / *política* or their Portuguese equivalents) and their source reference.
- **FR-104**: The PDF MUST carry a header with:
  - the service name;
  - the customer's first name and country;
  - the conversation reference and, if one exists, the case number;
  - the generation date and time with its time zone;
  - page numbers.
- **FR-105**: The PDF MUST carry a fixed notice in the conversation's language: a copy for the customer's records, not a claim decision, not a promise of any outcome. The notice MUST pass the same no-promise rule as every customer-facing text.
- **FR-106**: The PDF MUST NOT contain anything the customer's chat did not show. That includes the internal trace, case type, priority, fraud-risk estimate, security flags, compliance-review status, and other customers' data.
- **FR-107**: The PDF MUST mask full card numbers to their last four digits and mask anything the customer marked or the system detected as a code, PIN, or password, and it MUST say that masking was applied.
- **FR-108**: The PDF MUST be available only to the session's own customer, only for that session's conversation, and only while the session is valid. Other requests MUST be refused, and a request for another customer's conversation MUST be recorded as a security flag.
- **FR-109**: Fixed texts in the PDF (headings, labels, notice) MUST be in the language of the latest assistant message, Spanish or Portuguese.
- **FR-110**: The PDF MUST include the rights and deadline statements given in the chat exactly as shown, with their rule references.
- **FR-111**: Each PDF MUST print a check code derived from the transcript's content. The bank MUST store only that fingerprint, never the conversation text, with the case if one exists, otherwise with the conversation reference. Someone holding the check code and the case number or conversation reference MUST be able to confirm whether a PDF's content matches what the bank recorded: any change to a message, time, label, or case number makes the check fail. A PDF downloaded again after new messages gets a new code; earlier codes stay valid for the earlier content.
- **FR-112**: Producing a PDF MUST NOT call a language model or change the conversation, so it adds no model cost and cannot alter what was said.

### Key Entities

- **Conversation transcript**: the ordered messages of one session as the customer saw them: author, time, text, and for assistant messages the statements with basis and source. It also carries the case number, if any, and the conversation's language.
- **Transcript fingerprint**: the only thing the bank keeps about the conversation's text: the check code, the case number or conversation reference, and the generation time. It holds no message text.
- **Transcript document**: the PDF produced from a transcript: the check code, header (service, customer first name and country, conversation reference, case number, generation time and zone), the messages, the fixed notice, the masking note if any, and page numbers.
- **Session** and **Handoff**: as in `specs/001-dispute-intake-assistant/spec.md`. The session decides who may download; the handoff provides the case number.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-101**: A customer gets their PDF in **under 5 seconds** from choosing the action, for conversations up to the 40-turn limit.
- **SC-102**: In a check over the held-out evaluation conversations (both languages, every category), **100%** of PDFs contain every displayed message in order, with its labels and sources, and the case number when one exists.
- **SC-103**: **Zero** PDFs contain internal data (trace, case type, priority, risk estimate, compliance status) or another customer's data, including every compliance-review case in the evaluation.
- **SC-104**: **Zero** PDFs contain an unmasked full card number or a code a customer typed, on the evaluation cases seeded with one.
- **SC-105**: A reader who did not see the chat can identify the conversation's date, country, and case number, and states correctly that the document does not promise an outcome, in a check with at least 5 people or reviewers.
- **SC-106**: Producing PDFs adds **$0** in model cost.
- **SC-107**: **100%** of unaltered PDFs pass the check-code verification, and **100%** of PDFs with any edit to a message, time, label, or case number fail it, on the evaluation conversations.

## Assumptions

- **"Import" means export.** The customer takes the chat out of the app as a PDF; nothing is uploaded into the chat.
- **The customer triggers the download from the chat**, in the web app. Emailing or sending the PDF through WhatsApp is out of scope, since the prototype has no real channels.
- **Legal weight**: the PDF is a customer's copy, not a certified record or electronic signature. Whether a regulator in Mexico, Colombia, or Argentina accepts it is outside this feature and is not claimed.
- **Verification needs no conversation text**: the bank keeps only the fingerprint, so no new retention policy for conversation text is needed. The fingerprint's own retention follows the case. Who may run a check (the customer, a specialist, or a regulator) and through which channel is decided in the plan.
- **Only the current session's conversation** can be exported. There is no history of past conversations in the prototype.
- **The specialist side is unchanged.** Handoffs stay structured and never carry a raw transcript (Principle III).
- **Identity** is the demo login standing in for the bank's identity service, as in feature 001.
- **Priority against the deadline**: this is an addition to a submitted-quality build. Whether it lands before 2026-10-05 is a planning decision, not part of this spec.

## Clarifications

### Session 2026-09-30

- Q: How can a reader confirm the PDF matches the bank's record? → A: Option B (the owner's choice): a customer copy plus a check code. The bank stores only a fingerprint of the transcript, with the case, never the conversation text (FR-111, SC-107).
