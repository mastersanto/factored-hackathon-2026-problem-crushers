# Model card: fraud risk estimate

- **Code**: `backend/app/ml/fraud.py` (training, evaluation, inference).
- **Run**: `python -m app.ml.fraud` from `backend/`. It writes the model and report to `backend/data/models/` (git-ignored) and logs every candidate to MLflow (`backend/data/mlflow.db`).
- **Trained**: 2026-09-30, about 8 seconds on the full warehouse.

## What it is for

When a customer disputes a charge, the workflow asks: *does this charge look like fraud?* The answer changes only two things:

- **Priority.** A flagged charge's handoff goes to a person as high priority.
- **One statement.** The customer sees one sentence marked as an **estimate** ("tiene rasgos que suelen verse en fraudes").

It never decides a claim, refunds anything, or blocks a card.

## Data and labels

- **Data**: the organizers' synthetic LATAM Bank transactions, June 2023 to June 2026, 4,425,008 rows.
- **Label**: `is_fraud`, 4,316 positives (0.098%). It is the only valid fraud label in the supplied data.
- **Time split** (no shuffling; the model never sees the future):

| Set | Period | Rows | Frauds |
|-----|--------|-----:|-------:|
| Train | before 2025-10-01 | 171,581 (all frauds plus 5% of legitimate rows, reweighted) | 3,370 |
| Validation | 2025-10-01 to 2026-01-31 | 494,387 (all) | 452 |
| Test | 2026-02-01 onward | 564,540 (all) | 494 |

- **Features**: computed only from information available when the transaction happens.
  - The **existing detector score** (`fraud_score`), plus a flag for when it is missing (20% of rows).
  - **Behavioural features**:
    - amount in USD (log);
    - amount relative to the customer's previous 50 transactions;
    - transactions in the prior 24 hours;
    - first purchase at this merchant;
    - minutes since the previous transaction;
    - hour and weekday;
    - abroad;
    - transaction type, channel, category, and product type.

## What we found first

- **The label is random with respect to every behavioural feature.** Fraud stays at about 0.1% across:
  - every amount decile;
  - amount relative to the customer's usual spend;
  - 24-hour velocity;
  - new versus known merchant;
  - time since the previous transaction;
  - hour, channel, type, status, and country.

  This is a property of the synthetic data (`~/personal/factored-idea/.specify/memory/hackathon-data-profile.md`).
- **The detector score is the only signal, and it is sharp.**
  - Every legitimate transaction scores 30 or below.
  - 2,373 of the 4,316 frauds (55%) score above 30.
  - The remaining frauds score 30 or below, or have no score, and are indistinguishable from normal traffic.

## Candidates and results

- **Selection**: on validation, maximum precision-recall area. When two candidates are within 0.01, the simpler one wins.
- **Threshold**: the highest recall at a precision of at least 90%, chosen on validation.
- **Test**: reported once.

| Candidate | Validation PR-AUC | Test PR-AUC | Test alerts | Frauds caught (of 494) | Precision |
|-----------|------------------:|------------:|------------:|-----------------------:|----------:|
| Baseline: `fraud_score >= 50` (fixed rule) | 0.403 | 0.416 | 205 | 205 (41.5%) | 100% |
| Behavioural features only (gradient boosting, ablation) | 0.001 | 0.001 | 1 | 0 | – |
| Score plus behavioural features (gradient boosting) | 0.420 | 0.421 | 257 | 214 (43.3%) | 83% |
| **Calibrated score (isotonic regression), chosen** | **0.576** | **0.570** | **281** | **281 (56.9%)** | **100%** |

What the table shows:

- **The chosen model catches 37% more frauds than the fixed rule** (281 against 205 on the held-out months), with no false alarms.
- **The behavioural ablation performs at chance.** A PR-AUC of 0.001 equals the base rate of 0.000875, which confirms there is no behavioural signal.
- **Adding behavioural features to the score makes it worse**: the model fits noise.

## How to read this honestly

- **What the model learned.** The calibration learned a boundary at a score of about 30, where the synthetic data generator separates legitimate transactions from half of the frauds.
  - **In a real bank**, the same method (calibrating the bank's existing detector on labelled outcomes and setting the threshold on held-out data) is a standard, defensible step.
  - **Here**, it mostly shows that the fixed threshold of 50 was set too high for this detector.
- **Possible leakage.** The score may have been generated from the label. The deployed estimate treats it as the bank's detector output, available at authorization time, and does not use the label in any other way.
- **What it cannot catch.** 43% of the test frauds are invisible to every model here: low or missing score, and no behavioural signal. The workflow does not rely on the estimate. A customer who says "no fui yo" is always taken seriously, and the claim reaches a person whatever the estimate says.
- **What is not measured.** Fairness by segment, country, or accent is not measured yet. The estimate uses no customer attributes, only the transaction's score.

## Tracking and reproducibility

- **MLflow experiment `fraud-risk`**: one run per candidate, holding parameters, validation and test metrics, and the chosen model plus its report as artifacts.
- **Determinism**: the negative sample uses a fixed seed (`SEED = 42`), and the split dates are constants in the code.
- **To view the runs**: `mlflow ui --backend-store-uri sqlite:///backend/data/mlflow.db`
