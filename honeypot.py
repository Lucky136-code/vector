# honeypot.py
# updated — now auto-labels bots based on their user agent
# so we don't have to manually pass a label every time

from flask import Flask, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

LOG_FILE = "data/traffic_logs.json"

# these are the user agent signatures our simulated bots use
# any request matching these gets auto-labeled as bot (label=1)
BOT_SIGNATURES = [
    "python-requests", "scrapy", "curl", "go-http-client",
    "wget", "bot", "crawl", "spider"
]

def detect_label():
    # check if the user agent gives away that this is a bot
    ua = request.headers.get("User-Agent", "").lower()
    
    # if it matches any known bot signature → label 1 (bot)
    if any(sig in ua for sig in BOT_SIGNATURES):
        return 1
    
    # if it hits the secret honeypot page → almost certainly a bot
    if "secret" in request.path:
        return 1
    
    # otherwise assume human
    return 0

def log_request():
    label = detect_label()

    log_entry = {
        "timestamp"   : datetime.now().isoformat(),
        "ip"          : request.remote_addr,
        "method"      : request.method,
        "path"        : request.path,
        "user_agent"  : request.headers.get("User-Agent", "unknown"),
        "referer"     : request.headers.get("Referer", "none"),
        "accept_lang" : request.headers.get("Accept-Language", "none"),
        "label"       : label
    }

    if not os.path.exists(LOG_FILE):
        logs = []
    else:
        with open(LOG_FILE, "r") as f:
            logs = json.load(f)

    logs.append(log_entry)

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)

    return log_entry


@app.route("/")
def home():
    log_request()
    return "<h1>Welcome to VictorSite</h1><p>A totally normal website.</p>"

@app.route("/articles")
def articles():
    log_request()
    return "<h1>Articles</h1><p>Interesting content here.</p>"

@app.route("/about")
def about():
    log_request()
    return "<h1>About Us</h1><p>We make stuff.</p>"

@app.route("/secret-data")
def secret():
    log_request()
    return jsonify({"data": "nothing here, gotcha"})

@app.route("/api/log", methods=["POST"])
def receive_log():
    entry = log_request()
    return jsonify({"status": "logged", "entry": entry})


if __name__ == "__main__":
    print("Victor Honeypot is running on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)