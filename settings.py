import json
import os

SETTINGS_DIR = os.path.expanduser("~/.invoicer")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")


def load_settings() -> dict:
    if not os.path.exists(SETTINGS_FILE):
        return {"last_invoice_number": 1}
    with open(SETTINGS_FILE, "r") as f:
        return json.load(f)


def save_settings(data: dict):
    os.makedirs(SETTINGS_DIR, exist_ok=True)
    existing = load_settings()
    existing.update(data)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(existing, f, indent=2)
