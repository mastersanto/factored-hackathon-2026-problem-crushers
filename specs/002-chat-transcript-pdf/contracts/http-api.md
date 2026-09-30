# HTTP API additions: transcript download and verification

These extend `specs/001-dispute-intake-assistant/contracts/http-api.md`. All other endpoints are unchanged, except the `done` event, which gains one field.

## Changed: `done` event on `POST /api/chat`

```json
{"type": "done", "stage": "statement", "suggestions": ["…"], "lang": "es"}
```

- `lang` (`es` | `pt`) is the language of this turn's reply. The frontend uses it to label the download button.

## New: `POST /api/transcript`

Downloads the current conversation as a PDF.

**Request** (JSON):

```json
{"session_id": "<session token>", "conversation_ref": "CONV-AB12CD34"}
```

- `session_id` (required) identifies the customer, as for `/api/chat`.
- `conversation_ref` (optional) is sent by the UI for consistency. If it is present and differs from the session's, the request is refused.

**Responses**:

| Status | When | Body |
|---|---|---|
| 200 | The session is valid and has at least one committed turn | `application/pdf`, with `Content-Disposition: attachment; filename="conversacion-CONV-AB12CD34-20260930-1415.pdf"` and `X-Check-Code: XXXX-XXXX-XXXX-XXXX` |
| 401 | Unknown or expired session | `{"detail": "invalid session"}` |
| 403 | `conversation_ref` is not the session's. A security flag `transcript_other_conversation` is recorded on the session. | `{"detail": "not your conversation"}` |
| 409 | No committed turn yet | `{"detail": "nothing to export yet"}` |
| 429 | The per-IP limit was exceeded | `{"detail": "too many requests; try again later"}` |

**Guarantees**:

- The PDF contains only the entries recorded from customer-visible events (data-model: Entry).
- No model is called.
- A fingerprint record is appended to the register, unless the same fingerprint is already present.

## New: `POST /api/transcripts/verify`

Checks whether an uploaded PDF is an unaltered transcript issued by this service.

**Request**: `multipart/form-data` with one field, `file` (a PDF of at most 2 MB).

**Response** (200 in every case where the upload was received):

```json
{"result": "match", "check_code": "7K3M-Q9ZX-2RTA-VB41", "registered": true,
 "generated_at": "2026-09-30T14:15:02-05:00", "case_ids": ["CASE-000123"]}
```

| `result` | Meaning |
|---|---|
| `match` | The embedded transcript's HMAC matches its code, and the file is byte-identical to a fresh render of it. |
| `altered` | The HMAC doesn't match, or the file differs from the render. This includes a copy re-saved by another tool: only the original download verifies. |
| `unknown_version` | It was issued by a different renderer version, so the file cannot be re-rendered for comparison. The HMAC result is not reported. |
| `unreadable` | It is not a PDF, is encrypted, or has no embedded transcript. |

**Other statuses**:

- 413: the file is over 2 MB.
- 429: the per-IP limit was exceeded.

**Guarantees**:

- The response never contains message text, customer names, or amounts.
- The uploaded file is not stored.
