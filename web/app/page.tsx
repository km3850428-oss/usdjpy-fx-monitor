import { getLatestSnapshot, getPositions, getPriceHistory } from "@/lib/github";
import JudgmentPanel from "@/components/JudgmentPanel";
import ScoreBreakdown from "@/components/ScoreBreakdown";
import PositionsPanel from "@/components/PositionsPanel";
import PriceChart from "@/components/PriceChart";
import RefreshButton from "@/components/RefreshButton";
import RateTicker from "@/components/RateTicker";
import NewsCalendarPanel from "@/components/NewsCalendarPanel";

export const revalidate = 60;

export default async function Home() {
  const [snapshot, positions, history15m, history30m, history1h] = await Promise.all([
    getLatestSnapshot(),
    getPositions(),
    getPriceHistory("15m"),
    getPriceHistory("30m"),
    getPriceHistory("1h"),
  ]);

  return (
    <main className="page">
      <header className="page-header">
        <div className="page-header-row">
          <div>
            <h1>USD/JPY ライブダッシュボード</h1>
            <p>毎時自動更新されるテクニカル・ファンダメンタルズ判定と仮想トレード成績</p>
          </div>
          <RefreshButton />
        </div>
      </header>

      <RateTicker
        fallbackPrice={snapshot?.technical.indicators.price ?? null}
        fallbackTimeJst={snapshot?.generated_at_jst ?? null}
      />

      {snapshot ? (
        <>
          <JudgmentPanel snapshot={snapshot} />
          <ScoreBreakdown snapshot={snapshot} />
        </>
      ) : (
        <section className="panel">
          <p className="empty-state">判定データを取得できませんでした。しばらくしてから再読み込みしてください。</p>
        </section>
      )}

      <PriceChart histories={{ "15m": history15m, "30m": history30m, "1h": history1h }} />

      {positions ? (
        <PositionsPanel positions={positions} />
      ) : (
        <section className="panel">
          <p className="empty-state">ポジションデータを取得できませんでした。</p>
        </section>
      )}

      {snapshot && <NewsCalendarPanel snapshot={snapshot} />}
    </main>
  );
}
