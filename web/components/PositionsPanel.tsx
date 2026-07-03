import type { PositionsData } from "@/lib/types";
import { summarizePositions } from "@/lib/positions";

const RECENT_CLOSED_LIMIT = 15;

export default function PositionsPanel({ positions }: { positions: PositionsData }) {
  const summary = summarizePositions(positions.closed);
  const recentClosed = [...positions.closed].reverse().slice(0, RECENT_CLOSED_LIMIT);

  return (
    <section className="panel">
      <span className="panel-title">仮想ポジション（ペーパートレード）</span>

      <div className="kpi-row">
        <div className="kpi-tile">
          <span className="kpi-label">累計トレード</span>
          <span className="kpi-value">{summary.total}</span>
        </div>
        <div className="kpi-tile">
          <span className="kpi-label">勝率</span>
          <span className="kpi-value">{summary.winRate}%</span>
        </div>
        <div className="kpi-tile">
          <span className="kpi-label">累計損益</span>
          <span className={`kpi-value ${summary.cumulativePips >= 0 ? "status-good" : "status-critical"}`}>
            {summary.cumulativePips >= 0 ? "+" : ""}
            {summary.cumulativePips} pips
          </span>
        </div>
      </div>

      <div>
        <span className="panel-title">保有中ポジション（{positions.open.length}）</span>
        {positions.open.length === 0 ? (
          <p className="empty-state">現在保有中のポジションはありません</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>方向</th>
                  <th className="num">エントリー</th>
                  <th className="num">損切り</th>
                  <th className="num">利確</th>
                  <th>エントリー時刻</th>
                </tr>
              </thead>
              <tbody>
                {positions.open.map((p) => (
                  <tr key={p.id}>
                    <td>{p.direction}</td>
                    <td className="num">{p.entry_price}</td>
                    <td className="num">{p.stop_loss}</td>
                    <td className="num">{p.take_profit}</td>
                    <td>{formatJst(p.opened_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div>
        <span className="panel-title">決済履歴（直近{RECENT_CLOSED_LIMIT}件）</span>
        {recentClosed.length === 0 ? (
          <p className="empty-state">決済履歴はまだありません</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>方向</th>
                  <th className="num">エントリー</th>
                  <th className="num">決済</th>
                  <th className="num">損益(pips)</th>
                  <th>決済理由</th>
                  <th>決済時刻</th>
                </tr>
              </thead>
              <tbody>
                {recentClosed.map((p) => (
                  <tr key={p.id}>
                    <td>{p.direction}</td>
                    <td className="num">{p.entry_price}</td>
                    <td className="num">{p.exit_price}</td>
                    <td className={`num ${p.pnl_pips >= 0 ? "pnl-positive" : "pnl-negative"}`}>
                      {p.pnl_pips >= 0 ? "+" : ""}
                      {p.pnl_pips}
                    </td>
                    <td>{p.exit_reason}</td>
                    <td>{formatJst(p.closed_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}

function formatJst(isoString: string): string {
  try {
    return new Date(isoString).toLocaleString("ja-JP", {
      timeZone: "Asia/Tokyo",
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return isoString;
  }
}
