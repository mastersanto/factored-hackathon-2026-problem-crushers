# Tasks: Chat transcript as a PDF, with a check code

**Input**: design documents in `specs/002-chat-transcript-pdf/`: spec.md, plan.md, research.md, data-model.md, contracts/http-api.md, quickstart.md

**Tests**: included. The constitution's quality gates require a safety behaviour to add a test that fails without it (FR-106, FR-107, FR-108, FR-111), and Principle V requires measured success criteria (SC-101 to SC-107).

**Deadline context**: submissions close 2026-10-05 at midnight, Colombia time. The owner-only tasks T042 (video) and T044 (submission email) in feature 001 come first. The MVP of this feature is User Story 1.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task).
- **[Story]**: US1, US2, or US3, from spec.md.
- Paths are relative to the repository root.

## Quality gates (after every task that changes code)

- `make test`;
- `cd frontend && npm run build` (type-check and build);
- the secret scan on the staged diff (zero matches);
- `make eval` when the chat stream or engine changes.

A task is checked off only when its gates pass.

---

## Phase 1: Setup

**Purpose**: dependencies, font, configuration, and ignore rules.

- [X] T001 Add `fpdf2==2.8.9`, `pypdf==6.19.0` (both pinned exactly, for byte-identical rendering, research §3 and §5) and `tzdata` to `dependencies` in `backend/pyproject.toml`, then reinstall with `backend/.venv/bin/python -m pip install -e 'backend[dev]'`
- [X] T002 [P] Copy `DejaVuSans.ttf` and `DejaVuSans-Bold.ttf` from `/usr/share/fonts/truetype/dejavu/` into `backend/app/transcript/fonts/`, with the DejaVu font license as `backend/app/transcript/fonts/LICENSE`, and create an empty `backend/app/transcript/__init__.py`. Make sure the font files are included in the Docker image: `Dockerfile` copies `backend/app`, so check the build context's `.dockerignore`.
- [X] T003 [P] Add `transcript_hmac_key: str` (from `TRANSCRIPT_HMAC_KEY`, default empty) and `transcripts_path: Path` (from `TRANSCRIPTS_PATH`, default `BACKEND_DIR / "data" / "transcripts.jsonl"`) to `Settings` in `backend/app/config.py`, and include the key in `normalize_credentials()` (strip quotes and whitespace)
- [X] T004 [P] Add an empty `TRANSCRIPT_HMAC_KEY=` line with a one-line comment to `.env.example`, and add the patterns `conversacion-*.pdf`, `conversa-*.pdf`, and `/backend/data/transcripts.jsonl` to `.gitignore`. The local pre-commit hook already rejects values in `.env.example`.

---

## Phase 2: Foundational (blocks all stories)

**Purpose**: the recorded transcript and masking, which every story reads.

**⚠️ No story work starts until this phase is complete.**

- [X] T005 [P] Write failing tests for masking in `backend/tests/test_transcript.py`:
  - **Card numbers**: 13–19 digits, with optional spaces or dashes, become `•••• 1234`.
  - **Codes**: a run of 4–8 digits within 4 words of *código, clave, contraseña, PIN, NIP, OTP, token, senha, código de verificação* becomes `••••`.
  - **Left alone**: amounts ("1.250", "$ 1,250.00") and dates are not masked.
  - **Flag**: `masked=True` is reported.
- [X] T006 Implement `mask(text) -> tuple[str, bool]` in `backend/app/transcript/mask.py` to pass T005
- [X] T007 [P] Write failing tests for the recorder in `backend/tests/test_transcript.py`:
  - **Kinds**: only the entry kinds `customer`, `message`, `candidates`, `verdict`, `handoff`, and `notice` (from `error` events) are recorded.
  - **Excluded**: `step` events are never recorded, whether internal or not. A `handoff` entry holds `case_id` only.
  - **Timing**: a turn is committed only when its stream ends (or closes early). A turn still streaming is not visible.
  - **Language**: `lang` comes from the `done` event.
  - **Masking**: customer text is masked at record time.
- [X] T008 Add `conversation_ref` (`CONV-` + 8 characters from `[A-Z0-9]`, random, never derived from the session token) and `transcript` (in memory only) to `Session`, and add `"lang": s.lang` to the `done` event, in `backend/app/workflow/engine.py`
- [X] T009 Implement `Transcript`, `Entry`, and `TranscriptRecorder` in `backend/app/transcript/record.py`, following data-model.md:
  - **Fields**: `schema=1`; `renderer`; `conversation_ref`; `customer` = `{first_name, country}` only; `time_zone` from the country (`America/Mexico_City`, `America/Bogota`, `America/Argentina/Buenos_Aires`); `lang` ∈ {es, pt}; `case_ids`; `masked`; `entries`; `generated_at`.
  - **Passes T007.**
- [X] T010 Hook the recorder into `chat()` in `backend/app/api/main.py`:
  - record the customer's text before streaming;
  - record each event **after** the `internal` filter, only from what is yielded;
  - commit the turn in a `finally` on the generator.

  Add a test that an internal event (the compliance hold) never reaches the transcript.

**Checkpoint**: sessions now carry a masked, customer-visible transcript. `make test` and `make eval` pass unchanged.

---

## Phase 3: User Story 1 — Download my conversation as a PDF (Priority: P1) 🎯 MVP

**Goal**: the customer downloads the conversation as shown: messages in order, with author and time, statements with labels and sources, the case number, and rights and deadlines as stated.

**Independent Test**: file a claim in the chat, download, and compare the PDF with the screen (quickstart §2, step 1).

### Tests for User Story 1

- [X] T011 [P] [US1] Write failing rendering tests in `backend/tests/test_transcript.py`:
  - **Content**: the PDF's extracted text (pypdf, diagnostic only) contains every entry in order, each statement's basis label and source, the case number, and the rights and deadline text exactly as streamed.
  - **Determinism**: two renders of the same transcript are byte-identical.
  - **A conversation at the 40-turn limit**: renders in under 5 s (SC-101).
  - **No model**: the render makes no model call, checked by patching the LLM to raise (FR-112).
- [X] T012 [P] [US1] Write failing API tests in `backend/tests/test_transcript.py` for `POST /api/transcript`, following contracts/http-api.md:
  - **200**: `application/pdf`, with `Content-Disposition` and `X-Check-Code` set;
  - **401**: unknown or expired session;
  - **403**: a foreign `conversation_ref`, and the security flag `transcript_other_conversation` is recorded;
  - **409**: no committed turn yet;
  - **429**: over the per-IP limit.

### Implementation for User Story 1

- [X] T013 [US1] Implement `render(transcript) -> bytes` in `backend/app/transcript/render.py`:
  - **Format**: fpdf2 with DejaVu Sans, A4.
  - **Body**: entries with author labels and local times. Statements show their basis label and source. Candidates are shown as their numbered list, verdicts as their label, handoffs as "Caso X enviado a un especialista", and notices as text.
  - **Every page**: a header, and a footer with "página X de Y".
  - **Attachment**: `transcript.json` embedded.
  - **Metadata**: `set_creation_date(generated_at)` and a fixed `set_producer`, so the output is byte-identical.
  - **Page breaks**: a statement's label never splits from its text.
- [X] T014 [P] [US1] Create `backend/app/transcript/labels.py` with the Spanish fixed texts:
  - author labels;
  - basis labels *verificado · estimación · política*;
  - verdict labels, matching `frontend/src/Chat.tsx`;
  - header field names;
  - the page footer.

  Keep a `LABELS[lang]` shape, so User Story 3 only adds `pt`.
- [X] T015 [US1] Add `POST /api/transcript` to `backend/app/api/main.py`, following contracts/http-api.md:
  - session check;
  - `conversation_ref` check, with the security flag on a mismatch;
  - 409 when nothing is committed;
  - the per-IP guard (reuse `_session_log`'s pattern, with its own deque);
  - `generated_at` set now, in the customer's zone;
  - render and return. At this stage `X-Check-Code` is a placeholder until T021.
- [X] T016 [P] [US1] Add `downloadTranscript(sessionId, conversationRef)` to `frontend/src/api.ts`: POST, then a blob, then an object URL download using the `Content-Disposition` file name. Return `conversation_ref` from `POST /api/session` in `backend/app/api/main.py`.
- [X] T017 [US1] Add a "Descargar conversación (PDF)" button to the chat header in `frontend/src/Chat.tsx`:
  - it is disabled while `busy` or before the first completed turn;
  - it shows "Sesión expirada; inicie sesión de nuevo" on a 401;
  - after a `handoff` note, it adds a short hint: "Puede descargar una copia de esta conversación".

**Checkpoint**: User Story 1 works end to end in Spanish (quickstart §2, steps 1, 3, 4, and 7). This is a shippable MVP: the check code is not verifiable yet.

---

## Phase 4: User Story 2 — Identifiable, honest, and verifiable (Priority: P1)

**Goal**: a third party can place the document: header, notice, and check code. It says what it is not, and an edited copy fails verification (FR-104, FR-105, FR-111).

**Independent Test**: someone who didn't see the chat identifies the date, country, and case number, and the no-promise meaning. The original verifies as **match**, and an edited copy as **altered** (quickstart §2, steps 2 and 6).

### Tests for User Story 2

- [X] T018 [P] [US2] Write failing fingerprint tests in `backend/tests/test_transcript.py`:
  - **Canonical JSON**: sorted keys, no whitespace, UTF-8.
  - **Fingerprint**: `HMAC-SHA256(key, canonical)` is stable across runs.
  - **Check code**: `XXXX-XXXX-XXXX-XXXX` (Crockford base32 of the first 80 bits).
  - **Codes**: the same content gives the same code; one more message gives a new code.
  - **Register**: the JSONL line holds no message text, name, or amount, and a fingerprint already present is not appended again.
  - **Key**: a missing key gives an ephemeral key, and `/api/health` reports `"transcript_verification": "ephemeral"`.
- [X] T019 [P] [US2] Write failing verification tests in `backend/tests/test_transcript.py`:
  - **`match`**: the original, with `registered` true, then false after the register file is deleted.
  - **`altered`**: three tampers: (a) one character changed in a visible message, re-rendered with the original attachment; (b) the embedded JSON edited; (c) the case number swapped.
  - **`altered`**: a copy re-saved through pypdf's writer.
  - **`unknown_version`**: a different `renderer`.
  - **`unreadable`**: a non-PDF, and a PDF without the attachment.
  - **413**: over 2 MB.
  - **The response never contains message text.**
- [X] T020 [P] [US2] Write a failing test that the Spanish notice text passes the no-promise check (`PROMISES` in `backend/app/llm/claude.py`) and contains "no decide el reclamo" and "no promete ningún resultado", in `backend/tests/test_transcript.py`

### Implementation for User Story 2

- [X] T021 [US2] Implement `canonical()`, `fingerprint()`, `check_code()`, and `FingerprintRegister` (append-only JSONL at `settings.transcripts_path`, with a file lock like `HandoffQueue`) in `backend/app/transcript/fingerprint.py`.
  - **Ephemeral key**: when `transcript_hmac_key` is empty, generate a random key at import, with one warning log.
  - **Endpoint**: in `POST /api/transcript` (`backend/app/api/main.py`), compute the code, put it in the transcript, the footer, and `X-Check-Code`, then append to the register.
- [X] T022 [US2] Add the header fields, which are FR-104's full list, to `render()` in `backend/app/transcript/render.py`:
  - *Explica este cargo · LATAM Bank*;
  - the first name and country;
  - the conversation reference;
  - the case numbers;
  - the generation time with the zone name.

  Also add to the first page:
  - the fixed notice box;
  - "Conserve el archivo original: solo el original se puede verificar";
  - the masking note when `masked`.

  The check code goes in every page's footer.
- [X] T023 [US2] Implement `verify(pdf_bytes) -> dict` in `backend/app/transcript/verify.py`:
  1. read with pypdf; reject encrypted files or a missing `transcript.json` with `unreadable`;
  2. check `renderer`;
  3. recompute the HMAC over the canonical transcript without `check_code`, and compare it with the embedded and printed code;
  4. re-render and compare **byte for byte** with the upload;
  5. look up the register.

  Return only `result`, `check_code`, `registered`, `generated_at`, and `case_ids` (research §5).
- [X] T024 [US2] Add `POST /api/transcripts/verify` to `backend/app/api/main.py`: `multipart/form-data` field `file`, 413 over 2 MB, the per-IP guard, and the upload is never stored. Add `transcript_verification` (`"configured"` or `"ephemeral"`) to `/api/health`.
- [X] T025 [P] [US2] Add a "Verificar PDF" file input to `frontend/src/AgentQueue.tsx`, with `verifyTranscript(file)` in `frontend/src/api.ts`. Show the result as a coloured label:
  - *Coincide* (with "registrado" / "no está en el registro actual");
  - *Alterado*;
  - *Versión desconocida*;
  - *No legible*.
- [X] T026 [US2] In `scripts/deploy-azure.sh`, create the Container Apps secret `transcript-key` once if it is missing. Generate it with `python3 -c 'import secrets; print(secrets.token_urlsafe(32))'` into a variable that is never echoed. Wire it as `TRANSCRIPT_HMAC_KEY=secretref:transcript-key`, and keep the existing key when it is present, so issued PDFs keep verifying.

**Checkpoint**: User Stories 1 and 2 work together. The original verifies, and tampered and re-saved copies don't.

---

## Phase 5: User Story 3 — The PDF in my language (Priority: P2)

**Goal**: fixed texts follow the language of the latest assistant turn (FR-109).

**Independent Test**: download from a Portuguese conversation and a Spanish one, and check every fixed text (quickstart §2, step 5).

- [X] T027 [P] [US3] Write failing tests in `backend/tests/test_transcript.py`:
  - **Portuguese**: a Portuguese conversation gives Portuguese headings, labels (*verificado · estimativa · política*), and notice, and the file name `conversa-….pdf`.
  - **Language switch**: a conversation that switches language keeps its messages verbatim and follows the latest assistant turn for fixed texts.
  - **Notice**: the Portuguese notice passes the no-promise check.
- [X] T028 [US3] Add `pt` to `LABELS` in `backend/app/transcript/labels.py`, including the notice ("não decide a reclamação", "não promete nenhum resultado") and "Conserve o arquivo original…". Choose the file-name prefix by `lang` in `backend/app/api/main.py`.
- [X] T029 [US3] Label the download button by the `lang` of the latest `done` event ("Baixar conversa (PDF)"), and translate the post-handoff hint, in `frontend/src/useChat.ts` and `frontend/src/Chat.tsx`.

**Checkpoint**: all three stories work.

---

## Phase 6: Evaluation, docs, and deployment

- [X] T030 Add seeded cases to `backend/app/eval/cases.py`:
  - variants of `SHARED_YES` that include a code ("sí, le di el código 482913", "sim, passei o código 739201");
  - one message per language with a full test card number of 16 digits.

  Tag them `seeded_secret=True`. Keep the dev, test-seen, and test-heldout seeds and the per-set case count unchanged: replace phrasings rather than adding cases, and update `docs/evaluation.md` if counts move.
- [X] T031 Implement `backend/app/eval/transcript_check.py`. For each case of a run, rebuild the transcript from the run's streamed events through the same recorder, render it, and compute:
  - **SC-102**: complete and ordered, with the case number;
  - **SC-103**: internal markers absent: case type names, `priority`, `risk`, the compliance terms (*revisión*, *compliance*, *AML*, *lavado*), and any customer ID other than the session's. Report this for all cases, and separately for the compliance cases;
  - **SC-104**: no seeded secret unmasked;
  - **SC-107**: the original verifies, and the 3 tampers plus a re-save fail;
  - **SC-101**: p50 and p95 time per PDF.

  Call it from `backend/app/eval/run.py` after grading.
- [X] T032 Add a "Transcript PDF" section to the report in `backend/app/eval/report.py`, with counts and denominators per set and language. Run `make eval`, then regenerate `docs/evaluation.md`.
- [X] T033 [P] Update `docs/limitations.md`:
  - **Verification access**: the verify endpoint is unauthenticated in the demo, like the queue.
  - **Register durability**: the register is lost on scale to zero (verification still works, `registered: false`).
  - **Re-saved copies**: only the original file verifies.
  - **Legal status**: an HMAC is not a legal electronic signature. Future work: a signed PDF (PAdES) with a bank certificate.
- [X] T034 [P] Add the feature to `README.md` ("How it works" and the demo instructions), and add the transcript PDF and check code to `specs/001-dispute-intake-assistant/contracts/http-api.md` by linking to `specs/002-chat-transcript-pdf/contracts/http-api.md`
- [X] T035 Rebuild and redeploy with `make docker` and `make deploy-azure`. Then, on the deployed URL:
  - run quickstart §2, steps 1 and 6, and §3;
  - confirm that `/api/health` shows `"transcript_verification": "configured"`;
  - confirm that a PDF downloaded before an idle scale-to-zero still verifies as **match**.
- [ ] T036 SC-105, a manual check: show one Spanish and one Portuguese PDF to at least 5 readers who didn't see the chat. Record whether each one identifies the date, country, and case number and says the document does not promise an outcome. Record the result, as counts only, in `docs/evaluation.md`.
- [X] T037 Final gates:
  - run `make test`, the frontend build, and `make eval`;
  - run the full-history secret scan (0 matches);
  - check that `git ls-files '*.pdf'` lists only `docs/slides/slides.pdf`;
  - check off this file.

---

## Dependencies and execution order

- **Setup (T001–T004)** → **Foundational (T005–T010)** → the stories.
- **User Story 1 (T011–T017)** depends only on Foundational. It is the MVP.
- **User Story 2 (T018–T026)** depends on User Story 1's `render()` and endpoint (T013, T015). Its tests (T018–T020) can be written in parallel with User Story 1.
- **User Story 3 (T027–T029)** depends on `labels.py` (T014) and the `done` event's `lang` (T008). It can run in parallel with User Story 2.
- **Phase 6**: T030–T032 need User Stories 1 and 2; T035 needs everything; T036 needs a deployed build.

### Parallel opportunities

- **Setup**: T002, T003, and T004 together.
- **Foundational**: tests T005 and T007 together, then T006 in parallel with T008.
- **User Story 1**: T011, T012, and T014 together; T016 alongside T013.
- **User Story 2**: T018, T019, and T020 together; T025 alongside T023.
- **Across stories**: User Story 3 (T027–T029) alongside User Story 2's backend tasks, once T014 is done.
- **Docs**: T033 and T034 alongside T030–T032.

### Parallel example: User Story 1

```text
Together: T011 (render tests), T012 (API tests), T014 (Spanish labels)
Then:     T013 (render) with T016 (frontend api)
Then:     T015 (endpoint), T017 (button)
```

## Implementation strategy

1. **MVP first**: Setup, then Foundational, then User Story 1. The customer can download a faithful, masked, internal-data-free PDF. This is safe to deploy alone: the footer code would be a placeholder, so either hide it until User Story 2 lands or ship both together.
2. **Then User Story 2**: the check code and verification make it evidence. Deploy after T026, so the key persists.
3. **Then User Story 3**: Portuguese fixed texts.
4. **Then Phase 6**: measure (T030–T032), document, redeploy, run the reader check.

**Against the deadline**: if time runs short before 2026-10-05, the complete subset is User Stories 1 and 2 plus T031–T033 and T035. Portuguese labels (User Story 3) and the reader check (T036) would go to `docs/limitations.md` as open items.

## Notes

- **Never commit a generated PDF or the register.** Tests write to `tmp_path`.
- **Byte-identical rendering depends on the pinned fpdf2 version.** Bump the `renderer` identity in `backend/app/transcript/record.py` whenever the renderer or the layout changes. PDFs issued earlier then verify as `unknown_version`.
- Check off each task (`[X]`) when it lands and its gates pass.
