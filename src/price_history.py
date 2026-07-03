"""複数時間足（15分/30分/1時間）のOHLC履歴をyfinanceから取得し、ローリングJSONとして保存する。

初回はbootstrap_period（timeframeごとの最大取得可能期間）でフル取得し、
2回目以降はincremental_periodのみを取得して既存データにマージする。
未確定足（当該時間内で進行中の足）は次回実行時に同じキーで上書きされ、確定値に更新される。
"""
import json
import os

import yfinance as yf

from . import config


def _file_path(timeframe: str) -> str:
    return os.path.join(config.DATA_DIR, f"price_history_{timeframe}.json")


def _load(timeframe: str):
    path = _file_path(timeframe)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _fetch_bars(interval: str, period: str) -> list:
    df = yf.Ticker(config.YFINANCE_TICKER).history(period=period, interval=interval)
    if df.empty:
        return []
    df = df.tz_convert("UTC")
    bars = []
    for ts, row in df.iterrows():
        bars.append({
            "t": ts.isoformat().replace("+00:00", "Z"),
            "o": round(float(row["Open"]), 4),
            "h": round(float(row["High"]), 4),
            "l": round(float(row["Low"]), 4),
            "c": round(float(row["Close"]), 4),
        })
    return bars


def _merge_bars(existing: list, new: list, max_bars: int) -> list:
    by_time = {b["t"]: b for b in existing}
    for b in new:
        by_time[b["t"]] = b
    merged = sorted(by_time.values(), key=lambda b: b["t"])
    return merged[-max_bars:]


def update_timeframe(timeframe: str, tf_config: dict) -> int:
    """指定timeframeの履歴を更新し、保存後のbar数を返す。"""
    existing = _load(timeframe)
    period = tf_config["incremental_period"] if existing else tf_config["bootstrap_period"]

    new_bars = _fetch_bars(tf_config["interval"], period)
    if not new_bars:
        raise RuntimeError(f"{timeframe}のOHLCデータ取得に失敗しました（空データ）")

    existing_bars = existing["bars"] if existing else []
    merged_bars = _merge_bars(existing_bars, new_bars, tf_config["max_bars"])

    data = {
        "symbol": config.YFINANCE_TICKER,
        "interval": tf_config["interval"],
        "updated_at_utc": merged_bars[-1]["t"] if merged_bars else None,
        "max_bars": tf_config["max_bars"],
        "bars": merged_bars,
    }
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(_file_path(timeframe), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return len(merged_bars)


def update_all():
    """全timeframeを更新する。1つの時間足の失敗が他を止めないよう独立してtry/exceptする。"""
    for timeframe, tf_config in config.INTRADAY_TIMEFRAMES.items():
        try:
            count = update_timeframe(timeframe, tf_config)
            print(f"price_history_{timeframe}.json を更新しました（{count}本）")
        except Exception as exc:
            print(f"{timeframe}足の更新に失敗しました: {exc}")
