# 修正ログ: プロダクト整理 C-08〜C-11

実施日時: 2026-02-10T10:14:09
実施者: ashigaru6
親タスク: cmd_067 / subtask_067_06

---

## 修正9: app.py リネーム（C-08）

**対象**: `ui/app.py`
**内容**: `app.py` → `app_classic.py` にリネーム（mv）
**確認事項**:
- 他ファイルからの `app.py` import: **なし**（grep で確認済み）
- 旧 `app.py`: 削除済み（リネームのため自動削除）
- 新 `app_classic.py`: 存在確認済み

---

## 修正10: .gitignore に data/results/ 追加（C-09）

**対象**: `.gitignore`
**内容**:
- `data/results/` を追加（既存の `data/results/*.json` に加えてディレクトリ全体）
- `data/uploads/` を追加

**備考**: `data/` ルールで暗黙的にカバーされていたが、明示的に追加

---

## 修正11: 技術用語の平易化（C-10）

**対象**: `ui/app_classic.py`

| 変更前 | 変更後 | 該当箇所 |
|--------|--------|---------|
| Opal抽出 × Agentic判定 | 自動抽出 × 自動判定 | APP_TITLE |
| Opal項目抽出 / Agent判定処理（Stop設計） | 項目抽出 / 自動判定処理（確認ポイント） | APP_SUB |
| Opal抽出（揺れるJSON） | データ抽出（入力データの補正） | STEP1 |
| Adapter正規化（凍結スキーマ v1.0） | 変換処理（データ形式の固定 v1.0） | STEP2 |
| Classifier判定 | 自動判定 | STEP3 |
| Stop設計 | 確認ポイント | STOP_NOTE, コンテナ内説明 |
| Opal抽出JSON | 抽出データJSON | Step1見出し |
| OpalがOCR | 判定エンジンがOCR | Step1キャプション |
| デモ用のOpal JSON | デモ用の抽出JSON | selectbox help |
| Opal JSON を貼付 | 抽出JSON を貼付 | text_area ラベル |
| 正規化（Adapter結果） | 変換処理（正規化結果） | Step2見出し |
| Opal抽出を固定スキーマに正規化 | 抽出データを固定形式に正規化 | Step2キャプション |
| Adapter出力 | 変換処理の出力 | Step2 info |
| 判定（Agentic） | 自動判定 | Step3見出し |
| Stop設計（断定しない思想） | 確認ポイント（断定しない思想） | コンテナ見出し |
| 停止理由は flags に | 停止理由は注意事項に | コンテナ説明 |
| flags/evidence を見て | 注意事項/根拠を見て | 次にやること |
| Opal JSON（生データ） | 入力JSON（生データ） | expander |
| 止まる Agent | 止まる自動判定 | メインinfo |
| 📋 Opal JSON入力 | 📋 JSON入力 | タブラベル |
| 判断根拠（flags） | 判断根拠（注意事項） | VALUE_BULLETS |
| 責任境界の設計提案 | 責任境界の明確化 | VALUE_BULLETS |

**未変更（コード内部のため）**:
- `adapt_opal_to_v1`（関数名）
- `opal_dict`（変数名）
- `SAMPLE_DIR = ROOT_DIR / "data" / "opal_outputs"`（ディレクトリパス）

---

## 修正12: 結果テーブルのカラム名日本語化（C-11）

**対象**: `ui/app_classic.py`

### メイン結果テーブル（`_to_table_rows`）

| 変更前キー | 変更後キー |
|-----------|-----------|
| classification | 分類結果 |
| rationale_ja | 判定理由 |
| flags | 注意事項 |
| evidence | 根拠 |

### GUIDANCE詳細テーブル（`guidance_rows`）

| 変更前キー | 変更後キー |
|-----------|-----------|
| rationale_ja | 判定理由 |
| flags | 注意事項 |
| evidence.source_text | 根拠テキスト |

### 関連変更

| 箇所 | 変更 |
|------|------|
| `_render_dataframe` preferred リスト | 日本語キーに更新 |
| `_sort_rows_for_review` | `r.get("classification")` → `r.get("分類結果")` |
| `_to_table_rows` flags表示 | `flags: xxx` プレフィックス削除（カラム名で自明） |
| GUIDANCE詳細のラベル | `flags:` → `注意事項:` / `evidence.source_text:` → `根拠テキスト:` |

### result_card.py

**変更なし**: RACE-001に従い、カラム名に該当する表示要素がないため未修正。内部キー（`confidence`, `reasons` 等）とGUIDANCE用語（「たぶん大丈夫」等）は足軽7の管轄。

---

## 品質確認

- [x] `python3 -m py_compile ui/app_classic.py` → COMPILE_OK
- [x] 旧 `app.py` が残っていないことを確認
- [x] 新 `app_classic.py` の存在確認
- [x] `.gitignore` に `data/results/` と `data/uploads/` が追加されたことを確認
- [x] UI文字列に Opal/Adapter/Agentic/Stop設計/揺れるJSON/凍結スキーマ が残っていないことを grep で確認
