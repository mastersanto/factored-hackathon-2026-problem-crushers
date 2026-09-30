# Pending: UI improvements

**Feature**: [spec.md](spec.md) · **Tasks**: [tasks.md](tasks.md) · **As of**: 2026-09-30

The feature is implemented, and its automated checks pass: 51 UI checks, and the backend's 46 tests unchanged. This file lists what is still open, for review after the push.

## 1. Tasks not finished

| Task | What's left | Who | Blocks merge? |
|---|---|---|---|
| **T032** Manual checks ([quickstart §3](quickstart.md#3-manual-checks)) | Claim path on a real phone with the on-screen keyboard open; claim path with a screen reader (NVDA or VoiceOver), checking that each reply, verdict, and case card is read once and that Portuguese is pronounced as Portuguese; reduced-motion check. Record the results in a dated "Results" section at the end of `quickstart.md`. | Owner | No, but SC-204 is only half measured without it |
| **SC-202** Label test | Show one answer with all three labels to 3 people who haven't seen the product, and record whether each names fact, estimate, and rule correctly without help. | Owner | No |
| **T035** Container | Only the Windows Docker CLI is on this WSL, with no reachable engine, so `make docker` didn't run. Checked instead: `npm ci` from the lock plus `npm run build` on a clean copy both pass, and `.dockerignore` excludes the screenshots. Still to do: `make docker`, then `make docker-run`, and open `http://localhost:8080` at 375 px. | Owner (needs Docker Desktop with WSL integration) | Yes, before deploying |
| **T036** Official secret scan | The branch was pushed after a substitute scan: AWS keys, API keys, the local HMAC key, S3 and bucket references, customer, transaction, and contact IDs, and dataset names and merchants, with 0 findings. The official scan in `CLAUDE.md` needs `~/.aws/factored-datathon-scan-patterns` and `~/.aws/factored-datathon-bucket`, and neither is on this machine. Run it on the branch's diff against `main` (`git diff main...003-ui-improvements`, must be 0) before the pull request merges. | Owner | **Yes** (constitution IV) |

## 2. Review points

- **The charge list isn't in any automated check.** No demo customer produces more than one matching charge. `CandidateList` type-checks, but it hasn't been seen on screen. To see it, sign in and send a message that matches 2 to 5 charges, for example an amount with no merchant, then compare with the prototype's frame 3a.
- **The keyboard test takes one shortcut.** It focuses the text box directly instead of tabbing to it. Everything else is reached with Tab and Shift+Tab (`frontend/e2e/a11y.spec.ts`).
- **Message times come from the browser.** The PDF's come from the server, so they can differ by a minute at a minute boundary ([research R11](research.md#r11-times-on-messages)).
- **The design export** is committed as the visual reference, including `design/support.js` (the prototype's viewer). The `.zip`, `.thumbnail`, and `uploads/` are git-ignored. Decide whether the committed files should stay in the public repository.

## 3. Found outside this feature's scope

- **Demo customer labels are in English** ("charge flagged by the fraud-risk estimate", "pending charge"…). They come from the API (`/api/demo/customers`), and they show on sign-in. Fixing them means a backend change.
- **Spanish example messages show in a Portuguese chat** when a reply has no quick replies, for example after the Portuguese call check. They are sample customer messages from `suggestionsFor` in `App.tsx`, in both languages, not fixed UI text, so the language check excludes them. A possible follow-up is to show only Portuguese examples once the conversation is in Portuguese.
- **The specialist queue keeps growing** with each test run, since handoffs persist in `backend/data/handoffs.jsonl`, which is git-ignored. Clear it before a demo or before recording the video.

## 4. Prototype elements not built

These are listed in [research R10](research.md#r10-what-the-prototype-has-that-this-feature-doesnt-build). Each needs a workflow or API change, so each is a candidate for a later feature:

- "Hablar con una persona" in the composer, which needs an "ask for a person" intent;
- "Ninguno de estos cargos coincide" under the charge list, which needs a "none of these" intent;
- "Tomar caso" on specialist cards, which needs case assignment in the API;
- full name, card last four digits, and currency on sign-in and in the customer bar, which need new fields from the demo-customer endpoint;
- the deadline date inside the case card, which needs the date in the handoff event, and that means more data on the customer's device;
- the new PDF layout ("PDF Copy"), which needs a new renderer version (specs/002).

## 5. Local setup used for the checks (not in the repository)

- **Chromium libraries**: Chromium needed `libnspr4`, `libnss3`, and `libasound2`, which weren't installed, and sudo wasn't available. They were extracted into `~/.cache/playwright-libs`, and the checks ran with `LD_LIBRARY_PATH` pointing there. The steps are in the [quickstart](quickstart.md#prerequisites). `sudo npx playwright install-deps chromium` is the permanent fix.
- **Session limit**: the checks need `SESSIONS_PER_IP_HOUR=1000`, since a full run opens about 60 sessions ([quickstart §2](quickstart.md#2-automated-ui-checks)).
- **Node**: Node 22 via nvm, and npm 11 for installs, so the lock file keeps its `libc` fields (T001).
