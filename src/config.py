"""設定値の一元管理。"""
import os

# --- 通知 ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

# 定期通知を送る時刻（JST, 24時間表記）。この時刻を含む実行回で必ず通知する。
PERIODIC_NOTIFY_HOURS_JST = {9, 12, 18}

# --- スコアリング ---
# テクニカル / ファンダメンタルの重み（合計1.0）
TECHNICAL_WEIGHT = 0.5
FUNDAMENTAL_WEIGHT = 0.5

# 総合スコア（-1.0〜+1.0）がこの値を超えたら買い/売り、それ以外は待ち
BUY_THRESHOLD = 0.3
SELL_THRESHOLD = -0.3

# 主要指標発表がこの時間内（時間）に迫っている場合はスコアに関わらず「待ち」とする
EVENT_CAUTION_WINDOW_HOURS = 3

# --- 金利（BOJ政策金利は変更頻度が低いため手動更新） ---
# 更新日: 2025-01（日銀の追加利上げ後の水準）。日銀会合で変更があれば手動で書き換える。
BOJ_POLICY_RATE = 0.5

# FRED APIキー（任意）。未設定でも動作するが、米金利差の自動取得は無効になる。
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

# --- データ取得 ---
YFINANCE_TICKER = "JPY=X"  # USD/JPY
PRICE_HISTORY_PERIOD = "6mo"
PRICE_HISTORY_INTERVAL = "1d"

NEWS_RSS_FEEDS = [
    "https://www.investing.com/rss/news_285.rss",  # Forex news
    "https://jp.reuters.com/arc/outboundfeeds/v3/category/business/",
]

# ForexFactory の週間経済指標カレンダー（公開JSONエンドポイント、キー不要）
FOREX_CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

# --- 状態保存 ---
STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "state.json")
