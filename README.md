# 🛡️ Victor — Web Bot Fingerprint Detector

> **Victor** detects bot traffic using behavioral fingerprinting + an ensemble of Isolation Forest and XGBoost — then visualizes everything in a real-time Streamlit dashboard.

---

## 🧠 How It Works

```
Real site traffic
       │
       ▼
  [honeypot.py]  ← Flask server that logs every request with label
       │
       ▼
  [simulate_traffic.py]  ← Generates realistic bot & human sessions
       │
       ▼
  [feature_engineering.py]  ← Turns raw logs into ML features
       │
       ▼
  [train_model.py]  ← Isolation Forest + XGBoost ensemble
       │
       ▼
  [explain.py]  ← SHAP explainability charts
       │
       ▼
  [dashboard.py]  ← Streamlit live dashboard
```

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the honeypot server
```bash
python honeypot.py
```
Keep this running in a separate terminal.

### 3. Simulate traffic (bots + humans)
```bash
python simulate_traffic.py
```
Generates ~40 human sessions and ~40 bot sessions logged at `data/traffic_logs.json`.

### 4. Extract features
```bash
python feature_engineering.py
```

### 5. Train the model
```bash
python train_model.py
```
Outputs `data/predictions.csv` and `data/model_metrics.json`.

### 6. (Optional) Generate SHAP explainability
```bash
python explain.py
```

### 7. Launch the dashboard
```bash
streamlit run dashboard.py
```

---

## 📊 Features Extracted

| Feature | Description |
|---|---|
| `ua_is_suspicious` | User agent matches bot signatures (curl, scrapy, etc.) |
| `has_referer` | Request came with a Referer header |
| `has_accept_lang` | Accept-Language header was sent |
| `hit_secret_page` | Visited the hidden honeypot endpoint `/secret-data` |
| `ua_length` | Length of the user agent string |
| `time_gap_seconds` | Seconds between consecutive requests from same IP |
| `unique_pages_visited` | Distinct pages visited by this IP |
| `total_requests_from_ip` | Total request count from this IP |

---

## 🧩 Model Architecture

- **Isolation Forest** (unsupervised) — detects anomalies without labels; contributes 40% of ensemble score
- **XGBoost** (supervised) — trained on labeled data with early stopping + class-weight balancing; contributes 60%
- **Ensemble score** = `0.4 × iso_score + 0.6 × xgb_score`
- **Victor flag** = `1` if ensemble score > 0.5 (adjustable via dashboard slider)

---

## 📁 Project Structure

```
victor/
├── honeypot.py              # Flask server + request logger
├── simulate_traffic.py      # Bot & human traffic generator
├── feature_engineering.py   # Raw logs → ML features
├── train_model.py           # Isolation Forest + XGBoost training
├── explain.py               # SHAP explainability
├── dashboard.py             # Streamlit UI
├── requirements.txt         # Minimal dependencies
└── data/
    ├── traffic_logs.json    # Raw request logs (git-ignored)
    ├── features.csv         # Extracted features (git-ignored)
    ├── predictions.csv      # Model predictions (git-ignored)
    ├── model_metrics.json   # AUC / F1 / precision / recall
    └── shap/
        ├── global_summary.png
        ├── feature_bar.png
        └── shap_values.csv
```

---

## 🛡️ Dashboard Pages

| Page | Description |
|---|---|
| 📊 Dashboard | Metrics, pie chart, histogram, feature comparison |
| 🔍 Live IP Check | Enter any IP to see its full traffic profile & verdict |
| 🧠 Model Explainability | SHAP plots + feature heatmap + glossary |
| 📋 Raw Log | Full predictions table with filter + score threshold |

---

## ⚙️ Tech Stack

`Flask` · `XGBoost` · `scikit-learn` · `SHAP` · `Streamlit` · `Plotly` · `Pandas` · `Faker`

---

*Built with ❤️ — Victor knows who you are.*
