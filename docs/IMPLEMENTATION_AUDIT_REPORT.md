# 実装状況監査レポート
## 第4回 Agentic AI Hackathon with Google Cloud — 優勝必須要素の実装状況

**作成日**: 2026-01-24  
**対象リポジトリ**: `fixed-asset-agentic-repo`  
**提出期限**: 2026-02-13

---

## 1. PDF解析の深度

### 【未着手】

**現状:**
- **実装ファイル**: `core/pdf_extract.py`
- **実装済み機能**:
  - PyMuPDF（fitz）によるテキスト抽出（`_extract_with_fitz`）
  - pdfplumberによるテキスト抽出（`_extract_with_pdfplumber`）
  - pytesseractによるOCR（`_ocr_page_via_fitz`、オプション）
  - 基本的なevidence記録（ページ番号、スニペット）

**未実装機能:**
1. **Gemini 1.5 Proのマルチモーダル機能**
   - コードベース内にGemini/Vertex AIの統合コードが存在しない
   - `requirements.txt`に`google-cloud-aiplatform`や`vertexai`が含まれていない
   - PDFの画像としての理解（レイアウト、表構造、視覚的要素）が未実装

2. **レイアウト解析**
   - `extract_pdf`関数はテキストのみ抽出（`page.get_text("text")`）
   - 表構造の抽出は未実装（`tables: []`は常に空配列）
   - 品目と金額の対応関係の構造化が未実装

3. **DocAI統合**
   - `_try_docai`関数はプレースホルダーのみ（`core/pdf_extract.py:98-100`）
   ```python
   def _try_docai(path: Path) -> Optional[Dict[str, Any]]:
       # Placeholder for DocAI: intentionally returns None. Real implementation should go here.
       return None
   ```

**影響:**
- 審査員から「単なるテキスト抽出ラッパー」と評価されるリスクが高い
- 見積書/請求書の表構造（品目名、数量、単価、金額の対応）を正確に把握できない
- スキャンPDFやレイアウトが複雑な文書での精度が低い

**優先度**: **最高（P0）** — ハッカソンの「Google Cloud Native + Agentic AI」要件に直結

---

## 2. Agenticな推論プロセス

### 【調整中】

**現状:**
- **実装ファイル**: `api/main.py`（`classify`エンドポイント）
- **実装済み機能**:
  - 最小限のagentic loop（`api/main.py:206-225`）
    - GUIDANCE判定時に`answers`を受け取り、再分類を実行
    - `trace_steps`に`rerun_with_answers`を記録
  - ルールベースの分類（`core/classifier.py`）

**未実装機能:**
1. **Vertex AI / Gemini統合**
   - コードベース内にVertex AI SDKの使用箇所が存在しない
   - `DEMO.md:73`に「Next steps: Vertex AI integration」と記載されているが、実装されていない
   - GUIDANCE時にGeminiを呼び出して候補案を生成する機能が未実装

2. **Chain of Thought（思考の連鎖）**
   - 単一のプロンプトで完結する設計ではなく、複数ステップの推論が必要
   - 現状は「キーワードマッチ → GUIDANCE判定 → ユーザー入力待ち」の単純フロー
   - 複数のツール（法令検索、社内規定参照、金額計算）を自律的に使い分ける仕組みが未実装

3. **Vertex AI Search（法令検索）**
   - 税務・会計ルールの参照機能が未実装
   - 国税庁の基本通達や社内規定の検索機能が未実装

4. **AI候補案生成**
   - `docs/specs/2026-FA-03-ai-account-suggestion.md`に仕様が定義されているが、実装されていない
   - 期待される出力: `ai_suggestions`配列（勘定科目候補、confidence、reason）

**影響:**
- 「Agentic AI」としての評価が低い（現状は「ルールベース + 手動入力待ち」）
- 審査員から「自律的な推論プロセスがない」と評価されるリスク

**優先度**: **最高（P0）** — ハッカソンの「Agentic AI」要件の核心

---

## 3. 根拠の提示（Explainability）

### 【実装済み】※一部不足あり

**現状:**
- **実装ファイル**: 
  - `api/main.py`（`_format_classify_response`関数）
  - `core/adapter.py`（`_normalize_evidence`関数）
  - `ui/app_minimal.py`（Evidence表示）

**実装済み機能:**
1. **Evidence構造**
   - `evidence[]`配列に以下を含む:
     - `line_no`: 行番号
     - `description`: 明細の説明
     - `source_text`: 抽出元テキスト
     - `position_hint`: 位置情報
     - `confidence`: 信頼度（0.0-1.0、WIN+1フィールド）
     - `snippets[]`: ページ番号、抽出方法、スニペット

2. **Trace記録**
   - `trace[]`: 実行ステップ（`["extract", "parse", "rules", "format"]`）
   - GUIDANCE時の再実行では`rerun_with_answers`が追加される

3. **UI表示**
   - Streamlit UI（`ui/app_minimal.py`）でEvidenceを展開可能なカードとして表示
   - 各Evidenceにconfidenceを表示

**不足している機能:**
1. **参照した条文・法令の具体的な引用**
   - 判定根拠として「国税庁基本通達 第X条」などの具体的な参照が未実装
   - `evidence`に`legal_reference`や`regulation_citation`フィールドが存在しない

2. **PDF内の具体的な箇所の可視化**
   - `position_hint`は文字列のみ（座標情報やPDF内の矩形情報が未記録）
   - UIでPDFの該当箇所をハイライト表示する機能が未実装

3. **適用されたルールの明示**
   - `core/classifier.py`では`flags`にルールIDが記録されるが、`evidence`に`applied_rule`フィールドが未実装
   - 仕様（`docs/specs/2026-FA-02-rule-preclassification.md`）では`rules_applied[]`が期待されているが、APIレスポンスに含まれていない

**影響:**
- 監査時の根拠追跡は可能だが、「どの法令・ルールに基づいたか」の明示が弱い
- 審査員から「根拠の提示が不十分」と評価される可能性は中程度

**優先度**: **中（P1）** — 実装済み部分は十分だが、法令参照の追加で差別化可能

---

## 4. 未実装・脆弱なポイント

### 4.1 税務ロジックの正確性

**ステータス**: 【調整中】

**現状:**
- **実装ファイル**: `core/classifier.py`
- **実装済み**:
  - キーワードベースの分類（`CAPITAL_KEYWORDS`, `EXPENSE_KEYWORDS`, `MIXED_KEYWORDS`）
  - ポリシーによる閾値チェック（`policy["thresholds"]["guidance_amount_jpy"]`）
  - ポリシーファイル（`policies/company_default.json`）で設定可能

**未実装・不足:**
1. **20万円/60万円/10%基準の具体的な実装**
   - 国税庁の基本通達に基づく形式的判定フローがコードとして明示的に実装されていない
   - `core/classifier.py`には金額閾値のチェックがあるが、20万円/60万円/10%の具体的なロジックが未実装
   - テスト（`tests/test_pipeline.py:21-29`）では`guidance_amount_jpy`の閾値チェックのみ確認

2. **一括償却資産の判定（20万円未満）**
   - コード内に「20万円未満 = 一括償却資産」の判定ロジックが存在しない

3. **修繕費の判定（60万円未満 or 取得価額の10%以下）**
   - 「60万円未満」または「取得価額の10%以下」の判定ロジックが未実装

4. **継続的なメンテナンス vs 価値の向上（新設・増設）の峻別**
   - キーワードベースの判定のみで、金額や文脈を考慮した判定が不足

**影響:**
- 税務・会計の専門家から「形式的判定が不正確」と評価されるリスク
- ハッカソンの「正確性」要件に影響

**優先度**: **高（P0）** — 税務ロジックの正確性は審査の核心

---

### 4.2 判定根拠の可視化（推論プロセスの出力）

**ステータス**: 【調整中】

**現状:**
- `evidence`に`source_text`、`snippets`が含まれる
- `trace`に実行ステップが記録される

**不足:**
1. **`evidence_keywords`フィールドが未実装**
   - どのキーワード（「新設」「交換」など）が検出されたかを明示するフィールドがAPIレスポンスに存在しない
   - `core/classifier.py`では`cap_hits`、`exp_hits`が計算されるが、`evidence`に反映されていない

2. **`applied_rule`フィールドが未実装**
   - 適用された税務ルール名（例: "R-AMOUNT-001", "R-DESC-002"）が`evidence`に含まれていない
   - 仕様（`docs/specs/2026-FA-02-rule-preclassification.md`）では`rules_applied[]`が期待されている

3. **`trace_log`の詳細度が不足**
   - 現状は`["extract", "parse", "rules", "format"]`のような高レベルなステップのみ
   - 各ステップ内の詳細（どのキーワードを検出、どのルールを適用）が記録されていない

**影響:**
- ユーザーが「AIがどこを見て判断したか」を理解しにくい
- 審査員から「推論プロセスの可視化が不十分」と評価される可能性

**優先度**: **中（P1）** — 実装は容易で、差別化効果が高い

---

### 4.3 その他の技術的負債

1. **PDFエンドポイントの未実装**
   - `api/main.py`に`POST /classify_pdf`エンドポイントが存在しない
   - 仕様では「Optional」とされているが、デモでPDFを直接アップロードできない

2. **CI/CDの不完全性**
   - `.github/workflows/ci.yml`は存在するが、Vertex AI統合後のテストが未整備

3. **エラーハンドリングの強化**
   - Vertex AI呼び出し時のタイムアウトやレート制限の処理が未実装

---

## 優先順位付きアクションアイテム

### P0（最優先・必須）— 2/13までに実装必須

1. **Gemini 1.5 Proマルチモーダル統合**
   - `core/pdf_extract.py`にGemini Vision API呼び出しを追加
   - PDFを画像として送信し、レイアウト解析と表構造抽出を実装
   - ファイル: `core/pdf_extract.py`, `requirements.txt`

2. **Vertex AI統合（GUIDANCE時の候補案生成）**
   - `api/main.py`のagentic loop内でGeminiを呼び出し
   - `docs/specs/2026-FA-03-ai-account-suggestion.md`の仕様に基づき`ai_suggestions`を生成
   - ファイル: `api/main.py`, `core/ai_suggestion.py`（新規）

3. **税務ロジックの正確な実装**
   - 20万円/60万円/10%基準を`core/classifier.py`に実装
   - 一括償却資産、修繕費の判定ロジックを追加
   - ファイル: `core/classifier.py`

### P1（高優先度）— 差別化のために実装推奨

4. **根拠の強化（evidence_keywords, applied_rule）**
   - `_format_classify_response`で`evidence_keywords`と`applied_rule`を追加
   - ファイル: `api/main.py`

5. **Vertex AI Search統合（法令検索）**
   - GUIDANCE時に税務ルールを検索し、参照を`evidence`に追加
   - ファイル: `core/legal_search.py`（新規）

6. **PDFエンドポイントの実装**
   - `POST /classify_pdf`を追加
   - ファイル: `api/main.py`

### P2（中優先度）— 時間があれば実装

7. **UI改善（PDF内箇所のハイライト）**
   - Streamlit UIでPDFの該当箇所を可視化
   - ファイル: `ui/app_minimal.py`

8. **CI/CDの強化**
   - Vertex AI統合後のテストを追加
   - ファイル: `.github/workflows/ci.yml`

---

## 実装状況サマリー

| 項目 | ステータス | 実装率 | 優先度 |
|------|-----------|--------|--------|
| PDF解析の深度（Geminiマルチモーダル） | 未着手 | 0% | P0 |
| Agentic推論プロセス（Vertex AI統合） | 調整中 | 20% | P0 |
| 根拠の提示（Explainability） | 実装済み | 70% | P1 |
| 税務ロジックの正確性 | 調整中 | 40% | P0 |
| 判定根拠の可視化（推論プロセス） | 調整中 | 50% | P1 |

**総合評価**: 基礎的なルールベース分類とEvidence記録は実装済みだが、**「Google Cloud Native + Agentic AI」の核心であるVertex AI/Gemini統合が未実装**。2/13までにP0項目の実装が必須。

---

## 次のアクション（即座に実行すべき）

1. **`requirements.txt`に追加**:
   ```
   google-cloud-aiplatform>=1.38.0
   vertexai>=1.38.0
   ```

2. **`core/pdf_extract.py`にGemini Vision統合を追加**（`_try_gemini_vision`関数）

3. **`api/main.py`のagentic loop内でGeminiを呼び出し**（GUIDANCE時の候補案生成）

4. **`core/classifier.py`に税務ロジックを追加**（20万円/60万円/10%基準）

---

**レポート作成者**: AI Assistant  
**次回レビュー推奨日**: 2026-01-27（P0項目の進捗確認）
