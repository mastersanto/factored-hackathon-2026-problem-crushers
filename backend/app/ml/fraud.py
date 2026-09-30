"""Fraud risk estimate for a disputed transaction: the learned component.

Question it answers for the workflow: "does this charge look like fraud?" The answer only
changes the handoff's priority and adds a statement marked as an estimate. It never decides a claim.

Findings that shaped it (docs/model-card.md):
- The label `is_fraud` is random with respect to every behavioural feature in this synthetic data
  (amount, amount vs the customer's usual, velocity, new merchant, hour, channel, country).
- The dataset's `fraud_score` (the bank's existing detector, available at transaction time) separates
  about half of the frauds perfectly (score >= 50: 100% fraud) and the 30-50 band is 54% fraud;
  the rest of the frauds sit in the low band or have no score, indistinguishable from normal traffic.

So the candidates are compared on a time split, against the fixed rule `fraud_score >= 50`:
  rule_score_ge_50        the baseline
  behaviour_only_hgb      gradient boosting on behavioural features only (ablation: is there signal?)
  score_isotonic          isotonic calibration of the score (+ a missing-score flag)
  score_plus_behaviour    gradient boosting on the score and behavioural features
Validation picks the model and the alert threshold (precision >= 0.9); test reports once.

Usage:  python -m app.ml.fraud      (writes backend/data/models/fraud.joblib and logs to MLflow)
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import duckdb
import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import average_precision_score, precision_recall_curve

from app.config import BACKEND_DIR, settings

MODEL_PATH = BACKEND_DIR / "data" / "models" / "fraud.joblib"
REPORT_PATH = BACKEND_DIR / "data" / "models" / "fraud_report.json"
TRAIN_END, VALID_END = "2025-10-01", "2026-02-01"  # train < 2025-10 <= valid < 2026-02 <= test
NEG_SAMPLE = 0.05  # train on 5% of legitimate transactions (reweighted), all frauds
TARGET_PRECISION = 0.90
SEED = 42

BEHAVIOUR = ["log_amount_usd", "amount_ratio", "tx_24h", "new_merchant", "log_mins_since_prev", "hour", "weekday",
             "abroad", "type_code", "channel_code", "category_code", "product_code"]
SCORE = ["score", "score_missing"]

FEATURES_SQL = """
WITH base AS (
  SELECT t.transaction_id, t.transaction_date, t.is_fraud::int AS y, t.fraud_score, t.amount_usd,
         t.transaction_type, t.channel, coalesce(t.transaction_category, 'none') AS category, t.merchant_name,
         p.product_type, (t.transaction_country <> c.country) AS abroad, t.customer_id
  FROM '{w}/transactions.parquet' t
  JOIN '{w}/products.parquet' p USING (product_id)
  JOIN '{w}/customers.parquet' c ON c.customer_id = t.customer_id
)
SELECT transaction_id, transaction_date, y,
  coalesce(fraud_score, -1) AS score, (fraud_score IS NULL)::int AS score_missing,
  ln(1 + greatest(amount_usd, 0)) AS log_amount_usd,
  coalesce(amount_usd / nullif(avg(amount_usd) OVER w50, 0), -1) AS amount_ratio,
  count(*) OVER (PARTITION BY customer_id ORDER BY transaction_date RANGE BETWEEN INTERVAL 1 DAY PRECEDING AND CURRENT ROW) - 1 AS tx_24h,
  CASE WHEN merchant_name IS NULL THEN -1
       WHEN count(*) OVER (PARTITION BY customer_id, merchant_name ORDER BY transaction_date ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) = 0 THEN 1 ELSE 0 END AS new_merchant,
  ln(1 + coalesce(date_diff('minute', lag(transaction_date) OVER (PARTITION BY customer_id ORDER BY transaction_date), transaction_date), 1e6)) AS log_mins_since_prev,
  hour(transaction_date) AS hour, dayofweek(transaction_date) AS weekday, abroad::int AS abroad,
  dense_rank() OVER (ORDER BY transaction_type) AS type_code, dense_rank() OVER (ORDER BY channel) AS channel_code,
  dense_rank() OVER (ORDER BY category) AS category_code, dense_rank() OVER (ORDER BY product_type) AS product_code
FROM base
WINDOW w50 AS (PARTITION BY customer_id ORDER BY transaction_date ROWS BETWEEN 50 PRECEDING AND 1 PRECEDING)
"""


def load_frames(warehouse: Path = settings.warehouse_dir):
    con = duckdb.connect()
    con.sql(f"CREATE TEMP TABLE f AS {FEATURES_SQL.format(w=warehouse)}")
    con.sql(f"SELECT setseed({SEED / 100})")
    cols = ["y", *SCORE, *BEHAVIOUR]
    train = con.sql(f"SELECT {', '.join(cols)} FROM f WHERE transaction_date < '{TRAIN_END}' AND (y = 1 OR random() < {NEG_SAMPLE})").fetchnumpy()
    valid = con.sql(f"SELECT {', '.join(cols)} FROM f WHERE transaction_date >= '{TRAIN_END}' AND transaction_date < '{VALID_END}'").fetchnumpy()
    test = con.sql(f"SELECT {', '.join(cols)} FROM f WHERE transaction_date >= '{VALID_END}'").fetchnumpy()
    return train, valid, test


def X(frame, cols):
    return np.column_stack([np.asarray(frame[c], dtype=float) for c in cols])


class ScoreIsotonic:
    """Isotonic calibration of the existing score; a missing score maps to the base fraud rate."""

    def fit(self, frame, weight):
        s, m, y = np.asarray(frame["score"], float), np.asarray(frame["score_missing"]) == 1, np.asarray(frame["y"])
        self.iso = IsotonicRegression(out_of_bounds="clip").fit(s[~m], y[~m], sample_weight=weight[~m])
        self.missing_rate = float(np.average(y[m], weights=weight[m])) if m.any() else 0.0
        return self

    def predict(self, frame):
        s, m = np.asarray(frame["score"], float), np.asarray(frame["score_missing"]) == 1
        p = self.iso.predict(np.where(m, 0, s))
        return np.where(m, self.missing_rate, p)


def threshold_for_precision(y, p, target=TARGET_PRECISION):
    prec, rec, thr = precision_recall_curve(y, p)
    ok = np.where(prec[:-1] >= target)[0]
    return float(thr[ok[np.argmax(rec[ok])]]) if len(ok) else float(thr[-1])


def at_threshold(y, p, t):
    alert = p >= t
    tp = int((alert & (y == 1)).sum())
    return {"alerts": int(alert.sum()), "true_positives": tp, "frauds": int(y.sum()),
            "precision": round(tp / max(alert.sum(), 1), 4), "recall": round(tp / max(y.sum(), 1), 4)}


def train() -> dict:
    import mlflow

    t0 = time.time()
    train_f, valid_f, test_f = load_frames()
    ytr, yva, yte = (np.asarray(f["y"]) for f in (train_f, valid_f, test_f))
    w = np.where(ytr == 1, 1.0, 1.0 / NEG_SAMPLE)

    candidates = {}
    candidates["behaviour_only_hgb"] = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, random_state=SEED).fit(X(train_f, BEHAVIOUR), ytr, sample_weight=w)
    candidates["score_isotonic"] = ScoreIsotonic().fit(train_f, w)
    candidates["score_plus_behaviour"] = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, random_state=SEED).fit(X(train_f, SCORE + BEHAVIOUR), ytr, sample_weight=w)

    def predict(name, frame):
        m = candidates[name]
        if name == "score_isotonic":
            return m.predict(frame)
        cols = BEHAVIOUR if name == "behaviour_only_hgb" else SCORE + BEHAVIOUR
        return m.predict_proba(X(frame, cols))[:, 1]

    rule = lambda frame: (np.asarray(frame["score"], float) >= 50).astype(float)  # noqa: E731
    report = {"split": {"train_end": TRAIN_END, "valid_end": VALID_END, "neg_sample": NEG_SAMPLE,
                        "rows": {"train_sampled": len(ytr), "valid": len(yva), "test": len(yte)},
                        "frauds": {"train": int(ytr.sum()), "valid": int(yva.sum()), "test": int(yte.sum())}},
              "base_rate_test": round(float(yte.mean()), 6), "models": {}}
    report["models"]["rule_score_ge_50"] = {"valid_pr_auc": round(average_precision_score(yva, rule(valid_f)), 4),
                                            "test_pr_auc": round(average_precision_score(yte, rule(test_f)), 4),
                                            "threshold": 1.0, "test_at_threshold": at_threshold(yte, rule(test_f), 1.0)}
    for name in candidates:
        pva, pte = predict(name, valid_f), predict(name, test_f)
        thr = threshold_for_precision(yva, pva)
        report["models"][name] = {"valid_pr_auc": round(average_precision_score(yva, pva), 4),
                                  "test_pr_auc": round(average_precision_score(yte, pte), 4),
                                  "threshold": round(thr, 6), "valid_at_threshold": at_threshold(yva, pva, thr),
                                  "test_at_threshold": at_threshold(yte, pte, thr)}

    # Choose on validation only; prefer the simpler model when PR-AUC is within 0.01 (Occam).
    order = ["score_isotonic", "score_plus_behaviour", "behaviour_only_hgb"]
    best = max(order, key=lambda n: (round(report["models"][n]["valid_pr_auc"], 2), -order.index(n)))
    report["chosen"] = best
    report["train_seconds"] = round(time.time() - t0, 1)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"name": best, "model": candidates[best], "threshold": report["models"][best]["threshold"],
                 "features": SCORE if best == "score_isotonic" else (SCORE + BEHAVIOUR)}, MODEL_PATH)
    REPORT_PATH.write_text(json.dumps(report, indent=2))

    mlflow.set_tracking_uri(f"sqlite:///{BACKEND_DIR / 'data' / 'mlflow.db'}")
    if mlflow.get_experiment_by_name("fraud-risk") is None:
        mlflow.create_experiment("fraud-risk", artifact_location=(BACKEND_DIR / "data" / "mlartifacts").as_uri())
    mlflow.set_experiment("fraud-risk")
    for name, r in report["models"].items():
        with mlflow.start_run(run_name=name):
            mlflow.log_params({"model": name, "train_end": TRAIN_END, "valid_end": VALID_END, "neg_sample": NEG_SAMPLE,
                               "target_precision": TARGET_PRECISION, "chosen": name == best})
            mlflow.log_metrics({"valid_pr_auc": r["valid_pr_auc"], "test_pr_auc": r["test_pr_auc"],
                                "test_precision": r["test_at_threshold"]["precision"], "test_recall": r["test_at_threshold"]["recall"]})
            if name == best:
                mlflow.log_artifact(str(MODEL_PATH))
                mlflow.log_artifact(str(REPORT_PATH))
    return report


class FraudRisk:
    """Inference for the workflow. Only the score features are needed for the chosen model."""

    def __init__(self, path: Path = MODEL_PATH):
        bundle = joblib.load(path)
        self.name, self.model, self.threshold = bundle["name"], bundle["model"], bundle["threshold"]
        if self.name != "score_isotonic":
            raise RuntimeError(f"inference for {self.name} needs the full feature pipeline; retrain or extend FraudRisk")

    def estimate(self, fraud_score: float | None) -> tuple[float, bool]:
        frame = {"score": np.array([-1.0 if fraud_score is None else fraud_score]),
                 "score_missing": np.array([1 if fraud_score is None else 0])}
        p = float(self.model.predict(frame)[0])
        return p, p >= self.threshold


def load_fraud_risk() -> FraudRisk | None:
    try:
        return FraudRisk() if MODEL_PATH.exists() else None
    except Exception:
        return None


if __name__ == "__main__":
    # Import under the package name so pickled classes load as app.ml.fraud.*, not __main__.*
    from app.ml import fraud as _fraud

    print(json.dumps(_fraud.train(), indent=2))
