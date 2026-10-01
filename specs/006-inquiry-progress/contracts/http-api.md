# HTTP API changes: inquiry progress

Additive only. Every existing field keeps its meaning.

## `POST /api/chat` (stream): the `done` event

```json
{"type": "done", "stage": "confirm", "suggestions": ["Yes, it was me", "It wasn't me"], "lang": "en",
 "progress": {"path": "charge", "stage": 3, "total": 5, "done": false, "outcome": null, "case": null}}
```

- `progress` is null until an inquiry starts (data-model.md).
- **Error turns**: an expired session or the turn limit streams an `error` with no `done`. The browser keeps the last `progress`.
- **New step action**: `{"type": "step", "step": "decide", "action": "reask_pending", "question": "confirm" | "choose" | "contact_shared"}`. It's visible in the demo's technical trace, and evaluation can read it.

## `GET /api/session/conversation` and `POST /api/session/language`

The conversation view gains `progress`, with the same shape and the same value as the latest `done`:

```json
{"lang": "pt", "stage": "closed", "suggestions": null,
 "progress": {"path": "charge", "stage": 5, "total": 5, "done": true, "outcome": "specialist", "case": "CASO-EF06E0"},
 "turns": [...]}
```

Re-showed per-turn `done` markers keep `progress: null` (as with `stage` and `suggestions` today). The browser takes the view's top-level `progress`.

## Unchanged

- `/api/session` (sign-in)
- `/api/demo/customers`
- the handoff queue
- the transcript PDF and `/api/transcript/verify`
- the `message` event (its `statements` may now carry the new keys, which are stripped of key and params by `public_event` as today)
