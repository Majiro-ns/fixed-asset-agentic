# Fix Log: プライバシー修正 C-05〜C-07 + confidence バグ修正

**Task ID**: subtask_067_05
**担当**: ashigaru5
**日時**: 2026-02-10T10:12:00

## 修正5: PDF保持期間ポリシー（C-05）

- **ファイル**: `core/pipeline.py`
- **変更内容**:
  - `cleanup_old_files(directory, max_age_hours=24)` 関数を追加
  - `_cleanup_data_directories()` 関数を追加（uploads + results の一括クリーンアップ）
  - モジュールロード時（アプリ起動時）に自動実行
  - `data/uploads/` 配下の24時間以上経過したファイルを削除
- **追加import**: `os`, `time`

## 修正6: 抽出結果JSON保持期間（C-06）

- **ファイル**: `core/pipeline.py`
- **変更内容**:
  - `data/results/` にも同様の24時間クリーンアップを適用
  - `cleanup_old_files` を再利用（`_cleanup_data_directories` 内で呼び出し）

## 修正7: LLMデータ送信の情報開示（C-07）

- **ファイル**: `ui/app_minimal.py`
- **変更内容**:
  - コンポーネントベースレイアウト: `render_input_area()` の直前に `st.info()` を追加
  - フォールバックレイアウト: `file_uploader` の直前に `st.info()` を追加
  - 表示テキスト: 「アップロードされたPDFの内容は、判定のためにGoogle Gemini APIに送信されます。機密性の高い書類の場合はご注意ください。」

## 修正8: confidence デフォルト値修正

- **ファイル**: `api/main.py`
- **変更箇所**: 3箇所（Editツールで個別修正、RACE-001準拠）
  1. `item_confidence = item.get("confidence", 0.8)` → `item.get("confidence", 0.0)`
  2. `item.get("confidence", 0.8) for item in line_items` → `item.get("confidence", 0.0)`
  3. `confidences = [e.get("confidence", 0.8) for e in evidence]` → `[e.get("confidence", 0.0)]`
- **理由**: デフォルト値が0.8だと、classifierが confidence を返さなかった場合に誤った高確信度として扱われる

## 品質確認

- [x] `python3 -m py_compile core/pipeline.py` — OK
- [x] `python3 -m py_compile api/main.py` — OK
- [x] `python3 -m py_compile ui/app_minimal.py` — OK
- [x] api/main.py は Edit ツールのみ使用（Write 禁止、RACE-001 準拠）
- [x] 自分の担当範囲のみ修正（認証・CORS・UX改善等には未touch）
