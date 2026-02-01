# 提出前最終チェックリスト

> **Version**: 2.0.0
> **更新日**: 2026-02-01
> **対象**: 第4回 Agentic AI Hackathon with Google Cloud

---

## 自動検証の実行

**提出前に必ず実行せよ**:
```powershell
cd C:\Users\owner\Desktop\fixed-asset-ashigaru
python scripts/preflight_check.py
```

このスクリプトは以下を自動検証する:
- 必須ファイルの存在（12項目）
- デモPDFの存在（4パターン）
- 機密情報の混入チェック
- Cloud Run API稼働確認
- コード品質（DEBUG print、TODO/FIXME）
- Golden Set確認

---

## 殿（人間）確認項目

以下は自動検証できない。殿が手動で確認する。

### 提出ブロッカー（必須）

| # | 項目 | 確認方法 | 状態 |
|---|------|----------|------|
| 1 | 参加登録完了 | https://lu.ma/agentic-ai-hackathon-4 で登録済みか確認 | □ |
| 2 | GitHubリポジトリが Public | https://github.com/Majiro-ns/fixed-asset-agentic にアクセスし「Public」バッジ確認 | □ |
| 3 | Zenn記事が公開済み | Zenn管理画面で published: true 確認 | □ |
| 4 | Zenn記事にトピック gch4 | 記事設定でトピックに「gch4」があるか確認 | □ |
| 5 | Zenn記事にデモ動画埋め込み | 記事内にYouTube/Vimeo埋め込みがあるか確認 | □ |
| 6 | デモ動画がアクセス可能 | 動画URLを別ブラウザ/シークレットで開いて確認 | □ |
| 7 | Cloud Runに最新コードがデプロイ | `gcloud run deploy` 実行済みか確認 | □ |

### 品質向上（推奨）

| # | 項目 | 確認方法 | 状態 |
|---|------|----------|------|
| 8 | PDF_CLASSIFY_ENABLED=1 が設定 | Cloud Run環境変数で確認 | □ |
| 9 | GEMINI_PDF_ENABLED=1 が設定（任意） | Cloud Run環境変数で確認 | □ |
| 10 | デモ動画が3分以内 | 動画の長さを確認 | □ |

---

## 提出物URL一覧

提出フォームに入力する情報:

| 項目 | URL |
|------|-----|
| GitHubリポジトリ | https://github.com/Majiro-ns/fixed-asset-agentic |
| Cloud Run API | https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app |
| Zenn記事 | （公開後に記入） |
| デモ動画 | （アップロード後に記入） |

---

## 提出手順

### 1. 自動検証実行
```powershell
python scripts/preflight_check.py
```
→ 全項目PASSを確認

### 2. 最終コミット＆プッシュ
```powershell
git add -A
git commit -m "chore: 提出前最終確認完了"
git push origin main
```

### 3. Cloud Run再デプロイ
```powershell
gcloud run deploy fixed-asset-agentic-api `
  --source . `
  --region asia-northeast1 `
  --allow-unauthenticated `
  --set-env-vars "PDF_CLASSIFY_ENABLED=1,GEMINI_PDF_ENABLED=1"
```

### 4. デプロイ確認
```powershell
curl https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app/health
```
→ `{"ok":true}` を確認

### 5. 殿確認項目をチェック
上記「殿（人間）確認項目」を全てチェック

### 6. 提出フォームで提出
Discord または公式サイトの提出フォームに必要情報を入力

---

## トラブルシューティング

### preflight_check.py が失敗する場合

| エラー | 対処法 |
|--------|--------|
| requests ライブラリがない | `pip install requests` |
| LICENSE がない | `echo "MIT License" > LICENSE` で作成 |
| デモPDFがない | `python scripts/create_demo_pdfs.py` |
| /health が失敗 | Cloud Runがデプロイされているか確認 |
| 機密情報検出 | 該当ファイルを.gitignoreに追加し削除 |

### Cloud Run デプロイが失敗する場合

```powershell
# ログ確認
gcloud run services logs read fixed-asset-agentic-api --region asia-northeast1 --limit 50
```

---

## 締切

| 項目 | 締切 |
|------|------|
| 参加登録 | **2/13** |
| プロジェクト提出 | **2/14-15** |

---

*このチェックリストに従えば、提出漏れを構造的に防げる。*
