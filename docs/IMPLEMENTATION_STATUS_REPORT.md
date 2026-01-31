# 実装状況レポート（Implementation Status Report）
**作成日**: 2026-01-24  
**目的**: ハッカソン提出（2/13締切）に向けた実装状況の把握とギャップ分析

---

## 1. 現在の構造（フォルダ階層と各ディレクトリの役割）

### 1.1 ディレクトリ構造

```
fixed-asset-agentic-repo/
├── api/                    # FastAPI エンドポイント
│   ├── main.py            # POST /classify, /classify_pdf, /health
│   └── vertex_search.py  # Vertex AI Search統合（feature-flagged）
├── core/                   # コアロジック（凍結スキーマ v1.0）
│   ├── adapter.py         # Opal JSON → 正規化スキーマ変換
│   ├── classifier.py     # 3値判定（CAPITAL_LIKE/EXPENSE_LIKE/GUIDANCE）
│   ├── pdf_extract.py    # PDF抽出（PyMuPDF/pdfplumber、DocAI未実装）
│   ├── pipeline.py       # パイプライン実行（PDF/JSON）
│   ├── policy.py         # 企業ポリシー読み込み
│   └── schema.py         # 凍結スキーマ定義（v1.0）
├── ui/                     # Streamlit UI
│   ├── app_minimal.py    # メインUI（Agentic loop実装済み）
│   └── app.py            # 旧UI（非推奨）
├── data/                   # データディレクトリ
│   ├── demo/             # デモ用JSON（架空データ）
│   ├── golden/            # 評価用テストケース（10ケース）
│   └── uploads/           # PDFアップロード保存先
├── policies/               # 企業ポリシー設定
│   └── company_default.json
├── tests/                  # テスト
│   ├── test_pipeline.py
│   ├── test_pdf_extract.py
│   └── test_api_response.py
├── scripts/                # ユーティリティスクリプト
│   ├── eval_golden.py    # ゴールデンセット評価（10/10通過）
│   ├── smoke_cloudrun.ps1 # Cloud Runスモークテスト
│   └── demo_ui.ps1       # UI起動スクリプト
└── docs/                   # ドキュメント
    ├── specs/             # 仕様書（2026-FA-01〜04）
    ├── COMPLIANCE_CHECKLIST.md
    └── IMPLEMENTATION_AUDIT_REPORT.md
```

### 1.2 各ディレクトリの役割

| ディレクトリ | 役割 | 重要度 |
|------------|------|--------|
| `core/` | **凍結スキーマ v1.0** の実装。変更禁止（README.mdで明記）。 | P0 |
| `api/` | Cloud Runデプロイ用FastAPI。Agentic loop（answers処理）実装済み。 | P0 |
| `ui/` | Streamlit UI。GUIDANCE時の質問→再実行→DIFF表示を実装。 | P0 |
| `data/golden/` | 評価用テストケース（10ケース、100%通過）。 | P0 |
| `policies/` | 企業別キーワード・閾値設定（company_default.json）。 | P1 |
| `docs/specs/` | 仕様書（PDF抽出、ルール判定、AI候補提示、耐用年数）。 | P2 |

---

## 2. 機能マップ（各主要ファイルの実装状況）

### 2.1 コアロジック（`core/`）

| ファイル | 実装状況 | 主要機能 | 欠けている要素 |
|---------|---------|---------|--------------|
| `core/adapter.py` | ✅ 完了 | Opal JSON → 正規化スキーマ（v1.0）変換 | なし |
| `core/classifier.py` | ⚠️ **部分実装** | キーワードベース3値判定（CAPITAL/EXPENSE/GUIDANCE） | **税務基準未実装**（10万/20万/30万/60万ルール） |
| `core/pdf_extract.py` | ⚠️ **部分実装** | PyMuPDF/pdfplumberによるローカル抽出 | **DocAI未実装**（`_try_docai()`はplaceholder） |
| `core/pipeline.py` | ✅ 完了 | PDF/JSONパイプライン実行 | なし |
| `core/policy.py` | ✅ 完了 | 企業ポリシー読み込み | なし |
| `core/schema.py` | ✅ 完了 | 凍結スキーマ定義（v1.0） | なし |

### 2.2 API層（`api/`）

| ファイル | 実装状況 | 主要機能 | 欠けている要素 |
|---------|---------|---------|--------------|
| `api/main.py` | ✅ **Agentic loop実装済み** | POST /classify（answers対応）、POST /classify_pdf（feature-flagged）、GET /health | Vertex AI統合は`vertex_search.py`経由のみ |
| `api/vertex_search.py` | ⚠️ **部分実装** | Vertex AI Search（Discovery Engine）統合 | **GUIDANCE時のみ呼び出し**。classifier.py内での直接統合なし |

### 2.3 UI層（`ui/`）

| ファイル | 実装状況 | 主要機能 | 欠けている要素 |
|---------|---------|---------|--------------|
| `ui/app_minimal.py` | ✅ **Agentic loop実装済み** | GUIDANCE時の質問→回答→再実行→DIFF表示（Step 1-5対応） | なし |

### 2.4 評価・テスト

| ファイル | 実装状況 | 結果 |
|---------|---------|------|
| `scripts/eval_golden.py` | ✅ 完了 | **10/10通過（100% accuracy）** |
| `tests/test_pipeline.py` | ✅ 完了 | パイプライン動作確認 |
| `tests/test_pdf_extract.py` | ✅ 完了 | PDF抽出動作確認 |

---

## 3. 成果物の定義（ゴールイメージ）

### 3.1 入力フロー

1. **ユーザー**: 見積書PDFまたはOpal JSONをアップロード
2. **システム**: 
   - PDF → `core/pdf_extract.py`で抽出（現状: PyMuPDF/pdfplumber、**DocAI未実装**）
   - Opal JSON → `core/adapter.py`で正規化
3. **システム**: `core/classifier.py`で3値判定
   - **現状**: キーワードベース判定のみ
   - **欠如**: 税務基準（10万/20万/30万/60万ルール）未実装

### 3.2 Agenticな挙動（推論と判断のループ）

**実装済み（`api/main.py` + `ui/app_minimal.py`）:**

1. **止まる（GUIDANCE）**: `classifier.py`が`GUIDANCE`を返す
2. **根拠提示**: `_format_classify_response()`が`evidence`, `missing_fields`, `why_missing_matters`を生成
3. **質問**: UIが`missing_fields`をフォーム表示、`why_missing_matters`を説明
4. **再実行**: ユーザーが`answers`を入力 → `api/main.py`の`classify()`が`request.answers`を受け取り、`enhanced_opal`で再分類
5. **差分保存**: UIが`prev_result`と`result`を比較し、DIFF card表示（Decision/Confidence/Trace/Citations）

**推論ループの形成箇所:**
- **`api/main.py:262-281`**: `if initial_response.decision == "GUIDANCE" and request.answers` → 再分類ロジック
- **`ui/app_minimal.py:343-473`**: GUIDANCE時の質問フォーム → 再実行ボタン → DIFF表示

### 3.3 出力

**APIレスポンス（`ClassifyResponse`）:**
```json
{
  "decision": "CAPITAL_LIKE|EXPENSE_LIKE|GUIDANCE",
  "reasons": ["判定理由"],
  "evidence": [{"line_no": 1, "description": "...", "confidence": 0.8, ...}],
  "is_valid_document": true,
  "confidence": 0.8,
  "trace": ["extract", "parse", "rules", "format"],
  "missing_fields": ["field1", "field2"],
  "why_missing_matters": ["不足情報の影響説明"],
  "citations": []  // Vertex AI Search結果（GUIDANCE時のみ、feature-flagged）
}
```

**UI表示:**
- Decision badge（CAPITAL_LIKE/EXPENSE_LIKE/GUIDANCE）
- Evidence panel（confidence付き）
- GUIDANCE時: 質問フォーム → 再実行 → DIFF card（Before → After）

---

## 4. 実装のギャップ分析

### 4.1 Google Cloud Native要素の欠如

#### 4.1.1 `core/pdf_extract.py`のDocAI未実装

**現状:**
- `_try_docai()`関数（98-100行目）は`return None`のplaceholder
- ローカル抽出（PyMuPDF/pdfplumber）のみ実装

**欠如:**
- **Google Cloud Document AI（DocAI）統合が未実装**
- ハッカソン要件「Google Cloud AIを主要技術として使用」に不十分

**修正箇所:**
- `core/pdf_extract.py:98-100`の`_try_docai()`を実装
- 必要なライブラリ: `google-cloud-documentai`（`requirements.txt`に未追加）

#### 4.1.2 `core/classifier.py`のVertex AI/Gemini統合なし

**現状:**
- キーワードベースのルール判定のみ
- Vertex AI Searchは`api/vertex_search.py`経由でGUIDANCE時のみ呼び出し

**欠如:**
- **Vertex AI Gemini APIによる推論・判断支援が未実装**
- 複雑なケース（金額基準とキーワードの組み合わせ）でGeminiによる補助判断がない

**修正箇所:**
- `core/classifier.py`に`_classify_with_gemini()`関数を追加
- 必要なライブラリ: `google-cloud-aiplatform`（`requirements.txt`に未追加）

#### 4.1.3 Vertex AI Searchの統合範囲が限定的

**現状:**
- `api/vertex_search.py`はGUIDANCE時のみ呼び出し（`api/main.py:240-259`）
- 検索クエリは`get_citations_for_guidance()`で生成（description + flags）

**改善余地:**
- CAPITAL_LIKE/EXPENSE_LIKE判定時にも税務ルール参照を追加可能
- ただし、現状でも「GUIDANCE時に法令エビデンスを提示」は要件を満たす

### 4.2 日本の税務基準（10/20/30/60万ルール）の実装漏れ

#### 4.2.1 金額基準ルールの未実装

**現状:**
- `core/classifier.py`には`threshold_amount`チェック（116-127行目）があるが、**具体的な税務基準が未実装**
- `policies/company_default.json`の`guidance_amount_jpy: 1000000`は企業ポリシーであり、税法基準ではない

**欠如:**
- **10万円基準**: 少額固定資産の判定（取得価額10万円未満は費用処理可能）
- **20万円基準**: 一括償却資産の判定（20万円未満60万円以上は一括償却）
- **30万円基準**: 中小企業の特例（30万円未満は費用処理可能、条件付き）
- **60万円基準**: 修繕費の判定（60万円未満 or 取得価額の10%以下は修繕費）

**修正箇所:**
- `core/classifier.py:71-146`の`classify_line_item()`に税務基準ロジックを追加
- 具体的な関数名: `_apply_tax_rules(item: Dict[str, Any]) -> Dict[str, Any]`
- 必要な情報: `item.get("amount")`, `item.get("description")`, 取得価額（total_amountから推定）

#### 4.2.2 税務ルール名の証跡化不足

**現状:**
- `flags`に`"policy:amount_threshold"`は追加されるが、**適用された税務ルール名（例: "R-AMOUNT-001"）が`evidence`に含まれていない**

**欠如:**
- `docs/specs/2026-FA-02-rule-preclassification.md`で定義されたルールID（R-AMOUNT-001, R-DESC-002等）が出力されない

**修正箇所:**
- `core/classifier.py`の`classify_line_item()`で、適用された税務ルールIDを`flags`または`evidence`に追加
- 例: `flags.append("tax_rule:R-AMOUNT-001:20万円基準")`

---

## 5. 直近のロードマップ（P0タスクの具体的な修正手順）

### 5.1 P0-1: Vertex AI統合（DocAI + Gemini）

#### 5.1.1 `core/pdf_extract.py`にDocAI統合を追加

**ファイル**: `core/pdf_extract.py`

**修正内容:**
1. `requirements.txt`に追加: `google-cloud-documentai>=2.20.0`
2. `_try_docai()`関数を実装（98-100行目を置き換え）:

```python
def _try_docai(path: Path) -> Optional[Dict[str, Any]]:
    """Extract PDF using Google Cloud Document AI."""
    if not _bool_env("USE_DOCAI", False):
        return None
    
    try:
        from google.cloud import documentai
        
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("DOCAI_LOCATION", "us")
        processor_id = os.getenv("DOCAI_PROCESSOR_ID")
        
        if not project_id or not processor_id:
            return None
        
        client = documentai.DocumentProcessorServiceClient()
        processor_name = client.processor_path(project_id, location, processor_id)
        
        with open(path, "rb") as f:
            raw_document = documentai.RawDocument(content=f.read(), mime_type="application/pdf")
        
        request = documentai.ProcessRequest(name=processor_name, raw_document=raw_document)
        result = client.process_document(request=request)
        document = result.document
        
        pages: List[Dict[str, Any]] = []
        for i, page in enumerate(document.pages):
            text = page.text if hasattr(page, 'text') else ""
            pages.append({"page": i + 1, "text": text, "method": "docai"})
        
        return {
            "meta": {
                "filename": path.name,
                "sha256": _compute_sha256(path),
                "num_pages": len(pages),
                "extracted_at": datetime.datetime.utcnow().isoformat() + "Z",
                "source": "docai",
                "warnings": [],
            },
            "pages": pages,
        }
    except ImportError:
        return None
    except Exception:
        return None
```

**環境変数追加:**
- `USE_DOCAI=1`（feature flag）
- `GOOGLE_CLOUD_PROJECT`（必須）
- `DOCAI_LOCATION`（デフォルト: "us"）
- `DOCAI_PROCESSOR_ID`（必須）

#### 5.1.2 `core/classifier.py`にGemini統合を追加

**ファイル**: `core/classifier.py`

**修正内容:**
1. `requirements.txt`に追加: `google-cloud-aiplatform>=1.38.0`
2. 新しい関数を追加（`classify_line_item()`の前に）:

```python
def _classify_with_gemini(
    item: Dict[str, Any],
    context: Dict[str, Any],
) -> Optional[Dict[str, str]]:
    """
    Use Vertex AI Gemini to assist classification for ambiguous cases.
    Returns: {"classification": "CAPITAL_LIKE|EXPENSE_LIKE|GUIDANCE", "reason": "..."} or None
    """
    if not _bool_env("USE_GEMINI", False):
        return None
    
    try:
        from vertexai.generative_models import GenerativeModel
        
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GEMINI_LOCATION", "us-central1")
        
        if not project_id:
            return None
        
        # Build prompt
        description = item.get("description", "")
        amount = item.get("amount")
        prompt = f"""
        固定資産判定の補助判断を依頼します。
        
        明細: {description}
        金額: {amount}円
        
        以下の基準で判定してください:
        - 10万円未満: 少額固定資産（費用処理可能）
        - 20万円未満60万円以上: 一括償却資産
        - 60万円未満 or 取得価額の10%以下: 修繕費（費用）
        - それ以外: 固定資産（資産計上）
        
        判定結果（CAPITAL_LIKE/EXPENSE_LIKE/GUIDANCE）と理由をJSON形式で返してください。
        """
        
        model = GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        
        # Parse response (simple JSON extraction)
        # In production, use structured output
        # For now, return None to fall back to rule-based
        return None  # Placeholder: implement JSON parsing
        
    except ImportError:
        return None
    except Exception:
        return None
```

3. `classify_line_item()`内で呼び出し（キーワード判定の後）:

```python
# After keyword-based classification (line 99)
if classification == schema.GUIDANCE:
    gemini_result = _classify_with_gemini(item, {"document_info": doc.get("document_info", {})})
    if gemini_result:
        classification = gemini_result.get("classification", schema.GUIDANCE)
        flags.append("gemini_assisted")
```

**環境変数追加:**
- `USE_GEMINI=1`（feature flag）
- `GOOGLE_CLOUD_PROJECT`（必須）
- `GEMINI_LOCATION`（デフォルト: "us-central1"）

### 5.2 P0-2: 税務ロジック修正（10/20/30/60万ルール）

#### 5.2.1 `core/classifier.py`に税務基準関数を追加

**ファイル**: `core/classifier.py`

**修正内容:**
1. 新しい関数を追加（`classify_line_item()`の前に）:

```python
def _apply_tax_rules(item: Dict[str, Any], total_amount: Optional[float] = None) -> Dict[str, Any]:
    """
    Apply Japanese tax rules (10万/20万/30万/60万基準).
    Returns: {"rule_id": "R-AMOUNT-001", "classification_hint": "CAPITAL_LIKE|EXPENSE_LIKE|GUIDANCE", "reason": "..."}
    """
    amount = item.get("amount")
    if not isinstance(amount, (int, float)) or amount <= 0:
        return {}
    
    rules_applied = []
    classification_hint = None
    reason = ""
    
    # 10万円基準: 少額固定資産（10万円未満は費用処理可能）
    if amount < 100000:
        rules_applied.append("R-AMOUNT-003")
        classification_hint = "EXPENSE_LIKE"
        reason = "10万円未満のため少額固定資産（費用処理可能）"
    
    # 20万円基準: 一括償却資産（20万円未満60万円以上）
    elif 200000 <= amount < 600000:
        rules_applied.append("R-AMOUNT-001")
        classification_hint = "CAPITAL_LIKE"
        reason = "20万円以上60万円未満のため一括償却資産"
    
    # 60万円基準: 修繕費判定（60万円未満 or 取得価額の10%以下）
    elif amount < 600000:
        if total_amount and amount <= total_amount * 0.1:
            rules_applied.append("R-AMOUNT-002")
            classification_hint = "EXPENSE_LIKE"
            reason = "60万円未満かつ取得価額の10%以下のため修繕費"
        else:
            rules_applied.append("R-AMOUNT-002")
            classification_hint = "GUIDANCE"
            reason = "60万円未満だが取得価額の10%超過の可能性（要確認）"
    
    # 60万円以上: 固定資産
    else:
        rules_applied.append("R-AMOUNT-004")
        classification_hint = "CAPITAL_LIKE"
        reason = "60万円以上のため固定資産計上"
    
    return {
        "rule_id": rules_applied[0] if rules_applied else None,
        "rules_applied": rules_applied,
        "classification_hint": classification_hint,
        "reason": reason,
    }
```

2. `classify_line_item()`内で呼び出し（キーワード判定の前または後）:

```python
# After keyword-based classification (line 99)
tax_result = _apply_tax_rules(item, doc.get("totals", {}).get("total"))
if tax_result.get("rule_id"):
    # Add tax rule to flags
    flags.append(f"tax_rule:{tax_result['rule_id']}:{tax_result['reason']}")
    
    # If keyword-based classification is GUIDANCE, use tax rule hint
    if classification == schema.GUIDANCE and tax_result.get("classification_hint"):
        classification = tax_result["classification_hint"]
        rationale_ja = f"{tax_result['reason']}（{tax_result['rule_id']}適用）"
```

#### 5.2.2 税務ルールIDを`evidence`に追加

**ファイル**: `api/main.py`

**修正内容:**
1. `_format_classify_response()`内で、`flags`から税務ルールIDを抽出して`evidence`に追加（104-120行目の`evidence`構築部分）:

```python
# In evidence construction loop (around line 104-120)
evidence_item = {
    "line_no": item.get("line_no"),
    "description": item.get("description"),
    "source_text": ev.get("source_text", ""),
    "position_hint": ev.get("position_hint", ""),
    "confidence": ev.get("confidence", 0.8),
}

# Extract tax rule IDs from flags
flags = item.get("flags", [])
tax_rules = [f for f in flags if isinstance(f, str) and f.startswith("tax_rule:")]
if tax_rules:
    evidence_item["tax_rules"] = tax_rules

evidence.append(evidence_item)
```

### 5.3 実装順序（推奨）

1. **P0-2（税務ロジック）を先に実装**（Gemini統合より優先）
   - 理由: ハッカソン要件「税務基準の正確性」が審査の核心
   - 所要時間: 2-3時間
2. **P0-1（Vertex AI統合）を実装**
   - DocAI統合: 1-2時間
   - Gemini統合: 2-3時間
   - 合計: 3-5時間

### 5.4 テスト要件

**各修正後に必須:**
1. `python -m pytest -q` → 10 passed（exit code 0）
2. `python scripts/eval_golden.py` → 10/10 passed（100% accuracy）
3. `git diff --name-only | Select-String '^core/'` → 変更確認（core/*は慎重に）

---

## 6. Agentic AIとしての推論と判断のループ形成箇所

### 6.1 現在のループ形成

**場所1: `api/main.py:262-281`（再分類ロジック）**
```python
if initial_response.decision == "GUIDANCE" and request.answers and initial_response.missing_fields:
    # Check if answers cover missing fields
    answered_fields = set(request.answers.keys())
    missing_set = set(initial_response.missing_fields)
    if answered_fields and any(k in str(mf).lower() for mf in missing_set for k in answered_fields):
        trace_steps.append("rerun_with_answers")
        # Apply answers to opal_json
        enhanced_opal = opal_json.copy()
        enhanced_opal["document_info"]["user_answers"] = request.answers
        # Rerun classification
        enhanced_normalized = adapt_opal_to_v1(enhanced_opal)
        enhanced_classified = classify_document(enhanced_normalized, policy)
        return _format_classify_response(enhanced_classified, trace_steps=trace_steps, citations=citations)
```

**場所2: `ui/app_minimal.py:343-473`（UI側のループ）**
- GUIDANCE判定時に質問フォーム表示
- ユーザーが回答入力 → "Re-run Classification with Answers"ボタン
- 再実行後、`prev_result`と`result`を比較してDIFF card表示

### 6.2 推論ループの強化案（P1タスク）

**現状の課題:**
- `answers`の適用が単純なマージ（`document_info.user_answers`に追加）のみ
- 回答内容に基づく分類ロジックの調整がない

**改善案:**
- `core/classifier.py`に`classify_with_answers()`関数を追加
- `answers`の内容（例: `{"purpose": "repair"}`）に基づいて分類ロジックを調整
- ただし、**Stop-first設計を維持**（断定はしない）

---

## 7. まとめ

### 7.1 実装完了項目

- ✅ Agentic 5-step loop（止まる→根拠提示→質問→再実行→差分保存）
- ✅ キーワードベース分類（CAPITAL/EXPENSE/GUIDANCE）
- ✅ PDF抽出（ローカル実装）
- ✅ Cloud Runデプロイ準備
- ✅ ゴールデンセット評価（10/10通過）

### 7.2 実装不足項目（P0）

- ❌ **Google Cloud Document AI統合**（`core/pdf_extract.py`）
- ❌ **Vertex AI Gemini統合**（`core/classifier.py`）
- ❌ **税務基準実装**（10万/20万/30万/60万ルール）

### 7.3 優先順位

1. **P0-2: 税務ロジック修正**（2-3時間）
2. **P0-1: Vertex AI統合**（3-5時間）

**合計所要時間**: 5-8時間

### 7.4 リスク

- **core/*変更**: README.mdで「変更禁止」と明記されているが、P0タスクのため必要
- **ゲート維持**: `pytest -q`と`eval_golden.py`が常に通過することを確認
- **デプロイ**: Cloud Runデプロイ後のスモークテスト必須

---

**次のアクション**: P0-2（税務ロジック修正）から着手し、その後P0-1（Vertex AI統合）を実装。
