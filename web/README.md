# USD/JPY ライブダッシュボード（Web）

GitHub Actions側（`../src/`）が生成する `data/latest.json` / `positions.json` / `data/price_history_*.json` を
`raw.githubusercontent.com` から読み取り、判定・スコア内訳・価格チャート・仮想ポジション成績・ニュース／経済指標カレンダーを表示するNext.js（App Router）製ダッシュボードです。

Vercelは表示とトリガー役に徹し、データ取得・判定ロジックは既存のPythonパイプラインが担います。

## ローカル開発

```bash
npm install
npm run dev
```

[http://localhost:3000](http://localhost:3000) を開いて確認してください。ページは常にpublicの`raw.githubusercontent.com`からデータを取得するため、ローカルでも実データで表示されます。

## ディレクトリ構成

```
web/
├── app/
│   ├── page.tsx                 # ダッシュボード本体（Server Component, ISR revalidate=60s）
│   └── api/
│       ├── refresh/route.ts     # 手動更新ボタン用（GitHub Actions workflow_dispatchをトリガー）
│       └── rate/route.ts        # ライブレートティッカー用（Yahoo Finance chart APIをプロキシ）
├── components/                  # JudgmentPanel / ScoreBreakdown / PriceChart / PositionsPanel など
└── lib/                         # raw.githubusercontent.com からのデータ取得・型定義
```

## 環境変数

`/api/refresh`（手動更新ボタン）を使う場合のみ、Vercelに以下を設定してください。未設定でもダッシュボードの閲覧自体（判定・チャート・ポジション・ニュース）には影響しません。

| 変数名 | 必須 | 説明 |
|---|---|---|
| `GH_TOKEN` | 手動更新ボタンを使う場合のみ | 対象リポジトリ限定のfine-grained PAT。`Actions: Read and write` 権限が必要 |
| `GH_OWNER` | 任意 | 既定値 `km3850428-oss` |
| `GH_REPO` | 任意 | 既定値 `usdjpy-fx-monitor` |
| `GH_BRANCH` | 任意 | 既定値 `main` |
| `GH_WORKFLOW_FILE` | 任意 | 既定値 `fx_monitor.yml` |

Discord Webhook URLやFRED APIキーはVercel側には置かず、GitHub Actions Secrets側のみで完結させています。

## 既知の制約

- `raw.githubusercontent.com`はCDN+ISR（60秒）でキャッシュされるため、GitHub Actions実行完了からダッシュボードへの反映まで数分程度のタイムラグが生じることがあります。
- `/api/rate`は非公式のYahoo Finance chart APIに依存しています。取得に失敗した場合は自動的に判定データ内の価格にフォールバックし、「ライブ取得失敗中」バッジを表示します。
- 認証は設けていません（URLを知っていれば誰でも閲覧・手動更新ボタンの利用が可能）。ただしGitHub Actions側の`concurrency`設定により実行は実質1本化されるため、悪用による実害は小さい設計です。

## デプロイ

VercelのRoot Directoryを`web`に設定してデプロイしてください。[Next.jsデプロイ手順](https://nextjs.org/docs/app/building-your-application/deploying)も参照。
