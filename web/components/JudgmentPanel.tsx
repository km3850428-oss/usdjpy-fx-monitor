import type { LatestSnapshot } from "@/lib/types";
import { signalIcon, signalStatusClass } from "@/lib/status";

export default function JudgmentPanel({ snapshot }: { snapshot: LatestSnapshot }) {
  const { judgment, generated_at_jst } = snapshot;
  const statusClass = signalStatusClass(judgment.signal);

  return (
    <section className="panel">
      <span className="panel-title">現在の判定</span>
      <div className="hero">
        <span className={`hero-signal ${statusClass}`}>
          {signalIcon(judgment.signal)} {judgment.signal}
        </span>
        <span className="hero-meta">
          総合スコア {judgment.overall_score.toFixed(3)}（テクニカル {judgment.technical_score.toFixed(3)} / ファンダメンタル{" "}
          {judgment.fundamental_score.toFixed(3)}）
        </span>
      </div>
      {judgment.override_reason && <p className="override-note">⚠ {judgment.override_reason}</p>}
      <span className="hero-meta">判定時刻（JST）: {formatJst(generated_at_jst)}</span>
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
