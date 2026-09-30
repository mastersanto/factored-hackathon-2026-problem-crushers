# Contract: HTTP API and server-sent event protocol

Implemented in `backend/app/api/main.py`. All paths are under `/api`. In development the frontend reaches them through the Vite proxy.

## Endpoints

| Method and path | Request | Response | Notes |
|---|---|---|---|
| `GET /api/health` | none | `{status, as_of, llm_enabled, models: {understand, phrase} \| null}` | `as_of` is the dataset's "today" |
| `GET /api/demo/customers` | none | `[{label, customer_id, first_name, country, hint}]` | Development and demo only. It stands in for an identity service and offers one customer per workflow path. |
| `POST /api/session` | `{customer_id}` (must match `^CLI-[A-Z0-9]{6,}$`) | `{session_id, customer: {first_name, country}, expires_in_seconds}` | 404 for an unknown customer. The session id is the only credential used by `/api/chat`. |
| `POST /api/chat` | `{session_id, text}` (text of 1-2000 characters) | `text/event-stream` (see below) | 401 for an invalid session. An expired session streams an `error` event. |
| `GET /api/handoffs` | none | `[Handoff]`, newest first | The specialist view (data-model.md, Handoff) |
| `GET /api/metrics` | none | `{llm_calls, usd, by_model}` | Model usage since the process started |

## Chat stream

Each turn streams one event per server-sent event frame:

```text
event: <type>
data: <json>

```

The `data` JSON always has a `type` field equal to the event name. Events arrive in workflow order. The last one is always `done`.

| `type` | Fields | Meaning |
|---|---|---|
| `step` | `step` (understand, decide, act, verify, or escalate), plus step-specific detail such as `intent`, `source`, `slots`, `action`, `tool`, `results`, `verdict`, `case_id`, `priority`, `unsupported_removed`, `phrased_by` | The workflow trace, shown in the UI's side panel |
| `message` | `text`; `statements: [{text, basis, source}]` | What the customer reads, with the basis and source of every statement |
| `candidates` | `items: [{option, transaction_id, when, amount, merchant, status}]` | Several charges match; the customer picks one by number |
| `verdict` | `verdict` (`scam_asks_secret`, `bank_contact`, or `no_record`); `channel` | Result of the "is this really my bank?" check |
| `handoff` | `handoff` (a full Handoff object) | A case was sent to a person |
| `error` | `code` (for example `session_expired`); `text` | The turn could not proceed. No data is returned. |
| `done` | `stage`; `suggestions: string[] \| null` | End of turn. The quick replies for the assistant's question are in the customer's language; `null` means none. |

## Guarantees the contract makes

- **No other customer's data.** No event carries data belonging to anyone but the session's customer (constitution II).
- **No unsourced facts.** Every `message.statements[*]` with basis `known` or `rule` has a non-empty `source`, and `message.text` contains no number absent from its statements (constitution III).
- **Exactly one handoff per escalation.** A `handoff` event is emitted whenever a handoff is created, including the technical fallback.
