# Implementation Plan: Chat transcript as a PDF, with a check code

**Branch**: `main` (single-builder repository; the setup script reports `002-chat-transcript-pdf`, which is the feature folder, not a git branch) | **Date**: 2026-09-30 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-chat-transcript-pdf/spec.md`

## Summary

A signed-in customer downloads the current conversation as a PDF, for their records. The PDF shows what the chat showed, and nothing more:

- the messages;
- statements with their *verificado* / *estimación* / *política* labels and sources;
- candidate lists, contact verdicts, and case numbers.

It also carries a header, a fixed notice (no promise, not a claim decision), and a **check code**.

**Technical approach**:

- **The server records the transcript.** A recorder sits in the API stream, after the filter that drops internal events. It keeps each session's transcript in memory, so it can hold only what the customer was sent. Card numbers and codes are masked when recorded.
- **The PDF is rendered deterministically**, with fpdf2 and a bundled Unicode font. It embeds the canonical transcript (JSON) as an attachment.
- **The check code** is an HMAC-SHA256 of the canonical transcript, keyed by a server secret. The bank stores only the fingerprint record: HMAC, code, case numbers, conversation reference, and time. It never stores the text (spec FR-111, option B).
- **Verification**: a PDF is uploaded to a verify endpoint, which:
  1. extracts the embedded transcript;
  2. recomputes the HMAC and compares it with the printed code;
  3. re-renders the file and compares it byte for byte with the upload. A probe showed that comparing page content streams misses edits (research §5).

  It answers only match, altered, or unknown, and the specialist view gets an upload box for it.
- **No model is called**, so the feature adds no cost and cannot alter what was said.

## Technical Context

**Language/Version**: Python 3.10 (backend), TypeScript 5 with React 19 (frontend). Both are unchanged from feature 001.

**Primary Dependencies** (new ones pinned exactly, for deterministic rendering):

- `fpdf2==2.8.9`: renders PDFs and embeds files;
- `pypdf==6.19.0`: reads uploaded PDFs, their attachments, and their page content;
- `tzdata`: time zones inside the slim container;
- `python-multipart`: FastAPI's form parser for the verification upload (added during implementation).

Everything else is unchanged: FastAPI, DuckDB, the Anthropic SDK (not used by this feature), and Vite with TanStack Query.

**Storage**:

- **Transcripts**: in the session's memory, which already expires after 30 minutes.
- **Fingerprint register**: append-only JSON lines at `TRANSCRIPTS_PATH` (default `backend/data/transcripts.jsonl`, which is git-ignored), next to the handoffs.
- No conversation text is persisted.

**Testing**: pytest (new `backend/tests/test_transcript.py`), plus a transcript check over the evaluation sets in rules mode (free).

**Target Platform**: the existing single container on Azure Container Apps, and local development.

**Project Type**: web application (the existing `backend/` and `frontend/`).

**Performance Goals**: a PDF in under 5 s for a conversation at the 40-turn limit (SC-101). The expected time is under 1 s, since no model or data query is involved.

**Constraints**:

- The PDF contains only what was streamed to the customer (FR-106).
- No model calls (FR-112).
- The HMAC key comes only from the environment or the host's secret store (Principle IV).
- PDFs are never committed, since they hold synthetic customer rows.

**Scale/Scope**: one PDF per request; up to 40 turns; demo traffic, with the same per-IP guard as sessions.

## Constitution Check

*GATE: must pass before Phase 0 research, and is re-checked after Phase 1 design.*

| Principle | How this feature complies | Status |
|---|---|---|
| **I. Deterministic core, AI at the edges** | Recording, masking, rendering, fingerprinting, and verification are plain code. No model is called (FR-112), and the feature works the same in rules mode. | Pass |
| **II. Permissions in the tool layer** | The PDF comes from the **session's** transcript only. Identity is the session token, never a value in the request. An optional `conversation_ref` that doesn't match the session's is refused (403) and recorded as a security flag. An expired session gets 401. The conversation reference is random and is not a credential; the session token never appears in the PDF. | Pass |
| **III. Verified facts only** | The recorder sits **after** the API's internal-event filter, so internal events can't reach the PDF by construction (FR-106). Statements keep their basis and source (FR-103). The fixed notice is a customer-facing text, so a test runs it through the existing no-promise check (FR-105). The compliance-review case prints only the neutral message and case number. | Pass |
| **IV. No data or secrets in the repository** | `TRANSCRIPT_HMAC_KEY` lives in `.env.local` and is a Container Apps secret. `.env.example` holds an empty entry. The register is in the git-ignored `backend/data/`. Generated PDFs are ignored by pattern, and tests write to a temporary folder. The bundled font ships with its license. The secret scan runs on every commit. | Pass |
| **V. Evaluate before claiming** | SC-102 to SC-104 and SC-107 are measured on the held-out evaluation sets, with counts, and reported in `docs/evaluation.md`. The tamper checks mutate real PDFs. Masking is tested on seeded cases. | Pass |

No violations. Complexity tracking is not needed.

**Post-design re-check** (after Phase 1): still passes.

- The verify endpoint returns only a result, the issue time, and the case numbers, all already printed on the PDF its caller holds. It is rate-limited per IP.
- The endpoint and the specialist queue are unauthenticated in the demo. This limit is already documented, and production would put both behind staff authentication (added to `docs/limitations.md`).

## Project Structure

### Documentation (this feature)

```text
specs/002-chat-transcript-pdf/
├── spec.md
├── plan.md              # this file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   └── http-api.md      # Phase 1: download and verify endpoints
├── checklists/requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks; not created here)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── transcript/                 # new package
│   │   ├── __init__.py
│   │   ├── record.py               # TranscriptRecorder: builds entries from streamed events; masking
│   │   ├── mask.py                 # card-number and code/PIN masking (ES/PT keywords)
│   │   ├── fingerprint.py          # canonical JSON, HMAC, check code, FingerprintRegister (JSONL)
│   │   ├── render.py               # deterministic PDF: header, notice, entries, footer, embedded JSON
│   │   ├── verify.py               # extract, recompute, re-render, compare
│   │   ├── labels.py               # ES/PT fixed texts: headings, basis labels, notice, masking note
│   │   └── fonts/                  # DejaVuSans.ttf, DejaVuSans-Bold.ttf, LICENSE
│   ├── api/main.py                 # + recorder hook in the chat stream; POST /api/transcript; POST /api/transcripts/verify
│   ├── workflow/engine.py          # + Session.conversation_ref, Session.transcript; `lang` on the done event
│   ├── config.py                   # + transcript_hmac_key, transcripts_path
│   └── eval/transcript_check.py    # SC-102..104, SC-107 over the case sets
└── tests/test_transcript.py

frontend/src/
├── api.ts                          # + downloadTranscript(), verifyTranscript()
├── Chat.tsx                        # + "Descargar conversación (PDF)" / "Baixar conversa (PDF)" button; reminder after a handoff
└── AgentQueue.tsx                  # + "Verificar PDF" upload with the result

scripts/deploy-azure.sh             # + create the `transcript-key` secret once if missing (random, never printed)
.env.example                        # + TRANSCRIPT_HMAC_KEY= (empty)
.gitignore                          # + conversacion-*.pdf, conversa-*.pdf
docs/limitations.md, docs/evaluation.md, README.md   # the feature, its checks, and its limits
```

**Structure Decision**: this extends the existing web application, adding one backend package (`app/transcript/`) and small changes to the API, engine, frontend, and deploy script. It adds no new service or process.

## Complexity Tracking

None. There are no constitution violations to justify.
