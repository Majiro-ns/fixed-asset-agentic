# Gemini 3 Pro API キー取得・設定手順書

> **作成日**: 2026-02-08
> **対象モデル**: `gemini-3-pro-preview`
> **SDK**: `google-genai` (新SDK)

---

## 1. Google AI Studio でAPIキーを取得する

### 1-1. Google AI Studio にアクセス

```
https://aistudio.google.com/
```

Googleアカウントでログイン。初回はTerms of Serviceへの同意が必要。

### 1-2. APIキーを作成

1. 左サイドバーの **「Get API Key」** をクリック
2. **「Create API key」** をクリック
3. 既存のGCPプロジェクトを選択 or 新規プロジェクトを自動作成
4. 生成されたAPIキーをコピー（`AIza...` で始まる文字列）

> **注意**: APIキーは一度しか表示されない場合がある。必ずコピーして安全な場所に保存すること。

### 1-3. Gemini 3 Pro が使えるキーか確認

**無料枠**: Google AI Studio の無料枠でも Gemini 3 Pro Preview は利用可能。ただしレート制限あり。

**有料枠**: より高いレート制限が必要な場合は、Google Cloud Console で課金を有効化する。

確認方法は後述の「5. 動作確認」で実際にAPIを叩いて確認する。

---

## 2. 新SDK (google-genai) のインストール

### 2-1. pip でインストール

```bash
pip install -U google-genai
```

> **要件**: Python 3.10 以上
> **最新バージョン**: 1.62.0（2026-02-04 時点）

### 2-2. 旧SDKとの違い

| 項目 | 旧SDK (`google-generativeai`) | 新SDK (`google-genai`) |
|------|------|------|
| パッケージ名 | `google-generativeai` | `google-genai` |
| import | `import google.generativeai as genai` | `from google import genai` |
| 初期化 | `genai.configure(api_key=...)` | `client = genai.Client(api_key=...)` |
| API呼び出し | `model.generate_content(...)` | `client.models.generate_content(...)` |
| Gemini 3 対応 | 非対応 | 対応（v1.51.0以降） |

> **重要**: Gemini 3 系モデルは新SDK `google-genai` v1.51.0 以降が必要。旧 `google-generativeai` では動かない。

---

## 3. ローカル環境での設定

### 3-1. .env ファイルの設定

プロジェクトルートの `.env` に以下を追記：

```bash
# Gemini 3 Pro 用（新SDK が自動で読む）
GEMINI_API_KEY=ここにAPIキーを貼る

# 既存キー（Embedding等のフォールバック用に残す）
GOOGLE_API_KEY=既存のキーをそのまま残す

# Gemini分類を有効化
GEMINI_ENABLED=1

# 使用モデル
GEMINI_MODEL=gemini-3-pro-preview
```

> **環境変数の優先順位**:
> - `GEMINI_API_KEY` を設定すると新SDKが自動で検出する
> - `GOOGLE_API_KEY` も設定されている場合、`GOOGLE_API_KEY` が優先される（Google側の仕様）
> - 両方同じキーにしておけば問題ない

### 3-2. 環境変数を手動でexportする場合

```bash
export GEMINI_API_KEY="AIzaSy..."
export GEMINI_ENABLED=1
export GEMINI_MODEL=gemini-3-pro-preview
```

### 3-3. python-dotenv で .env を読み込む場合

```python
from dotenv import load_dotenv
load_dotenv()
```

---

## 4. Cloud Run 環境変数の更新

### 4-1. Secret Manager にキーを登録（推奨）

```bash
# シークレットを作成（初回のみ）
echo -n "AIzaSy..." | gcloud secrets create gemini-api-key \
  --replication-policy="automatic" \
  --data-file=-

# 既にシークレットがある場合はバージョンを追加
echo -n "AIzaSy..." | gcloud secrets versions add gemini-api-key \
  --data-file=-
```

### 4-2. Cloud Run サービスを更新

```bash
# サービス名を確認
gcloud run services list

# 環境変数 + シークレットを設定してデプロイ
gcloud run services update YOUR_SERVICE_NAME \
  --region=asia-northeast1 \
  --set-secrets "GEMINI_API_KEY=gemini-api-key:latest" \
  --update-env-vars "GEMINI_ENABLED=1,GEMINI_MODEL=gemini-3-pro-preview"
```

> `YOUR_SERVICE_NAME` は実際のCloud Runサービス名に置き換えること。

### 4-3. 環境変数を直接設定する場合（非推奨・テスト用）

```bash
gcloud run services update YOUR_SERVICE_NAME \
  --region=asia-northeast1 \
  --update-env-vars "GEMINI_ENABLED=1,GEMINI_API_KEY=AIzaSy...,GEMINI_MODEL=gemini-3-pro-preview"
```

> **非推奨の理由**: APIキーがCloud Runの設定に平文で保存される。本番では必ずSecret Managerを使うこと。

---

## 5. 動作確認

### 5-1. APIキーの疎通テスト（コピペでOK）

```bash
python3 -c "
from google import genai

client = genai.Client()
response = client.models.generate_content(
    model='gemini-3-pro-preview',
    contents='こんにちは。1+1は？'
)
print('=== 疎通成功 ===')
print(response.text)
"
```

**期待する出力**:
```
=== 疎通成功 ===
2です。
```

**エラーが出た場合**:
- `API key not valid` → キーが間違っている or 環境変数が設定されていない
- `Model not found` → モデル名が間違っている。`gemini-3-pro-preview` が正しいか確認
- `Permission denied` → 課金が必要な場合がある

### 5-2. gemini-3-pro-preview が使えるか確認

```bash
python3 -c "
from google import genai

client = genai.Client()

# 利用可能なモデル一覧からGemini 3系を検索
for model in client.models.list():
    if 'gemini-3' in model.name:
        print(f'{model.name} - {model.display_name}')
"
```

**期待する出力例**:
```
models/gemini-3-pro-preview - Gemini 3 Pro Preview
models/gemini-3-flash-preview - Gemini 3 Flash Preview
```

### 5-3. Thinking機能の確認（Gemini 3の新機能）

```bash
python3 -c "
from google import genai
from google.genai import types

client = genai.Client()
response = client.models.generate_content(
    model='gemini-3-pro-preview',
    contents='固定資産と費用の違いを簡潔に説明してください。',
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level='low')
    ),
)
print('=== Thinking機能テスト ===')
print(response.text)
"
```

> Gemini 3 Pro は Thinking（思考）機能を内蔵している。`thinking_level` は `"off"`, `"low"`, `"medium"`, `"high"` から選択可能。

### 5-4. 既存システムとの統合確認

```bash
# .env を読み込んだ状態で
GEMINI_ENABLED=1 GEMINI_MODEL=gemini-3-pro-preview python3 -c "
import os
os.environ['GEMINI_ENABLED'] = '1'
os.environ['GEMINI_MODEL'] = 'gemini-3-pro-preview'
print(f'GEMINI_ENABLED: {os.environ.get(\"GEMINI_ENABLED\")}')
print(f'GEMINI_MODEL: {os.environ.get(\"GEMINI_MODEL\")}')
print(f'GEMINI_API_KEY set: {bool(os.environ.get(\"GEMINI_API_KEY\") or os.environ.get(\"GOOGLE_API_KEY\"))}')
print('=== 環境変数の確認OK ===')
"
```

---

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| `ModuleNotFoundError: No module named 'google.genai'` | 旧SDKがインストールされている | `pip uninstall google-generativeai && pip install google-genai` |
| `google.genai.errors.ClientError: 400` | モデル名の誤り | `gemini-3-pro-preview` を正確に指定 |
| `google.genai.errors.ClientError: 403` | APIキーの権限不足 | AI Studio で新しいキーを再作成 |
| `google.genai.errors.ClientError: 429` | レート制限 | 無料枠の制限。しばらく待つ or 有料枠に切替 |
| `GEMINI_API_KEY` を設定したのに認識されない | 環境変数が読まれていない | `source .env` or `python-dotenv` で明示的に読込 |

---

## 参考リンク

- [Google AI Studio](https://aistudio.google.com/)
- [Gemini API キーの使い方](https://ai.google.dev/gemini-api/docs/api-key)
- [Gemini 3 開発者ガイド](https://ai.google.dev/gemini-api/docs/gemini-3)
- [google-genai PyPI](https://pypi.org/project/google-genai/)
- [google-genai GitHub](https://github.com/googleapis/python-genai)
- [Gemini API クイックスタート](https://ai.google.dev/gemini-api/docs/quickstart)
