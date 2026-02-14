---
title: "固定資産判定ツール スキル知見ベースレビュー"
date: 2026-02-10
reviewers: "multi-agent-shogun (ashigaru 1-8)"
---

# 固定資産判定ツール スキル知見ベースレビュー

## エグゼクティブサマリ

本レビューは8名の足軽がそれぞれの専門観点からfixed-asset-ashigaru（固定資産判定ツール）を精査した結果を統合したものである。**Critical指摘11件、Major指摘22件、Minor指摘14件**を検出した。最大のリスクはAPIの認証不在（セキュリティ）とアップロードPDFの無期限保存（プライバシー）である。一方、Stop-first/Fail-to-GUIDANCE設計は業界水準を超える優秀さであり、app_minimal.py + コンポーネント群のAgentic UXも高く評価できる。app.pyの技術用語露出、MVPスコープの肥大化、デフォルトconfidence 0.8の残存が横断的な改善課題である。

---

## 1. UI/認知判断レビュー

**レビュー元**: 01_ui_cognitive.md（ashigaru1）

### 評価概要

app_minimal.py（production版）は「止まる→聞く→変わる」のAgentic設計が認知設計の原則に沿って実装されており、特にguidance_panel.pyの2段階ウィザードは秀逸。初見3秒テストもクリア。一方、app.py（classic版）は技術用語（Opal/Adapter/Classifier/凍結スキーマ）がUIテキストに大量に露出しており、ペルソナ「高卒事務の経理担当者」にCriticalレベルの認知障壁を形成。

### 主要指摘

| # | 深刻度 | 対象 | 概要 |
|---|--------|------|------|
| UI-C01 | Critical | app.py:21-34 | タイトル・ステップラベルに開発者用技術用語（Opal、Agentic、凍結スキーマ、揺れるJSON）が露出 |
| UI-C02 | Critical | app.py:100-113 | テーブルカラム名が英語内部コード（classification, flags, evidence） |
| UI-M01 | Major | diff_display.py:87-92 | 「Before:/After:」英語ラベル |
| UI-M02 | Major | app.py:244-320 | Step1情報過多（1画面1メッセージの原則違反） |
| UI-M03 | Major | 複数コンポーネント | unsafe_allow_htmlにaria-label等アクセシビリティ属性が皆無 |
| UI-M04 | Major | 複数ファイル | GUIDANCE用語揺れ：「要確認」「GUIDANCE」「確認が必要」「判断を保留」の混在 |
| UI-M08 | Major | styles.py:122-126 | 免責事項のコントラスト比2.9:1（WCAG AA基準4.5:1未達） |

### 良い点

- app_minimal.pyの色彩設計（4色体系: amber/green/blue/gray）は一貫して適切
- 「色+emoji+テキスト」の冗長コーディングで色覚障害にも対応
- guidance_panel.pyのステップ進捗表示は認知負荷を適切に管理

---

## 2. オンボーディング/初回体験レビュー

**レビュー元**: 02_onboarding.md（ashigaru2）

### 評価概要

app_minimal.pyはTTFV（Time to First Value）約30秒で目標の60秒以内を達成。PDFドラッグ&ドロップ→判定→結果の3ステップ導線が直感的。app.pyはTTFVが60秒超の可能性が高く、ペルソナに対して不適格。

### 主要指摘

| # | 深刻度 | 対象 | 概要 |
|---|--------|------|------|
| OB-C01 | Critical | app.py:21-23 | タイトルに技術用語（Opal、Agentic、Stop設計）→初回5秒で離脱リスク |
| OB-C02 | Critical | app.py:32-37 | 「Opal JSON入力」タブがデフォルト→ペルソナはJSONを知らない |
| OB-M01 | Major | app.py:617-626 | 冒頭info枠「なぜ止まるAgentが必要か」が初回ユーザーに不要な認知負荷 |
| OB-M02 | Major | hero_section.py:24 | 「Powered by Gemini 3 Pro」バッジがペルソナに不要 |
| OB-M03 | Major | input_area.py:350-355 | 「高精度モード（AI Vision）」トグルが初回画面に露出 |
| OB-M04 | Major | input_area.py:413-414 | Empty Stateのガイダンスが1行のみ |

### 良い点

- guidance_panel.pyの2段階フローは設計工学的に正しいオンボーディング
- 開発者機能の分離（?dev=1パラメータ）は段階的開示の好例
- result_card.pyの信頼度表現（「ほぼ確実」「念のため確認を」）は平易で適切

---

## 3. 信頼設計レビュー

### 3.1 セキュリティ

**レビュー元**: 03_trust_security.md（ashigaru3）

#### 評価概要

Critical 4件、Major 4件、Minor 2件。APIエンドポイントに認証・認可が一切なく全エンドポイントが無防備。policy_pathにパストラバーサル脆弱性、PDFアップロードのバリデーション不在、プロンプトインジェクション対策未実装。Fail-to-GUIDANCE設計は適切だが、確信度90%超の免責表示ルールが未実装。

#### 主要指摘

| # | 深刻度 | 対象 | 概要 |
|---|--------|------|------|
| SEC-C01 | Critical | api/main.py:111 | APIエンドポイントに認証・認可がない（全エンドポイント無防備） |
| SEC-C02 | Critical | api/main.py:376-382 | policy_pathパラメータのパストラバーサル（../../etc/passwd等が読める） |
| SEC-C03 | Critical | api/main.py:506-514 | アップロードファイルのバリデーション不在（タイプ・サイズ・数の検証なし） |
| SEC-C04 | Critical | gemini_classifier.py:324-396 | プロンプトインジェクション対策の不在（悪意あるPDF入力で判定操作可能） |
| SEC-M01 | Major | api/main.py:120-138 | 確信度90%超の免責表示ルールが未実装 |
| SEC-M02 | Major | api/main.py:111 | CORS設定が未定義 |
| SEC-M03 | Major | 全エンドポイント | レート制限の不在（金銭的DoSリスク） |
| SEC-M04 | Major | core/pipeline.py:60-75 | 一時ファイル永続保存（data/uploads/にアクセス制御・暗号化・TTLなし） |

#### チェックリスト準拠率

- 脅威モデリング: 0/7項目準拠
- 認証: 0/4項目準拠
- 認可: 0/5項目準拠
- Fail-Safe Defaults: **GUIDANCE設計は秀逸**

### 3.2 プライバシー＋デフォルト安全

**レビュー元**: 04_trust_default_safe.md（ashigaru4）

#### 評価概要

Fail-Closed（Stop設計）は信頼設計のお手本。一方、アップロードPDFの永続保存が最大のプライバシーリスク。LLMへのデータ送信に関するユーザー通知・同意が皆無。

#### 主要指摘

| # | 深刻度 | 対象 | 概要 |
|---|--------|------|------|
| PRI-C01 | Critical | core/pipeline.py:60-75, ui/app.py:214-224 | アップロードPDFの無期限保存（削除ポリシー・保持期間・自動削除なし） |
| PRI-C02 | Critical | core/pipeline.py:78-109 | 抽出結果JSONの無期限保存（平文で機密情報を含む） |
| PRI-C03 | Critical | gemini_classifier.py:260-268 | LLMへのデータ送信に関する情報開示の欠如（同意取得なし） |
| PRI-M01 | Major | embedding_store.py:203-213 | Embedding StoreのJSON平文保存（暗号化なし） |
| PRI-M05 | Major | batch_upload.py:291 | 本番Cloud Run URLがソースコードにハードコード（GCPプロジェクト番号露出） |

#### チェックリスト準拠率

- プライバシー設計: 6/23（26%）— 要改善
- デフォルト安全: 2/9（22%）— 要改善
- **P6 Fail Secure（Stop設計）は業界水準を大きく超える優秀さ**

---

## 4. Zenn先行事例調査

**レビュー元**: 05_zenn_research_1.md + 06_zenn_research_2.md（ashigaru5, 6）

### 調査規模

- 11キーワードで計110件超の記事を調査、**22件を深掘り分析**

### 主要発見

#### 設計パターンの類型化

| パターン | 記事数 | 精度 | 概要 |
|---------|--------|------|------|
| A: LLM直接型 | 2件 | 約60% | 画像→LLM直接。最も低精度 |
| **B: OCR+LLMハイブリッド型** | **5件** | **約70-80%** | **最多。OCRでテキスト抽出→LLMで構造化** |
| **C: 三層型（OCR+LLM+ルール）** | **2件** | **約80%** | **最高精度。LLMの弱点をルールで補完** |
| D: LLM蒸留型 | 1件 | — | LLMで教師データ生成→小型モデル推論 |

#### 会計AI領域の共通パターン

1. **「AI提案→人間承認」モデル**: 完全自動化ではなく人間レビュー必須が標準
2. **信頼度スコアの可視化**: OCR/LLM判定の信頼度をUIに表示
3. **継続学習サイクル**: 人間の修正をフィードバックとして精度向上
4. **判定基準の標準化**: ポリシーベース判定ルールの明文化

### fixed-asset-ashigaruへの提言（優先度順）

| 優先度 | 改善点 | 効果 |
|--------|--------|------|
| **最優先** | 三層構造の採用（OCR→LLM→ルールベースバリデーション） | 精度向上（900件検証で最高精度） |
| **最優先** | 抽出結果の視覚的検証UI（座標ベースハイライト） | ユーザーの確認効率向上 |
| **最優先** | Few-shot Learningの導入 | 判定安定化 |
| 高 | LLM判定の信頼度スコア表示 | レビュー効率化 |
| 高 | 判定精度の定量評価基盤 | 品質の可視化 |
| 中 | Cloudflare Tunnel + Accessでのセキュアデプロイ | 認証をインフラレベルで解決 |
| 中 | FastAPIエンドポイントのMCP対応 | AIエージェント連携 |
| 中 | LLM呼び出しのリポジトリパターン化（オニオンアーキテクチャ） | LLMプロバイダ切り替え容易性 |

---

## 5. プロダクト判断力レビュー

**レビュー元**: 07_product_judgment.md（ashigaru7）

### 評価概要

コア判定ロジック（core/）は堅実でMVPとして適切なスコープ。しかしUIが2系統並存（app.py: 658行 / app_minimal.py: 755行）しており、batch_upload、embedding_store、similarity_search、ledger_import、pdf_splitter等のMVP不要機能が大量に実装済み。「ついでにこれも」症候群の典型。

### 主要指摘

| # | 深刻度 | 対象 | 概要 |
|---|--------|------|------|
| PRD-C01 | Critical | ui/app.py, ui/app_minimal.py | UIの二重実装（保守コスト2倍）→ app.py削除、app_minimal.pyに一本化 |
| PRD-C02 | Critical | data/results/ | 中間ファイルが100+件残存（機密データ含むリスク）→ .gitignoreに追加 |
| PRD-M01 | Major | ui/batch_upload.py | バッチアップロードはMVP不要（1件ずつで仮説検証可能） |
| PRD-M02 | Major | embedding/similarity/history | 類似検索・履歴検索機能群はMVP不要 |
| PRD-M03 | Major | pdf_splitter.py, gemini_splitter.py | PDF分割（高精度モード）はMVP不要 |
| PRD-M04 | Major | docs/ | ドキュメント過剰（約40ファイル）→ README + DEPLOY + 00_project の3ファイルに集約 |

### MVPチェックリスト結果

| フェーズ | 準拠/非準拠 |
|---------|-----------|
| 仮説の明確化 | 一部準拠（仮説は明確だが成功/失敗指標未定義） |
| スコープの絞り込み | **非準拠**（Must以外が大量に実装済み） |
| 検証方法の選択 | 不明（代替手段の検討記録なし） |
| MVP構築時のチェック | **非準拠**（Should/Couldが大量実装、「ついでにこれも」該当） |
| 計測と判断 | **非準拠**（アナリティクス未実装） |

### バランス評価

| 軸 | 評価 |
|----|------|
| 判定の正確さ | **過剰投資**（Gemini+ルールベース+Vertex AI Search+類似検索の4層。ルールベース1層で十分） |
| UXの良さ | **適切**（Streamlitベースの割り切り、Stop設計の反映） |
| 開発速度 | **遅延**（スコープ拡大により本来の2-3倍の工数） |

---

## 6. 既知バグ・教訓の確認

**レビュー元**: 08_known_bugs.md（ashigaru8）

### 確認結果

| バグ | 状態 | 深刻度 |
|------|------|--------|
| confidence常に0.80バグ | **部分的修正済** | Major |
| 集計ロジック「1つでもGUIDANCEなら全体GUIDANCE」 | **仕様通り（別ロジック）** | Minor |

### Bug 1: confidence常に0.80（Major）

`core/classifier.py`に`_calculate_confidence()`が新設され、分類結果に応じた確信度（0.40〜0.95）が適切に計算・設定されるようになった。しかし`api/main.py`内にデフォルト値0.8が**3箇所残存**（212行, 268行, 274行の`item.get("confidence", 0.8)`）。classifier障害時に不正な高確信度が暗黙的に返されるリスクあり。

### Bug 2: 集計ロジック（Minor）

現在の実装は「CAPITAL_LIKEとEXPENSE_LIKEが両方存在する場合にGUIDANCE」であり、「1つでもGUIDANCEなら全体GUIDANCE」ではない。Gemini decisionが最優先、次にルールベース多数決。Stop設計の思想に合致するが、仕様書に判定基準が明文化されていない。

---

## 指摘事項サマリ（全観点統合）

| # | 深刻度 | 観点 | 対象 | 概要 | 修正提案 |
|---|--------|------|------|------|----------|
| 1 | Critical | セキュリティ | api/main.py:111 | APIエンドポイントに認証・認可がない | APIキー認証またはCloud Run IAM有効化 |
| 2 | Critical | セキュリティ | api/main.py:376-382 | policy_pathパストラバーサル | パスバリデーション（ファイル名のみ許可） |
| 3 | Critical | セキュリティ | api/main.py:506-514 | ファイルアップロードのバリデーション不在 | MIMEタイプ・サイズ・数の検証追加 |
| 4 | Critical | セキュリティ | gemini_classifier.py:324-396 | プロンプトインジェクション対策なし | 入力デリミタ分離・長さ制限・サニタイズ |
| 5 | Critical | プライバシー | core/pipeline.py:60-75 | アップロードPDFの無期限保存 | 保持期間定義・自動削除の実装 |
| 6 | Critical | プライバシー | core/pipeline.py:78-109 | 抽出結果JSONの無期限平文保存 | 保持期間・暗号化・パーミッション制限 |
| 7 | Critical | プライバシー | gemini_classifier.py他 | LLMへのデータ送信の情報開示欠如 | UIに説明追加・オプトイン同意取得 |
| 8 | Critical | UI/認知 | app.py:21-34 | タイトル・ラベルに技術用語が大量露出 | ペルソナ向け平易な日本語に書き換え |
| 9 | Critical | UI/認知 | app.py:100-113 | テーブルカラム名が英語内部コード | 日本語ラベルに変更 |
| 10 | Critical | プロダクト | app.py / app_minimal.py | UIの二重実装 | app.py削除、app_minimal.pyに一本化 |
| 11 | Critical | プロダクト | data/results/ | 中間ファイル100+件残存 | .gitignore追加、git履歴からも除去 |
| 12 | Major | セキュリティ | api/main.py:120-138 | 確信度90%超の免責表示未実装 | disclaimerフィールド追加 |
| 13 | Major | セキュリティ | api/main.py:111 | CORS設定未定義 | CORSMiddleware追加（オリジン限定） |
| 14 | Major | セキュリティ | 全エンドポイント | レート制限の不在 | slowapi導入（10 req/min/IP等） |
| 15 | Major | セキュリティ | core/pipeline.py:60-75 | 一時ファイルの管理（uploads永続保存） | TTL設定・パーミッション制限 |
| 16 | Major | プライバシー | embedding_store.py:203-213 | Embedding Store平文保存 | 暗号化・パーミッション制限 |
| 17 | Major | プライバシー | batch_upload.py:291 | 本番Cloud Run URLハードコード | 環境変数化（デフォルトlocalhost） |
| 18 | Major | プライバシー | api/main.py:746-842 | バッチファイル数・サイズ制限なし | 上限設定（20ファイル、50MB/file） |
| 19 | Major | UI/認知 | 複数コンポーネント | unsafe_allow_htmlにaria属性なし | role/aria-label/aria-live追加 |
| 20 | Major | UI/認知 | 複数ファイル | GUIDANCE用語揺れ（5種類の表現混在） | 「確認が必要です」に統一 |
| 21 | Major | UI/認知 | styles.py:122-126 | 免責事項コントラスト比2.9:1 | 文字色を#6B7280以上に |
| 22 | Major | オンボーディング | app.py:617-626 | 冒頭info枠が初回ユーザーに不要 | expanderに格納または判定後に移動 |
| 23 | Major | オンボーディング | input_area.py:350-355 | 高精度モードトグルが初回画面に露出 | デフォルトONにし詳細設定に移動 |
| 24 | Major | オンボーディング | input_area.py:413-414 | Empty Stateのガイダンスが1行のみ | 対象PDF形式・サンプル導線を追加 |
| 25 | Major | 既知バグ | api/main.py:212,268,274 | デフォルトconfidence 0.8が3箇所残存 | デフォルト値を0.0またはNoneに変更 |
| 26 | Major | プロダクト | batch_upload.py, /classify_batch | バッチ機能はMVP不要 | feature flagで無効化 |
| 27 | Major | プロダクト | embedding/similarity/history | 類似検索・履歴機能群はMVP不要 | 後回し（try/except化済みで可） |
| 28 | Major | プロダクト | pdf_splitter.py, gemini_splitter.py | PDF分割はMVP不要 | 無効化 |
| 29 | Major | プロダクト | docs/（約40ファイル） | ドキュメント過剰 | README+DEPLOY+00_projectに集約 |
| 30 | Major | UI/認知 | diff_display.py:87-92 | 英語ラベル「Before:/After:」 | 「変更前:/変更後:」に変更 |
| 31 | Major | UI/認知 | app.py:244-320 | Step1情報過多 | 1カラム化、タブ切り替え |
| 32 | Major | プライバシー | api/main.py:501, gemini_classifier.py | エラーメッセージでの内部情報漏洩 | ユーザー向けは定型文、詳細はログのみ |
| 33 | Major | セキュリティ | api/ 全体 | 監査ログの不足（loggingすら未使用） | Python logging導入、構造化ログ |
| 34 | Minor | UI/認知 | hero_section.py:24 | 「Powered by Gemini 3 Pro」がペルソナに不要 | 非表示またはフッターに移動 |
| 35 | Minor | UI/認知 | input_area.py:350-355 | 「高精度モード（AI Vision）」ラベルが技術的 | 「手書き・複雑な表に対応」に変更 |
| 36 | Minor | UI/認知 | app_minimal.py:398 | 確信度「たぶん大丈夫」のトーンが軽い | 「概ね確実（念のため確認推奨）」に |
| 37 | Minor | UI/認知 | guidance_panel.py:466-468 | 「経費になります」の断言 | 「経費になることが多いです」に |
| 38 | Minor | UI/認知 | app.py:642-645 | サイドバーヘルプにクリッカブル要素なし | expanderまたはtooltip化 |
| 39 | Minor | オンボーディング | app_minimal.py:279-284 | サイドバーヘルプが3行のみ | 対象書類、結果の見方等を追記 |
| 40 | Minor | オンボーディング | app_minimal.py:612-618 | 免責事項が最下部のみ・小フォント | 結果カード直下にも簡潔な免責を配置 |
| 41 | Minor | オンボーディング | app_minimal.py:207-212 | サイドバーが初期折り畳み | 初回のみ展開、またはメイン画面にヘルプリンク |
| 42 | Minor | オンボーディング | guidance_panel.py全体 | 「選び直す」ボタンが目立たない | サイズ・色を強調 |
| 43 | Minor | 既知バグ | api/main.py:164-187 | 集計ロジックの仕様が明文化されていない | docs/に集計ロジック仕様を追記 |
| 44 | Minor | プロダクト | requirements.txt | MVP不要な依存含む | core/fullに分離 |
| 45 | Minor | プロダクト | .env | リポジトリに.envが存在する可能性 | .gitignore確認、.env.example用意 |
| 46 | Minor | プロダクト | scripts/ | デモPDF作成スクリプト3バージョン重複 | 最新版のみ残す |
| 47 | Minor | プロダクト | api/main.py:845-946 | _process_single_pdfとclassify_pdfが重複 | batch機能自体がMVP不要。残すなら共通化 |

---

## 推奨アクションプラン

### Phase 0: 即時対応（Critical — 1-2日）

1. **API認証の導入**: APIキー認証（X-API-Key）を最低限実装。Cloud Run IAMも有効化
2. **policy_pathバリデーション**: ファイル名のみ受付、`..` / `/`を含むパスは400エラー
3. **ファイルアップロードバリデーション**: MIMEタイプ（application/pdf）、マジックバイト（%PDF）、サイズ上限（50MB）を追加
4. **data/results/の整理**: .gitignoreに追加、機密データ含むファイルをgit履歴から除去

### Phase 1: 高優先度修正（Critical + 重要Major — 1週間）

5. **app.py削除、app_minimal.pyに一本化**: UIの二重実装を解消
6. **PDF永続保存の修正**: 保持期間（24時間）定義、自動削除バッチ導入
7. **LLMデータ送信の情報開示**: UIに「Google Gemini APIにデータが送信されます」の説明とオプトイン同意を追加
8. **プロンプトインジェクション対策**: 入力デリミタ分離、長さ制限、制御文字サニタイズ
9. **デフォルトconfidence 0.8の修正**: `item.get("confidence", 0.8)` → `item.get("confidence", 0.0)` に3箇所変更
10. **GUIDANCE用語統一**: 全UIファイルで「確認が必要です」に統一

### Phase 2: UX改善 + MVP整理（Major — 2週間）

11. CORS設定、レート制限の導入
12. アクセシビリティ属性（aria-label等）の追加
13. Empty Stateの充実（対象PDF形式、サンプル導線）
14. MVP不要機能のfeature flag化（batch、類似検索、PDF分割）
15. 免責表示ルールの実装（全レスポンスにdisclaimerフィールド）
16. 監査ログの導入（Python logging、リクエストID付き）
17. 本番URLハードコードの除去（環境変数化）
18. 免責事項コントラスト比の改善

### Phase 3: 中長期改善（Minor + Zenn知見 — 1ヶ月以降）

19. 三層構造の採用（OCR→LLM→ルールベースバリデーション）
20. 抽出結果の視覚的検証UI（座標ベースハイライト）
21. Few-shot Learningの導入
22. 判定精度の定量評価基盤（テストデータセット整備）
23. Cloudflare Tunnel + Accessでのセキュアデプロイ検討
24. ユーザーフィードバックループ（判定結果の正誤回答）
25. LLM呼び出しのリポジトリパターン化
26. 成功/失敗指標の定義、最低限のアナリティクス導入
