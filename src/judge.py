"""テクニカル・ファンダメンタルスコアを統合し、最終判定を行う。"""
from . import config


def judge(technical_score: float, fundamental_score: float, has_upcoming_event: bool):
    overall_score = (
        technical_score * config.TECHNICAL_WEIGHT
        + fundamental_score * config.FUNDAMENTAL_WEIGHT
    )

    if has_upcoming_event:
        signal = "待ち"
        override_reason = "重要指標発表が近いためスコアに関わらず待ちと判定"
    elif overall_score >= config.BUY_THRESHOLD:
        signal = "買い"
        override_reason = None
    elif overall_score <= config.SELL_THRESHOLD:
        signal = "売り"
        override_reason = None
    else:
        signal = "待ち"
        override_reason = None

    return {
        "signal": signal,
        "overall_score": round(overall_score, 3),
        "technical_score": round(technical_score, 3),
        "fundamental_score": round(fundamental_score, 3),
        "override_reason": override_reason,
    }
