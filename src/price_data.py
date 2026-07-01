"""価格データの取得とテクニカル指標のスコアリング。"""
import yfinance as yf
import pandas as pd

from . import config


def fetch_price_history() -> pd.DataFrame:
    df = yf.Ticker(config.YFINANCE_TICKER).history(
        period=config.PRICE_HISTORY_PERIOD,
        interval=config.PRICE_HISTORY_INTERVAL,
    )
    if df.empty:
        raise RuntimeError("価格データの取得に失敗しました（yfinanceが空データを返しました）")
    return df


def _sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window).mean()


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-9)
    return 100 - (100 / (1 + rs))


def _macd(series: pd.Series):
    ema12 = series.ewm(span=12, adjust=False).mean()
    ema26 = series.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    return macd_line, signal_line


def _bollinger(series: pd.Series, window: int = 20, num_std: float = 2.0):
    mid = _sma(series, window)
    std = series.rolling(window=window).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return upper, mid, lower


def compute_indicators(df: pd.DataFrame) -> dict:
    close = df["Close"]

    sma20 = _sma(close, 20)
    sma50 = _sma(close, 50)
    sma200 = _sma(close, 200)
    rsi14 = _rsi(close, 14)
    macd_line, signal_line = _macd(close)
    bb_upper, bb_mid, bb_lower = _bollinger(close)

    return {
        "price": float(close.iloc[-1]),
        "sma20": float(sma20.iloc[-1]) if pd.notna(sma20.iloc[-1]) else None,
        "sma50": float(sma50.iloc[-1]) if pd.notna(sma50.iloc[-1]) else None,
        "sma200": float(sma200.iloc[-1]) if pd.notna(sma200.iloc[-1]) else None,
        "rsi14": float(rsi14.iloc[-1]) if pd.notna(rsi14.iloc[-1]) else None,
        "macd": float(macd_line.iloc[-1]) if pd.notna(macd_line.iloc[-1]) else None,
        "macd_signal": float(signal_line.iloc[-1]) if pd.notna(signal_line.iloc[-1]) else None,
        "bb_upper": float(bb_upper.iloc[-1]) if pd.notna(bb_upper.iloc[-1]) else None,
        "bb_mid": float(bb_mid.iloc[-1]) if pd.notna(bb_mid.iloc[-1]) else None,
        "bb_lower": float(bb_lower.iloc[-1]) if pd.notna(bb_lower.iloc[-1]) else None,
    }


def score_technical(indicators: dict):
    """各指標を-1.0〜+1.0でスコア化し、平均値と根拠リストを返す。"""
    scores = []
    reasons = []

    price = indicators["price"]

    # 移動平均線トレンド（短期>中期>長期なら強気）
    sma20, sma50, sma200 = indicators["sma20"], indicators["sma50"], indicators["sma200"]
    if sma20 is not None and sma50 is not None:
        if sma20 > sma50:
            ma_score = 1.0
            reasons.append(f"SMA20({sma20:.2f}) > SMA50({sma50:.2f}) でゴールデンクロス状態（買い要因）")
        else:
            ma_score = -1.0
            reasons.append(f"SMA20({sma20:.2f}) < SMA50({sma50:.2f}) でデッドクロス状態（売り要因）")
        if sma200 is not None:
            if price > sma200:
                reasons.append(f"価格({price:.2f})はSMA200({sma200:.2f})より上位＝長期トレンドは上向き")
            else:
                ma_score -= 0.3
                reasons.append(f"価格({price:.2f})はSMA200({sma200:.2f})より下位＝長期トレンドは下向き")
        scores.append(max(-1.0, min(1.0, ma_score)))

    # RSI
    rsi = indicators["rsi14"]
    if rsi is not None:
        if rsi >= 70:
            rsi_score = -1.0
            reasons.append(f"RSI14={rsi:.1f}で買われすぎ水準（売り/待ち要因）")
        elif rsi <= 30:
            rsi_score = 1.0
            reasons.append(f"RSI14={rsi:.1f}で売られすぎ水準（買い要因）")
        else:
            rsi_score = (rsi - 50) / 20  # 50を中立として緩やかに傾斜
            reasons.append(f"RSI14={rsi:.1f}で中立圏")
        scores.append(max(-1.0, min(1.0, rsi_score)))

    # MACD
    macd, macd_signal = indicators["macd"], indicators["macd_signal"]
    if macd is not None and macd_signal is not None:
        if macd > macd_signal:
            scores.append(1.0)
            reasons.append("MACDがシグナルを上抜け（買い要因）")
        else:
            scores.append(-1.0)
            reasons.append("MACDがシグナルを下抜け（売り要因）")

    # ボリンジャーバンド
    bb_upper, bb_lower = indicators["bb_upper"], indicators["bb_lower"]
    if bb_upper is not None and bb_lower is not None:
        band_width = bb_upper - bb_lower
        if band_width > 0:
            if price >= bb_upper:
                scores.append(-0.7)
                reasons.append("価格がボリンジャーバンド+2σを上回り過熱感（売り/待ち要因）")
            elif price <= bb_lower:
                scores.append(0.7)
                reasons.append("価格がボリンジャーバンド-2σを下回り売られすぎ（買い要因）")

    if not scores:
        return 0.0, ["テクニカル指標を計算するためのデータが不足しています"]

    technical_score = sum(scores) / len(scores)
    return max(-1.0, min(1.0, technical_score)), reasons
