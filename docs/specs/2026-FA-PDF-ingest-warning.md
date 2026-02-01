0. 基本情報（必須）

Task ID: 2026-FA-PDF-ingest-warning

作成日: 2026-01-07

担当: 事務（固定資産）

関連Issue: #123（GitHub Issue番号）

優先度: High

1. 背景（Why：業務の困りごと）

固定資産の判定に使用するPDF（請求書・見積書）の中に、
スキャンされたPDFが含まれることがある。

その場合、

文字情報が少ない

なぜ判定できないのか分からない

後から説明しにくい

という問題が発生している。

2. 目的（Goal）

PDFを読み取った結果について、

判定できた／できない理由が分かる

スキャンPDFの場合は注意が明示される

後から第三者に説明できる情報が残る

状態にする。

3. 対象範囲（Scope）
対象とするもの

PDF入力（請求書・見積書・契約書）

PDFからのテキスト抽出処理

注意表示（warnings）の出力

UI / CLI / JSON 出力

対象外（Non-goals）

税務上の固定資産判定ルールの変更

耐用年数・勘定科目の定義変更

OCR精度そのものの改善（有効/無効の説明は対象）

4. 入力（Inputs）

PDFファイル

テキストPDF

スキャンPDF（画像ベース）

環境変数

USE_LOCAL_OCR=true / false

USE_DOCAI=true / false

OCR_TEXT_THRESHOLD（既存値）

5. 出力（Outputs）

以下のファイルが必ず生成されること。

data/results/<name>_extract.json

data/results/<name>_final.json

6. 出力要件（最重要）
6.1 warnings（必須）

meta.warnings が 必ず存在する（空配列でも可）

warnings は以下の構造を持つ

{
  "code": "TEXT_TOO_SHORT",
  "message": "Text extraction is too short; scanned PDF suspected.",
  "page": 1
}

想定コード例

TEXT_TOO_SHORT

OCR_DISABLED

OCR_NOT_INSTALLED

DOCAI_DISABLED

6.2 evidence（必須）

判定の根拠として evidence を保持する

evidence は以下を必ず含む

項目	内容
page	ページ番号
method	抽出方法（text / ocr / docai 等）
snippet	実際に使われた文字列
7. 業務的な完了条件（Acceptance Criteria）

以下 **すべてを満たした場合のみ「完了」**とする。

 PDFを読み込むと必ず結果が返る

 スキャンPDFの場合、warnings が表示される

 warnings は UI / CLI / JSON すべてで確認できる

 evidence が final.json に残っている

 OCR無効時は、その理由が warnings に記載される

 pytest がすべて通る（CI green）

8. 業務上の注意点（Danger / Approval）

税務判断・固定資産区分の定義は 変更しない

判断ロジックの意味変更が必要な場合は 実装せず提案止まり

silent fail（何も出さずに処理継続）は禁止

9. 想定されるリスクと対策
リスク	対策
スキャンPDFで誤解される	warnings を必ず表示
OCR未導入で問い合わせ増	OCR_DISABLED を明示
後から説明できない	evidence を必須化
10. レビュー時の確認ポイント（人が見る）

依頼内容とズレていないか

warnings / evidence が消えていないか

税務判断に触れていないか

テストが追加・更新されているか

11. 補足（任意）

今回は「説明性の改善」が目的

精度向上は次タスクで対応予定