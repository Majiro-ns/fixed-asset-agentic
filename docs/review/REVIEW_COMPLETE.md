# 成果物 完全レビュー

> **作成日**: 2026-02-01  
> **対象**: 見積書 固定資産判定システム（第4回 Agentic AI Hackathon with Google Cloud）  
> **目的**: 提出前の総合レビュー・不足漏れの完全一覧

---

# 第1部 サマリ

## 1.1 総合結果

| 観点 | 結果 | 備考 |
|------|------|------|
| **テスト** | ✅ 14/14 PASS | test_api_response 5件、test_pdf_extract 6件、test_pipeline 3件 |
| **Golden Set** | ✅ 10/10 (100%) | eval_golden.py 正常 |
| **LICENSE** | ✅ MIT | 記載あり |
| **README** | ✅ 充実 | 審査員向け3点セット、デモ手順 |
| **提出物** | ⚠️ 未完了 | Zenn、デモ動画、参加登録、デプロイ |
| **コード品質** | ⚠️ 軽微な問題 | DEBUG print 1件、ドキュメント誤記 |

## 1.2 最優先アクション（提出ブロッカー）

1. commit & push（未push 68件の可能性・LORD記載）
2. Cloud Run再デプロイ（PDF_CLASSIFY_ENABLED=1）
3. GitHub公開確認
4. デモ動画（3分・PDF→分類）
5. Zenn記事（gch4必須、デモ動画埋め込み）
6. 参加登録（2/13締切）
7. プロジェクト提出（2/14〜2/15締切）
8. pipeline.py DEBUG print 削除
9. final_procedure.md normalizer→adapter 修正

**Cloud Run URL（撮影時の参照）:** `https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app`

---

# 第2部 できること・できないこと

## 2.1 できること

| カテゴリ | 内容 |
|----------|------|
| **判定・分類** | 3値判定（CAPITAL/EXPENSE/GUIDANCE）、キーワード判定、税務ルール(10/20/30/60万)、根拠提示 |
| **エージェント** | 停止、根拠提示、再実行（answers）、差分表示 |
| **入出力** | PDF→テキスト、表構造抽出、行単位パース、JSON分類、ポリシー適用 |
| **Feature Flag** | Document AI、Gemini分類、Vertex AI Search |

## 2.2 できないこと

| カテゴリ | 内容 |
|----------|------|
| **責任・判断** | 最終判断、税務アドバイス、責任の肩代わり |
| **自律性の限界** | 判断の動的選択、Chain of Thought、ツール自律組み合わせ |
| **未実装** | 勘定科目候補、耐用年数API連携、PDF画像理解、取得価額10%基準 |
| **制約** | OCR変更、未知語推論、他帳票対応、法令条文引用、PDFハイライト |

## 2.3 まとめ図

```
┌─────────────────────────────────────────────────────────────┐
│                      できること                             │
├─────────────────────────────────────────────────────────────┤
│ ・見積書の明細を 資産/費用/要確認 に分類                      │
│ ・判断が割れる場合は止めて、人間に確認を促す                  │
│ ・PDFを読んで表・行を抽出し、分類まで実行                    │
│ ・ユーザーの追加回答を受けて再分類し、差分を返す             │
│ ・根拠（evidence, flags）と不足情報を提示                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     できないこと                            │
├─────────────────────────────────────────────────────────────┤
│ ・最終判断（人間の確認を前提とする）                         │
│ ・勘定科目・耐用年数の候補提示（未実装）                     │
│ ・法令の条文番号での引用                                     │
│ ・キーワードにない語の文脈推論                               │
│ ・請求書・領収書等他帳票への対応                             │
└─────────────────────────────────────────────────────────────┘
```

---

# 第3部 勝つために必要なもの

## 3.1 必須（提出ブロッカー）

| 項目 | 理由 |
|------|------|
| Zenn記事 | 提出要件。未提出は失格 |
| Zennトピック「gch4」 | これがないと失格 |
| デモ動画（3分以内） | 提出要件 |
| 参加登録（2/13締切） | 遅れると失格 |
| GitHub公開 | 提出要件 |
| Cloud Run再デプロイ（PDF機能ON） | **PDF→分類のデモが勝利の鍵** |
| commit & push | 未pushだとPDF機能がCloud Runに反映されない |

## 3.2 優勝に直結（過去受賞作の共通点）

| 項目 | 理由 |
|------|------|
| PDFアップロード→一発で結果 | エンドツーエンドのデモ。JSON手動選択ではなくPDFから結果まで |
| Human-in-the-Loopの説明 | 「止まるAI」= Human-in-the-Loop をピッチで明示 |
| 業務時間削減の数値 | 「67%削減」「月167分」等、具体的な数値 |
| 5ステップAgenticループのデモ | 止まる→根拠提示→質問→再実行→差分 を動画で |
| Before→After DIFF | 「変わる」瞬間を動画で見せる |

## 3.3 デモ動画の推奨構成

| 時間 | 内容 | ポイント |
|------|------|----------|
| 0:00-0:30 | 問題提起 | 「判断を疑う余裕がない現場」 |
| 0:30-1:00 | PDFアップロード→CAPITAL_LIKE | PDFから一発で資産判定 |
| 1:00-1:30 | PDFアップロード→EXPENSE_LIKE | 費用判定も見せる |
| 1:30-2:30 | **JSON**（demo04_guidance_ambiguous）で GUIDANCE→再分類 | ※PDFフローではAgentic Loop未対応のためJSONで代用 |
| 2:30-3:00 | 技術説明・まとめ | GCP活用、Stop-first設計 |

**強調すべき3つの瞬間:** 止まる／聞く／変わる

**注意:** 撮影5分前に /health を叩く（コールドスタート対策）。テスト用PDF 3パターン（CAPITAL/EXPENSE/GUIDANCE）を準備。100-150字要約を事前準備（参加登録用。例: 見積書PDFをアップするだけで、明細行を理解し、固定資産か修繕費かの判断を支援します。判断が割れる場合は断定せずガイダンスに落とす、安全設計の実務向けAgentic AIです。）。

## 3.4 勝つために必要なもの まとめ図

```
┌─────────────────────────────────────────────────────────────┐
│              勝つために必要なもの（優先順）                   │
├─────────────────────────────────────────────────────────────┤
│ 最優先: commit/push → Cloud Run再デプロイ → GitHub公開      │
│       → デモ動画 → Zenn記事 → 参加登録(2/13) → プロジェクト提出(2/14) │
│ デモ: PDF一発判定、「止まるAI」口頭強調、Agenticループ動画   │
└─────────────────────────────────────────────────────────────┘
```

---

# 第4部 コードベース詳細レビュー

## 4.1 コアモジュール（core/）

| ファイル | 状態 | コメント |
|----------|------|----------|
| adapter.py | ✅ OK | Opal→v1正規化、line_items構築 |
| classifier.py | ✅ OK | 3値判定、税務ルール(10/20/30/60万)、キーワード |
| pdf_extract.py | ✅ OK | fitz/pdfplumber、表抽出、行単位パース、evidence.snippets |
| pipeline.py | ⚠️ 要修正 | **1行目に `print("[DEBUG] pipeline.py loaded")` が残存** |
| policy.py | ✅ OK | JSONポリシー読み込み |
| schema.py | ✅ OK | 定数、VERSION定義 |

## 4.2 API（api/）

| ファイル | 状態 | コメント |
|----------|------|----------|
| main.py | ✅ OK | /health, /classify, /classify_pdf、Feature Flag、Agentic Loop |
| gemini_classifier.py | ✅ OK | Stop-first設計、フォールバック |
| vertex_search.py | ✅ OK | Feature Flag、graceful degradation |
| useful_life_estimator.py | ⚠️ 未統合 | ファイル存在するが main.py から未呼び出し |

## 4.3 設定・インフラ

- **requirements.txt**: FastAPI, PyMuPDF, pdfplumber, google-generativeai, google-cloud-documentai 等
- **.gitignore**: data/除外、!data/golden/ !data/demo/ 許可、.gcloud_config/、add_apikey.bat、deploy.bat 含む
- **.dockerignore**: docs/, tests/, scripts/, ui/ 除外。policies/ 含む
- **CI**: push/PR で pytest 実行

---

# 第5部 実装の不足・重大なギャップ

## 5.1 重大（デモに直結）

| 項目 | 詳細 | 影響 |
|------|------|------|
| **PDF→GUIDANCE→Agentic Loop** | PDFアップロードでGUIDANCEが出た場合、追加情報→再判定ができない | デモの核心「止まる→聞く→変わる」がPDFフローで見せられない |
| **opal_json をレスポンスに含めない** | /classify_pdf のレスポンスに抽出した opal_json が含まれない | UI が initial_opal を保持できず再判定時にエラー |

**回避策:** デモでは JSON（demo04_guidance_ambiguous）で Agentic Loop をデモ。PDFはCAPITAL/EXPENSEの一発判定のみ。

## 5.2 未実装・未統合

| カテゴリ | 項目 |
|----------|------|
| AI統合 | ai_suggestions、useful_life API、Geminiマルチモーダル、Vertex/Gemini/DocAI 実動作確認 |
| 根拠・証跡 | evidence_keywords、applied_rule、legal_reference、trace_log 詳細化 |
| UI | PDF該当箇所ハイライト、position_hint 座標 |
| 抽出・パース | 合計・小計行の除外、extraction confidence、日付・ベンダー抽出 |
| 税務 | 取得価額10%基準、文脈考慮判定 |
| 運用 | Vertex AI タイムアウト、レート制限 |

## 5.3 実装済み

- 3値判定、税務ルール(10/20/30/60万)、Stop-first、Agentic Loop（JSONフロー）
- PDF抽出（fitz/pdfplumber）、表・行パース、/classify, /classify_pdf
- Gemini統合、Vertex Search、DocAI 呼び出し（_try_docai 実装済み）
- evidence.snippets、tax_rules フラグ

## 5.4 実装不足 まとめ図

```
┌─────────────────────────────────────────────────────────────┐
│           現在の実装に不足しているもの（カテゴリ別）           │
├─────────────────────────────────────────────────────────────┤
│ 提出物 │ Zenn, デモ動画, 参加登録, デプロイ, push           │
│ AI統合 │ ai_suggestions, useful_life API, 実動作確認        │
│ 根拠   │ evidence_keywords, applied_rule, 条文引用          │
│ UI     │ PDFハイライト, 座標情報                            │
│ 抽出   │ 合計行除外, confidence, 日付・ベンダー             │
│ 税務   │ 取得価額10%基準, 文脈考慮                          │
│ 運用   │ タイムアウト, レート制限, Lint, CI                │
└─────────────────────────────────────────────────────────────┘
```

---

# 第6部 不足・漏れ 全件一覧（92件）

## 6.1 提出物・手続き（13件）

1. Zenn記事、2. Zennトピック「gch4」、3. Zennカテゴリ「Idea」、4. デモ動画、5. 参加登録、6. 参加登録フォームURL、7. 100-150字要約、8. GitHub公開、9. commit & push、10. Cloud Run再デプロイ、11. LICENSE（submission_checklist との矛盾）、12. .gcloud_config 機密確認、13. 機密ファイルのコミット確認

## 6.2 機能・実装（19件）

14-15. PDF→GUIDANCE→Agentic Loop、opal_json レスポンス含めず  
16-29. ai_suggestions、useful_life、Geminiマルチモーダル、取得価額10%、evidence_keywords、applied_rule、legal_reference、合計行除外、confidence、日付・ベンダー、PDFハイライト、position_hint、タイムアウト、レート制限、Vertex/Gemini/DocAI 実動作

## 6.3 コード・設定（4件）

33. DEBUG print、34-36. Lint、Lint placeholder、CI Vertex AI テスト

## 6.4 ドキュメント不整合（8件）

37-44. normalizer→adapter、README clone URL、deploy_status streamlit、submission_checklist LICENSE、IMPLEMENTATION_STATUS/AUDIT DocAI、DEMO.md Next steps

## 6.5 デモ・UI（5件）

45-49. テスト用PDF 3パターン、撮影5分前 /health、Zenn URLプレースホルダ、Zenn published: false、sample_text.pdf 日本語

## 6.6 依存・ビルド・品質・仕様・テンプレ・重複・将来（30件）

**依存・ビルド（50-52）:** requirements.txt バージョン固定、Docker イメージの streamlit 肥大化、google-cloud-discoveryengine コメントアウト

**品質・テスト（53-55）:** Golden Set 10→20 拡充、pytest PyMuPDF DeprecationWarning、pytest 環境（WSL等）

**仕様・設計（56-58）:** 2026-FA-01 extraction.fields、2026-FA-04 data/legal/useful_life_tables、DocAI 複数ページ

**テンプレ・プレースホルダ（59-63）:** CLOUD_RUN_URL、IMPLEMENTATION_DELIVERABLE、CLOUDRUN_TRIAGE、gemini_integration_design、ISSUE_TEMPLATE

**重複（64-65）:** DEMO.md vs DEMO_RUNBOOK.md、RULES.md vs RULES2.md

**将来・オプション（66-75）:** 請求書・領収書・注文書、耐用年数マスタ、監査証跡、マルチテナント、写真・音声・図面、Dark Mode、Print Stylesheet、Keyboard Shortcuts、Loading States、Tooltips

## 6.7 追加漏れ（17件）

76-92. data/opal_outputs 不在、app.py vs app_minimal、COMPLIANCE_CHECKLIST リポジトリ名、デモ動画プラットフォーム、参加登録URL、締切時刻、チーム参加注意、Discord、RULES2必須条件、API入力検証、Cloud Run 32MB、OpenAPI /docs、CHANGELOG、CONTRIBUTING、pyproject.toml、COMPLIANCE最終確認日、run_pipeline デフォルト入力

---

# 第7部 ドキュメント修正一覧

| 箇所 | 問題 | 修正案 |
|------|------|--------|
| docs/final_procedure.md L53 | core/normalizer.py | core/adapter.py |
| README L125 | your-org/fixed-asset-agentic-repo | 実リポジトリURL |
| deploy_status.md L92 | streamlit 主要依存 | 削除または注記 |
| submission_checklist.md | LICENSE未作成 | 完了に更新 |
| COMPLIANCE_CHECKLIST L96 | fixed-asset-agentic-repo | fixed-asset-agentic |
| IMPLEMENTATION_STATUS/AUDIT | DocAI placeholder | 実装済みに更新 |
| integration_test_report | useful_life_estimator.py 存在の反映 | 更新 |

---

# 第8部 セキュリティ・運用

| 項目 | 状態 |
|------|------|
| .gcloud_config/ | .gitignore に含まれる |
| add_apikey.bat, deploy.bat | .gitignore に含まれる |
| ハードコード認証情報 | なし |
| 機密ファイルコミット | `git ls-files | grep -E '\.env|secret|credential|key\.json'` で再確認 |
| PyMuPDF (AGPL-3.0) | 商用利用時注意。README に記載済み |

---

# 第9部 参照

- [../UNIMPLEMENTED_ISSUES.md](../UNIMPLEMENTED_ISSUES.md) - 未実装課題一覧
- [../LORD_INSTRUCTIONSハッカソン残タスク.md](../LORD_INSTRUCTIONSハッカソン残タスク.md)
- [../submission_checklist.md](../submission_checklist.md)
- [../winning_patterns_analysis.md](../winning_patterns_analysis.md)
- [../00_project.md](../00_project.md) - Non-goals
- [../github_checklist.md](../github_checklist.md)
- [../zenn_article_draft.md](../zenn_article_draft.md)
