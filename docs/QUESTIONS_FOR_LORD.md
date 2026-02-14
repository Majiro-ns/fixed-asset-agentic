# 🏯 殿への伺い事項

**最終更新**: 2026-02-01 20:25

---

## 回答済み

### Q1: Embedding API料金について ✅

**殿の指示**: API機能を使わず、履歴から引っ張る方法を検討。フラグでON/OFF制御。

**対応完了**:
- `api/history_search.py` を新規作成（API不要の文字列類似度検索）
- サイドバーに「📚 過去履歴から類似検索」トグルスイッチ追加
- ONの場合のみ機能、デフォルトOFF
- SequenceMatcherによる編集距離ベースの類似度計算

### Q2: PDF分割デモ方法 ✅

**殿の指示**: 既存デモPDFを結合して作成。

**対応完了**:
- `scripts/create_multi_doc_pdf.py` を作成
- `scripts/create_multi_doc_pdf.ps1` も作成（Windows用）
- 殿のWindows環境で以下を実行:
  ```powershell
  cd C:\Users\owner\Desktop\fixed-asset-ashigaru
  pip install PyMuPDF
  python scripts/create_multi_doc_pdf.py
  ```
- 出力: `data/demo_pdf/demo_multi_documents.pdf`（3書類結合）

### Q3: requirements.txt ✅

**殿の指示**: 受理。

---

## 🚨 殿のアクション待ち

### Gitコミット実行
WSL環境でgit configが未設定のため、殿のWindows環境でコミットを実行願います：

```powershell
cd C:\Users\owner\Desktop\fixed-asset-ashigaru
.\scripts\commit_new_features.ps1
```

または手動で:
```powershell
git commit -m "feat: 新機能5種追加（PDF分割、類似検索、バッチ処理、台帳インポート）"
```

---

## 実装判断（将軍判断で進めた事項）

### 1. 類似検索のデフォルト設定
- **デフォルトOFF** - 明示的にONにした場合のみ機能
- 理由: 履歴が少ない状態では類似事例が出ず混乱を招く

### 2. 類似度の閾値
- 履歴検索: 0.5（50%以上で表示）
- Embedding検索: 0.7（70%以上で表示）
- 履歴検索は文字列ベースのため、緩めの閾値を設定

---

## 実装完了報告（追加分）

| ファイル | 機能 |
|----------|------|
| `api/history_search.py` | 履歴ベース類似検索（API不要） |
| `scripts/create_multi_doc_pdf.py` | 複数書類PDF結合スクリプト |
| `scripts/create_multi_doc_pdf.ps1` | 同上（PowerShell版） |

### 変更ファイル
| ファイル | 変更内容 |
|----------|----------|
| `ui/app_minimal.py` | 類似検索トグル追加、履歴検索に切り替え、PDF分割UI統合 |
| `api/main.py` | /classify_batch追加、start_page/end_page対応 |

---

## 実装完了報告（新規ファイル全一覧）

| ファイル | 機能 |
|----------|------|
| `api/embedding_store.py` | Embedding生成（Gemini text-embedding-004） |
| `api/gemini_splitter.py` | PDF境界検出（Gemini Vision） |
| `api/history_search.py` | 履歴ベース類似検索（API不要） |
| `api/similarity_search.py` | コサイン類似度検索 |
| `core/pdf_splitter.py` | サムネイルグリッド生成 |
| `core/ledger_import.py` | CSV/Excel台帳インポート |
| `ui/batch_upload.py` | バッチアップロードUI |
| `ui/similar_cases.py` | 類似事例表示UI |
| `scripts/create_multi_doc_pdf.py` | デモPDF結合スクリプト |
| `scripts/create_multi_doc_pdf.ps1` | 同上（PowerShell版） |
| `tests/test_*.py` | 各モジュールのテスト |
| `docs/CHECKPOINT_SEKIGAHARA.md` | 復旧手順書 |
| `docs/DEMO_PDF_SPLIT_MEMO.md` | PDF分割デモメモ |

---

## 次のステップ（提出まで）

1. ✅ 全機能実装完了
2. ✅ Gitコミット完了（cbb48d7）
3. ⏳ Cloud Runデプロイ（API + UI）
   - 環境変数設定: `GEMINI_MODEL=gemini-3-pro-preview`, `GEMINI_SPLITTER_MODEL=gemini-3-pro-preview`
4. ⏳ デモ動画撮影（2/8予定）
5. ⏳ YouTube公開
6. ⏳ Zenn記事更新・公開
7. ⏳ 提出（締切: 2/13）

---

## ⚠️ デプロイ前チェックリスト

- [ ] **開発者オプションをUIから削除する**
  - `ui/app_minimal.py` の「🔧 開発者向け」セクションを削除またはコメントアウト
  - デバッグ表示トグルを本番UIから隠す

---
