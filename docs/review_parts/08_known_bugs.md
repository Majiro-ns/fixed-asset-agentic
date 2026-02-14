# 既知バグ・教訓の確認レビュー

## サマリ

| 項目 | 結果 |
|------|------|
| 確認バグ数 | 2件 |
| Critical | 0件（修正済 or 仕様通り） |
| Major | 1件（デフォルト値0.8の残存パターン） |
| Minor | 1件（集計ロジックの仕様明文化不足） |
| 波及箇所 | 3箇所（api/main.py内のデフォルト0.8パターン） |

---

## 各バグの確認結果

### Bug 1: confidence常に0.80バグ

**深刻度**: Major（修正済だが残存リスクあり）

**元の問題**: `ev.get('confidence', 0.8)` により、confidenceが常に0.80になるバグ。

**確認結果**: **部分的に修正済**

#### 修正された部分（Good）
- `core/classifier.py:129-168` に `_calculate_confidence()` 関数が新設され、分類結果に応じた確信度を計算している
  - CAPITAL_LIKE / EXPENSE_LIKE: 0.85〜0.95（キーワードヒット数に応じてボーナス）
  - GUIDANCE: 0.40〜0.65（理由に応じて段階的）
- `core/classifier.py:262-264` で `classify_line_item()` が確信度を計算し、`item["confidence"]` に格納（line 272）
- これにより、classifierが正常に動作する限り、各itemには適切なconfidenceが設定される

#### 残存する問題（Major）
`api/main.py` 内に **デフォルト値 0.8 が3箇所残存** している:

| 行番号 | コード | リスク |
|--------|--------|--------|
| **212行目** | `item.get("confidence", 0.8)` | evidence構築時。classifierがconfidenceを設定しなかった場合に0.8が使われる |
| **268行目** | `item.get("confidence", 0.8)` | document-level confidence計算時（matching items） |
| **274行目** | `e.get("confidence", 0.8)` | evidence listからのconfidence取得時 |

**問題の本質**: classifierが正常動作している限り問題は顕在化しないが、以下のケースで0.8が暗黙的に適用されうる:
1. classifierの `_calculate_confidence()` が例外を投げた場合（現状try-catchなし）
2. 外部から直接APIにPOSTされたline_itemsにconfidenceフィールドがない場合
3. Geminiがline_item単位でconfidenceを設定しなかった場合

**修正提案**: デフォルト値を `0.8` → `0.0` または `None` に変更し、「confidence未計算」を明示的に区別できるようにする。0.8は「それなりに高い確信度」を意味するため、フォールバック値として不適切。

#### 他の比較的安全なデフォルト値
- `api/main.py:42` - Gemini未インストール時: `confidence: 0.0` → **適切**（未計算であることが明確）
- `api/main.py:272` - `else 0.7` → 準適切（matching_confidencesが空の場合のフォールバック）
- `api/main.py:275` - `else 0.5` → 準適切（evidenceが空の場合のフォールバック）

---

### Bug 2: 集計ロジック「1つでもGUIDANCEなら全体GUIDANCE」

**深刻度**: Minor（仕様確認事項）

**元の問題**: 集計ロジックが「1つでもGUIDANCEなら全体GUIDANCE」になっている懸念。

**確認結果**: **現在の実装は異なるロジック（仕様通りと思われる）**

#### 現在の集計ロジック（api/main.py:164-187）

```
1. Gemini document-level decision がある → それを採用（最優先）
2. classificationsが空 → "UNKNOWN"
3. ルールベースフォールバック:
   a. capital_count > 0 AND expense_count > 0 → "GUIDANCE"
   b. capital_count >= total/2 → "CAPITAL_LIKE"
   c. expense_count >= total/2 → "EXPENSE_LIKE"
   d. capital_count > expense_count → "CAPITAL_LIKE"
   e. expense_count > capital_count → "EXPENSE_LIKE"
   f. else → "GUIDANCE"
```

**分析**:
- 「1つでもGUIDANCEなら全体GUIDANCE」ではない
- 実際は「CAPITAL_LIKEとEXPENSE_LIKEが**両方存在**する場合にGUIDANCE」
- これは「Stop設計」（迷うなら人に聞け）の思想に合致しており、合理的
- ただし、GUIDANCE判定されたline_itemの数は集計に影響しない（capitalとexpenseのカウントのみ使用）

**注意点**:
- ステップ3aにより、capital×1 + expense×9 でも GUIDANCE になる（少数派が混在するだけで専門家判断を促す）
- これは「安全寄り設計」として意図通りと解釈できるが、仕様書に明記されていない
- 仕様書に集計ロジックの判定基準を明文化することを推奨

---

## 他箇所への波及確認

### デフォルト値パターンの横展開確認

| ファイル | 箇所 | パターン | リスク |
|----------|------|----------|--------|
| `core/classifier.py` | `_calculate_confidence()` 全体 | 明示的な値を返す（0.40〜0.95） | **安全** |
| `core/classifier.py:272` | `item.update({"confidence": confidence})` | classifierが必ず設定 | **安全** |
| `core/adapter.py` | `adapt_opal_to_v1()` | confidence関連のデフォルト値なし | **安全** |
| `core/policy.py` | `load_policy()` | ポリシーの安全なデフォルト | **安全** |
| `core/schema.py` | 定数定義のみ | N/A | **安全** |
| `core/pipeline.py` | `run_pdf_pipeline()` | confidence操作なし | **安全** |
| `ui/app.py` | Streamlit UI | classifierの出力をそのまま表示 | **安全**（表示のみ） |
| `api/main.py:42` | Gemini fallback | `confidence: 0.0` | **安全**（明示的に0） |
| `api/main.py:212,268,274` | response formatting | `get("confidence", 0.8)` | **要修正**（前述） |

### 集計ロジックの横展開確認

- 集計ロジックは `api/main.py:164-187` の1箇所のみ
- `ui/app.py` には独自の集計ロジックはない（APIの結果を表示するのみ）
- `core/` には document-level の集計ロジックはない（line_item単位のみ）
- **横展開の問題なし**

---

## 教訓の横展開確認

### 教訓1: 「デフォルト値で重要な値を上書きしない」

| 確認結果 | 詳細 |
|----------|------|
| core/ | **教訓が適用済み** — classifierは明示的にconfidenceを計算・設定している |
| api/main.py | **教訓が未完全適用** — 3箇所でデフォルト0.8が残存。classifierが正常動作する限り顕在化しないが、防御的コーディングとしては不十分 |
| ui/app.py | **問題なし** — UIは受け取った値をそのまま表示 |

### 教訓2: 「集計ロジックの仕様を明確にする」

| 確認結果 | 詳細 |
|----------|------|
| コード上 | 集計ロジックは合理的に実装されている |
| ドキュメント | 集計ロジックの判定基準が仕様書として明文化されていない（コード内コメントのみ） |
| 推奨 | `docs/` 配下に集計ロジックの仕様を記載し、「なぜこの判定基準か」を残すべき |

---

## 指摘事項まとめ

| # | 深刻度 | 対象 | 概要 | 修正提案 |
|---|--------|------|------|----------|
| 1 | Major | api/main.py:212,268,274 | デフォルトconfidence 0.8が3箇所残存。classifier障害時に不正な高確信度を返すリスク | デフォルト値を0.0またはNoneに変更 |
| 2 | Minor | api/main.py:164-187 | 集計ロジックの判定基準が仕様書に明文化されていない | docs/に集計ロジック仕様を追記 |
| 3 | Info | core/classifier.py | confidence計算は適切に実装済。教訓が正しく適用されている | 現状維持 |
