# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

The build for the Factored AI & Data Hackathon 2026, team **Problem Crushers**: "Explain this charge", a transaction-dispute intake assistant for LATAM Bank customers in Mexico, Colombia, and Argentina, in Spanish and Portuguese.

- **Public repository name**: `factored-hackathon-2026-problem-crushers`, as the organizers require.
- **Deadline**: submissions close 2026-10-05, midnight Colombia time.
- **Where the idea comes from**: the assessment lives in the ideation repository `~/personal/factored-idea` (`.specify/assessments/explain-this-charge/`). This repository starts from `docs/idea-brief.md` and `docs/build-plan.md`. If they conflict with that assessment, the assessment's latest dated section wins.

## Spec Kit

This repository uses GitHub Spec Kit (`specify` 1.0.11.dev0, Claude integration).

- **The constitution** (`.specify/memory/constitution.md`, v1.0.0) overrides other guidance. This file must stay consistent with it.
- **Features**, each with spec, plan, research, data model, contracts, quickstart, and tasks:
  - `specs/001-dispute-intake-assistant/`: the assistant, as built. Open: T034-T035 (only if the financial specialist's answers arrive), T042 video and T044 submission (owner).
  - `specs/002-chat-transcript-pdf/`: the conversation as a PDF with a check code (HMAC; the bank keeps only fingerprints). Done and deployed. Open: T036, a reader check with 5 or more people (owner).
  - `specs/003-ui-improvements/`: UI in the customer's language, source labels, phone width, accessibility. Merged and deployed. Open items in its `pending.md` (manual checks and a label test, owner).
- **`.specify/feature.json`** (git-ignored) points the `/speckit-*` commands at the current feature. Update it when starting a new one.
- **Keeping tasks current**: check off a task in `tasks.md` when its work lands. Update the spec or plan when scope or architecture changes, and record decisions in `docs/build-plan.md`.

## Commands

| Command | What it does |
|---|---|
| `make setup` / `make data` / `make model` | venv and packages; Parquet warehouse from the local mirror; fraud model and MLflow |
| `make test` | backend tests, rules mode, free |
| `cd frontend && npm run build` | type-check and build |
| `make eval` | the three case sets in rules mode (free), then `docs/evaluation.md`; also runs the transcript-PDF checks |
| `make eval-llm` | the same with Claude; costs money, ask the owner first |
| `make dev` | API on :8000 (`--reload`) and web on :5173 |
| `cd frontend && npm run check:ui` | Playwright and axe UI checks against `make dev`, in rules mode |
| `make docker` / `make docker-run` | demo subset and image; run on :8080 with the key from `.env.local` at runtime |
| `make deploy-azure` | build locally, push to the private registry, update Azure Container Apps |

## Deployment (Azure Container Apps)

- **Live**: the URL is in `README.md`. It scales to zero, so the first request after idle is slow. Names of the resource group, registry, and app are in `scripts/deploy-azure.sh`.
- **Secrets live on the container app, never in the image**:
  - `anthropic-key` is overwritten from `.env.local` on every deploy;
  - `transcript-key` is created once and kept. **Never change or delete it**: every PDF issued so far would then fail verification.
- **After a deploy**, wait until the new revision takes 100% of traffic (`az containerapp revision list`) before checking `/api/health`: the first answers can come from the old revision.
- **The in-container files are lost on scale to zero**: the handoff queue and the fingerprint register. PDFs still verify after that (`registered: false`).
- **Rollback**: earlier revisions stay listed, inactive with 0% traffic, under `az containerapp revision list --all` (without `--all` only the active one shows). Roll back with `az containerapp revision activate --revision <name>`, then send it the traffic.

## Gotchas

- **Restarting the API**: kill uvicorn by PID and start it in a separate command, with `--reload`. A chained `pkill -f uvicorn` can match its own shell. An API started without `--reload` keeps serving old routes, and a POST to a missing `/api/...` route then returns 405 from the static-file mount.
- **Sessions live in memory**: every API restart ends open chats, so sign in again.
- **Rate limits**: 30 new sessions per visitor per hour (`SESSIONS_PER_IP_HOUR`). The UI checks create more than that, so run them against an API or container started with a higher limit, or they fail at sign-in with 429 (the sign-in screen then says there were too many conversations).
- **Playwright's browser**: the checks expect a headless-shell build that may not be installed. Either run `npx playwright install chromium-headless-shell`, or point `launchOptions.executablePath` at the cached shell under `~/.cache/ms-playwright/`.
- **New frontend packages after a pull**: run `npm i` in `frontend/`, then restart Vite, which caches failed imports.
- **The renderer is pinned**: transcript PDFs must render byte for byte the same (fpdf2 `2.8.9`, pypdf `6.19.0`). Bump `RENDERER` in `backend/app/transcript/record.py` whenever the PDF layout changes.
- **Never commit a generated PDF** (the patterns `conversacion-*.pdf` and `conversa-*.pdf` are ignored) or anything under `backend/data/`.

## Non-negotiables

- **Never commit data or secrets.** The repository is public.
  - Never commit the organizers' dataset, extracts, customer rows, the S3 keys, the bucket name, API keys, or `.env`. `.gitignore` excludes `data/`, `.env*` (except `.env.example`), and data file types.
  - Before every commit, scan the staged diff with the local patterns file, which is kept outside the repository and never printed: `git diff --cached | grep -E -c -f ~/.aws/factored-datathon-scan-patterns -e "$(cat ~/.aws/factored-datathon-bucket)"`. The result must be 0.
- **Deterministic core, AI at the edges.**
  - Finding transactions, checking the outbound record, country rules, deadlines, and permissions are code.
  - The language model interprets the customer and phrases answers only from facts the tools returned.
- **Permissions in the tool layer.** The session identity decides what a tool may read. Never rely on the prompt to keep one customer's data from another.
- **Never promise a claim's outcome, never ask for codes, PINs, or passwords, and never explain a charge under a suspicious-activity report or open investigation.**
- **Label every input** as synthetic organizer data, team-generated, or synthetic policy.

## Dataset access (owner's machine)

- **Local mirror**: `~/factored-hackathon-2026-scratch/data/`, about 5 GB, all 13 tables, read-only. A duckdb venv is in `~/factored-hackathon-2026-scratch/venv/`.
- **AWS**: profile `factored-datathon`, region `us-east-2`. The bucket name is in `~/.aws/factored-datathon-bucket`; read it into a shell variable and never print it. The keys can list unrelated buckets: touch only the datathon bucket.
- **Gotchas**:
  - Categorical values are in Spanish.
  - Currencies are USD, COP, and ARS only; there is no MXN.
  - Mexico is spelled two ways ("Mexico" and "México").
  - In duckdb, `matched` and `cost` are reserved words.
- **Where the team's measured facts live**: `~/personal/factored-idea/.specify/memory/hackathon-data-profile.md`. Cite it for dataset claims.

## Collaboration

- **The owner's own work** has gone straight to `main` with their go-ahead, each commit passing tests, the build, and the secret scan.
- **Teammates' branches**: run the official secret scan on `git diff main...<branch>`, the tests, the build, and the UI checks, then merge locally with `--no-ff` when the owner says so, putting the pull request description in the merge message. The GitHub CLI is installed at `~/.local/bin/gh` but not signed in: give the compare link (`https://github.com/mastersanto/factored-hackathon-2026-problem-crushers/compare/main...<branch>`) unless the owner signs in.
- **Redeploying** changes what the judges see, so ask first.
- **Before changing course**: keep `docs/build-plan.md` current with decisions as they are made.
