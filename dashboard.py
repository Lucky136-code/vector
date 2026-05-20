# dashboard.py  —  Victor  •  SOC Bot Detection Dashboard
# run:  streamlit run dashboard.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import shap
import joblib
import subprocess
from datetime import datetime

# ─────────────────────────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title = "Victor — SOC Threat Console",
    page_icon  = "🛡️",
    layout     = "wide",
    initial_sidebar_state = "expanded"
)

# ─────────────────────────────────────────────────────────────────
# CUSTOM "SIMPLY OLIVE" & WHITE ORGANIC SOC STYLING (HIGH CONTRAST)
# ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Comfortaa:wght@400;600;700&family=Outfit:wght@300;400;500;600;700;800&family=Fira+Code:wght@400;500;700&display=swap');

  /* Global adjustments - high contrast black text */
  html, body, [class*="css"] {
      font-family: 'Outfit', sans-serif !important;
      background-color: #ffffff;
      color: #000000 !important;
  }
  
  .stApp {
      background: #ffffff;
      color: #000000 !important;
  }

  /* Sidebar styling */
  [data-testid="stSidebar"] {
      background: #f4f4f0 !important;
      border-right: 1px solid rgba(85, 107, 47, 0.15) !important;
  }
  [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
      color: #000000 !important;
  }

  /* Minimalist Olive Card */
  .cyber-card {
      background: #fafaf7;
      border: 1px solid rgba(85, 107, 47, 0.25);
      border-radius: 12px;
      padding: 20px;
      box-shadow: 0 4px 20px rgba(85, 107, 47, 0.03);
      margin-bottom: 20px;
      transition: all 0.3s ease;
      color: #000000;
  }
  .cyber-card:hover {
      border: 1px solid rgba(85, 107, 47, 0.45);
      box-shadow: 0 4px 25px rgba(85, 107, 47, 0.06);
  }

  /* Custom metric card wrapper overrides - Black & Olive */
  [data-testid="stMetric"] {
      background: #fafaf7 !important;
      border: 1px solid rgba(85, 107, 47, 0.2) !important;
      border-radius: 12px !important;
      padding: 16px 20px !important;
      box-shadow: 0 2px 10px rgba(85, 107, 47, 0.02) !important;
      transition: all 0.3s ease !important;
  }
  [data-testid="stMetric"]:hover {
      transform: translateY(-2px) !important;
      border-color: rgba(85, 107, 47, 0.45) !important;
      box-shadow: 0 6px 20px rgba(85, 107, 47, 0.06) !important;
  }
  [data-testid="stMetricLabel"]  { color: #333333 !important; font-size: 0.78rem !important; letter-spacing: 0.06em; text-transform: uppercase; font-weight: 600; }
  [data-testid="stMetricValue"]  { color: #556b2f !important; font-size: 2.1rem !important; font-weight: 700; font-family: 'Comfortaa', sans-serif !important; }

  /* Custom badges (No Emojis) */
  .badge-bot     { background:#fee2e2; color:#dc2626; border:1px solid #fca5a5;
                   padding:2px 10px; border-radius:20px; font-weight:700; font-size:0.75rem; font-family: 'Fira Code', monospace; }
  .badge-human   { background:#d1fae5; color:#556b2f; border:1px solid #a7f3d0;
                   padding:2px 10px; border-radius:20px; font-weight:700; font-size:0.75rem; font-family: 'Fira Code', monospace; }
  .badge-blocked { background:#fef3c7; color:#d97706; border:1px solid #fde68a;
                   padding:2px 10px; border-radius:20px; font-weight:700; font-size:0.75rem; font-family: 'Fira Code', monospace; }

  /* Parchment Terminal logs styling (High Contrast Black Text) */
  .terminal-console {
      background: #fbfbfa;
      border: 1px solid rgba(85, 107, 47, 0.3);
      border-radius: 8px;
      padding: 14px 18px;
      font-family: 'Fira Code', monospace;
      font-size: 0.82rem;
      color: #000000;
      max-height: 250px;
      overflow-y: auto;
      box-shadow: inset 0 0 10px rgba(85, 107, 47, 0.05);
      margin-bottom: 20px;
  }
  .terminal-line {
      margin-bottom: 5px;
      line-height: 1.4;
  }
  .terminal-time { color: #555555; margin-right: 8px; }
  .terminal-info { color: #556b2f; font-weight: bold; }
  .terminal-warn { color: #d97706; font-weight: bold; }
  .terminal-alert { color: #dc2626; font-weight: bold; }
  .terminal-success { color: #556b2f; font-weight: bold; }

  /* Status pulse indicator */
  .pulse-green {
      display: inline-block;
      width: 10px;
      height: 10px;
      background-color: #556b2f;
      border-radius: 50%;
      box-shadow: 0 0 0 0 rgba(85, 107, 47, 0.7);
      animation: pulse-green-anim 1.8s infinite;
  }
  @keyframes pulse-green-anim {
      0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(85, 107, 47, 0.7); }
      70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(85, 107, 47, 0); }
      100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(85, 107, 47, 0); }
  }

  /* Header badge styling */
  .header-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(85, 107, 47, 0.06);
      border: 1px solid rgba(85, 107, 47, 0.25);
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 0.75rem;
      color: #556b2f;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
  }

  /* Custom typography titles */
  h1 { font-family: 'Comfortaa', sans-serif !important; font-weight: 700 !important; color: #556b2f !important; }
  h2, h3 { font-family: 'Comfortaa', sans-serif !important; font-weight: 600 !important; color: #333333 !important; }

  /* Custom tables wrapper styling */
  .victor-table-wrap {
      overflow-x: auto;
      border-radius: 12px;
      border: 1px solid rgba(85, 107, 47, 0.15);
      background: #fafaf7;
      margin-top: 8px;
  }
  .victor-table-wrap table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.85rem;
  }
  .victor-table-wrap th {
      background: rgba(85, 107, 47, 0.07);
      color: #556b2f;
      padding: 12px 14px;
      text-align: left;
      text-transform: uppercase;
      font-size: 0.72rem;
      font-family: 'Fira Code', monospace;
      letter-spacing: 0.06em;
      border-bottom: 1px solid rgba(85, 107, 47, 0.18);
  }
  .victor-table-wrap td {
      padding: 10px 14px;
      border-bottom: 1px solid rgba(85, 107, 47, 0.05);
      color: #000000;
  }
  .victor-table-wrap tr:hover td {
      background: rgba(85, 107, 47, 0.03);
  }
  
  /* Buttons custom color overrides to fit light theme */
  .stButton button {
      color: #000000 !important;
      border: 1px solid rgba(85, 107, 47, 0.3) !important;
      background-color: #fafaf7 !important;
      font-weight: 600 !important;
  }
  .stButton button:hover {
      border-color: #556b2f !important;
      background-color: #f4f4f0 !important;
  }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# DATA & MITIGATION LOADERS
# ─────────────────────────────────────────────────────────────────
FIREWALL_FILE = "data/firewall.json"

def load_firewall():
    if os.path.exists(FIREWALL_FILE):
        try:
            with open(FIREWALL_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"blocked": [], "whitelisted": []}

def save_firewall(firewall):
    os.makedirs("data", exist_ok=True)
    with open(FIREWALL_FILE, "w") as f:
        json.dump(firewall, f, indent=2)

def block_ip(ip):
    fw = load_firewall()
    if ip not in fw["blocked"]:
        fw["blocked"].append(ip)
    if ip in fw["whitelisted"]:
        fw["whitelisted"].remove(ip)
    save_firewall(fw)

def whitelist_ip(ip):
    fw = load_firewall()
    if ip not in fw["whitelisted"]:
        fw["whitelisted"].append(ip)
    if ip in fw["blocked"]:
        fw["blocked"].remove(ip)
    save_firewall(fw)

def remove_from_firewall(ip):
    fw = load_firewall()
    if ip in fw["blocked"]:
        fw["blocked"].remove(ip)
    if ip in fw["whitelisted"]:
        fw["whitelisted"].remove(ip)
    save_firewall(fw)

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

@st.cache_resource
def load_xgboost_model():
    if os.path.exists("models/xgboost_model.pkl"):
        return joblib.load("models/xgboost_model.pkl")
    return None

# Load base data
preds, features = load_data()
metrics = load_metrics()
xgb_model = load_xgboost_model()

# Load and apply Firewall Policy to data
firewall = load_firewall()
blocked_ips = firewall["blocked"]
whitelisted_ips = firewall["whitelisted"]

# Apply Active Override Logic
if "ip" in preds.columns:
    preds["original_ensemble_score"] = preds["ensemble_score"].copy()
    
    # Overwrite score and flag for blocked
    preds.loc[preds["ip"].isin(blocked_ips), "ensemble_score"] = 1.0
    preds.loc[preds["ip"].isin(blocked_ips), "victor_flag"] = 1
    
    # Overwrite score and flag for whitelisted
    preds.loc[preds["ip"].isin(whitelisted_ips), "ensemble_score"] = 0.0
    preds.loc[preds["ip"].isin(whitelisted_ips), "victor_flag"] = 0

# Feature column constants
FEATURE_COLS = [
    "ua_is_suspicious", "has_referer", "has_accept_lang",
    "hit_secret_page",  "ua_length",   "time_gap_seconds",
    "unique_pages_visited", "total_requests_from_ip"
]

# LIGHT OLIVE PLOTLY LAYOUT
DARK_LAYOUT = dict(
    paper_bgcolor = "rgba(0,0,0,0)",
    plot_bgcolor  = "rgba(0,0,0,0)",
    font          = dict(color="#000000", family="Outfit, system-ui, sans-serif"),
    xaxis         = dict(gridcolor="rgba(85, 107, 47, 0.08)", zerolinecolor="rgba(85, 107, 47, 0.15)", tickfont=dict(color="#333333")),
    yaxis         = dict(gridcolor="rgba(85, 107, 47, 0.08)", zerolinecolor="rgba(85, 107, 47, 0.15)", tickfont=dict(color="#333333")),
    legend        = dict(bgcolor="rgba(250, 250, 247, 0.9)", font=dict(color="#000000")),
    margin        = dict(t=30, b=40, l=10, r=10),
)

# ─────────────────────────────────────────────────────────────────
# SIDEBAR NAVIGATION & PANEL STATUS
# ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 20px;'>
      <div class='pulse-green'></div>
      <b style='color:#556b2f; font-family:"Fira Code", monospace; font-size:0.78rem; text-transform:uppercase; letter-spacing: 0.05em;'>SOC Status: Monitoring</b>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<h2 class='branding-title' style='margin:0; font-size:1.6rem;'>Victor // SOC</h2>", unsafe_allow_html=True)
    st.markdown("<small style='color:#333333'>Web Bot Fingerprint Console</small>", unsafe_allow_html=True)
    st.divider()

    st.markdown("**Navigate Console**")
    page = st.radio("Navigate Console", ["SOC Dashboard", "IP Threat Center", "Explainability Lab", "Firewall Policy", "Pipeline Control"], label_visibility="collapsed")
    st.divider()

    threshold = st.slider("Threat Score Threshold", 0.1, 0.9, 0.5, 0.05,
                          help="Requests above this rating are classified as anomalous bot behavior")
    st.divider()

    # Dynamic computations based on current threshold
    total = len(preds)
    flagged_bots = int((preds["ensemble_score"] > threshold).sum())
    clean_humans = total - flagged_bots

    st.markdown(f"""
    <div class='cyber-card' style='padding: 14px 18px;'>
      <b style='color:#556b2f; font-size: 0.85rem; font-family:"Comfortaa", cursive;'>Rules Summary</b><br>
      <small style='color:#333333'>Total Inspected</small>&nbsp;&nbsp;<b style='color:#000000'>{total:,}</b><br>
      <small style='color:#dc2626'>Bots Flagged</small>&nbsp;&nbsp;<b style='color:#dc2626'>{flagged_bots:,}</b><br>
      <small style='color:#556b2f'>Verified Human</small>&nbsp;&nbsp;<b style='color:#556b2f'>{clean_humans:,}</b><br>
      <small style='color:#d97706'>Blocked IPs</small>&nbsp;&nbsp;<b style='color:#d97706'>{len(blocked_ips)}</b>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# PAGE 1: SOC DASHBOARD
# ─────────────────────────────────────────────────────────────────
if page == "SOC Dashboard":
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 4px;'>
      <h1>Security Operations Center</h1>
      <span class='header-badge'>Ensemble Core</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<p style='color:#333333; font-size: 0.95rem; margin-top:-5px'>High-fidelity behavioral analytics utilizing consolidated XGBoost and Isolation Forest detectors.</p>", unsafe_allow_html=True)
    st.divider()

    # Metrics Row
    avg_score = round(preds["ensemble_score"].mean(), 3)
    bot_pct = (flagged_bots / total * 100) if total > 0 else 0.0
    human_pct = (clean_humans / total * 100) if total > 0 else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Inspected Requests", f"{total:,}")
    c2.metric("Threat Flags", f"{flagged_bots:,}", delta=f"{bot_pct:.1f}%", delta_color="inverse")
    c3.metric("Verified Human", f"{clean_humans:,}", delta=f"{human_pct:.1f}%")
    c4.metric("Avg Threat Rating", avg_score, delta="threshold 0.5", delta_color="off")

    st.divider()

    # Dynamic Console Logs Engine (Extracted from real log file)
    st.subheader("SOC Live Incident Feed")
    
    alerts = []
    if "ip" in preds.columns:
        # High threat alerts
        high_threats = preds[preds["ensemble_score"] > threshold].sort_values("timestamp", ascending=False).head(4)
        for idx, row in high_threats.iterrows():
            t_str = pd.to_datetime(row["timestamp"]).strftime("%H:%M:%S") if pd.notna(row["timestamp"]) else "11:24:08"
            ip_lbl = f"<span style='color:#dc2626'>{row['ip']}</span>"
            if row["ip"] in blocked_ips:
                ip_lbl += " <span class='badge-blocked' style='font-size:0.6rem; padding:1px 5px;'>OVERRIDE BLOCK</span>"
            
            alerts.append((row["timestamp"], f"<span class='terminal-time'>[{t_str}]</span> <span class='terminal-alert'>[ANOMALY FLAG]</span> Threat level exceeding {row['ensemble_score']:.2f} rating from IP {ip_lbl}. Signature check: suspicious UA."))
        
        # Honeypot hits
        honeypot_hits = preds[preds["hit_secret_page"] == 1].sort_values("timestamp", ascending=False).head(3)
        for idx, row in honeypot_hits.iterrows():
            t_str = pd.to_datetime(row["timestamp"]).strftime("%H:%M:%S") if pd.notna(row["timestamp"]) else "11:24:32"
            alerts.append((row["timestamp"], f"<span class='terminal-time'>[{t_str}]</span> <span class='terminal-warn'>[HONEYPOT EXPLORED]</span> Source IP <span style='color:#d97706'>{row['ip']}</span> queried hidden endpoint <span style='color:#dc2626'>/secret-data</span>. Immediate restriction recommended."))

        # Normal logs
        normal_logs = preds[preds["ensemble_score"] < 0.15].sort_values("timestamp", ascending=False).head(3)
        for idx, row in normal_logs.iterrows():
            t_str = pd.to_datetime(row["timestamp"]).strftime("%H:%M:%S") if pd.notna(row["timestamp"]) else "11:25:01"
            alerts.append((row["timestamp"], f"<span class='terminal-time'>[{t_str}]</span> <span class='terminal-success'>[VERIFIED HUMAN]</span> Clear fingerprint validated for IP <span style='color:#556b2f'>{row['ip']}</span>. Routing normal response."))

    # Sort and render alerts console
    alerts = sorted(alerts, key=lambda x: x[0])
    alert_lines = [a[1] for a in alerts[-10:]]

    terminal_html = "<div class='terminal-console'>"
    if alert_lines:
        for line in alert_lines:
            terminal_html += f"<div class='terminal-line'>{line}</div>"
    else:
        terminal_html += "<div class='terminal-line' style='color:#333333'>[INFO] No active traffic anomalies detected in threat log.</div>"
    terminal_html += "</div>"
    
    st.markdown(terminal_html, unsafe_allow_html=True)

    # Visualization grid
    left, right = st.columns(2)

    with left:
        st.subheader("Traffic Breakdown")
        pie_df = pd.DataFrame({"Type": ["Anomalous Bot", "Verified Human"], "Count": [flagged_bots, clean_humans]})
        fig_pie = px.pie(pie_df, names="Type", values="Count",
                         color="Type",
                         color_discrete_map={"Anomalous Bot": "#dc2626", "Verified Human": "#556b2f"},
                         hole=0.55)
        fig_pie.update_traces(textposition="inside", textinfo="percent+label",
                              marker=dict(line=dict(color="#ffffff", width=3)))
        fig_pie.update_layout(**DARK_LAYOUT)
        st.plotly_chart(fig_pie, width="stretch")

    with right:
        st.subheader("Ensemble Score Distribution")
        fig_hist = px.histogram(preds, x="ensemble_score", nbins=35,
                                color_discrete_sequence=["#808000"],
                                labels={"ensemble_score": "Bot Probability Score"})
        fig_hist.add_vline(x=threshold, line_dash="dash", line_color="#dc2626",
                           annotation_text=f"Trigger Threshold ({threshold})",
                           annotation_font_color="#dc2626", annotation_position="top left")
        fig_hist.update_layout(**DARK_LAYOUT)
        st.plotly_chart(fig_hist, width="stretch")

    st.divider()

    # Feature comparison
    st.subheader("Anatomical Feature Comparison — Anomalies vs Humans")
    bot_means   = features[features["label"] == 1][FEATURE_COLS].mean()
    human_means = features[features["label"] == 0][FEATURE_COLS].mean()
    compare_df  = pd.DataFrame({
        "Feature Signature": FEATURE_COLS,
        "Anomalous Bot Profile": bot_means.values,
        "Human Profile": human_means.values
    })

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(name="Anomalous Bot", x=compare_df["Feature Signature"], y=compare_df["Anomalous Bot Profile"],
                             marker_color="#dc2626", marker_opacity=0.8))
    fig_bar.add_trace(go.Bar(name="Human Verified", x=compare_df["Feature Signature"], y=compare_df["Human Profile"],
                             marker_color="#556b2f", marker_opacity=0.8))
    fig_bar.update_layout(barmode="group", xaxis_tickangle=-15, **DARK_LAYOUT)
    st.plotly_chart(fig_bar, width="stretch")

# ─────────────────────────────────────────────────────────────────
# PAGE 2: IP THREAT CENTER
# ─────────────────────────────────────────────────────────────────
elif page == "IP Threat Center":
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 4px;'>
      <h1>IP Threat Center</h1>
      <span class='header-badge'>Interactive Lookup & Mitigation</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<p style='color:#333333; font-size: 0.95rem; margin-top:-5px'>Inspect IP behavior profiles, investigate anomalous traffic logs, and deploy immediate policy rules.</p>", unsafe_allow_html=True)
    st.divider()

    # Sidebar or input select box for active IPs
    unique_ips = [""]
    if "ip" in preds.columns:
        unique_ips.extend(preds["ip"].dropna().unique().tolist())
    
    ip_input = st.selectbox("Select an IP address to inspect", unique_ips, index=0)
    
    # Text input for manual searches
    manual_ip = st.text_input("Or enter manual IP to audit", placeholder="e.g. 192.168.1.45")
    selected_ip = manual_ip.strip() if manual_ip.strip() else ip_input

    if selected_ip:
        # filter for IP records
        pred_ip = preds[preds["ip"] == selected_ip] if "ip" in preds.columns else pd.DataFrame()
        feat_ip = features[features["ip"] == selected_ip] if "ip" in features.columns else pd.DataFrame()

        if len(pred_ip) == 0:
            st.warning(f"No active log matches found for target: {selected_ip}")
        else:
            avg_ip_score = pred_ip["ensemble_score"].mean()
            is_flagged = avg_ip_score > threshold
            
            # Check policy overrides
            is_blocked = selected_ip in blocked_ips
            is_whitelisted = selected_ip in whitelisted_ips

            if is_blocked:
                card_border = "#d97706"
                verdict_lbl = "BLOCKED BY FIREWALL RULE"
                desc_lbl = "This IP address was manually blacklisted by an administrator."
            elif is_whitelisted:
                card_border = "#556b2f"
                verdict_lbl = "ADMIN WHITELISTED"
                desc_lbl = "This IP is protected from bot detection metrics via whitelist override."
            elif is_flagged:
                card_border = "#dc2626"
                verdict_lbl = "HIGH RISK ANOMALOUS BOT"
                desc_lbl = f"Consensus ML scores indicate this IP exhibits bot metrics ({avg_ip_score:.3f})."
            else:
                card_border = "#556b2f"
                verdict_lbl = "STABLE HUMAN SIGNATURE"
                desc_lbl = f"Safe traffic profile matches verified standard human browser fingerprints ({avg_ip_score:.3f})."

            st.markdown(f"""
            <div style='background:#fafaf7; border:1px solid {card_border}66;
                        border-radius:14px; padding:22px 26px; margin-bottom:20px; box-shadow: 0 4px 20px {card_border}0b'>
              <h3 style='color:{card_border}; margin:0; font-family:"Comfortaa", cursive; font-weight:700;'>{verdict_lbl}</h3>
              <p style='color:#000000; font-size:1.05rem; margin:6px 0 10px 0;'>{desc_lbl}</p>
              <small style='color:#333333; font-family:"Fira Code", monospace;'>IP Target: <b>{selected_ip}</b> &nbsp;·&nbsp; Total Sessions audited: <b>{len(pred_ip)}</b> requests</small>
            </div>
            """, unsafe_allow_html=True)

            # INTERACTIVE FIREWALL BLOCK/WHITELIST CONTROLS
            st.subheader("Real-Time Access Mitigation")
            
            col_b1, col_b2, col_b3 = st.columns(3)
            
            with col_b1:
                if not is_blocked:
                    if st.button("Deploy Immediate Block", use_container_width=True):
                        block_ip(selected_ip)
                        st.toast(f"IP {selected_ip} successfully blocked!", icon="🚫")
                        st.rerun()
                else:
                    st.button("Already Blocked", disabled=True, use_container_width=True)
            
            with col_b2:
                if not is_whitelisted:
                    if st.button("Force Whitelist Exception", use_container_width=True):
                        whitelist_ip(selected_ip)
                        st.toast(f"IP {selected_ip} added to whitelist!", icon="✅")
                        st.rerun()
                else:
                    st.button("Already Whitelisted", disabled=True, use_container_width=True)
            
            with col_b3:
                if is_blocked or is_whitelisted:
                    if st.button("Reset Mitigation Policy", use_container_width=True):
                        remove_from_firewall(selected_ip)
                        st.toast(f"Mitigation rules cleared for {selected_ip}!", icon="🔄")
                        st.rerun()
                else:
                    st.button("No Active Rule", disabled=True, use_container_width=True)

            st.divider()

            # IP Session logs
            st.subheader("Audited IP Activity Logs")
            
            show_cols = ["timestamp", "path", "user_agent", "ensemble_score"]
            ip_table_df = pred_ip[show_cols].copy() if len(pred_ip) > 0 else pd.DataFrame()
            if len(ip_table_df) > 0:
                ip_table_df["ensemble_score"] = ip_table_df["ensemble_score"].round(3)
                ip_table_df["status"] = ip_table_df["ensemble_score"].apply(
                    lambda s: "<span class='badge-bot'>BOT</span>" if s > threshold else "<span class='badge-human'>HUMAN</span>"
                )
                if is_blocked:
                    ip_table_df["status"] = "<span class='badge-blocked'>BLOCKED</span>"
                elif is_whitelisted:
                    ip_table_df["status"] = "<span class='badge-human'>WHITELISTED</span>"
                
                # Render beautiful custom table
                html_table = ip_table_df.to_html(index=False, escape=False)
                st.markdown(f"<div class='victor-table-wrap'>{html_table}</div>", unsafe_allow_html=True)
            
            # Session score distribution
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("Threat Score Profile Distribution")
            fig_ip = px.histogram(pred_ip, x="original_ensemble_score" if "original_ensemble_score" in pred_ip.columns else "ensemble_score", 
                                  nbins=10, color_discrete_sequence=["#808000"],
                                  labels={"x": "Score Rating"})
            fig_ip.add_vline(x=threshold, line_dash="dash", line_color="#dc2626")
            fig_ip.update_layout(**DARK_LAYOUT)
            st.plotly_chart(fig_ip, width="stretch")

    else:
        st.info("Select or enter an IP address above to run full diagnostic forensic audit.")

# ─────────────────────────────────────────────────────────────────
# PAGE 3: EXPLAINABILITY LAB
# ─────────────────────────────────────────────────────────────────
elif page == "Explainability Lab":
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 4px;'>
      <h1>Explainability Lab (SHAP Engine)</h1>
      <span class='header-badge'>Request Diagnostics</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<p style='color:#333333; font-size: 0.95rem; margin-top:-5px'>Explain exactly why Victor flagged a particular session. Demystify ML decisions using SHAP value contributions.</p>", unsafe_allow_html=True)
    st.divider()

    st.subheader("Local Request-Level SHAP Explorer")
    st.markdown("Select a specific request session to see a dynamic waterfall decomposition showing which features pushed the model's prediction toward a Bot classification (red) vs. a Human classification (green).")

    # Dropdown to select request index
    request_options = []
    if "ip" in preds.columns:
        for idx, row in preds.sort_values("ensemble_score", ascending=False).head(100).iterrows():
            request_options.append((idx, f"Row #{idx} | IP: {row['ip']} | Score: {row['ensemble_score']:.3f} | Path: {row['path']}"))
    
    if request_options:
        selected_idx_tuple = st.selectbox(
            "Select high-threat request to audit (showing top 100 highest scores):",
            request_options,
            format_func=lambda x: x[1]
        )
        selected_idx = selected_idx_tuple[0]
        
        # Display selected row features
        row_data = features.iloc[selected_idx][FEATURE_COLS].to_frame().T
        st.markdown("**Inspected Request Signature Features:**")
        st.dataframe(row_data, use_container_width=True)

        # Dynamic SHAP prediction calculation
        if xgb_model:
            try:
                explainer = shap.TreeExplainer(xgb_model)
                # ensure numeric types
                for col in FEATURE_COLS:
                    row_data[col] = pd.to_numeric(row_data[col])
                
                # Calculate SHAP values
                shap_arr = explainer.shap_values(row_data)
                
                # Check format of returned values
                if isinstance(shap_arr, list):
                    shap_row_values = shap_arr[0][0]
                elif len(shap_arr.shape) == 3: # multi-class probability shape
                    shap_row_values = shap_arr[0, :, 1]
                else: # 2D array
                    shap_row_values = shap_arr[0]
                
                # Create df
                shap_df = pd.DataFrame({
                    "Feature Name": FEATURE_COLS,
                    "SHAP Impact Value": shap_row_values,
                    "Influence": ["Pushing to Anomaly (Bot)" if val > 0 else "Pushing to Standard (Human)" for val in shap_row_values]
                })
                shap_df["Abs Impact"] = shap_df["SHAP Impact Value"].abs()
                shap_df = shap_df.sort_values("Abs Impact", ascending=True)

                fig_shap = px.bar(
                    shap_df,
                    x="SHAP Impact Value",
                    y="Feature Name",
                    color="Influence",
                    color_discrete_map={
                        "Pushing to Anomaly (Bot)": "#dc2626",
                        "Pushing to Standard (Human)": "#556b2f"
                    },
                    orientation="h",
                    title=f"SHAP Local Waterfall Attribution (Request Row #{selected_idx})"
                )
                fig_shap.update_layout(**DARK_LAYOUT)
                st.plotly_chart(fig_shap, width="stretch")
                
            except Exception as e:
                st.error(f"Failed to generate dynamic SHAP waterfall chart: {e}")
        else:
            st.warning("XGBoost model pkl not found. Please compile the model in the Pipeline Control tab first.")

    st.divider()

    # Global SHAP section
    st.subheader("Global Feature Significance")
    shap_img_bar    = "data/shap/feature_bar.png"
    shap_img_global = "data/shap/global_summary.png"

    if os.path.exists(shap_img_global) or os.path.exists(shap_img_bar):
        col1, col2 = st.columns(2)
        with col1:
            if os.path.exists(shap_img_global):
                st.image(shap_img_global, use_container_width=True, caption="Global Summary: Feature value densities and impact levels.")
        with col2:
            if os.path.exists(shap_img_bar):
                st.image(shap_img_bar, use_container_width=True, caption="Average Feature Impact: Mean absolute SHAP contribution ranking.")
    else:
        st.warning("Core SHAP plots not found. Please compile them via explain.py or model retraining.")

# ─────────────────────────────────────────────────────────────────
# PAGE 4: FIREWALL POLICY RULES
# ─────────────────────────────────────────────────────────────────
elif page == "Firewall Policy":
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 4px;'>
      <h1>Firewall & Policy Manager</h1>
      <span class='header-badge'>Mitigation Database</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<p style='color:#333333; font-size: 0.95rem; margin-top:-5px'>Manage administrative blacklist rules, enforce whitelists, and view policy override audits.</p>", unsafe_allow_html=True)
    st.divider()

    c_b, c_w = st.columns(2)

    with c_b:
        st.subheader("Active IP Blacklist Policies")
        if blocked_ips:
            for ip in blocked_ips:
                col_row_1, col_row_2 = st.columns([3, 1])
                with col_row_1:
                    st.markdown(f"**`{ip}`** — *QUARANTINED*")
                with col_row_2:
                    if st.button("Delete Block", key=f"del_b_{ip}"):
                        remove_from_firewall(ip)
                        st.toast(f"Removed block rules for {ip}!", icon="🔄")
                        st.rerun()
        else:
            st.info("No active IP blocklist rules currently deployed. System relies on pure ML scoring thresholds.")

    with c_w:
        st.subheader("Active IP Whitelist Exceptions")
        if whitelisted_ips:
            for ip in whitelisted_ips:
                col_row_1, col_row_2 = st.columns([3, 1])
                with col_row_1:
                    st.markdown(f"**`{ip}`** — *SAFE ROUTING EXCEPTION*")
                with col_row_2:
                    if st.button("Delete Safe", key=f"del_w_{ip}"):
                        remove_from_firewall(ip)
                        st.toast(f"Removed safe rules for {ip}!", icon="🔄")
                        st.rerun()
        else:
            st.info("No active IP whitelist exceptions configured.")

# ─────────────────────────────────────────────────────────────────
# PAGE 5: PIPELINE CONTROL
# ─────────────────────────────────────────────────────────────────
elif page == "Pipeline Control":
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 4px;'>
      <h1>Pipeline Control Room</h1>
      <span class='header-badge'>Automation Console</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<p style='color:#333333; font-size: 0.95rem; margin-top:-5px'>Initiate automated network traffic simulations and recompile model weights directly from the dashboard.</p>", unsafe_allow_html=True)
    st.divider()

    st.subheader("Automated Threat Traffic Generator")
    st.markdown("Run automated traffic modules to generate human-like sessions and simulated bot requests. This compiles mock logs to simulate threat mitigation.")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        num_h = st.slider("Human Verified Sessions", 10, 200, 50, 10)
    with col_s2:
        num_b = st.slider("Anomalous Bot Sessions", 10, 200, 50, 10)

    if st.button("Trigger Simulation Engine", use_container_width=True):
        with st.spinner("Generating simulated user sessions and writing to traffic logs..."):
            try:
                # Direct simulation generation fallback to bypass server outages
                import random
                from datetime import datetime, timedelta
                from faker import Faker
                fake = Faker()

                LOG_FILE = "data/traffic_logs.json"
                logs = []
                if os.path.exists(LOG_FILE):
                    try:
                        with open(LOG_FILE, "r") as f:
                            logs = json.load(f)
                    except Exception:
                        logs = []

                # Simulated lists
                human_agents = [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
                ]
                bot_agents = [
                    "python-requests/2.28.0",
                    "Scrapy/2.11.0 (+https://scrapy.org)",
                    "curl/7.88.1",
                    "Mozilla/5.0 (compatible; Googlebot/2.1)",
                    "Go-http-client/1.1"
                ]
                human_pages = ["/", "/articles", "/about"]
                bot_pages = ["/", "/articles", "/about", "/secret-data", "/secret-data", "/secret-data"]
                
                base_time = datetime.now()

                # Generate humans
                for i in range(num_h):
                    ip = f"192.168.1.{random.randint(10, 150)}"
                    agent = random.choice(human_agents)
                    session_time = base_time - timedelta(minutes=random.randint(1, 120))
                    pages = random.sample(human_pages, k=random.randint(2, 3))
                    
                    for p_idx, page in enumerate(pages):
                        req_time = session_time + timedelta(seconds=p_idx * random.uniform(2, 8))
                        entry = {
                            "timestamp": req_time.isoformat(),
                            "ip": ip,
                            "method": "GET",
                            "path": page,
                            "user_agent": agent,
                            "referer": "https://google.com" if random.random() > 0.2 else "none",
                            "accept_lang": "en-US,en;q=0.9",
                            "label": 0
                        }
                        logs.append(entry)

                # Generate bots
                for i in range(num_b):
                    ip = f"45.32.{random.randint(10, 250)}.{random.randint(10, 250)}"
                    agent = random.choice(bot_agents)
                    session_time = base_time - timedelta(minutes=random.randint(1, 120))
                    
                    for p_idx, page in enumerate(bot_pages):
                        req_time = session_time + timedelta(seconds=p_idx * random.uniform(0.01, 0.05))
                        entry = {
                            "timestamp": req_time.isoformat(),
                            "ip": ip,
                            "method": "GET",
                            "path": page,
                            "user_agent": agent,
                            "referer": "none" if random.random() > 0.1 else "https://bing.com",
                            "accept_lang": "none" if random.random() > 0.1 else "en-US",
                            "label": 1 if ("secret" in page or any(sig in agent.lower() for sig in ["python", "scrapy", "curl", "go-http", "wget", "bot"])) else 0
                        }
                        logs.append(entry)

                os.makedirs("data", exist_ok=True)
                with open(LOG_FILE, "w") as f:
                    json.dump(logs, f, indent=2)

                st.success(f"Successfully generated {num_h} human sessions and {num_b} bot sessions and written directly to log database.")
                
            except Exception as e:
                st.error(f"Traffic simulation failed: {e}")

    st.divider()

    st.subheader("Machine Learning Pipeline Compiler")
    st.markdown("Initiate the model compilation workflow. This performs feature engineering extraction, retrains the unsupervised Isolation Forest and supervised XGBoost classifiers, and compiles decision explanation parameters.")

    if st.button("Compile Pipeline & Re-Train Models", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("Step 1/3: Extracting feature engineering properties...")
            progress_bar.progress(33)
            p1 = subprocess.run(["python", "feature_engineering.py"], capture_output=True, text=True)
            
            if p1.returncode != 0:
                st.error(f"Feature engineering failed: {p1.stderr}")
            else:
                status_text.text("Step 2/3: Training models and optimizing consensus ensemble...")
                progress_bar.progress(66)
                p2 = subprocess.run(["python", "train_model.py"], capture_output=True, text=True)
                
                if p2.returncode != 0:
                    st.error(f"Model training failed: {p2.stderr}")
                else:
                    status_text.text("Step 3/3: Recalculating global SHAP significance arrays...")
                    progress_bar.progress(100)
                    p3 = subprocess.run(["python", "explain.py"], capture_output=True, text=True)
                    
                    if p3.returncode != 0:
                        st.error(f"SHAP compilation failed: {p3.stderr}")
                    else:
                        st.balloons()
                        st.success("Consensus model optimization pipeline completed successfully! All predictions, weights, and explanations are updated.")
                        
                        # Clear caching to refresh dashboard
                        st.cache_data.clear()
                        st.rerun()
                        
        except Exception as e:
            st.error(f"Model pipeline execution failed: {e}")
            progress_bar.empty()
            status_text.empty()

st.sidebar.divider()
st.sidebar.caption("Victor v2.0  •  SOC Advanced Edition")