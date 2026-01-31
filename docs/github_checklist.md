# GitHub リポジトリ公開チェックリスト

> **確認日**: 2026-01-30
> **対象リポジトリ**: https://github.com/Majiro-ns/fixed-asset-agentic

---

## チェック結果サマリ

| 項目 | 状態 | 備考 |
|------|------|------|
| リモートURL | OK | 公開可能 |
| 機密情報 | OK | ハードコードなし |
| .gitignore | OK | 適切に設定済み |
| LICENSE | **要対応** | ファイルが存在しない |

---

## 1. リモートURL確認

**結果**: OK

```
[remote "origin"]
    url = https://github.com/Majiro-ns/fixed-asset-agentic
```

- 公開GitHubリポジトリのURL
- 問題なし

---

## 2. 機密情報チェック

**結果**: OK（ハードコードされた機密情報なし）

### 検索対象キーワード
`API_KEY`, `SECRET`, `PASSWORD`, `TOKEN`, `CREDENTIAL`

### 検出ファイルと判定

| ファイル | 内容 | 判定 |
|----------|------|------|
| `api/vertex_search.py` | 説明文のみ（"credentials configured"） | OK |
| `tools/agent_run.py` | `os.environ.get('GITHUB_TOKEN')` 環境変数参照 | OK |
| `.github/workflows/agent.yml` | `${{ secrets.GITHUB_TOKEN }}` GitHub Secrets使用 | OK |
| `INDEX.md` | ルール説明文（"Never create secrets"） | OK |
| `docs/03_rules.md` | ルール説明文 | OK |

**結論**: 全て適切な方法（環境変数、GitHub Secrets）を使用。ハードコードされた認証情報なし。

---

## 3. .gitignore 確認

**結果**: OK

```gitignore
__pycache__/
*.py[cod]
*.pyo
*.pyd
*.DS_Store
.venv/
.env              # ← 環境変数ファイル除外
data/results/*.json
*.tmp
*.log
*_memo.txt
*_メモ.txt
脳みそ.txt
data/             # ← ランタイムデータ除外
!data/golden/     # ← ゴールデンセットは許可
!data/golden/**/*.json
!data/demo/       # ← デモデータは許可
!data/demo/**/*.json
openapi.json
```

### 確認ポイント

| 項目 | 状態 |
|------|------|
| `.env` 除外 | OK |
| `data/` 除外（golden/demo以外） | OK |
| キャッシュ・一時ファイル除外 | OK |
| ログファイル除外 | OK |

---

## 4. LICENSE ファイル確認

**結果**: 要対応（ファイルが存在しない）

### 現状
- `LICENSE` または `LICENSE.md` ファイルが存在しない
- README.md の「OSS/Licenses」セクションで依存ライブラリのライセンスは記載あり

### 推奨アクション

ハッカソン提出用として、以下のいずれかを選択：

| ライセンス | 特徴 | 推奨度 |
|-----------|------|--------|
| **MIT License** | 最も緩やか。商用利用・改変・再配布自由 | 推奨 |
| Apache License 2.0 | 特許条項あり。企業利用に適する | 可 |
| 独自ライセンス | ハッカソン審査用の限定公開として明示 | 可 |

### 注意事項
- **PyMuPDF (fitz)** は AGPL-3.0 ライセンス
- 本プロジェクトが PyMuPDF を使用する場合、ライセンス整合性に注意

---

## 5. 追加確認事項

### 未追跡ディレクトリ

| ディレクトリ/ファイル | 状態 | 対応 |
|----------------------|------|------|
| `.gcloud_config/` | 未追跡 | .gitignoreに追加推奨 |
| `api/vertex_search.py` | 未追跡 | コミット対象として問題なし |
| `docs/*.md` （新規作成分） | 未追跡 | コミット対象として問題なし |

### .gitignore 追加推奨項目

```gitignore
# GCP local config (should not be committed)
.gcloud_config/
```

---

## 推奨アクション一覧

| 優先度 | アクション | 担当 |
|--------|-----------|------|
| **高** | LICENSE ファイルを追加（MIT推奨） | 要判断 |
| 中 | `.gcloud_config/` を .gitignore に追加 | 足軽対応可 |
| 低 | 新規ドキュメントをコミット | 足軽対応可 |

---

## 結論

本リポジトリは**公開準備がほぼ完了**している。

唯一の必須対応事項は **LICENSE ファイルの追加** である。
殿の判断を仰ぎ、ライセンスを選択後、追加すべし。

---

*Checked by: Ashigaru-1*
*Last Updated: 2026-01-30*
