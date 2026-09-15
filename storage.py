import json
from pathlib import Path

PATH = Path(__file__).with_name("data.json")


def load():
    if PATH.exists():
        return json.loads(PATH.read_text(encoding="utf-8"))
    return {"last_update_id": 0, "next_id": 1, "watches": []}


def save(data):
    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
