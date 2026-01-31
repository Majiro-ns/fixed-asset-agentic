# 提出前最終チェックリスト

> **Version**: 1.0.0
> **作成日**: 2026-01-30
> **対象**: 第4回 Agentic AI Hackathon with Google Cloud

---

## 1. 提出要件サマリ

| 要件 | 状態 | 備考 |
|------|------|------|
| 公開GitHubリポジトリURL | ⚠️ 要確認 | URLは設定済み、公開状態の確認必要 |
| デプロイURL（動作確認可能） | ⚠️ 要確認 | URLあり、動作確認必要 |
| Zenn記事（カテゴリ:Idea、トピック:gch4） | ❓ 未確認 | コードベース外、別途確認必要 |
| デモ動画（3分） | ❓ 未確認 | Zenn記事内に含める |

---

## 2. 詳細チェック項目

### 2.1 GitHubリポジトリ

| チェック項目 | 状態 | 詳細 |
|--------------|------|------|
| リポジトリURL設定 | ✅ 完了 | `https://github.com/Majiro-ns/fixed-asset-agentic` |
| リポジトリ公開設定 | ⚠️ 要確認 | GitHub上で Public に設定されているか確認 |
| .gitignore設定 | ✅ 完了 | 機密ファイル除外設定あり |

**確認コマンド（手動）:**
```bash
# ブラウザで確認
https://github.com/Majiro-ns/fixed-asset-agentic
# → 「Public」バッジが表示されていればOK
```

### 2.2 デプロイURL

| チェック項目 | 状態 | 詳細 |
|--------------|------|------|
| Cloud Run URL | ✅ 設定済 | `https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app` |
| /health エンドポイント | ⚠️ 要確認 | `{"ok":true}` が返ること |
| /classify エンドポイント | ⚠️ 要確認 | 分類結果が返ること |

**確認コマンド:**
```powershell
# ヘルスチェック
curl.exe -s https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app/health

# 分類API
$body = '{"opal_json":{"invoice_date":"2024-01-01","vendor":"ACME","line_items":[{"item_description":"server install","amount":5000,"quantity":1}]}}'
Invoke-RestMethod -Uri "https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app/classify" -Method Post -Body $body -ContentType "application/json"
```

### 2.3 Zenn記事

| チェック項目 | 状態 | 詳細 |
|--------------|------|------|
| 記事作成 | ❓ 未確認 | Zenn上で確認必要 |
| カテゴリ: Idea | ❓ 未確認 | 記事設定で確認 |
| トピック: gch4 | ❓ 未確認 | 記事設定で確認 |
| デモ動画（3分）埋め込み | ❓ 未確認 | YouTube/Vimeo等の埋め込み |

**Zenn記事に含めるべき内容:**
- プロジェクト概要
- Stop-first設計の説明
- システム構成図
- デモ動画（3分）
- GitHubリポジトリリンク
- デプロイURLリンク

### 2.4 README.md 審査員向け整備

| チェック項目 | 状態 | 詳細 |
|--------------|------|------|
| 審査員向け3点セット記載 | ✅ 完了 | Agentic/Google Cloud AI/Repro の記載あり |
| システム構成図（Mermaid） | ✅ 完了 | README.md内に図あり |
| デモ手順リンク | ✅ 完了 | DEMO_RUNBOOK.md へのリンクあり |
| API仕様記載 | ✅ 完了 | /health, /classify, /classify_pdf の説明あり |
| 日本語主体 | ✅ 完了 | 日本語で記載 |

### 2.5 機密情報除去

| チェック項目 | 状態 | 詳細 |
|--------------|------|------|
| .env ファイル除外 | ✅ 完了 | .gitignoreに設定済み |
| APIキー・シークレット | ✅ 完了 | コードに直接記載なし |
| 個人情報 | ✅ 完了 | デモデータは全て架空 |
| 脳みそ.txt 除外 | ✅ 完了 | .gitignoreに設定済み |
| .gcloud_config | ⚠️ 要確認 | 認証情報が含まれていないか確認 |

**確認コマンド:**
```bash
# 機密ファイルがコミットされていないか確認
git ls-files | grep -E '\.env|secret|credential|key\.json'
```

### 2.6 ライセンス

| チェック項目 | 状態 | 詳細 |
|--------------|------|------|
| LICENSEファイル | ❌ 未作成 | ルートにLICENSEファイルが存在しない |
| OSS/Licenses記載 | ✅ 完了 | README.mdに依存ライブラリのライセンス明記 |
| PyMuPDF (AGPL-3.0) 注意 | ✅ 記載済 | 商用利用時の注意が記載されている |

**要対応:**
LICENSEファイルを作成する（例: MIT, Apache 2.0 等）

---

## 3. 未完了タスクリスト

### 3.1 必須（提出前に完了必要）

| 優先度 | タスク | 担当 | 状態 |
|--------|--------|------|------|
| 🔴 高 | GitHubリポジトリの公開設定確認 | 殿 | 未確認 |
| 🔴 高 | Cloud Run デプロイURL動作確認 | 殿 | 未確認 |
| 🔴 高 | Zenn記事作成・公開 | 殿 | 未確認 |
| 🔴 高 | デモ動画撮影・Zenn記事埋め込み | 殿 | 未確認 |
| 🟡 中 | LICENSEファイル作成 | 足軽/殿 | 未完了 |
| 🟡 中 | .gcloud_config の機密情報確認 | 殿 | 未確認 |

### 3.2 推奨（時間があれば）

| 優先度 | タスク | 担当 | 状態 |
|--------|--------|------|------|
| 🟢 低 | README.md の最終見直し | 足軽 | 可能 |
| 🟢 低 | Golden Set追加（10→20ケース） | 足軽 | 可能 |

---

## 4. 優先度順の残作業リスト

### 最優先（提出ブロッカー）

1. **Zenn記事の作成・公開**
   - カテゴリ: Idea
   - トピック: gch4
   - デモ動画（3分）を含める
   - GitHubリポジトリURLを記載
   - デプロイURLを記載

2. **GitHubリポジトリの公開確認**
   - https://github.com/Majiro-ns/fixed-asset-agentic
   - Settings → Danger Zone → Change visibility → Public

3. **Cloud Run動作確認**
   - /health → `{"ok":true}`
   - /classify → 分類結果が返る

### 次点（品質向上）

4. **LICENSEファイル作成**
   ```
   推奨: MIT License または Apache 2.0
   理由: PyMuPDF (AGPL-3.0) との互換性を考慮
   ```

5. **.gcloud_config の確認**
   - 認証情報（サービスアカウントキー等）が含まれていないか確認
   - 必要に応じて.gitignoreに追加

---

## 5. 成果物一覧

### コードベース内ドキュメント

| ファイル | 目的 | 状態 |
|----------|------|------|
| README.md | 審査員向け概要 | ✅ |
| INDEX.md | 開発ルール | ✅ |
| DEMO.md | デモスクリプト | ✅ |
| docs/DEMO_RUNBOOK.md | デモ手順詳細 | ✅ |
| docs/COMPLIANCE_CHECKLIST.md | 規約準拠確認 | ✅ |
| docs/future_vision.md | 将来ビジョン | ✅ |
| docs/technical_explanation.md | 技術解説 | ✅ |
| docs/use_cases.md | ユースケース | ✅ |
| docs/judge_value_proposition.md | 審査員向け価値提案 | ✅ |
| docs/qa_and_risks.md | Q&A・リスク | ✅ |
| docs/demo_script.md | デモ台本 | ✅ |
| docs/ui_improvements.md | UI改善 | ✅ |
| docs/winning_patterns_analysis.md | 勝ちパターン分析 | ✅ |

### 外部提出物

| 項目 | URL/場所 | 状態 |
|------|----------|------|
| GitHubリポジトリ | https://github.com/Majiro-ns/fixed-asset-agentic | ⚠️ 公開確認必要 |
| Cloud Run API | https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app | ⚠️ 動作確認必要 |
| Zenn記事 | 未作成 | ❓ |
| デモ動画 | 未撮影 | ❓ |

---

## 6. 最終確認チェックリスト（提出直前）

```
□ GitHubリポジトリが Public である
□ Cloud Run /health が {"ok":true} を返す
□ Cloud Run /classify が分類結果を返す
□ Zenn記事が公開されている
□ Zenn記事にデモ動画（3分）が埋め込まれている
□ Zenn記事のカテゴリが「Idea」である
□ Zenn記事のトピックに「gch4」が含まれている
□ Zenn記事にGitHubリポジトリURLが記載されている
□ Zenn記事にデプロイURLが記載されている
□ LICENSEファイルが存在する（推奨）
□ 機密情報がコミットされていない
```

---

## 付録: 参考リンク

- [ハッカソン参加規約](https://zenn.dev/topics/gch4) ※公式トピック
- [docs/COMPLIANCE_CHECKLIST.md](./COMPLIANCE_CHECKLIST.md) - 規約準拠詳細
- [docs/DEMO_RUNBOOK.md](./DEMO_RUNBOOK.md) - デモ手順
- [DEMO.md](../DEMO.md) - デモスクリプト

---

*本チェックリストは提出前の最終確認用です。全ての「⚠️ 要確認」「❓ 未確認」「❌ 未完了」項目を解消してから提出してください。*
