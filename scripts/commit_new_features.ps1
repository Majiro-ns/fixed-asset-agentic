# 新機能コミット用PowerShellスクリプト
# 実行: .\scripts\commit_new_features.ps1

Set-Location "C:\Users\owner\Desktop\fixed-asset-ashigaru"

Write-Host "=== 新機能コミット ===" -ForegroundColor Cyan

# ステージング確認
git status

# コミット実行
$commitMessage = @"
feat: 新機能5種追加（PDF分割、類似検索、バッチ処理、台帳インポート）

主要機能:
- A2: PDF複数書類分割（Gemini Vision境界検出 + サムネイルグリッド）
- A1: 類似検索（履歴ベース文字列検索、APIフラグ切り替え可）
- B2: 類似事例表示UI
- B3: バッチアップロード機能
- C1: CSV/Excel台帳インポート

新規ファイル:
- api/gemini_splitter.py - Gemini境界検出
- api/history_search.py - API不要の履歴検索
- api/embedding_store.py - Embedding生成
- api/similarity_search.py - コサイン類似度検索
- core/pdf_splitter.py - サムネイルグリッド生成
- core/ledger_import.py - 台帳インポート
- ui/batch_upload.py - バッチUI
- ui/similar_cases.py - 類似事例表示UI
- scripts/create_multi_doc_pdf.py - デモPDF結合スクリプト

関ヶ原チェックポイント（tag: sekigahara-checkpoint）から実装

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
"@

git commit -m $commitMessage

Write-Host ""
Write-Host "完了！" -ForegroundColor Green
git log --oneline -1
