# GitHub 公開手順書

> **対象**: Fixed Asset Agentic（固定資産判定 AI）
> **ライセンス**: MIT（PyMuPDF は AGPL-3.0）
> **最終更新**: 2026-02-14

---

## 1. リポジトリ名の提案

| 候補 | 説明 | 推奨度 |
|------|------|--------|
| `fixed-asset-agentic` | プロジェクト名そのまま。README の git clone と一致 | **推奨** |
| `fixed-asset-classifier` | 機能ベースの命名。検索しやすい | 次点 |
| `asset-classification-agent` | Agentic AI を強調。ハッカソン向け | 可 |

> README.md のクイックスタートに `git clone https://github.com/Majiro-ns/fixed-asset-agentic.git` と記載済みのため、`fixed-asset-agentic` を推奨。

---

## 2. プッシュ前チェックリスト

**この手順を飛ばすと機密情報が公開される。必ず実行すること。**

### 2-1. .gitignore 確認

以下のパターンが `.gitignore` に含まれていることを確認:

```
.env                    # APIキー・プロジェクトID
*.key                   # 秘密鍵
*.pem                   # 証明書
credentials*            # GCP認証情報
service-account*        # サービスアカウントキー
.gcloud_config/         # gcloud設定・認証DB
__pycache__/            # Pythonキャッシュ
```

### 2-2. 機密情報スキャン

```powershell
# .env ファイルがステージングされていないか確認
git status --porcelain | Select-String "\.env$"

# ハードコードされたAPIキー・パスワードの検索
Select-String -Path "**/*.py","**/*.yaml","**/*.json" -Pattern "(api_key|password|secret|token)\s*=\s*['\"][^'""]{8,}" -Recurse

# GCPプロジェクト番号の残存確認（ドキュメント以外）
Select-String -Path "**/*.py" -Pattern "986547623556" -Recurse
```

### 2-3. .env.example の確認

`.env.example` に実際の値が入っていないことを確認:

```
GOOGLE_CLOUD_PROJECT=your-gcp-project-id   # OK（プレースホルダ）
GOOGLE_API_KEY=your-api-key-here            # OK（プレースホルダ）
```

### 2-4. 大容量ファイルの確認

```powershell
# 10MB以上のファイルを検索
Get-ChildItem -Recurse -File | Where-Object { $_.Length -gt 10MB } | Select-Object FullName, @{N="SizeMB";E={[math]::Round($_.Length/1MB,1)}}
```

---

## 3. GitHub リポジトリ作成手順

### 方法A: GitHub CLI（推奨）

```powershell
# 1. プロジェクトディレクトリに移動
cd C:\Users\owner\Desktop\fixed-asset-ashigaru

# 2. git 初期化（未実施の場合）
git init

# 3. 全ファイルをステージング
git add -A

# 4. .gitignore が正しく機能しているか確認
#    .env, .gcloud_config/, __pycache__/ 等が表示されないこと
git status

# 5. 初回コミット
git commit -m "Initial commit: Fixed Asset Agentic - Stop-first Agentic AI for asset classification"

# 6. GitHub リポジトリ作成 + プッシュ（公開）
gh repo create fixed-asset-agentic --public --source=. --push --description "Stop-first Agentic AI for fixed asset classification powered by Gemini 3 Pro"
```

### 方法B: GitHub Web UI

1. https://github.com/new にアクセス
2. 以下を入力:
   - **Repository name**: `fixed-asset-agentic`
   - **Description**: `Stop-first Agentic AI for fixed asset classification powered by Gemini 3 Pro`
   - **Public** を選択
   - **Add a README file**: チェックしない（既存READMEを使用）
   - **Add .gitignore**: チェックしない（既存.gitignoreを使用）
   - **Choose a license**: チェックしない（既存LICENSEを使用）
3. 「Create repository」をクリック
4. ローカルからプッシュ:

```powershell
cd C:\Users\owner\Desktop\fixed-asset-ashigaru
git init
git add -A
git status  # .env等が含まれていないことを必ず確認
git commit -m "Initial commit: Fixed Asset Agentic - Stop-first Agentic AI for asset classification"
git branch -M main
git remote add origin https://github.com/Majiro-ns/fixed-asset-agentic.git
git push -u origin main
```

---

## 4. リポジトリ設定（プッシュ後）

### 4-1. Description & Topics

GitHub リポジトリページの Settings または About で設定:

| 項目 | 推奨値 |
|------|--------|
| **Description** | Stop-first Agentic AI for fixed asset classification powered by Gemini 3 Pro |
| **Website** | Cloud Run UI の URL（任意） |
| **Topics** | `agentic-ai`, `google-cloud`, `gemini`, `fastapi`, `streamlit`, `fixed-assets`, `accounting`, `hackathon` |

```powershell
# GitHub CLI で設定
gh repo edit --description "Stop-first Agentic AI for fixed asset classification powered by Gemini 3 Pro"
gh repo edit --add-topic agentic-ai,google-cloud,gemini,fastapi,streamlit,fixed-assets,accounting,hackathon
```

### 4-2. License

LICENSEファイルが既にリポジトリルートにあるため、GitHub が自動検出する。
表示が「MIT License」になっていることを確認。

### 4-3. Environments & Secrets（任意）

Cloud Run への自動デプロイを行う場合:

| Secret 名 | 内容 |
|-----------|------|
| `GCP_PROJECT_ID` | GCP プロジェクトID |
| `GCP_SA_KEY` | サービスアカウントキー（JSON） |
| `GOOGLE_API_KEY` | Gemini API キー |

設定場所: Settings → Secrets and variables → Actions

---

## 5. GitHub Actions 設定案（CI/CD）

### 5-1. テスト自動実行（PR時）

`.github/workflows/test.yml` を作成:

```yaml
name: Test

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest

      - name: Run tests
        run: pytest tests/ -v --tb=short
        env:
          GEMINI_ENABLED: "0"  # テスト時はGemini無効
```

### 5-2. Golden Set 評価（任意）

```yaml
name: Golden Set Evaluation

on:
  push:
    branches: [main]
    paths:
      - "api/**"
      - "core/**"
      - "data/golden/**"

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run Golden Set Evaluation
        run: python scripts/eval_golden.py
        env:
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
          GEMINI_ENABLED: "1"
```

### 5-3. Cloud Run デプロイ（任意）

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]
    paths-ignore:
      - "docs/**"
      - "*.md"

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write

    steps:
      - uses: actions/checkout@v4

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
          service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}

      - name: Deploy API to Cloud Run
        uses: google-github-actions/deploy-cloudrun@v2
        with:
          service: fixed-asset-agentic-api
          source: .
          region: asia-northeast1

      - name: Smoke Test
        run: |
          sleep 10
          curl -sf "${{ steps.deploy.outputs.url }}/health" | grep -q '"ok"'
```

---

## 6. プッシュ後の確認

| チェック項目 | 確認方法 |
|------------|---------|
| README が正しく表示される | リポジトリトップページで確認 |
| LICENSE が認識されている | リポジトリ右上に「MIT License」表示 |
| .env が含まれていない | リポジトリ内ファイル一覧を確認 |
| .gcloud_config/ が含まれていない | リポジトリ内ファイル一覧を確認 |
| Topics が設定されている | リポジトリトップページの About 欄 |
| デモデータが含まれている | `data/demo/` と `data/golden/` が存在 |

```powershell
# GitHub CLI で確認
gh repo view --web
```

---

## 7. ハッカソン提出時の注意

| 項目 | 内容 |
|------|------|
| リポジトリURL | `https://github.com/Majiro-ns/fixed-asset-agentic` |
| ブランチ | `main` |
| デモ動画 | 別途提出（リポジトリには含めない） |
| Cloud Run URL | README に記載済み |
| PyMuPDF ライセンス | README に AGPL-3.0 について記載済み |
