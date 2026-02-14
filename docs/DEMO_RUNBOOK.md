# デモ Runbook（3〜4分）

審査員向けのデモ台本。**Cloud Run が落ちていても Docker だけで同じ価値を示せます。** Cloud Run が Ready でないときは [DEMO_FALLBACK_DOCKER.md](DEMO_FALLBACK_DOCKER.md) へ。

---

## 1. 目的（20秒）

- **解決したいこと**: 見積書の固定資産／費用判定で、AI の「断定しすぎ」を防ぎ、判断が割れる行だけ人に委ねる。
- **新規性**: **Stop-first**（迷ったら GUIDANCE で止める）＋ **evidence**（判定根拠・税務ルール参照を `evidence` / `tax_rules` で提示）。誤判定を自動で通さない設計。

---

## 2. デモの前提（10秒）

- **Docker が主**: ローカルで build/run → スモーク → `/classify` → 税務閾値・`/classify_pdf` OFF まで。ここだけで価値は伝わる。
- **Cloud Run は任意**: Ready の場合だけ、同じスモークを Cloud Run URL で実行。

---

## 3. デモ手順（2〜3分）— Docker ルート

**作業ディレクトリ**: リポジトリルート（例: `c:\Users\owner\Desktop\fixed-asset-ashigaru`）。他環境では `cd` でリポジトリルートに移動。

### 成功基準

- `scripts/docker_smoke.ps1` が `=== All docker smoke tests passed ===` で終了（exit 0）
- `/classify` の JSON に `decision`, `evidence`, `trace`, `confidence`, `missing_fields`, `why_missing_matters` が含まれる
- 税務閾値（200k / 600k）の例で `evidence[].tax_rules` に `tax_rule:*` が出る
- `/classify_pdf` は 400 で `detail.error=PDF_CLASSIFY_DISABLED`、`detail.how_to_enable`、`detail.fallback` がある

---

### (a) Docker build / run

```powershell
cd c:\Users\owner\Desktop\fixed-asset-ashigaru
docker build -t fixed-asset-api .
```

```powershell
docker run --rm -e PORT=8080 -p 8080:8080 fixed-asset-api
```

- `PORT=8080`、`0.0.0.0:8080` で listen。**別ターミナル**で以下を実行。停止は `Ctrl+C`。

---

### (b) scripts/docker_smoke.ps1

別ターミナルで 1 行ずつ:

```powershell
cd c:\Users\owner\Desktop\fixed-asset-ashigaru
.\scripts\docker_smoke.ps1
```

- **期待**: `=== All docker smoke tests passed ===`、exit 0。
- **失敗時**: ターミナルに `FAIL:` と不足キー名 or HTTP コードが出る。コンテナが `http://localhost:8080` で動いているか、`DOCKER_SMOKE_URL` 未設定時は `http://localhost:8080` を使う。

---

### (c) /classify を 1 回叩く（主要キー確認）

```powershell
$body = '{"opal_json":{"invoice_date":"2024-01-01","vendor":"ACME","line_items":[{"item_description":"server install","amount":5000,"quantity":1}]}}'
Invoke-RestMethod -Uri "http://localhost:8080/classify" -Method Post -Body $body -ContentType "application/json"
```

- **期待**: HTTP 200。JSON に `decision`, `evidence`, `trace`, `confidence`, `missing_fields`, `why_missing_matters` が含まれる。

---

### (d) 税務閾値が evidence.tax_rules に出るのを「見せる」（200k or 600k）

**200k の例（R-AMOUNT-001 / R-AMOUNT-SME300k など）:**

```powershell
$body = '{"opal_json":{"invoice_date":"2024-01-01","vendor":"ACME","line_items":[{"item_description":"test 200k","amount":200000,"quantity":1}]}}'
$r = Invoke-RestMethod -Uri "http://localhost:8080/classify" -Method Post -Body $body -ContentType "application/json"
$r.evidence | ForEach-Object { $_.tax_rules }
```

- **期待**: `tax_rule:*` のいずれか（例: `R-AMOUNT-001`, `R-AMOUNT-SME300k`）が `evidence[].tax_rules` に出る。

**600k の例（R-AMOUNT-600k）:**

```powershell
$body = '{"opal_json":{"invoice_date":"2024-01-01","vendor":"ACME","line_items":[{"item_description":"test 600k","amount":600000,"quantity":1}]}}'
$r = Invoke-RestMethod -Uri "http://localhost:8080/classify" -Method Post -Body $body -ContentType "application/json"
$r.evidence | ForEach-Object { $_.tax_rules }
```

- **期待**: `tax_rule:*` に `R-AMOUNT-600k` が含まれる。

---

### (e) /classify_pdf は既定 OFF → 400（Stop-first / 安全設計）

`.\scripts\docker_smoke.ps1` が /classify_pdf で 400 と `detail.error` / `detail.how_to_enable` / `detail.fallback` を検証する。手動で叩く例（`cd` でリポジトリルートにいる前提）:

```powershell
$form = @{ file = Get-Item -LiteralPath ".\tests\fixtures\sample_text.pdf" }
try { Invoke-WebRequest -Uri "http://localhost:8080/classify_pdf" -Method Post -Form $form -UseBasicParsing } catch { [int]$_.Exception.Response.StatusCode }
```

- **期待**: `400` が出力される。本文の `detail` に `error=PDF_CLASSIFY_DISABLED`、`how_to_enable`、`fallback` がある（詳細は `docker_smoke.ps1` の 3 番チェック）。→ 機能を明示的に有効化するまで動かさない安全設計として説明。

---

### (f) DocAI（USE_DOCAI=1）— Google Cloud AI の位置づけ

- **USE_DOCAI=1** かつ `GOOGLE_CLOUD_PROJECT` / `DOCAI_PROCESSOR_ID` が揃うと、PDF 抽出に Document AI を使用。
- **未設定**なら PyMuPDF / pdfplumber にフォールバック。デモでは未設定でよい。  
- 「Google Cloud AI を主要技術として扱い、任意で DocAI を組み込める」と説明。

---

## 4. Cloud Run での同等デモ（30〜60秒）— Ready の場合だけ

**Cloud Run のサービスが Ready（`Ready=True`）のときのみ**実行。

```powershell
$env:CLOUD_RUN_URL = "https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app"
.\scripts\smoke_cloudrun.ps1
```

- URL は `gcloud run services describe fixed-asset-agentic-api --region asia-northeast1 --project fixedassets-project --format="value(status.url)"` で取得した値に差し替えてよい。
- **期待**: `=== All smoke tests passed ===`。内容は Docker スモークと同じ（/health, /classify, /classify_pdf OFF→400）。

---

## 5. 想定 QA（30秒）

| 質問 | 回答 |
|------|------|
| なぜ GUIDANCE が重要か | 判断が割れる行を「要確認」として止め、`missing_fields` / `why_missing_matters` で人に委ねる。誤った自動化を通さない。 |
| ルールと AI の役割分担 | 税務閾値・キーワードはルール（`evidence.tax_rules` に参照）。分類の揺れ・文脈は AI。GUIDANCE で止めて人が最終判断。 |
| Cloud AI の使い所 | DocAI: PDF 抽出（USE_DOCAI=1）。Vertex Search: 法令エビデンス（フラグ任意）。Cloud Run: ホスティング。いずれもオフにしても Docker で同じ価値をデモ可能。 |

---

## リンク

- Docker 手順の詳細: [DOCKER_LOCAL_SMOKE.md](DOCKER_LOCAL_SMOKE.md)
- Cloud Run が落ちているとき: [DEMO_FALLBACK_DOCKER.md](DEMO_FALLBACK_DOCKER.md)
- 環境変数: [CLOUDRUN_ENV.md](CLOUDRUN_ENV.md)
