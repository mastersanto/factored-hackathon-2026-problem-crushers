# Quickstart: validating the UI improvements

**Feature**: [spec.md](spec.md) · **Contract**: [contracts/ui.md](contracts/ui.md)

## Prerequisites

- The repository is set up as in the [README](../../README.md#run-it-locally): `make setup`, `make data`, and `make model` have run.
- Node 20 or later, from WSL, not Windows.
- Playwright's Chromium, installed once:
  ```bash
  cd frontend && npx playwright install chromium
  # WSL only, if Chromium fails to start:
  sudo npx playwright install-deps chromium
  ```
  - **Without sudo**: on the owner's WSL (Ubuntu 26.04), Chromium was missing only `libnspr4`, `libnss3`, and `libasound2`. Extract them into a user folder and point the checks at it:
    ```bash
    D=~/.cache/playwright-libs; mkdir -p $D/debs && cd $D/debs
    apt-get download libnspr4 libnss3 libasound2t64 && for f in *.deb; do dpkg -x $f $D/root; done
    export LD_LIBRARY_PATH=$D/root/usr/lib/x86_64-linux-gnu   # in the shell that runs npm run check:ui
    ```
- Rules mode is enough, and free: leave `ANTHROPIC_API_KEY` empty, or set `LLM_DISABLED=1`.

## 1. The existing guarantees still hold

```bash
make test                         # 46 passed, unchanged (SC-206)
cd frontend && npx tsc -b && npm run build
```

- **Expected**: every existing test passes, and the type-check fails if any text is missing in either language (FR-201).
- **Evaluation**: this feature doesn't touch the workflow, so `make eval` isn't required. `docs/evaluation.md` must not change.

## 2. Automated UI checks

```bash
SESSIONS_PER_IP_HOUR=1000 LLM_DISABLED=1 make dev   # terminal 1: API :8000, web :5173, rules mode
cd frontend && npm run check:ui                     # terminal 2
```

- **Session limit**: a full run opens about 60 sessions, and the API allows 30 per IP per hour by default (`SESSIONS_PER_IP_HOUR`). The higher limit is for the local check only.
- **Port**: the checks expect the web app on `:5173`. If an old dev server holds it, Vite moves to `:5174` and every check fails to connect.

| Check | What it does | Covers |
|---|---|---|
| Screenshots | claim (ES), call check (PT), scam (ES), refusal, and specialist queue, at 1200 and 375 px, light and dark, saved to `frontend/e2e/screenshots/` | visual comparison with [design/](design/) |
| No sideways scroll | every screen at 375 px | SC-203, FR-208 |
| No Spanish in Portuguese | fixed texts in the PT run contain no Spanish-only string from the dictionary | SC-201, FR-201 |
| axe | sign-in, chat, and specialist views, light and dark, 0 violations | SC-205, FR-214, FR-216 |
| Keyboard only | claim path completed with Tab / Enter / Space only | SC-204 (automated part), FR-212 |
| Tap targets | every control at least 44 × 44 px at 375 px | FR-211 |

- **Expected**: every check passes.
- **Visual review**: compare the screenshots with the prototype's frames. Open `design/Explica este cargo.dc.html` in a browser (it loads `support.js` from the same folder). The differences listed in [research R10](research.md#r10-what-the-prototype-has-that-this-feature-doesnt-build) are intended.

## 3. Manual checks

1. **Phone**:
   - Open `http://<wsl-ip>:5173` on a real phone (`npm run dev -- --host`), or use the browser's device mode at 375 px.
   - Complete the claim path. With the keyboard open, the text box and the latest message stay visible (FR-209).
   - The steps drawer opens and closes, and it is closed by default (FR-210).
2. **Screen reader** (NVDA on Windows, or VoiceOver):
   - Complete the claim path.
   - Each reply, verdict, and case card is read out once without moving focus (FR-213).
   - The text box is read as "Mensaje" / "Mensagem".
   - A Portuguese message is pronounced in Portuguese (FR-215).
3. **Source labels**:
   - Tap a label's reference on a phone, and reach it by keyboard.
   - Open "¿De dónde sale este dato?". It explains the three kinds in the conversation's language (FR-205, FR-206).
4. **Label test (SC-202)**: show one answer that has all three labels to 3 people who haven't seen the product, and record whether each names fact, estimate, and rule correctly without help.
5. **Reduced motion**: turn on "reduce motion" in the operating system. New messages appear with no smooth scroll and no animation (FR-217).
6. **Claude mode** (optional, costs a few cents): with a key set, a reworded answer shows as a paragraph plus a "Fuentes" list, and the words match the PDF ([research R2](research.md#r2-statements-and-their-source-labels)).

## Known differences from the PDF

- **Message times**: the chat takes them from the browser, the PDF from the server. They can differ by a minute at a minute boundary ([R11](research.md#r11-times-on-messages)). The PDF is the record.
