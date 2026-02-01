# AIエージェント 実装指示プロンプト（究極版）

> **用途**: このプロンプトをAIエージェントに渡し、REVIEW_COMPLETE に基づくコード・ドキュメント修正を実行させる  
> **参照**: [REVIEW_COMPLETE.md](./REVIEW_COMPLETE.md)

---

## トリガー

ユーザーが以下を入力したら、本プロンプトに従って実行する:

```
REVIEW_IMPLEMENT: fixed-asset-ashigaru
```

または

```
docs/review/REVIEW_COMPLETE.md に基づき、AIが実装可能な項目を実行せよ
```

---

## 前提

| 項目 | 内容 |
|------|------|
| **プロジェクトルート** | `C:\Users\owner\Desktop\fixed-asset-ashigaru` |
| **実施者** | AIエージェント（コード・ドキュメント編集のみ） |
| **実施しない** | commit/push、Cloud Runデプロイ、Zenn、デモ動画、参加登録、Git操作 |
| **参照ドキュメント** | `docs/review/REVIEW_COMPLETE.md` |

**実行前**: 本プロンプト内の「開発ドキュメント」「ベストプラクティス」を必ず参照し、全タスクで厳守すること。

---

## 禁止事項（ハード制約）

- `90_Outputs/` への書き込み禁止
- 既存ノート・ファイルの**移動・削除・リネーム**禁止
- git commit / git push 禁止
- gcloud / Cloud Run デプロイ禁止
- 人間実施項目（Zenn、デモ動画、参加登録）への着手禁止

---

## AI実装対象タスク（優先順・具体指示）

### タスク1: pipeline.py DEBUG print 削除

| 項目 | 内容 |
|------|------|
| ファイル | `core/pipeline.py` |
| 行 | 1行目 |
| 削除する文字列 | `print("[DEBUG] pipeline.py loaded")` |
| 残す | 直後の改行を維持し、`import datetime` から始まる2行目以降はそのまま |

**操作**: 1行目を削除する。2行目が先頭になる。

---

### タスク2: final_procedure.md normalizer → adapter 修正

| 項目 | 内容 |
|------|------|
| ファイル | `docs/final_procedure.md` |
| 検索 | `core/normalizer.py` |
| 置換 | `core/adapter.py` |
| 該当箇所 | 表「`core/normalizer.py` \| 正規化ルールの一貫性」の行 |

**操作**: `core/normalizer.py` を `core/adapter.py` に置換（該当する全ての出現）

---

### タスク3: README clone URL 修正

| 項目 | 内容 |
|------|------|
| ファイル | `README.md` |
| 検索 | `git clone https://github.com/your-org/fixed-asset-agentic-repo.git` |
| 置換 | `git clone https://github.com/Majiro-ns/fixed-asset-agentic.git` |
| 検索2 | `cd fixed-asset-agentic-repo` |
| 置換2 | `cd fixed-asset-agentic` |

---

### タスク4: COMPLIANCE_CHECKLIST リポジトリ名修正

| 項目 | 内容 |
|------|------|
| ファイル | `docs/COMPLIANCE_CHECKLIST.md` |
| 検索 | `fixed-asset-agentic-repo` |
| 置換 | `fixed-asset-agentic` |

---

### タスク5: submission_checklist LICENSE 状態更新

| 項目 | 内容 |
|------|------|
| ファイル | `docs/submission_checklist.md` |
| 該当行 | `|| LICENSEファイル | ❌ 未作成 | ルートにLICENSEファイルが存在しない |` |
| 置換後 | `|| LICENSEファイル | ✅ 完了 | MIT License 存在 |` |

※該当する表の行を置換。

---

### タスク6: deploy_status.md streamlit 記載修正

| 項目 | 内容 |
|------|------|
| ファイル | `docs/deploy_status.md` |
| 該当 | `### 主要依存関係` 直下の `- streamlit` の行 |
| 操作 | `- streamlit` を `- streamlit（requirements.txt に含む。API本体は未使用）` に変更するか、該当行を削除 |

---

### タスク7: IMPLEMENTATION_STATUS_REPORT DocAI 記載修正（任意）

| 項目 | 内容 |
|------|------|
| ファイル | `docs/IMPLEMENTATION_STATUS_REPORT.md` |
| 操作 | `_try_docai` が「placeholder」「未実装」と記載されている箇所を「実装済み」に修正 |
| 注意 | 該当箇所を検索して文脈に合わせて修正。見つからない場合はスキップ可 |

---

### タスク8: IMPLEMENTATION_AUDIT_REPORT DocAI 記載修正（任意）

| 項目 | 内容 |
|------|------|
| ファイル | `docs/IMPLEMENTATION_AUDIT_REPORT.md` |
| 操作 | DocAI が「Placeholder」と記載されている箇所を「実装済み」に修正 |
| 注意 | 該当箇所を検索して文脈に合わせて修正。見つからない場合はスキップ可 |

---

### タスク9: integration_test_report useful_life 記載修正（任意）

| 項目 | 内容 |
|------|------|
| ファイル | `docs/integration_test_report.md` |
| 背景 | useful_life_estimator.py は**存在する**が、同レポートは「存在しない」と記載 |
| 操作 | `useful_life_estimator.py` が「存在しない」「見つからない」とある箇所を「存在する。main.py から未統合」等に修正 |
| 注意 | 複数箇所ある場合は文脈に合わせて修正。スキップ可 |

---

## 実行順序

1. タスク1（pipeline.py）
2. タスク2（final_procedure.md）
3. タスク3（README.md）
4. タスク4（COMPLIANCE_CHECKLIST.md）
5. タスク5（submission_checklist.md）
6. タスク6（deploy_status.md）
7. タスク7〜9（任意）

---

## 検証

全タスク完了後、以下を実行して結果を報告する:

```powershell
cd C:\Users\owner\Desktop\fixed-asset-ashigaru
python -m pytest -v
```

**期待**: 14 passed

```powershell
python scripts/eval_golden.py
```

**期待**: 10/10 PASS, 100.0%

---

## レポート出力

実施後に以下の形式で報告する:

```
# 実装レポート (REVIEW_IMPLEMENT)

## 実施タスク
- タスク1: pipeline.py DEBUG print 削除 — done
- タスク2: final_procedure.md normalizer→adapter — done
- ...

## 検証結果
- pytest: 14/14 PASS
- Golden Set: 10/10 (100%)

## スキップ（人間実施）
- commit & push
- Cloud Run再デプロイ
- Zenn、デモ動画、参加登録
```

---

## 人間実施項目（AIは着手しない）

| 項目 | 理由 |
|------|------|
| commit & push | Git操作。人間が確認後に実行 |
| Cloud Run再デプロイ | gcloud 認証・ネットワーク必要 |
| GitHub公開確認 | ブラウザ操作 |
| Zenn記事 | 外部サービス |
| デモ動画 | 撮影・編集 |
| 参加登録 | フォーム入力 |
| プロジェクト提出 | 手続き |

---

---

# 開発ドキュメント（AI必須参照）

## ディレクトリ構造

| パス | 役割 |
|------|------|
| `core/` | adapter（Opal正規化）、classifier（3値判定）、policy、schema、pipeline |
| `api/` | FastAPI。main.py、gemini_classifier、vertex_search、useful_life_estimator |
| `ui/` | Streamlit デモ。app_minimal.py（本番デモ）、app.py（ローカルOpal連携） |
| `policies/` | company_default.json。ポリシー未指定時は空デフォルト |
| `scripts/` | run_adapter.py、run_pipeline.py、run_pdf.py、eval_golden.py、dev_run_checks.ps1 |
| `data/` | demo/、golden/。opal_outputs は設計上あるが実フォルダ不在 |
| `docs/specs/` | 2026-FA-01〜04。SPEC が単一の真実。書いていないことは実装しない |

## データフロー

1. Opal JSON → `adapt_opal_to_v1`（adapter）→ 正規化スキーマ v1.0
2. `load_policy`（policy）→ 欠損/不正時は安全な空デフォルト
3. `classify_document`（classifier）→ CAPITAL_LIKE/EXPENSE_LIKE/GUIDANCE、flags、rationale
4. pipeline が adapter + classifier をオーケストレーション

## 境界と責任

| コンポーネント | 責務 | 禁止 |
|----------------|------|------|
| Adapter | フィールド整形のみ。ビジネスルールなし | 判定ロジックの追加 |
| Classifier | Stop-first。曖昧→GUIDANCE。ポリシーは追加のみ | 安全性の緩和 |
| Policy | パイプラインを落とさない。不正時は空デフォルト | 失敗で停止 |
| UI | 可視化のみ。コアロジックは変更しない | ロジック改変 |

## 品質ゲート（必須）

- **ローカル**: `python -m pytest` を実行。14/14 PASS が必須
- **Golden Set**: `python scripts/eval_golden.py`。10/10 PASS が必須
- **CI**: `.github/workflows/ci.yml` が同じゲートを実行
- **dev_run_checks.ps1**: pip install + pytest。PR 前に必ず通過させる

## コマンド一覧

| 用途 | コマンド |
|------|----------|
| テスト | `python -m pytest -v` |
| Golden Set | `python scripts/eval_golden.py` |
| Adapter のみ | `python scripts/run_adapter.py --in data/.../xxx.json --out data/results/xxx_norm.json` |
| フルパイプライン | `python scripts/run_pipeline.py --in data/.../xxx.json --out data/results/xxx_final.json` |
| PDF | `python scripts/run_pdf.py --pdf tests/fixtures/sample_text.pdf --out data/results` |
| UI | `streamlit run ui/app_minimal.py`（デモ用） |

---

# ベストプラクティス（AI厳守）

## 原則

1. **SPEC が単一の真実** — 書いていないことは実装しない
2. **迷ったら止まる** — 曖昧・矛盾・不足時は推測せず質問
3. **沈黙 ≠ 承認** — 承認不明なら実装しない

## コード品質

| ルール | 内容 |
|--------|------|
| 最小編集 | 必要な変更のみ。スコープ拡大禁止 |
| テスト優先 | 挙動変更よりテスト追加を優先 |
| 説明的 | 賢さより説明可能性を優先 |
| 差分小さく | レビューしやすいサイズに抑える |

## 禁止事項（絶対）

| 項目 | 理由 |
|------|------|
| 税務・会計ロジックの無承認変更 | 人間の判断が必要 |
| evidence / rationale の削減 | 証跡を残す設計原則 |
| 例外の握りつぶし | 文脈付きでバブルアップ |
| 有料・外部API追加 | 依存をローカルに保つ |
| 認証情報の作成・コミット | 既存環境変数のみ使用 |
| main への直接 push | 常に PR 経由 |
| メジャーバージョン bump | 提案のみ。承認後に実施 |

## 許容されるデフォルト

- 曖昧（混合キーワード、シグナル不足）→ GUIDANCE + flags
- ポリシーファイル欠損/不正 → 空デフォルトで継続
- 入力不正 → 安全なデフォルト + 可視フラグ

## 変更時のチェック

- [ ] pytest 14/14 PASS
- [ ] eval_golden 10/10 PASS
- [ ] evidence / rationale が維持または拡張されているか
- [ ] 新機能は SPEC に記載されているか

## SPEC 一覧

| ファイル | 内容 |
|----------|------|
| 2026-FA-01 | PDF抽出スキーマ |
| 2026-FA-02 | ルール事前分類 |
| 2026-FA-03 | AI勘定科目候補（未実装） |
| 2026-FA-04 | 耐用年数候補 |
| 2026-FA-PDF-ingest-warning | PDF取り込み警告 |

※新機能実装時は該当 SPEC を参照。SPEC に無い機能は実装しない。

---

## 参照

- [REVIEW_COMPLETE.md](./REVIEW_COMPLETE.md) — 全レビュー内容
- [../UNIMPLEMENTED_ISSUES.md](../UNIMPLEMENTED_ISSUES.md) — 未実装課題一覧
- [../INDEX.md](../INDEX.md) — 自動開発ルール
- [../docs/00_project.md](../00_project.md) — 目的・スコープ
- [../docs/01_commands.md](../01_commands.md) — コマンド単一真実
- [../docs/02_arch.md](../02_arch.md) — アーキテクチャ
- [../docs/03_rules.md](../03_rules.md) — ドメイン安全ルール
- [../docs/specs/](../specs/) — SPEC ファイル群
