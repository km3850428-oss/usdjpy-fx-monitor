"""ファンダメンタル要因（金利差・ニュース・経済指標カレンダー）の取得とスコアリング。"""
from datetime import datetime, timezone, timedelta

import requests
import feedparser

from . import config

USD_BULLISH_KEYWORDS = [
    "rate hike", "hawkish", "利上げ", "タカ派", "強いドル", "ドル高",
    "rate increase", "inflation surge",
]
USD_BEARISH_KEYWORDS = [
    "rate cut", "dovish", "利下げ", "ハト派", "為替介入", "intervention",
    "円高", "safe haven", "risk-off", "recession",
]


def fetch_rate_differential_score():
    """米10年債利回りと日本長期金利の差から金利差スコアを算出する。FREDキー未設定時はNoneを返す。"""
    if not config.FRED_API_KEY:
        return None, "FRED APIキー未設定のため金利差の自動評価をスキップ"

    try:
        resp = requests.get(
            "https://api.stlouisfed.org/fred/series/observations",
            params={
                "series_id": "DGS10",
                "api_key": config.FRED_API_KEY,
                "file_type": "json",
                "sort_order": "desc",
                "limit": 1,
            },
            timeout=15,
        )
        resp.raise_for_status()
        us_10y = float(resp.json()["observations"][0]["value"])
    except Exception as exc:
        return None, f"米金利データの取得に失敗: {exc}"

    jp_policy = config.BOJ_POLICY_RATE
    diff = us_10y - jp_policy
    # 金利差が大きいほどドル買い（円安）要因。5%を最大とみなし-1〜+1に正規化
    score = max(-1.0, min(1.0, diff / 5.0))
    reason = f"米10年債利回り{us_10y:.2f}% と日銀政策金利{jp_policy:.2f}%の差は{diff:.2f}pt（{'ドル買い' if diff > 0 else 'ドル売り'}要因）"
    return score, reason


def fetch_news_sentiment_score():
    """RSSニュース見出しのキーワードから簡易センチメントスコアを算出する。"""
    bullish_hits = []
    bearish_hits = []

    for url in config.NEWS_RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
        except Exception:
            continue
        for entry in feed.entries[:20]:
            title = getattr(entry, "title", "") or ""
            title_lower = title.lower()
            for kw in USD_BULLISH_KEYWORDS:
                if kw.lower() in title_lower:
                    bullish_hits.append(title)
                    break
            for kw in USD_BEARISH_KEYWORDS:
                if kw.lower() in title_lower:
                    bearish_hits.append(title)
                    break

    total = len(bullish_hits) + len(bearish_hits)
    if total == 0:
        return 0.0, "関連ニュース見出しにドル/円方向を示すキーワードなし（中立）"

    score = (len(bullish_hits) - len(bearish_hits)) / total
    reason = f"ニュース見出し {len(bullish_hits)}件がドル買い方向、{len(bearish_hits)}件がドル売り方向のキーワードを含む"
    return max(-1.0, min(1.0, score)), reason


def fetch_upcoming_high_impact_event():
    """USD/JPY関連の重要指標発表が警戒時間内に迫っていないか確認する。"""
    try:
        resp = requests.get(config.FOREX_CALENDAR_URL, timeout=15)
        resp.raise_for_status()
        events = resp.json()
    except Exception as exc:
        return None, f"経済指標カレンダーの取得に失敗: {exc}"

    now = datetime.now(timezone.utc)
    window_end = now + timedelta(hours=config.EVENT_CAUTION_WINDOW_HOURS)

    upcoming = []
    for ev in events:
        if ev.get("country") not in ("USD", "JPY"):
            continue
        if ev.get("impact") != "High":
            continue
        try:
            ev_time = datetime.fromisoformat(ev["date"])
        except Exception:
            continue
        if ev_time.tzinfo is None:
            ev_time = ev_time.replace(tzinfo=timezone.utc)
        if now <= ev_time <= window_end:
            upcoming.append(f"{ev.get('country')} {ev.get('title')} ({ev_time.strftime('%m/%d %H:%M UTC')})")

    if upcoming:
        return True, "今後" + str(config.EVENT_CAUTION_WINDOW_HOURS) + "時間以内の重要指標: " + " / ".join(upcoming)
    return False, "直近の重要指標発表なし"


def score_fundamental():
    scores = []
    reasons = []

    rate_score, rate_reason = fetch_rate_differential_score()
    reasons.append(rate_reason)
    if rate_score is not None:
        scores.append(rate_score)

    news_score, news_reason = fetch_news_sentiment_score()
    reasons.append(news_reason)
    scores.append(news_score)

    has_event, event_reason = fetch_upcoming_high_impact_event()
    reasons.append(event_reason)

    fundamental_score = sum(scores) / len(scores) if scores else 0.0
    return max(-1.0, min(1.0, fundamental_score)), reasons, bool(has_event)
