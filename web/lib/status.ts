import type { Signal } from "./types";

export function signalStatusClass(signal: Signal): "status-good" | "status-critical" | "status-neutral" {
  if (signal === "買い") return "status-good";
  if (signal === "売り") return "status-critical";
  return "status-neutral";
}

export function signalIcon(signal: Signal): string {
  if (signal === "買い") return "▲";
  if (signal === "売り") return "▼";
  return "●";
}
