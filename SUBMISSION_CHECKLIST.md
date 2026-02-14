# ハッカソン提出チェックリスト（2026-02-14）

> **第4回 Agentic AI Hackathon with Google Cloud**
> **提出締切: 2026-02-15（RULES.md）/ 2026-02-14（RULES2.md）**
> ※ 日程齟齬あり。**安全策として本日2/14中に全て完了させる**

---

## 提出に必要な3点（RULES2.md準拠）

| # | 提出物 | 状態 | 備考 |
|---|--------|------|------|
| 1 | GitHubリポジトリURL（公開） | ⬜ 未着手 | 下記手順で作成 |
| 2 | デプロイURL（動作確認可能） | ✅ 完了 | API+UI共にCloud Run稼働中 |
| 3 | Zenn記事URL | ⬜ TODO4件あり | 動画URL・スクショ3箇所を埋める |

---

## フェーズ0: 今すぐできる準備（足軽の作業完了を待たずに着手可能）

### 0-1. 録画環境の準備
- [ ] **OBS Studio** がインストールされているか確認（なければ https://obsproject.com/ja からDL）
- [ ] OBSを起動 → ソース「ウィンドウキャプチャ」でChrome指定
- [ ] ソース「音声入力キャプチャ」でマイク指定
- [ ] 設定 → 出力: 1920x1080, 30fps, MP4, ビットレート4000-6000kbps
- [ ] テスト録画10秒 → 再生して映像・音声を確認
- [ ] 録画出力先フォルダを決めておく（デスクトップ推奨）

### 0-2. PC環境の整備
- [ ] Windows **集中モード ON**（設定 → システム → 集中モード）
- [ ] Slack, Teams, Discord 等の通知アプリを終了
- [ ] Chrome以外のブラウザ・不要アプリを閉じる

### 0-3. Chromeの準備
- [ ] ブックマークバー非表示（Ctrl+Shift+B）
- [ ] 不要な拡張機能アイコンを非表示
- [ ] ズーム100%（Ctrl+0）
- [ ] タブをデモ用1つだけにする

### 0-4. デプロイ済みUIの動作確認（cold start解消も兼ねる）

```powershell
# ヘルスチェック
curl.exe -s https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app/health
# 期待値: {"ok":true}
```

- [ ] UIにブラウザでアクセス → 正常表示
- [ ] サンプルデータで1回判定テスト（CAPITAL_LIKE確認 + cold start解消）

### 0-5. YouTube・Zennの下準備
- [ ] YouTubeにアップロードできるアカウントでログイン確認
- [ ] Zenn記事の下書きを開き、TODO4箇所の位置を確認しておく

### 0-6. GitHubの下準備
- [ ] GitHubにログイン済み確認
- [ ] リポジトリ作成画面（https://github.com/new）をブックマーク
- [ ] `git --version` でgitが使えることを確認

### 0-7. ナレーション練習（本番品質に最も効果大）

VIDEO_RECORDING_GUIDE.md 末尾のクイックリファレンスを**印刷 or 別画面に表示**し、声に出して1回通す。

キーフレーズ（3つだけ覚える）:
1. **「知らないを、知っているAI」**（オープニング・クロージング）
2. **「止まる、聞く、変わる」**（GUIDANCEデモ中）
3. **「人の判断を奪わない。支える。」**（クロージング）

- [ ] タイマーで計測しながら1回通し読み
- [ ] 3分以内に収まることを確認
- [ ] 水を手元に用意

---

## フェーズ1: コード修正（足軽が実施中）

> cmd_035で家老・足軽が対応中。殿は待つだけ。

- [ ] RISK-002: slowapiレート制限追加
- [ ] RISK-003: Gemini APIタイムアウト30秒設定
- [ ] RISK-004: コスト制御（トークン上限・thinking_level適正化）
- [ ] RISK-005: bare except → 具体的例外 + logger.exception()
- [ ] RISK-006: 起動時Gemini接続テスト
- [ ] NOTE-03: app_minimal.py L79 GCPプロジェクト番号を環境変数化
- [ ] AGPL-3.0（PyMuPDF）ライセンスをREADMEに明記

**確認方法**: dashboard.md を見て全て完了になったら次へ

---

## フェーズ2: GitHub公開（殿の作業）

### 2-1. 機密情報の最終確認

```powershell
# .gitignoreに以下が含まれていることを確認
cat .gitignore | Select-String "\.env|credentials|secret|apikey"
```

確認すべき項目:
- [ ] `.env` がgitignoreに含まれている
- [ ] `credentials.json` 等がgitignoreに含まれている
- [ ] GCPプロジェクト番号がコードにハードコードされていない（cmd_035で修正済みのはず）
- [ ] GOOGLE_API_KEY がコードに直書きされていない

### 2-2. GitHubリポジトリ作成・プッシュ

```powershell
# 1. プロジェクトディレクトリに移動
cd C:\Users\owner\Desktop\fixed-asset-ashigaru

# 2. gitリポジトリ初期化（まだの場合）
git init

# 3. 全ファイルをステージング
git add -A

# 4. コミット
git commit -m "Initial commit: Fixed Asset Agentic - Agentic AI Hackathon submission"

# 5. GitHubでリポジトリを作成（ブラウザで）
#    → https://github.com/new
#    → リポジトリ名: fixed-asset-ashigaru（推奨）
#    → Public を選択
#    → "Create repository" をクリック

# 6. リモート追加＆プッシュ（GitHubの画面に表示されるコマンドをコピペ）
git remote add origin https://github.com/<あなたのユーザー名>/fixed-asset-ashigaru.git
git branch -M main
git push -u origin main

# 7. 提出用タグを打つ（審査期間中の状態を保持）
git tag -a v1.0-submission -m "Hackathon submission 2026-02-14"
git push origin v1.0-submission
```

### 2-3. 公開後の確認

- [ ] リポジトリが Public になっている
- [ ] README.md が表示されている
- [ ] ライセンス情報が明記されている
- [ ] .env や credentials がプッシュされていない
- [ ] タグ `v1.0-submission` が存在する

---

## フェーズ3: 再デプロイ（足軽が実施 → 殿が確認）

> コード修正後、足軽が再デプロイする。殿は動作確認のみ。

確認URL:
- API: https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app/health
- UI: https://fixed-asset-agentic-ui-986547623556.asia-northeast1.run.app/

- [ ] `/health` が `{"ok": true}` を返す
- [ ] UI画面が正常に表示される
- [ ] サンプルデータで判定が動作する（CAPITAL_LIKE判定を1回テスト）
- [ ] GUIDANCEフロー（止まる→聞く→変わる）が動作する

---

## フェーズ4: デモ動画撮影（殿の作業）

> 詳細は VIDEO_RECORDING_GUIDE.md 参照

### 4-1. 撮影準備（30分前）
- [ ] PC再起動
- [ ] Cloud Run ヘルスチェック OK
- [ ] Chrome フルスクリーン、通知OFF
- [ ] OBS設定: 1920x1080, 30fps, マイクOK
- [ ] テスト録画10秒 → 再生確認

### 4-2. 撮影（3分以内）
```
[0:00-0:25] オープニング 「知らないを、知っているAI」
[0:25-0:40] Case1: CAPITAL_LIKE即判定
[0:40-2:10] Case2: GUIDANCE（止まる→聞く→変わる→DIFF）★核心
[2:10-2:40] 技術ハイライト
[2:40-3:00] クロージング 「人の判断を奪わない。支える。」
```

### 4-3. 撮影後チェック
- [ ] 3分以内に収まっている
- [ ] 音声が明瞭
- [ ] UI画面の文字が読める
- [ ] エラーが映っていない
- [ ] ファイル形式: MP4

---

## フェーズ5: YouTube公開（殿の作業）

- [ ] YouTubeにアップロード
  - タイトル例: 「Fixed Asset Agentic - 知らないを、知っているAI【Agentic AI Hackathon】」
  - 説明文にプロジェクト概要を記載
  - 公開設定: **限定公開** or **公開**
- [ ] 動画URLを控える

---

## フェーズ6: Zenn記事の仕上げ（殿の作業）

> 既存の下書きにTODO4件を埋める

### Zenn記事の設定（RULES2.md必須要件）
- [ ] カテゴリ: **Idea** を選択
- [ ] トピック: **gch4** を追加

### 記事に含める内容（RULES2.md必須要件）
- [ ] プロジェクト概要（対象ユーザー、課題、特徴）
- [ ] システムアーキテクチャ図
- [ ] デモ動画（YouTube埋め込み） ← TODO: 動画URL
- [ ] スクリーンショット3箇所 ← TODO: 撮影時にキャプチャ

### TODO埋め作業
1. YouTube動画URLを記事に埋め込む
2. スクリーンショット3箇所を撮影・貼付
3. 記事を公開

---

## フェーズ7: 提出フォーム送信（殿の作業）

- [ ] 主催者指定の提出フォームにアクセス
- [ ] 以下3点のURLを記入:
  1. **GitHubリポジトリURL**: `https://github.com/<ユーザー名>/fixed-asset-ashigaru`
     （タグURL: `https://github.com/<ユーザー名>/fixed-asset-ashigaru/releases/tag/v1.0-submission`）
  2. **デプロイURL**: `https://fixed-asset-agentic-ui-986547623556.asia-northeast1.run.app/`
  3. **Zenn記事URL**: （公開後のURL）
- [ ] 使用Google Cloud製品を記入:
  - Cloud Run（アプリ実行）
  - Gemini API（AI判定）
  - Document AI（PDF抽出）
  - Vertex AI Search（法令検索）
- [ ] 送信

---

## フェーズ8: 提出後の確認

- [ ] GitHubリポジトリにアクセスできる（シークレットウィンドウで確認）
- [ ] デプロイURLが動作する
- [ ] Zenn記事が公開されている
- [ ] デモ動画が再生できる
- [ ] **2026年3月2日まで** この状態を維持する（RULES2.md要件）

---

## タイムライン目安

| 時刻目安 | フェーズ | 作業者 |
|----------|----------|--------|
| 〜完了待ち | F1: コード修正 | 足軽（自動） |
| 修正完了後 | F2: GitHub公開 | 殿 |
| 修正完了後 | F3: 再デプロイ確認 | 足軽→殿確認 |
| GitHub後 | F4: デモ動画撮影 | 殿 |
| 撮影後 | F5: YouTube公開 | 殿 |
| YouTube後 | F6: Zenn記事仕上げ | 殿 |
| 全完了後 | F7: 提出フォーム送信 | 殿 |
| 提出後 | F8: 最終確認 | 殿 |

---

## 注意事項

- **日程齟齬**: RULES.mdは提出2/15、RULES2.mdは提出2/14。**安全策で本日中に完了**
- **GitHubは3/2まで保持**: 提出後もリポジトリ・デプロイを維持すること
- **デプロイURLは記事に掲載不要**（RULES2.md注意事項）だが、掲載する場合はクラウド費用に注意
- **pptxプレゼン**: 足軽が作成中。1次審査通過後の最終ピッチ（3/19）で使用
