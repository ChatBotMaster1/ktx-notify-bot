import os

import requests


def _call(method, **params):
    url = f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/{method}"
    r = requests.post(url, json=params, timeout=30)
    r.raise_for_status()
    return r.json()["result"]


def send(text):
    _call("sendMessage", chat_id=os.environ["TELEGRAM_CHAT_ID"], text=text)


def get_updates(offset):
    return _call("getUpdates", offset=offset, timeout=0)
