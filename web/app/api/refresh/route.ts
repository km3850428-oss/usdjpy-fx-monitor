import { dispatchRun, getLatestRun } from "@/lib/githubActions";

export async function GET() {
  const run = await getLatestRun();
  if (!run) {
    return Response.json({ error: "実行状況を取得できませんでした" }, { status: 502 });
  }
  return Response.json({ run });
}

export async function POST() {
  const run = await getLatestRun();
  if (run && (run.status === "queued" || run.status === "in_progress")) {
    return Response.json({ error: "既に実行中です", run }, { status: 409 });
  }

  const result = await dispatchRun();
  if (!result.ok) {
    return Response.json({ error: result.error }, { status: 502 });
  }
  return Response.json({ ok: true }, { status: 202 });
}
