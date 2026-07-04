const YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/JPY=X?interval=1m&range=1d";

interface YahooChartMeta {
  regularMarketPrice: number;
  previousClose: number;
  regularMarketTime: number;
}

export async function GET() {
  try {
    const res = await fetch(YAHOO_CHART_URL, {
      headers: { "User-Agent": "Mozilla/5.0" },
      next: { revalidate: 5 },
    });
    if (!res.ok) throw new Error(`upstream status ${res.status}`);

    const data = (await res.json()) as {
      chart?: { result?: { meta?: YahooChartMeta }[] };
    };
    const meta = data.chart?.result?.[0]?.meta;
    if (!meta || typeof meta.regularMarketPrice !== "number") {
      throw new Error("unexpected payload shape");
    }

    return Response.json(
      {
        price: meta.regularMarketPrice,
        previous_close: meta.previousClose,
        time_utc: new Date(meta.regularMarketTime * 1000).toISOString(),
        source: "Yahoo Finance（非公式）",
      },
      { headers: { "Cache-Control": "s-maxage=5, stale-while-revalidate=15" } },
    );
  } catch {
    return Response.json({ error: "ライブレートを取得できませんでした" }, { status: 502 });
  }
}
