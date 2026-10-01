# HTTP API changes: three languages

These extend `specs/001-dispute-intake-assistant/contracts/http-api.md` and `specs/002-chat-transcript-pdf/contracts/http-api.md`. Every endpoint not listed here is unchanged.

## Changed: `POST /api/session`

**Request**:

```json
{"customer_id": "CLI-XXXXXX", "lang": "en"}
```

- `lang` (optional, `en | es | pt`, default `es` for compatibility): the app language at sign-in. It sets the session's starting language.

**Response**: unchanged, plus `"lang"` echoing the session's language.

## Changed: `POST /api/chat` events

- **`done`**: `lang` can be `en`. It is the session's language after this turn: the language of a clear message, or the previous one.
- **`message`**: unchanged shape. `statements[]` never carries `key` or `params`.
- **All events**: the text is in `done.lang`.

## New: `POST /api/session/language`

Sets the session's language (the switcher) and returns the whole conversation in it.

**Request**:

```json
{"session_id": "<session token>", "lang": "pt"}
```

**Response 200**:

```json
{
  "lang": "pt",
  "stage": "confirm",
  "suggestions": ["Sim, fui eu", "Não fui eu"],
  "turns": [
    {"role": "customer", "text": "Não reconheço…", "lang": "pt", "at": 1759259111000,
     "original": {"text": "No reconozco un cargo de 181,46 en Óptica…", "lang": "es"}, "translated": true},
    {"role": "assistant", "lang": "pt", "at": 1759259113000,
     "events": [{"type": "message", "text": "A cobrança é de 181,46 USD…", "statements": [{"text": "…", "basis": "known", "source": "transaction:TX-…"}]}]}
  ]
}
```

- **`turns`**: in order, one per customer message and one per assistant reply, in the shapes the chat already uses.
- **Customer turns**:
  - `translated: true` with `original` when a translation is shown;
  - `translation_missing: true` with the original text when none is available;
  - neither when the message was written in `lang`.
- **Assistant turns**:
  - `events` contains only `message`, `candidates`, `verdict`, `handoff`, customer-visible `error` events, and a closing `done` marker (as when the reply was streamed). Never `step` events, `key`, `params`, or `raw`.
  - Each statement's `basis` and `source` are identical to what was first sent (FR-420).
- **`at`**: milliseconds since the epoch, as the chat already uses (as built, T036).

| Status | When |
|---|---|
| 200 | valid session |
| 401 | unknown or expired session |
| 422 | `lang` not one of `en`, `es`, `pt` |

**Guarantees**:
- No tool is called and no record is read. Only stored entries are re-rendered.
- The model is called only to translate customer messages not yet cached, within the spend cap.
- The response is the same for the same session, language, and cache state.

## New: `GET /api/session/conversation?session_id=…`

The same response as above, in the session's current language, without changing it. The browser calls it when a reply's `done.lang` differs from the screen's language.

## Changed: `POST /api/transcript`

- The PDF is produced in the session's language at download (`en`, `es`, or `pt`), with schema 2 and renderer r2 (data-model: Transcript snapshot).
- The English file name is `conversation-CONV-…-YYYYMMDD-HHMM.pdf`.

## Changed: `POST /api/transcripts/verify`

- Verifies schema 1 / r1 (issued before this feature) and schema 2 / r2.
- Results and their meaning are unchanged.

## Changed: `GET /api/handoffs`

- **New optional query parameter**: `lang` (`en | es | pt`).
- When `lang` is given, each case whose `language` differs gains `translations: {request?, customer_statement?}`: marked model translations, cached per case and field.
- The original fields are unchanged.

## Changed: `GET /api/demo/customers`

- Each item gains `scenario` (a stable id; data-model: Demo customer).
- `label` is unchanged.
