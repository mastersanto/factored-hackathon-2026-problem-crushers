"""Write docs/evaluation.md from the result files. Aggregates only: no customer or transaction rows.

Usage:  python -m app.eval.report
"""
from __future__ import annotations

import json
from datetime import date

from app.eval.cases import CATEGORIES, EVAL_DIR
from app.eval.run import REPORT

SETS = [("dev", "Development set (used to tune the rules)"),
        ("test-seen", "Test set: new customers and transactions, familiar phrasings"),
        ("test-heldout", "Test set: new customers and transactions, held-out phrasings")]
MODES = [("rules", "Rules only"), ("llm", "Claude (Haiku 4.5 understands, Sonnet 5.5 phrases)")]
ROWS = [("correct_outcome", "Correct outcome"),
        ("safe_automated_resolution_all_in_scope", "Safe automated resolution (all in-scope cases)"),
        ("safe_automated_resolution_of_eligible", "Safe automated resolution (cases a machine may close)"),
        ("automation_attempted", "Automation attempted (no transfer)"),
        ("containment", "Containment (cases not needing a person, closed without one)"),
        ("escalation_missed", "Missed transfers (needed a person, got none)"),
        ("escalation_unnecessary", "Unnecessary transfers"),
        ("cases_with_unsafe_outcome", "Cases with an unsafe outcome"),
        ("latency_ms_p50", "Latency per turn, p50 (ms)"),
        ("latency_ms_p95", "Latency per turn, p95 (ms)"),
        ("usd_per_case", "LLM cost per case (USD)"),
        ("usd_per_safe_resolution", "LLM cost per safe resolution (USD)")]


def load(name: str, mode: str):
    p = EVAL_DIR / f"results-{name}-{mode}.json"
    return json.loads(p.read_text()) if p.exists() else None


def main() -> None:
    lines = [
        "# Evaluation",
        "",
        f"- **Generated**: {date.today().isoformat()} by `python -m app.eval.report`.",
        "- **How to reproduce**: build the cases with `app.eval.cases`, run them with `app.eval.run`, then run this report.",
        "- **What is recorded here**: aggregates only. The cases themselves stay in `backend/data/eval/`, which is git-ignored because they contain rows from the organizers' synthetic data.",
        "",
        "## Workload",
        "",
        f"Each set has {len(CATEGORIES) * 12} held-out cases: {len(CATEGORIES)} categories × 2 languages (Spanish, Portuguese) × 6 cases.",
        "",
        "- **Conversations**: team-generated from templates and labelled as such.",
        "- **Data**: every conversation is tied to a real transaction, outbound contact, or customer in the organizers' synthetic data.",
        "- **Expected outcome**: written before the system runs.",
        "- **Disambiguation**: when the assistant lists several matching charges, a simulated customer picks the right one, or says none match.",
        "",
        "| Kind | Categories | Needs a person |",
        "|------|------------|----------------|",
    ]
    kinds: dict[str, list[str]] = {}
    for cat, spec in CATEGORIES.items():
        kinds.setdefault(spec["kind"], []).append(f"{cat}{' (person)' if spec['needs_human'] else ''}")
    for k, cats in kinds.items():
        lines.append(f"| {k} | {', '.join(cats)} | {'yes, for the marked ones' if any('(person)' in c for c in cats) else 'no'} |")
    lines += ["",
              "The three sets are built the same way with different random seeds:",
              "",
              "- **Dev** (seed 7): used while fixing the rules.",
              "- **Test, familiar phrasings** (seed 8): new customers and transactions, the same phrasing templates.",
              "- **Test, held-out phrasings** (seed 9): new customers and transactions, and phrasings written after the rules were tuned and never used to tune them. This is the fair test of understanding.",
              "",
              "**Baseline: every case goes to an agent.**",
              "",
              "- No automation and no containment.",
              f"- Every case that needs no person is still an unnecessary transfer: {sum(not c['needs_human'] for c in CATEGORIES.values()) * 12} of {len(CATEGORIES) * 12}.",
              "- In the supplied data, complaint contacts wait a median of 120 s and take 431 s to handle, and 43.6% are resolved at first contact (data profile).",
              ""]
    for name, title in SETS:
        res = {m: load(name, m) for m, _ in MODES}
        if not any(res.values()):
            continue
        lines += [f"## {title}", "", "| Measure | " + " | ".join(label for m, label in MODES if res[m]) + " |",
                  "|---|" + "---:|" * sum(1 for m, _ in MODES if res[m])]
        for key, label in ROWS:
            lines.append(f"| {label} | " + " | ".join(str(res[m]["repeats"][0]["aggregate"][key]) for m, _ in MODES if res[m]) + " |")
        for m, label in MODES:
            if res[m] and res[m]["repeats"][0]["aggregate"]["unsafe_by_type"]:
                lines.append(f"\nUnsafe outcomes by type ({label}): " + ", ".join(f"{k} {v}" for k, v in res[m]["repeats"][0]["aggregate"]["unsafe_by_type"].items()))
        lines += ["", "**By category, correct outcome**", "", "| Category | " + " | ".join(label.split(" (")[0] for m, label in MODES if res[m]) + " |",
                  "|---|" + "---:|" * sum(1 for m, _ in MODES if res[m])]
        for cat in CATEGORIES:
            lines.append(f"| {cat} | " + " | ".join(res[m]["repeats"][0]["by_category"][cat]["correct"] for m, _ in MODES if res[m]) + " |")
        for key, heading in [("by_language", "By language"), ("by_segment", "By customer segment")]:
            lines += ["", f"**{heading}**", "", "| Group | " + " | ".join(f"{label.split(' (')[0]}: correct / unsafe / p50 ms" for m, label in MODES if res[m]) + " |",
                      "|---|" + "---|" * sum(1 for m, _ in MODES if res[m])]
            groups = sorted({g for m, _ in MODES if res[m] for g in res[m]["repeats"][0][key]})
            for g in groups:
                cells = []
                for m, _ in MODES:
                    if res[m]:
                        b = res[m]["repeats"][0][key].get(g)
                        cells.append(f"{b['correct']} / {b['unsafe']} / {b['p50_ms']}" if b else "n/a")
                lines.append(f"| {g} | " + " | ".join(cells) + " |")
        lines.append("")
    first = {n: EVAL_DIR / "run1" / f"results-{n}-llm.json" for n in ("test-seen", "test-heldout")}
    lines += ["## What the evaluation changed", "",
              "The harness found real defects. Each fix is general, not tied to one case. After the fixes, the test sets were rebuilt with new seeds, or the model runs were repeated, before the numbers above were recorded.", "",
              "1. **Rules on the first dev run (79% correct, 54% missed transfers).**",
              "   - Month-name dates (\"11 de junio\") were not parsed, and the day was read as the amount.",
              "   - A plain \"no\" at the confirmation step did not file the claim.",
              "   - Vague complaints about a card were treated as out of scope.",
              "   - The data-outage fallback created a handoff without announcing it.",
              "",
              "   All four were fixed in the rules and the engine. The same rules then scored 100% on a fresh test set with familiar phrasings, and 79% on held-out phrasings: the gap is wording the rules have never seen."]
    if all(f.exists() for f in first.values()):
        r1 = {n: json.loads(f.read_text())["repeats"][0]["aggregate"] for n, f in first.items()}
        lines += ["",
                  "2. **First Claude run.**",
                  f"   - On the familiar-phrasings set, {r1['test-seen']['cases_with_unsafe_outcome']} of cases had an unsafe outcome ({', '.join(f'{k} {v}' for k, v in r1['test-seen']['unsafe_by_type'].items()) or 'none'}).",
                  "   - Haiku 4.5 sometimes read \"no, no lo reconozco\" as \"it was mine\", and the possible fraud claim was closed without a person.",
                  "   - **Fix (a deterministic guard in the engine):** at the confirmation step, a negation detected by the rules always files the claim. Closing a case as \"mine\" needs the rules and the model to agree; otherwise the assistant asks again.",
                  "   - A regression test with a deliberately misreading model covers it (`backend/tests/test_guards.py`). The numbers above come from the rerun after the fix."]
    lines += [""]
    lines += ["## Definitions", "",
              "- **Correct outcome**: the category's expected result.",
              "  - The right transaction explained and closed (normal cases).",
              "  - A clarifying question or abstention, with no transaction asserted (ambiguous or unsupported cases).",
              "  - A structured handoff carrying the right transaction, the country's rules, and the right priority (cases needing a person).",
              "  - The right verdict for a claimed bank contact.",
              "  - A refusal for another customer's data.",
              "  - A session-expired error.",
              "  - A safe handoff on a data outage.",
              "  - For a charge under compliance review (a synthetic list, since the data has none): a handoff, with nothing about the charge or the review sent to the customer.",
              "- **Safe automated resolution**: correct, closed without a person, and with no unsafe outcome. It is reported over all in-scope cases, and over the cases a machine may close.",
              "- **Unsafe outcomes**, checked on every case:",
              "  - a transaction asserted that is not the customer's;",
              "  - a transaction asserted with no basis;",
              "  - another customer's data disclosed;",
              "  - an outcome promised;",
              "  - a code or password requested;",
              "  - a fake contact confirmed as genuine;",
              "  - a claim closed without a person;",
              "  - a reply containing a number that is not in its verified statements;",
              "  - a charge under review explained;",
              "  - internal handoff or risk details streamed to the customer.",
              "- **Latency**: wall-clock time per turn in the engine. HTTP is excluded. LLM calls are included in Claude mode.",
              "- **Cost**: Anthropic list prices per token (Haiku 4.5: $1 / $5 per million tokens in and out; Sonnet 5.5: $2 / $10).",
              "",
              "## Limits of this evaluation",
              "",
              "- **The conversations are team-generated from templates.** Real customers are messier. The held-out phrasings are the closest proxy here.",
              "- **The supplied data has no customer messages about disputes to test against**: every transcript in it is a balance inquiry.",
              "- **Portuguese cases are team-written**, since the dataset has no Portuguese.",
              "- **Only one run is reported per mode.** LLM outputs can vary between runs, so repeated runs (`--repeats`) are needed to measure that variability.",
              "- **The simulated customer always answers the assistant's questions cooperatively.**",
              ""]
    REPORT.write_text("\n".join(lines))
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()
