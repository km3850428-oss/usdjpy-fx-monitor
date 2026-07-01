"""前回判定の保存・読み込み（変化検知に使用）。"""
import json
import os

from . import config


def load_last_signal():
    if not os.path.exists(config.STATE_FILE):
        return None
    try:
        with open(config.STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("signal")
    except Exception:
        return None


def save_state(judgment: dict, timestamp_iso: str):
    data = {**judgment, "timestamp": timestamp_iso}
    with open(config.STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
