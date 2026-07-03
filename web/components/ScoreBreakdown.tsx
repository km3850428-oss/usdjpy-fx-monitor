import type { LatestSnapshot } from "@/lib/types";

function scoreStatusClass(score: number): "status-good" | "status-critical" | "" {
  if (score > 0.1) return "status-good";
  if (score < -0.1) return "status-critical";
  return "";
}

function fmt(value: number | null, digits = 2): string {
  return value === null ? "—" : value.toFixed(digits);
}

export default function ScoreBreakdown({ snapshot }: { snapshot: LatestSnapshot }) {
  const { judgment, technical, fundamental } = snapshot;
  const ind = technical.indicators;

  return (
    <section className="panel">
      <span className="panel-title">スコア内訳</span>

      <div className="kpi-row">
        <div className="kpi-tile">
          <span className="kpi-label">総合スコア</span>
          <span className={`kpi-value ${scoreStatusClass(judgment.overall_score)}`}>
            {fmt(judgment.overall_score, 3)}
          </span>
        </div>
        <div className="kpi-tile">
          <span className="kpi-label">テクニカル</span>
          <span className={`kpi-value ${scoreStatusClass(judgment.technical_score)}`}>
            {fmt(judgment.technical_score, 3)}
          </span>
        </div>
        <div className="kpi-tile">
          <span className="kpi-label">ファンダメンタル</span>
          <span className={`kpi-value ${scoreStatusClass(judgment.fundamental_score)}`}>
            {fmt(judgment.fundamental_score, 3)}
          </span>
        </div>
      </div>

      <div className="kpi-row">
        <div className="kpi-tile">
          <span className="kpi-label">価格</span>
          <span className="kpi-value">{fmt(ind.price, 3)}</span>
        </div>
        <div className="kpi-tile">
          <span className="kpi-label">RSI14</span>
          <span className="kpi-value">{fmt(ind.rsi14, 1)}</span>
        </div>
        <div className="kpi-tile">
          <span className="kpi-label">SMA20 / 50</span>
          <span className="kpi-value">
            {fmt(ind.sma20, 2)} / {fmt(ind.sma50, 2)}
          </span>
        </div>
        <div className="kpi-tile">
          <span className="kpi-label">ATR14</span>
          <span className="kpi-value">{fmt(ind.atr14, 3)}</span>
        </div>
      </div>

      <div>
        <span className="panel-title">テクニカル根拠</span>
        <ul className="reason-list">
          {technical.reasons.map((reason, i) => (
            <li key={i}>{reason}</li>
          ))}
        </ul>
      </div>

      <div>
        <span className="panel-title">ファンダメンタル根拠</span>
        <ul className="reason-list">
          {fundamental.reasons.map((reason, i) => (
            <li key={i}>{reason}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}
