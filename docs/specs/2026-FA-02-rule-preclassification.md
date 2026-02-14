# SPEC: Rule-based Preclassification for Fixed Assets (Step 2)

## 目的（Purpose）
Step 1 で抽出された PDF の構造化データ（Extraction Schema）を入力として、
**税務・会計判断を行わずに**、後続判断のための「整理された一次判定結果」を生成する。

本ステップでは以下を目的とする：
- 人が考える前に、論点を減らす
- 判断材料を「分類・整理」する
- AI判定・人判定に渡す **下地データ** を作る

---

## 前提（Input）
- 入力は Step 1 の Extraction Schema に完全準拠していること
- extraction.warnings が存在していても処理は継続する
- extraction.fields の value が unknown の場合も前提として扱う

---

## スコープ（In Scope）
- ルールベースによる一次分類
- 資産候補 / 費用候補 / 判断保留 の切り分け
- 勘定科目「候補群」の提示（確定しない）
- 判定理由（rules / evidence）の明示

---

## スコープ外（Out of Scope）
- 勘定科目の最終確定
- 耐用年数の確定
- 税法解釈の変更
- AIによる自然言語判断

---

## 出力スキーマ（Preclassification Result）

### preclassification.meta
```json
{
  "version": "1.0",
  "generated_at": "ISO-8601 datetime",
  "based_on_spec": "2026-FA-01-pdf-extraction-schema"
}
preclassification.summary
json
コードをコピーする
{
  "asset_likelihood": "high | medium | low | unknown",
  "expense_likelihood": "high | medium | low | unknown",
  "confidence_note": "string"
}
※ 両方が high / medium になってもよい（排他的にしない）

preclassification.rules_applied
json
コードをコピーする
[
  {
    "rule_id": "R-AMOUNT-001",
    "description": "Total amount exceeds capitalization threshold",
    "result": "matched | not_matched | unknown",
    "related_fields": ["total_amount"],
    "evidence_refs": ["ev-004"]
  }
]
preclassification.asset_indicators
json
コードをコピーする
{
  "amount_indicator": {
    "value": "high | low | unknown",
    "reason": "500,000 yen exceeds internal threshold",
    "evidence_refs": ["ev-004"]
  },
  "quantity_indicator": {
    "value": "single | multiple | unknown",
    "reason": "Quantity is 1",
    "evidence_refs": ["ev-004"]
  },
  "description_indicator": {
    "value": "equipment_like | consumable_like | unknown",
    "reason": "Contains keyword 'プリンター'",
    "evidence_refs": ["ev-003"]
  }
}
preclassification.account_candidates
json
コードをコピーする
[
  {
    "account_code": "工具器具備品",
    "confidence": 0.6,
    "reason": "Equipment-like description and high amount",
    "rules": ["R-DESC-002", "R-AMOUNT-001"]
  },
  {
    "account_code": "消耗品費",
    "confidence": 0.3,
    "reason": "Possible consumable wording detected",
    "rules": ["R-DESC-005"]
  }
]
※ 並列で複数候補を出す（1つに絞らない）

preclassification.warnings
json
コードをコピーする
[
  {
    "code": "LOW_TEXT_CONFIDENCE",
    "message": "Extraction confidence is low; classification reliability reduced",
    "severity": "warning",
    "related_fields": ["item_description"]
  }
]
ルール設計方針（Rule Design Policy）
基本方針
すべて if-then 型の単純ルール

スコアリング・機械学習は禁止

1ルール＝1理由 が説明できること

代表的ルール例（非網羅）
Rule ID	内容
R-AMOUNT-001	金額が社内資産計上基準以上
R-AMOUNT-002	金額が少額である
R-DESC-002	設備系キーワードを含む（更新・新設・設置・増設・購入・導入・構築・整備・改修）
R-DESC-005	消耗品系キーワードを含む（保守・点検・修理・修繕・調整・清掃・清拭・消耗品・雑費・メンテナンス・維持・管理・交換・補修・年間・定期・契約）
R-DESC-006	除外費用キーワードを含む（撤去・廃棄・処分・解体・除却・原状回復・養生・仮設）
R-DESC-007	取得価額算入キーワードを含む（運搬・運賃・搬入・配送・据付・荷造）
R-DESC-008	按分対象キーワードを含む（諸経費・一般管理費・現場管理費・共通仮設）
R-DESC-009	混在キーワードを含む（一式・移設・既設）
R-QTY-001	数量が1である
R-QTY-002	数量が複数

### キーワード分類の優先順位
1. **除外費用キーワード** (R-DESC-006): 取得価額に含めない → EXPENSE_LIKE
2. **取得価額算入キーワード** (R-DESC-007): 取得価額に算入 → CAPITAL_LIKE
3. **按分対象キーワード** (R-DESC-008): 資産/費用比率で按分（端数は経費側）
4. **混在キーワード** (R-DESC-009): 判断保留 → GUIDANCE
5. **競合検出**: 資産・費用キーワードが混在 → GUIDANCE

### GUIDANCE項目への ai_hint 付与
GUIDANCEに分類された明細には、参考情報として `ai_hint` を付与できる。
判定自体はGUIDANCEを維持し、最終判断を人間に委ねる設計は変わらない。

- **Phase 1**: Gemini APIによる推定（8秒タイムアウト）
- **Phase 2（フォールバック）**: キーワードヒューリスティック（例: 「撤去」→ EXPENSE_LIKE）

```json
{
  "ai_hint": {
    "suggestion": "EXPENSE_LIKE",
    "suggestion_label": "費用寄り",
    "confidence": 0.6,
    "reasoning": "「撤去」を含むため費用の可能性"
  }
}
```

`ai_hint` は判断の下準備に徹するという本SPECの基本方針に沿い、あくまで参考情報として提示する。

実装要件（Implementation Requirements）
必須
すべての判定結果に reason を付与

reason は「人が読んで理解できる文章」であること

extraction.evidence を必ず引き継ぐ

unknown の場合は unknown と明示する

禁止
勘定科目を1つに決め打ちする

税法・通達ベースの判断を書く

AI的な推測表現（〜と思われる等）

## 税額閾値ルールとキーワード判定の関係

### 税額閾値（10万/20万/30万/60万円）
- **キーワードで明確に判定できる場合**: 税額閾値は参考情報としてフラグに記録するのみ（判定を上書きしない）
- **キーワードで判定できない場合**: 税額閾値に基づきGUIDANCE（要確認）に設定

### 例: 撤去費 15万円
- キーワード「撤去」→ EXPENSE_LIKE
- 税額閾値「10万円以上20万円未満」→ フラグに記録するが、EXPENSE_LIKEを維持
- これにより、明確な経費が金額閾値で誤って資産扱いされることを防ぐ

### 例: 不明な工事 25万円
- キーワードなし → 判定不可
- 税額閾値「20万円以上30万円未満」→ GUIDANCE（中小企業特例等の確認が必要）

受け入れ条件（Acceptance Criteria）
Step 1 の出力JSONを入力として処理できる

extraction.warnings があっても結果が出る

asset / expense の両方向候補が並立可能

人が「なぜこの候補が出たか」を説明できる

次工程への引き渡し
本SPECの出力を入力として

Step 3：AIによる勘定科目案提示

Step 4：耐用年数候補提示
を実装可能であること

備考
本ステップは 人の判断を置き換えない

判断の「下準備」に徹する

説明責任を最優先する
