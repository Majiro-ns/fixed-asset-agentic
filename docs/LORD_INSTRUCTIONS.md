# 🏯 殿の完全チェックリスト

> **最終更新**: 2026-01-31 19:35
> **提出期限**: 2026-02-15（残り15日）
> **目標**: 第4回 Agentic AI Hackathon with Google Cloud 最優秀賞（50万円）

---

## ✅ これを全て完了すれば提出OK

---

## 🔴 Phase 1: 今日やること（技術準備）【最重要】

### 🚨 1. pytest実行
```powershell
cd C:\Users\owner\Desktop\fixed-asset-ashigaru
python -m pytest tests/ -v
```
- [ ] 全テストPASS確認

### 🚨 2. commit & push【未実行だとPDF機能がデプロイされない】
```powershell
cd C:\Users\owner\Desktop\fixed-asset-ashigaru

# .gitignoreに機密除外を追加
Add-Content -Path .gitignore -Value "`n# GCloud config`n.gcloud_config/`nadd_apikey.bat`ndeploy.bat`ndeploy_now.bat"

# ステージング
git add .

# コミット
git commit -m "ハッカソン提出準備: PDF分類・Gemini統合・ドキュメント整備"

# プッシュ
git push origin main
```
- [ ] commit完了
- [ ] push完了

### 🚨 3. Cloud Run再デプロイ【PDF機能を有効化】
```powershell
cd C:\Users\owner\Desktop\fixed-asset-ashigaru

# 再デプロイ（PDF機能ON）
gcloud run deploy fixed-asset-agentic-api --source . --region asia-northeast1 --allow-unauthenticated --set-env-vars "PDF_CLASSIFY_ENABLED=1"
```
- [ ] デプロイ完了
- [ ] `/classify_pdf` が動作確認

**確認コマンド:**
```powershell
# PDF機能確認（ダミーでエラー内容を見る）
curl.exe -s -X POST "https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app/classify_pdf" -F "file=@README.md"
# → "Invalid PDF" エラーが返ればエンドポイントは動作中（Not Foundではない）
```

### 4. GitHubをPublicに変更
1. https://github.com/Majiro-ns/fixed-asset-agentic にアクセス
2. **Settings** → 最下部 **Danger Zone**
3. **Change visibility** → **Public** に変更
- [ ] Public設定完了

---

## 🟡 Phase 2: デモ動画作成（2/3〜2/7推奨）

### 5. デモ動画撮影（3分以内）

**事前準備:**
- [ ] 撮影5分前に `/health` を叩いてウォームアップ
  ```powershell
  curl.exe https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app/health
  ```
- [ ] テスト用PDFを準備（見積書サンプル）

**デモの流れ（勝つための構成）:**

| 時間 | 内容 | ポイント |
|------|------|----------|
| 0:00-0:30 | 問題提起 | 「判断を疑う余裕がない現場」 |
| 0:30-1:00 | **PDFアップロード→CAPITAL_LIKE** | PDFから一発で資産判定 |
| 1:00-1:30 | **PDFアップロード→EXPENSE_LIKE** | 費用判定も見せる |
| 1:30-2:30 | **PDFアップロード→GUIDANCE→再分類** | 「止まるAI」の核心 |
| 2:30-3:00 | 技術説明・まとめ | GCP活用、Stop-first設計 |

**強調すべき3つの瞬間:**
1. 「止まる」瞬間 — GUIDANCE表示時に一拍置く
2. 「聞く」瞬間 — missing_fieldsと質問表示
3. 「変わる」瞬間 — DIFFカードのBefore→After

- [ ] 「止まるAI」を口頭で強調
- [ ] 3分以内に収める
- [ ] YouTube/Vimeoにアップロード

---

## 🟡 Phase 3: Zenn記事作成（2/8〜2/10推奨）

### 6. Zenn記事作成・公開
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

### 7. 参加登録フォーム提出
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
□ Cloud Run /classify_pdf が動作する（Not Foundではない）
□ Zenn記事が公開されている
□ Zenn記事のトピックに「gch4」がある
□ Zenn記事にデモ動画（3分以内）が埋め込まれている
□ 参加登録フォームを提出した
```

---

## 📊 現在の状況サマリ

### ✅ 完了済み（足軽が対応）

| 項目 | 状態 |
|------|------|
| Cloud Run基本動作 | ✅ /health, /classify 正常 |
| README時間削減数値追記 | ✅ 67%削減など追加済み |
| デモデータ確認 | ✅ 4件存在 |
| ゴールデンセット確認 | ✅ 10ケース存在 |
| LICENSEファイル | ✅ MIT License存在 |
| PDF抽出コード | ✅ ローカルに実装済み |

### 🚨 致命的問題（未解決）

| 項目 | 状態 | 影響 |
|------|------|------|
| **未コミット変更** | ❌ 68件未push | PDF機能がCloud Runにない |
| **Cloud Run再デプロイ** | ❌ 未実行 | /classify_pdf が動かない |
| **GitHub非公開** | ❌ Private | 提出不可 |

### ⏳ 殿待ち

| 項目 | 状態 |
|------|------|
| pytest実行 | ⏳ |
| commit & push | ⏳ **最優先** |
| Cloud Run再デプロイ | ⏳ **最優先** |
| GitHub公開化 | ⏳ |
| デモ動画撮影 | ⏳ |
| Zenn記事 | ⏳ |
| 参加登録 | ⏳ |

---

## 🏆 勝つためのポイント

### 審査基準と対応

| 審査基準 | 本プロジェクトの強み |
|----------|---------------------|
| 課題の新規性 | 「止まるAI」という逆転の発想 |
| 解決策の有効性 | Stop-first設計、67%時間削減 |
| 実装品質・拡張性 | Golden Set 100%、Cloud Run稼働中 |

### PDF→分類を見せることが勝利の鍵

過去の受賞作品は全て**エンドツーエンドのデモ**を見せている。
JSONを手動選択するのではなく、**PDFをアップロードして一発で結果が出る**流れを見せるべし。

---

## 🚨 注意事項

### 絶対に忘れるな

1. **Cloud Run再デプロイ** — PDF機能がないと勝てない
2. **Zennトピック「gch4」** — これがないと失格
3. **デモ動画3分以内** — オーバーすると減点
4. **参加登録締切2/13** — 遅れると失格

### デモ前のウォームアップ

Cloud Runはコールドスタートに2.2秒かかる。撮影5分前に必ず `/health` を叩け。

---

## 📞 サポート

追加の作業が必要な場合は将軍に伝達くだされ。足軽が対応いたす。

**ハッカソン勝利を祈念いたす！**
