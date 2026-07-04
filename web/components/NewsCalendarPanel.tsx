import type { LatestSnapshot, CalendarEvent } from "@/lib/types";

const SENTIMENT_LABEL: Record<string, string> = {
  bullish: "強気",
  bearish: "弱気",
  neutral: "中立",
};

const SENTIMENT_CLASS: Record<string, string> = {
  bullish: "status-good",
  bearish: "status-critical",
  neutral: "status-neutral",
};

const IMPACT_LABEL: Record<string, string> = { High: "高", Medium: "中", Low: "低" };

function isCautionEvent(ev: CalendarEvent, cautionHours: number, nowMs: number): boolean {
  if (ev.impact !== "High") return false;
  if (ev.country !== "USD" && ev.country !== "JPY") return false;
  const t = new Date(ev.time).getTime();
  if (Number.isNaN(t)) return false;
  const hoursUntil = (t - nowMs) / 3_600_000;
  return hoursUntil >= 0 && hoursUntil <= cautionHours;
}

function formatDate(value: string | null): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString("ja-JP", {
    timeZone: "Asia/Tokyo",
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export default function NewsCalendarPanel({ snapshot }: { snapshot: LatestSnapshot }) {
  const { news, calendar } = snapshot;
  const nowMs = new Date(snapshot.generated_at_utc).getTime();

  return (
    <>
      <section className="panel">
        <span className="panel-title">ニュース見出し</span>
        {news.items.length === 0 ? (
          <p className="empty-state">直近のニュース見出しはありません</p>
        ) : (
          <ul className="reason-list">
            {news.items.map((item, i) => (
              <li key={i}>
                {item.link ? (
                  <a href={item.link} target="_blank" rel="noopener noreferrer">
                    {item.title}
                  </a>
                ) : (
                  item.title
                )}{" "}
                <span className={`badge ${SENTIMENT_CLASS[item.sentiment] ?? ""}`}>
                  {SENTIMENT_LABEL[item.sentiment] ?? item.sentiment}
                </span>{" "}
                <span className="hero-meta">
                  {item.source} / {formatDate(item.published_at)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="panel">
        <span className="panel-title">
          経済指標カレンダー（今後{calendar.display_window_hours}時間 / 警戒ウィンドウ{" "}
          {calendar.caution_window_hours}時間）
        </span>
        {calendar.events.length === 0 ? (
          <p className="empty-state">表示期間内の重要指標の予定はありません</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>通貨</th>
                  <th>指標</th>
                  <th>重要度</th>
                  <th>時刻（JST）</th>
                  <th className="num">予想</th>
                  <th className="num">前回</th>
                  <th className="num">結果</th>
                </tr>
              </thead>
              <tbody>
                {calendar.events.map((ev, i) => (
                  <tr key={i}>
                    <td>{ev.country}</td>
                    <td>
                      {ev.title}
                      {isCautionEvent(ev, calendar.caution_window_hours, nowMs) && (
                        <>
                          {" "}
                          <span className="badge status-critical">⚠ 警戒</span>
                        </>
                      )}
                    </td>
                    <td>
                      <span
                        className={`badge ${ev.impact === "High" ? "status-critical" : "status-neutral"}`}
                      >
                        {IMPACT_LABEL[ev.impact] ?? ev.impact}
                      </span>
                    </td>
                    <td>{formatDate(ev.time)}</td>
                    <td className="num">{ev.forecast ?? "—"}</td>
                    <td className="num">{ev.previous ?? "—"}</td>
                    <td className="num">{ev.actual ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}
