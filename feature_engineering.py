# feature_engineering.py
# we take the raw JSON logs and turn them into numbers
# because ML models only understand numbers, not strings like "Mozilla/5.0..."

import json
import pandas as pd
import numpy as np
from datetime import datetime

LOG_FILE = "data/traffic_logs.json"

# ─────────────────────────────────────────────
# STEP 1 — load the raw logs
# ─────────────────────────────────────────────

def load_logs():
    with open(LOG_FILE, "r") as f:
        logs = json.load(f)

    df = pd.DataFrame(logs)

    # convert timestamp string into an actual datetime object
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # sort by time so session analysis makes sense
    df = df.sort_values("timestamp").reset_index(drop=True)

    print(f"Loaded {len(df)} log entries.")
    return df


# ─────────────────────────────────────────────
# STEP 2 — extract features from each row
# ─────────────────────────────────────────────

def extract_features(df):

    features = pd.DataFrame()

    # --- feature 1: is the user agent suspicious? ---
    # real browsers have long, detailed user agents
    # bots often use short ones like "python-requests/2.28"
    BOT_KEYWORDS = ["python", "scrapy", "curl", "go-http", "wget", "bot", "crawl", "spider"]

    features["ua_is_suspicious"] = df["user_agent"].str.lower().apply(
        lambda ua: 1 if any(kw in ua for kw in BOT_KEYWORDS) else 0
    )

    # --- feature 2: does it have a referer? ---
    # humans usually come from somewhere (google, social, etc.)
    # bots often just hit URLs directly with no referer
    features["has_referer"] = df["referer"].apply(
        lambda r: 0 if r == "none" else 1
    )

    # --- feature 3: does it have an accept-language header? ---
    # real browsers always send this — bots often skip it
    features["has_accept_lang"] = df["accept_lang"].apply(
        lambda a: 0 if a == "none" else 1
    )

    # --- feature 4: did it hit the secret honeypot page? ---
    # only bots (or very curious people) find /secret-data
    features["hit_secret_page"] = df["path"].apply(
        lambda p: 1 if "secret" in p else 0
    )

    # --- feature 5: user agent length ---
    # bots tend to have very short or very generic user agents
    features["ua_length"] = df["user_agent"].str.len()

    # --- feature 6: time gap between requests from same IP ---
    # bots move fast — near-zero gaps between requests
    # humans pause and read — 2 to 10 seconds between clicks
    df["time_gap"] = df.groupby("ip")["timestamp"].diff().dt.total_seconds().fillna(5)
    features["time_gap_seconds"] = df["time_gap"]

    # --- feature 7: how many unique pages did this IP visit? ---
    # bots usually visit many unique pages quickly
    page_counts = df.groupby("ip")["path"].nunique()
    features["unique_pages_visited"] = df["ip"].map(page_counts)

    # --- feature 8: total requests from this IP ---
    # bots rack up a high request count in short time
    request_counts = df.groupby("ip")["path"].count()
    features["total_requests_from_ip"] = df["ip"].map(request_counts)

    # keep the label so we can evaluate later
    features["label"] = df["label"].values

    # preserve raw metadata columns for realistic dashboard lookups
    features["ip"] = df["ip"].values
    features["timestamp"] = df["timestamp"].values
    features["user_agent"] = df["user_agent"].values
    features["path"] = df["path"].values

    print(f"Extracted {features.shape[1]-5} features (plus 4 metadata columns) from {len(features)} entries.")
    return features


# ─────────────────────────────────────────────
# STEP 3 — save features to CSV
# ─────────────────────────────────────────────

def save_features(features):
    features.to_csv("data/features.csv", index=False)
    print("Saved to data/features.csv")


if __name__ == "__main__":
    df       = load_logs()
    features = extract_features(df)
    save_features(features)

    # quick preview
    print("\nSample of extracted features:")
    print(features.head(10).to_string())

    print("\nBot vs Human label counts:")
    print(features["label"].value_counts())