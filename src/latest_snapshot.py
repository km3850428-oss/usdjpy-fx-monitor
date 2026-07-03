"""ダッシュボード表示用のスナップショット（判定根拠・indicators・news・calendar）をdata/latest.jsonに保存する。"""
import json
import os

from . import config


def _serialize_calendar_event(ev: dict) -> dict:
    return {**ev, "time": ev["time"].isoformat()}


def build(judgment: dict, indicators: dict, technical_reasons: list,
          fundamental_result: dict, timestamp_jst_iso: str, timestamp_utc_iso: str) -> dict:
    return {
        "generated_at_jst": timestamp_jst_iso,
        "generated_at_utc": timestamp_utc_iso,
        "judgment": judgment,
        "technical": {
            "reasons": technical_reasons,
            "indicators": indicators,
        },
        "fundamental": {
            "reasons": fundamental_result["reasons"],
            "has_upcoming_event": fundamental_result["has_upcoming_event"],
        },
        "news": {
            "items": fundamental_result["news_headlines"],
        },
        "calendar": {
            "caution_window_hours": config.EVENT_CAUTION_WINDOW_HOURS,
            "display_window_hours": config.CALENDAR_DISPLAY_WINDOW_HOURS,
            "events": [_serialize_calendar_event(ev) for ev in fundamental_result["calendar_events"]],
        },
    }


def save(snapshot: dict):
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(config.LATEST_FILE, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
