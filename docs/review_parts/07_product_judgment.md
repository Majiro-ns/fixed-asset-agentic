# プロダクト判断力レビュー

**レビュー対象**: fixed-asset-ashigaru（固定資産判定ツール）
**レビュー日**: 2026-02-10
**レビュアー**: ashigaru7（シニアコンサルタント ペルソナ）
**照合チェックリスト**: MVPの切り方チェックリスト

---

## サマリ

1. **コア判定ロジック（core/）は堅実で、ハッカソンMVPとして適切なスコープに収まっている。** Stop設計（GUIDANCE）という独自の価値提案も明確。
2. **UIが2系統（app.py: 658行 / app_minimal.py: 755行）並存しており、これがMVP最大のスコープクリープ。** app.pyは削除し、app_minimal.pyに一本化すべき。
3. **batch_upload.py、embedding_store、similarity_search、ledger_import、pdf_splitter は全てMVP不要。** 「ついでにこれも」症候群の典型であり、即座に後回しにすべき。

---

## 機能一覧と MVP 評価

### コアロジック（core/）

| 機能 | MVPに必要か | 理由 |
|------|-------------|------|
| adapter.py（Opal→v1正規化） | **Must** | 入力の揺れを吸収する基盤。仮説検証に必須 |
| classifier.py（キーワードルール判定） | **Must** | コア価値そのもの。3値判定（CAPITAL/EXPENSE/GUIDANCE）がプロダクトの心臓 |
| policy.py（企業ポリシー読み込み） | **Must** | 企業ごとのカスタマイズ。差別化要素 |
| schema.py（スキーマ定数） | **Must** | 3行のファイル。過不足なし |
| pipeline.py（パイプライン統合） | **Must** | PDF→正規化→判定の一連フロー |
| pdf_extract.py（PDF抽出） | **Must** | PDF入力がコア機能 |
| pdf_splitter.py（PDF分割・高精度モード） | **Won't** | 複数書類の自動分割は高度な機能。MVP後で十分 |
| ledger_import.py（台帳インポート） | **Won't** | 過去データ学習はMVP後の機能 |

### API（api/）

| 機能 | MVPに必要か | 理由 |
|------|-------------|------|
| main.py: /classify | **Must** | JSON入力→判定のAPIエンドポイント |
| main.py: /classify_pdf | **Must** | PDF入力→判定のAPIエンドポイント |
| main.py: /classify_batch | **Won't** | 一括処理はMVP後。1件ずつで仮説検証は可能 |
| main.py: /healthz, /health | **Must** | Cloud Runヘルスチェック。インフラ要件 |
| gemini_classifier.py | **Should** | Gemini連携は精度向上のため有用だが、ルールベースで仮説検証は可能 |
| gemini_splitter.py | **Won't** | PDF分割のGemini連携。高度な機能 |
| embedding_store.py | **Won't** | 類似検索用エンベディング。MVP後 |
| similarity_search.py | **Won't** | 類似事例検索。MVP後 |
| history_search.py | **Won't** | 履歴ベース検索。MVP後 |
| vertex_search.py | **Should** | 法令引用は付加価値だが、仮説検証には不要 |
| useful_life_estimator.py | **Should** | 耐用年数推定は有用だが、MVP後で十分 |

### UI（ui/）

| 機能 | MVPに必要か | 理由 |
|------|-------------|------|
| app.py（Opal JSON + PDFフロー） | **Won't** | app_minimal.pyと重複。削除すべき |
| app_minimal.py（メインUI） | **Must** | 実際にユーザーが使うUI |
| batch_upload.py | **Won't** | 一括アップロードはMVP後 |
| similar_cases.py | **Won't** | 類似事例表示はMVP後 |
| components/（5ファイル） | **Must** | app_minimal.pyが依存するUIコンポーネント |
| styles.py | **Must** | CSS定義。app_minimal.pyが使用 |

### インフラ・設定

| 機能 | MVPに必要か | 理由 |
|------|-------------|------|
| Dockerfile | **Must** | Cloud Runデプロイ用 |
| Dockerfile.ui | **Should** | UI単体デプロイ。API統合なら不要 |
| requirements.txt | **Must** | ただし不要な依存は削除すべき |
| requirements-ui.txt | **Should** | Dockerfile.uiと連動。統合なら不要 |
| policies/company_default.json | **Must** | デモ用ポリシー。1ファイルで適切 |
| .github/workflows/ | **Should** | CI/CDはあって損なし、だがMVP検証に必須ではない |

### ドキュメント・スクリプト

| 機能 | MVPに必要か | 理由 |
|------|-------------|------|
| docs/（約40ファイル） | 過剰 | ドキュメント量がプロダクションレベル。ハッカソンには README + DEMO で十分 |
| scripts/（約15ファイル） | 過剰 | デモPDF作成スクリプトが3バージョン（v1/v2/v3）存在。1つで十分 |
| data/results/（約100ファイル） | **Won't** | 開発中の中間ファイルが大量残存。git管理すべきでない |
| data/golden/（10ケース） | **Must** | テスト用ゴールデンデータ。品質保証に必要 |

---

## 指摘事項

### Critical

#### C-1: UIの二重実装（app.py と app_minimal.py）

- **深刻度**: Critical
- **対象**: `ui/app.py`（658行）、`ui/app_minimal.py`（755行）
- **問題の説明**: 2つのStreamlitアプリが並存している。app.pyは3ステップのOpal JSON + PDFフロー。app_minimal.pyはPDF中心のシンプルUIで、コンポーネント分割済み。機能が大幅に重複しており、どちらが「本物」か不明確。保守コストが2倍になる。
- **修正提案**: app.pyを削除し、app_minimal.pyを`app.py`にリネームして一本化。app.pyにしかない機能（JSON直接入力、3ステップ表示）が必要なら、app_minimal.pyにタブとして統合する。

#### C-2: data/resultsに中間ファイルが大量残存

- **深刻度**: Critical
- **対象**: `data/results/`（100+ファイル）
- **問題の説明**: 開発中のテスト実行結果（extract/final JSON）がgitに含まれている可能性が高い。機密データ（見積書内容）が含まれるリスクもある。
- **修正提案**: `.gitignore`に`data/results/`を追加。既存ファイルはgit historyから除去（`git filter-branch`または`BFG Repo Cleaner`）。ローカル開発用は`data/results/.gitkeep`のみ残す。

### Major

#### M-1: batch_upload.pyはMVPに不要

- **深刻度**: Major
- **対象**: `ui/batch_upload.py`（296行）
- **問題の説明**: 複数PDFの一括アップロード・判定機能。MVPの「仮説検証」には1件ずつの判定で十分。開発工数に対するユーザー価値が低い。対応するAPIエンドポイント`/classify_batch`も同様。
- **修正提案**: MVP後のフェーズに移動。batch_upload.pyとAPI側の/classify_batchエンドポイントを一時的に無効化（コード削除ではなくfeature flag）。

#### M-2: 類似検索・履歴検索機能群はMVP不要

- **深刻度**: Major
- **対象**: `api/embedding_store.py`、`api/similarity_search.py`、`api/history_search.py`、`ui/similar_cases.py`、`core/ledger_import.py`
- **問題の説明**: エンベディングベースの類似事例検索、過去履歴からの検索、台帳インポートの3機能。いずれも「精度向上」のための機能であり、MVP段階では「ルールベース判定が使えるか」の仮説検証が優先。
- **修正提案**: 全て後回し。現在のtry/except importによるオプショナル化は良い設計。requirements.txtから関連依存を削除し、MVP版の軽量化を推奨。

#### M-3: PDF分割（高精度モード）はMVP不要

- **深刻度**: Major
- **対象**: `core/pdf_splitter.py`、`api/gemini_splitter.py`
- **問題の説明**: 複数書類が混在するPDFを自動検出・分割する高度な機能。Gemini Vision APIへの依存もある。MVPでは「1書類1PDF」の前提で十分。
- **修正提案**: 後回し。ユーザーに「1書類ずつアップロードしてください」と案内する方がMVP的に正しい。

#### M-4: ドキュメントの過剰

- **深刻度**: Major
- **対象**: `docs/`（約40ファイル）
- **問題の説明**: DEMO.md、DEMO_JP.md、VIDEO_SHOOTING_GUIDE_FINAL.md、VIDEO_FAQ_FOR_LORD.md、CLOUDRUN_TROUBLESHOOTING.md等、プロダクション運用レベルのドキュメント群。ハッカソンMVPの段階では過剰。ドキュメント作成にかけた時間をプロダクト改善に使うべきだった。
- **修正提案**: README.md + DEPLOY.md + docs/00_project.md の3ファイルに集約。残りはarchive/に退避。

#### M-5: スクリプトの重複

- **深刻度**: Major
- **対象**: `scripts/create_demo_pdfs.py`、`scripts/create_demo_pdfs_v2.py`、`scripts/create_demo_pdfs_v3.py`
- **問題の説明**: デモPDF作成スクリプトが3バージョン存在。v3のみが最新と推測されるが、v1/v2が残存。
- **修正提案**: 最新版のみ残して他を削除。

### Minor

#### m-1: requirements.txtにMVP不要な依存が含まれる

- **深刻度**: Minor
- **対象**: `requirements.txt`
- **問題の説明**: `google-genai`、`google-cloud-documentai`等がハードコードされている。MVP版ではこれらはオプショナルであるべき。ビルド時間とイメージサイズに影響。
- **修正提案**: `requirements-core.txt`（必須のみ）と`requirements-full.txt`に分離。

#### m-2: .envファイルがリポジトリに存在

- **深刻度**: Minor
- **対象**: `.env`
- **問題の説明**: 環境変数ファイルがリポジトリルートに存在。APIキー等の機密情報が含まれる可能性。
- **修正提案**: `.gitignore`に`.env`が含まれているか確認。含まれていなければ追加し、`.env.example`を用意。

#### m-3: app_minimal.pyのフォールバックUI（2カラムレイアウト）が冗長

- **深刻度**: Minor
- **対象**: `ui/app_minimal.py` 620行〜755行
- **問題の説明**: コンポーネントが読み込めない場合のフォールバックUIが約135行。コンポーネントが確実に存在する前提なら不要。
- **修正提案**: コンポーネントがMVPに含まれるなら、フォールバックを削除して100行以上のコードを削減。

#### m-4: _process_single_pdf関数がclassify_pdf関数とほぼ同一

- **深刻度**: Minor
- **対象**: `api/main.py` 845〜946行
- **問題の説明**: バッチ処理用の内部関数が、単体処理と大部分重複している。DRY原則違反。
- **修正提案**: batch機能自体がMVP不要だが、残すなら共通化すべき。

---

## MVPチェックリスト照合結果

### Phase 1: 仮説の明確化

| 項目 | 準拠/非準拠 | 備考 |
|------|-----------|------|
| 仮説を言語化した | **準拠** | 「Stop設計でAIの誤判定を防ぐ」が明確 |
| 解決したい課題が明確 | **準拠** | 「固定資産/費用の誤判定防止」が1文で説明可能 |
| 成功指標を定義した | **非準拠** | 数値目標が見当たらない（判定精度○%等） |
| 失敗基準を定義した | **非準拠** | Kill基準が未定義 |
| 検証期限を設定した | **非準拠** | 期限の記載なし（ハッカソンの締切が暗黙的にある可能性） |

### Phase 2: スコープの絞り込み

| 項目 | 準拠/非準拠 | 備考 |
|------|-----------|------|
| 全機能を書き出した | **準拠** | docs/に機能一覧あり |
| MoSCoWで分類した | **非準拠** | 分類の痕跡なし。Must以外が大量に実装済み |
| Must以外を外した | **非準拠** | batch、類似検索、PDF分割、台帳インポート等が残存 |
| Must機能が仮説検証に必要最小限 | **非準拠** | 上記の通り |

### Phase 3: 検証方法の選択

| 項目 | 準拠/非準拠 | 備考 |
|------|-----------|------|
| コードを書かずに検証できないか確認 | **不明** | Figmaプロトタイプ等の記録なし |
| 最もコストの低い方法を選択した | **非準拠** | 実コードMVPを選択（妥当な判断だが代替手段の検討記録なし） |

### Phase 4: MVP構築時のチェック

| 項目 | 準拠/非準拠 | 備考 |
|------|-----------|------|
| 実装範囲がMustのみ | **非準拠** | Should/Couldが大量に実装済み |
| 「ついでにこれも」がない | **非準拠** | batch_upload、類似検索、PDF分割が該当 |
| デザインの完成度にこだわりすぎていない | **準拠** | Streamlitベースで適切な割り切り |
| エッジケースの網羅的対応をしていない | **非準拠** | 税ルール（10/20/30/60万）の網羅的実装が早期すぎる可能性 |
| 管理画面を作っていない | **準拠** | dev=1パラメータの軽量な仕組み |
| リリースまでの工数が2-4週間以内 | **非準拠** | コード量・ドキュメント量から2-4週間を超過していると推定 |

### Phase 5: 計測と判断

| 項目 | 準拠/非準拠 | 備考 |
|------|-----------|------|
| 計測の仕組みを実装した | **非準拠** | アナリティクス未実装。UIの履歴機能はブラウザ内のみ |
| Actionable Metricsを使っている | **非準拠** | 計測自体が未実装 |

### アンチパターン該当

| アンチパターン | 該当 | 備考 |
|----------------|------|------|
| 「まず全機能作ってから出す」 | **該当** | batch、類似検索等がMVP段階で実装済み |
| 「技術的に面白いから」 | **やや該当** | Gemini連携、Vertex AI Search、エンベディング等 |
| 「あとで削るのは大変」 | **該当の兆候** | UI二重実装が残存している |

---

## 推奨するスコープ調整

### 即座に削除（Won't → 削除またはアーカイブ）

| 対象 | アクション | 理由 |
|------|-----------|------|
| `ui/app.py` | 削除 | app_minimal.pyと重複 |
| `ui/batch_upload.py` | 無効化（feature flag） | MVP不要 |
| `api/main.py` の `/classify_batch` | 無効化 | batch_upload.pyと連動 |
| `core/pdf_splitter.py` | 無効化 | MVP不要 |
| `api/gemini_splitter.py` | 無効化 | MVP不要 |
| `api/embedding_store.py` | 無効化（現状try/exceptで可） | MVP不要 |
| `api/similarity_search.py` | 無効化 | MVP不要 |
| `api/history_search.py` | 無効化 | MVP不要 |
| `core/ledger_import.py` | 無効化 | MVP不要 |
| `ui/similar_cases.py` | 無効化 | MVP不要 |
| `data/results/*` | .gitignore追加、git履歴からも除去 | 中間ファイル |
| `scripts/create_demo_pdfs.py`、`_v2.py` | 削除（v3のみ残す） | 重複 |
| `docs/` の大半 | archive/ に退避 | 過剰 |

### 後回し（Should → Phase 2以降）

| 対象 | 理由 |
|------|------|
| Gemini連携（gemini_classifier.py） | ルールベースで仮説検証してから精度向上を検討 |
| Vertex AI Search（vertex_search.py） | 法令引用は付加価値。判定精度の検証が先 |
| 耐用年数推定（useful_life_estimator.py） | CAPITAL_LIKE判定が正しいかの検証が先 |
| CI/CD（.github/workflows/） | 手動デプロイで十分 |
| Dockerfile.ui + requirements-ui.txt | API/UI統合デプロイで十分 |

### 追加すべき（Must → 未実装）

| 対象 | 理由 |
|------|------|
| 成功/失敗指標の定義 | MVPチェックリストPhase 1 未達 |
| 最低限のアナリティクス | 判定回数、GUIDANCE率、離脱率の計測 |
| ユーザーフィードバック機能 | 「この判定は正しかったですか？」の1クリック回答 |

### 「判定の正確さ」vs「UXの良さ」vs「開発速度」のバランス評価

| 軸 | 現状の評価 | コメント |
|----|-----------|---------|
| 判定の正確さ | **過剰投資** | Gemini + ルールベース + Vertex AI Search + 類似検索の4層。ルールベース1層で十分 |
| UXの良さ | **適切** | Streamlitベースで割り切っている。Stop設計の思想がUIに反映されている |
| 開発速度 | **遅延** | スコープ拡大により本来の2-3倍の工数を投下している印象 |

**推奨バランス**: 判定の正確さへの投資を減らし、開発速度を優先。ルールベース判定で仮説を検証し、精度不足が検証されてからGemini等を導入する順序が正しい。
