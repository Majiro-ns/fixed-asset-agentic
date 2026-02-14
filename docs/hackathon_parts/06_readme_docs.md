# README/ドキュメント改善分析

> **分析者**: ashigaru6
> **分析日時**: 2026-02-10
> **対象**: fixed-asset-ashigaru プロジェクト
> **タスクID**: subtask_068_06 / cmd_068

---

## 現状の構成

### リポジトリルートの文書ファイル

| ファイル | 存在 | 行数 | 備考 |
|---------|------|------|------|
| README.md | ✅ | 507行 | 非常に詳細。技術スタック・API仕様・デプロイ手順完備 |
| LICENSE | ✅ | MIT | Copyright 2026 Majiro-ns |
| requirements.txt | ✅ | 26行 | google-genai>=1.51.0, streamlit, fastapi等 |
| requirements-ui.txt | ✅ | — | UI専用依存関係 |
| CONTRIBUTING.md | ❌ | — | 不在。README内にインライン記載あり（470-483行） |
| .env.example | ❌ | — | 不在。環境変数の一覧が散在（CLOUDRUN_ENV.md等） |
| DEMO.md | ✅ | — | デモ手順（README.mdからリンク） |
| INDEX.md | ✅ | — | 自動開発ルール |

### docs/ 配下の文書一覧と評価

**合計: 77ファイル以上**（md, txt, html, mmd含む）

#### カテゴリ別分類

| カテゴリ | ファイル数 | 代表的ファイル | 外部公開適性 |
|---------|-----------|---------------|-------------|
| **コア設計文書** | 4 | 00_project.md, 01_commands.md, 02_arch.md, 03_rules.md | △ 内部向け |
| **仕様書 (specs/)** | 5 | 2026-FA-01〜04, PDF-ingest-warning | △ 技術者向け |
| **ハッカソン用** | 7 | judge_value_proposition, submission_checklist, COMPLIANCE_CHECKLIST, SCHEDULE, demo_script, DEMO_RUNBOOK, VIDEO_SHOOTING_GUIDE_FINAL | ✅ 審査対応 |
| **デプロイ・運用** | 6 | CLOUDRUN_ENV, CLOUDRUN_TROUBLESHOOTING, DOCKER_LOCAL_SMOKE, DOCKER_STARTUP_REPORT, deploy_status, DEMO_FALLBACK_DOCKER | ✅ 再現性担保 |
| **レビュー分析 (review_parts/)** | 8 | 01_ui_cognitive〜08_known_bugs | △ 内部品質管理 |
| **修正ログ (fix_log_parts/)** | 5 | fix_04_security〜fix_08_security_enhance | ✗ 完全内部向け |
| **リサーチ** | 10 | research_a〜ij, side_business_research | ✗ 完全内部向け |
| **Zenn記事** | 1 | zenn_article_draft.md | ✅ 提出物の核 |
| **図・スライド** | 5 | architecture_diagram.md, slides/*.html, slides/*.mmd | ✅ プレゼン用 |
| **その他** | 20+ | LORD_INSTRUCTIONS, QUESTIONS_FOR_LORD, CHECKPOINT_SEKIGAHARA等 | ✗ 内部管理用 |

#### docs/ の問題点

1. **外部向け/内部向けが混在**: 審査員がdocs/を見た場合、research_a〜ijやLORD_INSTRUCTIONSなど内部文書が見えてしまう
2. **命名規則が不統一**: 英語大文字(CLOUDRUN_ENV)、英語小文字(research_a)、日本語(LORD_INSTRUCTIONSハッカソン残タスク)が混在
3. **INDEX/目次がない**: docs/の全体像を示すREADME.mdやINDEX.mdがdocs/内にない
4. **images/ ディレクトリが不在**: architecture_diagram.md で推奨されている docs/images/ が存在しない（スクリーンショット・図の画像ファイルなし）

---

## README.md分析（セクション別評価）

### 審査員が3分で理解できるか → **概ねYes、ただし冗長**

| セクション | 行 | 評価 | コメント |
|-----------|-----|------|---------|
| バッジ群 | 1-9 | ✅ 優秀 | Python, Gemini, FastAPI, Streamlit, Google Cloud, License, Golden Set。視覚的に技術スタックを即把握可能 |
| Stop-first概要（30秒） | 11-34 | ✅ 優秀 | ASCII図で3値判定フローを一目で理解。キャッチコピーも明快 |
| 審査員向け3点セット | 38-48 | ✅ 優秀 | Agentic / Google Cloud AI / Reproの3軸を表形式で簡潔に提示 |
| 技術的ハイライト | 51-127 | ⚠️ やや冗長 | 5つのハイライトは良いが、コードスニペット含め80行近く。審査員が全読するか疑問 |
| 概要 | 130-138 | ✅ 良好 | 課題認識→設計思想を簡潔に記述 |
| 導入効果 | 142-150 | ✅ 良好 | 定量的数値が説得力あり |
| 3値判定 | 154-163 | ✅ 良好 | 表形式で明快 |
| デモ | 166-194 | ✅ 良好 | クイック起動＋デモシナリオ＋デモデータ注記 |
| クイックスタート | 197-233 | ⚠️ 4ステップ | git clone → pip install ×2 → uvicorn + streamlit。**3ステップ以内でない**（pip install が2回、サーバー起動が2コマンド） |
| アーキテクチャ図 | 237-304 | ✅ 良好 | Mermaid図あり。ただし **「Opal OCR」「Opal JSON」** が残存（C-10の修正範囲外だったため） |
| API仕様 | 308-366 | ⚠️ 冗長 | curl例＋レスポンスJSON全量。審査員向けには情報過多 |
| Cloud Runデプロイ | 369-405 | ✅ 良好 | 実URLあり。手順も明確 |
| 評価（Golden Set） | 409-424 | ✅ 良好 | 100% Accuracyの表記はインパクトあり |
| 技術スタック | 426-459 | ✅ 優秀 | コア＋Google Cloud AI＋依存ライブラリ＋ライセンスを表形式で整理 |
| ライセンス | 462-467 | ✅ OK | MITへのリンクあり |
| コントリビューション | 470-483 | ✅ OK | 5ステップの手順。ただしCONTRIBUTING.mdは別途不在 |
| 関連ドキュメント | 486-497 | ✅ 良好 | 主要ドキュメントへのリンク表 |

### README.md 総合スコア

| 観点 | スコア | 理由 |
|------|--------|------|
| 冒頭の目的明確度 | 9/10 | 「Stop-first Agentic AI」のキャッチが優秀 |
| 技術スタック一覧 | 10/10 | バッジ＋表形式で完璧 |
| アーキテクチャ図 | 8/10 | Mermaid図あり。ただし「Opal」用語残存 |
| セットアップ容易性 | 6/10 | 4ステップ必要。Makefileやdocker-compose未提供 |
| 環境変数説明 | 4/10 | .env.example不在。散在する環境変数が把握困難 |
| スクリーンショット/GIF | 1/10 | **完全に不在**。UIの見た目がREADMEからは全く分からない |
| 全体の長さ | 6/10 | 507行は長め。審査員が全読する可能性は低い |

---

## Zenn記事の準備状況 【⚠️ 最重要：公式提出必須物】

### 下書きファイル: `docs/zenn_article_draft.md`（354行）

| 項目 | 状態 | 詳細 |
|------|------|------|
| frontmatter | ✅ 完了 | type: "idea", topics: ["gch4", ...], published: true |
| カテゴリ「Idea」 | ✅ 設定済 | `type: "idea"` |
| トピック「gch4」 | ✅ 設定済 | `topics: ["gch4", "googlecloud", "agenticai", "fastapi", "経理DX"]` |
| プロジェクト概要 | ✅ 充実 | 対象ユーザー・課題・特徴が明確。ストーリー性も高い |
| システムアーキテクチャ図 | ✅ Mermaid | 167-186行。ただし画像としてのエクスポートは未実施 |
| YouTube デモ動画 | 🚨 **未完了** | 27行に `<!-- TODO: 殿がYouTube/Vimeoにアップロード後、以下を置き換える -->` |
| スクリーンショット | 🚨 **未完了** | 4箇所にTODO（92, 113, 135, 145行目）。UIスクショが一切ない |
| 税務知識セクション | ✅ 充実 | 取得価額の範囲、金額閾値、資本的支出vs修繕費 |
| Before/After比較 | ✅ 良好 | テキストベースの対比が効果的 |
| 実務機能の補足 | ✅ 良好 | :::details で折りたたみ記載 |
| 制限事項・今後の課題 | ✅ 良好 | 誠実な記載 |

### 🚨 Zenn記事のブロッカー

1. **デモ動画が未撮影・未アップロード**（公式要件: YouTube上のデモ動画3分程度を埋め込み）
2. **スクリーンショット4箇所が全てTODO**（GUIDANCE画面、停止表示、2択ボタン、Before/After差分）
3. **Zennへの実際の投稿/公開が未実施**（ローカル下書きのみ）

→ スケジュール上は Phase 3（2/8-10）が Zenn記事作成期間。**本日（2/10）がバッファ日**。動画撮影は Phase 2（2/3-7）の予定だったが、完了状況不明。

---

## 改善提案（優先度順）

### 🔴 P0: ハッカソン提出ブロッカー（あと5日以内に必須）

| # | 項目 | 内容 | 担当候補 |
|---|------|------|---------|
| 1 | **デモ動画撮影・YouTube公開** | Zenn記事必須要件。3分程度のデモ動画を撮影し、YouTubeにアップロード | 殿 |
| 2 | **UIスクリーンショット4枚撮影** | GUIDANCE画面、停止表示、2択質問、Before/After差分。Zenn記事のTODO解消用 | 殿 |
| 3 | **Zenn記事のTODO解消・公開** | 動画URL埋め込み、スクショ挿入、Zennに実際に投稿して公開 | 殿 |
| 4 | **参加登録** | lu.maでの登録。締切: 2/13 | 殿 |

### 🟡 P1: README品質向上（提出前に対応推奨）

| # | 項目 | 内容 | 工数目安 |
|---|------|------|---------|
| 5 | **スクリーンショット追加** | README冒頭付近にUIのスクリーンショットまたはGIFを1-2枚追加。審査員の第一印象に直結 | 30分 |
| 6 | **README内Opal用語の修正** | Mermaid図(243行)に `Opal OCR`、`Opal JSON` が残存。C-10で app_classic.py は修正済みだがREADMEは未対応 | 15分 |
| 7 | **.env.example 作成** | `GOOGLE_API_KEY`, `PDF_CLASSIFY_ENABLED`, `USE_DOCAI`, `VERTEX_SEARCH_ENABLED`, `GEMINI_PDF_ENABLED`, `PORT` 等をまとめた .env.example を作成 | 15分 |
| 8 | **セットアップ手順の簡素化** | docker-compose.yaml 作成 or Makefile追加で `make run` 一発起動を実現。現状4ステップ→1-2ステップに | 30分 |
| 9 | **README長さの最適化** | API仕様の詳細（curl例・レスポンスJSON全量）を別ファイル（docs/API.md）に分離。README本体を300行以下に圧縮 | 30分 |

### 🟢 P2: ドキュメント整理（提出後でも可）

| # | 項目 | 内容 |
|---|------|------|
| 10 | **docs/ にINDEX.md追加** | docs/配下の77ファイルを「外部向け」「内部開発用」に分類する目次を作成 |
| 11 | **内部文書の隔離** | research_*, fix_log_parts/, LORD_INSTRUCTIONS* 等を docs/internal/ に移動 |
| 12 | **CONTRIBUTING.md 作成** | README内のインライン記載を独立ファイルに分離 |
| 13 | **architecture_diagram.md → 実画像化** | docs/images/ にPNG/SVGとしてエクスポート。Zenn記事にも利用可能 |
| 14 | **00_project.md の用語更新** | 「Opal OCR/output」「adapter + classifier」等の旧用語が残存 |
| 15 | **Google Gemini API利用規約への言及** | READMEまたはCOMPLIANCE_CHECKLISTにGenAI API利用規約（Generative AI Prohibited Use Policy）への準拠を明記 |

---

## README改善案（構成のみ）

```
# 見積書 固定資産判定 (Fixed Asset Classifier)

[バッジ群: 現状のまま維持]

> **Stop-first Agentic AI** — キャッチコピー

🖼️ [スクリーンショット or デモGIF]  ← 【新規追加】

## 30秒でわかる Stop-first AI
[現状のASCII図: そのまま]

## 審査員向け 技術3点セット
[現状の表: そのまま]

## デモ
[クイック起動 + デモシナリオ。現状を維持]

## クイックスタート
### ローカル起動（3ステップ）   ← 【簡素化】
  1. git clone && cd
  2. pip install -r requirements.txt
  3. docker-compose up  ← 【新規】またはMakefile
### Docker起動
[現状のまま]

## アーキテクチャ
[Mermaid図: Opal→「OCR抽出」に修正]  ← 【用語修正】
[UI構成・ディレクトリ構成: 現状のまま]

## 導入効果
[現状の表: そのまま]

## 3値判定
[現状のまま]

## 技術的ハイライト（要約版）  ← 【圧縮】
[5つのハイライトを表形式で要約。コードスニペットは1つだけ残す]

## 評価（Golden Set）
[現状のまま]

## 技術スタック
[現状のまま]

## API仕様 → [詳細はdocs/API.md](docs/API.md)  ← 【分離】
[エンドポイント表のみREADMEに残す]

## Cloud Run デプロイ → [詳細はdocs/CLOUDRUN_ENV.md]  ← 【圧縮】
[サービス一覧表のみ]

## 環境変数
[.env.example へのリンク]  ← 【新規追加】

## ライセンス・クレジット
[現状 + Google Gemini API利用規約への言及]  ← 【追加】

## 関連ドキュメント
[現状の表: そのまま]

---
ハッカソンフッター
```

**想定行数**: 280-320行（現状507行 → 約40%圧縮）

---

## ライセンス・クレジット分析

| 項目 | 状態 | 詳細 |
|------|------|------|
| LICENSEファイル | ✅ | MIT License, Copyright 2026 Majiro-ns |
| OSSライブラリクレジット | ✅ | README.md「依存ライブラリ」セクションにライセンス種別まで記載 |
| PyMuPDF AGPL警告 | ✅ | README.md 459行に商用利用時の注意を明記 |
| Google Gemini API利用規約 | ⚠️ | **明示的な言及なし**。COMPLIANCE_CHECKLIST.mdにGoogle Cloud AI使用の項目はあるが、Generative AI Prohibited Use Policy / Terms of Service への直接リンクがない |
| CONTRIBUTING.md | ❌ | 独立ファイルとしては不在。README内に5ステップの手順あり |

---

## 付録: Zenn記事TODOの具体的位置

| 行 | TODO内容 | 必要な素材 |
|----|---------|-----------|
| 27 | `<!-- TODO: 殿がYouTube/Vimeoにアップロード後、以下を置き換える -->` | YouTube動画URL |
| 92 | `<!-- TODO: スクリーンショット: GUIDANCE画面（2択ボタン）-->` | GUIDANCE画面のスクショ |
| 113 | `<!-- TODO: スクリーンショット: 🛑 AIが判断を保留しました -->` | 停止表示のスクショ |
| 135 | `<!-- TODO: スクリーンショット: 2択ボタン + 2段階質問 -->` | 質問UIのスクショ |
| 145 | `<!-- TODO: スクリーンショット: Before/After差分表示 -->` | DIFF表示のスクショ |

**全5箇所のTODOが未解消。うち動画1箇所が公式提出必須要件に直結。**

---

*本分析は subtask_068_06 (cmd_068 ワークストリームB) として実施*
