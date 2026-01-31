# Dockerfile / 起動要件 静的チェック REPORT

**対象**: `Dockerfile`, `api/main.py`, `requirements.txt`（実行は未実施）

---

## CMD と PORT / 0.0.0.0

| 項目 | 状態 |
|------|------|
| PORT | `ENV PORT=8080` でデフォルト設定。`CMD` 内で `--port ${PORT:-8080}` により Cloud Run の `PORT` を利用。問題なし。 |
| 0.0.0.0 | `uvicorn ... --host 0.0.0.0` で全インターフェース listen。Cloud Run 向けで問題なし。 |

---

## api/main.py の app 名と Dockerfile CMD

| 項目 | 状態 |
|------|------|
| モジュール:app | `api/main.py` に `app = FastAPI(...)` が定義されている。 |
| CMD | `uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8080}` で `api.main:app` を参照。整合している。 |

---

## requirements とビルド

| 項目 | 状態・懸念 |
|------|------------|
| `google-cloud-documentai>=2.20.0` | 常時 `pip install` 対象。**懸念**: イメージサイズ・ビルド時間の増加。grpcio 等の依存で、ごく稀に python:3.11-slim 上で wheel が無くビルドが失敗する可能性はあるが、slim では一般的に wheel が提供されており、リスクは低い。 |
| `google-cloud-discoveryengine` | コメントでオプション扱い。requirements には未記載。未入りでも ImportError で `get_citations_for_guidance` は fallback され、ビルドは壊れない。 |
| その他 (pytest, streamlit, PyMuPDF, fastapi, uvicorn, gunicorn, requests) | 従来どおり。Dockerfile の `pip install -r requirements.txt` でビルドが失敗する要因は見当たらない。 |

---

## 懸念点まとめ（箇条書き）

- **`google-cloud-documentai`**: 常時インストールのため、イメージサイズ・ビルド時間が増える。`USE_DOCAI=1` のときのみ使用するが、未使用時もコンテナには含まれる。
- **gunicorn**: `requirements.txt` にはあるが、`Dockerfile` の `CMD` は uvicorn のみ。gunicorn に切り替える場合は `--bind 0.0.0.0:${PORT}` などの指定が必要になる点に注意。
