# dashboard.py  —  Victor  •  Bot Detection Dashboard
# run:  streamlit run dashboard.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json, os

# ─────────────────────────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title = "Victor — Bot Detector",
    page_icon  = "🛡️",
    layout     = "wide",
    initial_sidebar_state = "expanded"
)

# ─────────────────────────────────────────────────────────────────
# CUSTOM CSS  —  dark glassmorphism theme
# ─────────────────────────────────────────────────────────────────

st.markdown("""
<style>
  /* ── global background ── */
  .stApp {
      background: linear-gradient(135deg, #0a0e1a 0%, #0f1729 50%, #0a1628 100%);
      color: #e2e8f0;
  }

  /* ── sidebar ── */
  [data-testid="stSidebar"] {
      background: rgba(15, 23, 41, 0.95);
      border-right: 1px solid rgba(99, 102, 241, 0.2);
  }

  /* ── metric cards ── */
  [data-testid="stMetric"] {
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(99,102,241,0.25);
      border-radius: 14px;
      padding: 16px 20px;
      backdrop-filter: blur(12px);
      transition: transform 0.2s, box-shadow 0.2s;
  }
  [data-testid="stMetric"]:hover {
      transform: translateY(-3px);
      box-shadow: 0 8px 30px rgba(99,102,241,0.25);
  }
  [data-testid="stMetricLabel"]  { color: #94a3b8 !important; font-size: 0.78rem !important; letter-spacing: 0.06em; text-transform: uppercase; }
  [data-testid="stMetricValue"]  { color: #f1f5f9 !important; font-size: 1.9rem !important; font-weight: 700; }
  [data-testid="stMetricDelta"]  { font-size: 0.85rem !important; }

  /* ── section headings ── */
  h1 { color: #818cf8 !important; font-weight: 800 !important; }
  h2, h3 { color: #c7d2fe !important; }

  /* ── divider ── */
  hr { border-color: rgba(99,102,241,0.2) !important; }

  /* ── data table wrapper ── */
  .victor-table-wrap {
      overflow-x: auto;
      border-radius: 12px;
      border: 1px solid rgba(99,102,241,0.2);
      background: rgba(255,255,255,0.02);
      backdrop-filter: blur(8px);
      margin-top: 8px;
  }
  .victor-table-wrap table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.82rem;
  }
  .victor-table-wrap th {
      background: rgba(99,102,241,0.15);
      color: #a5b4fc;
      padding: 10px 12px;
      text-align: left;
      text-transform: uppercase;
      font-size: 0.7rem;
      letter-spacing: 0.06em;
      border-bottom: 1px solid rgba(99,102,241,0.2);
  }
  .victor-table-wrap td {
      padding: 8px 12px;
      border-bottom: 1px solid rgba(255,255,255,0.04);
      color: #cbd5e1;
  }
  .victor-table-wrap tr:hover td { background: rgba(99,102,241,0.06); }

  /* ── status badges ── */
  .badge-bot   { background:#ef444420; color:#f87171; border:1px solid #f8717150;
                 padding:2px 10px; border-radius:20px; font-weight:700; font-size:0.75rem; }
  .badge-human { background:#22c55e20; color:#4ade80; border:1px solid #4ade8050;
                 padding:2px 10px; border-radius:20px; font-weight:700; font-size:0.75rem; }

  /* ── radio + selectbox ── */
  .stRadio label, .stSelectbox label { color: #94a3b8 !important; }

  /* ── info box ── */
  .info-card {
      background: rgba(99,102,241,0.08);
      border: 1px solid rgba(99,102,241,0.25);
      border-radius: 12px;
      padding: 16px 20px;
      margin-bottom: 12px;
  }

  /* ── plotly charts — dark bg ── */
  .js-plotly-plot { border-radius: 12px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# PLOTLY shared dark layout
# ─────────────────────────────────────────────────────────────────

DARK_LAYOUT = dict(
    paper_bgcolor = "rgba(0,0,0,0)",
    plot_bgcolor  = "rgba(0,0,0,0)",
    font          = dict(color="#94a3b8", family="Inter, system-ui, sans-serif"),
    xaxis         = dict(gridcolor="rgba(255,255,255,0.05)", zerolinecolor="rgba(255,255,255,0.05)"),
    yaxis         = dict(gridcolor="rgba(255,255,255,0.05)", zerolinecolor="rgba(255,255,255,0.05)"),
    legend        = dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#cbd5e1")),
    margin        = dict(t=30, b=40, l=10, r=10),
)


# ─────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────

@st.cache_data
def load_data():
    preds    = pd.read_csv("data/predictions.csv")
    features = pd.read_csv("data/features.csv")
    return preds, features

@st.cache_data
def load_metrics():
    if os.path.exists("data/model_metrics.json"):
        with open("data/model_metrics.json") as f:
            return json.load(f)
    return None

@st.cache_data
def load_shap_csv():
    path = "data/shap/shap_values.csv"
    if os.path.exists(path):
        return pd.read_csv(path)
    return None


FEATURE_COLS = [
    "ua_is_suspicious", "has_referer", "has_accept_lang",
    "hit_secret_page",  "ua_length",   "time_gap_seconds",
    "unique_pages_visited", "total_requests_from_ip"
]

preds, features = load_data()
metrics = load_metrics()


# ─────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🛡️ Victor")
    st.markdown("<small style='color:#64748b'>Web Bot Fingerprint Detector</small>", unsafe_allow_html=True)
    st.divider()

    st.markdown("**Navigate**")
    page = st.radio("", ["📊 Dashboard", "🔍 Live IP Check", "🧠 Model Explainability", "📋 Raw Log"], label_visibility="collapsed")
    st.divider()

    # model metrics in sidebar if available
    if metrics:
        st.markdown("**Model Performance**")
        st.metric("XGBoost AUC", f"{metrics.get('xgb_auc', 0):.3f}")
        st.metric("IsoForest AUC", f"{metrics.get('iso_auc', 0):.3f}")
        st.divider()

    threshold = st.slider("🎚️ Bot Score Threshold", 0.1, 0.9, 0.5, 0.05,
                          help="Requests above this score are flagged as bots")
    st.divider()

    total         = len(preds)
    flagged_bots  = int((preds["ensemble_score"] > threshold).sum())
    clean_humans  = total - flagged_bots

    st.markdown(f"""
    <div class='info-card'>
      <b style='color:#a5b4fc'>Session Stats</b><br>
      <small style='color:#64748b'>Total requests</small><br>
      <b style='font-size:1.3rem;color:#f1f5f9'>{total:,}</b><br><br>
      <small style='color:#f87171'>● Bots detected</small> &nbsp;<b style='color:#f87171'>{flagged_bots:,}</b><br>
      <small style='color:#4ade80'>● Clean humans</small> &nbsp;<b style='color:#4ade80'>{clean_humans:,}</b>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# ── PAGE 1: DASHBOARD ──
# ─────────────────────────────────────────────────────────────────

if page == "📊 Dashboard":
    st.markdown("# 🛡️ Victor — Bot Detection Dashboard")
    st.markdown("<p style='color:#64748b;margin-top:-10px'>Real-time behavioral fingerprinting · Ensemble ML · XGBoost + Isolation Forest</p>", unsafe_allow_html=True)
    st.divider()

    avg_bot_score = round(preds["ensemble_score"].mean(), 3)
    bot_pct       = flagged_bots / total * 100
    human_pct     = clean_humans / total * 100

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Requests",  f"{total:,}")
    c2.metric("Bots Flagged",    f"{flagged_bots:,}",  delta=f"{bot_pct:.1f}%",   delta_color="inverse")
    c3.metric("Clean (Human)",   f"{clean_humans:,}",  delta=f"{human_pct:.1f}%")
    c4.metric("Avg Bot Score",   avg_bot_score,         delta="threshold 0.5",     delta_color="off")

    st.divider()

    # ── row 1: pie + histogram ──
    left, right = st.columns(2)

    with left:
        st.subheader("Traffic Breakdown")
        pie_df = pd.DataFrame({"Type": ["Bot", "Human"], "Count": [flagged_bots, clean_humans]})
        fig_pie = px.pie(pie_df, names="Type", values="Count",
                         color="Type",
                         color_discrete_map={"Bot": "#ef4444", "Human": "#22c55e"},
                         hole=0.5)
        fig_pie.update_traces(textposition="inside", textinfo="percent+label",
                              marker=dict(line=dict(color="#0f1729", width=3)))
        fig_pie.update_layout(**DARK_LAYOUT)
        st.plotly_chart(fig_pie, use_container_width=True)

    with right:
        st.subheader("Bot Confidence Score Distribution")
        fig_hist = px.histogram(preds, x="ensemble_score", nbins=35,
                                color_discrete_sequence=["#6366f1"],
                                labels={"ensemble_score": "Bot Probability"})
        fig_hist.add_vline(x=threshold, line_dash="dash", line_color="#f87171",
                           annotation_text=f"Threshold ({threshold})",
                           annotation_font_color="#f87171")
        fig_hist.update_layout(**DARK_LAYOUT)
        st.plotly_chart(fig_hist, use_container_width=True)

    st.divider()

    # ── row 2: feature comparison bar chart ──
    st.subheader("Feature Comparison — Bots vs Humans")

    bot_means   = features[features["label"] == 1][FEATURE_COLS].mean()
    human_means = features[features["label"] == 0][FEATURE_COLS].mean()
    compare_df  = pd.DataFrame({
        "Feature": FEATURE_COLS,
        "Bot":     bot_means.values,
        "Human":   human_means.values
    })

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(name="Bot",   x=compare_df["Feature"], y=compare_df["Bot"],
                             marker_color="#ef4444", marker_opacity=0.85))
    fig_bar.add_trace(go.Bar(name="Human", x=compare_df["Feature"], y=compare_df["Human"],
                             marker_color="#22c55e", marker_opacity=0.85))
    fig_bar.update_layout(barmode="group", xaxis_tickangle=-20, **DARK_LAYOUT)
    st.plotly_chart(fig_bar, use_container_width=True)

    # ── row 3: score over time (if timestamp available) ──
    if "timestamp" in preds.columns:
        st.divider()
        st.subheader("Bot Score Over Time")
        preds_t = preds.copy()
        preds_t["timestamp"] = pd.to_datetime(preds_t["timestamp"], errors="coerce")
        preds_t = preds_t.dropna(subset=["timestamp"]).sort_values("timestamp")
        fig_line = px.line(preds_t, x="timestamp", y="ensemble_score",
                           color_discrete_sequence=["#818cf8"])
        fig_line.add_hline(y=threshold, line_dash="dash", line_color="#f87171")
        fig_line.update_layout(**DARK_LAYOUT)
        st.plotly_chart(fig_line, use_container_width=True)


# ─────────────────────────────────────────────────────────────────
# ── PAGE 2: LIVE IP CHECK ──
# ─────────────────────────────────────────────────────────────────

elif page == "🔍 Live IP Check":
    st.markdown("# 🔍 Live IP Lookup")
    st.markdown("<p style='color:#64748b;margin-top:-10px'>Check any IP address against the logged traffic data.</p>", unsafe_allow_html=True)
    st.divider()

    ip_input = st.text_input("Enter an IP address to inspect", placeholder="e.g. 127.0.0.1")

    if ip_input:
        ip_rows = preds[features["label"].index.isin(
            features[preds.index].index  # align on same index
        )].copy() if "ip" not in preds.columns else preds[preds.get("ip", pd.Series()) == ip_input]

        # fallback: search in features if ip column exists there
        feat_ip = features[features["ip"] == ip_input] if "ip" in features.columns else pd.DataFrame()
        pred_ip = preds.loc[feat_ip.index] if len(feat_ip) > 0 else pd.DataFrame()

        if len(pred_ip) == 0 and "ip" in preds.columns:
            pred_ip = preds[preds["ip"] == ip_input]

        if len(pred_ip) == 0:
            st.warning(f"No traffic records found for **{ip_input}**.")
        else:
            avg_score = pred_ip["ensemble_score"].mean()
            is_bot    = avg_score > threshold

            verdict_color = "#f87171" if is_bot else "#4ade80"
            verdict_label = "⚠️ BOT" if is_bot else "✅ HUMAN"

            st.markdown(f"""
            <div style='background:rgba(255,255,255,0.03);border:1px solid {verdict_color}40;
                        border-radius:14px;padding:20px 24px;margin-bottom:20px'>
              <h3 style='color:{verdict_color};margin:0'>{verdict_label}</h3>
              <p style='color:#94a3b8;margin:4px 0 0'>IP: <b style='color:#f1f5f9'>{ip_input}</b>
                 &nbsp;·&nbsp; {len(pred_ip)} requests logged
                 &nbsp;·&nbsp; Avg score: <b style='color:{verdict_color}'>{avg_score:.3f}</b>
              </p>
            </div>
            """, unsafe_allow_html=True)

            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Requests",     len(pred_ip))
            col_b.metric("Avg Bot Score", f"{avg_score:.3f}")
            col_c.metric("Verdict",       "BOT" if is_bot else "HUMAN")

            st.markdown("**Score distribution for this IP**")
            fig_ip = px.histogram(pred_ip, x="ensemble_score", nbins=15,
                                  color_discrete_sequence=["#6366f1"])
            fig_ip.add_vline(x=threshold, line_dash="dash", line_color="#f87171")
            fig_ip.update_layout(**DARK_LAYOUT)
            st.plotly_chart(fig_ip, use_container_width=True)
    else:
        st.info("💡 Enter an IP address above to see its full activity profile.")


# ─────────────────────────────────────────────────────────────────
# ── PAGE 3: MODEL EXPLAINABILITY ──
# ─────────────────────────────────────────────────────────────────

elif page == "🧠 Model Explainability":
    st.markdown("# 🧠 Model Explainability")
    st.markdown("<p style='color:#64748b;margin-top:-10px'>SHAP values reveal <em>why</em> Victor flagged each request — not just that it did.</p>", unsafe_allow_html=True)
    st.divider()

    shap_img_bar    = "data/shap/feature_bar.png"
    shap_img_global = "data/shap/global_summary.png"
    shap_csv        = load_shap_csv()

    if os.path.exists(shap_img_global) or os.path.exists(shap_img_bar):
        col1, col2 = st.columns(2)
        with col1:
            if os.path.exists(shap_img_global):
                st.subheader("Global Feature Importance")
                st.image(shap_img_global, use_container_width=True)
        with col2:
            if os.path.exists(shap_img_bar):
                st.subheader("Average Feature Impact")
                st.image(shap_img_bar, use_container_width=True)
    else:
        st.warning("SHAP plots not found. Run `python explain.py` to generate them.")

    if shap_csv is not None:
        st.divider()
        st.subheader("SHAP Value Heatmap (top 200 rows)")
        shap_display = shap_csv.head(200)
        shap_renamed = shap_display.rename(columns={c: c.replace("shap_", "") for c in shap_display.columns})
        fig_heat = px.imshow(
            shap_renamed.values.T,
            x=list(range(len(shap_renamed))),
            y=list(shap_renamed.columns),
            color_continuous_scale="RdBu_r",
            aspect="auto",
            labels=dict(x="Request Index", y="Feature", color="SHAP")
        )
        fig_heat.update_layout(**DARK_LAYOUT, height=380)
        st.plotly_chart(fig_heat, use_container_width=True)

    st.divider()
    st.subheader("What Each Feature Means")
    explanations = {
        "ua_is_suspicious":      "User agent matches known bot signatures (python-requests, curl, etc.)",
        "has_referer":           "Whether the request came with a Referer header (humans usually do)",
        "has_accept_lang":       "Whether Accept-Language header was sent (bots often skip it)",
        "hit_secret_page":       "Whether the IP visited the hidden honeypot endpoint /secret-data",
        "ua_length":             "Length of the user agent string (bots tend to have shorter ones)",
        "time_gap_seconds":      "Seconds between requests from the same IP (bots move very fast)",
        "unique_pages_visited":  "Number of distinct pages visited (bots sweep many pages)",
        "total_requests_from_ip":"Total request count from this IP in the dataset",
    }
    for feat, desc in explanations.items():
        st.markdown(f"**`{feat}`** — {desc}")


# ─────────────────────────────────────────────────────────────────
# ── PAGE 4: RAW LOG ──
# ─────────────────────────────────────────────────────────────────

elif page == "📋 Raw Log":
    st.markdown("# 📋 Raw Predictions Log")
    st.markdown("<p style='color:#64748b;margin-top:-10px'>Full dataset with scores, flags, and filtering.</p>", unsafe_allow_html=True)
    st.divider()

    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        filter_opt = st.radio("Show:", ["All", "Bots only", "Humans only"], horizontal=True)
    with col_f2:
        search_score = st.slider("Min ensemble score", 0.0, 1.0, 0.0, 0.01)

    display_df = preds.copy()
    display_df["victor_flag"] = (display_df["ensemble_score"] > threshold).astype(int)

    if filter_opt == "Bots only":
        display_df = display_df[display_df["victor_flag"] == 1]
    elif filter_opt == "Humans only":
        display_df = display_df[display_df["victor_flag"] == 0]

    display_df = display_df[display_df["ensemble_score"] >= search_score]

    cols_to_show = [c for c in [*FEATURE_COLS, "iso_score", "xgb_score", "ensemble_score", "victor_flag"] if c in display_df.columns]
    display_df = display_df[cols_to_show].sort_values("ensemble_score", ascending=False).reset_index(drop=True)

    for col in ["iso_score", "xgb_score", "ensemble_score"]:
        if col in display_df.columns:
            display_df[col] = display_df[col].round(3)

    def style_row(row):
        status = "<span class='badge-bot'>BOT</span>" if row.get("victor_flag", 0) == 1 else "<span class='badge-human'>HUMAN</span>"
        return status

    display_df["status"] = display_df.apply(style_row, axis=1)
    display_df = display_df.drop(columns=["victor_flag"], errors="ignore")

    html_table = display_df.to_html(index=False, escape=False)
    st.markdown(f"<div class='victor-table-wrap'>{html_table}</div>", unsafe_allow_html=True)
    st.caption(f"Showing {len(display_df):,} of {len(preds):,} total requests  •  threshold = {threshold}")