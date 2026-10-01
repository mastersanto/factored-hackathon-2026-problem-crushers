# Feature Specification: Suggestions in the language I'm writing in

**Feature Branch**: `005-suggestions-language`

**Created**: 2026-10-01

**Status**: Draft

**Input**: User description: "as user I'd like to see answer suggestions in same language I'm writting on"

## Context

The chat offers two kinds of suggestions the customer can tap instead of typing:

- **Quick replies**: short answers to the question the assistant just asked ("Sí, fui yo" / "No fui yo", "Sí, lo compartí" / "No, no compartí nada", and the three statement answers).
  - They already follow the conversation's language (specs/004).
- **Example messages**: the starter suggestions shown before the first message, and again once a case is closed.
  - Today they are a fixed mix: the "I don't recognize this charge" example in Spanish, Portuguese, and English, then the bank-contact check, the scam call, and the "show me another customer's charges" test in Spanish only.
  - An English or Portuguese customer sees mostly Spanish suggestions, and tapping one switches the conversation to Spanish (specs/004, FR-407).

This feature makes every suggestion follow the language the customer is using.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Example messages in my language (Priority: P1)

A customer opens the chat. Every example message is in the app's current language, the one from the browser, the switcher, or what the customer last wrote, and covers the same situations in every language.

**Why this priority**: example messages are the first thing a customer can tap. In the wrong language they look broken, and tapping one silently switches the conversation to another language.

**Independent Test**: with the app in English, Spanish, and Portuguese in turn, sign in and check that every example message is in that language, and that tapping each one gets a reply in the same language.

**Acceptance Scenarios**:

1. **Given** the app in English, **When** the customer signs in, **Then** every example message is in English, and none is in Spanish or Portuguese.
2. **Given** the app in Spanish or Portuguese, **When** the customer signs in, **Then** every example message is in that language.
3. **Given** any language, **Then** the example messages cover the same situations as today, each in that language:
   - the customer's own recent charge (amount and merchant, from their data);
   - the bank-contact check (channel and date, from their data), when the customer has one;
   - the scam call that asked for a code;
   - the request for another customer's data.
4. **Given** an example message tapped, **Then** the reply is in the same language and the conversation's language does not change.

---

### User Story 2 - Suggestions follow me when the language changes (Priority: P1)

When the language changes, by writing in another language or with the switcher, every suggestion on screen changes to the new language at once.

**Why this priority**: the language can change mid-conversation (specs/004). Suggestions left in the old language pull the customer back into it.

**Independent Test**: in a Spanish conversation, write a message in Portuguese, then use the switcher to pick English. After each change, every suggestion on screen is in the new language.

**Acceptance Scenarios**:

1. **Given** quick replies on screen in one language, **When** the customer writes in another language, **Then** the next quick replies are in the new language (already the case; kept).
2. **Given** quick replies on screen, **When** the customer picks another language with the switcher, **Then** the same quick replies are shown in the new language, for the same question.
3. **Given** example messages on screen (before the first message, or after a case closed), **When** the language changes either way, **Then** the example messages are shown in the new language.
4. **Given** a quick reply tapped in any language, **Then** it is understood exactly as before: "yes" confirms only with the rules' agreement, and "no" always files the claim (constitution III).

---

### Edge Cases

- **A customer without a recent charge or a bank contact** in the demo data: only the examples that apply are shown, in the current language, as today.
- **Amounts and dates in examples** are written the way that language writes them: 1,234.56 in English and 1.234,56 in Spanish and Portuguese, and dates day first. Each example must still be understood and still find the same charge or contact.
- **Merchant names and channel names**: merchant names stay as recorded. Channel words follow the language ("correo" or "email", "llamada" or "call").
- **A suggestion tapped while the language is changing**: the suggestion shown is the one sent, and the reply comes in that suggestion's language.
- **Ended session or turn limit**: no suggestions are shown, as today.
- **Screen readers**: the suggestion groups keep their spoken names in the current language, and each suggestion is marked with its language.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-501**: Every example message MUST be in the app's current language (specs/004, FR-401). No example in another language may be shown alongside it.
- **FR-502**: The example messages MUST cover the same situations in English, Spanish, and Portuguese: the customer's recent charge, the bank-contact check when the data has one, the scam call that asked for a code, and the request for another customer's data.
- **FR-503**: Every example message MUST be understood in its language exactly like its Spanish counterpart: the same intent, the same charge or contact found, the same verdict, refusal, or safety flag. Tapping it MUST NOT change the conversation's language.
- **FR-504**: Quick replies MUST be in the conversation's current language. When the switcher changes the language, the quick replies for the pending question MUST be shown in the new language without the customer sending anything.
- **FR-505**: When the language changes, the example messages on screen MUST change to the new language at once.
- **FR-506**: Amounts and dates inside example messages MUST be written in that language's format (specs/004, research R5).
- **FR-507**: Suggestions MUST keep the specs/003 rules: 44 × 44 px tap targets on phones, no sideways scroll from 360 px, spoken names for each group, and each suggestion marked with its language.
- **FR-508**: This feature MUST NOT change what the assistant understands or says, its guards, or the evaluation results.

### Key Entities

- **Example message**: a starter suggestion built from the signed-in customer's own demo data (a recent charge or bank contact) or a fixed demo situation (scam call, request for another customer's data). It exists in each of the three languages, and the one in the app's language is shown.
- **Quick reply**: an answer to the assistant's pending question, one set per language, chosen by the conversation's stage.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-501**: In each of the three languages, **100%** of the suggestions on screen (example messages and quick replies) are in that language, before the first message, at each question, and after a case closes.
- **SC-502**: Tapping each example message in each language gives a reply in that same language, with the same outcome as its Spanish counterpart (the same charge found, verdict, refusal, or flag), in **100%** of cases.
- **SC-503**: After a language change by writing or by the switcher, every suggestion on screen is in the new language within the same screen update. The customer never sees suggestions in two languages at once.
- **SC-504**: The existing tests, UI checks, and evaluation results are unchanged.

## Assumptions

- **"The language I'm writing in"** is the app's current language as specs/004 defines it: from the browser, then the language of the customer's latest clear message, or the switcher, whichever came last. Before the first message, it is the browser's or the switcher's language.
- **The demo's mixed-language examples are no longer needed.** They let a judge try Portuguese and English from one screen. With the EN / ES / PT switcher (specs/004), each language's examples are one tap away, so mixing is unnecessary. The demo path (Spanish, then Portuguese) uses the switcher or a typed message.
- **Wording**: the English and Portuguese examples are team-written translations of the Spanish ones, in the same register as the assistant's texts, labelled team-generated. The request for another customer's data keeps the same made-up customer ID.
- **Quick replies already exist in all three languages** (specs/004). This feature only ensures they are re-shown in the new language when the switcher changes it.

## Out of Scope

- New kinds of suggestions, or suggestions generated by a model.
- Changing the wording of the existing Spanish suggestions.
- Changes to understanding, the workflow, the guards, or the PDF.
