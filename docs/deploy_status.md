# Cloud Run デプロイ状況レポート

> **確認日時**: 2026-01-30T19:06:56
> **確認者**: 足軽2（自動確認）
> **ステータス**: デプロイ済み・正常稼働中

---

## 1. デプロイ状態サマリ

| 項目 | 値 |
|------|-----|
| **サービス名** | fixed-asset-agentic-api |
| **リージョン** | asia-northeast1 |
| **URL** | https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app |
| **ステータス** | **稼働中** |

---

## 2. エンドポイント動作確認結果

### 2.1 /health

| 項目 | 結果 |
|------|------|
| HTTPステータス | **200 OK** |
| レスポンス | `{"ok":true}` |
| 判定 | **正常** |

### 2.2 /classify

| 項目 | 結果 |
|------|------|
| HTTPステータス | **200 OK** |
| レスポンス | decision, evidence, questions等を含むJSON |
| 判定 | **正常** |

テストリクエスト:
```json
{
  "opal_json": {
    "invoice_date": "2024-01-01",
    "vendor": "Test",
    "line_items": [{"item_description": "server", "amount": 5000, "quantity": 1}]
  }
}
```

レスポンス（抜粋）:
```json
{
  "decision": "GUIDANCE",
  "reasons": ["判断が割れる可能性があるため判定しません", "flag: no_keywords"],
  "evidence": [{"line_no": 1, "description": "server", ...}],
  "questions": ["Line 1: server - flags: no_keywords"]
}
```

### 2.3 /classify_pdf

| 項目 | 結果 |
|------|------|
| HTTPステータス | **400**（期待通り） |
| Feature Flag | OFF（`PDF_CLASSIFY_ENABLED`未設定） |
| 判定 | **正常**（OFFが期待値） |

---

## 3. 環境変数設定状況

現在のCloud Run環境変数の設定状況（推定）:

| 変数名 | 設定状況 | 説明 |
|--------|----------|------|
| `PORT` | 自動設定 | Cloud Runが自動設定 |
| `PDF_CLASSIFY_ENABLED` | **未設定（OFF）** | PDF分類機能は無効 |
| `USE_DOCAI` | 未設定（OFF） | Document AI未使用 |
| `VERTEX_SEARCH_ENABLED` | 未設定（OFF） | Vertex AI Search未使用 |

---

## 4. Dockerイメージ情報

### Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=8080
CMD ["sh", "-c", "exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
```

### 主要依存関係
- Python 3.11
- FastAPI
- uvicorn
- PyMuPDF
- streamlit（requirements.txt に含む。API本体は未使用）
- google-cloud-documentai（オプション）

---

## 5. 追加機能の有効化手順

### 5.1 PDF分類機能（/classify_pdf）を有効化する場合

```bash
gcloud run services update fixed-asset-agentic-api \
  --region asia-northeast1 \
  --set-env-vars PDF_CLASSIFY_ENABLED=1
```

### 5.2 Document AI（高精度PDF抽出）を有効化する場合

```bash
gcloud run services update fixed-asset-agentic-api \
  --region asia-northeast1 \
  --set-env-vars USE_DOCAI=1,GOOGLE_CLOUD_PROJECT=YOUR_PROJECT,DOCAI_PROCESSOR_ID=YOUR_PROCESSOR_ID
```

### 5.3 Vertex AI Search（法令エビデンス検索）を有効化する場合

```bash
gcloud run services update fixed-asset-agentic-api \
  --region asia-northeast1 \
  --set-env-vars VERTEX_SEARCH_ENABLED=1,GOOGLE_CLOUD_PROJECT=YOUR_PROJECT,DISCOVERY_ENGINE_DATA_STORE_ID=YOUR_DATASTORE_ID
```

---

## 6. スモークテスト実行方法

### PowerShell（一括実行）

```powershell
# 環境変数設定（オプション、未設定時はデフォルトURLを使用）
$env:CLOUD_RUN_URL = "https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app"

# スモークテスト実行
.\scripts\smoke_cloudrun.ps1
```

### 手動確認

```bash
# /health
curl -s https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app/health

# /classify
curl -s -X POST https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app/classify \
  -H "Content-Type: application/json" \
  -d '{"opal_json":{"invoice_date":"2024-01-01","vendor":"Test","line_items":[{"item_description":"server","amount":5000,"quantity":1}]}}'
```

---

## 7. 関連ドキュメント

| ドキュメント | 内容 |
|-------------|------|
| [CLOUDRUN_ENV.md](./CLOUDRUN_ENV.md) | 環境変数一覧 |
| [DOCKER_LOCAL_SMOKE.md](./DOCKER_LOCAL_SMOKE.md) | ローカルDockerテスト手順 |
| [DEMO_RUNBOOK.md](./DEMO_RUNBOOK.md) | デモ実行手順 |
| [DEMO_FALLBACK_DOCKER.md](./DEMO_FALLBACK_DOCKER.md) | Cloud Run障害時の代替手順 |

---

## 8. 結論

**現在のCloud Runサービスは正常に稼働中**である。

- 基本機能（/health, /classify）: 正常動作
- オプション機能（/classify_pdf, DocAI, Vertex Search）: 未有効化（デフォルト設定）
- 追加機能が必要な場合は、上記「5. 追加機能の有効化手順」を参照

---

*本レポートは自動確認により生成されました。gcloud認証が利用できなかったため、HTTP接続による動作確認を実施しています。*
