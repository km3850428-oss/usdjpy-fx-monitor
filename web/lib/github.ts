import type { LatestSnapshot, PositionsData, PriceHistory } from "./types";

const OWNER = "km3850428-oss";
const REPO = "usdjpy-fx-monitor";
const BRANCH = "main";

function rawUrl(path: string): string {
  return `https://raw.githubusercontent.com/${OWNER}/${REPO}/${BRANCH}/${path}`;
}

async function fetchJson<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(rawUrl(path), { next: { revalidate: 60 } });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export function getLatestSnapshot(): Promise<LatestSnapshot | null> {
  return fetchJson<LatestSnapshot>("data/latest.json");
}

export function getPositions(): Promise<PositionsData | null> {
  return fetchJson<PositionsData>("positions.json");
}

export function getPriceHistory(
  timeframe: "15m" | "30m" | "1h",
): Promise<PriceHistory | null> {
  return fetchJson<PriceHistory>(`data/price_history_${timeframe}.json`);
}
