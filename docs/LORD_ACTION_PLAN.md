# 殿（人間）実行手順書

> **作成日**: 2026-02-01
> **更新日**: 2026-02-01
> **目的**: ハッカソン提出に必要な人間実施タスクを優先順・締切付きで整理
> **締切**: 参加登録 2/13、プロジェクト提出 2/14-15

---

## 0. 提出前自動検証（最初に実行）

**全ての作業の前に実行せよ**:
```powershell
cd C:\Users\owner\Desktop\fixed-asset-ashigaru
python scripts/preflight_check.py
```

このスクリプトが全項目PASSであることを確認してから次へ進む。
FAILがあれば、表示される指示に従って修正する。

---

## 最優先アクション（締切順）

| 優先度 | タスク | 締切 |
|--------|--------|------|
| 🔴 P1 | 参加登録 | **2/13** |
| 🔴 P1 | 自動検証実行 (preflight_check.py) | 2/14前 |
| 🔴 P1 | commit & push | 2/14前 |
| 🔴 P1 | Cloud Run再デプロイ | 2/14前 |
| 🔴 P1 | GitHub公開確認 | 2/14前 |
| 🔴 P1 | デモ動画撮影 | 2/14前 |
| 🔴 P1 | Zenn記事作成 | 2/14前 |
| 🔴 P1 | プロジェクト提出 | **2/14-15** |

---

## 1. 参加登録（2/13締切）

### 手順

1. 参加登録フォームにアクセス
   - **URL**: https://lu.ma/agentic-ai-hackathon-4 （要確認）
   - または Discord で最新URLを確認

2. 必要情報を入力
   - 名前
   - メールアドレス
   - チーム名（個人参加の場合は個人名）
   - プロジェクト名: `見積書 固定資産判定システム`

3. **100-150字要約**（コピー用）:
   ```
   見積書PDFをアップするだけで、明細行を理解し、固定資産か修繕費かの判断を支援します。判断が割れる場合は断定せずガイダンスに落とす、安全設計の実務向けAgentic AIです。
   ```

### 注意
- **締切は2/13**。これを過ぎると失格
- Discord への参加も必要な場合あり（要確認）

---

## 2. commit & push

### 前提
- AIエージェントがコード・ドキュメント修正を完了していること
- 未pushのコミットがある可能性（68件）

### 手順

```powershell
cd C:\Users\owner\Desktop\fixed-asset-ashigaru

# 変更状況確認
git status

# 全変更をステージング
git add -A

# コミット
git commit -m "fix: DEBUG print削除、ドキュメント修正（cmd_009）"

# プッシュ
git push origin main
```

### 確認
```powershell
git log --oneline -5
```

---

## 3. Cloud Run再デプロイ

### 重要
- **PDF_CLASSIFY_ENABLED=1** を環境変数に設定
- これがないとPDF機能がデモできない

### 手順

```powershell
cd C:\Users\owner\Desktop\fixed-asset-ashigaru

# gcloud認証（未認証の場合）
gcloud auth login

# プロジェクト設定
gcloud config set project YOUR_PROJECT_ID

# デプロイ
gcloud run deploy fixed-asset-agentic-api \
  --source . \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --set-env-vars "PDF_CLASSIFY_ENABLED=1,GEMINI_CLASSIFY_ENABLED=1"
```

### 確認
デプロイ後、以下を叩いてレスポンスを確認:
```powershell
curl https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app/health
```

---

## 4. GitHub公開確認

### 手順

1. ブラウザで以下にアクセス:
   ```
   https://github.com/Majiro-ns/fixed-asset-agentic
   ```

2. 確認項目:
   - [ ] リポジトリが Public になっている
   - [ ] README.md が表示されている
   - [ ] LICENSE ファイルが存在する
   - [ ] 最新のコミットがpushされている

3. Private の場合:
   - Settings → Danger Zone → Change visibility → Make public

---

## 5. デモ動画撮影（3分以内）

### 事前準備

1. **撮影5分前に /health を叩く**（コールドスタート対策）:
   ```powershell
   curl https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app/health
   ```

2. テスト用PDF 3パターンを準備:
   - CAPITAL判定用PDF（固定資産）
   - EXPENSE判定用PDF（修繕費）
   - GUIDANCE用JSON（demo04_guidance_ambiguous.json）

### 推奨構成（3分）

| 時間 | 内容 | ポイント |
|------|------|----------|
| 0:00-0:30 | 問題提起 | 「経理担当者の判断を疑う余裕がない現場」 |
| 0:30-1:00 | PDFアップロード→CAPITAL_LIKE | PDFから一発で資産判定。**止まる** |
| 1:00-1:30 | PDFアップロード→EXPENSE_LIKE | 費用判定も見せる。**止まる** |
| 1:30-2:30 | JSON（demo04）で GUIDANCE→再分類 | **聞く→変わる**。Agentic Loop |
| 2:30-3:00 | 技術説明・まとめ | GCP活用、Stop-first設計 |

### 強調すべき3つの瞬間

1. **止まる** — 判断が割れたら止まる
2. **聞く** — 追加情報を要求する
3. **変わる** — 情報を受けて再分類、差分表示

### 録画ツール
- OBS Studio（推奨）
- Windows Game Bar（Win+G）
- Loom

### 注意
- 3分以内に収める
- 音声があると良い
- YouTube または Vimeo にアップロード

---

## 6. Zenn記事作成

### 必須項目

| 項目 | 内容 |
|------|------|
| **トピック** | `gch4` （必須。これがないと失格） |
| **カテゴリ** | Idea |
| **published** | `true` （公開必須） |
| **デモ動画** | 記事内に埋め込み必須 |

### 記事構成（推奨）

```markdown
---
title: "見積書PDFから固定資産判定を支援するAgentic AI"
emoji: "📊"
type: "idea"
topics: ["gch4", "gemini", "cloudrun", "agenticai"]
published: true
---

## はじめに
経理担当者が見積書を見て「固定資産か修繕費か」を判断する作業は...

## 課題
- 判断ミスによる税務リスク
- 担当者の属人化
- 確認作業の非効率

## 解決策
見積書PDFをアップロードするだけで、AIが明細行を分類...

## アーキテクチャ
- Google Cloud Run
- Gemini API
- Document AI（オプション）
- Vertex AI Search（オプション）

## デモ
[YouTube動画を埋め込み]

## Human-in-the-Loop
判断が割れる場合は断定せず「要確認（GUIDANCE）」に...

## 今後の展望
- 勘定科目の候補提示
- 耐用年数の自動提案

## リポジトリ
https://github.com/Majiro-ns/fixed-asset-agentic
```

### 下書きファイル
- `docs/zenn_article_draft.md` を参照

### 公開手順
1. https://zenn.dev にログイン
2. 新規記事作成
3. 上記内容を入力
4. **トピック「gch4」を必ず追加**
5. 「公開する」をクリック

---

## 7. プロジェクト提出（2/14-15）

### 手順

1. 提出フォーム/方法を確認（Discord または公式サイト）

2. 必要情報:
   - プロジェクト名
   - GitHub URL: `https://github.com/Majiro-ns/fixed-asset-agentic`
   - Cloud Run URL: `https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app`
   - Zenn記事URL
   - デモ動画URL
   - 100-150字要約

3. 提出前最終チェック:
   - [ ] GitHub が Public
   - [ ] Cloud Run が動作中（/health 確認）
   - [ ] Zenn記事が公開済み
   - [ ] デモ動画がアクセス可能
   - [ ] トピック「gch4」が付いている

---

## チェックリスト

### 2/13まで（必須）
- [ ] 参加登録完了

### 2/14まで（推奨）
- [ ] commit & push 完了
- [ ] Cloud Run再デプロイ完了
- [ ] GitHub公開確認
- [ ] デモ動画撮影・アップロード
- [ ] Zenn記事公開

### 2/14-15（提出）
- [ ] プロジェクト提出

---

## 緊急連絡先

- Discord（ハッカソン公式チャンネル）
- 問題発生時は Discord で質問

---

## 参考リンク

- [REVIEW_COMPLETE.md](./review/REVIEW_COMPLETE.md) — 全レビュー
- [submission_checklist.md](./submission_checklist.md) — 提出チェックリスト
- [winning_patterns_analysis.md](./winning_patterns_analysis.md) — 過去受賞分析
- [zenn_article_draft.md](./zenn_article_draft.md) — Zenn下書き

---

*この手順書に従って実行すれば、提出は完了します。最優秀賞を目指しましょう！*
