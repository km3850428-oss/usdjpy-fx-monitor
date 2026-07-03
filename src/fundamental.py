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


def fetch_news_headlines(limit_per_feed: int = None) -> list:
    """RSSニュース見出しを正規化して返す（表示用・センチメント判定用の両方に使う）。"""
    limit_per_feed = limit_per_feed or config.NEWS_HEADLINES_LIMIT_PER_FEED
    headlines = []

    for url in config.NEWS_RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
        except Exception:
            continue
        source = getattr(feed.feed, "title", "") or url
        for entry in feed.entries[:limit_per_feed]:
            title = getattr(entry, "title", "") or ""
            if not title:
                continue
            title_lower = title.lower()
            sentiment = "neutral"
            if any(kw.lower() in title_lower for kw in USD_BULLISH_KEYWORDS):
                sentiment = "bullish"
            elif any(kw.lower() in title_lower for kw in USD_BEARISH_KEYWORDS):
                sentiment = "bearish"

            published_at = getattr(entry, "published", None)
            headlines.append({
                "title": title,
                "link": getattr(entry, "link", None),
                "source": source,
                "published_at": published_at,
                "sentiment": sentiment,
            })

    return headlines


def fetch_news_sentiment_score(headlines: list = None):
    """ニュース見出しのセンチメント（bullish/bearish件数）から簡易スコアを算出する。"""
    if headlines is None:
        headlines = fetch_news_headlines()

    bullish_hits = [h for h in headlines if h["sentiment"] == "bullish"]
    bearish_hits = [h for h in headlines if h["sentiment"] == "bearish"]

    total = len(bullish_hits) + len(bearish_hits)
    if total == 0:
        return 0.0, "関連ニュース見出しにドル/円方向を示すキーワードなし（中立）"

    score = (len(bullish_hits) - len(bearish_hits)) / total
    reason = f"ニュース見出し {len(bullish_hits)}件がドル買い方向、{len(bearish_hits)}件がドル売り方向のキーワードを含む"
    return max(-1.0, min(1.0, score)), reason


def fetch_calendar_events() -> list:
    """ForexFactoryの週間経済指標カレンダーから生のイベント一覧を取得・正規化する。取得失敗時は空リスト。"""
    try:
        resp = requests.get(config.FOREX_CALENDAR_URL, timeout=15)
        resp.raise_for_status()
        raw_events = resp.json()
    except Exception:
        return []

    events = []
    for ev in raw_events:
        try:
            ev_time = datetime.fromisoformat(ev["date"])
        except Exception:
            continue
        if ev_time.tzinfo is None:
            ev_time = ev_time.replace(tzinfo=timezone.utc)
        events.append({
            "country": ev.get("country"),
            "title": ev.get("title"),
            "impact": ev.get("impact"),
            "time": ev_time,
            "forecast": ev.get("forecast"),
            "previous": ev.get("previous"),
            "actual": ev.get("actual"),
        })
    return events


def filter_high_impact_within_window(events: list, hours: int):
    """USD/JPY関連の重要指標発表が警戒時間内に迫っていないか判定する（judge()向け）。"""
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(hours=hours)

    upcoming = [
        ev for ev in events
        if ev["country"] in ("USD", "JPY") and ev["impact"] == "High" and now <= ev["time"] <= window_end
    ]

    if upcoming:
        labels = [f"{ev['country']} {ev['title']} ({ev['time'].strftime('%m/%d %H:%M UTC')})" for ev in upcoming]
        return True, f"今後{hours}時間以内の重要指標: " + " / ".join(labels)
    return False, "直近の重要指標発表なし"


def filter_events_for_display(events: list, hours: int, countries=("USD", "JPY"), min_impact=None) -> list:
    """ダッシュボード表示用に、より広い時間窓でイベント一覧を返す（過去分は含めない）。"""
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(hours=hours)

    impacts_order = {"Low": 0, "Medium": 1, "High": 2}
    min_rank = impacts_order.get(min_impact, -1) if min_impact else -1

    display = [
        ev for ev in events
        if ev["country"] in countries
        and now <= ev["time"] <= window_end
        and impacts_order.get(ev["impact"], -1) >= min_rank
    ]
    return sorted(display, key=lambda ev: ev["time"])


def score_fundamental() -> dict:
    scores = []
    reasons = []

    rate_score, rate_reason = fetch_rate_differential_score()
    reasons.append(rate_reason)
    if rate_score is not None:
        scores.append(rate_score)

    headlines = fetch_news_headlines()
    news_score, news_reason = fetch_news_sentiment_score(headlines)
    reasons.append(news_reason)
    scores.append(news_score)

    calendar_events = fetch_calendar_events()
    has_event, event_reason = filter_high_impact_within_window(calendar_events, config.EVENT_CAUTION_WINDOW_HOURS)
    reasons.append(event_reason)
    display_events = filter_events_for_display(calendar_events, config.CALENDAR_DISPLAY_WINDOW_HOURS)

    fundamental_score = sum(scores) / len(scores) if scores else 0.0
    return {
        "score": max(-1.0, min(1.0, fundamental_score)),
        "reasons": reasons,
        "has_upcoming_event": bool(has_event),
        "news_headlines": headlines,
        "calendar_events": display_events,
    }
