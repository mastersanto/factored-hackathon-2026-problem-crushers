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
- **Feature `specs/001-dispute-intake-assistant/`** holds:
  - `spec.md`: what is built and what remains;
  - `plan.md`: the architecture as built;
  - `research.md`: decisions and alternatives;
  - `data-model.md`, `contracts/http-api.md`, and `quickstart.md`;
  - `tasks.md`: T001-T019 done, T020-T044 remaining until submission.
- **Keeping tasks current**: check off a task in `tasks.md` when its work lands. Update the spec or plan when scope or architecture changes.

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

- **Branches and pull requests**: branch per feature and open a pull request to `main`. The owner opens pull requests and creates the GitHub repository themselves, so push branches and give the compare link.
- **Before changing course**: keep `docs/build-plan.md` current with decisions as they are made.
