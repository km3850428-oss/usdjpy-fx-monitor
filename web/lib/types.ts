export type Signal = "買い" | "売り" | "待ち";

export interface Judgment {
  signal: Signal;
  overall_score: number;
  technical_score: number;
  fundamental_score: number;
  override_reason: string | null;
}

export interface Indicators {
  price: number;
  sma20: number | null;
  sma50: number | null;
  sma200: number | null;
  rsi14: number | null;
  macd: number | null;
  macd_signal: number | null;
  bb_upper: number | null;
  bb_mid: number | null;
  bb_lower: number | null;
  atr14: number | null;
}

export interface NewsItem {
  title: string;
  link: string | null;
  source: string;
  published_at: string | null;
  sentiment: "bullish" | "bearish" | "neutral";
}

export interface CalendarEvent {
  country: string;
  title: string;
  impact: string;
  time: string;
  forecast: string | null;
  previous: string | null;
  actual: string | null;
}

export interface LatestSnapshot {
  generated_at_jst: string;
  generated_at_utc: string;
  judgment: Judgment;
  technical: {
    reasons: string[];
    indicators: Indicators;
  };
  fundamental: {
    reasons: string[];
    has_upcoming_event: boolean;
  };
  news: {
    items: NewsItem[];
  };
  calendar: {
    caution_window_hours: number;
    display_window_hours: number;
    events: CalendarEvent[];
  };
}

export interface OpenPosition {
  id: number;
  direction: "買い" | "売り";
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  atr_at_entry: number;
  opened_at: string;
}

export interface ClosedPosition extends OpenPosition {
  closed_at: string;
  exit_price: number;
  exit_reason: string;
  pnl_pips: number;
}

export interface PositionsData {
  next_id: number;
  open: OpenPosition[];
  closed: ClosedPosition[];
}

export interface PriceBar {
  t: string;
  o: number;
  h: number;
  l: number;
  c: number;
}

export interface PriceHistory {
  symbol: string;
  interval: string;
  updated_at_utc: string | null;
  max_bars: number;
  bars: PriceBar[];
}
