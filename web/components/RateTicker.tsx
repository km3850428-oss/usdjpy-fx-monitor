"use client";

import { useEffect, useRef, useState } from "react";

interface RateData {
  price: number;
  previous_close: number;
  time_utc: string;
  source: string;
}

const POLL_INTERVAL_MS = 10000;

type Status = "loading" | "live" | "stale";

export default function RateTicker({
  fallbackPrice,
  fallbackTimeJst,
}: {
  fallbackPrice: number | null;
  fallbackTimeJst: string | null;
}) {
  const [rate, setRate] = useState<RateData | null>(null);
  const [status, setStatus] = useState<Status>("loading");
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      try {
        const res = await fetch("/api/rate", { cache: "no-store" });
        if (!res.ok) throw new Error("bad status");
        const data = (await res.json()) as RateData;
        if (!cancelled) {
          setRate(data);
          setStatus("live");
        }
      } catch {
        if (!cancelled) setStatus("stale");
      }
    }

    poll();
    timerRef.current = setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const isLive = status === "live" && rate !== null;
  const price = isLive ? rate!.price : fallbackPrice;
  const change = isLive ? rate!.price - rate!.previous_close : null;
  const changeClass = change === null ? "" : change >= 0 ? "status-good" : "status-critical";
  const changeIcon = change === null ? "" : change >= 0 ? "▲" : "▼";

  return (
    <section className="panel">
      <div className="chart-toolbar">
        <span className="panel-title">現在レート</span>
        {status === "loading" ? (
          <span className="badge">接続中…</span>
        ) : (
          <span className={`badge ${isLive ? "status-good" : "status-critical"}`}>
            {isLive ? "● LIVE" : "⚠ ライブ取得失敗中"}
          </span>
        )}
      </div>

      <div className="hero">
        <span className="hero-signal">{price !== null ? price.toFixed(3) : "—"}</span>
        {change !== null && (
          <span className={`hero-meta ${changeClass}`}>
            {changeIcon} {change >= 0 ? "+" : ""}
            {change.toFixed(3)}（前日比）
          </span>
        )}
      </div>

      <span className="hero-meta">
        {isLive
          ? `${rate!.source} / ${formatJst(rate!.time_utc)}`
          : status === "loading"
            ? "ライブ取得に接続しています…"
            : fallbackTimeJst
              ? `最終判定時の価格にフォールバック中 / ${formatJst(fallbackTimeJst)}`
              : "データ取得中…"}
      </span>
    </section>
  );
}

function formatJst(isoString: string): string {
  try {
    return new Date(isoString).toLocaleString("ja-JP", {
      timeZone: "Asia/Tokyo",
      dateStyle: "medium",
      timeStyle: "medium",
    });
  } catch {
    return isoString;
  }
}
