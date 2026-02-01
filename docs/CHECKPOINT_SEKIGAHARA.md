# 🏯 関ヶ原チェックポイント

**作成日時**: 2026-02-01 19:45
**合言葉**: `関ヶ原に退け`

## 復帰方法

新機能実装で行き詰まった場合、以下のコマンドで本チェックポイントに戻る:

```powershell
cd C:\Users\owner\Desktop\fixed-asset-ashigaru

# 方法1: タグに戻る（推奨）
git checkout sekigahara-checkpoint

# 方法2: ブランチに戻る
git checkout backup/sekigahara-20260201-1945

# 方法3: mainを強制リセット（注意: 全変更が消える）
git checkout main
git reset --hard sekigahara-checkpoint
```

## チェックポイント時点の状態

### コミット済み機能
- ✅ 基本判定機能（CAPITAL_LIKE / EXPENSE_LIKE / GUIDANCE）
- ✅ PDF判定（通常 + 高精度モード）
- ✅ 耐用年数自動判定
- ✅ 判定履歴蓄積 + CSVエクスポート
- ✅ 免責事項・セキュリティ説明
- ✅ 判断理由表示・次アクション明示
- ✅ Cloud Run デプロイ済み（API + UI）

### 未コミットの変更
以下は作業中のファイルとして残っている:
- `docs/zenn_article_draft.md` - 今後の課題追記
- `ui/app_minimal.py` - ペルソナ評価に基づく改善
- `docs/NEW_FEATURES_CANDIDATES.md` - 新機能候補一覧

### Git情報
- **タグ**: `sekigahara-checkpoint`
- **ブランチ**: `backup/sekigahara-20260201-1945`
- **コミットハッシュ**: `29e41f0`

## これから実装する予定の機能

| 機能 | 工数（8名並列） |
|------|----------------|
| A2: 複数書類PDF分割 | 9.0h |
| A1: 資産名類似度学習 | 3.0h |
| B2: 類似事例の提示 | 2.0h |
| B3: 一括アップロード | 4.0h |
| C1: 固定資産台帳インポート | 2.0h |

## 撤退判断基準

以下の場合は「関ヶ原に退け」を発動:
1. 新機能がデプロイ後に動作しない
2. 既存機能に影響が出た
3. 締切（2/13）に間に合わない見込み
4. デモ動画撮影に支障が出る
