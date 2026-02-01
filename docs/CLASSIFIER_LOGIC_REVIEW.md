# 判定ロジック精査報告（会計税務専門家レビュー）

> 作成日: 2026-02-01
> 目的: classifier.py の判定ロジックの隙を洗い出し、改善点を特定する

---

## 現行ロジックの構造

```
1. キーワードマッチング
   → CAPITAL_KEYWORDS / EXPENSE_KEYWORDS / MIXED_KEYWORDS

2. 金額による税ルール適用
   → 10万/20万/30万/60万 の閾値

3. ポリシーによる上書き
   → guidance_add, always_guidance, thresholds
```

---

## 現行コードの金額閾値ロジック

```python
if amount < 100_000:      # 10万円未満 → suggests_guidance: False
elif amount < 200_000:    # 10万〜20万 → suggests_guidance: True
elif amount < 300_000:    # 20万〜30万 → suggests_guidance: True
elif amount < 600_000:    # 30万〜60万 → suggests_guidance: False  ★問題
else:                     # 60万以上 → suggests_guidance: True
```

---

## 問題点1: 金額閾値ロジックの根拠が混在している

**問題**: 30万〜60万円で `suggests_guidance: False` となっているが、これは**少額減価償却資産の判定**と**資本的支出vs修繕費の判定**を混同している。

**国税庁基準との対比**:

| 金額 | 少額資産判定 | 修繕費vs資本的支出 |
|------|-------------|-------------------|
| 10万円未満 | 即時損金可 | 関係なし |
| 10万〜20万円 | 一括償却可 | 関係なし |
| 20万〜30万円 | 中小特例で即時可 | 関係なし |
| 20万円未満 | - | 修繕費OK |
| 60万円未満 | - | 修繕費OK（簡易判定） |
| 60万円以上 | - | **要判定** |

**指摘**: 現行ロジックは「少額減価償却資産」と「修繕費vs資本的支出」という**別次元の判定**を1つの閾値で処理しようとしている。

---

## 問題点2: MIXED_KEYWORDSに「更新」が含まれているが、CAPITAL_KEYWORDSにも「更新」がある

```python
CAPITAL_KEYWORDS = ["更新", "新設", ...]  # 更新あり
MIXED_KEYWORDS = ["一式", "撤去", "移設", "既設", "更新"]  # 更新あり
```

ロジック上、MIXED_KEYWORDSが先にチェックされるため、「更新」は常にGUIDANCEになる。これは意図的かもしれないが、「サーバー更新」のような明確な資産計上案件も止まってしまう。

---

## 問題点3: company_default.jsonのguidance_addが過剰

```json
"guidance_add": ["撤去", "廃棄", "移設", "既設", "更新", "一式", "設置", "配線"]
```

「設置」がguidance_addに含まれているが、これはCAPITAL_KEYWORDSにも含まれる。結果として「設置」は常にGUIDANCEになる。

**新設工事の設置**は明確に資産計上すべきケースが多いため、これは過剰な「止まる」設計。

---

## 問題点4: 個別明細の金額で判定しているが、合計金額を考慮していない

見積書全体で110万円でも、個別明細が30万〜60万円の範囲なら`suggests_guidance: False`になる。

しかし国税庁基準では:
> 「一つの修理、改良などの金額が60万円未満」

「一つの修理」とは**工事全体**を指すことが多い。個別明細ではなく、見積書合計で判定すべきケースがある。

---

## 問題点5: 「修繕費vs資本的支出」の本質的判定基準が欠けている

国税庁の判定基準:
1. **価値増加・耐久性向上** → 資本的支出
2. **原状回復・維持管理** → 修繕費

現行ロジックはキーワードで代用しているが、以下が考慮されていない:
- 「原状回復」目的かどうか
- 「耐用年数延長」につながるか
- 「用途変更」を伴うか

---

## 修正提案

### 提案1: 金額閾値ロジックの整理

```python
def _apply_tax_rules(amount, total_amount=None):
    # 見積書合計金額がある場合はそちらを優先
    target_amount = total_amount if total_amount else amount

    if target_amount < 200_000:
        # 20万円未満: 修繕費として処理可能（簡易判定）
        return [{"suggests_guidance": False, ...}]
    elif target_amount < 600_000:
        # 60万円未満: 修繕費として処理可能だが確認推奨
        return [{"suggests_guidance": False, ...}]  # ただしフラグは付ける
    else:
        # 60万円以上: 要判定
        return [{"suggests_guidance": True, ...}]
```

### 提案2: MIXED_KEYWORDSから「更新」を削除

「更新」は文脈次第で資産/修繕どちらにもなりうるが、「サーバー更新」「設備更新」は資産寄りのケースが多い。

### 提案3: company_default.jsonのguidance_addから「設置」を削除

新設工事の設置は資産計上が基本。

### 提案4: 見積書合計金額での判定オプション追加

個別明細ではなく、合計金額で税ルールを適用するオプション。

---

## 参考資料（国税庁）

- [No.5402 修繕費とならないものの判定｜国税庁](https://www.nta.go.jp/taxes/shiraberu/taxanswer/hojin/5402.htm)
- [No.5408 中小企業者等の少額減価償却資産の取得価額の損金算入の特例｜国税庁](https://www.nta.go.jp/taxes/shiraberu/taxanswer/hojin/5408.htm)
- [第8節 資本的支出と修繕費｜国税庁](https://www.nta.go.jp/law/tsutatsu/kihon/hojin/07/07_08.htm)

---

## 対応済み（2026-02-01）

- ✅ EXPENSE_KEYWORDSに「修繕」追加
- ✅ 確信度90%超の場合は免責表示を省略
- ✅ GUIDANCEの場合、金額基準（20万/60万）で判定を倒す表示に変更
- ✅ 免責コメントを小さい字で表示（借金CM方式）
- ✅ 耐用年数判定（useful_life_estimator）のAPI統合
- ✅ CAPITAL_LIKE判定時にUIで耐用年数を表示
- ✅ 確信度（confidence）を分類結果に基づいて動的計算

---

## 今後の課題（実運用に向けて）

### 設計変更が必要な項目

| 優先度 | 課題 | 内容 | 必要な対応 |
|--------|------|------|-----------|
| High | 少額減価償却 vs 修繕費判定の分離 | 現行は2つの異なる税制度を1つのロジックで処理 | 「新規取得」「既存資産への支出」を分離した判定フロー |
| High | 見積書合計金額での判定 | 個別明細ではなく工事全体で60万円判定すべきケース | total_amountを判定ロジックに反映 |
| Medium | 取得価額10%基準 | 60万円以上でも取得価額の10%以下なら修繕費 | 取得価額入力フィールド追加 |
| Medium | 7:3基準（継続適用） | 30%を修繕費、70%を資本的支出とする継続適用 | 会社ポリシー設定機能 |
| Low | 中小企業特例の適用要件 | 資本金1億円以下、従業員500人以下等のチェック | 会社情報入力機能 |
| Low | 周期的修繕の判定 | 3年以内の周期的修繕は修繕費 | 過去の修繕履歴参照 |

### キーワード調整（運用で対応可能）

| 項目 | 現状 | 推奨対応 |
|------|------|---------|
| 「更新」の重複 | CAPITAL + MIXED + guidance_add で3重止まり | MIXED/guidance_addから削除検討 |
| 「設置」の重複 | CAPITAL + guidance_add で2重止まり | guidance_addから削除検討 |
| 「一式」の厳格さ | 明確な資産案件も止まる | 他キーワードとの組み合わせ判定に変更 |

---

## 参考資料（国税庁）

- [No.5402 修繕費とならないものの判定｜国税庁](https://www.nta.go.jp/taxes/shiraberu/taxanswer/hojin/5402.htm)
- [No.5408 中小企業者等の少額減価償却資産の取得価額の損金算入の特例｜国税庁](https://www.nta.go.jp/taxes/shiraberu/taxanswer/hojin/5408.htm)
- [第8節 資本的支出と修繕費｜国税庁](https://www.nta.go.jp/law/tsutatsu/kihon/hojin/07/07_08.htm)
