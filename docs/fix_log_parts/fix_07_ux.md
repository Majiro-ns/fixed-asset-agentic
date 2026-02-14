# 修正ログ: UX改善（ワークストリームC）

**担当**: 足軽7号
**タスクID**: subtask_067_07
**日時**: 2026-02-10

---

## 修正13: GUIDANCE用語の統一

**対象ファイル**:
- `ui/components/diff_display.py` (L15): `"⚠️ 要確認（自動判定不可）"` → `"⚠️ 確認が必要です"`
- `ui/app_minimal.py` (L289): `"確認が必要"` → `"確認が必要です"`（ヘルプ欄）
- `ui/app_minimal.py` (L728): `"要確認"` → `"確認が必要です"`（フォールバックUI判定変化ラベル）

**変更なし**:
- `ui/components/guidance_panel.py`: GUIDANCE用語（「要確認」「判断停止」等）のUI表示なし。ヘッダーは「AIが判断を保留しました」で別表現。
- `ui/components/hero_section.py`: GUIDANCE関連のUI表示なし。
- `ui/components/result_card.py`: GUIDANCEはearly return（対象外）。

## 修正14: diff_display.pyの日本語化

**対象**: `ui/components/diff_display.py`
- L87: `"Before:"` → `"変更前:"`
- L91: `"After:"` → `"変更後:"`

## 修正15: 免責事項コントラスト比改善

**対象**: `ui/styles.py`
- L124: `.disclaimer` の `color: #9CA3AF` → `color: #4B5563`（WCAG AA 4.5:1準拠）

## 修正16: 確信度表現の改善

**対象**: `ui/components/result_card.py`
- L48: `"たぶん大丈夫"` → `"概ね確実（念のため確認推奨）"`

**RACE-001遵守**: カラム名日本語化（足軽6担当）には触れず。確信度表現テキストのみ変更。

## 修正17: Empty Stateのガイダンス充実

**対象**: `ui/components/input_area.py`
- L414: `st.caption("👆 PDFをアップロードして判定を実行")` → 3行ガイダンスに拡充:
  - 「請求書・見積書・領収書のPDFをアップロードしてください。」
  - 「対応形式: PDF（テキスト埋め込み型推奨）」
  - 「サンプルで試す場合は下の「デモで試す」ボタンをどうぞ。」

---

## 品質確認

全修正ファイル（5件）に `python3 -m py_compile` を実行し、全件パス。

| ファイル | py_compile |
|---|---|
| ui/styles.py | OK |
| ui/components/diff_display.py | OK |
| ui/components/result_card.py | OK |
| ui/components/input_area.py | OK |
| ui/app_minimal.py | OK |
