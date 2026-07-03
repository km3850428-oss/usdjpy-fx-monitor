import { getLatestSnapshot, getPositions } from "@/lib/github";
import JudgmentPanel from "@/components/JudgmentPanel";
import ScoreBreakdown from "@/components/ScoreBreakdown";
import PositionsPanel from "@/components/PositionsPanel";

export const revalidate = 60;

export default async function Home() {
  const [snapshot, positions] = await Promise.all([getLatestSnapshot(), getPositions()]);

  return (
    <main className="page">
      <header className="page-header">
        <h1>USD/JPY ライブダッシュボード</h1>
        <p>毎時自動更新されるテクニカル・ファンダメンタルズ判定と仮想トレード成績</p>
      </header>

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

      {positions ? (
        <PositionsPanel positions={positions} />
      ) : (
        <section className="panel">
          <p className="empty-state">ポジションデータを取得できませんでした。</p>
        </section>
      )}
    </main>
  );
}
