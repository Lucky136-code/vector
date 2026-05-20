# train_model.py
# fixed version — handles edge cases like single-class labels
# and removes the deprecated use_label_encoder argument

import pandas as pd
import numpy as np
import joblib
import os
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
from xgboost import XGBClassifier

# ─────────────────────────────────────────────
# STEP 1 — load features
# ─────────────────────────────────────────────

df = pd.read_csv("data/features.csv")

FEATURE_COLS = [
    "ua_is_suspicious",
    "has_referer",
    "has_accept_lang",
    "hit_secret_page",
    "ua_length",
    "time_gap_seconds",
    "unique_pages_visited",
    "total_requests_from_ip"
]

X = df[FEATURE_COLS]
y = df["label"]

print(f"Dataset: {len(df)} rows | Bots: {y.sum()} | Humans: {(y==0).sum()}")

# safety check — we need both classes to train properly
if y.nunique() < 2:
    print("\nERROR: Only one class found in labels.")
    print("This means the logs weren't labeled correctly.")
    print("Please delete data/traffic_logs.json and re-run:")
    print("  1. python honeypot.py")
    print("  2. python simulate_traffic.py")
    print("  3. python feature_engineering.py")
    print("  4. python train_model.py")
    exit()


# ─────────────────────────────────────────────
# STEP 2 — Isolation Forest (unsupervised)
# ─────────────────────────────────────────────

# estimate contamination from our actual data
# this tells the model roughly how many anomalies to expect
contamination_rate = round(float(y.mean()), 2)
contamination_rate = max(0.05, min(contamination_rate, 0.45))  # keep it in valid range

iso_forest = IsolationForest(
    n_estimators  = 200,
    contamination = contamination_rate,
    random_state  = 42
)

iso_forest.fit(X)

iso_preds      = iso_forest.predict(X)
iso_preds_bin  = (iso_preds == -1).astype(int)   # -1 means anomaly → bot

# normalize scores to 0–1 range
iso_raw    = iso_forest.decision_function(X)
iso_scores = 1 - (iso_raw - iso_raw.min()) / (iso_raw.max() - iso_raw.min())

print("\n--- Isolation Forest Results ---")
print(classification_report(y, iso_preds_bin, target_names=["Human", "Bot"], zero_division=0))
print(f"ROC-AUC: {roc_auc_score(y, iso_scores):.3f}")


# ─────────────────────────────────────────────
# STEP 3 — XGBoost (supervised)
# ─────────────────────────────────────────────

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)

xgb_model = XGBClassifier(
    n_estimators  = 200,
    max_depth     = 4,
    learning_rate = 0.1,
    eval_metric   = "logloss",   # no use_label_encoder — removed in newer XGBoost
    random_state  = 42
)

xgb_model.fit(X_train, y_train)

xgb_preds  = xgb_model.predict(X_test)
xgb_scores_test = xgb_model.predict_proba(X_test)[:, 1]

print("\n--- XGBoost Results ---")
print(classification_report(y_test, xgb_preds, target_names=["Human", "Bot"], zero_division=0))
print(f"ROC-AUC: {roc_auc_score(y_test, xgb_scores_test):.3f}")


# ─────────────────────────────────────────────
# STEP 4 — ensemble: combine both scores
# ─────────────────────────────────────────────

xgb_scores_full = xgb_model.predict_proba(X)[:, 1]
ensemble_score  = (iso_scores + xgb_scores_full) / 2

df["iso_score"]      = iso_scores
df["xgb_score"]      = xgb_scores_full
df["ensemble_score"] = ensemble_score
df["victor_flag"]    = (ensemble_score > 0.5).astype(int)

df.to_csv("data/predictions.csv", index=False)
print("\nPredictions saved to data/predictions.csv")

total   = len(df)
flagged = df["victor_flag"].sum()
print(f"Victor Summary: {flagged}/{total} requests flagged as bots ({flagged/total*100:.1f}%)")


# ─────────────────────────────────────────────
# STEP 5 — save models
# ─────────────────────────────────────────────

os.makedirs("models", exist_ok=True)
joblib.dump(iso_forest, "models/isolation_forest.pkl")
joblib.dump(xgb_model,  "models/xgboost_model.pkl")
print("Models saved to models/")