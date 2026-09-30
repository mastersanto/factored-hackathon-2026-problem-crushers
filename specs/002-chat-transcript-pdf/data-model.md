# Data model: Chat transcript as a PDF

The entities this feature adds. **Session** and **Handoff** are those of feature 001 (`specs/001-dispute-intake-assistant/data-model.md`); two fields are added to Session.

## Session (extended)

| Field | Type | Rule |
|---|---|---|
| `conversation_ref` | string `CONV-` + 8 characters `[A-Z0-9]` | Random, set at session creation. Printed on the PDF. It is **not** a credential and never equals or derives from the session token. |
| `transcript` | Transcript | In memory only. It expires with the session (TTL 30 min) and is never written to disk. |

## Transcript

The canonical record of what the customer was shown. It is fingerprinted and embedded in the PDF.

| Field | Type | Rule |
|---|---|---|
| `schema` | int | `1`. Bumped on any change to this structure. |
| `renderer` | string | The pinned renderer identity, e.g. `fpdf2-2.8.9/r1`. Verification re-renders byte for byte only with the same identity (research §5). |
| `conversation_ref` | string | From the session. |
| `customer` | `{first_name, country}` | Only these two fields: no ID, document, or contact details. |
| `time_zone` | IANA string | Derived from the country (research §6). |
| `lang` | `es` \| `pt` | The language of the latest assistant turn (FR-109). |
| `case_ids` | list of strings | Every handoff case number shown in the conversation, in order. It may be empty. |
| `masked` | bool | True if any entry was masked (FR-107). |
| `entries` | list of Entry | In the order shown. Only committed (complete) turns. |
| `generated_at` | ISO 8601 with offset | Set when the PDF is produced. It is part of the fingerprinted content. |

## Entry

One item as the customer saw it. The kinds mirror the customer-visible stream events of feature 001.

| `kind` | Fields | Source |
|---|---|---|
| `customer` | `at`, `text` (masked) | the customer's message |
| `message` | `at`, `text`, `statements[]` (`text`, `basis` ∈ {known, guessed, rule}, `source`) | a `message` event |
| `candidates` | `at`, `items[]` (`option`, `amount`, `merchant`, `when`, `status`) | a `candidates` event |
| `verdict` | `at`, `verdict` ∈ {bank_contact, no_record, scam_asks_secret}, `channel` | a `verdict` event |
| `handoff` | `at`, `case_id` | a `handoff` event (case number only) |
| `notice` | `at`, `code`, `text` | an `error` event shown to the customer (turn limit, data service unavailable) |

**Validation rules**:

- **Only customer-visible events.** `step` events are never recorded, internal or not. The chat shows the trace panel, but the PDF is the conversation, not the trace, and `step` details may name internal steps.
- **An entry's text is stored exactly as streamed.** The only exception is masking of `customer` text.
- **A turn's entries are appended when the turn's stream ends.** A partial turn is kept if the client disconnected after receiving it. A turn that is still streaming is not visible to a PDF request.

## Fingerprint record

This is the only thing persisted, as one JSON line in `TRANSCRIPTS_PATH` (research §4).

| Field | Type | Rule |
|---|---|---|
| `fingerprint` | hex string (64) | `HMAC-SHA256(key, canonical transcript)` |
| `check_code` | `XXXX-XXXX-XXXX-XXXX` | Crockford base32 of the first 80 bits |
| `conversation_ref` | string | |
| `case_ids` | list of strings | |
| `generated_at` | ISO 8601 | |
| `schema`, `renderer` | as in Transcript | |

**Rule**: it holds no message text, name, or amount. Records are append-only, and a fingerprint already present is not appended again.

## Transcript document (PDF)

- **Pages**: A4.
- **Header on every page**:
  - the service name, *Explica este cargo · LATAM Bank*;
  - the customer's first name and country;
  - the conversation reference;
  - the case numbers;
  - the generation date and time with the zone.
- **First page**: the fixed notice (FR-105), a line saying to keep the original file because only it can be verified, and, if `masked`, the masking note.
- **Body**: the entries, each with its author label (*Usted* / *Você*, *Asistente* / *Assistente*) and local time. Statements show their basis label (*verificado · estimación · política* / *verificado · estimativa · política*) and source.
- **Footer on every page**: "página X de Y" / "página X de Y" and the check code.
- **Attachment**: `transcript.json`, the canonical transcript plus `check_code`.
- **Metadata**: the creation date equals `generated_at`, and the producer string is fixed.
- **File name**: `conversacion-<conversation_ref>-<YYYYMMDD-HHMM>.pdf`, or `conversa-…` in Portuguese.

## Verification result

| Field | Values |
|---|---|
| `result` | `match` \| `altered` \| `unknown_version` \| `unreadable` |
| `check_code` | as printed, when readable |
| `registered` | bool: whether the register still holds the fingerprint (`match` only) |
| `generated_at`, `case_ids` | from the embedded transcript (`match` only) |

It never includes message text.
