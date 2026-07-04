const GH_API = "https://api.github.com";

export interface WorkflowRun {
  id: number;
  status: string;
  conclusion: string | null;
  created_at: string;
  html_url: string;
}

function config() {
  const token = process.env.GH_TOKEN;
  if (!token) return null;
  return {
    token,
    owner: process.env.GH_OWNER ?? "km3850428-oss",
    repo: process.env.GH_REPO ?? "usdjpy-fx-monitor",
    branch: process.env.GH_BRANCH ?? "main",
    workflowFile: process.env.GH_WORKFLOW_FILE ?? "fx_monitor.yml",
  };
}

function headers(token: string): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
    Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
  };
}

export async function getLatestRun(): Promise<WorkflowRun | null> {
  const cfg = config();
  if (!cfg) return null;

  const url = `${GH_API}/repos/${cfg.owner}/${cfg.repo}/actions/workflows/${cfg.workflowFile}/runs?per_page=1&branch=${cfg.branch}`;
  const res = await fetch(url, { headers: headers(cfg.token), cache: "no-store" });
  if (!res.ok) return null;

  const data = (await res.json()) as { workflow_runs?: WorkflowRun[] };
  return data.workflow_runs?.[0] ?? null;
}

export async function dispatchRun(): Promise<{ ok: true } | { ok: false; error: string }> {
  const cfg = config();
  if (!cfg) return { ok: false, error: "GH_TOKEN が設定されていません" };

  const url = `${GH_API}/repos/${cfg.owner}/${cfg.repo}/actions/workflows/${cfg.workflowFile}/dispatches`;
  const res = await fetch(url, {
    method: "POST",
    headers: { ...headers(cfg.token), "Content-Type": "application/json" },
    body: JSON.stringify({ ref: cfg.branch }),
  });

  if (!res.ok) {
    return { ok: false, error: `GitHub API error (${res.status})` };
  }
  return { ok: true };
}
