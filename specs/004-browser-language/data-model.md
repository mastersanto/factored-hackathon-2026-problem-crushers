# Data model: The whole app in English, Spanish, or Portuguese

Everything here lives in memory for the session, like today, except the stored language choice (on the visitor's device) and the PDF's embedded JSON. No new data file, and no conversation text written to disk.

## Lang

`"en" | "es" | "pt"`. English is the base language: the source wording and the fallback.

## App language (browser)

| Field | Type | Rule |
|---|---|---|
| `lang` | Lang | `pickLanguage(navigator.languages, stored)`: the stored choice, else the first preference whose primary subtag is en, es, or pt, else `en` (FR-402, FR-403) |
| stored choice | Lang or absent | `localStorage["app-language"]`, written only by the switcher. Reading or writing it never throws (FR-406) |

**Transitions**:
- on load: from the stored choice or the browser;
- switcher: set and store;
- a reply whose `done.lang` differs: set, but don't store (the customer's writing is a signal for this conversation, not a saved preference).

## Session (server, extended)

| Field | Change | Rule |
|---|---|---|
| `lang` | `es \| pt` → `en \| es \| pt` | Starts from the app language sent at sign-in. A clear message language overwrites it at any stage (FR-407). `POST /api/session/language` overwrites it |
| `translations` | new: `dict[(entry_index, Lang), str \| None]` | Cache of customer-message translations. `None` records "no usable translation", so it is not retried (R7) |

## Understanding (the common form, extended)

| Field | Change |
|---|---|
| `language` | `es \| pt` → `en \| es \| pt \| None`. `None` = unclear (R4) |
| everything else | unchanged: intent, amount, merchant, date, channel, `asked_for_secret`, `shared_secret`, option, `other_customer_reference`, `injection_suspected`, source |

**Validation**: `other_customer_reference`, `injection_suspected`, and `asked_for_secret` from the rules are OR-ed into any model result. A rules negation at the confirm step always gives `file_claim` (unchanged).

## Statement (extended)

| Field | Type | Sent to the browser |
|---|---|---|
| `text` | str, in the language it was produced in | yes |
| `basis` | `known \| guessed \| rule` | yes |
| `source` | str or None | yes |
| `key` | str: a template key, or `rule:<rule id>` | **no** |
| `params` | dict of raw verified values (numbers, ISO dates, codes, names, case number) | **no** |

**Validation**: `translator.render([st], lang)` must give back exactly `st.text` when `lang` is the language `st` was produced in, for every template statement. This is tested for every key in all three languages.

## Transcript entry (server recorder, extended; specs/002)

| Kind | Fields kept (new in **bold**) |
|---|---|
| `customer` | `ts`, `text` (masked original), **`lang`** (the message's detected language, or the session's when unclear) |
| `message` | `ts`, `text` (as shown), `statements` (with **`key`**, **`params`**), **`lang`**, **`phrased_by`** (`template \| llm`) |
| `candidates` | `ts`, `items` (as shown) plus **raw values per item** (amount, currency, ISO date, merchant or type code, status) |
| `verdict` | `ts`, `verdict`, `channel` (codes: language-neutral already) |
| `handoff` | `ts`, `case_id` |
| `notice` | `ts`, `code`, `text`, **`lang`** |

**Re-rendering an entry in language L**:
- `message`: if `L == lang`, the stored text; else `render(statements, L)`.
- `candidates`: rebuilt from raw values in L.
- `notice`: rebuilt from its code in L.
- `customer`: if `L == lang`, the original; else the cached or new translation, marked; or the original with `translation_missing`.

## Conversation view (API response)

The whole conversation in one language, in the same event shapes the chat already streams. Defined in [contracts/http-api.md](contracts/http-api.md).

## Transcript snapshot, schema 2 (PDF; specs/002, extended)

| Field | Change |
|---|---|
| `schema` | `2` |
| `renderer` | `fpdf2-2.8.9/r2` |
| `lang` | `en \| es \| pt`: the session's language at download |
| `entries[].kind = customer` | `original`, `original_lang`, and when `original_lang != lang`: `translation` or `translation_missing: true` |
| `entries[].kind = message` | `text` and `statements` in `lang` (re-rendered when needed). No `key` or `params` |
| all other fields | unchanged |

**Verification**: schema 1 with renderer r1 → `render_v1`. Schema 2 with r2 → `render`. Anything else → `unknown_version`. The check code covers the whole JSON, `lang` and translations included.

## Handoff (extended)

| Field | Change |
|---|---|
| `language` | can be `en` |
| `request`, `customer_statement` | unchanged: the customer's words as written (masked by the same rules as the transcript) |
| view only: `translations` | added by `GET /api/handoffs?lang=L` for cases whose language differs from L: `{request?, customer_statement?}`, each a marked translation or absent. Never stored in the queue file |

## Demo customer (API, extended)

| Field | Change |
|---|---|
| `scenario` | new, stable id: `fraud_flagged`, `pending`, `mx_debit_48h`, `co_purchase`, `ar_purchase`, `compliance`, `bank_message` |
| `label` | unchanged (English), used by the UI checks |
