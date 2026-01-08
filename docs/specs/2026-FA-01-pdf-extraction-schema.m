# SPEC: PDF Extraction Schema for Fixed Assets (Step 1)

## 目的（Purpose）
固定資産に関する請求書・見積書PDFから、後続の判定（資産/費用、勘定科目、耐用年数候補）に必要な情報を、
**毎回同じ構造（スキーマ）で安定的に取得**できる状態を作る。

本SPECでは「正しく判断する」ことは目的とせず、  
**判断に必要な材料を漏れなく・説明可能な形で並べること**を目的とする。

---

## スコープ（In Scope）
- PDF（テキストPDF / スキャンPDF）の読み込み
- テキスト抽出結果をもとにした **項目候補の抽出**
- 抽出結果を **標準スキーマ（JSON）** に格納
- 抽出不能・不確実な場合の **warnings / reasons の明示**

---

## スコープ外（Out of Scope）
- 資産/費用の最終判定
- 勘定科目の確定
- 耐用年数の確定
- 税務・会計上の判断ロジックの変更

---

## 前提条件・制約
- OCR / DocAI は **有効・無効どちらでも動作**すること
- OCR 未実行の場合でも、**注意喚起（warnings）は必ず出力**する
- 抽出結果には必ず **evidence（根拠テキスト）** を紐づける
- 抽出できない項目は空欄にせず、`unknown` と理由を残す

---

## 標準出力スキーマ（Extraction Schema）

### extraction.meta
```json
{
  "source_type": "pdf",
  "file_name": "string",
  "extracted_at": "ISO-8601 datetime",
  "text_length": 1234,
  "ocr_used": true,
  "docai_used": false
}
extraction.warnings
json
コードをコピーする
[
  {
    "code": "TEXT_TOO_SHORT",
    "message": "Extracted text is unusually short; scanned PDF suspected.",
    "severity": "warning",
    "related_fields": ["all"]
  }
]
extraction.fields（項目候補）
json
コードをコピーする
{
  "transaction_date": {
    "value": "2026-04-01 | unknown",
    "confidence": 0.7,
    "evidence_refs": ["ev-001"]
  },
  "counterparty": {
    "value": "株式会社サンプル | unknown",
    "confidence": 0.8,
    "evidence_refs": ["ev-002"]
  },
  "item_description": {
    "value": "業務用プリンター | unknown",
    "confidence": 0.6,
    "evidence_refs": ["ev-003"]
  },
  "quantity": {
    "value": 1,
    "confidence": 0.9,
    "evidence_refs": ["ev-004"]
  },
  "unit_price": {
    "value": 500000,
    "confidence": 0.9,
    "evidence_refs": ["ev-004"]
  },
  "total_amount": {
    "value": 500000,
    "confidence": 0.9,
    "evidence_refs": ["ev-004"]
  },
  "tax_category": {
    "value": "課税 | 非課税 | 不明",
    "confidence": 0.5,
    "evidence_refs": ["ev-005"]
  }
}
evidence スキーマ（必須）
json
コードをコピーする
{
  "id": "ev-003",
  "page": 1,
  "method": "pdf_text | ocr | docai",
  "snippet": "業務用プリンター一式"
}
snippet は 人が読んで根拠として理解できる長さにする

1項目に複数 evidence が紐づいてもよい

実装要件（Implementation Requirements）
必須要件
すべての抽出結果は上記スキーマに従う

confidence は 推定値（0.0〜1.0） でよいが、必ず付与する

unknown の場合も value: "unknown" + confidence: 0.0 を返す

warnings が1つ以上ある場合でも、処理は中断しない

禁止事項
抽出できない項目を黙って省略すること

evidence を伴わない value の出力

税務・会計的な解釈をここで行うこと

受け入れ条件（Acceptance Criteria）
テキストPDF / スキャンPDF の両方で extraction JSON が生成される

スキャンPDFで文字数が極端に少ない場合、warnings が出力される

final.json に extraction スキーマが保存される

後続タスク（ルール判定・AI案）が このスキーマ前提で実装可能であること

次工程への引き渡し
本SPECの出力を入力として、

Step 2：ルールベース一次判定

Step 3：勘定科目候補提示
を実装する

備考
本SPECは「判断の自動化」ではなく「判断材料の整備」を目的とする

人がレビューしやすい構造であることを最優先とする
