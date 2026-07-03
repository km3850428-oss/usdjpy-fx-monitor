import type { ClosedPosition } from "./types";

export interface PositionsSummary {
  total: number;
  wins: number;
  winRate: number;
  cumulativePips: number;
}

export function summarizePositions(closed: ClosedPosition[]): PositionsSummary {
  const total = closed.length;
  const wins = closed.filter((p) => p.pnl_pips > 0).length;
  const cumulativePips = Math.round(closed.reduce((sum, p) => sum + p.pnl_pips, 0) * 10) / 10;
  const winRate = total ? Math.round((wins / total) * 1000) / 10 : 0;
  return { total, wins, winRate, cumulativePips };
}
