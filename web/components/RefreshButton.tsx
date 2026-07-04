"use client";

import { useEffect, useRef, useState } from "react";

interface RunInfo {
  id: number;
  status: string;
  conclusion: string | null;
  created_at: string;
  html_url: string;
}

type Phase = "idle" | "requesting" | "polling" | "done" | "timeout" | "error";

const POLL_INTERVAL_MS = 9000;
const MAX_POLLS = 40; // ~6分

async function fetchRun(): Promise<RunInfo | null> {
  const res = await fetch("/api/refresh", { cache: "no-store" });
  if (!res.ok) return null;
  const data = (await res.json()) as { run?: RunInfo };
  return data.run ?? null;
}

export default function RefreshButton() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [message, setMessage] = useState<string | null>(null);
  const baselineRunId = useRef<number | null>(null);
  const pollCount = useRef(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  function stopPolling() {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }

  function startPolling() {
    pollCount.current = 0;
    stopPolling();
    timerRef.current = setInterval(async () => {
      pollCount.current += 1;
      const run = await fetchRun();

      if (run && run.id !== baselineRunId.current && run.status === "completed") {
        stopPolling();
        setPhase("done");
        setMessage(
          run.conclusion === "success"
            ? "更新が完了しました。反映まで数分かかる場合があります。"
            : `実行が完了しましたが結果は "${run.conclusion ?? "不明"}" でした。`,
        );
        return;
      }

      if (pollCount.current >= MAX_POLLS) {
        stopPolling();
        setPhase("timeout");
        setMessage("確認がタイムアウトしました。GitHub Actionsの実行状況を直接ご確認ください。");
      }
    }, POLL_INTERVAL_MS);
  }

  async function handleClick() {
    setPhase("requesting");
    setMessage(null);

    const baseline = await fetchRun();
    baselineRunId.current = baseline?.id ?? null;

    try {
      const res = await fetch("/api/refresh", { method: "POST" });
      const data = (await res.json()) as { error?: string; run?: RunInfo };

      if (res.status === 202) {
        setPhase("polling");
        setMessage("更新をリクエストしました。実行状況を確認しています…");
        startPolling();
      } else if (res.status === 409) {
        setPhase("polling");
        setMessage("既に実行中です。完了を待っています…");
        startPolling();
      } else {
        setPhase("error");
        setMessage(data.error ?? "更新リクエストに失敗しました。");
      }
    } catch {
      setPhase("error");
      setMessage("更新リクエストに失敗しました。ネットワークをご確認ください。");
    }
  }

  const isBusy = phase === "requesting" || phase === "polling";

  return (
    <div className="refresh-control">
      <button type="button" className="refresh-button" onClick={handleClick} disabled={isBusy}>
        {isBusy ? "更新中…" : "手動更新"}
      </button>
      {message && (
        <span
          className={`refresh-message ${phase === "error" || phase === "timeout" ? "status-critical" : ""}`}
        >
          {message}
        </span>
      )}
    </div>
  );
}
