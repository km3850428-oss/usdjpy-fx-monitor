"""エントリーポイント: データ取得→スコアリング→判定→（必要なら）通知。"""
import sys
from datetime import datetime, timezone, timedelta

from . import config, price_data, fundamental, judge as judge_mod, state, notify_discord

JST = timezone(timedelta(hours=9))


def run():
    now_jst = datetime.now(JST)
    timestamp_jst = now_jst.strftime("%Y-%m-%d %H:%M")

    print(f"[{timestamp_jst}] 判定処理を開始します")

    df = price_data.fetch_price_history()
    indicators = price_data.compute_indicators(df)
    technical_score, technical_reasons = price_data.score_technical(indicators)
    print(f"テクニカルスコア: {technical_score:+.3f}")

    fundamental_score, fundamental_reasons, has_event = fundamental.score_fundamental()
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


if __name__ == "__main__":
    run()
