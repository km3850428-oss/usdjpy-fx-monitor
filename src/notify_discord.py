"""Discord Webhookへの通知送信。"""
import requests

from . import config

SIGNAL_COLOR = {
    "買い": 0x2ECC71,   # green
    "売り": 0xE74C3C,   # red
    "待ち": 0x95A5A6,   # gray
}


def _truncate(text: str, limit: int = 1000) -> str:
    return text if len(text) <= limit else text[: limit - 3] + "..."


def build_payload(judgment: dict, technical_reasons: list, fundamental_reasons: list,
                   timestamp_jst: str, is_change: bool) -> dict:
    signal = judgment["signal"]
    title_prefix = "【判定変化】" if is_change else "【定期レポート】"
    title = f"{title_prefix} ドル円 {signal}シグナル"

    description = (
        f"総合スコア: **{judgment['overall_score']:+.2f}**"
        f"（テクニカル {judgment['technical_score']:+.2f} / ファンダメンタル {judgment['fundamental_score']:+.2f}）"
    )
    if judgment.get("override_reason"):
        description += f"\n⚠️ {judgment['override_reason']}"

    embed = {
        "title": title,
        "description": description,
        "color": SIGNAL_COLOR.get(signal, 0x95A5A6),
        "fields": [
            {
                "name": "テクニカル根拠",
                "value": _truncate("\n".join(f"・{r}" for r in technical_reasons) or "なし"),
                "inline": False,
            },
            {
                "name": "ファンダメンタル根拠",
                "value": _truncate("\n".join(f"・{r}" for r in fundamental_reasons) or "なし"),
                "inline": False,
            },
        ],
        "footer": {"text": f"判定時刻（JST）: {timestamp_jst}"},
    }
    return {"embeds": [embed]}


def send(payload: dict):
    if not config.DISCORD_WEBHOOK_URL:
        raise RuntimeError("DISCORD_WEBHOOK_URL が設定されていません")
    resp = requests.post(config.DISCORD_WEBHOOK_URL, json=payload, timeout=15)
    resp.raise_for_status()
