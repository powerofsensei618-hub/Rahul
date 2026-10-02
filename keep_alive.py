import os
import time
import requests

API_URL = os.environ.get("KEEP_ALIVE_URL", "https://youtube-6kes.onrender.com")


def keep_awake():
    while True:
        try:
            response = requests.get(API_URL, timeout=30)
            print(f"Pinged {API_URL}: {response.status_code}", flush=True)
        except Exception as e:
            print(f"Error: {e}", flush=True)

        time.sleep(300)  # every 5 minutes


if __name__ == "__main__":
    keep_awake()
