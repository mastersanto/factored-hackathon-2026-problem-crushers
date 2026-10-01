# UI contract: three languages

This extends `specs/003-ui-improvements/contracts/ui.md`. Where the two differ, this file wins on language.

## App language

- **Decided before the first render.** The first text on screen is in the final language, and `<html lang>` matches it (FR-404, FR-409).
- **One language for every fixed text on every screen**: header, sign-in (heading, lead, notice, scenario labels, loading, errors including the 429 message), chat (all of specs/003's `TextSet`), specialist view (titles, field names, priorities, case types, the PDF check, empty and error states).

## Switcher

- **Placement**: in the header, on every screen, at desktop and phone width.
- **Options**: "EN", "ES", "PT", shown as a group.
  - Each option's spoken name is in its own language: "English", "Español", "Português".
  - The current option is marked with `aria-pressed` or the equivalent, and is announced.
- **Size**: each option meets the 44 × 44 px tap target at phone width (specs/003, FR-211), and the header keeps 0 sideways scroll at 360 and 375 px.
- **Picking an option**:
  - switches every fixed text at once, with no reload;
  - stores the choice on the device;
  - during a conversation, re-shows the conversation in the new language (below).
  - The composer keeps its unsent text, and focus stays on the switcher.

## Re-showing the conversation

- **Triggers**: the switcher, or a reply whose `done.lang` differs from the screen's language.
- **The browser** replaces the shown turns with the server's re-rendered ones in one update. The log does not jump, and the newest message stays in view.
- **A translated customer message**:
  - shows the translation with a "Translated" / "Traducido" / "Traduzido" mark;
  - has a control that shows the original, reachable by keyboard, with a spoken name;
  - the original is marked with its own `lang`.
- **A missing translation** shows the original, with a short note in the app language.
- **Each message** keeps its `lang` attribute for the language it is shown in.
- **Screen readers**: a re-show is announced once ("Conversation shown in Portuguese" in the new language), not message by message.

## Specialist view

- **Field names, priorities, and case types** follow the app language.
- **The customer's words** are shown as written, with a marked translation beneath them when the case's language differs.
- **Verified facts and IDs** are not translated.

## Checks

The existing four projects (`desktop-light`, `desktop-dark`, `phone-light`, `phone-dark`) run with `locale: 'es-MX'`. The new specs cover:

| Spec | What it checks |
|---|---|
| `e2e/detect.spec.ts` | `en-US`, `es-MX`, `pt-BR`, `fr-FR` → EN, ES, PT, EN; `fr-FR,es` → ES; a stored choice wins over the browser |
| `e2e/switcher.spec.ts` | switching on each screen; persistence across reload; spoken names; tap targets; no sideways scroll |
| `e2e/reshow.spec.ts` | Spanish claim path, then a switch to PT and to EN: same case number, same sources, a translation mark on customer messages, the original reachable; then a switch back shows the originals |
| `e2e/language.spec.ts` (extended) | an English conversation shows 0 Spanish or Portuguese fixed texts |
| `e2e/a11y.spec.ts` (extended) | axe on sign-in, chat, and specialist view in English, both themes |
