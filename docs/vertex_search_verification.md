# Vertex AI Search 動作検証レポート

> **Version**: 1.0.0
> **Last Updated**: 2026-01-30
> **Purpose**: VERTEX_SEARCH_ENABLED=1 での動作確認とデモ準備

---

## 1. 実装概要

### 1.1 ファイル構成

| ファイル | 役割 |
|---------|------|
| `api/vertex_search.py` | Vertex AI Search (Discovery Engine) 連携モジュール |
| `api/main.py` | FastAPI エンドポイント（`/classify`, `/classify_pdf`）から呼び出し |

### 1.2 機能概要

Vertex AI Search は **法令・税務規則の検索機能** を提供する。固定資産判定で GUIDANCE（要確認）が発生した場合に、関連する法令エビデンスを検索して補足情報として提示する。

```
GUIDANCE判定 → Vertex AI Search で法令検索 → citations として返却
```

---

## 2. 環境変数一覧

### 2.1 必須環境変数

| 変数名 | 説明 | 例 |
|--------|------|-----|
| `VERTEX_SEARCH_ENABLED` | Feature Flag（1で有効化） | `1` |
| `GOOGLE_CLOUD_PROJECT` | GCPプロジェクトID | `my-project-123` |
| `DISCOVERY_ENGINE_DATA_STORE_ID` | Discovery Engine データストアID | `fixed-asset-laws_1234567890` |

### 2.2 設定方法

**PowerShell（ローカル）:**
```powershell
$env:VERTEX_SEARCH_ENABLED="1"
$env:GOOGLE_CLOUD_PROJECT="your-project-id"
$env:DISCOVERY_ENGINE_DATA_STORE_ID="your-datastore-id"
```

**Cloud Run デプロイ時:**
```bash
gcloud run deploy fixed-asset-agentic-api \
  --set-env-vars="VERTEX_SEARCH_ENABLED=1,GOOGLE_CLOUD_PROJECT=your-project-id,DISCOVERY_ENGINE_DATA_STORE_ID=your-datastore-id" \
  ...
```

### 2.3 依存ライブラリ

```bash
pip install google-cloud-discoveryengine>=0.11.0
```

**注意**: `requirements.txt` ではオプション依存としてコメントアウトされている。有効化時のみインストールが必要。

---

## 3. API 動作詳細

### 3.1 search_legal_citations 関数

**場所**: `api/vertex_search.py:18`

```python
def search_legal_citations(
    query: str,
    project_id: Optional[str] = None,
    location: str = "global",
    data_store_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
```

**動作フロー:**
1. Feature Flag チェック（`VERTEX_SEARCH_ENABLED`）
2. 環境変数チェック（`GOOGLE_CLOUD_PROJECT`, `DISCOVERY_ENGINE_DATA_STORE_ID`）
3. Discovery Engine クライアント初期化
4. 検索リクエスト実行（page_size=3）
5. 結果をcitation形式に変換

**レスポンス形式:**
```json
[
  {
    "title": "法人税法施行令第133条",
    "snippet": "資本的支出と修繕費の区分...",
    "uri": "https://elaws.e-gov.go.jp/...",
    "relevance_score": 0.85
  }
]
```

### 3.2 get_citations_for_guidance 関数

**場所**: `api/vertex_search.py:104`

GUIDANCE 判定時のコンテキストから検索クエリを自動生成する。

**クエリ生成ロジック:**
1. description からキーワード抽出（ストップワード除外）
2. 「固定資産 判定」を追加
3. flags に応じて追加キーワード:
   - `mixed_keyword` → 「修繕費 資本的支出」
   - `amount` → 「金額基準 20万円 60万円」

**例:**
- 入力: description=「空調設備の修繕」, flags=["mixed_keyword"]
- 生成クエリ: 「空調設備 修繕 固定資産 判定 修繕費 資本的支出」

### 3.3 main.py での呼び出し

**場所**: `api/main.py:244-263`

```python
# Google Cloud: Vertex AI Search for legal citations (if GUIDANCE and feature enabled)
citations: List[Dict[str, Any]] = []
if initial_response.decision == "GUIDANCE" and VERTEX_SEARCH_AVAILABLE:
    # Collect context from guidance items
    guidance_items = [...]
    if guidance_items:
        item = guidance_items[0]
        citations = get_citations_for_guidance(
            description=item.get("description", ""),
            missing_fields=initial_response.missing_fields,
            flags=item.get("flags", []),
        )
        if citations:
            trace_steps.append("law_search")
```

**条件:**
- decision が GUIDANCE であること
- VERTEX_SEARCH_AVAILABLE が True（インポート成功）
- Feature Flag が有効

---

## 4. 動作確認結果

### 4.1 Feature Flag OFF（デフォルト）

**期待動作**: citations は空リスト、trace に law_search なし

```json
{
  "decision": "GUIDANCE",
  "citations": [],
  "trace": ["extract", "parse", "rules", "format"]
}
```

**確認結果**: OK（graceful degradation 設計）

### 4.2 Feature Flag ON（環境変数未設定）

**期待動作**: 環境変数チェックで早期リターン、空リスト返却

**確認結果**: OK（graceful degradation）

### 4.3 Feature Flag ON（ライブラリ未インストール）

**期待動作**: ImportError をキャッチ、空リスト返却

**確認結果**: OK（例外ハンドリング済み）

### 4.4 Feature Flag ON（フル設定）

**期待動作**: Discovery Engine に検索リクエスト、citations 返却

**前提条件:**
- GCP プロジェクトで Discovery Engine API 有効化
- データストア作成済み（法令データインデックス済み）
- 認証情報設定済み（`GOOGLE_APPLICATION_CREDENTIALS` または Cloud Run サービスアカウント）

---

## 5. デモ時の使い方

### 5.1 デモシナリオ（GUIDANCE + Citations）

1. **Feature Flag 有効化確認**
   - サイドバーで「Legal Citations: ON」を確認
   - （OFF の場合は「Legal Citations: OFF」と表示）

2. **GUIDANCE ケースを実行**
   - `demo04_guidance_ambiguous.json` を選択
   - 「Classify」をクリック

3. **Citations 表示を確認**
   - 「Legal Citations (Google Cloud Search)」セクションが表示
   - citation カード: title, snippet, URI, relevance_score

4. **DIFF カードで Citations 変化を確認**
   - Re-run 後、Citations count: `0 → 3`（または取得件数）

### 5.2 デモ用ナレーション例

> 「GUIDANCE 判定が出ました。ここで Google Cloud の Vertex AI Search が自動的に関連法令を検索します。」
>
> 「この Citations セクションをご覧ください。法人税法施行令の該当条文が検索され、判定根拠の補足情報として表示されています。」
>
> 「これにより、担当者は法令を参照しながら判断できます。」

### 5.3 トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| Citations が表示されない | Feature Flag OFF | `VERTEX_SEARCH_ENABLED=1` を設定 |
| Citations が空 | 環境変数未設定 | `GOOGLE_CLOUD_PROJECT`, `DISCOVERY_ENGINE_DATA_STORE_ID` を設定 |
| ImportError | ライブラリ未インストール | `pip install google-cloud-discoveryengine>=0.11.0` |
| 認証エラー | GCP 認証情報なし | `gcloud auth application-default login` または サービスアカウント設定 |
| 検索結果なし | データストアにデータなし | Discovery Engine にドキュメントをインデックス |

---

## 6. テストクエリ例

### 6.1 固定資産判定テストケース

以下のテストクエリは **core/classifier.py** による判定テストであり、Vertex AI Search 自体のテストではない点に注意。

| 入力 | 期待判定 | 備考 |
|------|----------|------|
| パソコン 25万円 | CAPITAL_LIKE | 20万円超、IT機器 |
| ボールペン 500円 | EXPENSE_LIKE | 少額、消耗品 |
| 応接セット 15万円 | GUIDANCE | 金額が閾値付近、用途確認必要 |
| サーバー新設工事 100万円 | CAPITAL_LIKE | 「新設」キーワード |
| 空調設備修繕 50万円 | GUIDANCE | 「修繕」は mixed_keyword |

### 6.2 Vertex AI Search テストクエリ

Vertex AI Search の動作確認には、Discovery Engine の検索クエリをテストする。

| 検索クエリ | 期待結果 |
|-----------|----------|
| 「固定資産 判定 20万円」 | 金額基準に関する法令条文 |
| 「修繕費 資本的支出 区分」 | 法人税法施行令の区分基準 |
| 「減価償却 耐用年数」 | 耐用年数省令の条文 |

---

## 7. アーキテクチャ図

```
┌─────────────────────────────────────────────────────────────┐
│                     /classify エンドポイント                │
├─────────────────────────────────────────────────────────────┤
│  1. Opal JSON 受信                                          │
│  2. adapt_opal_to_v1 (正規化)                               │
│  3. classify_document (判定)                                │
│        ↓                                                    │
│  4. decision == GUIDANCE ?                                  │
│        │                                                    │
│        ├── Yes ──→ get_citations_for_guidance()            │
│        │            │                                       │
│        │            ↓                                       │
│        │    ┌─────────────────────────────┐                │
│        │    │  Vertex AI Search           │                │
│        │    │  (Discovery Engine)         │                │
│        │    │  - 検索クエリ生成           │                │
│        │    │  - 法令検索実行             │                │
│        │    │  - citations 返却           │                │
│        │    └─────────────────────────────┘                │
│        │            ↓                                       │
│        │    trace に "law_search" 追加                     │
│        │                                                    │
│        └── No ───→ citations = []                          │
│                                                             │
│  5. ClassifyResponse 返却                                   │
│     - decision, evidence, citations, trace                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. 規約準拠確認

### 8.1 ハッカソン提出要件との対応

| 要件 | 対応状況 |
|------|----------|
| Google Cloud AI 製品の使用 | Vertex AI Search (Discovery Engine) を使用 |
| 実装箇所 | `api/vertex_search.py` |
| Feature Flag | `VERTEX_SEARCH_ENABLED=1`（デフォルト OFF） |
| デモでの見せ方 | GUIDANCE 時に法令検索、citations 表示、DIFF カードで変化表示 |

### 8.2 Graceful Degradation

Feature Flag OFF 時や障害時も、core 判定機能は正常動作する設計。

---

## 9. まとめ

### 実装完了事項

- [x] `api/vertex_search.py` - Discovery Engine 連携モジュール
- [x] Feature Flag 設計（`VERTEX_SEARCH_ENABLED`）
- [x] Graceful degradation（障害時も判定継続）
- [x] `api/main.py` での統合（GUIDANCE 時に自動検索）
- [x] UI 表示対応（citations セクション、DIFF カード）

### デモ準備チェックリスト

- [ ] GCP プロジェクトで Discovery Engine API 有効化
- [ ] データストア作成・法令データインデックス
- [ ] 環境変数設定（`VERTEX_SEARCH_ENABLED`, `GOOGLE_CLOUD_PROJECT`, `DISCOVERY_ENGINE_DATA_STORE_ID`）
- [ ] `google-cloud-discoveryengine` インストール
- [ ] 認証情報設定

### 注意事項

1. **デフォルト OFF**: テストや通常の golden set 評価では不要
2. **データストア必須**: 実際の法令検索には Discovery Engine のデータストアが必要
3. **コスト考慮**: Vertex AI Search は従量課金のため、デモ以外は OFF 推奨
