"use client";

import { useEffect, useRef, useState } from "react";
import {
  createChart,
  CandlestickSeries,
  LineSeries,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
} from "lightweight-charts";
import type { PriceBar, PriceHistory } from "@/lib/types";

type Timeframe = "15m" | "30m" | "1h";

const TIMEFRAME_LABELS: Record<Timeframe, string> = {
  "15m": "15分足",
  "30m": "30分足",
  "1h": "1時間足",
};

const SMA_PERIODS = [20, 50] as const;
const SMA_COLORS: Record<(typeof SMA_PERIODS)[number], string> = {
  20: "#4a9eff",
  50: "#c98a3e",
};

function toBarTime(iso: string): UTCTimestamp {
  return (new Date(iso).getTime() / 1000) as UTCTimestamp;
}

function computeSma(bars: PriceBar[], period: number) {
  const points: { time: UTCTimestamp; value: number }[] = [];
  let sum = 0;
  for (let i = 0; i < bars.length; i++) {
    sum += bars[i].c;
    if (i >= period) sum -= bars[i - period].c;
    if (i >= period - 1) {
      points.push({ time: toBarTime(bars[i].t), value: sum / period });
    }
  }
  return points;
}

export default function PriceChart({
  histories,
}: {
  histories: Record<Timeframe, PriceHistory | null>;
}) {
  const [timeframe, setTimeframe] = useState<Timeframe>("1h");
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const smaSeriesRef = useRef<Record<number, ISeriesApi<"Line">>>({});

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      autoSize: true,
      layout: {
        background: { color: "transparent" },
        textColor: "#c3c2b7",
        fontFamily: "var(--font-geist-mono), ui-monospace, monospace",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: "#2c2c2a" },
        horzLines: { color: "#2c2c2a" },
      },
      rightPriceScale: { borderColor: "#2c2c2a" },
      timeScale: { borderColor: "#2c2c2a", timeVisible: true, secondsVisible: false },
      crosshair: { mode: 0 },
    });

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#0ca30c",
      downColor: "#d03b3b",
      borderUpColor: "#0ca30c",
      borderDownColor: "#d03b3b",
      wickUpColor: "#0ca30c",
      wickDownColor: "#d03b3b",
    });

    const smaSeries: Record<number, ISeriesApi<"Line">> = {};
    for (const period of SMA_PERIODS) {
      smaSeries[period] = chart.addSeries(LineSeries, {
        color: SMA_COLORS[period],
        lineWidth: 2,
        priceLineVisible: false,
        lastValueVisible: false,
        crosshairMarkerVisible: false,
      });
    }

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    smaSeriesRef.current = smaSeries;

    return () => {
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      smaSeriesRef.current = {};
    };
  }, []);

  useEffect(() => {
    const history = histories[timeframe];
    const candleSeries = candleSeriesRef.current;
    const smaSeries = smaSeriesRef.current;
    if (!candleSeries || !history || history.bars.length === 0) return;

    candleSeries.setData(
      history.bars.map((bar) => ({
        time: toBarTime(bar.t),
        open: bar.o,
        high: bar.h,
        low: bar.l,
        close: bar.c,
      })),
    );

    for (const period of SMA_PERIODS) {
      smaSeries[period]?.setData(computeSma(history.bars, period));
    }

    chartRef.current?.timeScale().fitContent();
  }, [timeframe, histories]);

  const activeHistory = histories[timeframe];

  return (
    <section className="panel">
      <div className="chart-toolbar">
        <span className="panel-title">価格チャート</span>
        <div className="timeframe-switch">
          {(Object.keys(TIMEFRAME_LABELS) as Timeframe[]).map((tf) => (
            <button
              key={tf}
              type="button"
              className={`timeframe-btn ${tf === timeframe ? "is-active" : ""}`}
              onClick={() => setTimeframe(tf)}
            >
              {TIMEFRAME_LABELS[tf]}
            </button>
          ))}
        </div>
      </div>

      <div className="chart-legend">
        <span className="legend-item">
          <span className="legend-swatch" style={{ background: SMA_COLORS[20] }} />
          SMA20
        </span>
        <span className="legend-item">
          <span className="legend-swatch" style={{ background: SMA_COLORS[50] }} />
          SMA50
        </span>
      </div>

      {activeHistory && activeHistory.bars.length > 0 ? (
        <div ref={containerRef} className="chart-container" />
      ) : (
        <p className="empty-state">この時間足のチャートデータを取得できませんでした。</p>
      )}
    </section>
  );
}
