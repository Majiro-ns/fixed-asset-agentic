# SPEC: Useful Life Candidates (Step 4)

## 業務目的（Why）
固定資産の耐用年数検討において、国税庁・省令別表に基づく「候補」を先に提示し、
担当者が確定判断を行うための下準備（論点整理・根拠提示）を自動化する。

- 最終確定は人が行う（AIは確定しない）
- 出力は「候補」と「根拠（国の資料 / 過去例 / 抽出evidence）」を必ず伴う

---

## 入力（Input）
- extraction（PDF抽出結果。evidence/warnings含む）
- preclassification（ルールベース一次整理）
- ai_suggestions（Step 3の勘定科目・区分候補）
- optional: historical_judgements（社内過去判定ログ/教師データ検索結果）

---

## データソース（必須）
### A. 法定耐用年数データ（一次情報）
- 「減価償却資産の耐用年数等に関する省令」別表（機械装置/その他/無形等）
- 国税庁の耐用年数表（代表例PDF）
※ 実装では、上記を “機械可読の辞書” に変換したファイルをリポジトリに同梱すること

### B. 社内過去判定（任意だが推奨）
- 過去の採用結果（品名/摘要/用途/勘定科目/耐用年数/理由）を検索し、類似例として提示

---

## 出力（Output）: useful_life_candidates
### 形式（例）
```json
{
  "useful_life": {
    "candidates": [
      {
        "life_years": 5,
        "asset_class": "工具器具備品",
        "legal_basis": {
          "source": "ministerial_ordinance_appended_table",
          "table": "AppendedTableX",
          "row_key": "…",
          "match_reason": "…"
        },
        "supporting_evidence_refs": ["ev-003", "ev-007"],
        "historical_support": {
          "similar_cases": 3,
          "examples": [
            { "case_id": "HIST-2024-0012", "life_years": 5, "note": "…" }
          ]
        },
        "confidence": "medium",
        "risk_notes": [
          "用途が不明確。現物の使用形態で年数が変わる可能性あり"
        ]
      }
    ],
    "recommendation": {
      "recommended_life_years": null,
      "policy": "AI does not finalize. Human must select."
    },
    "warnings": [
      { "code": "LOW_TEXT_CONFIDENCE", "message": "Extraction is weak; candidate reliability reduced." }
    ]
  }
}
推察（AI）の許可範囲（重要）
AIが行ってよいのは以下のみ：

法定耐用年数データ辞書の「どの行に近いか」を推定し、候補として列挙する

過去判定の類似例を引用して、候補の妥当性を補強する

不明点・論点（用途/構造/セット品/資本的支出の可能性等）を “質問候補” として列挙する

AIが行ってはいけない：

最終耐用年数の確定

税法解釈の変更・新ルールの創作

証拠なしの断定

ルール（Candidate Generation）
候補は必ず複数（最低2件：本命＋代替）を返す

各候補に以下を必須付与：

legal_basis（一次情報への参照キー）

match_reason（何が一致したか）

supporting_evidence_refs（PDF抽出evidenceの参照）

extraction.warnings がある場合：

confidence を1段階落とす、または warnings に転記する

historical_support は任意だが、ある場合は件数と例を示す

実装要件（Implementation Requirements）
同梱する辞書ファイルの配置：

data/legal/useful_life_tables/*.json（推奨）

または data/legal/useful_life_tables.csv

辞書は “出典URL/作成日/バージョン” をmetaとして保持する

テスト：

fixture入力から candidates が複数出ること

legal_basis が空にならないこと

recommendation.recommended_life_years が null のままであること（確定禁止の担保）

受け入れ条件（Acceptance Criteria）
Step 1〜3 の出力を入力として動作する

候補が複数出る

根拠（legal_basis）と evidence_refs が必ず付く

AIが確定せず、人が選ぶ前提の出力になっている

yaml
コードをコピーする

---

## 次に作る「タスク」を順番に（Issue化しやすい粒度）
このStep 4を実装するために、Issue（＝自律開発単位）はこう切るのが安全です。

### Task 4-1：法定耐用年数テーブルの“辞書化”
- `data/legal/useful_life_tables/` を新設
- e-Gov/国税庁PDFのどこをソースにしたかを `meta.json` に保存
- まずは「よく出るカテゴリ」だけ（例：工具器具備品/機械装置/車両/ソフト/建物附属設備）から始める  
  ※省令別表全網羅は後回し

### Task 4-2：辞書検索（ルール＋簡易類似）
- Step3の `account_name` と `description_indicator` をキーに候補行を絞る
- “一致理由” を必ず出す

### Task 4-3：過去判定（履歴）検索の口（任意）
- あなたの教師データCSVを読み込める形にする（ローカル前提でOK）
- 類似例3件くらい返す（件数と差分を出す）

### Task 4-4：UI表示
- Streamlitで「候補・根拠・過去例」を並べて、担当者が選べる画面
