# 🏯 殿の完全チェックリスト

> **最終更新**: 2026-01-31 19:19
> **提出期限**: 2026-02-15（残り15日）
> **目標**: 第4回 Agentic AI Hackathon with Google Cloud 最優秀賞（50万円）

---

## ✅ これを全て完了すれば提出OK

---

## 🔴 Phase 1: 今日やること（技術準備）

### 1. pytest実行 ⏳
```powershell
cd C:\Users\owner\Desktop\fixed-asset-ashigaru
python -m pytest tests/ -v
```
- [ ] 全テストPASS確認

### 2. commit & push ⏳
```powershell
cd C:\Users\owner\Desktop\fixed-asset-ashigaru

# .gitignoreに機密除外を追加
Add-Content -Path .gitignore -Value "`n# GCloud config`n.gcloud_config/`nadd_apikey.bat`ndeploy.bat`ndeploy_now.bat"

# ステージング
git add .

# コミット
git commit -m "ハッカソン提出準備完了: 導入効果追記・ドキュメント整備"

# プッシュ
git push origin main
```
- [ ] commit完了
- [ ] push完了

### 3. GitHubをPublicに変更 ⏳
1. https://github.com/Majiro-ns/fixed-asset-agentic にアクセス
2. **Settings** → 最下部 **Danger Zone**
3. **Change visibility** → **Public** に変更
- [ ] Public設定完了

---

## 🟡 Phase 2: デモ動画作成（2/3〜2/7推奨）

### 4. デモ動画撮影（3分以内）
- [ ] 撮影5分前に `/health` を叩いてウォームアップ
  ```powershell
  curl.exe https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app/health
  ```
- [ ] 台本確認: `docs/DEMO_RUNBOOK.md`
- [ ] UI起動:
  ```powershell
  cd C:\Users\owner\Desktop\fixed-asset-ashigaru
  streamlit run ui/app_minimal.py
  ```
- [ ] 3シナリオ録画:
  1. CAPITAL_LIKE（30秒）— サーバー新設 → 即座に資産判定
  2. EXPENSE_LIKE（30秒）— 保守作業 → 費用判定
  3. GUIDANCE + 再分類（90秒）— 曖昧なケース → 停止 → 質問 → 再実行 → DIFF表示
- [ ] 「止まるAI」を口頭で強調
- [ ] 3分以内に収める
- [ ] YouTube/Vimeoにアップロード

---

## 🟡 Phase 3: Zenn記事作成（2/8〜2/10推奨）

### 5. Zenn記事作成・公開
- [ ] 新規記事作成
- [ ] カテゴリ: **Idea**（必須）
- [ ] トピック: **gch4**（必須！これがないと失格）
- [ ] 含める内容:
  - [ ] プロジェクト概要（Stop-first設計）
  - [ ] システム構成図（README.mdからコピー）
  - [ ] デモ動画埋め込み
  - [ ] GitHubリポジトリURL
  - [ ] Cloud Run URL
- [ ] 公開

---

## 🟡 Phase 4: 参加登録（締切: 2/13）

### 6. 参加登録フォーム提出
- [ ] GitHubリポジトリURL: `https://github.com/Majiro-ns/fixed-asset-agentic`
- [ ] デプロイURL: `https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app`
- [ ] Zenn記事URL: （公開後に記入）
- [ ] 100-150字要約:
  > 見積書PDFをアップするだけで、明細行を理解し、固定資産か修繕費かの判断を支援します。判断が割れる場合は断定せずガイダンスに落とす、安全設計の実務向けAgentic AIです。
- [ ] フォーム提出完了

---

## ✅ Phase 5: 提出直前の最終確認（2/15）

```
□ GitHubリポジトリが Public である
□ 最新コードがpush済みである
□ Cloud Run /health が {"ok":true} を返す
□ Zenn記事が公開されている
□ Zenn記事のトピックに「gch4」がある
□ Zenn記事にデモ動画（3分以内）が埋め込まれている
□ Zenn記事にGitHubリポジトリURLが記載されている
□ Zenn記事にデプロイURLが記載されている
□ 参加登録フォームを提出した
```

---

## 📊 現在の状況サマリ

### ✅ 完了済み（足軽が対応）

| 項目 | 状態 |
|------|------|
| Cloud Run動作確認 | ✅ /health 200 OK |
| README時間削減数値追記 | ✅ 67%削減など追加済み |
| Cloud Runウォームアップ計測 | ✅ コールド2.2秒、ウォーム0.13秒 |
| デモデータ確認 | ✅ 4件存在（demo01〜04） |
| ゴールデンセット確認 | ✅ 10ケース存在 |
| LICENSEファイル | ✅ MIT License存在 |
| DEMO.md / DEMO_RUNBOOK.md | ✅ 台本準備済み |

### ⏳ 殿待ち

| 項目 | 状態 |
|------|------|
| pytest実行 | ⏳ Windows PowerShellで実行 |
| commit & push | ⏳ 68 modified + 50 untracked |
| GitHub公開化 | ⏳ 現在Private |
| デモ動画撮影 | ⏳ 未撮影 |
| Zenn記事 | ⏳ 未作成 |
| 参加登録 | ⏳ 締切2/13 |

---

## 📅 推奨スケジュール

| 期間 | やること |
|------|----------|
| **1/31（今日）** | pytest → commit → push → GitHub公開 |
| **2/3〜2/7** | デモ動画撮影・編集・アップロード |
| **2/8〜2/10** | Zenn記事作成・公開 |
| **2/11〜2/13** | 最終確認・参加登録 |
| **2/15** | 提出完了確認 |

---

## 🏆 勝つためのポイント

### 審査基準と対応

| 審査基準 | 本プロジェクトの強み |
|----------|---------------------|
| 課題の新規性 | 「止まるAI」という逆転の発想 |
| 解決策の有効性 | Stop-first設計、67%時間削減 |
| 実装品質・拡張性 | Golden Set 100%、Cloud Run稼働中 |

### デモで強調すべき3つの瞬間

1. **「止まる」瞬間** — GUIDANCE表示時に一拍置く
2. **「聞く」瞬間** — missing_fieldsと質問表示
3. **「変わる」瞬間** — DIFFカードのBefore→After

### 30秒ピッチ（Zenn記事冒頭用）

> 「AIが賢くなる」ではなく「AIが止まる」ことを価値とする。
> 経理現場では、月末・決算期に判断を疑う余裕がない。
> 本システムは、判断が割れる場面で**自律的に停止**し、人間に確認すべきポイントを明示する。
> これが「Agentic AI」の新しい定義 — **判断を行う／止めるを選択できる自律性**。

---

## 🚨 注意事項

### 絶対に忘れるな

1. **Zennトピック「gch4」** — これがないと失格
2. **デモ動画3分以内** — オーバーすると減点
3. **参加登録締切2/13** — 遅れると失格

### デモ前のウォームアップ

Cloud Runはコールドスタートに2.2秒かかる。撮影5分前に必ず `/health` を叩け。

---

## 📞 サポート

追加の作業が必要な場合は将軍に伝達くだされ。足軽が対応いたす。

**ハッカソン勝利を祈念いたす！**
