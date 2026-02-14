# Docker ローカル起動スモーク

Cloud Run の `ContainerImageImportFailed` 切り分けのため、**gcloud を使わず**ローカルで Docker ビルド・起動・HTTP スモークを実施する手順。

---

## 1. ビルド

```powershell
cd c:\Users\owner\Desktop\fixed-asset-ashigaru
docker build -t fixed-asset-api .
```

- 成功: `Successfully built` / `Successfully tagged fixed-asset-api:latest`
- 失敗: ビルドログを保存し、`docs/DOCKER_STARTUP_REPORT.md` 等を参照

---

## 2. 起動

```powershell
docker run --rm -e PORT=8080 -p 8080:8080 fixed-asset-api
```

- フォアグラウンドで起動。別のターミナルで以下を実行する。
- 停止: `Ctrl+C`

---

## 3. HTTP スモーク（別ターミナル）

### 手動

```powershell
# /health
curl.exe -s http://localhost:8080/health
# 期待: {"ok":true}

# /classify
curl.exe -s -X POST http://localhost:8080/classify -H "Content-Type: application/json" -d "{\"opal_json\":{\"invoice_date\":\"2024-01-01\",\"vendor\":\"ACME\",\"line_items\":[{\"item_description\":\"server install\",\"amount\":5000,\"quantity\":1}]}}"
# 期待: JSON に decision, is_valid_document, confidence, trace, missing_fields, why_missing_matters を含む

# /classify_pdf（既定 OFF → 400）
curl.exe -s -X POST http://localhost:8080/classify_pdf -F "file=@tests\fixtures\sample_text.pdf" -w "\n%{http_code}"
# 期待: 400 且つ本文の detail.error=PDF_CLASSIFY_DISABLED, detail.how_to_enable, detail.fallback を含む
```

### 一括（推奨）

```powershell
$env:DOCKER_SMOKE_URL = "http://localhost:8080"
.\scripts\docker_smoke.ps1
```

- コンテナが `http://localhost:8080` で listen している前提。`DOCKER_SMOKE_URL` 未設定時も `http://localhost:8080` を使用。

---

## 4. 期待値

| 項目 | 期待 |
|------|------|
| **/health** | HTTP 200、`{"ok": true}` |
| **/classify** | HTTP 200、`decision`, `is_valid_document`, `confidence`, `trace`, `missing_fields`, `why_missing_matters` を含む |
| **/classify_pdf**（PDF_CLASSIFY_ENABLED 未設定＝OFF） | HTTP 400、`detail.error == "PDF_CLASSIFY_DISABLED"`、`detail.how_to_enable`、`detail.fallback` を含む |

- 全項目が期待どおりなら、`docker_smoke.ps1` は `=== All docker smoke tests passed ===` を出力し exit 0。いずれか失敗で exit 1。

---

## 5. コピペ用（ビルド→起動→スモーク）

**ターミナル 1（起動）:**

```powershell
cd c:\Users\owner\Desktop\fixed-asset-ashigaru
docker build -t fixed-asset-api .
docker run --rm -e PORT=8080 -p 8080:8080 fixed-asset-api
```

**ターミナル 2（スモーク、起動後に実行）:**

```powershell
cd c:\Users\owner\Desktop\fixed-asset-ashigaru
.\scripts\docker_smoke.ps1
```
