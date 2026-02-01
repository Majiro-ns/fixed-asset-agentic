# REPORT: Docker ローカルスモーク・税務証跡テスト・ENV 整備

**目的**: Cloud Run `ContainerImageImportFailed` の切り分けを早めるため、gcloud を使わずローカルで進められる作業を追加。

---

## What changed

| 種別 | パス | 内容 |
|------|------|------|
| 追加 | `docs/DOCKER_LOCAL_SMOKE.md` | Docker ビルド・起動・HTTP スモークの手順とコピペ用コマンド。`/health` 200、`/classify` 200、`/classify_pdf` 400（`detail.error=PDF_CLASSIFY_DISABLED` および `how_to_enable` / `fallback`）の期待値を記載。 |
| 追加 | `scripts/docker_smoke.ps1` | 上記 3 本の HTTP スモークを実行。`DOCKER_SMOKE_URL` 未設定時は `http://localhost:8080`。失敗時は exit 1。 |
| 追加 | `tests/test_api_response.py` | `test_evidence_tax_rules_reflects_flags_200k`、`test_evidence_tax_rules_reflects_flags_600k` を追加。`evidence[].tax_rules` に `flags` の `tax_rule:*` が反映されることを 200k/600k の最小ケースで検証。 |
| 追加 | `docs/CLOUDRUN_ENV.md` | Cloud Run 用環境変数チェックリスト。`USE_DOCAI` / `GOOGLE_CLOUD_PROJECT` / `DOCAI_PROCESSOR_ID` / `DOCAI_LOCATION`、`PDF_CLASSIFY_ENABLED`、`VERTEX_SEARCH_ENABLED` 等。`/classify_pdf` OFF 時の期待（400、`detail.error` / `how_to_enable` / `fallback`）を明記。 |
| 変更 | `scripts/cloudrun_triage_and_fix.ps1` | 末尾の「報告時に貼るべき3点」を整理。(1) services describe の完全出力とコマンド、(2) revisions describe の完全出力とコマンド、(3) IAM 実行の有無。gcloud の実行は増やしていない。 |

- **core/\***: 未変更。

---

## How to test

### ゲート（pytest / eval_golden）

```powershell
cd c:\Users\owner\Desktop\fixed-asset-agentic-repo
python -m pytest -q
python scripts\eval_golden.py
```

- **期待**: pytest 12 passed、eval_golden 10/10。

### Docker ローカルスモーク（Docker が使える環境）

```powershell
docker build -t fixed-asset-api .
docker run --rm -e PORT=8080 -p 8080:8080 fixed-asset-api
```

別ターミナル:

```powershell
.\scripts\docker_smoke.ps1
```

- **期待**: `=== All docker smoke tests passed ===`、exit 0。

### 手順ドキュメント

- `docs/DOCKER_LOCAL_SMOKE.md` に上記と同じビルド・起動・スモークのコピペ用コマンドを記載。
