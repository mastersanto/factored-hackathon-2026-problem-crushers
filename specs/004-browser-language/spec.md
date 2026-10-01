# Feature Specification: The whole app in English, Spanish, or Portuguese

**Feature Branch**: `004-browser-language`

**Created**: 2026-09-30

**Status**: Draft (owner's answers to Q1-Q3 and follow-ups applied, 2026-09-30)

**Input**: User description: "as user I'd like to set the app language based on my browser preferences, having english as default, and spanish and portuguese as extra options. Other browser's language preference (if not spanish or portuguese) should display english as default"

## Clarifications

### Session 2026-09-30

- **Q1. Does "app language" include the conversation?** Yes. The assistant converses in English, Spanish, and Portuguese. Owner's direction for the design: an *interpreter* that processes every customer message into one common English form, and a *translator* that receives the target language as a parameter and produces what the customer sees.
- **Q2. Which language wins when the browser says one thing and the customer writes in another?** The language the customer is interacting in. An English browser whose user writes in Spanish switches the whole app to Spanish.
- **Q3. A language switcher?** Yes, with ES, PT, and EN.
- **Added by the owner**: switching language mid-conversation shows the whole previous conversation in the new language.
- **English as the base language** (owner, follow-up): the interpreter's common form uses English, so that more languages can be added later by adding only their understanding and their wording. Agreed reading: the common form is the language-neutral understanding with English names, and English is the source wording that every other language translates. The customer's words are not first translated into English text: understanding goes straight from any language to the common form, and the safety checks read the original words (FR-411, FR-412).
- **Demo path** (owner, follow-up): the demo starts in Spanish and switches to Portuguese mid-conversation. Re-showing the conversation on a switch (User Story 5) is therefore P1, and it does not depend on the English conversation (User Story 2).

## Context

- **Today**:
  - the conversation runs in Spanish or Portuguese only, detected from what the customer writes (specs/001, FR-015);
  - the sign-in screen, the header, and the specialist view are always in Spanish (specs/003, FR-203);
  - the chat's fixed texts follow the latest reply's language, and messages already shown are never re-translated (specs/003, FR-201 and FR-202).
- **What changes**: one *app language* (English, Spanish, or Portuguese) drives every screen and the conversation. It starts from the browser's preference, follows the language the customer writes in, and can be set with a switcher. Changing it re-shows the earlier conversation in the new language.
- **What must not change**: the deterministic core and its guards (constitution I to III). Finding transactions, the outbound-record check, country rules, deadlines, permissions, refusing other customers' data, catching requests for secrets, and the "no fui yo always files the claim" rule stay in code and must not depend on a model's translation.
- **Constitution**: its Hackathon Constraints name Spanish and Portuguese only. Adding English to the workflow needs an amendment (MINOR), approved by the owner, before implementation.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The app opens in my browser's language (Priority: P1)

A visitor opens the app. Every screen (sign-in, header, chat, specialist view) appears in their browser's preferred language if it is English, Spanish, or Portuguese, and in English otherwise.

**Why this priority**: it is the first thing every visitor and judge sees. Today the first screen is Spanish with English scenario labels, whatever the visitor's language.

**Independent Test**: open the app with the browser set to English, Spanish (Mexico), Portuguese (Brazil), and French, and check that every fixed text is in English, Spanish, Portuguese, and English respectively.

**Acceptance Scenarios**:

1. **Given** a browser whose first offered language is English, Spanish, or Portuguese (any region), **When** the visitor opens the app, **Then** every fixed text on every screen is in that language.
2. **Given** a browser listing only other languages (for example French, German, Japanese), or no preference at all, **When** the visitor opens the app, **Then** every fixed text is in English.
3. **Given** a browser listing French then Spanish, **When** the visitor opens the app, **Then** it opens in Spanish.
4. **Given** any of the above, **Then** the page never shows one language and then switches to another while loading.

---

### User Story 2 - I can talk to the assistant in English (Priority: P1)

A customer writes in English about a charge they don't recognize, a contact claiming to be the bank, or a claim. The assistant understands them and answers in English, with the same facts, sources, labels, guards, and handoffs as in Spanish and Portuguese.

**Why this priority**: the owner's answer to Q1. Without it, an English interface would surround a conversation the visitor cannot hold in English.

**Independent Test**: run the three required cases (normal path, ambiguous request, human-required case), the scam check, and the refusal of another customer's data, entirely in English, in rules mode and with the model, and compare the outcome of each with its Spanish counterpart.

**Acceptance Scenarios**:

1. **Given** an English message describing a charge, **When** the customer sends it, **Then** the assistant finds the same charge it would find for the Spanish message, and explains it in English with the same amount, date, merchant, card ending, and sources.
2. **Given** "it wasn't me" (or similar) in English after an explanation, **Then** the claim is filed exactly as "no fui yo" files it, and the English reply lists the country's rights and deadlines in English.
3. **Given** an English message saying someone claiming to be the bank asked for a code, **Then** the verdict is a scam, in English, and the case escalates if the customer shared it.
4. **Given** an English message naming another customer's ID, or trying to override the instructions, **Then** the request is refused and flagged exactly as in Spanish.
5. **Given** no model available (rules mode), **Then** every scenario above still works in English.

---

### User Story 3 - The app follows the language I write in (Priority: P1)

A visitor whose browser is in English signs in and writes in Spanish. The assistant answers in Spanish, and the whole app (header, chat texts, labels, buttons) switches to Spanish.

**Why this priority**: the owner's answer to Q2. Customers in Mexico, Colombia, and Argentina often have English or other-language browsers, and must still get their own language.

**Independent Test**: with an English browser, sign in, send a Spanish message, and check that the reply and every fixed text are in Spanish. Then send a Portuguese message and check the same in Portuguese.

**Acceptance Scenarios**:

1. **Given** the app in English, **When** the customer sends a message clearly in Spanish, **Then** the reply and every fixed text on screen are in Spanish.
2. **Given** the app in any language, **When** the customer sends something with no clear language (an option number, "ok", an amount, a date), **Then** the app language does not change.
3. **Given** a language switch triggered by a message, **Then** the earlier conversation is re-shown in the new language (User Story 5).

---

### User Story 4 - I can pick the language myself (Priority: P2)

A language switcher with ES, PT, and EN is always visible in the header, on every screen. Picking one switches the whole app at once.

**Why this priority**: the owner's answer to Q3. It helps on shared or borrowed devices, and lets a judge see each language.

**Independent Test**: on each screen, pick each language in turn and check that every fixed text switches at once, without a reload and without ending the conversation.

**Acceptance Scenarios**:

1. **Given** any screen, **When** the visitor picks a language, **Then** every fixed text switches at once, the switcher shows the current language, and an open conversation continues.
2. **Given** a language picked by hand, **When** the visitor reloads or comes back later on the same device, **Then** the app opens in that language, not the browser's.
3. **Given** a language picked by hand, **When** the customer then writes in another language, **Then** the app follows what they write (User Story 3): the most recent of the two signals wins.
4. **Given** a screen reader or a keyboard, **Then** the switcher is reachable and operable, each option has a spoken name in its own language ("English", "Español", "Português"), and the current one is announced.

---

### User Story 5 - Switching language re-shows the whole conversation (Priority: P1)

A customer is talking in Spanish and switches to Portuguese, by the switcher or by writing in Portuguese. Every earlier message, the assistant's and their own, is now shown in Portuguese.

**Why this priority**: the owner's addition, and the centre of the demo (Spanish, then a switch to Portuguese). A conversation half in one language and half in another is hard to follow, and the customer may hand the device to someone else. It works between Spanish and Portuguese without the English conversation.

**Independent Test**: hold a Spanish conversation that reaches a filed claim, switch to Portuguese, then to English, and check that every earlier message is shown in the new language with unchanged facts, sources, labels, and case number.

**Acceptance Scenarios**:

1. **Given** a conversation, **When** the language changes, **Then** every earlier assistant message is shown in the new language with exactly the same facts: the same amounts, dates, merchants, card endings, sources, labels, verdicts, and case numbers. No fact is added, dropped, or changed.
2. **Given** a conversation, **When** the language changes, **Then** every earlier customer message is shown translated into the new language, marked as a translation, with the customer's original words one tap away.
3. **Given** a translation that cannot be made (no model available, or the translation fails its checks), **Then** the original text is shown with a note that no translation is available. Nothing is invented.
4. **Given** a switch back to the original language, **Then** the original messages are shown exactly as first sent.

---

### Edge Cases

- **Several preferences**: the app takes the first entry in the browser's ordered list that it offers. French then Spanish shows Spanish; French then German shows English.
- **Region variants**: any English variant shows the app's English, any Spanish variant its Spanish (neutral Latin American, formal "usted"), and any Portuguese variant its Portuguese (Brazilian), including pt-PT.
- **Mixed or unclear messages**: a message mixing languages, or too short to tell ("1", "sí", "ok", an amount), keeps the current language. The language changes only on a clear signal.
- **A switch in the middle of a question**: if the assistant asked "was it you?" in Spanish and the customer switches to English, the pending question is re-shown in English, and "yes" or "no" in English answers it, with the same deterministic rules ("no" always files the claim).
- **Rules-mode translation**: with no model, the assistant's earlier messages are still re-shown in the new language (they are built from verified facts and fixed wording). Customer messages are shown in their original words, with a note.
- **Country rights texts** (deadlines, the right not to pay while a claim is open) appear in the conversation's language, including English, and keep their rule IDs.
- **Model-reworded replies**: when a reply was reworded by the model, the re-shown version in a new language must pass the same faithfulness check (the same numbers, no new ones, no promises). Otherwise the fixed wording in the new language is shown.
- **The conversation PDF** (specs/002): downloaded in the current app language. See FR-424 to FR-426.
- **The specialist's case**: the specialist sees the case in their own app language. The customer's own words are shown as written, with a translation into the specialist's language beside them, marked as such.
- **Sign-in errors** (session limit, failed sign-in, server unreachable) appear in the app language.
- **Demo scenario labels** on the sign-in cards appear in the app language.
- **The page's declared language** for screen readers matches what is on screen, and each message is marked with the language it is shown in.
- **Spending**: translating earlier messages must not make a language switch costly: a switch does not re-run the model on facts it already has wording for, and it counts against the same model-spend cap as every other call.

## Requirements *(mandatory)*

### The app language

- **FR-401**: The app MUST have one app language at a time: English, Spanish, or Portuguese. It drives every fixed text on every screen and the language of the assistant's replies.
- **FR-402**: On first load, the app language MUST come from the browser's ordered preferences: the first entry whose primary language is English, Spanish, or Portuguese. If there is none, or the browser reports none, it MUST be English.
- **FR-403**: All regional variants MUST map to the one variant the app offers: English, Spanish (neutral Latin American, formal "usted"), Portuguese (Brazilian).
- **FR-404**: The app language MUST be settled before the first text is shown: no flash of another language.
- **FR-405**: A header switcher with ES, PT, and EN MUST be available on every screen. Picking a language MUST switch the whole app at once, without a reload or ending the conversation.
- **FR-406**: A language picked by hand MUST be remembered on that device and used on the next visit in place of the browser's preference. Only the choice is stored, on the device. Nothing about it is sent to or kept by the bank's side beyond the current session.
- **FR-407**: When the customer sends a message clearly in English, Spanish, or Portuguese, the app language MUST become that language. A message with no clear language MUST NOT change it. The most recent signal, the switcher or a clear message, wins.
- **FR-408**: Every fixed text MUST follow the app language: sign-in (including the demo scenario labels and errors), the header, the security notice, the chat (opening line, input hint, buttons, source labels and their explanations, verdicts, case note, flow panel, spoken names), and the specialist view. This replaces specs/003 FR-201 to FR-203.
- **FR-409**: The page's declared language MUST match the app language, and each message MUST be marked with the language it is shown in.

### Understanding any of the three languages (interpreter)

- **FR-410**: The assistant MUST understand customer messages in English, Spanish, and Portuguese, turning each one into the same language-neutral understanding (intent, amount, merchant, date, channel, and safety signals) whatever its language. Every decision after that point MUST be the same for the same meaning, in any language.
- **FR-411**: The safety checks MUST run in code on the customer's original words, in every language, before and independently of any model translation: requests for codes, PINs, or passwords; references to another customer; attempts to override the instructions; and the negation that always files a claim. A model's interpretation MUST NOT be able to drop any of them (constitution II and III).
- **FR-412**: Understanding MUST work in all three languages with no model available (rules mode), as it does today for Spanish and Portuguese.
- **FR-413**: The interpreter MUST detect the message's language and report it with the understanding, to drive FR-407.

### Answering in the app language (translator)

- **FR-414**: Every reply MUST be produced in the language it is asked for, English, Spanish, or Portuguese, from the verified statements, with every statement keeping its basis and source.
- **FR-415**: Every reply MUST have fixed wording in all three languages, so the assistant answers in any of them with no model available.
- **FR-416**: When a model rewords a reply in any language, the rewording MUST pass the existing faithfulness check (the same numbers, no new numbers, no promises), with the promise list extended to English. Otherwise the fixed wording is shown.
- **FR-417**: The country rights and deadlines (Mexico, Colombia, Argentina) MUST exist in English with the same rule IDs and meaning, labelled as synthetic policy and team-translated.
- **FR-418**: Quick replies MUST be offered in the app language, and MUST work when tapped in that language.
- **FR-419**: Every English text MUST meet the rules every customer-facing text meets: no promise of a claim's outcome, a refund, or approval; never asking for codes, PINs, passwords, or card data; and nothing explained about a charge under compliance review.

### Re-showing the conversation

- **FR-420**: When the app language changes, every earlier assistant message MUST be re-shown in the new language with exactly the same statements, bases, sources, verdicts, charge options, and case numbers. Facts MUST NOT be added, dropped, or altered.
- **FR-421**: Re-showing assistant messages MUST work with no model, from their verified statements and the fixed wording in the new language.
- **FR-422**: Every earlier customer message MUST be shown translated into the new language, marked as a translation, with the original one tap away. Without a usable translation, the original MUST be shown with a note. The original words MUST be kept as the record.
- **FR-423**: Returning to a message's original language MUST show it exactly as first sent or shown.

### The PDF and the specialist

- **FR-424**: The conversation PDF MUST be produced in the app language at the time of download: fixed texts and assistant messages in that language, rendered from the same verified statements.
- **FR-425**: In the PDF, each customer message MUST appear in the customer's original words, with the translation beneath it, marked as a translation, when the PDF's language differs.
- **FR-426**: The PDF's check code MUST still detect any change to the file, and the language MUST be part of what it covers. PDFs issued before this feature MUST keep verifying.
- **FR-427**: The specialist's case MUST show the customer's words as written, the conversation's language, and a marked translation into the specialist's app language. The verified facts are not translated.

### What must not change

- **FR-428**: For the same meaning, the workflow MUST take the same decisions, call the same tools, read the same data, and apply the same guards in all three languages. Permissions stay in the tool layer, keyed by the session.
- **FR-429**: Every existing workflow, guard, security, and transcript test MUST keep passing. The Spanish and Portuguese evaluation results MUST NOT get worse.
- **FR-430**: Only the fields a turn needs MUST be sent to a model for interpreting or translating. Never another customer's data or identity documents (constitution IV).

### Evaluation

- **FR-431**: English MUST get its own team-generated evaluation cases in every category, including held-out phrasings the rules never saw, written before the system runs on them (constitution V).
- **FR-432**: The evaluation MUST add cases that switch language mid-conversation, including at the "was it you?" question, and check that facts and outcomes are unchanged.
- **FR-433**: The evaluation report MUST break results down by language, English included, in rules mode and with the model.

### Key Entities

- **App language**: English, Spanish, or Portuguese. Set from the browser on first load, by the switcher, or by the language of the customer's latest clear message. The most recent signal wins. A choice made with the switcher is remembered on the device.
- **Message language**: the language the interpreter detects in each customer message, or "unclear".
- **Understanding**: the language-neutral meaning of a customer message (intent, slots, safety signals). It is the same for the same meaning in any language.
- **Verified statement**: one fact or rule, with its basis and source, independent of language. It can be worded in any of the three languages.
- **Customer message**: the original words (the record) and, when shown in another language, a marked translation.
- **Interface text set**: the fixed texts in one language. There are three: English, Spanish, Portuguese.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-401**: With the browser set to each of 10 representative preference lists (single languages, region variants, mixed orders such as French then Portuguese, an empty list), the app opens in the expected language in **10 of 10**, with no visible switch while loading.
- **SC-402**: On every screen and in every app language, **100%** of fixed texts are in that language. No text from another language appears outside customer data and record IDs.
- **SC-403**: On the English evaluation cases, the share of correct outcomes is within 5 points of the Spanish cases, and there are **0** unsafe outcomes, in rules mode and with the model.
- **SC-404**: For every evaluation case run in all three languages, the tools called, the transaction found, the decision, and the handoff are the same in **100%** of cases.
- **SC-405**: In every language-switch case, **100%** of earlier assistant messages are re-shown with identical facts and sources, and the conversation continues to the same outcome.
- **SC-406**: **0** cases where a safety check (secret request, other customer, injection, negation) fires in one language and not in another for the same meaning.
- **SC-407**: A language switch re-shows the conversation in under 2 seconds for a 20-message conversation.
- **SC-408**: The automated accessibility and phone-width checks from specs/003 pass in all three languages, in both themes: 0 contrast failures, 0 missing labels, 0 sideways scroll at 375 px.
- **SC-409**: A PDF downloaded in each language verifies as a match, and an edited one as altered. A PDF issued before this feature still verifies.

## Assumptions

- **Owner's architectural direction**: English is the base language. An interpreter turns any message into one common form with English names, and a translator takes the target language as a parameter, with English as the source wording. A new language later means adding its understanding and its wording, and nothing in the core. The plan decides whether they run as separate services or as separate parts of the current one, weighing the deadline, cost, and the single-container deployment. Either way, FR-411 holds: safety checks run on the original words, in code.
- **Constitution amendment**: the owner amends the Hackathon Constraints to add English (MINOR version bump) before implementation.
- **English texts**: written by the team, in the same register as the Spanish and Portuguese ones, and labelled team-generated. The country rights in English are desk-research translations, not legal advice, like the originals.
- **Customer translations use the model**: translating a customer's own words needs a model. In rules mode they are shown as written, with a note.
- **Where the record lives**: the original messages and the verified statements are the record. Every other language is a rendering of them.
- **Staff screens**: the specialist view follows the specialist's own app language, like every other screen.
- **The UI checks**: the existing checks run with an explicit browser language, and new checks cover English, the fallback, the switcher, and re-showing.
- **Timeline**: submissions close 2026-10-05, and the video is not recorded yet. The live demo must not be put at risk: the stories ship in priority order, each only if every gate passes, and redeploying needs the owner's approval.

## Out of Scope

- Languages other than English, Spanish, and Portuguese.
- Detecting the language from the visitor's location or IP address.
- Translating customer data: names, merchant names, cities, record IDs, and rule IDs stay as recorded.
- Changes to the data, the permissions, or what the assistant may say about a charge.
- Voice input or output.
