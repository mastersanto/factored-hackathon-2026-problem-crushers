# Research: The whole app in English, Spanish, or Portuguese

Decisions for [plan.md](plan.md). Each one gives the decision, why, and what else was considered.

## R1. Interpreter and translator: separate modules in the one container, not separate services

- **Decision**: two new Python packages, behind narrow interfaces, inside the existing API process:
  - `app/language/interpreter.py`: `interpret(text, context) -> Understanding`, from any of the three languages to the common form;
  - `app/language/translator.py`: `render(statements, lang)` for assistant messages, and `translate_customer(text, target)` for the customer's own words.

  The engine calls only these two. Their inputs and outputs are plain data (Pydantic models), so either can move behind an HTTP boundary later without changing the engine.
- **Why**:
  - The deployment is one container on Azure Container Apps, scaling to zero. Three services would mean three cold starts on the first request, three images and three sets of secrets, and network failure modes between them, all with five days left.
  - Rules mode must work with no model (constitution I). In-process calls keep that fallback a function call, not a degraded network path.
  - The owner's goal, adding languages later without touching the core, comes from the interface boundary, not from the process boundary.
- **Considered**:
  - Separate Container Apps for the interpreter and the translator. Rejected for now for the reasons above. Revisit if a language team needs to deploy on its own.
  - One "language service" doing both. Rejected: the interpreter is on the safety path and the translator is not, and keeping them apart keeps that clear.

## R2. English as the base: the common form, the source wording, and the template keys

- **Decision**:
  - The common form is the existing `Understanding` (intent, slots, safety signals), with English names. Its `language` field gains `en`, plus a "clear" flag (R4).
  - The fixed wording in `workflow/messages.py` gains `en` for every key, and English is listed first as the source text. Spanish and Portuguese stay as they are, word for word, so their evaluation results cannot move.
  - Country rights (`policy/rules.py`), channel, product, and transaction-type names, month names, and quick replies gain `en`.
- **Why**: a new language then means one more column of wording, one keyword list, and one line in the model's instructions. The engine, tools, rules, and guards do not change (constitution I).
- **Considered**: translating the customer's text into English sentences first and understanding the English. Rejected by the owner's clarification and constitution v1.1.0: it breaks rules mode, garbles amount and date formats and negations before the code sees them, and adds a model call to every message.

## R3. Safety checks on the original words, in all three languages

- **Decision**: the deterministic scans in `workflow/understanding.py` gain English keywords and always run on the original message, before and alongside any model:
  - requests for secrets: "code", "pin", "password", "otp", "token", "cvv", combined with "asked", "requested", "give", "send";
  - injection: "ignore previous", "ignore your instructions", "you are now", "system prompt", "developer mode";
  - other customers: the `CLI-…` pattern, unchanged;
  - negation (files the claim): "wasn't me", "was not me", "not me", "didn't make", "did not make", "don't recognize", "do not recognize", "not mine", "fraud", "stolen", "dispute", "i want to dispute";
  - recognition (needs agreement to close): "it was me", "yes it was me", "i made it", "i recognize it", "that's mine".

  The existing merge in `Engine._understand` is kept: the model's flags are OR-ed with the rules' flags, a rules negation always files the claim, and closing needs both to agree.
- **Why**: constitution II and III, and FR-411. A model's reading cannot drop a flag.
- **Test**: a parametrized test runs every guard phrase in all three languages, with the deliberately wrong fake model the guard tests already use. Each guard must fire in every language (SC-406).

## R4. Detecting the message's language, and when it is "clear"

- **Decision**:
  - **Rules**: score marker words per language (English, Spanish, and the existing Portuguese markers), after removing accents and lowercasing. The language is clear when the top score is at least 1 and strictly higher than the others, and the message has at least two words of letters. Otherwise it is unclear (`None`).
    - Option numbers, "ok", amounts, dates, and a bare "sí" or "yes" are therefore unclear.
    - "sí" and "yes" are still understood at the confirm step, which already uses `CONFIRM_YES` and `CONFIRM_NO` (extended with "yes", "yeah", "no", "nope").
  - **Model**: the understanding schema's `language` becomes `en | es | pt | unclear`, with an instruction to answer `unclear` for short or mixed messages. When the model runs, its language is used only if the message passes the same two-word minimum.
- **Why**: FR-407 asks for a switch only on a clear signal. A bare "1" must never flip the conversation's language.
- **Considered**: a language-identification library (`langdetect`, `lingua`). Rejected: a new dependency, unreliable on short messages, and the marker approach already works for Portuguese and is tested.

## R5. Number and date formats per language

- **Decision**:
  - Amounts are written as `1,234.56 USD` in English and `1.234,56 USD` in Spanish and Portuguese.
  - Dates are written as "June 12, 2026, 14:05" in English and "12 de junio de 2026, 14:05" in Spanish.
  - The value, currency, and time are identical across languages. Only the formatting differs.
- **Parsing**: numeric dates (`12/06`) are read day first in every language, since every customer is in Mexico, Colombia, or Argentina. English month names ("June 12", "12 June") and "yesterday" and "today" are added. Amounts accept both separator styles, as today.
- **Faithfulness**: the check compares numbers within one language (source statements against the model's rewording in that same language), so per-language formatting does not affect it. The English promise list is added: "we will refund", "you will get your money back", "guaranteed", "will be approved", "send us the code", "share your password".

## R6. Every assistant message keeps a language-neutral recipe (template key and parameters)

- **Decision**: `Statement` gains two server-side fields:
  - `key`: the template key, or `rule:<id>` for a right;
  - `params`: the raw verified values (amount, currency, date as ISO text, merchant, city, country, channel code, product code, last four digits, counts, case number).

  Candidate cards and verdicts already carry codes. Their raw values are kept server-side in the same way.
  - `translator.render(statements, lang)` rebuilds the text in any language from key and params, with no model.
  - The API strips `key` and `params` before streaming, so the browser receives exactly what it does today.
- **Why**: FR-420 and FR-421. Re-showing earlier messages must not add, drop, or change a fact, and must work in rules mode. Rebuilding from the recipe guarantees both. Translating rendered text with a model guarantees neither.
- **Re-showing a reply the model reworded**:
  - in its original language, the original text is shown (FR-423);
  - in another language, the fixed wording is rebuilt. It is not re-phrased by the model on a switch, which keeps switching free and instant (SC-407) and leaves nothing to fail the faithfulness check.
- **Considered**: asking Sonnet to re-phrase in the new language, checked for faithfulness. Rejected: it costs a model call per message per switch, it is slower than 2 s for 20 messages, and the gain is only style.

## R7. Translating the customer's own words

- **Decision**:
  - **The call**: `translator.translate_customer(masked_text, target)` uses Claude Haiku 4.5, with the text passed as data inside tags and an instruction to translate only.
  - **Accepted only if** every number in the original appears in the translation, no new number appears, and the length stays within 0.5× to 2× of the original. Otherwise no translation is shown, and the original appears with a note (FR-422).
  - **Cached** per session, keyed by (message index, target language), so a second switch to the same language costs nothing.
  - **Only the masked text is sent.** Card numbers and codes the customer typed are already replaced with •••• by the transcript recorder (specs/002), which meets constitution IV.
  - **Spend** counts against the same `MAX_LLM_USD` cap. Past the cap, no translation is made, and the original is shown with a note.
- **Why**: only a model can translate free text. The customer's words remain the record (constitution v1.1.0, Principle I).
- **Rules mode**: no translation; the original is shown with a note.

## R8. Changing language: who decides, and how the server learns of it

- **Decision**:
  - The session gains `lang` (`en | es | pt`), set when the session is created, from the app language the browser sends.
  - **A clear message language** sets `s.lang` at any stage, not only at the start as today. The reply comes in that language, and `done.lang` reports it.
  - **The switcher**:
    - before sign-in, it changes only the browser's state;
    - after sign-in, it calls `POST /api/session/language`, which sets `s.lang` and returns the whole conversation re-rendered (R6, R7).
  - **A reply whose `done.lang` differs from the screen's language** makes the browser fetch the re-rendered conversation once, through the same endpoint.
  - **The most recent signal wins**, with no extra rule: each signal simply overwrites `s.lang`.
- **The pending question**: when the language changes at the "was it you?" step, the stage does not change. The re-rendered history shows the question in the new language, the quick replies come in the new language, and the confirm rules accept "yes" and "no" in all three.

## R9. The browser side: detection, storage, and no flash of another language

- **Decision**:
  - **`frontend/src/language.ts`** holds two functions:
    - `pickLanguage(navigator.languages, stored)`: a stored choice wins. Otherwise the first entry whose primary subtag (lower-cased) is `en`, `es`, or `pt`. Otherwise `en`.
    - `storeLanguage(lang)`: writes to `localStorage` key `app-language`, inside try/catch, so the app works when storage is blocked.
  - **No flash**: the language is computed once in `main.tsx`, before the first render, and `document.documentElement.lang` is set at the same moment. All three text sets are in the bundle, so there is no loading step to wait for.
  - **A React context** provides `lang` and `setLang`. `App` reads it everywhere. `TEXT` becomes `Record<'en' | 'es' | 'pt', TextSet>`, so a missing text in any language fails the type-check, as in specs/003.
- **Why**: FR-402 to FR-406. `navigator.languages` is the browser's ordered preference list. Only the choice is stored, on the device.

## R10. Screens that were Spanish-only

- **Decision**: every fixed text in `App.tsx` (header, sign-in, security notice, errors) and `AgentQueue.tsx` (specialist view, PDF check) moves into `TextSet`.
  - The demo endpoint adds a stable `scenario` id to each customer (`fraud_flagged`, `pending`, `mx_debit_48h`, `co_purchase`, `ar_purchase`, `compliance`, `bank_message`), and the card shows `TEXT[lang].scenario[id]`.
  - The English `label` stays in the API for the UI checks.
- **The specialist's translations**: `GET /api/handoffs?lang=xx` adds, for each case whose language differs, a marked translation of the request and of the customer's statement (R7 rules, cached per case). The verified facts and IDs are not translated.

## R11. The PDF: a new renderer version, with the old one frozen

- **Decision**:
  - **The snapshot** is built in the session's language at download time, with schema `2`:
    - assistant entries carry the text rebuilt in that language (or the original text, if that was its language);
    - customer entries carry `original`, `original_lang`, and, when they differ from the PDF's language, `translation` (or `translation_missing: true`).
  - **The renderer** becomes `fpdf2-2.8.9/r2`. It adds an English label set and prints a customer translation beneath the original, marked as a translation.
  - **The r1 renderer and its labels are copied, unchanged, into `transcript/render_v1.py`**. `verify()` picks the renderer by the embedded `schema` and `renderer`. PDFs issued before this feature still re-render byte for byte and verify (FR-426, SC-409).
  - **The language is inside the fingerprinted JSON**, as today, so changing it is detected as an alteration.
  - **English file names** start with `conversation-`, added to `.gitignore` next to `conversacion-*.pdf` and `conversa-*.pdf`.
- **Why**: verification re-renders the embedded JSON and compares bytes. Changing the r1 layout or labels in place would turn every PDF issued so far into "altered" or "unknown version".
- **Considered**: bumping the renderer and accepting that old PDFs become "unknown version". Rejected: `CLAUDE.md` forbids breaking PDFs already issued, and the live demo has issued some.

## R12. Evaluation in three languages (constitution V)

- **Decision**:
  - **English phrasings** are added to `eval/cases.py` for every category, in both the tuning set (`DESCRIBE`, `CONFIRM`, …) and a separate held-out set (`HELDOUT`). The held-out English is written before the rules are tuned on the English dev set, and is never used to tune them.
  - Each set grows from 15 categories × 2 languages × 6 cases (180) to 15 × 3 × 6 (270).
  - **A new category `language_switch`**, 6 cases per set: describe in one language, answer the question in another, file the claim. Expected: the same transaction, the same handoff, and every earlier assistant message re-rendered with the same sources.
  - **A parity check** runs 6 transactions through the same steps in all three languages and compares the tools called, the transaction found, the decision, and the handoff (SC-404).
  - **The report** adds English to "By language", in rules mode for free. Claude-mode numbers need `make eval-llm`, which costs about $3 with the larger sets, so the owner is asked first.
- **Why**: no metric without a reproducible run on held-out cases (constitution V). The Spanish and Portuguese phrasings and seeds stay unchanged, so their results stay comparable.

## R13. UI checks with an explicit browser language

- **Decision**:
  - The four existing Playwright projects set `locale: 'es-MX'`, so every existing check runs unchanged: before the first reply, the texts are Spanish.
  - New specs set the locale per test (`en-US`, `pt-BR`, `fr-FR`, and `fr-FR,es` through `extraHTTPHeaders` and `navigator.languages`). They cover detection, the fallback, the switcher, re-showing, and axe and phone width in English.
  - The sign-in helper finds the card by the `scenario` id and clicks it by its text in the current language.
- **Why**: Playwright defaults to `en-US`. Without the explicit locale, every existing Spanish check would fail for the wrong reason.

## R14. Delivery order, given the deadline

- **Decision**: build and ship in three increments, each passing every gate on its own:
  1. **Interface**: browser detection, the switcher, the English text set, and the screens that were Spanish-only. Frontend only (stories 1 and 4, and FR-408 for the fixed texts).
  2. **Conversation**: English understanding and wording, statement recipes, the language endpoint, re-showing, and customer translation (stories 2, 3, and 5). This includes the demo path: Spanish, then a switch to Portuguese.
  3. **Records**: the PDF r2 with r1 frozen, the specialist's translations, and the evaluation in three languages.
- **Why**: submissions close 2026-10-05, and the video is not recorded. Increment 1 is low-risk and visible. Increment 2 holds the demo's centre. Increment 3 completes the record and the evidence. Each redeploy needs the owner's approval.
