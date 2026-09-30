# Explain this charge

**Team Problem Crushers**, Factored AI & Data Hackathon 2026.

An AI customer-service system for one banking workflow: **transaction-dispute intake**. A customer who does not recognize a charge, or thinks it is wrong, gets it explained from the bank's own records. The system also checks whether a "message from the bank" really came from the bank. The customer can then confirm the charge or file a complete claim, and likely fraud reaches a person with a structured handoff. The system works in Spanish and Portuguese, for customers in Mexico, Colombia, and Argentina.

> Status: build starting (2026-09-30). Submissions close 2026-10-05, midnight Colombia time.

## Documents

- [`docs/idea-brief.md`](docs/idea-brief.md): the problem, the workflow, the required cases, the metrics, and the data limits.
- [`docs/build-plan.md`](docs/build-plan.md): architecture, open team decisions, the day plan, the test cases, and the security rules.

## Data

The organizers' synthetic LATAM Bank dataset (13 tables, June 2023 to June 2026). **It is not in this repository and must never be committed.** Test conversations, Portuguese cases, and any fee schedule are team-generated or synthetic, and are labelled as such.

## Limitations, caveats, and future work

To be written as the build progresses. The data's known limits are listed in [`docs/idea-brief.md`](docs/idea-brief.md#what-the-data-cannot-do-report-these-honestly).
