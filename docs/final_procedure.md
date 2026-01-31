# 殿のための最終確認手順書

> **Version**: 1.0.0
> **作成日**: 2026-01-30
> **作成者**: 将軍

---

## 概要

本手順書は、殿が提出前に成果物を確認するための手順をまとめたものである。
コードロジックの矛盾確認、成果物の品質確認、提出準備の最終チェックを行う。

---

## 1. 成果物の格納場所

```
C:\Users\owner\Desktop\fixed-asset-ashigaru\
├── README.md              # 審査員向けメイン文書
├── DEMO.md                # デモ台本（統合版）
├── INDEX.md               # 開発ルール
├── docs/
│   ├── judge_value_proposition.md   # 審査員向け価値定義
│   ├── use_cases.md                 # 実務ユースケース
│   ├── technical_explanation.md     # 技術説明（Zenn記事向け）
│   ├── demo_script.md               # → DEMO.mdへ統合済み
│   ├── qa_and_risks.md              # 想定QA・リスク
│   ├── future_vision.md             # 将来ビジョン
│   ├── winning_patterns_analysis.md # 勝ちパターン分析
│   ├── ui_improvements.md           # UI改善提案
│   ├── github_checklist.md          # GitHubリポジトリ確認
│   ├── deploy_status.md             # Cloud Runデプロイ状況
│   ├── zenn_article_draft.md        # Zenn記事ドラフト
│   ├── architecture_diagram.md      # システム構成図
│   ├── time_savings_calculation.md  # 業務時間削減試算
│   └── submission_checklist.md      # 提出前チェックリスト
└── ui/
    └── (UI改善済みコード)
```

---

## 2. 殿が確認すべき項目

### 2.1 コードロジックの矛盾確認

以下のファイルを確認し、ロジックの一貫性を検証：

| ファイル | 確認ポイント |
|----------|-------------|
| `core/classifier.py` | 3値判定（CAPITAL_LIKE/EXPENSE_LIKE/GUIDANCE）のロジック |
| `core/normalizer.py` | 正規化ルールの一貫性 |
| `api/main.py` | APIエンドポイントの動作 |
| `policies/*.json` | ポリシー設定の整合性 |

**確認コマンド:**
```powershell
# テスト実行
cd C:\Users\owner\Desktop\fixed-asset-ashigaru
pytest tests/ -v
```

### 2.2 成果物の品質確認

| 成果物 | 確認ポイント |
|--------|-------------|
| README.md | 審査員向け3点セットが記載されているか |
| DEMO.md | 3分以内で実行可能なシナリオか |
| docs/zenn_article_draft.md | Zenn記事として公開可能な品質か |
| docs/technical_explanation.md | 技術的に正確か |

### 2.3 動作確認

**Cloud Run:**
```powershell
# ヘルスチェック
Invoke-RestMethod -Uri "https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app/health"

# 分類API
$body = '{"opal_json":{"invoice_date":"2024-01-01","vendor":"ACME","line_items":[{"item_description":"server install","amount":5000,"quantity":1}]}}'
Invoke-RestMethod -Uri "https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app/classify" -Method Post -Body $body -ContentType "application/json"
```

**ローカルUI:**
```powershell
cd C:\Users\owner\Desktop\fixed-asset-ashigaru
streamlit run ui/app_minimal.py
```

---

## 3. 提出前チェックリスト

### 3.1 必須（提出ブロッカー）

```
□ GitHubリポジトリが Public である
  URL: https://github.com/Majiro-ns/fixed-asset-agentic

□ Cloud Run が正常動作している
  URL: https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app

□ Zenn記事が公開されている
  - カテゴリ: Idea
  - トピック: gch4
  - デモ動画（3分）埋め込み

□ デモ動画が撮影・アップロードされている
  - YouTube公開
  - 3分以内
```

### 3.2 推奨

```
□ LICENSEファイルが存在する
□ 機密情報がコミットされていない
□ Golden Setテストがパスする
```

---

## 4. 最終提出物

| 項目 | 状態 | 備考 |
|------|------|------|
| GitHubリポジトリURL | ⚠️ 要確認 | 公開設定確認 |
| デプロイURL | ✅ 確認済 | 動作確認済み |
| Zenn記事URL | ❓ 未作成 | docs/zenn_article_draft.md を基に作成 |
| デモ動画 | ❓ 未撮影 | DEMO.md の台本を使用 |

---

## 5. 殿への報告事項

### 5.1 完了タスク

- [x] 審査員向け価値定義
- [x] 実務ユースケース設計
- [x] 判定ロジック説明
- [x] デモ台本
- [x] UI改善
- [x] 想定QA・リスク
- [x] README整形
- [x] 将来ビジョン
- [x] 勝ちパターン分析
- [x] GitHubリポジトリ確認
- [x] Cloud Runデプロイ状況確認
- [x] Zenn記事ドラフト作成
- [x] システム構成図作成
- [x] 業務時間削減数値化
- [x] 提出前チェックリスト作成
- [x] 重複コンテンツ整理

### 5.2 殿の対応が必要な項目

1. **GitHubリポジトリの公開確認**
   - Settings → Danger Zone → Change visibility → Public

2. **Zenn記事の作成・公開**
   - `docs/zenn_article_draft.md` を基に作成
   - カテゴリ: Idea、トピック: gch4

3. **デモ動画の撮影**
   - `DEMO.md` の台本に従って撮影
   - 3分以内
   - YouTube公開

4. **成果物の最終確認**
   - 本手順書に従って確認

### 5.3 スキル化候補（承認待ち）

| スキル名 | 用途 |
|----------|------|
| faq-risk-generator | FAQ・リスク対策文書の自動生成 |
| readme-formatter | README整形 |
| tech-doc-generator | 技術ドキュメント生成 |
| mojibake-fixer | 文字化け修正 |

---

## 6. 緊急連絡先

問題発生時は将軍に報告せよ。

---

*本手順書は将軍が作成した最終確認用文書である。*
