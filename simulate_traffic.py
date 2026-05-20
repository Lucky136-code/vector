# simulate_traffic.py
# faster version — reduced sleep times so simulation finishes in ~30 seconds
# the timing patterns still differ enough for Victor to learn from

import requests
import time
import random
from faker import Faker

fake = Faker()

BASE_URL = "http://127.0.0.1:5000"

HUMAN_PAGES = ["/", "/articles", "/about"]
BOT_PAGES   = ["/", "/articles", "/about", "/secret-data", "/secret-data", "/secret-data"]


def simulate_human(num_sessions=40):
    print("Simulating human traffic...")

    for i in range(num_sessions):
        pages = random.sample(HUMAN_PAGES, k=random.randint(2, 3))

        for page in pages:
            try:
                requests.get(
                    BASE_URL + page,
                    headers={
                        "User-Agent"      : fake.user_agent(),
                        "Referer"         : "https://google.com",
                        "Accept-Language" : "en-US,en;q=0.9"
                    },
                    timeout=3
                )
            except Exception as e:
                print(f"  Error: {e}")

            # reduced from 2–6s to 0.3–0.8s — still slower than bots
            time.sleep(random.uniform(0.3, 0.8))

        # reduced gap between sessions
        time.sleep(random.uniform(0.2, 0.5))

        # progress update every 10 sessions so you know it's running
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{num_sessions} human sessions done...")

    print(f"Done — {num_sessions} human sessions logged.")


def simulate_bot(num_sessions=40):
    print("\nSimulating bot traffic...")

    bot_agents = [
        "python-requests/2.28.0",
        "Scrapy/2.11.0 (+https://scrapy.org)",
        "curl/7.88.1",
        "Mozilla/5.0 (compatible; Googlebot/2.1)",
        "Go-http-client/1.1"
    ]

    for i in range(num_sessions):
        for page in BOT_PAGES:
            try:
                requests.get(
                    BASE_URL + page,
                    headers={"User-Agent": random.choice(bot_agents)},
                    timeout=3
                )
            except Exception as e:
                print(f"  Error: {e}")

            # bots are fast — barely any pause
            time.sleep(random.uniform(0.01, 0.05))

        time.sleep(random.uniform(0.05, 0.15))

        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{num_sessions} bot sessions done...")

    print(f"Done — {num_sessions} bot sessions logged.")


if __name__ == "__main__":
    print("Starting Victor traffic simulation...\n")
    simulate_human(num_sessions=40)
    simulate_bot(num_sessions=40)
    print("\nAll done! Check data/traffic_logs.json for your dataset.")