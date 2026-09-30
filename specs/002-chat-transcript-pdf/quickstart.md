# Quickstart: validate the transcript PDF

How to prove the feature works end to end. The contracts are in [`contracts/http-api.md`](contracts/http-api.md), and the structures in [`data-model.md`](data-model.md).

## Prerequisites

- The feature 001 setup (`make setup`, `make data`, `make model`).
- `TRANSCRIPT_HMAC_KEY` set in `.env.local`, for example to the output of `python -c "import secrets; print(secrets.token_urlsafe(32))"`. Never commit it. Without it, the app uses an ephemeral key, and `/api/health` shows `"transcript_verification": "ephemeral"`.
- **Never commit a generated PDF**: it holds synthetic customer rows. Save downloads outside the repository, or rely on the `.gitignore` patterns `conversacion-*.pdf` and `conversa-*.pdf`.

## 1. Automated checks

```bash
make test    # includes backend/tests/test_transcript.py
make eval    # rules mode; the transcript checks run after each set
```

The expected results in `docs/evaluation.md`, section "Transcript PDF":

| Check | Expected |
|---|---|
| SC-102: complete and ordered | 100% of cases, with the count shown |
| SC-103: internal data or other customers' data | 0, including every compliance-review case |
| SC-104: unmasked seeded card numbers or codes | 0 |
| SC-107: untouched PDFs that verify / tampered PDFs that fail | 100% / 100% (3 tampers per case) |
| SC-101: time per PDF | p95 under 5 s (expected under 1 s) |
| Model calls made by the feature | 0 |

## 2. Manual walk-through (`make dev`, http://localhost:5173)

1. **Claim, in Spanish**: pick the Argentina or Colombia customer. Click "No reconozco un cargo…", pick the charge, then "No fui yo".
   - Click **Descargar conversación (PDF)**.
   - Check that the PDF shows every message in order, the *verificado* / *política* labels with sources, the case number, the deadline exactly as in the chat, the notice, the zone-stamped header, "página X de Y", and the check code.
2. **Download twice**: the check code is the same. Send one more message and download again: the code changes.
3. **Masking**: type "Compartí el código 482913 por teléfono". The PDF shows `••••` and the masking note. The rest of the sentence is unchanged.
4. **Compliance hold**: pick the synthetic compliance-review customer and ask about the charge. The PDF has the neutral message and the case number, and no mention of a review, priority, or risk.
5. **Portuguese**: write "Não reconheço uma compra…". The button, headings, labels, and notice are in Portuguese, and the file is named `conversa-…pdf`.
6. **Verification**: open **Especialista** and upload the PDF from step 1. The result is **match**.
   - Edit a message in the PDF, for example with a PDF editor, and upload it again. The result is **altered**.
   - Open the original in a viewer and "print to PDF", then upload the copy. The result is **altered**: only the original download verifies.
   - Upload any other PDF. The result is **unreadable**.
7. **Expired session**: set `SESSION_TTL_SECONDS=5`, restart, wait, then download. The request gets a 401 and the UI asks the customer to sign in again.

## 3. In the container and on Azure

```bash
make docker && make docker-run    # the same walk-through on http://localhost:8080
make deploy-azure                 # creates the `transcript-key` secret once if it is missing (never printed)
```

On the deployed URL, repeat steps 1 and 6. Then wait for the app to scale to zero, open it again, and verify the same PDF. The result is still **match**, with `registered: false` if the register was lost with the container: the HMAC key persists as a secret, and the register does not (see `docs/limitations.md`).
