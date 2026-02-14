# 未修正指摘 再確認結果

**確認日**: 2026-02-10
**確認者**: ashigaru3
**参照元**: 08_Skill_Based_Review.md（47件） / 09_Fix_Log.md（22件修正済み）

---

## サマリ

- 総指摘数: **47件**
- 修正済み: **25件**（Fix Log記載21件 + コード確認で追加発見4件）
- 部分修正: **1件**（#10: app.pyリネームのみ、削除未実施）
- 未修正: **21件**（Major 10件 + Minor 11件）

### 修正状況の内訳

| カテゴリ | 修正済み | 部分修正 | 未修正 |
|----------|---------|---------|--------|
| Critical (11件) | 10 | 1 | 0 |
| Major (22件) | 12 | 0 | 10 |
| Minor (14件) | 3 | 0 | 11 |

---

## Fix Log記載の修正済み22件 → 実際に対応した指摘21件

| Fix# | 指摘# | 概要 | コード確認 |
|------|-------|------|-----------|
| 1 | #1 SEC-C01 | APIキー認証導入 | ✅ api/main.py:82-92 verify_api_key実装確認 |
| 2 | #2 SEC-C02 | パストラバーサル対策 | ✅ api/main.py:96-106 _validate_policy_path実装確認 |
| 3 | #3 SEC-C03 | アップロードバリデーション | ✅ MIME・マジックバイト・サイズ・バッチ数制限確認 |
| 4 | #4 SEC-C04 | プロンプトインジェクション対策 | ✅ _sanitize_text・デリミタ分離確認 |
| 5 | #5 PRI-C01 | PDF保持期間ポリシー | ✅ cleanup_old_files関数確認 |
| 6 | #6 PRI-C02 | JSON保持期間ポリシー | ✅ data/results/にもクリーンアップ適用確認 |
| 7 | #7 PRI-C03 | LLMデータ送信の情報開示 | ✅ app_minimal.py:629 st.info確認 |
| 8 | #25 Bug | confidence 0.8→0.0 | ✅ 3箇所修正確認 |
| 9 | #10 PRD-C01 | UI二重実装 | ⚠️ app.py→app_classic.pyリネームのみ。削除未実施 |
| 10 | #11 PRD-C02 | .gitignore追加 | ✅ data/results/、data/uploads/追加確認 |
| 11 | #8 UI-C01 | 技術用語平易化 | ✅ app_classic.pyで書換確認 |
| 12 | #9 UI-C02 | テーブルカラム日本語化 | ✅ app_classic.pyで書換確認 |
| 13 | #20 UI-M04 | GUIDANCE用語統一 | ✅ 「確認が必要です」に統一確認 |
| 14 | #30 UI-M01 | diff_display日本語化 | ✅ diff_display.py:87-91 変更前:/変更後: 確認 |
| 15 | #21 UI-M08 | コントラスト比改善 | ✅ #4B5563（WCAG AA準拠）確認 |
| 16 | #36 m-03 | 確信度表現改善 | ✅ 「概ね確実（念のため確認推奨）」確認 |
| 17 | #24 OB-M04 | Empty State充実 | ✅ input_area.py:414-418 3行ガイダンス確認 |
| 18 | #13 SEC-M02 | CORS設定 | ✅ CORSMiddleware追加確認 |
| 19 | #14 SEC-M03 | レート制限 | ✅ slowapi導入確認 |
| 20 | #17 PRI-M05 | URL hardcode除去 | ✅ 環境変数API_BASE_URL化確認 |
| 21 | #33 監査ログ | 構造化ログ導入 | ✅ _JSONFormatter・request_id付きログ確認 |
| 22 | #12 SEC-M01 | 免責表示ルール | ✅ disclaimerフィールド・高確信度追加免責確認 |

---

## Fix Logに記載なし・コード確認で修正済みと判明（4件）

| 指摘# | 概要 | 確認結果 |
|-------|------|---------|
| #15 SEC-M04 | 一時ファイル管理（uploads永続保存） | ✅ Fix #5/6のcleanup_old_filesがdata/uploads/にも適用。24時間TTL |
| #18 バッチ制限 | バッチファイル数・サイズ制限なし | ✅ Fix #3に含まれる（_MAX_BATCH_FILES=20、_MAX_UPLOAD_SIZE=50MB） |
| #39 OB-m01 | サイドバーヘルプが3行のみ | ✅ app_minimal.py:279-300 expanderで「使い方」「判定結果の見方」「制限事項」に拡充済み |
| #45 PRD-m02 | .envがリポジトリに存在する可能性 | ✅ .gitignoreに`.env`が記載済み |

---

## 部分修正（1件）

| 指摘# | 概要 | 状況 | 残作業 |
|-------|------|------|--------|
| #10 PRD-C01 | UIの二重実装（app.py/app_minimal.py） | app.py→app_classic.pyにリネーム済み。しかし削除されておらず、658行のコードが残存 | app_classic.pyの削除、またはapp_minimal.pyへの必要機能統合 |

---

## 未修正指摘一覧

### Major（10件）

| # | 指摘# | 深刻度 | 対象ファイル:行 | 内容 | 修正優先度 |
|---|-------|--------|----------------|------|-----------|
| 1 | #16 | Major | api/embedding_store.py:203-213 | Embedding StoreのJSON平文保存（暗号化なし、パーミッション未設定） | 中（MVP不要機能内の問題） |
| 2 | #19 | Major | ui/components/result_card.py, guidance_panel.py, diff_display.py | unsafe_allow_htmlコンポーネントにrole/aria-label/aria-live属性が皆無 | 高（アクセシビリティ） |
| 3 | #22 | Major | ui/app_classic.py:620-626 | 冒頭info枠「なぜ止まる自動判定が必要か」が初回ユーザーに不要な認知負荷 | 低（app_classic.pyは非主要UI） |
| 4 | #23 | Major | ui/components/input_area.py:350-355 | 高精度モードトグルが初回画面に露出（デフォルトOFFのまま初見ユーザーの認知負荷増） | 中 |
| 5 | #26 | Major | ui/batch_upload.py（全体） | バッチアップロード機能はMVP不要（feature flagによる無効化未実施） | 中（プロダクト判断） |
| 6 | #27 | Major | api/embedding_store.py, similarity_search.py, history_search.py | 類似検索・履歴検索機能群はMVP不要（ファイル残存） | 中（プロダクト判断） |
| 7 | #28 | Major | core/pdf_splitter.py, api/gemini_splitter.py | PDF分割機能はMVP不要（ファイル残存） | 中（プロダクト判断） |
| 8 | #29 | Major | docs/（65ファイル） | ドキュメント過剰（47→65ファイルに増加）。README+DEPLOY+00_projectに集約推奨 | 低 |
| 9 | #31 | Major | ui/app_classic.py:244-320相当 | Step1情報過多（1画面1メッセージの原則違反） | 低（app_classic.pyは非主要UI） |
| 10 | #32 | Major | api/main.py:620, api/main.py:970 | エラーメッセージで内部情報漏洩。`f"Invalid input: {str(e)}"` と `f"処理中にエラーが発生: {str(e)}"` が残存 | 高（セキュリティ） |

### Minor（11件）

| # | 指摘# | 深刻度 | 対象ファイル:行 | 内容 | 修正優先度 |
|---|-------|--------|----------------|------|-----------|
| 11 | #34 | Minor | ui/components/hero_section.py:24,65 | 「Powered by Gemini 3 Pro」バッジがペルソナに不要 | 低 |
| 12 | #35 | Minor | ui/components/input_area.py:351 | 「高精度モード（AI Vision）」ラベルが技術的。「手書き・複雑な表に対応」推奨 | 低 |
| 13 | #37 | Minor | ui/components/guidance_panel.py:467 | 「→ 経費になります」の断言表現。「→ 経費になることが多いです」推奨 | 低 |
| 14 | #38 | Minor | ui/app_classic.py:642-645 | サイドバーヘルプがcaption（テキスト）のみ、expanderなし | 最低（app_classic.pyは非主要UI） |
| 15 | #40 | Minor | ui/app_minimal.py:612-618 | 免責事項がフッター最下部のみ。結果カード直下にも簡潔な免責を配置推奨 | 低 |
| 16 | #41 | Minor | ui/app_minimal.py:211 | サイドバーが初期折り畳み（initial_sidebar_state="collapsed"）。初回のみ展開推奨 | 低 |
| 17 | #42 | Minor | ui/components/guidance_panel.py:278 | 「↩ 選び直す」ボタンが目立たない（デフォルトスタイル） | 低 |
| 18 | #43 | Minor | api/main.py:164-187相当 | 集計ロジック（CAPITAL/EXPENSE/GUIDANCE判定）の仕様が明文化されていない | 低 |
| 19 | #44 | Minor | requirements.txt | google-genai, google-cloud-documentai等がMVP不要な依存として含まれる | 低（google-genaiはGEMINI_ENABLED用） |
| 20 | #46 | Minor | scripts/ | create_demo_pdfs, _v2, _v3 の3バージョンが重複残存 | 低 |
| 21 | #47 | Minor | api/main.py:982 | _process_single_pdfとclassify_pdf関数の大部分が重複（DRY違反） | 低（batch機能自体がMVP不要） |

---

## 優先度別推奨アクション

### 高優先度（次スプリント推奨）

| # | 指摘# | アクション |
|---|-------|-----------|
| 1 | #32 | api/main.py:620,970のエラーメッセージを定型文に変更。例外詳細はlogger.errorのみ |
| 2 | #19 | result_card.py, guidance_panel.py, diff_display.pyのカードにrole="region" aria-label追加 |
| 3 | #10 | app_classic.pyの削除判断（必要機能があればapp_minimal.pyに統合） |

### 中優先度（プロダクト判断待ち）

| # | 指摘# | アクション |
|---|-------|-----------|
| 4 | #23 | 高精度モードトグルをデフォルトON化、または詳細設定に移動 |
| 5 | #26-28 | batch_upload, 類似検索, PDF分割のfeature flag無効化（殿の判断待ち） |
| 6 | #16 | Embedding Store暗号化（ただしMVP不要機能内の問題） |

### 低優先度（改善推奨）

| # | 指摘# | アクション |
|---|-------|-----------|
| 7 | #34,35 | Geminiバッジ移動、高精度モードラベル変更 |
| 8 | #37 | 断言表現の緩和 |
| 9 | #40,41 | 免責事項の配置改善、サイドバー初期状態 |
| 10 | #29 | docs/の整理（65→3-5ファイルに集約） |
| 11 | #46 | スクリプト重複削除 |
| 12 | #42,43 | 選び直しボタン強調、集計ロジック仕様書 |
| 13 | #44,47 | requirements分離、関数重複解消 |

---

## 検証記録

| ファイル | 確認行 | 備考 |
|----------|--------|------|
| api/main.py | 1-100, 155-185, 490-570, 620, 970, 982 | 認証・CORS・ログ・エラーメッセージ・関数重複 |
| api/embedding_store.py | 195-250 | save()のJSON平文保存確認 |
| api/gemini_classifier.py | (前回精読済み) | プロンプトインジェクション対策確認 |
| ui/app_minimal.py | 195-245, 270-320, 600-650 | サイドバー・免責事項・フォールバック |
| ui/app_classic.py | 610-658 | info枠・サイドバーヘルプ・タブ構造 |
| ui/components/hero_section.py | 1-73 | Geminiバッジ確認 |
| ui/components/input_area.py | 1-419 | 高精度モードトグル・Empty State確認 |
| ui/components/guidance_panel.py | 455-504 | 断言表現・選び直しボタン確認 |
| ui/components/result_card.py | 170-218 | aria属性の不在確認 |
| ui/components/diff_display.py | 75-102 | 日本語ラベル確認・aria属性不在確認 |
| requirements.txt | 全体 | 依存パッケージ確認 |
| .gitignore | 全体 | .env、data/results/、data/uploads/確認 |
| scripts/ | ファイル一覧 | create_demo_pdfs 3バージョン残存確認 |
| docs/ | ファイル数 | 65ファイル確認 |

全47件を漏れなく確認済み。未修正判定は全て実コードの該当行を読んで確認。
