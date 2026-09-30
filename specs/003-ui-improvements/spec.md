# Feature Specification: UI improvements (language, source labels, phone width, accessibility)

**Feature Branch**: `003-ui-improvements`

**Created**: 2026-09-30

**Status**: Implemented 2026-09-30 (open items in [pending.md](pending.md))

**Input**: User description: "mejoras del UI". Scope taken from the owner's plan for this feature: the chat's fixed texts follow the conversation's language, clearer *verificado* / *estimación* / *política* labels, a phone-width layout, and accessibility (contrast, keyboard use, screen-reader labels). The plan asks for a spec with no visuals; the look is settled afterwards in a design prototype that the owner approves.

## Context

What the chat does today (checked in the frontend on 2026-09-30):

- **Language**: only the PDF download texts switch to Portuguese (specs/002, FR-109). Every other fixed text in the chat stays in Spanish during a Portuguese conversation: the source labels, the verdicts ("Estafa: pidió un código", "Sin registro del banco", "Contacto real del banco"), "(pendiente)" on a charge, the handoff note ("Caso … enviado a un especialista"), the opening line, the input hint, and the send button. That falls short of spec 001, FR-015 and User Story 4 (the same service in Portuguese).
- **Source labels**: a small coloured tag with a record or rule ID. What each label means is not explained anywhere, and the source appears only as a hover tooltip, which touch screens and keyboards can't reach.
- **Phone width**: the side panel drops below the chat, but the chat keeps a fixed height tied to the window, and the header, session bar, and specialist cards were not designed for about 360-400 px.
- **Accessibility**: new assistant messages are not announced to screen readers, the text box has only a placeholder, not a label, message language is not marked, and colour contrast has not been checked in either theme.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The whole chat in my language (Priority: P1)

A customer writes in Portuguese. The replies already come back in Portuguese, and now everything around them does too: the source labels, the verdict on a suspicious call, the charge status, the note that a specialist received the case, the input hint, and the send button.

**Why this priority**: the organizers require both languages. A Portuguese conversation dotted with Spanish labels looks unfinished, and the source labels and verdicts are exactly the text the customer relies on.

**Independent Test**: run the same scenarios in Portuguese and in Spanish (explain a charge, check a call, file a claim) and list every fixed text on screen. In the Portuguese run, none is in Spanish.

**Acceptance Scenarios**:

1. **Given** a conversation whose latest assistant message is in Portuguese, **When** the customer looks at the chat, **Then** every fixed text in the chat (source labels, verdicts, charge status, handoff note, input hint, send button, download action) is in Portuguese.
2. **Given** a conversation that switches from Spanish to Portuguese, **When** the next assistant reply arrives, **Then** the chat's fixed texts switch with it. Messages already shown keep their original wording.
3. **Given** a new session with no reply yet, **Then** fixed texts are in Spanish, and the opening line invites the customer to write in Spanish or Portuguese in both languages.

---

### User Story 2 - I can tell what each source label means (Priority: P1)

Under each answer, the customer sees whether each statement is verified from a bank record, an estimate, or a bank or legal rule. The meaning of each label is available in the chat, and the record or rule reference can be read by tap, by click, or by keyboard, not only by hovering a mouse.

**Why this priority**: the source labels carry the product's main safety promise (Principle III), and they are shown on screen for judges and customers. They only help if people understand them.

**Independent Test**: show an answer with all three labels to someone who has not seen the product. Without help they can say which statement is a fact, which is an estimate, and which is a rule, and they can open each reference on a phone and with the keyboard alone.

**Acceptance Scenarios**:

1. **Given** an answer with verified, estimated, and rule statements, **When** the customer reads it, **Then** the three kinds can be told apart by text, not by colour alone.
2. **Given** a source label, **When** the customer taps it, clicks it, or reaches it by keyboard, **Then** its meaning and its reference (record ID or rule ID) are shown in the conversation's language.
3. **Given** a statement with no reference (an estimate), **Then** the label says it is an estimate and no empty reference is shown.

---

### User Story 3 - Use it on a phone (Priority: P2)

A customer opens the demo on a phone, about 360-400 px wide. They pick a test customer, chat, choose a charge from the list, file a claim, and download the PDF, without zooming or scrolling sideways. A specialist can open the Especialista tab on a phone and read a handoff.

**Why this priority**: customers disputing a charge are usually on their phones, and judges may open the link on one. The desktop experience already works.

**Independent Test**: at 375 px wide, complete the claim path and the call-check path end to end, and open the specialist queue. Nothing needs sideways scrolling, and every button can be tapped.

**Acceptance Scenarios**:

1. **Given** a 375 px wide screen, **When** the customer uses any part of the customer view, **Then** the page never scrolls sideways and no text is cut off.
2. **Given** a phone with the on-screen keyboard open, **When** the customer types, **Then** the text box and the latest message stay visible.
3. **Given** a phone, **Then** the "flow of the last turn" panel does not push the chat off screen: it stays reachable but out of the way.
4. **Given** a phone, **When** a specialist opens a handoff card, **Then** every field is readable without sideways scrolling, except that a wide facts table may scroll inside its own box.

---

### User Story 4 - Usable with a keyboard and a screen reader (Priority: P2)

A customer who uses only a keyboard, or a screen reader, can sign in as a test customer, send messages, pick suggested replies and charges, hear each new answer and verdict, read the source labels, download the PDF, and switch to the specialist view.

**Why this priority**: a bank's customer service must be usable by everyone. It also makes the demo sturdier.

**Independent Test**: complete the claim path with the keyboard alone, and again with a screen reader, in both themes. A contrast check of every text and label in light and dark themes finds no failures.

**Acceptance Scenarios**:

1. **Given** keyboard only, **When** the customer moves through the page, **Then** every action can be reached in a logical order, and the focused element is always clearly visible.
2. **Given** a screen reader, **When** an assistant reply, verdict, or handoff note arrives, **Then** it is announced once, without the customer moving focus.
3. **Given** a screen reader, **Then** the text box, the send button, the download action, the suggested replies, the charge options, and the tabs each have a spoken name in the conversation's language.
4. **Given** a Portuguese message on screen, **Then** it is marked as Portuguese, so a screen reader pronounces it correctly.
5. **Given** light or dark theme, **Then** all text and labels meet the WCAG 2.1 AA contrast minimums (4.5:1 for normal text, 3:1 for large text and interface parts).

---

### Edge Cases

- A reply arrives while the customer is scrolled up reading earlier messages: it is still announced to screen readers.
- A reply ends with an error or the session expires: the error text follows the conversation's language, and the download action says why it is unavailable.
- A long merchant name, amount, or record ID on a phone: it wraps and is never cut off.
- Many suggested replies on a phone: they wrap or scroll inside their own row, and never widen the page.
- The customer turns the phone to landscape with the keyboard open: the text box stays usable.
- The browser's text is enlarged to 200%: nothing overlaps, and nothing important is hidden.
- The customer prefers reduced motion: the scroll to the newest message happens without animation.

## Requirements *(mandatory)*

### Functional Requirements

**Language**

- **FR-201**: Every fixed text in the customer's chat MUST follow the language of the latest assistant message, Spanish or Portuguese, the same rule the PDF already uses (specs/002, FR-109). This covers source labels and their explanations, verdicts, charge status, the handoff note, the opening line, the input hint, the send button, the download action and its outcomes, the flow panel's headings, and spoken names for assistive technology.
- **FR-202**: Before the first assistant reply, fixed texts MUST be in Spanish. Messages already shown MUST never be re-translated.
- **FR-203**: The sign-in screen, the header, and the specialist view MAY stay in Spanish, since they are used before a conversation or by bank staff (see Assumptions).

**Source labels**

- **FR-204**: Each statement's source label MUST name its kind in words (verified / estimate / rule, in the conversation's language), so the kinds never differ by colour alone.
- **FR-205**: Each label's meaning and reference (record ID or rule ID) MUST be reachable by tap, click, and keyboard, and MUST be read out by screen readers. A hover-only tooltip is not enough.
- **FR-206**: The chat MUST explain what the three labels mean somewhere the customer can find without leaving the conversation.
- **FR-207**: The labels MUST show exactly the kind and reference that the answer came with. The interface MUST NOT add, remove, or reword statements, references, amounts, or dates.

**Phone width**

- **FR-208**: At widths from 360 px up, every screen (sign-in, chat, specialist view) MUST work without sideways page scrolling. Only a wide facts table may scroll within its own box.
- **FR-209**: At phone width, the text box MUST stay visible while typing, and the newest message MUST stay in view as replies arrive.
- **FR-210**: At phone width, the flow panel MUST NOT come between the customer and the chat. It stays available on request.
- **FR-211**: Buttons, suggested replies, charge options, and source labels MUST offer a tap target of at least 44 × 44 px at phone width.

**Accessibility**

- **FR-212**: Every action on every screen MUST be operable by keyboard alone, in a logical order, with a clearly visible focus indicator.
- **FR-213**: New assistant messages, verdicts, handoff notes, and download outcomes MUST be announced to screen readers when they arrive, once each.
- **FR-214**: Every control MUST have a spoken name. The text box MUST have a real label, not only a placeholder.
- **FR-215**: Each message MUST be marked with its language, and the page's language MUST follow the conversation.
- **FR-216**: All text and interface parts MUST meet WCAG 2.1 AA contrast in both the light and the dark theme.
- **FR-217**: Motion MUST respect the customer's reduced-motion setting.

**Guarantees that stay unchanged**

- **FR-218**: This feature MUST NOT change what the chat says, which data it shows, or when it offers the download. Every existing workflow, guard, and security test MUST keep passing unchanged.
- **FR-219**: The customer's view MUST keep showing only a case number for a handoff, never the handoff's internal content (priority, security flags, or assessments).

### Key Entities

- **Interface text set**: the chat's fixed texts, one set per language (Spanish, Portuguese). The latest assistant message's language picks which set is shown.
- **Source label**: the kind of a statement (verified, estimate, rule), its reference (record ID, rule ID, or none), and its explanation, in the conversation's language.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-201**: In a Portuguese run of the claim, call-check, and explain-a-charge paths, 0 fixed texts in the chat are in Spanish (counted from screenshots at each step).
- **SC-202**: 3 of 3 people who haven't seen the product correctly name the kind of each statement in a sample answer (fact, estimate, rule) without help.
- **SC-203**: At 375 px wide, the claim path and the call-check path are completed end to end with 0 sideways page scrolls and 0 cut-off texts, confirmed by screenshots at each step at desktop and phone width.
- **SC-204**: The claim path is completed with the keyboard alone, and again with a screen reader, in both themes, with no step that needs a mouse.
- **SC-205**: An automated accessibility check of the sign-in, chat, and specialist screens, in both themes, reports 0 contrast failures and 0 missing labels.
- **SC-206**: The existing test suite passes unchanged (46 of 46 at the time of writing), and the evaluation results in docs/evaluation.md do not change.

## Assumptions

- **Staff screens stay in Spanish**: the specialist view is used by the bank's staff, and the sign-in screen stands in for an identity service, so both stay in Spanish. The handoff card already shows the conversation's language.
- **Visual reference**: this spec says what must improve, not how it looks. The owner approved the design prototype "Bóveda" (Claude Design, exported to [design/](design/)). The plan uses it as the visual reference, and [research.md](research.md#r10-what-the-prototype-has-that-this-feature-doesnt-build) lists which of its elements are left out because they would need a workflow or API change.
- **Browsers**: current Chrome, Safari, Firefox, and Edge, on desktop and on phones (iOS Safari and Android Chrome). No support for old browsers.
- **Accessibility target**: WCAG 2.1 level AA, the usual standard for banking services.
- **Themes**: the existing light and dark themes, following the device setting. No theme switch is added.
- **Flow panel**: following the approved design, the "flow of the last turn" panel becomes five plain-language steps ("Cómo revisamos su caso"). The raw trace stays one tap away under "Detalle técnico" for judges. On phones it is a drawer, closed by default.
- **Where the texts come from**: the chat's replies, quick replies, and error texts already come in the conversation's language. This feature covers only the texts fixed in the interface.
- **Inputs**: no new data. The screens show synthetic organizer data and team-generated conversations, labelled as before.

## Out of Scope

- A new visual identity or branding, and a manual theme switch.
- Languages other than Spanish and Portuguese, or a manual language picker.
- Translating the specialist view.
- Changes to what the assistant says, to the workflow, or to the PDF (specs/002).
- A native mobile app.

## Results (2026-09-30, rules mode, `npm run check:ui`: 51 passed, 9 skipped by design across 4 projects)

The 9 skips are by design: the phone tests don't run in the 2 desktop projects, and the keyboard-only run happens in `desktop-light` only.

- **SC-201**: met. The Portuguese call check shows 0 Spanish-only fixed texts, in all four projects (`e2e/language.spec.ts`).
- **SC-202**: pending. It needs three outside people (quickstart §3.4, task T032).
- **SC-203**: met. At 375 px there is no sideways scroll on sign-in, the claim path through the case card, the call check, or the specialist view, and every control is at least 44 × 44 px (`e2e/phone.spec.ts`). Screenshots are in `frontend/e2e/screenshots/`, which is git-ignored.
- **SC-204**: automated part met. The claim path completes with the keyboard alone (`e2e/a11y.spec.ts`). The screen-reader run is pending (T032).
- **SC-205**: met. axe (WCAG 2.1 A and AA) reports 0 violations on sign-in, chat (explained charge, case card, scam verdict), and the specialist view, in light and dark.
- **SC-206**: met. `make test` gives 46 passed, and no backend file or `docs/evaluation.md` changed.

