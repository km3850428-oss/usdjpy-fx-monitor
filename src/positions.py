"""仮想トレード（ペーパートレード）のポジション管理。

エントリーは判定が「買い」「売り」に新しく変化した時点で自動的に仮想オープンする。
決済（利確・損切り・シグナル反転）を毎回チェックし、条件を満たしたものを自動でクローズする。
実際の売買は行わず、あくまで通知のための架空シミュレーション。
"""
import json
import os

from . import config


def _default_data():
    return {"next_id": 1, "open": [], "closed": []}


def load_positions() -> dict:
    if not os.path.exists(config.POSITIONS_FILE):
        return _default_data()
    try:
        with open(config.POSITIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("next_id", 1)
        data.setdefault("open", [])
        data.setdefault("closed", [])
        return data
    except Exception:
        return _default_data()


def save_positions(data: dict):
    data["closed"] = data["closed"][-config.MAX_CLOSED_HISTORY:]
    with open(config.POSITIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def open_position(data: dict, direction: str, entry_price: float, atr: float, timestamp_iso: str) -> dict:
    sl_distance = atr * config.ATR_STOP_LOSS_MULTIPLIER
    tp_distance = atr * config.ATR_TAKE_PROFIT_MULTIPLIER

    if direction == "買い":
        stop_loss = entry_price - sl_distance
        take_profit = entry_price + tp_distance
    else:  # 売り
        stop_loss = entry_price + sl_distance
        take_profit = entry_price - tp_distance

    position = {
        "id": data["next_id"],
        "direction": direction,
        "entry_price": round(entry_price, 3),
        "stop_loss": round(stop_loss, 3),
        "take_profit": round(take_profit, 3),
        "atr_at_entry": round(atr, 3),
        "opened_at": timestamp_iso,
    }
    data["next_id"] += 1
    data["open"].append(position)
    return position


def _pnl_pips(direction: str, entry_price: float, exit_price: float) -> float:
    diff = exit_price - entry_price
    if direction == "売り":
        diff = -diff
    return round(diff / config.PIP_SIZE, 1)


def evaluate_open_positions(data: dict, current_price: float, current_signal: str, timestamp_iso: str) -> list:
    """保有中の仮想ポジションを判定し、決済条件を満たしたものをクローズする。クローズしたポジションのリストを返す。"""
    still_open = []
    closed_now = []

    for pos in data["open"]:
        exit_reason = None
        exit_price = current_price

        if pos["direction"] == "買い":
            if current_price >= pos["take_profit"]:
                exit_reason = "利確（目標値到達）"
                exit_price = pos["take_profit"]
            elif current_price <= pos["stop_loss"]:
                exit_reason = "損切り"
                exit_price = pos["stop_loss"]
            elif current_signal == "売り":
                exit_reason = "シグナル反転による決済"
        else:  # 売り
            if current_price <= pos["take_profit"]:
                exit_reason = "利確（目標値到達）"
                exit_price = pos["take_profit"]
            elif current_price >= pos["stop_loss"]:
                exit_reason = "損切り"
                exit_price = pos["stop_loss"]
            elif current_signal == "買い":
                exit_reason = "シグナル反転による決済"

        if exit_reason:
            closed_pos = {
                **pos,
                "closed_at": timestamp_iso,
                "exit_price": round(exit_price, 3),
                "exit_reason": exit_reason,
                "pnl_pips": _pnl_pips(pos["direction"], pos["entry_price"], exit_price),
            }
            data["closed"].append(closed_pos)
            closed_now.append(closed_pos)
        else:
            still_open.append(pos)

    data["open"] = still_open
    return closed_now


def summary_stats(data: dict) -> dict:
    closed = data["closed"]
    total = len(closed)
    wins = sum(1 for p in closed if p["pnl_pips"] > 0)
    cumulative_pips = round(sum(p["pnl_pips"] for p in closed), 1)
    win_rate = round(wins / total * 100, 1) if total else 0.0
    return {"total": total, "wins": wins, "win_rate": win_rate, "cumulative_pips": cumulative_pips}
