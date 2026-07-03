"""エントリーポイント: データ取得→スコアリング→判定→（必要なら）通知。"""
import sys
from datetime import datetime, timezone, timedelta

from . import config, price_data, fundamental, judge as judge_mod, state, notify_discord, positions, latest_snapshot, price_history

JST = timezone(timedelta(hours=9))


def run():
    now_jst = datetime.now(JST)
    timestamp_jst = now_jst.strftime("%Y-%m-%d %H:%M")

    print(f"[{timestamp_jst}] 判定処理を開始します")

    df = price_data.fetch_price_history()
    indicators = price_data.compute_indicators(df)
    technical_score, technical_reasons = price_data.score_technical(indicators)
    print(f"テクニカルスコア: {technical_score:+.3f}")

    fundamental_result = fundamental.score_fundamental()
    fundamental_score = fundamental_result["score"]
    fundamental_reasons = fundamental_result["reasons"]
    has_event = fundamental_result["has_upcoming_event"]
    print(f"ファンダメンタルスコア: {fundamental_score:+.3f}")

    judgment = judge_mod.judge(technical_score, fundamental_score, has_event)
    print(f"判定: {judgment['signal']}（総合スコア {judgment['overall_score']:+.3f}）")

    last_signal = state.load_last_signal()
    is_change = last_signal is not None and last_signal != judgment["signal"]
    is_periodic_hour = now_jst.hour in config.PERIODIC_NOTIFY_HOURS_JST
    is_first_run = last_signal is None

    should_notify = is_change or is_periodic_hour or is_first_run

    if should_notify:
        payload = notify_discord.build_payload(
            judgment, technical_reasons, fundamental_reasons, timestamp_jst,
            is_change=is_change,
        )
        try:
            notify_discord.send(payload)
            print("Discordへ通知を送信しました")
        except Exception as exc:
            print(f"Discord通知に失敗しました: {exc}", file=sys.stderr)
    else:
        print("通知条件に該当しないためスキップします")

    state.save_state(judgment, now_jst.isoformat())

    try:
        snapshot = latest_snapshot.build(
            judgment, indicators, technical_reasons, fundamental_result,
            now_jst.isoformat(), datetime.now(timezone.utc).isoformat(),
        )
        latest_snapshot.save(snapshot)
        print("data/latest.json を更新しました")
    except Exception as exc:
        print(f"data/latest.json の更新に失敗しました: {exc}", file=sys.stderr)

    try:
        price_history.update_all()
    except Exception as exc:
        print(f"価格チャート履歴の更新に失敗しました: {exc}", file=sys.stderr)

    # --- 仮想トレード（ペーパートレード）の決済・エントリー判定 ---
    pos_data = positions.load_positions()

    closed_now = positions.evaluate_open_positions(
        pos_data, indicators["price"], judgment["signal"], now_jst.isoformat()
    )
    for closed_pos in closed_now:
        summary = positions.summary_stats(pos_data)
        print(f"仮想決済: {closed_pos['direction']} {closed_pos['exit_reason']} 損益{closed_pos['pnl_pips']:+.1f}pips")
        try:
            notify_discord.send(notify_discord.build_exit_payload(closed_pos, summary, timestamp_jst))
        except Exception as exc:
            print(f"仮想決済のDiscord通知に失敗しました: {exc}", file=sys.stderr)

    if is_change and judgment["signal"] in ("買い", "売り"):
        atr = indicators.get("atr14")
        if atr is None:
            print("ATRが計算できないため仮想エントリーをスキップします")
        else:
            new_pos = positions.open_position(
                pos_data, judgment["signal"], indicators["price"], atr, now_jst.isoformat()
            )
            print(f"仮想エントリー: {new_pos['direction']} @ {new_pos['entry_price']}")
            try:
                notify_discord.send(notify_discord.build_entry_payload(new_pos, timestamp_jst))
            except Exception as exc:
                print(f"仮想エントリーのDiscord通知に失敗しました: {exc}", file=sys.stderr)

    positions.save_positions(pos_data)


if __name__ == "__main__":
    run()
