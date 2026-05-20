# honeypot.py  —  Victor's honeypot server
# Runs a realistic-looking Flask site that silently logs every request.
# Humans see a styled page; bots see responses too but get fingerprinted.
# Run:  python honeypot.py

from flask import Flask, request, jsonify, make_response
import json, os
from datetime import datetime

app = Flask(__name__)

LOG_FILE = "data/traffic_logs.json"

# Known bot user-agent signatures
BOT_SIGNATURES = [
    "python-requests", "scrapy", "curl", "go-http-client",
    "wget", "bot", "crawl", "spider"
]

# ─────────────────────────────────────────────────────────────────
# Shared HTML template  —  styled dark theme
# ─────────────────────────────────────────────────────────────────

def html_page(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — VictorSite</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: 'Segoe UI', system-ui, sans-serif;
      background: #0a0e1a;
      color: #e2e8f0;
      min-height: 100vh;
    }}
    nav {{
      background: rgba(15,23,41,0.95);
      border-bottom: 1px solid rgba(99,102,241,0.25);
      padding: 14px 40px;
      display: flex;
      align-items: center;
      gap: 32px;
    }}
    nav .logo {{
      color: #818cf8;
      font-weight: 800;
      font-size: 1.2rem;
      text-decoration: none;
    }}
    nav a {{
      color: #94a3b8;
      text-decoration: none;
      font-size: 0.9rem;
      transition: color 0.2s;
    }}
    nav a:hover {{ color: #c7d2fe; }}
    .hero {{
      max-width: 860px;
      margin: 80px auto 0;
      padding: 0 24px;
    }}
    .hero h1 {{
      font-size: 2.4rem;
      font-weight: 800;
      background: linear-gradient(135deg, #818cf8, #6366f1);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 16px;
    }}
    .hero p {{
      color: #94a3b8;
      font-size: 1.05rem;
      line-height: 1.7;
      margin-bottom: 12px;
    }}
    .card {{
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(99,102,241,0.2);
      border-radius: 14px;
      padding: 24px 28px;
      margin-top: 24px;
    }}
    .card h2 {{
      color: #a5b4fc;
      margin-bottom: 10px;
      font-size: 1.1rem;
    }}
    footer {{
      text-align: center;
      color: #334155;
      font-size: 0.78rem;
      padding: 40px 0;
      margin-top: 80px;
    }}
  </style>
</head>
<body>
  <nav>
    <a class="logo" href="/">🛡️ VictorSite</a>
    <a href="/">Home</a>
    <a href="/articles">Articles</a>
    <a href="/about">About</a>
  </nav>
  <div class="hero">
    <h1>{title}</h1>
    {body}
  </div>
  <footer>© 2025 VictorSite · Powered by Victor Bot Detection</footer>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────
# Logging helpers
# ─────────────────────────────────────────────────────────────────

def detect_label() -> int:
    ua = request.headers.get("User-Agent", "").lower()
    if any(sig in ua for sig in BOT_SIGNATURES):
        return 1
    if "secret" in request.path:
        return 1
    return 0


def log_request() -> dict:
    os.makedirs("data", exist_ok=True)
    label = detect_label()

    entry = {
        "timestamp"  : datetime.now().isoformat(),
        "ip"         : request.remote_addr,
        "method"     : request.method,
        "path"       : request.path,
        "user_agent" : request.headers.get("User-Agent", "unknown"),
        "referer"    : request.headers.get("Referer", "none"),
        "accept_lang": request.headers.get("Accept-Language", "none"),
        "label"      : label
    }

    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []

    logs.append(entry)
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)

    return entry


# ─────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    log_request()
    body = """
    <p>Welcome to VictorSite — a totally normal technology blog. We write about AI, security, and the web.</p>
    <div class="card">
      <h2>Latest Posts</h2>
      <p>→ <a href="/articles" style="color:#818cf8">How LLMs are changing threat detection</a></p>
      <p>→ <a href="/articles" style="color:#818cf8">Why bots are harder to detect in 2025</a></p>
    </div>
    """
    return make_response(html_page("Home", body))


@app.route("/articles")
def articles():
    log_request()
    body = """
    <p>A curated collection of articles on AI security, web scraping ethics, and behavioral analysis.</p>
    <div class="card">
      <h2>Featured</h2>
      <p>→ Understanding Isolation Forests for anomaly detection</p>
      <p>→ XGBoost vs Random Forest: which wins at fingerprinting?</p>
      <p>→ SHAP: the tool that makes ML explainable</p>
    </div>
    """
    return make_response(html_page("Articles", body))


@app.route("/about")
def about():
    log_request()
    body = """
    <p>VictorSite is a research honeypot designed to study bot vs human traffic patterns using ensemble ML.</p>
    <div class="card">
      <h2>The Stack</h2>
      <p>Flask · XGBoost · Isolation Forest · SHAP · Streamlit</p>
    </div>
    """
    return make_response(html_page("About", body))


@app.route("/secret-data")
def secret():
    log_request()
    # bots will find this; humans almost never click unlisted URLs
    return jsonify({"data": "nothing here — but we logged you 👀", "status": "honeypot"})


@app.route("/health")
def health():
    """Simple health check — useful for monitoring."""
    log_count = 0
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            try:
                log_count = len(json.load(f))
            except Exception:
                log_count = -1
    return jsonify({"status": "ok", "logs_collected": log_count})


@app.route("/api/log", methods=["POST"])
def receive_log():
    entry = log_request()
    return jsonify({"status": "logged", "entry": entry})


# ─────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    print("Victor Honeypot running  ->  http://127.0.0.1:5000")
    print("Endpoints: /  /articles  /about  /secret-data  /health")
    app.run(debug=True, port=5000)