# dashboard.py
# this is Victor's live dashboard — built with Streamlit
# run it with: streamlit run dashboard.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# ─────────────────────────────────────────────
# page config — must be the very first streamlit call
# ─────────────────────────────────────────────

st.set_page_config(
    page_title = "Victor — Bot Detector",
    page_icon  = "🔍",
    layout     = "wide"
)

# ─────────────────────────────────────────────
# load data
# ─────────────────────────────────────────────

@st.cache_data
def load_data():
    preds    = pd.read_csv("data/predictions.csv")
    features = pd.read_csv("data/features.csv")
    return preds, features

preds, features = load_data()

# ─────────────────────────────────────────────
# header
# ─────────────────────────────────────────────

st.title("🔍 Victor — Web Scraping Fingerprint Detector")
st.markdown("Detects bot traffic using behavioral fingerprinting + ensemble ML.")
st.divider()

# ─────────────────────────────────────────────
# top metrics row
# ─────────────────────────────────────────────

total         = len(preds)
flagged_bots  = int(preds["victor_flag"].sum())
clean_humans  = total - flagged_bots
avg_bot_score = round(preds["ensemble_score"].mean(), 3)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Requests",    total)
col2.metric("Flagged as Bots",   flagged_bots,  delta=f"{flagged_bots/total*100:.1f}%")
col3.metric("Clean (Human)",     clean_humans,  delta=f"{clean_humans/total*100:.1f}%")
col4.metric("Avg Bot Score",     avg_bot_score)

st.divider()

# ─────────────────────────────────────────────
# two column layout for charts
# ─────────────────────────────────────────────

left, right = st.columns(2)

# --- pie chart: bot vs human split ---
with left:
    st.subheader("Traffic Breakdown")

    pie_data = pd.DataFrame({
        "Type"  : ["Bot", "Human"],
        "Count" : [flagged_bots, clean_humans]
    })

    fig_pie = px.pie(
        pie_data,
        names  = "Type",
        values = "Count",
        color  = "Type",
        color_discrete_map = {"Bot": "#ef4444", "Human": "#22c55e"},
        hole   = 0.4
    )
    fig_pie.update_layout(margin=dict(t=20, b=20))
    st.plotly_chart(fig_pie, use_container_width=True)

# --- histogram: ensemble score distribution ---
with right:
    st.subheader("Bot Confidence Score Distribution")

    fig_hist = px.histogram(
        preds,
        x         = "ensemble_score",
        nbins     = 30,
        color_discrete_sequence = ["#6366f1"],
        labels    = {"ensemble_score": "Bot Probability (0=Human, 1=Bot)"}
    )
    fig_hist.add_vline(
        x          = 0.5,
        line_dash  = "dash",
        line_color = "red",
        annotation_text = "Decision boundary"
    )
    fig_hist.update_layout(margin=dict(t=20, b=20))
    st.plotly_chart(fig_hist, use_container_width=True)

st.divider()

# ─────────────────────────────────────────────
# feature comparison: bots vs humans
# ─────────────────────────────────────────────

st.subheader("Feature Comparison — Bots vs Humans")

FEATURE_COLS = [
    "ua_is_suspicious", "has_referer", "has_accept_lang",
    "hit_secret_page",  "ua_length",   "time_gap_seconds",
    "unique_pages_visited", "total_requests_from_ip"
]

# average each feature separately for bots and humans
bot_means   = features[features["label"] == 1][FEATURE_COLS].mean()
human_means = features[features["label"] == 0][FEATURE_COLS].mean()

compare_df = pd.DataFrame({
    "Feature" : FEATURE_COLS,
    "Bot"     : bot_means.values,
    "Human"   : human_means.values
})

fig_bar = go.Figure()
fig_bar.add_trace(go.Bar(name="Bot",   x=compare_df["Feature"], y=compare_df["Bot"],   marker_color="#ef4444"))
fig_bar.add_trace(go.Bar(name="Human", x=compare_df["Feature"], y=compare_df["Human"], marker_color="#22c55e"))
fig_bar.update_layout(
    barmode = "group",
    xaxis_tickangle = -30,
    margin = dict(t=20, b=80)
)
st.plotly_chart(fig_bar, use_container_width=True)

st.divider()



# ─────────────────────────────────────────────
# raw predictions table with filter
# ─────────────────────────────────────────────

st.subheader("Flagged Requests Log")

filter_option = st.radio(
    "Show:",
    ["All", "Bots only", "Humans only"],
    horizontal = True
)

display_df = preds.copy()

if filter_option == "Bots only":
    display_df = display_df[display_df["victor_flag"] == 1]
elif filter_option == "Humans only":
    display_df = display_df[display_df["victor_flag"] == 0]

display_df = display_df[[
    *FEATURE_COLS,
    "iso_score", "xgb_score", "ensemble_score", "victor_flag"
]].sort_values("ensemble_score", ascending=False).reset_index(drop=True)

# round floats so they look clean
for col in ["iso_score", "xgb_score", "ensemble_score"]:
    display_df[col] = display_df[col].round(3)

# human readable status column
display_df["status"] = display_df["victor_flag"].apply(
    lambda x: "BOT" if x == 1 else "HUMAN"
)
display_df = display_df.drop(columns=["victor_flag"])

# render as plain HTML table — zero pyarrow dependency
st.markdown(
    display_df.to_html(index=False),
    unsafe_allow_html=True
)

st.caption(f"Showing {len(display_df)} of {len(preds)} total requests")