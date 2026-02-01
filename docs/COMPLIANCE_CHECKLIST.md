# 規約準拠チェックリスト
## 第4回 Agentic AI Hackathon with Google Cloud 提出要件への準拠確認

本ドキュメントは、ハッカソン参加規約への準拠を確認するためのチェックリストです。

---

## 1. Google Cloud AI 製品の使用

### 要件
指定のGoogle Cloud AI製品・アプリ関連製品を用いること。

### 本プロジェクトでの実装
- **主要技術**: Vertex AI Search / Discovery Engine を主要技術として使用
- **実装箇所**: `api/vertex_search.py`（法令エビデンス検索機能）
- **Feature Flag**: `VERTEX_SEARCH_ENABLED=1`（デフォルトOFF、デモ時のみON）
- **デモでの見せ方**: 
  - GUIDANCE判定時にVertex AI Searchで法令・税務ルールを検索
  - 検索結果を`citations[]`としてAPIレスポンスに含める
  - UIで「Legal Citations (Google Cloud Search)」セクションとして表示
  - DIFFカードでCitations countを表示（`0 → 3`など）

### 確認方法
- `api/vertex_search.py`の実装を確認
- `api/main.py`での呼び出し箇所を確認
- `ui/app_minimal.py`でのCitations表示を確認
- DEMO.mdの「Enable Legal Citations」セクションで有効化手順を確認

**ステータス**: ✅ 実装済み（feature-flagged、デフォルトOFF）

---

## 2. 第三者権利・データ取り扱い

### 要件
- 実在の企業名、請求書、見積書を含めない
- 個人情報・機密情報を含めない
- デモデータはすべて架空（ダミー）データであること

### 本プロジェクトでの対応
- **デモデータ**: `data/demo/*.json` - すべて架空データ
- **評価データ**: `data/golden/*.json` - すべて架空データ
- **明記箇所**: 
  - README.md「デモデータについて」セクション
  - DEMO.md「デモデータについて」セクション

### 確認方法
- `data/demo/` と `data/golden/` のJSONファイルを確認
- 実在の企業名、請求書番号、見積書番号が含まれていないことを確認

**ステータス**: ✅ すべて架空データ（README/DEMOに明記済み）

---

## 3. OSS ライセンス遵守

### 要件
使用しているOSSライブラリのライセンスを遵守し、適切に表記すること。

### 本プロジェクトでの対応
- **表記箇所**: README.md「OSS/Licenses」セクション
- **主要依存関係**:
  - pytest (MIT)
  - streamlit (Apache 2.0)
  - PyMuPDF (fitz) (AGPL-3.0) - 商用利用時は注意
  - fastapi (MIT)
  - uvicorn (BSD)
  - gunicorn (MIT)
  - requests (Apache 2.0)
- **オプション依存関係**:
  - google-cloud-discoveryengine (Apache 2.0)

### 確認方法
- README.md「OSS/Licenses」セクションを確認
- `requirements.txt`の依存関係とライセンス表記が一致していることを確認

**ステータス**: ✅ README.mdに表記済み

---

## 4. 提出物要件

### 要件
以下の提出物をすべて提供すること：
1. コード（GitHubリポジトリ）
2. 説明テキスト＆構成図
3. デモ動画

### 本プロジェクトでの対応

#### 1. コード
- **GitHubリポジトリ**: 本リポジトリ（`fixed-asset-agentic`）
- **主要コンポーネント**:
  - FastAPI（`api/main.py`）: Cloud Run上で動作
  - Streamlit UI（`ui/app_minimal.py`）: デモ用Webインターフェース
  - コアロジック（`core/`）: 分類・正規化・ポリシー適用
  - Vertex AI Search統合（`api/vertex_search.py`）: 法令エビデンス検索

#### 2. 説明テキスト＆構成図
- **README.md**: プロジェクト概要、システム構成、API仕様、デプロイ手順
- **システム構成図**: README.md内のMermaid図（PDF → Opal → UI → Cloud Run → Vertex AI Search）
- **DEMO.md**: デモ手順（タイムライン形式、Agentic 5-step対応）

#### 3. デモ動画
- **デモ手順**: DEMO.mdに記載（3-4分のデモスクリプト）
- **実際の動画**: 別途提出（DEMO.mdの手順に従って録画）

### 確認方法
- README.md「提出物詳細」セクションを確認
- README.mdのMermaid構成図を確認
- DEMO.mdのタイムライン形式デモ手順を確認

**ステータス**: ✅ すべて提供（README.mdに明記済み）

---

## 5. 日本語での記載

### 要件
提出物ドキュメントは日本語で記載すること（英語は補助のみ）。

### 本プロジェクトでの対応
- **README.md**: 日本語を主とする（英語は補助）
- **DEMO.md**: 日本語を主とする（英語は補助）
- **docs/COMPLIANCE_CHECKLIST.md**: 日本語で記載（本ファイル）

### 確認方法
- README.md、DEMO.md、docs/*.md の主要セクションが日本語であることを確認

**ステータス**: ✅ 日本語を主とする（英語は補助）

---

## 6. 免責・責任

### 要件
第三者権利侵害が起きないようにする運用メモを記載すること。

### 本プロジェクトでの対応
- **デモデータ**: すべて架空データ（実在の企業名・請求書・見積書を含めない）
- **運用メモ**: 
  - デモ時は必ず `data/demo/*.json` の架空データを使用
  - 実在の請求書・見積書をアップロードしない
  - 個人情報・機密情報を含むデータを使用しない
- **明記箇所**: 
  - README.md「デモデータについて」セクション
  - DEMO.md「デモデータについて」セクション

### 確認方法
- README.mdとDEMO.mdに「デモデータはすべて架空データ」の明記があることを確認

**ステータス**: ✅ 運用メモをREADME/DEMOに記載済み

---

## 総合確認

| 項目 | ステータス | 確認箇所 |
|------|-----------|---------|
| Google Cloud AI製品の使用 | ✅ | `api/vertex_search.py`, README.md, DEMO.md |
| 第三者権利・データ取り扱い | ✅ | README.md, DEMO.md「デモデータについて」 |
| OSSライセンス遵守 | ✅ | README.md「OSS/Licenses」 |
| 提出物要件（コード/構成図/動画） | ✅ | README.md「提出物詳細」 |
| 日本語での記載 | ✅ | README.md, DEMO.md, docs/*.md |
| 免責・責任（運用メモ） | ✅ | README.md, DEMO.md「デモデータについて」 |

**最終確認日**: 2026-01-24

---

## 補足

- 本チェックリストは提出時の自己確認用です。
- 規約本文は公式サイトで確認してください。
- 不明点がある場合は、ハッカソン運営に問い合わせてください。
