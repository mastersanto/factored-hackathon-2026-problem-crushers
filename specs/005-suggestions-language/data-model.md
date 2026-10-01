# Data model: Suggestions in the language I'm writing in

No stored data changes. Everything here is built per request from the demo data the API already reads.

## Demo customer (API, extended)

| Field | Change | Rule |
|---|---|---|
| `examples` | new: `{en: string[], es: string[], pt: string[]}` | The same situations in the same order in every language (research R2). Built from `hint`. Amounts in each language's format; contact dates day first in es/pt and with the month name in en (R3) |
| `label`, `scenario`, `hint`, … | unchanged | |

**Validation**:
- the three lists have the same length;
- each list contains only the situations its hint supports (a charge example only with an amount; a contact example only with a channel and date);
- the scam and other-customer examples are always present.

## Example message (browser)

The visible list is `examples[appLanguage]`. It changes whenever the app language changes (FR-505), with no request.

## Quick reply (unchanged)

One set per stage and language (`messages.QUICK_REPLIES`), sent with each reply (`done.suggestions`) and with each re-show (`suggestions`).
