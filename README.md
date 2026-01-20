見積書 固定資産判定

― Opal抽出 × Agentic判定（Stop設計）

概要



本プロジェクトは、見積書の固定資産／費用判定において、

AIが判断を誤る可能性そのものを、設計で吸収する Agentic AI を提案します。



OCRや項目抽出の精度が向上しても、

実務における「判断」は常に文脈依存であり、揺れを伴います。



さらに現場では、

人であっても AI であっても、

その判断を十分に疑う余裕がない状況が頻発します。



本システムは、この前提に立ち、

判断を無理に自動化せず、

判断を行う／止めるを自律的に選択するエージェントとして設計されています。



背景にある構造的な課題（重要）



経理業務では、

人の判断であっても、AIの判断であっても、

常に正しさを検証できるとは限りません。



特に以下のような状況では、



月末・決算期など、時間的余裕がない



人員不足により確認工程が圧縮される



過去と同じ処理を踏襲せざるを得ない



結果として、



「人が判断したから大丈夫」



「AIが出した結果だから正しい」



という 思考停止が起きやすい構造が生まれます。



AIによる自動化は、

この「疑えない状況」を解消するどころか、

誤った判断を高速に通過させてしまうリスクも持っています。



解決したい課題



経理・税務の現場では、以下のような事故が起きがちです。



AIが断定した結果を、そのまま採用してしまう



判断が割れる行（撤去・移設など）が他の行に埋もれる



後から「なぜその処理になったのか」を説明できない



多くの自動化ツールは、

すべてを自動で処理することを前提としており、

止まる設計を持っていません。



本プロジェクトの新規性（Agentic AIとして）



本プロジェクトは、

「AIが迷う場面では自動化を止める」ことを価値とする

Agentic AI の設計パターンを提示します。



ここでいう自律とは、



すべてを自動で処理することではなく、

判断を行う／止めるを選択できること



と定義しています。



システム構成

見積書PDF

&nbsp;  ↓

Opal（OCR・項目抽出）

&nbsp;  ↓  ※揺れるJSON

Adapter（凍結スキーマ v1.0）

&nbsp;  ↓

Classifier（3値判定 + Stop設計）

&nbsp;  ↓

UI（要確認行を可視化・証跡保存）



3ステップの動作概要

Step1｜Opalで抽出（揺れるJSON）



Opalを高性能OCRとして利用し、

項目抽出までを担当させます。

この時点では 判定は行いません。



Step2｜Adapter正規化（凍結スキーマ）



抽出結果を、構造が固定されたスキーマに正規化します。

これにより、後段の判定ロジックを安定させます。



Step3｜Classifier判定（3値・断定しない）



各明細行を以下の3値で判定します。



CAPITAL\_LIKE（資産寄り）



EXPENSE\_LIKE（費用寄り）



GUIDANCE（要確認・判断停止）



判断が割れる語（撤去／移設／既設など）を検知した場合、

自律的に GUIDANCE として停止します。



Stop設計（本プロジェクトの核心）



GUIDANCE は誤判定ではありません。



判断が割れる行を検知した結果



人が確認すべき箇所を明示するための停止



停止理由は flags として証跡に残る



これにより、



誤った自動化を防ぎ



経理担当者は確認すべき行だけに集中でき



後から判断根拠を追跡可能



となります。



利用シーン（1コマ）



月末、経理担当者は

要確認（GUIDANCE）の行だけを優先的に確認すればよくなります。



意図的に実装しなかったもの



本プロジェクトでは、以下を意図的に除外しています。



自動仕訳・自動計上

→ 誤判定時の責任境界が不明確になるため



耐用年数まで含めた自動判定

→ 法改正・企業差異が大きく、

疑う余裕がない状態での断定を避けるため



OCRの自前実装

→ 本質ではなく、Opalに委譲すべきため



なぜ Agentic AI Hackathon なのか



本システムにおける Agent とは、

判断を自律的に「行う／止める」を選択する存在です。



これは、

単なる自動化ではなく、

人とAIの責任分界点を明確にする意思決定支援の実例です。



今後の拡張（構想）



耐用年数マスタとの接続（任意・確認前提）



過去判断履歴との比較（参考情報として）

※前例踏襲による思考停止リスクを伴うため注意



他帳票（請求書・領収書）への横展開



※いずれも Stop設計を維持した上で拡張予定です。



まとめ



本プロジェクトは、

AIの賢さを制限することで、

疑う余裕がない現場でも使える判断支援を実現する

Agentic AI の設計提案です。
Minimal per-company policy hook (v0.1): place a JSON like `policies/company_default.json` to add company-specific keywords, optional GUIDANCE regex, and a caution threshold while keeping the Stop-first design intact. If no policy is provided or it is unreadable, the pipeline behaves exactly as before (schema v1.0 unchanged).

Policyファイル: `policies/company_default.json` を配置。UIはサイドバーで選択、CLIは `POLICY_PATH=policies/company_default.json python scripts/run_pipeline.py --in data/opal_outputs/01_opal.json --out data/results/01_final.json` などで適用できます。

---
Quick links:
- See INDEX.md for autonomous dev rules and gates.
- See docs/00_project.md, docs/01_commands.md, docs/02_arch.md, docs/03_rules.md for context and workflows.
- PDF: `python scripts/run_pdf.py --pdf tests/fixtures/sample_text.pdf --out data/results` (artifacts go to `data/uploads` and `data/results`)
- UI: `streamlit run ui/app.py` then use the JSON tab or the new PDF Upload tab
- API: `uvicorn api.main:app --reload --port 8000` (see API section below)
- Agent (hands-off): on an Issue, add label `agent:run` to let GitHub Actions branch→run checks→push→open PR and comment back. No auto-merge; main requires PR.

## API (FastAPI)

### ローカル起動

```bash
uvicorn api.main:app --reload --port 8000
```

### エンドポイント

#### GET /health
ヘルスチェックエンドポイント（Cloud Run公式）。`/healthz`はCloud Runで予約パスのため使用不可。

```bash
curl http://localhost:8000/health
```

レスポンス: `{"ok": true}`

#### POST /classify
Opal JSONを送信して固定資産判定を実行。WIN+1: オプショナルな`answers`フィールドでagenticループをサポート。

```bash
curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d '{
    "opal_json": {
      "invoice_date": "2024-01-01",
      "vendor": "ACME Corp",
      "line_items": [
        {"item_description": "server install", "amount": 5000, "quantity": 1}
      ]
    },
    "policy_path": "policies/company_default.json",
    "answers": {"field1": "value1"}
  }'
```

`policy_path` が指定されない場合、デフォルトで `policies/company_default.json` が使用されます。
`answers` はオプショナルで、GUIDANCE判定時に不足情報を補完して再分類を試みます。

レスポンス形式:
```json
{
  "decision": "CAPITAL_LIKE|EXPENSE_LIKE|GUIDANCE",
  "reasons": ["判定理由のリスト"],
  "evidence": [{"line_no": 1, "description": "...", "source_text": "...", "confidence": 0.8, ...}],
  "questions": ["GUIDANCE項目に対する確認質問"],
  "metadata": {"version": "v1.0", "document_info": {...}, "totals": {...}, ...},
  "is_valid_document": true,
  "confidence": 0.8,
  "error_code": null,
  "trace": ["extract", "parse", "rules", "format"],
  "missing_fields": ["field1", "field2"],
  "why_missing_matters": ["Missing information prevents classification"]
}
```

WIN+1追加フィールド:
- `is_valid_document`: ドキュメントが有効かどうか
- `confidence`: 判定の信頼度（0.0-1.0）
- `error_code`: エラーコード（エラー時のみ）
- `trace`: 実行ステップのトレース
- `missing_fields`: GUIDANCE時に不足しているフィールドのリスト
- `why_missing_matters`: 不足情報が判定に与える影響の説明
- `evidence[].confidence`: 各エビデンス項目の信頼度（デフォルト0.8）

### Docker ビルド・実行

```bash
# ビルド
docker build -t fixed-asset-api .

# ローカル実行（ポート8080で起動）
docker run -p 8080:8080 -e PORT=8080 fixed-asset-api
```

### Cloud Run デプロイ

**前提条件:** GCPプロジェクトにBillingアカウントをリンクしてください。

#### デプロイ手順（最短）

```bash
# 1. プロジェクト設定
gcloud config set project YOUR_PROJECT_ID

# 2. 必要APIを有効化
gcloud services enable run.googleapis.com artifactregistry.googleapis.com aiplatform.googleapis.com

# 3. Cloud Runにデプロイ
gcloud run deploy fixed-asset-agentic-api \
  --source . \
  --region asia-northeast1 \
  --allow-unauthenticated

# 4. デプロイ後の疎通確認
curl.exe -s https://SERVICE_URL/health

# または PowerShell smoke script を使用
.\scripts\smoke_cloudrun.ps1
```

#### 方法2: 事前ビルドしたイメージからデプロイ

#### 方法2: 事前ビルドしたイメージからデプロイ

```bash
# GCR/Artifact Registryにプッシュ
docker tag fixed-asset-api gcr.io/YOUR_PROJECT_ID/fixed-asset-api
docker push gcr.io/YOUR_PROJECT_ID/fixed-asset-api

# Cloud Runにデプロイ
gcloud run deploy fixed-asset-api \
  --image gcr.io/YOUR_PROJECT_ID/fixed-asset-api \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated
```

Cloud Runは自動的に `PORT` 環境変数を設定します。コンテナ内のアプリケーションは `0.0.0.0:$PORT` でリッスンします。

## Evaluation

### Golden Set Evaluation

評価用のゴールデンセット（10ケース）が `data/golden/` に含まれています。
各ケースは `caseXX_request.json` と `caseXX_expected.json` のペアで構成されています。

評価スクリプトを実行:

```bash
python scripts/eval_golden.py
```

出力例:
```
============================================================
Golden Set Evaluation
============================================================

PASS: Case 01: PASS
PASS: Case 02: PASS
...
PASS: Case 10: PASS

============================================================
Summary
============================================================
Total cases: 10
Passed: 10
Failed: 0
Accuracy: 100.0%

All tests passed!
```

### Current Score

- **Golden Set Accuracy: 100.0%** (10/10 cases passed)
- Last evaluated: 2026-01-20
