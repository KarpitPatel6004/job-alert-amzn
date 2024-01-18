import os
import requests

TOKEN = os.environ["TELE_TOKEN"]
CHAT_IDS = os.environ["IDS"].split(',')

def send_test_alert():
    url = f"https://api.telegram.org/bot{TOKEN}"
    for chat_id in CHAT_IDS:
        params = {"chat_id": chat_id, "text": "This is a test message"}
        r = requests.get(url + "/sendMessage", params=params)

        if r.status_code != 200:
            print("Could not send an alert")

send_test_alert()