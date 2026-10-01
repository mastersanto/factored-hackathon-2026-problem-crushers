# UI contract: suggestions in the current language

Extends `specs/004-browser-language/contracts/ui.md`.

## Example messages

- **What is shown**: `examples[appLanguage]` from the signed-in customer's demo item. Never examples from another language alongside them (FR-501).
- **When they change**: on any change of the app language (a clear message in another language, or the switcher), at once and with no request (FR-505).
- **Markup**: each example button has `lang` set to the app language (FR-507).

## Quick replies

- **What is shown**: the quick replies of the latest reply or re-show, in their language.
- **When they change**: when the switcher changes the language at a question, they are replaced by the re-show's `suggestions` (FR-504).
- **Markup**: each quick-reply button has `lang` set to the language it came with.

## Checks (`frontend/e2e/suggestions.spec.ts`)

| Check | What it asserts |
|---|---|
| Examples per language | In `en-US`, `es-MX`, and `pt-BR` browsers, every example chip has the browser's language in its `lang` and contains none of the other two languages' example texts |
| Examples follow the switcher | Before the first message, picking each language replaces every example at once |
| Tapping keeps the language | Tapping the charge example in English gets an English reply, with `<html lang="en">` |
| Quick replies follow the switcher | At "was it you?", switching ES → EN changes the quick replies to "Yes, it was me" / "It wasn't me" |
| Phone width | Chips keep their 44 px targets and there is no sideways scroll at 375 px in all three languages |
