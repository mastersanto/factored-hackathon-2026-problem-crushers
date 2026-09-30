# Research: Chat transcript as a PDF

The decisions behind the plan. The spec left none of these open, since FR-111 was resolved as option B. The plan chooses where the transcript comes from, how the check code works, and who can verify a PDF.

## 1. Where the transcript comes from: recorded by the server, not sent by the browser

- **Decision**: a `TranscriptRecorder` in the API's chat stream records every event **after** the internal-event filter, plus the customer's message. It stores the entries in the session's memory. A turn is committed when its stream ends, including when the client disconnects, so a PDF requested mid-reply holds only completed turns.
- **Rationale**:
  - A check code only means something if the bank computes it over content the bank produced. A transcript posted by the browser could be edited before signing.
  - Recording after the filter makes FR-106 structural: an event the customer never received cannot be recorded.
  - Memory storage expires with the session, so no conversation text is persisted, as option B requires.
- **Alternatives considered**:
  - **Build the PDF in the browser from the chat state**: this is simple, but the bank cannot vouch for it and it cannot carry a meaningful code.
  - **Re-run the conversation on the server**: model replies vary, so the result would not be what the customer saw.

## 2. Masking: at record time, before anything is stored or fingerprinted

- **Decision**:
  - **Card numbers**: runs of 13 to 19 digits, with optional spaces or dashes, become `•••• 1234` (the last four digits kept).
  - **Codes, PINs, passwords, tokens**: a run of 4 to 8 digits within a few words of a keyword becomes `••••`. The keywords are, in Spanish and Portuguese: *código, clave, contraseña, PIN, OTP, token, NIP, senha, código de verificação*.
  - **Where**: masking applies to the customer's messages only. The assistant never prints these.
  - **Marking**: a masked entry is flagged, and the PDF prints the masking note.
- **Rationale**:
  - The masked text is what gets fingerprinted and embedded, so no secret reaches the register, the embedded JSON, or the PDF.
  - The customer's other words stay verbatim, as evidence.
- **Alternatives considered**:
  - **Mask only when rendering**: the embedded JSON would still hold the secret.
  - **Drop the whole message**: that loses evidence the customer may need, such as "I shared the code by phone".

## 3. Rendering: fpdf2 with a bundled DejaVu Sans, pinned, deterministic

- **Decision**:
  - **Engine**: fpdf2 `2.8.9`, pinned exactly; A4 pages.
  - **Font**: DejaVu Sans, regular and bold, bundled with its license. It covers Spanish and Portuguese accents, «», ¿¡, •, and →.
  - **Every page** carries a header, and a footer with "página X de Y" and the check code.
  - **The canonical transcript** is embedded as `transcript.json`.
  - **Metadata**: the PDF's creation date is set to the transcript's `generated_at`, and the producer string is fixed, so the same transcript always renders to the same bytes (confirmed by the probe in §5).
- **Rationale**:
  - fpdf2 is pure Python with no system dependencies, which keeps the container slim, and it supports embedded files.
  - Deterministic rendering is what lets verification re-render and compare pages (decision 5).
- **Alternatives considered**:
  - **WeasyPrint**: HTML to PDF, but it needs Pango and Cairo in the image.
  - **ReportLab**: capable, but embedding files needs more work, with no benefit here.
  - **The browser's print dialog**: output varies by browser, and the server can't fingerprint it.

## 4. The check code: HMAC-SHA256 over canonical JSON, keyed by a server secret

- **Decision**:
  - **Canonical form**: the transcript as JSON with sorted keys, no whitespace, UTF-8, and a `schema` and `renderer` version field.
  - **Fingerprint**: `HMAC-SHA256(TRANSCRIPT_HMAC_KEY, canonical)`, stored in hex.
  - **Check code**: the first 80 bits in Crockford base32, grouped `XXXX-XXXX-XXXX-XXXX`.
  - **Register**: each download appends `{fingerprint, check_code, conversation_ref, case_ids, generated_at, schema, renderer}` to the register. Identical content is not duplicated.
- **Rationale**:
  - **Why a keyed hash**: a plain hash of a short conversation could let anyone who obtains the register confirm a guessed conversation. The key prevents that. It also makes the code unforgeable without the bank's secret.
  - **Survives restarts**: verification recomputes the HMAC, so a PDF still verifies after the register is lost. The register adds only the issue time and revocation-style information.
  - **Code length**: 80 bits is short enough to read aloud and long enough to be unguessable.
- **Key handling**:
  - **Local**: from `.env.local`.
  - **Azure**: a Container Apps secret `transcript-key`, created once by `deploy-azure.sh` from a random value that is never printed.
  - **When missing**: the app generates an ephemeral key at start and logs a warning. `/api/health` then reports `transcript_verification: "ephemeral"`, since codes won't verify after a restart.
- **Alternatives considered**:
  - **A digital signature (RSA or Ed25519, PAdES)**: anyone could verify offline, but it needs key management and a certificate story beyond a prototype. It is listed as future work.
  - **Storing the full transcript** (option C): rejected by the owner.

## 5. Verification: an upload, with three checks

- **Decision**: `POST /api/transcripts/verify` takes a PDF (at most 2 MB) and returns:
  - `unreadable` if it is not a PDF, or has no embedded transcript;
  - `altered` if either:
    1. the recomputed HMAC doesn't match the code in the embedded transcript;
    2. the uploaded file is not byte-for-byte identical to a fresh render of the embedded transcript;
  - `unknown_version` if the renderer version differs from the current one;
  - `match` otherwise. It includes `registered: true|false` (whether the register still holds the fingerprint), the issue time, and the case numbers.

  It never returns message text.
- **Rationale**:
  - Check 1 catches edits to the embedded data. Check 2 catches edits to the visible pages, even if the attachment is left intact.
  - **A probe on 2026-09-30 (fpdf2 2.8.9, pypdf 6.19.0) ruled out comparing page content streams.**
    - With a subset TTF font, the streams hold glyph indices assigned in order of first use. Changing "•" to "x" left the page streams identical; only the font subset changed.
    - Whole-file output, with a fixed creation date and producer, was byte-identical across renders.
    - So the check compares the whole file.
  - **Consequence**: a copy re-saved by another tool (for example "print to PDF") reports `altered`, even if the text looks the same. The customer should keep the original download, and the UI and the notice say so.
  - Text extraction (pypdf read the accents, «», and → correctly) is kept only as a diagnostic in tests. It is lossy with wrapped lines, so it is never used as the check.
- **Who verifies**:
  - **In the demo**: the **Especialista** tab gets an upload box, standing in for the bank's staff tools.
  - **Rate limit**: the endpoint shares the per-IP guard.
  - **Production**: it would sit behind staff authentication, and could be offered to regulators through the bank's normal channels (see `docs/limitations.md`).
- **Alternatives considered**:
  - **Verification by code and case number only**: this proves the code was issued, not that the text wasn't changed, so it doesn't meet FR-111.
  - **Customer-side self-check**: unnecessary, since the customer has the original.
  - **Comparing page content streams**: misses edits (see the probe above).

## 6. Language and time zone

- **Decision**:
  - **Language**: fixed texts follow the language of the latest assistant turn. The engine adds `lang` to the `done` event, and the recorder stores it per turn.
  - **Time zone**: times use the customer's country, via the IANA zones `America/Mexico_City`, `America/Bogota`, and `America/Argentina/Buenos_Aires`, and the header names the zone.
  - **Clock**: times are real wall-clock times. "Today" in the dataset is a separate notion, used only for charge lookups.
- **Rationale**: FR-109 and FR-104. `tzdata` is added so the zones exist in the slim image.

## 7. Evaluation of the feature

- **Decision**: a new module, `app/eval/transcript_check.py`, runs after each evaluation run. It renders every case's PDF and checks:
  - **SC-102**: every streamed customer-visible event appears, in order, with labels and sources, plus the case number when one exists;
  - **SC-103**: no internal marker appears, such as case types, priority, the risk estimate, compliance terms, or other customers' IDs. This includes every compliance-review case;
  - **SC-104**: seeded card numbers and codes are masked. The generator adds variants of the "I shared a code" and "here is my card number" messages that include a number;
  - **SC-107**: every untouched PDF verifies, and three tampered copies of each fail: an edited visible message, an edited embedded JSON, and a swapped case number;
  - **SC-101**: the time per PDF.

  Results go into a new section of `docs/evaluation.md`, as counts with denominators. The checks run in rules mode, for free.
- **Rationale**: Principle V. The claims in the spec are measured on the same held-out sets as the rest of the system.
- **Not automated**: SC-105 (readers identifying the document) is a manual check with at least 5 people. It is recorded when done.
