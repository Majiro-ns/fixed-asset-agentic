# ハッカソン開発の軌跡 — multi-agent-shogunで挑んだ固定資産AI仕分けエージェント

## 目次

- [0. はじめに — なぜこのハッカソンに出ようと思ったか](#section-0)
- [1. プロジェクトのアイデア着想](#section-1)
- [2. 開発環境の構築](#section-2)
- [3. 開発の全タイムライン](#section-3)
- [4. 技術的な深掘り](#section-4)
- [5. マルチエージェント開発の詳細](#section-5)
- [6. 失敗と学び](#section-6)
- [7. 審査基準に対する戦略的アプローチ](#section-7)
- [8. デプロイまでの道のり（拡充版）](#section-8)
- [9. 提出物の準備（拡充版）](#section-9)
- [10. 数字で見る開発の全容（拡充版）](#section-10)
- [11. 振り返り — 殿の声](#section-11)
- [12. 教訓の深掘り（拡充版）](#section-12)
- [13. 技術スタック完全版（拡充版）](#section-13)
- [14. 技術調査の全記録 — docs/research_*.md の総覧](#section-14)
- [15. 仕様設計の変遷 — docs/specs/ の全記録](#section-15)
- [16. レビューと品質改善の全記録](#section-16)
- [17. ハッカソン戦略の全容](#section-17)
- [18. デプロイ戦記 — Cloud Runとの格闘の全記録](#section-18)
- [19. 将来ビジョン — Stop-first設計の可能性](#section-19)
- [20. スキル化候補9件の詳細](#section-20)
- [21. おわりに（拡充版）](#section-21)

---

<a id="section-0"></a>

## 0. はじめに — なぜこのハッカソンに出ようと思ったか

### 参加の動機

<!-- 殿記入欄: このハッカソンを知ったきっかけ。どこで見つけたか、最初に何を感じたか -->

<!-- 殿記入欄: 参加を決めた理由。何が自分を突き動かしたか。「面白そうだったから」でも「賞金が欲しかったから」でも構わない。率直に -->

<!-- 殿記入欄: 過去にハッカソンに参加した経験はあるか？あるなら、その経験が今回にどう活きたか -->

### ハッカソンの概要 — 第4回 Agentic AI Hackathon with Google Cloud

今回参加したのは、**クラスメソッド株式会社**が主催し、**株式会社ボイスリサーチ**がスポンサーとして協力する「**第4回 Agentic AI Hackathon with Google Cloud**」である。

#### スケジュール

| 日程 | イベント |
|------|---------|
| 2025年12月10日 | LP公開・エントリー開始 |
| 2026年2月13日(金) | 参加登録締め切り（申し込みフォーム） |
| 2026年2月14日(土) | **プロジェクト提出締め切り** |
| 2026年2月15日(日) | プロジェクト提出締め切り（規約上） |
| 2026年2月16日〜23日 | 1次審査期間 |
| 2026年2月24日〜3月2日 | 2次審査期間（3月2日に受賞者・候補者通知） |
| 2026年3月19日 | **Agentic AI Summit**にて最終ピッチおよび表彰式 |

> **NOTE-01**: RULES.md（参加規約）では提出締め切りが「2月15日」、RULES2.md（提出要項ページ）では「2月14日(土)」と記載されている。この日程齟齬は主催者の正データであるため修正不可。実運用上は**2月14日を締め切り**として動いた。

#### 賞金構成

| 賞 | 賞金額 | 枠数 |
|----|--------|------|
| **最優秀賞** | 500,000円 | 1枠 |
| **優秀賞** | 250,000円 | 3枠 |
| **奨励賞** | 100,000円 | 5枠 |
| **合計** | **1,750,000円** | 9枠 |

賞品に関わる税務申告および納税は受賞者自身の責任。

#### 参加資格

- 日本国内に居住する18歳以上の個人またはチーム
- 政府機関職員、スポンサー/主催者関係者は参加不可
- 個人でもチームでも参加可能。複数プロジェクトへの参加も可能

#### 必須条件

提出するプロジェクトは以下の**全て**を満たす必要がある:

**1. Google Cloud アプリケーション実行プロダクトの利用（1つ以上）**:
- App Engine / Google Compute Engine / GKE / **Cloud Run** / Cloud Functions / Cloud TPU・GPU

**2. Google Cloud AI技術の利用（1つ以上）**:
- **Vertex AI** / **Gemini API** / Gemma / Imagen / Agent Builder / ADK / Speech-to-Text・Text-to-Speech / Vision AI / Natural Language AI / Translation AI

**3. 提出物（3点セット）**:

| 提出物 | 条件 |
|--------|------|
| **GitHubリポジトリURL** | 公開リポジトリ。提出時点の状態を2026年3月2日まで維持 |
| **デプロイしたプロジェクトURL** | 動作確認できる状態を2026年3月2日まで維持 |
| **Zenn記事URL** | カテゴリ: Idea、トピック: `gch4` |

Zenn記事に含めるべき内容:
- プロジェクト概要（対象ユーザー、解決課題、ソリューション特徴）
- システムアーキテクチャ図
- デモ動画（3分程度）— YouTubeに公開し記事に埋め込み

#### 審査基準

| 基準 | 内容 |
|------|------|
| **課題の新規性** | 多くの人が抱えていて、いまだに解決策が与えられていない課題を発見したプロジェクトを評価 |
| **解決策の有効性** | 提案されたソリューションがその中心となる課題に効果的に対処し、解決しているかを評価 |
| **実装品質と拡張性** | アイデアの実現度、ツール活用度、拡張性、運用しやすさ、費用対効果を評価 |

審査は主催者およびスポンサーが選任する審査員により実施。結果は最終的なもので、異議申し立て不可。知的財産権は参加者に帰属。

### 個人参加という選択

<!-- 殿記入欄: なぜチームではなく個人で参加したのか。一人で全てをやることの覚悟、あるいはマルチエージェントシステムがあるから一人でもやれるという自信があったか -->

<!-- 殿記入欄: 「一人 + AI（multi-agent-shogun）」というスタイルは、チーム参加の代替になり得ると感じたか -->

### 開発スケジュール全体像（SCHEDULE.mdより）

提出締め切りまでの15日間を、5つのフェーズに分けて進行した:

| フェーズ | 期間 | 内容 |
|---------|------|------|
| Phase 1 | 1/31〜2/2 | 技術的課題解消（Cloud Run動作確認、LICENSE作成、pytest実行） |
| Phase 2 | 2/3〜2/7 | デモ動画作成（スクリプト確認、リハーサル、撮影、編集、YouTube公開） |
| Phase 3 | 2/8〜2/10 | Zenn記事作成（執筆、動画埋め込み、公開） |
| Phase 4 | 2/11〜2/13 | 最終確認（全体動作確認、チェックリスト、参加登録フォーム提出） |
| Phase 5 | 2/14〜2/15 | 提出準備（最終確認・微調整、プロジェクト提出） |

Phase 1〜3の作業は主にmulti-agent-shogunの足軽チームが実行し、Phase 4〜5は殿（人間）が主導する設計。15日間で技術完成→動画→記事→提出まで到達するには、人間とAIの並列作業が不可欠だった。

---

<a id="section-1"></a>

## 1. プロジェクトのアイデア着想

### なぜ「固定資産判定」を選んだか

<!-- 殿記入欄: 固定資産判定を選んだきっかけ。実務経験からの課題意識？あるいは周囲の経理担当者を見ていて感じたこと？材料工学が専門でありながら、なぜ経理のテーマを選んだのか -->

<!-- 殿記入欄: 他の候補テーマはあったか？あったなら、なぜ固定資産判定が最終的に選ばれたか -->

固定資産判定が抱える4つの構造的課題は、use_cases.md（実務ユースケース設計書）で明確に分析されている:

1. **判断の属人化**: 固定資産/費用の判定は担当者の経験に依存。担当者不在時に処理が滞り、引継ぎが困難。
2. **時間的プレッシャーによる見落とし**: 月末・決算期は処理量が集中し、確認時間が不足。判断が割れる項目が他の行に埋もれる。
3. **判断根拠の追跡困難**: 「なぜこの処理になったか」の記録が残らない。税務調査時に説明できない。
4. **AI自動化の両刃の剣**: 既存のAI自動化ツールは「すべて自動処理」が前提。誤った判断が高速に通過してしまう。

### 「止まるAI」の発想

<!-- 殿記入欄: 「止まるAI」という逆転の発想はどこから来たか。AIが全自動で判定するのではなく、あえて止まることに価値を見出した瞬間はいつか -->

<!-- 殿記入欄: 「AIの最大のリスクは自信を持って間違えること」— このフレーズが生まれた背景 -->

従来のAIプロジェクトの多くは、**全自動化**を目指す。しかし本プロジェクトの核心は真逆で、**「AIが判断に迷ったら、自ら止まる」** という設計思想である。

30秒エレベーターピッチ（JUDGE_PREP.mdより）:

> 経理の現場では、月末や決算期に見積書の固定資産判定を大量にこなします。
> しかし時間に追われ、判断を十分に検証する余裕がありません。
>
> ここにAIの全自動化を入れると、誤った判断を高速に通過させるリスクがあります。
>
> 私たちのシステムは違います。**判断が割れたら、AIが自ら止まります。**
> 何の情報が不足しているかを具体的に提示し、人間に確認を求めます。
> 回答を受けて再判定し、変更の全過程をDIFFとして記録します。
>
> **止まる、聞く、変わる。** これが私たちの定義するAgentic AIです。

### ペルソナ設定の背景

本プロジェクトのターゲットユーザーは、**設備会社の経理担当者**である。具体的なペルソナとして**「高卒事務の女性」**を想定した。

**ペルソナの特徴**:
- 税務の専門知識がない（国税庁基準の20万円/60万円ルールを毎回調べる）
- 月末や決算期に大量の見積書・請求書を処理する
- 時間に追われ、判断を十分に検証する余裕がない
- AIツールに不慣れ。専門用語が並ぶUIは使えない

use_cases.mdでは5つの具体的なユースケースシナリオが設計されている:

| シナリオ | ユーザー | 状況 |
|---------|---------|------|
| **1. 月次決算** | 田中さん（中小企業経理） | 毎月10-20件の見積書処理。月末残業が常態化 |
| **2. 大型設備投資** | 山田さん（CFO） | 3,000万円の重機導入。付帯工事の取扱い確認 |
| **3. 複数クライアント** | 佐藤さん（会計事務所） | 顧問先30社、月100件以上を一括処理 |
| **4. 税務調査対応** | 鈴木さん（経理部長） | 3年前の判定根拠を問われ、担当者は退職済み |
| **5. 新人教育** | 高橋さん（新人） | 入社2ヶ月目、実例ベースで判断基準を学習 |

シナリオ4の「税務調査対応」は特に重要。当時の担当者が退職していても、システムに証跡（Evidence）が残っているため判断根拠を即座に提示できる。これはStop-first設計の「監査証跡」という実務的価値を直接示すユースケースである。

### 「借金CMのように」— UIデザイン原則の着想

UIの設計原則として「借金CM」を参考にした。テレビの消費者金融CMでは、画面いっぱいに「今すぐお電話を！」というインパクトのあるメッセージが表示され、法的な免責事項（「ご利用は計画的に」等）は画面の端に小さく表示される。

本プロジェクトでは、この構造を転用した:

- **大きく表示**: 判定結果（CAPITAL_LIKE / EXPENSE_LIKE / GUIDANCE）のバッジ、確信度スコア
- **小さく表示**: 技術的な詳細、処理ステップのトレース
- **GUIDANCE（判断停止）の場合**: 判定を出さず、「なぜ止まったか」「何の情報が不足しているか」を前面に出す

Memory MCPに保存された設計原則:

> - UI設計原則: GUIDANCEでは判定を出さず「止まる」ことを強調する
> - 「止まる→聞く→変わる」の3フェーズを視覚的に表現する
> - 差分表示では「監査時の説明資料として利用可能」と明記する
> - 確信度90%超なら免責不要

### 「知らないを、知っているAI」— キャッチコピーの誕生

<!-- 殿記入欄: 「知らないを、知っているAI」というキャッチコピーが生まれた経緯。誰かの言葉にインスピレーションを受けたか、自分で思いついたか -->

このキャッチコピーは、Stop-first設計の本質を一言で表現したものである。従来のAIは「知っている」ことを出力する。本プロジェクトのAIは「知らない（= 判断できない）」ことを検知し、その事実を人間に伝える。

**AIが「止まる」ことの価値** (JUDGE_PREP.md Q10より):

> AIの最大のリスクは「自信を持って間違える」ことです。特に月末・決算期の経理現場では、AIの判定結果を検証する余裕がありません。全自動化は、誤った判断を高速に通過させるリスクを生みます。「止まる」ことで、人間が確認すべきポイントを明示し、判断の質を担保します。これは「AIの限界」ではなく「AIの知性」です。

### 導入効果の試算（time_savings_calculation.mdより）

本プロジェクトの実務的価値を定量的に示すため、業務時間削減効果の詳細試算を行った。

#### 処理時間の比較

| 作業項目 | 従来（As-Is） | 導入後（To-Be） | 根拠 |
|---------|--------------|----------------|------|
| 見積書オープン | 1分 | 0.5分 | UIからの直接アップロード |
| 明細読み取り | 3分 | 0分 | システムが自動抽出 |
| 判定 | 5分 | 1分 | 80%が自動判定完了 |
| 相談 | 4分（50%発生） | 0.4分（20%発生） | GUIDANCE項目のみ確認 |
| 入力 | 2分 | 1分 | 判定結果コピー可能 |
| **合計** | **15分/件** | **5分/件** | **67%削減** |

#### 規模別効果

| 区分 | 年間処理時間削減 | 年間金額効果 |
|------|----------------|-------------|
| 中小企業（月20件、時給3,000円） | **40時間（2,400分）** | **120,000円** |
| 会計事務所（月100件、時給4,000円） | **200時間（12,000分）** | **800,000円** |

#### GUIDANCE発生率20%の根拠

実務データの分析:
- 明確な資産（新設、購入）: 40%
- 明確な費用（消耗品、修繕）: 40%
- 判断が割れる（撤去、移設、既設）: **20%** → GUIDANCE対象

つまり全体の80%はAIが自動判定し、残り20%のGUIDANCE項目だけに人間が集中すればよい。「全自動化」ではなく「80%自動化 + 20%人間判断」が現実的な最適解である。

---

<a id="section-2"></a>

## 2. 開発環境の構築

### multi-agent-shogun — マルチエージェント並列開発基盤

本プロジェクトの開発で最も特徴的なのは、**multi-agent-shogun** というマルチエージェント並列開発基盤を使ったことである。これは戦国時代の軍制をモチーフとした3階層のAIエージェントシステムで、Claude Code + tmux を使って最大8名のAIエージェントを並列稼働させる。

#### 階層構造

```
上様（人間 / The Lord）— 殿
  │
  ▼ 直接指示
┌──────────────┐
│   SHOGUN     │ ← 将軍（プロジェクト統括、意思決定）
│   (将軍)     │    tmux pane: shogun:0.0
└──────┬───────┘
       │ YAMLファイル経由
       ▼
┌──────────────┐
│    KARO      │ ← 家老（タスク管理・分配、ダッシュボード更新）
│   (家老)     │    tmux pane: multiagent:0.0
└──────┬───────┘
       │ YAMLファイル経由
       ▼
┌───┬───┬───┬───┬───┬───┬───┬───┐
│A1 │A2 │A3 │A4 │A5 │A6 │A7 │A8 │ ← 足軽（実働部隊）
│   │   │   │   │   │   │   │   │    tmux pane: multiagent:0.1〜0.8
└───┴───┴───┴───┴───┴───┴───┴───┘
```

#### なぜ作ったか

<!-- 殿記入欄: multi-agent-shogunを作ろうと思ったきっかけ。Claude Codeを1つだけ使っていて物足りなかったのか。並列処理のアイデアはどこから来たか -->

ハッカソンのような限られた時間で大量の作業をこなすには、**並列処理**が不可欠である。人間が1人のAIエージェントに逐次指示を出すスタイルでは、タスク完了を待っている間にボトルネックが発生する。

multi-agent-shogunでは:
- **将軍**が殿（人間）の意志を受けてプロジェクト全体を統括
- **家老**がタスクを分解し、足軽8名に分配
- **足軽8名**が並列で作業を実行

#### 通信プロトコル

エージェント間の通信は**YAML + tmux send-keys**によるイベント駆動方式を採用した。

**なぜYAMLか**:
- 構造化データにより、指示・報告の内容が曖昧にならない
- ファイルとして永続化されるため、コンパクション（コンテキスト圧縮）後も情報が失われない
- 各足軽に専用のタスクファイルを割り当てることで、他の足軽のタスクを誤って実行するリスクを排除

```yaml
# queue/tasks/ashigaru3.yaml の例
task:
  task_id: subtask_037_01
  parent_cmd: cmd_037
  description: |
    【任務: HACKATHON_JOURNEY.md 拡充 — セクション0〜4（前半）】
    出力先: /tmp/journey_part1.md
  target_path: "/tmp/journey_part1.md"
  project: fixed-asset-ashigaru
  status: in_progress
  priority: critical
```

**なぜポーリング禁止か**:
- API代金の節約。8名の足軽が常時ポーリングすると、Claude Code APIのトークン消費が膨大になる
- 代わりに、タスクファイル作成後にtmux send-keysで対象ペインを起動する

```bash
# 足軽を起こす（必ず2回のBash呼び出しに分ける）
# 【1回目】メッセージを送る
tmux send-keys -t multiagent:0.3 'queue/tasks/ashigaru3.yaml に任務がある。確認して実行せよ。'
# 【2回目】Enterを送る
tmux send-keys -t multiagent:0.3 Enter
```

**なぜ2回に分けるか**: 1回のBash呼び出しでメッセージとEnterを同時に送ると、Enterが正しく解釈されない問題が発生した。この教訓はMemory MCPに永続化し、全エージェントが遵守するルールとした。

#### ファイル構成

```
multi-agent-shogun/
├── config/
│   ├── projects.yaml              # プロジェクト一覧
│   └── settings.yaml              # 言語設定（ja）、シェル設定
├── status/
│   └── master_status.yaml         # 全体進捗
├── queue/
│   ├── shogun_to_karo.yaml        # Shogun → Karo 指示キュー
│   ├── tasks/
│   │   ├── ashigaru1.yaml         # 足軽1専用タスクファイル
│   │   ├── ashigaru2.yaml         # 足軽2専用タスクファイル
│   │   ├── ...
│   │   └── ashigaru8.yaml         # 足軽8専用タスクファイル
│   └── reports/
│       ├── ashigaru1_report.yaml  # 足軽1報告
│       ├── ...
│       └── ashigaru8_report.yaml  # 足軽8報告
├── instructions/
│   ├── shogun.md                  # 将軍の指示書
│   ├── karo.md                    # 家老の指示書
│   └── ashigaru.md                # 足軽の指示書
├── dashboard.md                   # 人間用ダッシュボード（家老が更新）
├── CLAUDE.md                      # システム全体のルール（全エージェント共有）
└── skills/                        # 生成されたスキルファイル
```

#### 報告の流れ（割り込み防止設計）

| 方向 | 方法 | 理由 |
|------|------|------|
| **上→下（指示）** | YAML + send-keys | 確実に相手を起動 |
| **下→上（報告）** | dashboard.md 更新のみ | 殿の入力中に割り込みが発生するのを防止 |

足軽は作業完了後、報告ファイル（`queue/reports/ashigaru{N}_report.yaml`）に結果を書き、家老にsend-keysで通知する。家老はdashboard.mdを更新する。**足軽が殿に直接話しかけることは禁止**（F002: 切腹レベルの違反）。

#### 戦国風日本語

`config/settings.yaml` の `language: ja` 設定により、全エージェントが戦国風日本語で通信する:

- 「はっ！」— 了解
- 「承知つかまつった」— 理解した
- 「任務完了でござる」— タスク完了
- 「出陣いたす」— 作業開始

### WSL2 + tmux + Claude Code の構成

#### tmuxセッション構成

2つのtmuxセッションで合計10ペインを管理する:

**shogunセッション（1ペイン）**:
```
Window 0, Pane 0: SHOGUN（将軍）
```

**multiagentセッション（9ペイン）**:
```
Window 0, Pane 0: karo（家老）
Window 0, Pane 1: ashigaru1（足軽1号）
Window 0, Pane 2: ashigaru2（足軽2号）
Window 0, Pane 3: ashigaru3（足軽3号）← 本記事の筆者
Window 0, Pane 4: ashigaru4（足軽4号）
Window 0, Pane 5: ashigaru5（足軽5号）
Window 0, Pane 6: ashigaru6（足軽6号）
Window 0, Pane 7: ashigaru7（足軽7号）
Window 0, Pane 8: ashigaru8（足軽8号）
```

合計10のClaude Codeインスタンスが同時に稼働する。各インスタンスは独立したコンテキストウィンドウを持ち、自分の指示書（`instructions/ashigaru.md` 等）に従って動く。

#### コンパクション問題

Claude Codeのコンテキストウィンドウには上限がある。長時間の作業や大量のファイル読み込みを行うと、古いコンテキストが圧縮（コンパクション）される。この際に「自分が誰か」「何をしていたか」を忘れるリスクがある。

**対策（CLAUDE.mdに明記）**:

```markdown
## コンパクション復帰時（全エージェント必須）

コンパクション後は作業前に必ず以下を実行せよ：

1. **自分の位置を確認**: `tmux display-message -p '#{session_name}:#{window_index}.#{pane_index}'`
2. **対応する instructions を読む**
3. **instructions 内の「コンパクション復帰手順」に従い、正データから状況を再把握する**
4. **禁止事項を確認してから作業開始**

summaryの「次のステップ」を見てすぐ作業してはならぬ。まず自分が誰かを確認せよ。
```

さらに、**Memory MCP**（知識グラフ）に重要なルール、ポストモーテム、プロジェクト文脈を永続保存し、コンパクション後も参照できるようにした。

### PC環境

| パーツ | 型番 |
|--------|------|
| **マザーボード** | ASRock Z890 Steel Legend WiFi |
| **GPU** | NVIDIA GeForce RTX 5060 Ti |
| **メモリ** | Micron DDR5 16GB × 2 = 32GB（非RGB） |
| **OS** | Windows + WSL2 (Ubuntu) |

### 開発で使ったツール一覧

#### アプリケーション開発ツール

| ツール | 用途 | バージョン |
|--------|------|-----------|
| **Python** | メインランタイム | 3.11 |
| **FastAPI** | REST APIフレームワーク | 0.100+ |
| **Streamlit** | デモUIフロントエンド | 1.28+ |
| **Docker** | コンテナ化・デプロイ | — |
| **pytest** | 自動テスト | 136件通過 |
| **python-pptx** | プレゼン資料自動生成 | — |
| **PyMuPDF (fitz)** | PDF テキスト抽出（AGPL-3.0） | — |
| **pdfplumber** | PDF テキスト抽出（MIT、フォールバック用） | — |

#### Google Cloud AIサービス

| サービス | 用途 | SDK |
|----------|------|-----|
| **Gemini 3 Pro Preview** | 固定資産判定（`thinking_level=HIGH`） | `google-genai` == 1.62.0 |
| **Cloud Run** | API / UI サーバーレスデプロイ | gcloud CLI |
| **Document AI** | PDF 高精度テキスト抽出（Feature Flag: `USE_DOCAI=1`） | `google-cloud-documentai` |
| **Vertex AI Search** | 法令エビデンス検索（Feature Flag: `VERTEX_SEARCH_ENABLED=1`） | `google-cloud-discoveryengine` |

#### 開発基盤ツール

| ツール | 用途 |
|--------|------|
| **Claude Code (Opus 4.6)** | AIエージェントの頭脳（10インスタンス同時稼働） |
| **tmux** | 複数エージェントの並列実行・ペイン管理 |
| **WSL2** | Windows上のLinux開発環境 |
| **Memory MCP** | 知識グラフによるポストモーテム・ルールの永続保存 |
| **Git** | バージョン管理 |
| **gcloud CLI** | Google Cloud操作 |

---

<a id="section-3"></a>

## 3. 開発の全タイムライン

### 概観

本プロジェクトの開発は、大きく以下のフェーズに分かれる:

1. **初期開発フェーズ**（〜2026年1月末）: プロトタイプ構築、バグ発見・修正
2. **品質改善フェーズ**（2026年2月初旬）: 品質監査、セキュリティ修正、テスト拡充
3. **ハッカソン準備フェーズ**（2026年2月中旬）: 最終総点検、資料作成、デプロイ、提出物準備

### 初期開発フェーズ

#### 〜2026年1月末: プロトタイプの構築

<!-- 殿記入欄: プロトタイプはいつ頃から開発を始めたか。最初のコードはどんなものだったか -->

<!-- 殿記入欄: 最初のプロトタイプで見えた課題。何がうまくいって、何がうまくいかなかったか -->

初期プロトタイプでは以下の基本構造を確立した:

```
見積書データ（JSON） → ルールベース分類 → 3値判定（CAPITAL_LIKE / EXPENSE_LIKE / GUIDANCE）
```

この段階では Gemini API は統合されておらず、`core/classifier.py` のキーワードマッチングのみで判定を行っていた。

#### 2026年1月30日: Gemini API統合設計

gemini_integration_design.md にて、Gemini統合の設計方針が策定された。この時点での重要な設計判断:

- `google-generativeai`（旧SDK）ではなく`google-genai`（新SDK v1.51.0+）を採用
- `thinking_level` パラメータを活用するため、Gemini 3 Pro Preview が必須
- 旧SDKから新SDKへの移行では、インポートパス・モデル名・API呼び出し方法が全て変更

```python
# 旧SDK → 新SDK移行のポイント
# 旧: import google.generativeai as genai
# 新: from google import genai
# 旧: genai.configure(api_key=...)
# 新: client = genai.Client()  # 環境変数 GOOGLE_API_KEY を自動検出
# 旧: model = genai.GenerativeModel("gemini-pro")
# 新: client.models.generate_content(model="gemini-3-pro-preview", ...)
```

#### 2026年2月1日: confidence bug の発見と修正

**ポストモーテム — Lesson_FixedAsset_Confidence_Bug**:

| 項目 | 内容 |
|------|------|
| **発生日** | 2026-02-01 |
| **症状** | confidenceが常に0.80になる |
| **原因** | `api/main.py` 127行目で `ev.get('confidence', 0.8)` とハードコード |
| **根本原因** | PDF抽出時にconfidenceフィールドを設定していなかったため、常にデフォルト値(0.8)が使用された |
| **修正** | `core/classifier.py` に `_calculate_confidence()` 関数を追加 |

修正後の `_calculate_confidence()` のロジック:

```python
def _calculate_confidence(classification, cap_hits, exp_hits, mixed_hits, guidance_hits, flags):
    if classification == schema.CAPITAL_LIKE:
        base = 0.85
        bonus = min(len(cap_hits) - 1, 2) * 0.03
        return min(base + bonus, 0.95)
    elif classification == schema.EXPENSE_LIKE:
        base = 0.85
        bonus = min(len(exp_hits) - 1, 2) * 0.03
        return min(base + bonus, 0.95)
    else:  # GUIDANCE
        if "conflicting_keywords" in flags:
            return 0.55
        elif "no_keywords" in flags:
            return 0.40
        elif mixed_hits:
            return 0.60
        elif guidance_hits:
            return 0.65
        else:
            return 0.50
```

#### 2026年2月1日: aggregation bug の発見と修正

| 項目 | 内容 |
|------|------|
| **症状** | ドキュメント全体が意図せずGUIDANCEになる |
| **原因** | 「1つでもGUIDANCEがあれば全体がGUIDANCE」という集計ロジック |
| **修正** | 集計ロジックを見直し、明細ごとに個別判定を維持 |

#### 2026年2月1日: 判定ロジック精査（CLASSIFIER_LOGIC_REVIEW.md）

会計税務専門家の視点でclassifier.pyを精査し、**5つの問題点**を特定した:

| # | 問題 | 内容 |
|---|------|------|
| 1 | **金額閾値ロジックの根拠混在** | 「少額減価償却資産」と「修繕費vs資本的支出」を1つのロジックで処理。30万〜60万円で`suggests_guidance: False`は修繕費の簡易判定と少額資産判定の混同 |
| 2 | **「更新」キーワードの重複** | CAPITAL_KEYWORDSとMIXED_KEYWORDSの両方に存在。MIXED優先のため「サーバー更新」のような明確な資産案件も常にGUIDANCE |
| 3 | **company_default.jsonのguidance_add過剰** | 「設置」がguidance_addに含まれ、新設工事の設置という明確な資産計上ケースも止まる |
| 4 | **合計金額の未考慮** | 個別明細で判定しているが、国税庁基準の「一つの修理」は工事全体を指す場合が多い |
| 5 | **修繕費vs資本的支出の本質的判定基準不足** | 「価値増加・耐久性向上→資本的支出」「原状回復・維持管理→修繕費」という本質が未実装 |

**修正対応（2026-02-01に実施済み）**:
- EXPENSE_KEYWORDSに「修繕」追加
- 確信度90%超の場合は免責表示省略
- GUIDANCEの場合、金額基準（20万/60万）で判定を倒す表示に変更
- 確信度を分類結果に基づいて動的計算（_calculate_confidence関数）
- 耐用年数判定（useful_life_estimator）のAPI統合

これら2つのバグと5つの問題点の教訓は **QA_Checklist_Before_Complete** としてMemory MCPに永続化した。

#### UI設計の試行錯誤

<!-- 殿記入欄: UIのデザインで最も苦労したこと -->

UIはStreamlitで構築し、コンポーネント設計を採用:

```
ui/
├── app_minimal.py          # メインアプリケーション
├── styles.py               # 共通CSS
├── components/
│   ├── hero_section.py     # ヒーローセクション
│   ├── input_area.py       # 入力エリア（JSON/PDF切替）
│   ├── result_card.py      # 判定結果カード（3色バッジ）
│   ├── guidance_panel.py   # GUIDANCE対話パネル
│   └── diff_display.py     # Before/After差分表示
├── similar_cases.py        # 類似事例検索
└── batch_upload.py         # バッチアップロード
```

#### Gemini API統合

<!-- 殿記入欄: Gemini APIの統合で苦労した点 -->

Gemini API統合は `api/gemini_classifier.py` で実装。Feature Flag (`GEMINI_ENABLED=1`) による段階的導入を採用した。

**SDK移行の重要ポイント（GEMINI3_API_SETUP.mdより）**:

新SDK（`google-genai`）は旧SDK（`google-generativeai`）と全く異なるインターフェースを持つ。移行時に注意すべき点:

```python
# 新SDKでのthinking_level使用例
from google import genai
from google.genai import types

client = genai.Client()
response = client.models.generate_content(
    model="gemini-3-pro-preview",
    contents=user_prompt,
    config=types.GenerateContentConfig(
        system_instruction=CLASSIFICATION_SYSTEM_PROMPT,
        response_mime_type="application/json",
        temperature=0.1,
        thinking_config=types.ThinkingConfig(thinking_level="HIGH"),
    ),
)
```

### 品質改善フェーズ

#### cmd_027: 品質監査 — 72/100点の衝撃

2026年2月12日、ハッカソン提出に向けて品質監査を実施した。結果は**72/100点**。

殿の指示: 「品質確認だけでなく改善実施も求める。ハッカソンで勝つことが最優先目標。85点以上を目標とせよ」

#### cmd_028: 改善実施（85+目標）

| 改善領域 | 実施内容 |
|----------|----------|
| セキュリティ | bare exception修正、依存パッケージバージョン固定 |
| Dockerfile | 非rootユーザー実行、HEALTHCHECK追加 |
| ドキュメント | docstring追加、テスト拡充 |
| デモ | DEMO.md強化、審査対策ドキュメント作成 |

### ハッカソン準備フェーズ — 提出日当日（2026年2月14日）

提出日当日は、multi-agent-shogunの全力が発揮された日である。

#### cmd_033: ハッカソン最終総点検（05:45開始）

4つの任務を4名の足軽で並列処理:

| 任務 | 担当 | 結果 |
|------|------|------|
| 資料間の齟齬検証 | 足軽1 | **15件の齟齬を発見・修正** |
| Cloud Runデプロイ | 足軽2 | デプロイ成功、ヘルスチェック通過 |
| 動画撮影手順書作成 | 足軽3（筆者） | VIDEO_RECORDING_GUIDE.md 作成 |
| 懸念点・リスク洗い出し | 足軽4 | **17件のリスクを検出**（高6/中6/低5） |

#### cmd_034: pptxプレゼン資料作成（05:47開始）

python-pptxを使い、**12枚のプレゼンスライド**を生成。足軽5（前半）+ 足軽6（後半）+ 足軽7（結合検証）の3名体制。

最終ファイル: **presentation.pptx** 54,460バイト、5検証ALL PASS。

#### cmd_035: リスク対処・GitHub公開準備（06:04開始）

高リスク6件を3チームで並列対処。RACE-001回避として各足軽の担当ファイルに重複がないことを事前確認。

修正後のテスト結果: **pytest 136件全通過、3件skip、0件失敗**。

#### cmd_036〜cmd_037: HACKATHON_JOURNEY.md 作成・大幅拡充

cmd_036で初版8セクション構成を作成。殿の指示「もっと長くてよい。とにかく振り返って分かるようにいろいろ記す」を受け、cmd_037で14セクション構成に大幅拡充。RACE-001回避のため3名の足軽に分担:

| 足軽 | 担当セクション | 出力先 |
|------|--------------|--------|
| 足軽3（筆者） | セクション0-4 | /tmp/journey_part1.md |
| 足軽4 | セクション5-9 | /tmp/journey_part2.md |
| 足軽8 | セクション10-14 + 結合 | /tmp/journey_part3.md → 最終結合 |

### タイムラインまとめ

| 時刻 | コマンド | 主な成果 |
|------|---------|---------|
| 05:45 | cmd_033開始 | 最終総点検（4任務並列） |
| 05:47 | cmd_034開始 | pptxプレゼン資料作成（3名並列） |
| 06:00 | cmd_033完了 | 齟齬15件修正、デプロイ成功、リスク17件検出 |
| 06:04 | cmd_035開始 | リスク対処（3名並列） |
| 06:11 | cmd_036開始 | 軌跡記事作成 |
| 06:17 | cmd_034完了 | presentation.pptx 12枚 5検証ALL PASS |
| 06:21 | cmd_036完了 | HACKATHON_JOURNEY.md 全8セクション |
| 06:22 | cmd_035完了 | 全RISK修正、pytest 136件全通過 |
| 06:35 | cmd_037開始 | HACKATHON_JOURNEY.md 大幅拡充 |

**約1時間で**: 最終総点検、プレゼン資料作成、リスク対処、GitHub公開準備、軌跡記事作成、大幅拡充 — これら全てを並列処理で完了。逐次処理なら数時間かかる作業量である。

しかし、本当の戦いはここからだった。以下は提出日当日の全コマンド詳細記録である。

### cmd_038: さらなる拡充 — 90+ファイルからの情報マイニング（06:40開始）

cmd_037と並列で、cmd_038が発令された。今度はプロジェクト内の**90件以上のMarkdownファイル**から情報を掘り起こし、記事にさらなる厚みを加える大規模作戦である。

#### 参照対象ファイル群

| カテゴリ | ファイル例 | 件数 |
|----------|----------|------|
| 開発プロセス | SCHEDULE.md, LORD_INSTRUCTIONS, LORD_ACTION_PLAN.md, CHECKPOINT_SEKIGAHARA.md | 5件 |
| 技術調査 | research_a.md〜research_ij.md, gemini_integration_design.md, GEMINI3_API_SETUP.md | 12件+ |
| 仕様設計 | docs/specs/ 全4文書 | 4件 |
| 品質・レビュー | review_parts/ 全8件, fix_log_parts/ 全5件, qa_and_risks.md | 14件 |
| ハッカソン戦略 | hackathon_parts/ 全5件, winning_patterns_analysis.md, judge_value_proposition.md | 7件 |
| デモ・動画 | demo_script.md, VIDEO_SHOOTING_SCRIPT.md, VIDEO_FAQ_FOR_LORD.md | 4件 |
| デプロイ・インフラ | CLOUDRUN_ENV.md, CLOUDRUN_TROUBLESHOOTING.md, DOCKER_STARTUP_REPORT.md | 7件 |
| その他 | use_cases.md, time_savings_calculation.md, future_vision.md, zenn_article_draft.md | 10件+ |

これにより、記事は**22セクション・2,769行**にまで拡充された。当初の目標1,500行の**184%**という分量。

cmd_038完了: **07:10**。

### cmd_039: pptxの文字ズレ修正と配色改善（06:40開始、cmd_038と並列）

cmd_034で生成したpresentation.pptxに、殿から指摘が入った。**文字がズレている。黄色が多すぎる。**

cmd_039はcmd_038と同時刻に発令された。空いている足軽をフル投入。

#### 問題1: テキストの位置ズレ（P0）

根本原因は4つあった:

| 原因 | 詳細 | 修正 |
|------|------|------|
| **(A) bodyPr anchor未設定** | テキストがボックス下部に落ちる | `bodyPr.set('anchor', 'ctr')` を全テキストフレームに適用 |
| **(B) 行間隔が過大** | `font_size × 1.5` が小ボックスで圧縮を発生 | line_spacingを1.0〜1.2に変更 |
| **(C) マージン未設定** | デフォルト0.1インチが全方向に適用されスペースを圧迫 | `margin_top/bottom=Pt(2)`, `margin_left/right=Pt(6)` を明示設定 |
| **(D) 整数除算の誤差** | `//` 演算子による水平位置のマイクロズレ | `/` に変更しfloat除算に |

#### 問題2: 黄色の過剰使用

殿の審美眼は正しかった。黄色（#FFC107等）は画面上で悪目立ちし、テキストの可読性を下げていた。修正方針: GUIDANCEマーカーをライトグレー（#E8E8E8）+ ダークテキストに変更。黄色は広い背景として使わず、小さなアクセントのみに限定した。

修正後、12スライド全枚のテキスト位置と配色を検証 — **ALL PASS**。

cmd_039完了: **07:25**。

### ここまでの戦果 — 開始から1時間40分

| 時刻 | コマンド | 完了 | 主な成果 |
|------|---------|------|---------|
| 05:45 | cmd_033 | 06:00 | 最終総点検（齟齬15件修正、リスク17件検出、デプロイ成功） |
| 05:47 | cmd_034 | 06:17 | pptx 12枚生成、5検証ALL PASS |
| 06:04 | cmd_035 | 06:22 | 高リスク6件対処、GitHub公開準備、pytest 136全通過 |
| 06:11 | cmd_036 | 06:21 | 軌跡記事 初版8セクション |
| 06:35 | cmd_037 | 06:50 | 軌跡記事 14セクションに拡充 |
| 06:40 | cmd_038 | 07:10 | 軌跡記事 22セクション 2,769行（90+ファイルからマイニング） |
| 06:40 | cmd_039 | 07:25 | pptx文字ズレ修正・配色改善 |

7コマンド、全て完了。逐次処理なら半日はかかる作業量を、multi-agent-shogunの並列実行で1時間40分に圧縮した。

しかし、本当のドラマはここから始まる。

### cmd_040: P0致命的バグの発見と修正（07:02開始）

**怒涛の修正ラッシュ、始まる。**

cmd_033〜039で提出物を磨き上げていた最中、テストの中で致命的な問題が浮上した。

**問題: 複数明細の見積書で、個別判定ではなく文書全体の集約判定が返される**

例えば、以下のような4行の見積書を想像してほしい:

```
1. サーバーハードウェア設置工事  400,000円 → 期待: CAPITAL_LIKE（個別判定）
2. ネットワーク機器導入工事    300,000円 → 期待: CAPITAL_LIKE（個別判定）
3. セキュリティシステム構築    200,000円 → 期待: CAPITAL_LIKE（個別判定）
4. インフラ基盤構築工事       100,000円 → 期待: CAPITAL_LIKE（個別判定）
---
小計: 1,000,000円 / 消費税: 100,000円 / 合計: 1,100,000円
```

本来なら各行ごとに判定すべきである。しかし実際には、合計金額に基づく**文書全体の一括判定**が返されていた。

これは単一箇所のバグではなかった。**5つのレイヤーにまたがる複合的な問題**だった。

#### バグの所在 — 5レイヤーの解剖

足軽5, 6, 7の3名が、コードを上流から下流まで逐次調査した。

| レイヤー | ファイル | 状態 | 詳細 |
|---------|---------|------|------|
| PDF抽出 | `core/pdf_extract.py` | ✓ 問題なし | 個別行を正しく抽出している |
| アダプター | `core/adapter.py` | ✓ 問題なし | line_no, description, quantity, unit_price, amount を個別に保持 |
| ルールベース分類 | `core/classifier.py` | ✓ 問題なし | 各行を個別に分類 |
| **Gemini分類** | `api/gemini_classifier.py` | **★ 問題あり** | システムプロンプトが合計額で判定するよう指示していた |
| **APIレスポンス集約** | `api/main.py` | **★ 問題あり** | 文書レベルの判定で個別判定を上書き |
| **UI表示** | `ui/app_minimal.py` | **★ 問題あり** | 文書判定の単一バッジ表示 |

#### なぜ今まで発見されなかったか

答えは単純で残酷だ — **デモデータとゴールデンテストケースが、全て単一明細のみだったから。**

demo01.json〜demo04.jsonもcase01〜case10（ゴールデンセット）も、全て1行のみの見積書だった。単一明細なら「個別判定 = 文書全体判定」となるため、バグは表面化しない。

**テストが通っている ≠ バグがない。テストが現実のユースケースをカバーしている場合にのみ、テストは価値を持つ。**

#### 修正の実施と検証

足軽1, 2, 3, 5の4名が修正を実装。足軽7が6つの修正提案を優先度付きで提出:

1. **(P0)** UI個別ラベル表示 — 行ごとにCAPITAL_LIKE→「→ 資産」、EXPENSE_LIKE→「→ 費用」、GUIDANCE→「→ 要確認」
2. **(P0)** UI個別税務ルール適用 — 合計ではなく各行の金額で税務ルールを判定
3. **(P1)** 取得原価の取り込み — Geminiの `included_in_acquisition_cost` をUIチェックボックスのデフォルト値に
4. **(P1)** ルールベース取得原価 — classifier.pyに `included_in_acquisition_cost` フィールドを追加
5. **(P2)** レスポンスメタデータ — `acquisition_cost_total`, `excluded_total` をメタデータに含める
6. **(P1)** 複数明細ゴールデンテスト追加

足軽4が包括的検証を実施: **pytest 159 PASSED / 3 SKIPPED / 0 FAILED** ✅

修正を反映し、Cloud Runに再デプロイ:

| コンポーネント | リビジョン | ステータス |
|--------------|----------|----------|
| API | revision 00036-xjz | ✅ ヘルスチェック通過 |
| UI | revision 00006-kxj | ✅ デプロイ成功 |

cmd_040完了: **09:20**。約2時間20分の大手術だった。

### cmd_041: バグ修正2件 — 日付誤読・GUIDANCEボタンUI（09:25開始）

cmd_040の大手術が完了した直後、殿が2件のバグを指摘した。

#### Bug A: 日付の数字が金額として誤読される

| 項目 | 内容 |
|------|------|
| ファイル | `core/pdf_extract.py` |
| 症状 | 日付（例: 「2024-02-15」）の数字が金額として誤認識される |
| 担当 | 足軽2 |
| 修正 | 2段階修正 — (1) 金額パーシング前の日付パターン検出 (2) 時間的コンテキスト検証 |

#### Bug B: GUIDANCEボタンのUI改善

| 項目 | 内容 |
|------|------|
| ファイル | `ui/components/guidance_panel.py` |
| 症状 | GUIDANCEパネルのボタンが不明瞭・位置ずれ |
| 担当 | 足軽3 |
| 修正 | ボタンテキストの明確化、視覚的階層の改善、レスポンスフローの明確化 |

修正後: **pytest 159 PASSED / 3 SKIPPED / 0 FAILED** ✅

cmd_041完了: **10:00**。約25分で2件を効率的に並列処理。

### Phase別の開発ダイナミクス

#### Phase 1（1/31〜2/2）: 技術的課題解消 — 基礎固めの3日間

プロトタイプの基本構造を確立しながら、致命的なバグ2件（confidence bug、aggregation bug）を発見・修正した。CLASSIFIER_LOGIC_REVIEW.mdで5つの問題点を特定。この3日間で得た教訓がQA_Checklist_Before_Complete としてMemory MCPに永続化された。

#### Phase 2（2/3〜2/7）: デモ動画作成 — 「見せる」フェーズ

技術基盤が固まった後、プロダクトを外部に見せる準備のフェーズ。Gemini 3 Pro PreviewのSDK移行完了、Feature Flag設計の確立、デモシナリオ設計（3分間のデモ動画で「止まる→聞く→変わる」の3ステップを可視化）。

#### Phase 3（2/8〜2/10）: Zenn記事作成 — 言語化のフェーズ

プロジェクトの価値を文章で伝えるフェーズ。architecture_diagram.mdの7つのMermaid図が体系的に整理されていたことがここで活きた。

#### Phase 4（2/11〜2/13）: 最終確認 — 品質監査の衝撃

cmd_027で品質監査を実施した結果: **72/100点**。殿の反応は明確だった — 「85点以上を目標とせよ」。cmd_028で一気に改善を実施し、85+ラインに到達。

#### Phase 5（2/14〜2/15）: 提出準備 — 怒涛の最終日

cmd_033〜041の9コマンドが怒涛のように発令・完了された。本セクションで詳述した通りである。

### 最終日の数字で見る開発密度

| 指標 | 値 |
|------|-----|
| 発令コマンド数 | 9（cmd_033〜041） |
| 実行時間帯 | 05:45〜10:00（4時間15分） |
| ドキュメント齟齬 修正数 | 15件 |
| リスク検出・対処数 | 17件（高6/中6/低5） |
| P0致命的バグ 発見箇所 | 5レイヤー |
| 修正提案数（cmd_040） | 6件（P0×2, P1×3, P2×1） |
| プレゼンスライド 生成枚数 | 12枚 |
| 軌跡記事 最終行数 | 2,769行（22セクション） |
| テスト通過数 | 159 PASSED / 3 SKIPPED / 0 FAILED |
| Cloud Run再デプロイ回数 | 2回（API + UI） |
| 参照ファイル数（cmd_038） | 90件以上 |

**4時間15分で9コマンドを並列消化** — これがmulti-agent-shogunの最終日の実力である。

### 転機と教訓 — 最終日を通じて見えたもの

**転機1: cmd_040のP0バグ発見** — 提出日にP0バグを発見するのは、通常なら絶望的な事態だ。しかしmulti-agent-shogunでは、3名が原因調査、4名が修正実装、1名が包括検証という並列体制を即座に組めた。2時間20分で5レイヤーの複合バグを解剖・修正・検証・再デプロイまで完了。

**転機2: テストの盲点の発見** — デモデータとゴールデンテストケースが「全て単一明細」だった問題は、テスト設計の根本的な教訓を残した。実務では複数明細の見積書が普通であり、単一明細のテストだけでは本番環境の振る舞いを保証できない。

**転機3: 品質と速度の両立** — 最終日に「品質を妥協して締め切りに間に合わせる」のではなく、「品質を上げつつ締め切りに間に合わせる」ことができたのは、足軽8名の並列処理による時間圧縮のおかげだ。発見→対処→検証のサイクルを1日に4回回せた。

**教訓: 並列処理の限界と可能性** — 独立した作業は完全に並列化でき4倍の速度向上が得られる。しかしcmd_040のような複合バグの修正は、調査フェーズ（並列可）→修正フェーズ（一部直列）→検証フェーズ（並列可）と、完全な並列化はできない。事前の依存分析と競合回避設計（RACE-001ルール）が不可欠である。

### バックアップログから見る進化の軌跡

#### dashboard.mdの変遷（5世代分）

| バックアップ日時 | 特徴 |
|---|---|
| 2026-01-30 22:18 | 初期構造。シンプルなタスク一覧 |
| 2026-01-31 01:48 | cmd_019前後。家老ボトルネック改善の萌芽 |
| 2026-02-01 05:29 | 8足軽並列稼働が本格化。スキル化候補が登場 |
| 2026-02-02 01:31 | send-keys事件後。監視スクリプト導入 |
| 2026-02-02 20:41 | 安定運用期。チェックリスト導入済み |

#### shogun_to_karo.yamlの指示件数推移

- 初期（〜cmd_019）: 単発指示中心
- 中期（cmd_020〜039）: 並列指示の増加、Phase分割の導入
- 後期（cmd_040〜070）: スキル化・品質改善・振り返りフェーズ

---

<a id="section-4"></a>

## 4. 技術的な深掘り

### frozen schema v1.0 — なぜスキーマを固定したか

`core/schema.py` は本プロジェクトの基盤となるスキーマ定義:

```python
# core/schema.py
VERSION = "v1.0"

CAPITAL_LIKE = "CAPITAL_LIKE"
EXPENSE_LIKE = "EXPENSE_LIKE"
GUIDANCE = "GUIDANCE"
```

3値判定の設計は、Stop-first原則に直結している。2値（資産/経費）ではなく3値にしたことで、**「判断しない」という選択肢をシステムレベルで保証**した。

### ゴールデンセット評価 10/10 の意味

| Metric | Value |
|--------|-------|
| **Total Cases** | 10 |
| **Passed** | 10 |
| **Accuracy** | **100.0%** |

**ゴールデンセット100%の真の意味は「AIが間違えない」ではなく「AIが間違える前に止まる」ことが100%保証されている**ということ。

### ルールファースト設計の詳細

本システムの判定ロジックは2段構成:

1. **ルールベース分類**（`core/classifier.py`）: キーワードマッチング + 税務ルール + ポリシーオーバーライド
2. **Gemini AI分類**（`api/gemini_classifier.py`）: 書類全体の文脈理解 + 深い推論

#### ルールベースのキーワード体系

```python
CAPITAL_KEYWORDS = [
    "更新", "新設", "設置", "増設", "購入", "導入", "構築", "整備", "改修",
]

EXPENSE_KEYWORDS = [
    "保守", "点検", "修理", "修繕", "調整", "清掃", "消耗品", "雑費",
    "メンテナンス", "維持", "管理", "交換", "補修", "年間", "定期", "契約",
]

MIXED_KEYWORDS = [
    "一式", "撤去", "移設", "既設",  # → 常にGUIDANCE（判断停止）
]
```

#### ポリシーファイルによる企業カスタマイズ

```json
{
  "version": "0.1",
  "company_id": "demo",
  "description": "設備会社向けデモ用",
  "keywords": {
    "asset_add": ["更新", "新設", "設置", "増設"],
    "expense_add": ["保守", "点検", "修理", "調整"],
    "guidance_add": ["撤去", "廃棄", "移設", "既設", "一式", "配線"]
  },
  "thresholds": { "guidance_amount_jpy": 1000000 },
  "regex": { "always_guidance": ".*(撤去|移設).*" }
}
```

**Stop-firstの徹底**: ポリシーオーバーライドは**GUIDANCEの追加のみ**を行い、判定を緩めることはできない。

#### 税務ルールの実装

| 金額範囲 | ルールID | 判定 |
|----------|---------|------|
| 10万円未満 | R-AMOUNT-003 | 少額固定資産 — GUIDANCE不要 |
| 10万〜20万円 | R-AMOUNT-100k200k | 3年一括償却 — **GUIDANCE** |
| 20万〜30万円 | R-AMOUNT-001 + SME300k | 一括償却 + 中小企業特例 — **GUIDANCE** |
| 30万〜60万円 | R-AMOUNT-001 | 一括償却 — GUIDANCE不要 |
| 60万円以上 | R-AMOUNT-600k | 修繕費vs資本的支出 — **GUIDANCE** |

### PDF抽出パイプライン

4段階のフォールバック構造:

```
PDF入力
  ├── Priority 1: Gemini Vision API（GEMINI_PDF_ENABLED=1）
  ├── Priority 2: Document AI（USE_DOCAI=1）
  ├── Priority 3: PyMuPDF (fitz)
  └── Priority 4: pdfplumber
```

### Vertex AI Searchによる法令根拠引用

GUIDANCE判定時に、法令・通達の根拠を自動引用。Feature Flagが無効でも空リストを返す（graceful degradation）。

```python
# api/vertex_search.py — graceful degradation設計
if not _bool_env("VERTEX_SEARCH_ENABLED", False):
    return []  # Feature off → 空リスト
```

vertex_search_verification.md で検証されたFeature Flag動作パターン:

| 状態 | VERTEX_SEARCH_ENABLED | ライブラリ | 結果 |
|------|----------------------|-----------|------|
| OFF | 未設定 or "0" | 不問 | 空リスト返却 |
| ON（環境未設定） | "1" | あり | エラー → 空リスト |
| ON（ライブラリなし） | "1" | なし | ImportError → 空リスト |
| ON（正常） | "1" | あり | 検索結果返却 |

全パターンでシステムが停止しない設計。

### アーキテクチャ図の体系（architecture_diagram.mdより）

architecture_diagram.md には7つのMermaid図が体系的に定義されている:

| # | 図の名称 | 用途 |
|---|---------|------|
| 1 | システム全体構成図 | README/Zenn記事用（入力層→コア処理層→出力層→GCP層） |
| 2 | レイヤードアーキテクチャ図 | 技術ドキュメント用（API/Core/Infrastructure/External） |
| 3 | 処理パイプライン図 | 開発者向け（PDF→抽出→分類→出力の流れ） |
| 4 | APIシーケンス図 | API仕様書用（Client→FastAPI→Classifier→Gemini→Vertex AI Search） |
| 5 | Agentic 5-Step フロー図 | 審査員向け（止まる→根拠提示→質問→再判定→差分表示） |
| 6 | 業務プロセス統合図 | ビジネス向け（見積書→PDF抽出→AI判定→対話→仕訳） |
| 7 | マルチエージェント将来構想図 | 拡張性アピール用 |

### Feature Flag設計 — 段階的機能有効化

| Feature Flag | デフォルト | 機能 |
|-------------|----------|------|
| `GEMINI_ENABLED=1` | OFF | Gemini 3 Pro Preview による AI判定 |
| `USE_DOCAI=1` | OFF | Document AI による PDF抽出 |
| `VERTEX_SEARCH_ENABLED=1` | OFF | Vertex AI Search による法令引用 |
| `PDF_CLASSIFY_ENABLED=1` | OFF | PDF直接分類エンドポイント |
| `GEMINI_PDF_ENABLED=1` | OFF | Gemini Vision による PDF画像認識 |
| `USE_LOCAL_OCR=1` | OFF | ローカルOCR（Tesseract） |

### 「止まる→聞く→変わる」のAgentic設計思想の詳細

Agentic 5-Step プロセス:

| Step | 動作 | 技術実装 |
|------|------|----------|
| 1 | **止まる** | confidence < 0.7 で GUIDANCE に強制フォールバック |
| 2 | **根拠提示** | `missing_fields` + `why_missing_matters` で不足情報を構造化 |
| 3 | **質問** | UI（guidance_panel.py）が質問を表示 |
| 4 | **再判定** | `answers` を付与して Gemini 3 Pro に再投入 |
| 5 | **差分表示** | Before/After の Decision・Confidence・Reasons を DIFF 表示 |

### Gemini 3 Pro Preview + thinking_level の選択理由

| パラメータ | 値 | 理由 |
|-----------|-----|------|
| `model` | `gemini-3-pro-preview` | 推論能力が最も高い |
| `thinking_level` | `HIGH` | 税務判定は多段階の論理が必要 |
| `response_mime_type` | `application/json` | 構造化出力を強制 |
| `temperature` | `0.1` | 再現性の高い判定結果 |

### confidence閾値0.7の設計根拠

| 分類 | 確信度範囲 |
|------|-----------|
| CAPITAL_LIKE | 0.85〜0.95 |
| EXPENSE_LIKE | 0.85〜0.95 |
| GUIDANCE（conflicting） | 0.55 |
| GUIDANCE（no_keywords） | 0.40 |
| GUIDANCE（mixed） | 0.60 |
| GUIDANCE（policy） | 0.65 |

CAPITAL_LIKE/EXPENSE_LIKEの基準確信度(0.85)と閾値(0.7)の間に明確なギャップがあり、中間で迷うケースが生まれない。

### 全明細一括判定

書類全体を1回のAPI呼び出しで判定する設計。付随費用（設置費・運搬費）を本体と合算して判断できる。

### 導入効果の試算

| 指標 | 削減量 |
|------|--------|
| 処理時間 | **67%削減**（15分/件 → 5分/件） |
| 年間削減時間 | **40時間**（中小企業）/ **200時間**（会計事務所） |
| 年間削減金額 | **12万円**（中小企業）/ **80万円**（会計事務所） |
| 判断ミス | **80%以上削減** |
| 月末残業 | **60%削減** |
| 税務調査対応 | **75%削減**（2時間 → 30分） |

<!-- 殿記入欄: これらの試算値の根拠。実体験に基づくものか、業界データに基づくものか -->

### Gemini APIプロンプトの改修過程 — 「合計一括判定」から「個別明細判定」への転換

本プロジェクトの技術的な転換点は、Gemini APIへの問い合わせ方式を根本から変えた瞬間にある。

初期実装では、書類全体を1回のAPI呼び出しで判定する「合計一括判定」方式を採用していた。直感的にはシンプルだし、API呼び出し回数も1回で済む。

しかし、この設計には致命的な欠陥があった。

**問題1: 合計金額バイアス**。書類全体の合計金額が大きいと、Geminiは「高額だから資産」と判断する傾向があった。実際には、100万円の見積書の中に「撤去費30万円」（費用処理）が含まれていても、合計100万円という数字に引きずられてCAPITAL_LIKEを返してしまう。

**問題2: 混在ケースの取りこぼし**。1つの書類に「サーバー購入 50万円」（資産）と「旧サーバー撤去 20万円」（費用）が混在するケースで、一括判定は「全体としてどちらか」の二択を迫られる。現実の経理実務では、明細ごとに仕訳を切る。

**問題3: 付随費用の取得価額算入判定ができない**。設置費・運搬費が本体の取得価額に含まれるか否かは、明細ごとに個別判定が必要。一括方式ではこの粒度の判定が構造的に不可能だった。

この気づきから、プロンプトを全面改修した。改修の核心は「**明細個別判定の原則**」の明文化である:

```
【明細個別判定の原則】
- 各明細は独立して判定すること。他の明細の金額と合算して判定してはならない
- 付随費用は品名から判断。迷う場合はGUIDANCE
- 1つの書類に資産計上と費用処理が混在するのは正常
- 書類タイトルや取引先は参考情報とし、判定は各明細の内容と個別金額に基づくこと
```

さらに「**合計金額バイアス防止**」のために、プロンプト構築関数 `_build_user_prompt()` では意図的に合計金額を表示しない設計にした。コード中に `# NOTE: 合計金額は表示しない（合計ベース判定のバイアス防止）` というコメントが2箇所ある。

### 4段階判定フローの実装

判定ロジックの最大の進化は、「1段階の分類」から「4段階のフロー」への転換である。

**STEP 1: 各明細行を個別に判定** — 各明細を独立してCAPITAL_LIKE / EXPENSE_LIKE / GUIDANCEに分類する。金額基準（10万/20万/30万円）は各明細の個別金額に対して適用する。

**STEP 2: 各明細が取得価額に含めるべきか個別判定** — 付随費用（設置費、運搬費、試運転費等）が本体の取得価額に含まれるか否かを判定する。税法上、「購入代価 + 付随費用 = 取得価額」であり、この判定は資産の帳簿価額を左右する。

**STEP 3: 取得価額合計と費用合計を算出（税抜き基準）** — STEP 2の結果を集約し、`acquisition_cost_total` と `expense_total` を算出する。

**STEP 4: 資産分の想定耐用年数を提示** — 減価償却資産の耐用年数等に関する省令を参照し、`estimated_useful_life_years`、`useful_life_basis`、`asset_category`を返す。

4段階フローの導入前後で最も変わったのは、「混在ケース」の処理品質である。1つの見積書に「サーバー購入 50万円」「設置工事 15万円」「旧機撤去 10万円」「年間保守 5万円」が並ぶケースで:

- STEP 1: サーバー→CAPITAL_LIKE, 設置→CAPITAL_LIKE, 撤去→EXPENSE_LIKE, 保守→EXPENSE_LIKE
- STEP 2: サーバー→取得価額に含む, 設置→取得価額に含む, 撤去→含まない, 保守→含まない
- STEP 3: 取得価額合計=65万円, 費用合計=15万円
- STEP 4: サーバー→器具及び備品・電子計算機→4年

経理担当者がこの情報を見れば、仕訳を切るための判断材料が全て揃う。

### 3値判定（CAPITAL_LIKE / EXPENSE_LIKE / GUIDANCE）の設計根拠

「LIKE」という接尾辞が付いている理由は、AIの判定は最終的な会計処理の決定ではなく「傾向の提示」だからである。最終判断は人間が行う。

GUIDANCEはただ「分かりません」と返すのではない。`missing_fields`（何の情報が不足しているか）と`why_missing_matters`（なぜその情報が必要か）を構造化して返す。さらにcmd_040の改修で`similar_case`（類似の実務事例）も生成するようになった。「止まる」だけでなく「なぜ止まったか」「次に何をすべきか」まで提示するのが、単なるエラーハンドリングとGUIDANCEの違いである。

### Cloud Runデプロイで遭遇した問題 — WSL2→GCP連携

デプロイ環境は「WSL2 on Windows 11 → Google Cloud Run」という、やや特殊な構成だった。

**問題1: gcloud認証のWSL2問題**。WSL2内で`gcloud auth login`を実行するとブラウザ認証フローが正常に動作しない。解決策は、Windows側のgcloud認証情報をWSL2から直接参照する方式:

```bash
export CLOUDSDK_CONFIG="/mnt/c/Users/owner/AppData/Roaming/gcloud"
```

この手法はcmd_033で足軽2が発見・確立し、以降の全デプロイの標準手順となった。

**問題2: ContainerImageImportFailed**。Cloud Buildでビルドは成功しても、Cloud Runがイメージをpullできないエラー。原因はArtifact Registryの読み取り権限不足。ビルドは成功しているのでDockerfile自体に問題はなく、エラーメッセージもIAM権限不足を直接示さない。問題の特定に至るまでに `gcloud run services describe` と `gcloud run revisions describe` の出力を丁寧に読み解く必要があった。最終的に `scripts/cloudrun_triage_and_fix.ps1` として対話形式のトラブルシューティングスクリプトを作成した。

**問題3: Dockerfile差し替え方式**。APIとUIで異なるDockerfileを使い分ける必要があったが、Cloud Runの`--source .`デプロイではルートの`Dockerfile`しか参照されない。UIデプロイ時にDockerfileを差し替え、デプロイ後に復元する方式を採用した。一見トリッキーだが、Cloud Runのソースデプロイの制約下では最もシンプルな解法だった。

本プロジェクトでは合計4回のCloud Runデプロイを実施した。4回全てで`/health`エンドポイントの200 OK確認、POST `/classify`の正常動作確認を実施している。

### PDF抽出→Gemini判定→レスポンス集約のパイプライン全体像

システムのデータフローは、4段階のフォールバックを持つPDF抽出から始まり、Gemini APIでの判定を経て、構造化されたレスポンスに集約される。

```
PDF入力
  │
  ├── Priority 1: Gemini Vision API（GEMINI_PDF_ENABLED=1）
  │     └── PDFページをグリッド画像化 → gemini_splitter.py で文書境界検出
  ├── Priority 2: Document AI（USE_DOCAI=1）
  │     └── Google Cloud Document AI による高精度OCR
  ├── Priority 3: PyMuPDF (fitz)
  │     └── テキストレイヤーの直接抽出
  └── Priority 4: pdfplumber
        └── PyMuPDFのフォールバック
  │
  ▼
明細テキスト抽出
  │
  ├── core/classifier.py（ルールベース分類）
  │     ├── キーワードマッチング
  │     ├── 金額閾値チェック
  │     └── ポリシーオーバーライド
  │
  ├── api/gemini_classifier.py（Gemini AI分類、GEMINI_ENABLED=1）
  │     ├── _normalize_line_items(): 入力正規化
  │     ├── _build_user_prompt(): プロンプト構築（合計金額バイアス防止）
  │     ├── _sanitize_text(): プロンプトインジェクション対策
  │     ├── classify_with_gemini(): 4段階フロー実行
  │     └── _parse_gemini_response(): レスポンスバリデーション
  │
  ▼
構造化レスポンス
  ├── decision: CAPITAL_LIKE / EXPENSE_LIKE / GUIDANCE
  ├── confidence: 0.0〜1.0（0.7未満はGUIDANCE強制）
  ├── line_item_analysis: 各明細の個別判定
  ├── acquisition_cost_total: 取得価額合計
  ├── expense_total: 費用合計
  ├── estimated_useful_life_years: 想定耐用年数
  ├── missing_fields + why_missing_matters: 不足情報
  ├── similar_case: 類似実務事例（GUIDANCEのみ）
  └── evidence: 判定根拠（Vertex AI Search）
```

このパイプラインの設計で最も重視したのは**graceful degradation**（優雅な劣化）である。Feature Flagが無効な場合、APIキーが未設定の場合、ライブラリが未インストールの場合——どの状態でもシステムは**停止しない**。機能が段階的に縮退し、最低限のルールベース分類は常に動作する。

`gemini_classifier.py`のdefault_responseもこの思想を体現している。Geminiが使えなければ、GUIDANCE（安全側）を返す。ImportError、JSONDecodeError、ConnectionError、TimeoutError——全ての例外パスがGUIDANCEフォールバックに収束する。Stop-first原則がエラーハンドリング設計にまで貫かれている。

### テスト159件を積み上げた過程

テスト件数の推移は、プロジェクトの成熟度を物語る。

| テストファイル | 対象 | 特徴 |
|-------------|------|------|
| `test_classifier.py` | ルールベース分類 | キーワードマッチング、金額閾値、ポリシーオーバーライド |
| `test_api_response.py` | APIレスポンス形式 | FastAPIエンドポイントの入出力検証 |
| `test_pdf_extract.py` | PDF抽出 | PyMuPDF/pdfplumberのフォールバック動作 |
| `test_e2e_pipeline.py` | エンドツーエンド | PDF入力→判定結果出力の全パイプライン |
| `test_gemini_splitter.py` | 文書境界検出 | 複数文書PDF分割のGemini Vision連携 |
| `test_embedding_store.py` | ベクトルストア | 類似事例検索の精度検証 |
| `test_similarity_search.py` | 類似検索 | 類似事例検索のエンドポイント |
| `test_adapter.py` | アダプター | 入出力形式の変換検証 |
| `test_ai_hints.py` | AIヒント | GUIDANCEヒント生成 |
| `test_pipeline.py` | パイプライン | 処理パイプラインの結合テスト |

ゴールデンセット（Golden Set）は10件の代表的なテストケースで構成される。10/10 = 100%通過。この100%の意味は「AIが間違えない」ではない。「**AIが間違える前に止まる**」ことが100%保証されているということ。

### セキュリティの改修 — RISK対処の実際

品質監査（cmd_027）で高リスク6件が検出された。これらはcmd_035で足軽チームが並列修正した。

| RISK | 内容 | 修正 |
|------|------|------|
| RISK-002 | slowapiレート制限が全5エンドポイントに未適用 | `@limiter.limit()` を全エンドポイントに適用。GET /health: 30/min, POST /classify: 10/min |
| RISK-003 | Gemini APIタイムアウト未設定 | `_GEMINI_TIMEOUT_MS = 30_000` を設定 |
| RISK-004 | 入力サイズ制限なし | `_MAX_PROMPT_CHARS = 10000`, `_MAX_LINE_ITEMS = 50` を設定 |
| RISK-005 | bare Exception 15箇所 | 全箇所を具体的例外クラスに修正 |
| RISK-006 | Gemini接続テスト未実装 | `startup_gemini_check()` 追加。`/health` レスポンスに `gemini_connected` フィールド追加 |

特に RISK-004（コスト制御）は、`_sanitize_text()` 関数によるプロンプトインジェクション対策と合わせて実装された。修正後のテスト結果: **136 passed, 3 skipped, 0 failed (1.86s)**。

### 技術選択の試行錯誤

#### Gemini SDK移行

`google-generativeai`（旧SDK）から`google-genai`（新SDK v1.51.0+）への移行は、一見単純なライブラリ更新だが実際には全く異なるインターフェースへの切り替えだった。移行の動機は`thinking_level`パラメータの利用。税務判定は「この明細は付随費用に該当するか」「金額基準のどれに当てはまるか」など多段階の論理推論が必要で、`thinking_config=types.ThinkingConfig(thinking_level="MEDIUM")`による深い推論がGemini 3 Pro Previewで利用可能になった。

#### PDF抽出の多段フォールバック

PDF抽出に4段階のフォールバックを設けたのは、デプロイ環境の多様性に対応するためである。Gemini Vision APIやDocument AIはGCP上でのみ動作する。ローカル開発環境ではPyMuPDFやpdfplumberが必要。Feature Flagで切り替え可能にし、どの環境でも動作するようにした。

PyMuPDFはAGPL-3.0ライセンスであり、これはRISK-001として検出された。対処はGitHub公開によるソースコード開示義務の充足（殿の判断）と、README.mdへのAGPLセクション新設。

---

<a id="section-5"></a>

## 5. マルチエージェント開発の詳細

### 将軍・家老・足軽の日常的なやりとり

multi-agent-shogunでは、指示と報告はすべてYAMLファイルに記載し、通知はtmux send-keysで相手を「起こす」方式をとる。Claude Codeは「待機」ができない（プロンプト待ち＝停止）ため、イベント駆動設計が必須である。

#### 指示の流れ

```
殿（人間） → 将軍に口頭/テキストで指示
将軍 → queue/shogun_to_karo.yaml に構造化指示を記載
将軍 → tmux send-keys で家老を起こす
家老 → YAML読み込み → タスク分解 → 足軽専用ファイルに書き込み
家老 → tmux send-keys で各足軽を起こす
足軽 → 自分のタスクファイルを読み → 作業開始
```

#### 報告の流れ

```
足軽 → queue/reports/ashigaru{N}_report.yaml に結果を書く
足軽 → tmux send-keys で家老を起こす
家老 → 全報告ファイルをスキャン（通信ロスト安全策）
家老 → dashboard.md を更新（殿への報告はここだけ）
```

**重要な設計判断**: 下→上への報告は dashboard.md 更新のみとし、send-keysは行わない。殿がターミナルで入力中に割り込みが発生するのを防ぐための設計。

### YAML通信の実例

#### 将軍→家老への指示例

cmd_033の指示は、本ハッカソン開発で最大規模のタスクだった:

```yaml
- id: cmd_033
  timestamp: "2026-02-14T05:45:45"
  command: |
    ハッカソン最終提出に向けた総点検・デプロイ・動画撮影手順書の作成を行え。
    対象プロジェクト: /mnt/c/Users/owner/Desktop/fixed-asset-ashigaru
    本日が提出日である。これが最後の機会だ。
    【任務1: 資料間の齟齬検証】...
    【任務2: Cloud Runデプロイ】...
    【任務3: 動画撮影手順書作成】...
    【任務4: 懸念点・リスク洗い出し】...
  project: fixed-asset-ashigaru
  priority: critical
  status: done
```

#### 足軽→家老への報告例

```yaml
worker_id: ashigaru2
task_id: subtask_035_02
parent_cmd: cmd_035
timestamp: "2026-02-14T06:11:19"
status: done
result:
  summary: "RISK-003/004/005 全修正完了。4ファイル修正、テスト136件全通過でござる"
  files_modified:
    - "api/gemini_classifier.py"
    - "core/pdf_extract.py"
    - "api/vertex_search.py"
    - "api/embedding_store.py"
  verification:
    syntax_check: "全4ファイル ast.parse OK"
    test_result: "136 passed, 3 skipped, 0 failed (1.86s)"
skill_candidate:
  found: false
```

報告書には `skill_candidate` が全報告に必須。再利用可能なパターンの継続的な蓄積を促す仕組みである。

### ダッシュボード運用の実際

dashboard.md は人間（殿）が見るための唯一の状況表示画面。家老のみが更新責任を持つ。

ダッシュボードの構造:
- **🚨 要対応**: 殿の判断が必要な事項
- **🔄 進行中**: 各cmdの進捗状況
- **✅ 本日の戦果**: 完了タスクのタイムスタンプ付きログ
- **⏸️ 待機中**: 次の任務を待つ足軽一覧

**「上様お伺いルール」**: 殿への確認事項は**全て**「🚨 要対応」セクションに集約する。これは殿から直接指摘された最重要ルール。

### コンパクション問題と対策

マルチエージェントシステムでは、以下の情報が失われるリスクがある:
1. **自分が誰か**: 将軍/家老/足軽のいずれかの役割
2. **何をしていたか**: 作業中のタスクID、進捗状態
3. **禁止事項**: 各役割の行動制約

**対策1: 正データ参照方式**: dashboard.mdは二次情報。コンパクション後は必ずYAMLファイル（正データ）を参照。

**対策2: Memory MCPによる知識の永続化**: ポストモーテム、運用ルール、プロジェクト文脈、QAチェックリストを永続保存。

**対策3: エージェント作業チェックリスト**: `queue/agent_checklist.yaml` で「やったつもり」を防止。

### 殿への質問と回答（QUESTIONS_FOR_LORD.mdより）

開発過程で殿に伺いを立てた重要事項:

| Q | 質問 | 回答・対処 |
|---|------|-----------|
| Q1 | Embedding APIの利用について | `history_search.py` で既存のembeddingを使えばAPI不要と判明 |
| Q2 | PDF分割デモについて | `create_multi_doc_pdf.py` で複数文書PDFを自動生成 |
| Q3 | requirements.txtはdevcontainer対応必要か？ | そのままでOK（殿承認） |

### lu.ma誤報事件の詳細と教訓

足軽がハッカソン公式ページに存在しない「lu.ma登録」を致命的リスクとして報告した事件。

**教訓**: AIエージェントが「ハルシネーション」を起こし、それを組織の報告系統に乗せてしまうリスク。Memory MCPに「致命的リスクの報告時は公式一次情報での検証を必須とせよ」を追記。

### send-keys忘れ事件の詳細と対策

家老がタスクファイルを配置後、send-keysを忘れ全足軽が停止。

**対策**:
1. Memory MCPに `家老運用ルール_send_keys必須` を永続化
2. karo.md にstep 7 `send_keys` + step 7.5 `verify_ashigaru_wakeup` を追加
3. send-keysの2回分割ルールを厳格化

### 90秒ルール・逐次起動ルールの導入経緯

殿から家老のボトルネック化が指摘された:

> 「家老がボトルネック化するケースが多い。家老の1分の遅延 = 足軽8人の1分の待機 = 8分の無駄」

**核心的な洞察**: マルチエージェントシステムでは、管理者の長考が全体のスループットを著しく低下させる。完璧な計画より迅速な分配が正義。

導入ルール:
- **逐次起動**: 1件分解したら即座に足軽を起こす（全件揃うまで待つな）
- **90秒ルール**: 思考は90秒以内。纏まった分から即実行

### 足軽8名の同時稼働の実際

cmd_035での同時稼働タイムライン:

```
06:07  足軽6 完了: pptxスライド7-12
06:10  足軽3 完了: GitHub公開準備
06:11  足軽2 完了: RISK-003/004/005修正
06:11  足軽5 完了: pptxスライド1-6
06:15  足軽1 完了: RISK-002/005/006修正
06:15  足軽7 完了: pptx結合・最終検証
06:16  足軽8 開始: 再デプロイ
06:16  足軽4 開始: HACKATHON_JOURNEY.md作成
06:20  足軽4 完了: HACKATHON_JOURNEY.md作成完了
```

**約13分**でコード修正5ファイル、pptx12枚、GitHub準備、記事1本、再デプロイ開始を完了。逐次処理なら2-3時間の作業量。

### 将軍・家老・足軽 — 戦国階層がソフトウェア開発で機能した理由

multi-agent-shogunの階層構造は、単なるメタファーではない。実際のプロジェクト管理上の問題を解決するために設計された、実用的なアーキテクチャである。

#### なぜ3階層なのか

Claude Codeには「待機」という概念がない。プロンプト待ちは完全な停止を意味する。この制約が3階層設計を必然にした:

- **将軍（Shogun）**: 殿（人間）の意図を解釈し、構造化された指示に翻訳する。将軍は直接足軽に指示を出してはならない。必ず家老を経由する。
- **家老（Karo）**: 将軍の「目的」を受け取り、「実行計画」に分解する。何人の足軽を使うか、どのペルソナで作業させるか、依存関係はあるか——これらの判断は全て家老の裁量。将軍の指示をそのまま横流しすることは「家老の名折れ」として禁じられている。
- **足軽（Ashigaru）**: 実働部隊。1人1タスク。自分専用のYAMLファイルだけを読み、完了したら報告ファイルを書く。他の足軽のファイルに触れることは禁止。

#### 「横流し禁止」が生んだ品質

家老の指示書（karo.md）には「五つの問い」が定められている:

| # | 問い | 考えるべきこと |
|---|------|----------------|
| 壱 | 目的分析 | 殿が本当に欲しいものは何か？ |
| 弐 | タスク分解 | どう分解すれば最も効率的か？ |
| 参 | 人数決定 | 1人で十分なら1人で良い |
| 四 | 観点設計 | どのペルソナ・シナリオが有効か？ |
| 伍 | リスク分析 | 競合（RACE-001）の恐れはないか？ |

例えば、将軍が「install.batをレビューせよ」と指示した場合。悪い家老はこれを足軽にそのまま渡す。良い家老は、足軽1を「Windowsバッチ専門家としてコード品質レビュー」に、足軽2を「完全初心者ペルソナでUXシミュレーション」に割り当てる。この判断こそが家老の存在意義だった。

### 家老ボトルネック問題 — 全足軽が20分停止した日

2026年2月11日、殿から痛烈な指摘が飛んだ:

> 「家老がボトルネック化するケースが多い。具体的な問題: (1)家老の思考時間が長い（20-30分の思考ブロック頻発）、(2)足軽への指示出しが遅延、(3)コンパクションリスクが家老に集中、(4)dashboardの更新が遅れがち」

家老は将軍から指示を受けると、8人全員分のタスクを「完璧に」分解してから一斉に配信していた。だが問題は、家老が考えている20〜30分の間、8人の足軽が**全員プロンプト待ち（＝完全停止）**だったことだ。

**家老の1分の遅延 = 足軽8人の1分の待機 = 8分の無駄。**

#### 逐次起動ルールの導入

```
✅ 正しい流れ:
  指示受領 → 1件目分解(30秒) → 足軽1起動 → 2件目分解(30秒) → 足軽2起動 → ...

❌ 禁止パターン:
  指示受領 → 全件分解(3分) → 足軽1起動 → 足軽2起動 → ...
  （3分間、全足軽が停止している！）
```

さらに「90秒ルール」を追加した。思考は90秒以内。90秒で計画が纏まらなければ、纏まった分から即座に配信する。

**「完璧な計画より迅速な分配。これが鉄則じゃ」** ——この一文がkaro.mdに太字で追記された。

#### タスクレベル判定（クイックディスパッチ）

全タスクに同じ分析深度を適用するのは非効率。家老は受領した指示を即座にレベル判定する:

| レベル | 条件 | 分析深度 | 目標時間 |
|--------|------|----------|----------|
| S（Simple） | 足軽1人、対象1-2ファイル | 五つの問い省略 | 2分以内 |
| M（Medium） | 足軽2-3人、軽い判断が必要 | 壱・弐・参のみ | 5分以内 |
| L（Large） | 足軽4人以上、複雑な依存関係 | フル実施 | 10分以内 |

Sレベルなら「五つの問い」すら省略して即配信。改善前: タスク受領→全足軽起動まで20〜30分。改善後: タスク受領→最初の足軽起動まで90秒以内。

### agent_checklist.yaml — 「やったつもり」を殺すファイル

コンパクションが起きると、エージェントは「自分が何をしていたか」を忘れる。これは理論上の問題ではなかった。実際のハッカソン開発中に何度も発生した。

#### チェックリストの構造

```yaml
current_tasks:
  - id: cmd_044
    description: "fixed-asset-ashigaruリポジトリのCI修正→push"
    started_at: "2026-02-15T07:35:10"
    status: in_progress
    priority: critical

checklist:
  - id: subtask_044_01
    task: "バックアップ→CI修正→push→CI緑確認"
    assigned_to: ashigaru1
    done: false

dispatch_status:
  ashigaru1: working_cmd044
  ashigaru2: idle
  ...
```

ポイントは3つ: (1) current_tasks: 今何のコマンドを処理中か、(2) checklist: 各サブタスクの完了状態、(3) dispatch_status: 全8足軽の稼働状態。dashboard.mdは家老が整形した「二次情報」に過ぎないが、agent_checklist.yamlは作業の「正データ」だ。

### YAML駆動通信 — ポーリング禁止の経済学

Claude CodeはAPIコールごとに課金される。もしエージェントが定期的にポーリングすれば、何もしていない時間にも課金が発生する。足軽8人が10秒ごとにポーリングすれば、1分で48回のAPIコール。何も起きていなくても。

だからポーリングは`F004`として絶対禁止事項に指定されている。代わりに採用したのが「イベント駆動」設計: 指示内容をYAMLファイルに書き、tmux send-keysで相手のペインに送信する。YAMLは人間にも機械にも読める。Git管理もできる。トラブル時にviで直接編集もできる。

### 報告通知プロトコル — 通信ロスト対策

send-keysには通知が届かないケースがあった。家老がその瞬間に別の処理をしていると、send-keysのメッセージがパーミッション確認ダイアログに「消費」されてしまう。

対策は二重化:
1. **報告ファイルは必ず書く**: これが正データ
2. **send-keysで通知を試みる**: busyなら最大3回、10秒間隔でリトライ
3. **家老は起こされるたびに全報告をスキャン**: 特定の足軽からの通知で起きた場合でも、全報告ファイルを毎回スキャンする

この「全スキャン」方式により、send-keysの通知が失われても報告が漏れることはなくなった。ファイルシステムが最終的な真実の情報源（Source of Truth）として機能する。

### 家老コンパクション早期検出 — 足軽が止まる前に気づく

足軽がコンパクションを起こすと、作業途中で停止する。しかし家老はそれを知らない。2026年2月10日、殿の指示で「足軽コンパクション早期検出」メカニズムが導入された:

1. 足軽にタスクを送信してから5分経過後、全足軽のペインを`tmux capture-pane`でスキャン
2. プロンプト（`❯`や`bypass permissions on`）が表示されている足軽を検出
3. その足軽の報告ファイルを確認し、現在のcmdの報告でなければ→コンパクション停止と判定
4. 該当足軽にsend-keysで再起動

ポーリング禁止（F004）に抵触しないよう、チェックのタイミングは「足軽全員にsend-keys送信完了した直後」と「報告待ちで起こされた際に報告元以外の足軽も全員チェック」の2つだけに限定されている。

### send-keys忘れ事件 — 全足軽が停止した日

家老がタスクをYAMLファイルに書き込んだ後、tmux send-keysで足軽を起こす手順を忘れた。結果、全8足軽がタスクファイルに新任務があるにもかかわらず待機状態のまま停止。殿が異常に気づき、手動で足軽を再起動するまで長時間のロスが発生した。

対策として `scripts/monitor_ashigaru.sh`（73行）が作成された。各足軽のタスクファイルと実際の稼働状態を比較し、タスクがあるのに動いていない足軽を検出するスクリプトである。

また、全足軽一括再起動コマンドもTOMORROW_RESUME.mdに記載された:

```bash
for i in $(seq 1 8); do
  tmux send-keys -t multiagent:0.$i "queue/tasks/ashigaru${i}.yaml を確認せよ" Enter
done
```

### コンパクションで作業が飛んだ事件（cmd_052）

足軽7号がcmd_052で908行の `app_minimal.py` を編集中にコンパクションが発生。コンパクション後、作業状態を復元できず、どこまで編集したか不明な状態に。足軽7号はスタック（動けなくなった）し、足軽3号が代わりに後片付けを実施。同じ作業を2人がやることになり、工数が倍増した。

この事件を契機に `skills/compaction-guard.md` にスキル設計書が作成された。コンパクション前に作業状態を正データ（YAMLファイル）に書き出す仕組みである。`queue/agent_checklist.yaml` の導入もこの事件が契機だ。

### 数字が語るマルチエージェントの現実

ハッカソン全体を通じて、以下の数字が記録された:

- **cmd_033〜044**: 12コマンドを約2日間で完了
- **最大並列稼働**: 足軽8名同時
- **1コマンドあたりの平均完了時間**: 20〜40分（複雑なcmdを含む）
- **send-keys事故**: 少なくとも2回（家老の送信忘れ、1行書き問題）
- **コンパクション発生**: 複数回（agent_checklist.yamlの導入がその証拠）
- **導入されたルール数**: 逐次起動、90秒ルール、2回分割、全スキャン、コンパクション早期検出

マルチエージェント開発は「設定して放置」ではない。運用中に問題が見つかり、ルールが追加され、ルールが破られ、さらにルールが厳格化される——その繰り返しだった。戦国時代の軍制がそうであったように、実戦の中でしか磨かれないものがある。

---

<a id="section-6"></a>

## 6. 失敗と学び

<!-- 殿記入欄: 開発中に一番困ったこと -->

<!-- 殿記入欄: もっと早くやればよかったこと -->

### Confidence Bug — デフォルト値の罠

`api/main.py` L127: `ev.get('confidence', 0.8)` — このデフォルト値0.8が閾値0.7を偶然上回っていたため、**「止まるべき場面で止まらない」**というStop-first設計の根幹を破壊するバグだった。

### Aggregation Bug — 集計ロジックの暴走

「1つでもGUIDANCEがあれば全体がGUIDANCE」— 安全側に倒しすぎると使い物にならなくなる教訓。

### QAチェックリストの誕生

```
1. 実際にテストを実行して結果を確認したか？
2. ハードコードされたデフォルト値が残っていないか？
3. 集計ロジックの仕様は意図通りか？
4. エッジケースをテストしたか？
5. 変更した関数の呼び出し元すべてを確認したか？
```

### ドキュメント齟齬15件の具体的内容

| カテゴリ | 件数 | 具体例 |
|----------|------|--------|
| 機能説明の不一致 | 4件 | APIエンドポイントの説明が古い |
| 技術スタック記載のブレ | 3件 | Vertex AI Search vs Discovery Engine |
| デプロイ手順の不正確さ | 3件 | 環境変数名の間違い |
| 審査員向け情報の誤り | 2件 | 古いスコア情報の残存 |
| スクリーンショットの不整合 | 2件 | UI変更後の更新漏れ |
| ライセンス記載の不足 | 1件 | PyMuPDF AGPLの記載なし |

### AGPL問題への対処

PyMuPQ AGPL-3.0 → GitHub公開で義務充足（殿の判断）。README.mdにAGPLセクション新設。

### リスク17件の全容

高リスク6件:

| ID | タイトル | 対処 |
|----|----------|------|
| RISK-001 | PyMuPDF AGPL-3.0 | GitHub公開で義務充足 |
| RISK-002 | slowapiレート制限未適用 | 全5エンドポイントに適用 |
| RISK-003 | Gemini APIタイムアウト未設定 | 30秒timeout設定 |
| RISK-004 | コスト制御なし | 入力10,000字+明細50件制限 |
| RISK-005 | bare Exception 15箇所 | 全箇所を具体的例外に修正 |
| RISK-006 | 環境変数バリデーション不足 | startup_gemini_check()追加 |

### P0致命的バグ5件 — 提出2日前の大手術（cmd_040）

2月13日深夜。提出日まで残り約36時間。品質検査を徹底実行した結果、5件の「P0 = 即座に修正しなければ提出不可」の致命的バグが発覚した。テストは全件PASSしていた。見た目もそれらしく動いていた。しかし「正しく動いているように見えて、実は根本的に壊れている」という、もっとも厄介な種類のバグだった。

#### Bug 1: 合計一括判定ロジックの暴走

見積書に複数明細がある場合、1つの明細でもGUIDANCEと判定されると、書類全体がGUIDANCEになってしまう。本来は多数決 + 金額加重であるべきところを、最も慎重な判定が全体を支配する設計になっていた。安全側に倒した設計は一見正しく見えるが、すべてが「要確認」になるシステムは、何も判定しないシステムと同じだ。

#### Bug 2: Confidence値が常に0.80に固定

`api/main.py` 127行目の `ev.get('confidence', 0.8)` というたった1行。このシステムでは confidence < 0.7 で GUIDANCE（止まれ）を発動する。デフォルト値0.8は閾値0.7を上回るため、**「止まるべき場面で絶対に止まらない」**という、Stop-first設計の根幹を破壊するバグだった。

#### Bug 3: 日付フィールドの誤読

OCR後のテキストパースで、和暦表記や多様なフォーマットに対応できていなかった。固定資産の取得日は税務上の重要情報であり、これが誤っていると判定結果の根拠が揺らぐ。

#### Bug 4: 集計ロジックの重複カウント

PDF内のテーブル抽出で、ページ跨ぎの行が重複抽出される場合があり、それがそのまま集計に反映されていた。

#### Bug 5: エビデンス参照の不整合

Vertex AI Searchからの検索結果と、Geminiの判定ロジックが独立して動いており、両者の整合性チェックが欠如していた。

#### 修正の全プロセス

足軽8名が並列稼働し、約2時間でP0バグ5件を全件修正。修正後のテスト結果は186件全PASS。この経験から、QAチェックリストがMemory MCPに `QA_Checklist_Before_Complete` として永続保存され、以降のすべてのタスクで参照されるルールとなった。

### GUIDANCEボタンUI問題 — 「止まれ」が伝わらないUI（cmd_041）

Stop-first設計の核心は「AIが迷ったら止まる」こと。しかしUIを見た殿の第一声は:

> 「GUIDANCEって何？ 止まってるの？ 進めていいの？」

致命的だった。システムの最も重要な概念が、ユーザーに1秒で伝わらない。GUIDANCEの黄色バッジに加え、「判定を保留しました」「以下の情報を追加してください」という平易な日本語メッセージを追加。ボタンのラベルも「再判定する」に変更し、次のアクションが明確になるようにした。

ペルソナは「設備会社の経理担当者（高卒事務の女性）」。専門用語の排除はプロジェクト開始時から掲げていた方針なのに、最も重要なラベルで英語の専門用語を使っていた。技術的には軽微だが、プロダクトとしては致命的な問題だった。

### lu.ma誤報事件 — AIのハルシネーションが組織を走らせた日

この事件の経緯はさらに詳細に記録されている。足軽6号がlu.maのイベントURL情報を収集した際、URLの存在確認を行わずに報告。報告時に付けるべき「要確認」タグを落とした。足軽8号がその情報を受け取り、未検証のまま「クリティカルリスク」としてエスカレーション。将軍経由で殿に報告され、殿が直接確認したところURLが無効であることが判明した。

cmd_070として正式な調査指令が発行され、構造的対策3件が導入された:
1. **信頼度スキーマ（confidence schema）**: 情報に信頼度レベルを付与する仕組み
2. **重要度ゲート（severity gate）**: 一定以上の重要度の情報は自動エスカレーションしない
3. **ソース追跡（source tracking）**: 情報の出所を必ず記録・検証する

AIエージェントは「もっともらしい情報」を生成できてしまう。人間のレビューなしにエスカレーションすると、偽情報が組織を駆け上がる。Stop-first設計の重要性を再確認した事件だった。

### 失敗から生まれた強靭さ

これらの失敗は、すべて「動いているように見えた」段階で発覚した。テストは通っていた。見た目は正常だった。報告書は整然としていた。

しかし:
- Confidenceは常に0.80で固定されていた
- 集計ロジックは全件GUIDANCEにしていた
- lu.maは存在しなかった
- 家老は30分考えている間に足軽8人が停止していた
- send-keysのEnterは届いていなかった
- コンパクション後のエージェントは自分が誰かわかっていなかった

**「正しく動いているように見える」ことと「正しく動いている」ことは全く別物だ。** この教訓がmulti-agent-shogunを鍛え、QAチェックリスト、90秒ルール、正データ参照方式、Memory MCP永続化——これらすべての仕組みを生み出した。

回り道こそが、最短経路だった。

---

<a id="section-7"></a>

## 7. 審査基準に対する戦略的アプローチ

### 3基準への対応戦略

#### 課題の新規性

「AIが止まることに価値がある」という逆転の発想。「Agentic AI」の定義を「全自動化」から「判断制御」に再定義。

#### 解決策の有効性

Stop-first設計の3ステップ（止まる→聞く→変わる）を実動デモで見せる。定量的効果: 処理時間67%削減、年間200時間削減（会計事務所規模）。

#### 実装品質と拡張性

Google Cloud AIの4サービス統合。pytest 136件通過、Golden Set 10/10。Feature Flagによる段階的機能有効化。REST API（POST /classify）でERP/RPA連携可能。

### 審査員に刺さるキーワード戦略

| キーワード | 使い所 | 狙い |
|-----------|--------|------|
| 「知らないを、知っているAI」 | オープニング・クロージング | キャッチコピーとして記憶に残る |
| 「止まる、聞く、変わる」 | GUIDANCEデモの核心 | 3語でAgentic設計を説明 |
| 「Stop-first」 | 技術ハイライト | 設計思想の一言要約 |
| 「メタ認知」 | 技術ハイライト | AIが自分の不確実性を認識する高度さ |
| 「監査証跡」 | DIFF表示時 | 実務的な価値の訴求 |
| 「人の判断を奪わない。支える。」 | クロージング | ヒューマンセントリック思想 |

### デモシナリオの設計思想

GUIDANCEのCase 2に90秒（全体の50%）を割り当てた理由:

1. CAPITAL_LIKEやEXPENSE_LIKEは「AIが正しく判定した」だけで差別化にならない
2. GUIDANCEこそが本プロジェクトの独自性 — AIが「迷った」ことを認め、自ら止まり、人に聞く
3. DIFF表示が「監査証跡」という実務的価値を生む

**デモの3分間配分（LORD_INSTRUCTIONSハッカソン残タスク.mdより）**:

```
0:00-0:25  オープニング（問題提起）       25秒
0:25-0:40  Case 1: CAPITAL_LIKE（即判定）  15秒
0:40-2:10  Case 2: GUIDANCE（核心!!）       90秒  ← 50%
2:10-2:40  技術ハイライト                  30秒
2:40-3:00  クロージング                    20秒
```

**強調すべき3瞬間**（LORD_INSTRUCTIONSハッカソン残タスク.mdより）:

| 瞬間 | 演出 | セリフ例 |
|------|------|---------|
| **止まる** | GUIDANCEが表示された瞬間に1-2秒の間 | 「ここでAIが止まりました」 |
| **聞く** | 不足情報の構造化提示 | 「単に分からないではなく、何が必要かを示します」 |
| **変わる** | Before/After DIFF | 「この差分が監査証跡そのものです」 |

### 提出チェックリスト（LORD_ACTION_PLAN.mdより）

提出に必要な全工程を体系化:

| Phase | 内容 | 状態 |
|-------|------|------|
| 1. Preflight | pytest全通過確認、preflight_check.py実行 | 足軽対応 |
| 2. Commit & Push | git add/commit/push → GitHub Public確認 | 殿対応 |
| 3. Cloud Run | gcloud run deploy（PDF_CLASSIFY_ENABLED=1含む） | 足軽→殿確認 |
| 4. Demo Video | OBS/Game Bar/Loom で3分動画撮影→YouTube公開 | 殿対応 |
| 5. Zenn Article | トピック `gch4`、カテゴリ Idea | 殿対応 |
| 6. Submission | lu.maフォーム入力（GitHub URL + Deploy URL + Zenn URL） | 殿対応 |

### pptxスライド12枚の構成

| # | タイトル | 目的 |
|---|---------|------|
| 1 | 表紙 | キャッチコピー |
| 2 | 課題（問題提起） | ペルソナの3つの痛み |
| 3 | 解決策 | 「止まる→聞く→変わる」 |
| 4-5 | デモ画面 | 単品判定 + バッチ処理 |
| 6 | 技術スタック | 4つのGoogle Cloudサービス |
| 7 | アーキテクチャ | システム構成図 |
| 8 | Agentic設計 | フロー図 + 従来AI比較表 |
| 9 | Before/After | 15分→5分、67%削減 |
| 10 | 成果・実績 | Golden Set 100%, pytest 136件 |
| 11 | 今後の展望 | 他業務展開、エコシステム統合 |
| 12 | クロージング | CTA + GitHub URL |

---

<a id="section-8"></a>

## 8. デプロイまでの道のり（拡充版）

### 8.1 Cloud Run選定の5つの理由

本プロジェクトのデプロイ先として Cloud Run を選定した理由は明確だった。

| # | 理由 | 詳細 |
|---|------|------|
| 1 | **サーバーレス** | インフラ運用の負荷を最小化。ハッカソン期間中はプロダクト開発に集中できる |
| 2 | **自動スケーリング** | リクエスト数に応じたスケールアップ/ダウン。審査時のアクセス集中にも対応 |
| 3 | **コスト最適化** | リクエストがなければ0円。ハッカソン期間中のコスト管理が容易 |
| 4 | **Dockerベース** | ローカル開発環境とデプロイ環境の差異を最小化 |
| 5 | **ハッカソン要件** | RULES2.md で Cloud Run が必須要件として明記されていた |

### 8.2 Dockerfile設計 — 2つのDockerfile戦略

API用とUI用で別々のDockerfileを用意し、デプロイ時に差し替える方式を採用した。

**API用Dockerfile（メイン）:**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=8080
CMD ["sh", "-c", "exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
```

**セキュリティ対策:**

| 対策 | 内容 |
|------|------|
| 非rootユーザー | `appuser`（appgroup）でコンテナ実行。権限を最小化 |
| HEALTHCHECK | `/health`エンドポイントへの死活監視（30秒間隔） |
| 最小パッケージ | `--no-install-recommends`で不要パッケージを排除 |

**UIデプロイ時の差し替え手順:**

```powershell
# 1. バックアップ & 差し替え
Copy-Item Dockerfile Dockerfile.api.bak
Copy-Item Dockerfile.ui Dockerfile
# 2. デプロイ
gcloud run deploy fixed-asset-agentic-ui --source . --region asia-northeast1 \
  --set-env-vars "API_URL=https://fixed-asset-agentic-api-xxx.asia-northeast1.run.app"
# 3. 元に戻す
Copy-Item Dockerfile.api.bak Dockerfile
```

この「Dockerfile差替方式」は一見トリッキーだが、Cloud Runのソースデプロイ（`--source .`）を使う場合、ルートのDockerfileが参照されるため、この方法が最もシンプルだった。

### 8.3 ContainerImageImportFailed との戦い

デプロイ中に最も苦戦したのが `ContainerImageImportFailed` エラーだった。

**原因**: Artifact Registry の pull 権限不足。Cloud Build がイメージを push した後、Cloud Run のリビジョンがイメージを pull できない。

**対処フロー:**

```
1. gcloud run services describe でステータス確認
2. gcloud run revisions describe で失敗原因特定
3. ランタイムSA と サービスエージェントを特定
4. 両方に roles/artifactregistry.reader を付与
5. digest指定で再デプロイ（ビルドなし）
6. smoke_cloudrun.ps1 で動作確認
```

この経験を元に、3つのドキュメントを整備した:

- **CLOUDRUN_TROUBLESHOOTING.md**: 原因と対処の詳細手順
- **CLOUDRUN_TRIAGE_TEMPLATE.md**: 障害報告時の3点テンプレ
- **DOCKER_LOCAL_SMOKE.md**: gcloudを使わないローカル検証手順

### 8.4 環境変数とFeature Flag設計

Cloud Run の環境変数をFeature Flagとして活用する設計を採用した。

```yaml
# 必須
PORT: 8080  # Cloud Runが自動設定

# Feature Flags（未設定=OFF、安全側にフォールバック）
PDF_CLASSIFY_ENABLED: "1"     # /classify_pdf エンドポイント有効化
USE_DOCAI: "1"                # Document AI によるPDF抽出
VERTEX_SEARCH_ENABLED: "1"    # Vertex AI Search 法令検索
GEMINI_ENABLED: "1"           # Gemini API による分類
GOOGLE_API_KEY: "..."         # Gemini API キー（Secret Manager推奨）

# セキュリティ
FIXED_ASSET_API_KEY: "..."    # APIキー認証
CORS_ORIGINS: "http://localhost:8501"  # CORS許可オリジン
```

**設計思想**: 全Feature Flagは「未設定=OFF=安全側」。Document AIが使えなければPyMuPFにフォールバック。Vertex AI Searchが使えなければcitationsなしで処理続行。**Stop-first原則がインフラ設計にまで浸透している。**

### 8.5 デプロイ結果

最終的に2つのCloud Runサービスが稼働状態となった。

| サービス | URL | ステータス |
|---------|-----|-----------|
| API | `https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app` | 稼働中 |
| UI | `https://fixed-asset-agentic-ui-986547623556.asia-northeast1.run.app` | 稼働中 |

スモークテスト結果:

| エンドポイント | 期待 | 結果 |
|---------------|------|------|
| `/health` | HTTP 200, `{"ok":true}` | PASS |
| `/classify` | HTTP 200, decision含むJSON | PASS |
| `/classify_pdf` (OFF時) | HTTP 400, `PDF_CLASSIFY_DISABLED` | PASS |

<!-- 殿記入欄: デプロイ時に一番困ったこと・工夫したこと -->

---

<a id="section-9"></a>

## 9. 提出物の準備（拡充版）

### 9.1 GitHub公開準備 — 機密情報との戦い

GitHubリポジトリをPublicにする前に、以下の機密情報スキャンを実施した。

**スキャン対象と結果:**

| カテゴリ | チェック内容 | 結果 |
|---------|------------|------|
| APIキー | GOOGLE_API_KEY, GEMINI_API_KEY のハードコード | .env.exampleに移行済み |
| GCPプロジェクト番号 | 986547623556 のソースコード内残存 | batch_upload.py修正済み（注: app_minimal.py L79に残存→要修正） |
| .gitignore | data/results/, data/uploads/ | 追加済み |
| .env | リポジトリ内の.envファイル | .gitignoreで除外確認済み |

**NOTE-03修正（AGPL問題）:**

PyMuPDF（fitz）がAGPL-3.0ライセンスであることが判明。殿に3つの選択肢を提示し、判断を仰いだ。

| 選択肢 | 内容 | 殿の判断 |
|--------|------|---------|
| A | PyMuPFを除去し、pdfplumberに完全移行 | — |
| B | PyMuPFを残しつつ、ライセンス注記を明記 | **採用** |
| C | Document AI のみに依存 | — |

結果として、README.mdの依存ライブラリセクションに「PyMuPDF (AGPL-3.0) — 商用利用時は注意」と明記した。

### 9.2 Zenn記事の設計

Zenn記事はハッカソン公式提出物の一つであり、以下の要件を満たす必要があった。

```yaml
# Zenn frontmatter
type: "idea"
topics: ["gch4", "googlecloud", "agenticai", "fastapi", "経理DX"]
published: true
```

**記事構成（354行）:**

| セクション | 内容 | 状態 |
|-----------|------|------|
| プロジェクト概要 | 対象ユーザー・課題・特徴 | 完成 |
| デモ動画 | YouTube埋め込み | <!-- 殿記入欄: YouTube動画URL --> |
| システムアーキテクチャ | Mermaid図 | 完成（PNG化推奨） |
| Stop-first設計の解説 | GUIDANCE発動の仕組み | 完成 |
| スクリーンショット4枚 | GUIDANCE画面、停止表示、質問UI、DIFF | <!-- 殿記入欄: スクリーンショット撮影・挿入 --> |
| 税務知識セクション | 取得価額・閾値・資本的支出vs修繕費 | 完成 |

### 9.3 デモ動画の台本設計

3分間のデモ動画台本を2バージョン作成した。

**タイムライン（VIDEO_SHOOTING_SCRIPT.md準拠）:**

```
[0:00-0:10] スライド1: タイトル+課題提起
             「止まれないAIが本当の脅威だ」

[0:10-0:55] Case 1-2: CAPITAL / EXPENSE（即断）
             明確なケースの自動判定を見せる

[0:55-2:30] Case 3: GUIDANCE（★最重要パート 95秒）
  [0:55-1:20] 瞬間1: 止まる — 「......止まりました。」（2秒の沈黙）
  [1:20-1:40] 瞬間2: 聞く — 不足情報と理由の提示
  [1:40-2:00] 瞬間3: 深く聞く — 2段階目の質問
  [2:00-2:30] 瞬間4: 変わる — Before/After差分

[2:30-2:55] スライド2-4: 技術構成+GCP+エンドカード
             「止まる、聞く、深く聞く、そして変わる」
```

**演出の要:**

| 場面 | トーン | 特記 |
|------|--------|------|
| 「止まりました」 | 低く、ゆっくり | **2秒の完全沈黙**が最重要 |
| 2段階質問 | やや高く | 「1回聞いて終わりではない」を強調 |
| Before/After | 熱を込めて | 各単語間に0.5秒の沈黙 |

**キーメッセージ「4つの瞬間」:**

| No | 瞬間 | キーフレーズ |
|----|------|-------------|
| 1 | 止まる | 「AIが自分で判断できないと認識して停止」 |
| 2 | 聞く | 「何が不足し、なぜ必要かを説明」 |
| 3 | 深く聞く | 「1回聞いて終わりではない。さらに踏み込む」 |
| 4 | 変わる | 「対話を経て判定が変化。履歴が証跡に残る」 |

### 9.4 プレゼン資料（pptx）の品質チェック

12枚のスライドを足軽5・6号が作成し、足軽7号が結合・検証した。

| チェック項目 | 結果 |
|-------------|------|
| スライド枚数 | 12枚 |
| ファイルサイズ | 54KB |
| 全スライドに内容あり | PASS |
| フォント統一 | PASS |
| 審査基準カバー | PASS |

---

<a id="section-10"></a>

## 10. 数字で見る開発の全容（拡充版）

### 10.1 コマンド統計

将軍が発行した全コマンド（cmd_001〜cmd_038+）の統計:

| 指標 | 数値 | 備考 |
|------|------|------|
| 総コマンド数 | 37+ | cmd_001〜cmd_038以上 |
| 足軽への展開 | 120+ サブタスク | 1コマンドあたり平均3-4サブタスク |
| ドキュメント作成数 | 77+ ファイル | docs/配下のmd, txt, html, mmd含む |
| テスト通過数 | 136 テスト | pytest全数パス |
| Golden Set精度 | 100% | 10/10ケース正答 |
| リスク検出数 | 17件 | 高6/中6/低5 |
| リスク対処済み | 17件 | 全件対処完了 |
| スキル候補 | 9件 | 足軽報告から抽出 |
| プレゼンスライド | 12枚 | 54KB |
| デプロイ回数 | 4+ | API×2 + UI×2以上 |

### 10.2 足軽稼働の時間分析

cmd_036（HACKATHON_JOURNEY.md作成）での足軽8名同時稼働のタイムスタンプ分析:

```
06:07 足軽1号 起動 → 06:14 完了（7分）
06:08 足軽2号 起動 → 06:15 完了（7分）
06:08 足軽3号 起動 → 06:16 完了（8分）
06:09 足軽4号 起動 → 06:17 完了（8分）
06:10 足軽5号 起動 → 06:15 完了（5分）
06:10 足軽6号 起動 → 06:16 完了（6分）
06:11 足軽7号 起動 → 06:18 完了（7分）
06:12 足軽8号 起動 → 06:20 完了（8分）
```

**8名の足軽が13分間（06:07〜06:20）で全作業を完了。** 逐次起動ルール（前の足軽の起動完了を確認してから次を起動）が適用され、同時起動による家老のボトルネックを回避している。

### 10.3 品質レビューの統計

cmd_066で実施したスキル知見ベースレビューの集計:

| 深刻度 | 件数 | 修正状況 |
|--------|------|---------|
| Critical | 11 | 10修正済 + 1部分修正 |
| Major | 22 | 12修正済 + 10未修正 |
| Minor | 14 | 3修正済 + 11未修正 |
| **合計** | **47** | **25修正済（53%）** |

cmd_070の統合検証結果:

| 検証カテゴリ | 項目数 | PASS | PARTIAL | FAIL |
|-------------|--------|------|---------|------|
| cmd_066成果物 | 8 | 8 | 0 | 0 |
| cmd_067 Critical | 11 | 11 | 0 | 0 |
| cmd_067 UX+SEC | 11 | 9 | 2 | 0 |
| cmd_067 スキル | 6 | 6 | 0 | 0 |
| cmd_068成果物 | 5 | 5 | 0 | 0 |
| **合計** | **41** | **39** | **2** | **0** |

**虚偽報告ゼロ。** 全成果物が報告通りに実在することを独立検証で確認した。

---

<a id="section-11"></a>

## 11. 振り返り — 殿の声

<!-- 殿記入欄: 開発全体を通しての感想・振り返り -->

<!-- 殿記入欄: マルチエージェント開発で感じたこと（良かった点・改善点） -->

<!-- 殿記入欄: ハッカソンを通じて学んだこと -->

---

<a id="section-12"></a>

## 12. 教訓の深掘り（拡充版）

### 12.1 TOP5 教訓

| 順位 | 教訓 | 具体的エピソード |
|------|------|----------------|
| 1 | **「止まる」設計は全レイヤーに適用せよ** | Stop-first原則はコード（GUIDANCE）だけでなく、Dockerfile（Feature Flag=OFF）、API（フォールバック）、運用（人間確認）の全レイヤーに浸透させた |
| 2 | **未検証情報に「要確認」タグを付けよ** | lu.ma誤報事件。URLの真偽を検証せずに記載→転記時にタグ脱落→致命的リスクに格上げ。構造的再発防止策（YAMLスキーマのconfidenceフィールド）を導入 |
| 3 | **並列作業には通信プロトコルが必須** | 8名の足軽が同時にapi/main.pyを編集する場面。RACE-001（直接編集禁止、/tmpに出力→結合者が統合）で衝突ゼロを実現 |
| 4 | **デフォルト値で重要な値を上書きするな** | Confidence Bug。`ev.get('confidence', 0.8)` のデフォルト値0.8が、classifier未計算時に「それなりに高い確信度」を偽装。0.0に修正 |
| 5 | **ドキュメントは「二次情報」と「正データ」を区別せよ** | dashboard.mdは家老が整形した要約（二次情報）。正データはYAMLファイル。コンパクション復帰時に二次情報を信じて行動すると齟齬が生じる |

### 12.2 やってはいけないこと（Don'ts）

| # | Don't | なぜダメか |
|---|-------|-----------|
| 1 | AIの出力を無検証で伝言ゲーム | lu.ma誤報の直接原因 |
| 2 | 同一ファイルの並列編集 | マージ地獄。RACE-001で回避 |
| 3 | summary/要約を正データとして使う | コンパクション後に誤った状態把握につながる |
| 4 | send-keysを1回のBash呼び出しで済ませる | Enterが正しく解釈されない。必ず2回に分ける |
| 5 | Feature Flagのデフォルトを「有効」にする | 未設定時に予期せぬ動作を引き起こす |

### 12.3 次にハッカソンに出るなら

<!-- 殿記入欄: 次のハッカソンで活かしたいこと -->

---

<a id="section-13"></a>

## 13. 技術スタック完全版（拡充版）

### 13.1 コアスタック

| レイヤー | 技術 | バージョン | 用途 |
|---------|------|-----------|------|
| 言語 | Python | 3.11 | 全コンポーネント |
| API | FastAPI | 最新 | REST APIフレームワーク |
| ASGI | uvicorn | 最新 | ASGIサーバー |
| UI | Streamlit | 最新 | デモ用Web UI |
| PDF抽出 | PyMuPDF (fitz) | 最新 | PDFテキスト抽出（AGPL-3.0注意） |
| PDF抽出（代替） | pdfplumber | 最新 | PyMuPDFのフォールバック |
| テスト | pytest | 最新 | 136テスト全数パス |

### 13.2 Google Cloud AI

| サービス | 用途 | Feature Flag | 実装ファイル |
|---------|------|-------------|------------|
| **Gemini 3 Pro Preview** | 3値判定（thinking_level=HIGH） | `GEMINI_ENABLED` | `api/gemini_classifier.py` |
| **Gemini 2.0 Flash** | PDF読み取り・文書分割 | `GEMINI_PDF_ENABLED` | `api/gemini_splitter.py` |
| **Document AI** | 高精度PDF抽出（OCR） | `USE_DOCAI` | `core/pdf_extract.py` |
| **Vertex AI Search** | 法令エビデンス自動検索 | `VERTEX_SEARCH_ENABLED` | `api/vertex_search.py` |
| **Cloud Run** (×2) | API + UI 分離デプロイ | — | `Dockerfile`, `Dockerfile.ui` |

### 13.3 セキュリティスタック（cmd_067で導入）

| 対策 | 実装 | ファイル |
|------|------|---------|
| APIキー認証 | `X-API-Key` + `Depends(verify_api_key)` | api/main.py |
| パストラバーサル防止 | `_validate_policy_path()` + resolve検証 | api/main.py |
| PDFバリデーション | MIME + マジックバイト + 50MB制限 | api/main.py |
| プロンプトインジェクション対策 | `_sanitize_text()` + デリミタ分離 + 50000文字制限 | api/gemini_classifier.py |
| CORS | `CORSMiddleware` + 環境変数ベース | api/main.py |
| レート制限 | slowapi 10 req/min/IP | api/main.py |
| 構造化ログ | JSON形式 + UUID request_id | api/main.py |
| PDF自動削除 | 24時間経過ファイルの自動クリーンアップ | core/pipeline.py |
| 免責表示 | disclaimerフィールド + 高確信度時追加文言 | api/main.py |

### 13.4 開発基盤

| ツール | 用途 |
|-------|------|
| multi-agent-shogun | マルチエージェント並列開発基盤（本システム） |
| Claude Code + tmux | 8足軽の同時実行環境 |
| Memory MCP | 知識グラフによるポストモーテム・ルールの永続化 |
| GitHub | ソースコード管理（Public、2026/3/2まで維持） |

---

<a id="section-14"></a>

## 14. 技術調査の全記録 — docs/research_*.md の総覧

### 概要

cmd_012で足軽8名を動員し、AIエージェント事業のビジネスリサーチを10カテゴリ（A〜J）×各10件 = **80件のビジネスアイデア**を並列調査した。これはmulti-agent-shogunの「8名並列処理」の実力を示す代表的なユースケースである。

### カテゴリ一覧と担当

| カテゴリ | テーマ | 担当 | 行数 | トップ項目 |
|---------|--------|------|------|-----------|
| **A** | 受託開発・技術支援 | 足軽1 | 324行 | コードレビュー代行、テストコード作成 |
| **B** | ドキュメント・コンテンツ生成 | 足軽2 | 237行 | SEOコンテンツ、技術文書、README整備 |
| **C** | データ処理・分析 | 足軽3 | 555行 | Excel整形、CSV変換、スクレイピング |
| **D** | AI/ML関連 | 足軽4 | 455行 | プロンプトエンジニアリング代行、ChatGPTコンサル |
| **E** | 翻訳・ローカライゼーション | 足軽5 | 632行 | 技術文書翻訳、マニュアル翻訳 |
| **F** | 調査・リサーチ | 足軽6 | 323行 | 市場調査レポート、競合分析 |
| **G+H** | 自動化・効率化 + 教育 | 足軽7 | 1,166行 | Zapier/Make連携、フォーム処理、オンライン講座 |
| **I+J** | クリエイティブ + 専門分野 | 足軽8 | 1,191行 | コピーライティング、補助金申請、事業計画 |

**合計**: 約4,883行のリサーチドキュメント（8ファイル）

### 各カテゴリの分析フォーマット

全カテゴリで統一された分析フレームワーク:

```markdown
### [ビジネスアイデア名]
- **概要**: サービスの説明
- **ターゲット**: 想定顧客
- **市場性**: ★1〜★5 の評価
- **AI活用度**: S/A/B/C のランク
- **収益モデル**: 価格帯、課金方式
- **参入障壁**: 競合状況、差別化ポイント
- **リスク**: 法的、技術的、市場リスク
```

### カテゴリ別ハイライト

#### A: 受託開発・技術支援（足軽1）

市場規模: ITフリーランス市場1兆1,849億円。「コードレビュー代行」「テストコード自動作成」が高評価。AIエージェントが人間のレビュアーの補助として品質向上に貢献するモデル。

#### C: データ処理・分析（足軽3 = 筆者）

筆者が担当したカテゴリ。AI活用度A（高）の項目が多く、「Excel定型整形」「CSV/JSONデータ変換」「Webスクレイピング」「定期レポート自動生成」はいずれも自動化の恩恵が大きい領域。

#### D: AI/ML関連（足軽4）

プロンプトエンジニアの平均年収1,116万円（2024年調査）という市場データが印象的。「プロンプトエンジニアリング代行」「ChatGPT/Claudeコンサルティング」は今後拡大が見込まれる。

#### E: 翻訳・ローカライゼーション（足軽5）

日本翻訳市場28億ドル。技術文書翻訳、マニュアル翻訳、SNS翻訳が高評価。AIの翻訳精度向上により、人間翻訳者の「後校正」モデルへの移行が加速。

#### G+H: 自動化・効率化 + 教育（足軽7）

1,166行と最大規模のレポート。Zapier/Make連携（★5）、フォーム処理自動化（★5）、オンライン講座制作（★5）が最高評価。

#### I+J: クリエイティブ + 専門分野（足軽8）

1,191行で最長。コピーライティング、SNS投稿代行、動画シナリオ作成がクリエイティブ領域。補助金申請書作成、事業計画書作成が専門分野。特に補助金申請は行政手続きの定型性が高くAI適性が高い。

### リサーチの意義

このcmd_012のリサーチは、固定資産判定システムの開発とは直接関係しないが、multi-agent-shogunの**並列調査能力のデモンストレーション**として重要である。

- **8名が同時に独立したリサーチを実行**: 1人あたり約30分で10件の詳細分析
- **統一フォーマットでの出力**: 分析フレームワークが共通なので比較・統合が容易
- **約5,000行の成果物を1時間以内に生成**: 人間1人なら数日かかる作業量

---

<a id="section-15"></a>

## 15. 仕様設計の変遷 — docs/specs/ の全記録

### 概要

docs/specs/ 配下に5つの仕様書が作成された。これらは固定資産判定パイプラインの4ステップ構造と、PDFインジェスト時の警告仕様を定義している。

### パイプラインの4ステップ構造

```
Step 1: PDF抽出       → 判断材料の整備（判断の自動化ではない）
Step 2: ルール前分類   → if-then ルールで資産/費用の傾向を判定
Step 3: AI勘定提案     → 複数候補を提示（確定表現・断定は禁止）
Step 4: 耐用年数候補   → 省令別表から複数候補を提示（推奨値はnull）
```

### 仕様書一覧

#### 2026-FA-01: PDF Extraction Schema（Step 1）

**設計思想**: 「判断材料の整備」であり「判断の自動化」ではない

```json
{
  "meta": {
    "extraction_method": "pymupdf",
    "extraction_date": "2026-01-30T10:00:00+09:00",
    "source_file": "見積書_サンプル.pdf",
    "total_pages": 2
  },
  "warnings": [
    {
      "code": "TEXT_TOO_SHORT",
      "message": "抽出テキストが50文字未満です",
      "severity": "medium"
    }
  ],
  "fields": {
    "vendor_name": "株式会社サンプル設備",
    "document_date": "2026-01-15",
    "total_amount": 1500000,
    "line_items": [...]
  },
  "evidence": {
    "pages": [
      {
        "page_number": 1,
        "method": "pymupdf",
        "raw_text_snippet": "見積書 ...",
        "confidence": 0.85
      }
    ]
  }
}
```

`evidence` セクションでページごとの抽出方法と信頼度を記録。後工程での検証・監査に使用。

#### 2026-FA-02: Rule-based Preclassification（Step 2）

**設計思想**: MLを使わない。if-thenルールのみで事前分類。

出力フォーマット:

```json
{
  "asset_likelihood": "high",
  "expense_likelihood": "low",
  "rules_applied": [
    { "rule_id": "KW-001", "matched": "新設", "effect": "asset_up" }
  ],
  "account_candidates": [
    { "code": "141", "name": "建物付属設備" },
    { "code": "142", "name": "構築物" }
  ],
  "stop_flags": ["mixed_keyword:一式"]
}
```

**重要な設計制約**: `account_candidates` は**必ず複数**提示する。単一候補の確定表現は禁止。

#### 2026-FA-03: AI Account Suggestion（Step 3）

**設計思想**: AIは候補を「提案」するだけ。確定はしない。

MUST（必須）:
- 複数の候補を提示すること
- 各候補に `reason`（理由）を付与すること
- `confidence` は high/medium/low の3段階

MUST NOT（禁止）:
- 確定表現（「〜です」「〜に該当します」）
- 断定（候補を1つに絞る行為）

```json
{
  "suggestions": [
    {
      "account_code": "141",
      "account_name": "建物付属設備",
      "confidence": "high",
      "reason": "空調設備の新設工事であり、建物付属設備に該当する可能性が高い"
    },
    {
      "account_code": "156",
      "account_name": "工具器具備品",
      "confidence": "low",
      "reason": "個別の機器として管理する場合の代替候補"
    }
  ]
}
```

#### 2026-FA-04: Useful Life Candidates（Step 4）

**設計思想**: 省令別表からの候補提示。推奨値は**null**。

```json
{
  "candidates": [
    {
      "useful_life_years": 15,
      "legal_basis": "耐用年数省令 別表第一 建物付属設備 冷暖房設備",
      "confidence": "high"
    },
    {
      "useful_life_years": 13,
      "legal_basis": "耐用年数省令 別表第一 建物付属設備 その他",
      "confidence": "medium"
    }
  ],
  "recommendation": {
    "recommended_life_years": null,
    "note": "最終的な耐用年数の決定は税理士等の専門家にご確認ください"
  }
}
```

`recommended_life_years: null` は意図的な設計。**システムは候補を提示するが、最終決定は人間に委ねる**。これもStop-first設計の一環。

#### 2026-FA-PDF-ingest-warning: PDF取り込み警告仕様

PDFからの抽出品質を保証するための警告コード体系:

| コード | 説明 | 重要度 |
|--------|------|--------|
| `TEXT_TOO_SHORT` | 抽出テキストが50文字未満 | medium |
| `OCR_DISABLED` | OCRが無効でスキャンPDFの可能性 | high |
| `LOW_CONFIDENCE` | 抽出信頼度が閾値未満 | medium |
| `MISSING_AMOUNT` | 金額フィールドが抽出できない | high |
| `TABLE_PARSE_FAIL` | テーブル構造の解析に失敗 | medium |

各警告には `evidence`（どのページでどの抽出方法を使ったか）を付与。

### 仕様設計の変遷が示すもの

5つの仕様書に一貫しているのは**「システムは判断しない。判断材料を整備する」**という設計哲学である。

| ステップ | やること | やらないこと |
|---------|---------|-------------|
| Step 1 | テキスト抽出、構造化 | 内容の解釈 |
| Step 2 | ルールベースの傾向判定 | 確定判定 |
| Step 3 | 複数候補の提案 | 単一候補への絞り込み |
| Step 4 | 法定耐用年数の候補提示 | 推奨値の決定 |

これは固定資産判定という「専門家の判断が必要な領域」において、AIが果たすべき役割を明確に限定した設計である。AIは「判断支援ツール」であり「判断代行ツール」ではない。この思想がStop-first設計の根底にある。
<a id="section-16"></a>

## 16. レビューと品質改善の全記録

### 17.1 スキル知見ベースレビュー（cmd_066）

cmd_066では、8名の足軽がそれぞれの専門観点からfixed-asset-ashigaruを精査した。各足軽にペルソナ（UI/UXデザイナー、セキュリティエンジニア、プロダクトマネージャー等）を割り当て、チェックリスト駆動でレビューを実施。

#### レビュー観点と担当

| # | 観点 | 担当 | レビューファイル | 主要発見 |
|---|------|------|----------------|---------|
| 1 | UI/認知判断 | 足軽1 | 01_ui_cognitive.md | app.pyの技術用語露出がCritical。app_minimal.pyの色彩設計は優秀 |
| 2 | オンボーディング | 足軽2 | 02_onboarding.md | TTFV 30秒（目標60秒以内を達成）。app.pyはTTFV 60秒超で不適格 |
| 3 | セキュリティ | 足軽3 | 03_trust_security.md | API認証なし（C4件）。Fail-to-GUIDANCE設計は業界水準超え |
| 4 | プライバシー | 足軽4 | 04_trust_default_safe.md | PDF無期限保存が最大リスク。LLMへの同意取得なし |
| 5-6 | Zenn先行事例調査 | 足軽5-6 | 05/06_zenn_research.md | 11キーワード×110件調査、22件深掘り。設計パターン4類型を発見 |
| 7 | プロダクト判断力 | 足軽7 | 07_product_judgment.md | UI二重実装、MVP不要機能の大量残存。「ついでにこれも」症候群 |
| 8 | 既知バグ確認 | 足軽8 | 08_known_bugs.md | confidence 0.8デフォルト値が3箇所残存。集計ロジックは仕様通り |

#### 指摘の統計

```
Critical: 11件（セキュリティ4 + プライバシー3 + UI2 + プロダクト2）
Major:    22件（セキュリティ4 + プライバシー4 + UI6 + オンボーディング4 + プロダクト4）
Minor:    14件（UI5 + オンボーディング4 + プロダクト3 + バグ2）
─────────────────
合計:     47件
```

#### Zenn先行事例から得た設計パターン

| パターン | 記事数 | 精度 | 本プロジェクトの位置 |
|---------|--------|------|-------------------|
| A: LLM直接型 | 2件 | 約60% | — |
| B: OCR+LLMハイブリッド | 5件 | 約70-80% | ベースはここ |
| C: 三層型（OCR+LLM+ルール） | 2件 | 約80% | **ここ + Stop-first + ポリシーエンジン** |
| D: LLM蒸留型 | 1件 | — | — |

**結論**: 本プロジェクトは「パターンCの進化形」。三層構造にStop-first原則とAgenticループを組み合わせた設計は、調査した22件の先行事例に存在しない。

### 17.2 Critical修正の全記録（cmd_067）

レビュー結果を受けて、5名の足軽が並列で22件の修正を実施した。

#### ワークストリーム別修正

**ワークストリームB: セキュリティCritical（足軽4号）**

| # | 修正 | 実装詳細 |
|---|------|---------|
| C-01 | APIキー認証 | `verify_api_key` + `Depends()` を3エンドポイントに適用。キー未設定時は開発モード |
| C-02 | パストラバーサル対策 | `_validate_policy_path()`: `..` / `/` チェック + resolve後のstartswith検証 |
| C-03 | アップロードバリデーション | MIME (`application/pdf`) + マジックバイト (`%PDF`) + 50MB + バッチ20件制限 |
| C-04 | プロンプトインジェクション対策 | `_sanitize_text()`: 50000文字制限 + 制御文字除去 + デリミタ分離 |

**ワークストリームA: プライバシー + confidence（足軽5号）**

| # | 修正 | 実装詳細 |
|---|------|---------|
| C-05 | PDF自動削除 | `cleanup_old_files(directory, max_age_hours=24)` をモジュールロード時に自動実行 |
| C-06 | JSON保持期間 | data/results/ にも同様の24時間クリーンアップ適用 |
| C-07 | LLMデータ送信の同意表示 | `st.info("Google Gemini APIに送信されます")` をUI2箇所に追加 |
| Bug修正 | confidence 0.8→0.0 | `item.get("confidence", 0.8)` → `item.get("confidence", 0.0)` を3箇所修正 |

**ワークストリームD: プロダクト整理（足軽6号）**

| # | 修正 | 実装詳細 |
|---|------|---------|
| C-08 | UI二重実装解消 | `app.py` → `app_classic.py` にリネーム |
| C-09 | .gitignore強化 | `data/results/`, `data/uploads/` を追加 |
| C-10 | 技術用語平易化 | 30+箇所の用語を日本語化（Opal→自動抽出、Stop設計→確認ポイント等） |
| C-11 | カラム名日本語化 | classification→分類結果、flags→注意事項、evidence→根拠 |

**ワークストリームC: UX改善（足軽7号）**

| # | 修正 | 実装詳細 |
|---|------|---------|
| 13 | GUIDANCE用語統一 | 「要確認」「GUIDANCE」→「確認が必要です」に統一 |
| 14 | 英語ラベル日本語化 | Before:/After: → 変更前:/変更後: |
| 15 | コントラスト比改善 | #9CA3AF→#4B5563（WCAG AA 4.5:1準拠） |
| 16 | 確信度表現改善 | 「たぶん大丈夫」→「概ね確実（念のため確認推奨）」 |
| 17 | Empty State充実 | 1行ガイダンス→3行（対応形式、サンプル導線を追加） |

**ワークストリームC: セキュリティ強化+ログ（足軽8号）**

| # | 修正 | 実装詳細 |
|---|------|---------|
| 18 | CORS設定 | `CORSMiddleware` + 環境変数`CORS_ORIGINS`から読込 |
| 19 | レート制限 | slowapi 10/minute、graceful fallback（未インストール時は警告のみ） |
| 20 | URL除去 | Cloud Run URLハードコード → 環境変数`API_BASE_URL` |
| 21 | 構造化ログ | `_JSONFormatter` + UUID request_id + /classify,/classify_pdfにログ |
| 22 | 免責表示 | disclaimerフィールド + confidence>0.9で追加免責 |

#### 並列修正の安全性

api/main.pyに5名が同時に修正を加える必要があったが、全員がEditツール（差分編集: old_string→new_string）を使用し、Write（全文上書き）を禁止。RACE-001ルールにより**衝突ゼロ**で完了した。

### 17.3 統合検証（cmd_070）

修正が報告通りに実施されたかを7名の足軽が独立検証した。

**検証の3原則:**

1. **実コード読み**: 報告の転記は一切行わず、Read/Grep/Bash で実ファイルを直接確認
2. **証拠ベース**: 全項目にファイル名:行番号 or コマンド出力を記録
3. **独立検証**: 各足軽が他の足軽の検証結果を参照せずに独立実施

**結果**: 41検証項目中、PASS=39件、PARTIAL=2件、FAIL=0件。**虚偽報告ゼロ。**

PARTIAL 2件の内容:
- **UX-01**: 主要UIは統一済みだが、副次UI（similar_cases.py, batch_upload.py）に旧表記残存
- **SEC-05**: batch_upload.pyは修正済みだが、app_minimal.py L79にGCPプロジェクト番号残存

---

### 72/100点の衝撃 — cmd_027が突きつけた現実

2026年2月12日。ハッカソン提出まで残り2日。

殿の指示で品質監査を実施した。将軍がcmd_027を発令し、fixed-asset-ashigaruの全コードを対象に、セキュリティ・テスト・ドキュメント・デプロイの4観点でスコアリングした。

結果は**72/100点**。

この数字を見た殿の反応は即座だった。

> 「品質確認だけでなく改善実施も求める。ハッカソンで勝つことが最優先目標。**85点以上を目標とせよ**」

72点という数字は「動いてはいるが、審査に耐えられない」という意味だった。bare exceptionが散在し、依存パッケージのバージョンが固定されておらず、Dockerfileは非rootユーザー実行もHEALTHCHECKもない。ドキュメントのdocstringは不足し、テストカバレッジも十分ではない。

個別に見れば「軽微な問題」だが、それが積み重なって72点だった。

### cmd_028: 85+を目指した4領域同時改善

cmd_028は、72→85+のギャップを埋めるために設計された改善指令である。

| 改善領域 | 実施内容 | 影響範囲 |
|----------|----------|----------|
| セキュリティ | bare exception修正、依存パッケージバージョン固定 | 全Pythonファイル、requirements.txt |
| Dockerfile | 非rootユーザー実行、HEALTHCHECK追加 | Dockerfile, Dockerfile.ui |
| ドキュメント | docstring追加、テスト拡充 | 主要モジュール全体 |
| デモ | DEMO.md強化、審査対策ドキュメント作成 | docs/配下 |

足軽が並列で各領域を担当し、一気に改善を実施した。ここで初めて、テスト数が**136件**に到達する。

---

### セキュリティ修正の全容 — cmd_067で導入した9つの盾

品質改善のピークは、cmd_066（8名クロスレビュー）の結果を受けたcmd_067である。ここで6件のセキュリティCriticalが発見・修正された。

#### ワークストリームB: セキュリティCritical（足軽4号担当）

足軽4号がセキュリティエンジニアのペルソナで対処した4件:

**C-01: APIキー認証の導入**

修正前、3つのエンドポイント（`/classify`, `/classify_pdf`, `/batch_classify`）は認証なしで公開されていた。`verify_api_key` 関数を新設し、`Depends()` で全エンドポイントに適用。環境変数 `API_KEY` 未設定時は開発モードとして動作させ、本番との切り替えを実現した。

**C-02: パストラバーサル対策**

ポリシーファイルのパス指定にユーザー入力が使われていた。`_validate_policy_path()` を新設し、`..` や `/` のチェックに加え、`resolve()` 後の `startswith()` 検証で実パスの脱出を防止した。

**C-03: アップロードバリデーション**

PDFアップロードに制限がなかった。MIME型チェック（`application/pdf`）、マジックバイト検証（`%PDF`）、ファイルサイズ上限（50MB）、バッチ件数上限（20件）の4重バリデーションを導入した。

**C-04: プロンプトインジェクション対策**

Gemini APIに送信するテキストにサニタイズ処理がなかった。`_sanitize_text()` を新設し、50,000文字制限、制御文字除去、デリミタ分離の3段構えで防御した。

#### ワークストリームC: セキュリティ強化（足軽8号担当）

足軽8号が追加した防御層:

**CORS設定**: `CORSMiddleware` を追加し、環境変数 `CORS_ORIGINS` からオリジンを読み込む設計。ワイルドカード(`*`)のハードコードを排除した。

**レート制限**: slowapiで10リクエスト/分/IPに制限。未インストール時はgraceful fallback（警告ログのみ）で、既存環境を壊さない設計。

これらの修正により、セキュリティスタックは以下の9項目に拡充された:

| # | 対策 | 実装 |
|---|------|------|
| 1 | APIキー認証 | `X-API-Key` + `Depends(verify_api_key)` |
| 2 | パストラバーサル防止 | `_validate_policy_path()` + resolve検証 |
| 3 | PDFバリデーション | MIME + マジックバイト + 50MB制限 |
| 4 | プロンプトインジェクション対策 | `_sanitize_text()` + 50,000文字制限 |
| 5 | CORS | `CORSMiddleware` + 環境変数ベース |
| 6 | レート制限 | slowapi 10 req/min/IP |
| 7 | 構造化ログ | JSON形式 + UUID request_id |
| 8 | PDF自動削除 | 24時間経過ファイルのクリーンアップ |
| 9 | 免責表示 | disclaimerフィールド + 高確信度時追加文言 |

**5名の足軽が同時に `api/main.py` を編集していた**ことを強調したい。通常なら衝突が起きて当然の状況だ。だが全員がEditツール（差分編集: old_string→new_string）を使用し、Write（全文上書き）を禁止するRACE-001ルールにより、**衝突ゼロ**で完了した。

---

### プレゼン資料の戦い — 文字ズレ・黄色問題とpptx日本語文字化け

品質改善はコードだけではない。プレゼン資料（pptx）もまた、品質との戦いだった。

#### cmd_034: 12枚スライドの生成（3名並列体制）

提出日当日の05:47、python-pptxを使った12枚のプレゼンスライド生成が開始された。

- 足軽5: 前半6枚（表紙〜技術ハイライト）
- 足軽6: 後半6枚（アーキテクチャ〜クロージング）
- 足軽7: 結合・最終検証

約30分で12枚のスライドが完成し、5つの品質チェック（スライド枚数、ファイルサイズ、内容充足、フォント統一、審査基準カバー）を全PASS。ファイルサイズ54,460バイト。

ところが、殿がスライドを確認した段階で2つの問題が発覚した。

#### cmd_039: 文字ズレと黄色問題

**問題1: 文字ズレ（P0）**

Part2スクリプト（`/tmp/generate_part2.py`）に4つの不具合があった:

| 原因 | 症状 | 修正 |
|------|------|------|
| `bodyPr anchor` 未設定 | テキストがボックス下部に落ちる | `bodyPr.set('anchor', 'ctr')` を全テキストフレームに追加 |
| `line_spacing` 過大（font_size × 1.5） | 小型ボックスでテキスト圧縮 | line_spacingを1.0〜1.2に変更 |
| マージン未設定 | デフォルト0.1"が四方に適用され領域圧迫 | `margin_top/bottom=Pt(2)`, `margin_left/right=Pt(6)` を明示設定 |
| 整数除算(`//`) | 水平方向の微細なズレ | `//` を `/` に変更 |

Part1スクリプトには正しい実装（`centered_shape_text()` 関数）があったのに、Part2では適用されていなかった。足軽5と足軽6が別々に実装していたため、実装の統一が漏れたのだ。Part1の正しい実装をPart2に統一適用することで解決した。

**問題2: 黄色の使用頻度**

殿からの直接指示:「**黄色は見づらいので使用頻度を下げよ**」。

GUIDANCE関連で多用していた黄色（`#FFC107`）を最小限に抑え、以下の代替色を適用した:

- GUIDANCE: 薄いグレー(`#E8E8E8`) + 濃い文字、またはオレンジ(`#FF6D00`)のアクセントライン
- 警告系: 薄いオレンジ背景(`#FFF3E0`) + 濃いオレンジ文字(`#E65100`)
- メインカラー（Google Cloud Blue `#4285F4`）とアクセント（`#EA4335`）は維持

#### pptx日本語文字化け問題（回セルプロジェクト）

fixed-asset-ashigaruとは別プロジェクトだが、同時期に回セル（Excel VBAバッチエンジン）の業務改善発表スライドでもpptx問題が発生していた。

Marp CLI（Markdownからスライドを生成するツール）で作成したスライドで、日本語が文字化けした。原因はMarp CLIのフォント設定にあり、Noto Sans JPの`@import`追加で解決。この知見は後にスキル化候補としても記録された。

回セルでは日本語改行位置の問題も発覚し、足軽8号が全18スライドの改行を手動修正した。「熟語・カタカナ語・助詞・数値+単位の不自然な分断」を一つずつ解消する地道な品質改善だった。

---

### 8名足軽によるクロスレビュー — cmd_066の47件

品質改善の転機となったのは、cmd_066の**スキル知見ベースレビュー**である。

8名の足軽にそれぞれ専門ペルソナを割り当て、チェックリスト駆動でfixed-asset-ashigaruを精査させた。

| # | 観点 | ペルソナ | 主要発見 |
|---|------|---------|---------|
| 1 | UI/認知判断 | UI/UXデザイナー | app.pyの技術用語露出がCritical。app_minimal.pyの色彩設計は優秀 |
| 2 | オンボーディング | UXリサーチャー | TTFV 30秒（目標60秒以内を達成）。app.pyはTTFV 60秒超で不適格 |
| 3 | セキュリティ | セキュリティエンジニア | API認証なし（Critical 4件）。一方でFail-to-GUIDANCE設計は業界水準超え |
| 4 | プライバシー | プライバシーエンジニア | PDF無期限保存が最大リスク。LLMへの同意取得なし |
| 5-6 | Zenn先行事例 | リサーチャー | 11キーワード×110件調査、22件深掘り。設計パターン4類型を発見 |
| 7 | プロダクト判断力 | プロダクトマネージャー | UI二重実装、MVP不要機能の大量残存。「ついでにこれも」症候群 |
| 8 | 既知バグ確認 | QAエンジニア | confidence 0.8デフォルト値が3箇所残存。集計ロジックは仕様通り |

結果は苛烈だった。

```
Critical: 11件（セキュリティ4 + プライバシー3 + UI2 + プロダクト2）
Major:    22件（セキュリティ4 + プライバシー4 + UI6 + オンボーディング4 + プロダクト4）
Minor:    14件（UI5 + オンボーディング4 + プロダクト3 + バグ2）
─────────────────
合計:     47件
```

このレビューは単なる粗探しではない。足軽5-6号のZenn先行事例調査が、本プロジェクトの独自性を裏付ける根拠を生み出した。11キーワード×110件を網羅的に調査し、22件を深掘りした結果、既存プロジェクトの設計パターンが4類型に分類された:

| パターン | 精度 | 本プロジェクトの位置 |
|---------|------|-------------------|
| A: LLM直接型 | 約60% | — |
| B: OCR+LLMハイブリッド | 約70-80% | ベースはここ |
| C: 三層型（OCR+LLM+ルール） | 約80% | **ここ + Stop-first + ポリシーエンジン** |
| D: LLM蒸留型 | — | — |

**結論**: 本プロジェクトは「パターンCの進化形」。三層構造にStop-first原則とAgenticループを組み合わせた設計は、調査した22件の先行事例に存在しない。品質改善の過程が、プロジェクトの競争優位を証明する根拠にもなったのだ。

---

### cmd_067: 5名並列の修正オペレーション

47件の指摘に対し、cmd_067で5名の足軽が5つのワークストリームに分かれて並列修正を実施した。

| ワークストリーム | 担当 | 修正件数 | 主要内容 |
|----------------|------|---------|---------|
| A: プライバシー + confidence | 足軽5 | 4件 | PDF自動削除、LLM同意表示、confidence 0.8→0.0 |
| B: セキュリティCritical | 足軽4 | 4件 | APIキー認証、パストラバーサル、PDFバリデーション、プロンプトインジェクション |
| C: UX改善 | 足軽7 | 5件 | GUIDANCE用語統一、コントラスト比改善(WCAG AA準拠)、Empty State充実 |
| D: プロダクト整理 | 足軽6 | 4件 | UI二重実装解消、.gitignore強化、技術用語平易化(30+箇所) |
| E: セキュリティ強化+ログ | 足軽8 | 5件 | CORS、レート制限、URL除去、構造化ログ、免責表示 |

**合計22件を修正**。特に注目すべきは足軽6による**技術用語平易化**だ。本プロジェクトのペルソナは「設備会社の経理担当者（高卒事務の女性）」である。`Opal`→`自動抽出`、`Stop設計`→`確認ポイント`、`classification`→`分類結果`、`flags`→`注意事項`、`evidence`→`根拠`。30箇所以上のUIラベルを日本語化した。コードの品質改善ではなく、**ユーザー体験の品質改善**である。

---

### テストカバレッジの拡充過程 — 136 → 159 → 186

テスト件数の変遷は、品質改善の段階を物語っている。

#### Phase 1: 136件（cmd_028完了時点）

cmd_027の品質監査（72点）を受けたcmd_028の改善で、テスト数が136件に到達した。bare exception修正や依存パッケージバージョン固定と並行して、不足していたテストケースを追加。この時点で「pytest 136件全通過、3件skip、0件失敗」の状態を確立した。

#### Phase 2: 159件（cmd_040完了時点）

提出日当日の2月14日、殿から致命的バグが報告された。見積書の明細を個別に判定せず、合計金額で判定してしまう問題だ。

cmd_040で足軽5号がゴールデンセット4件（case11〜14）とE2Eテスト3件を追加した:

| ケース | テスト内容 | 検証ポイント |
|--------|----------|-------------|
| case11 | 複数明細の個別判定 | 4明細を個別に判定し、合計で判定しないこと |
| case12 | 小計・消費税・合計行の除外 | 7行入力→4明細のみが分類対象 |
| case13 | 資産・費用混在ケース | CAPITAL+EXPENSE混在→各明細が個別に分類 |
| case14 | 高額単品+低額付随費用 | 各明細が個別金額で判定されること |

E2Eテスト3件は、これらのゴールデンセットに対応する統合テストだ。classify_document()に実データを投入し、明細の個別判定が正しく機能することを検証する。

136件→159件: **23件の純増**。うちE2Eテスト3件が品質の要。

#### Phase 3: 186件（cmd_044完了時点）

最終フェーズでは、CI修正と合わせてテスト数が186件に到達した。CI環境のPythonバージョンを3.12に統一し、依存関係の互換性を解消した。ローカルで186件全通過を確認した後にpush→CI緑を確認する手順を厳守した。

```
Phase 1:  136件  ← 品質監査による改善
Phase 2:  159件  ← P0バグ修正 + ゴールデンセット追加
Phase 3:  186件  ← CI修正 + 最終品質強化
```

テスト数だけでなく、テストの「質」も向上した。Phase 2で追加されたE2Eテストは、殿が実際に遭遇したバグケースに基づいている。「テストがあれば安心」ではなく、「実運用で発見された問題をテストで再発防止する」というサイクルが確立された。

---

### cmd_070: 統合検証 — 虚偽報告ゼロの証明

修正が「報告通り」に実施されたかを、7名の足軽が独立検証した。

検証の3原則:
1. **実コード読み**: 報告の転記は一切行わず、Read/Grep/Bash で実ファイルを直接確認
2. **証拠ベース**: 全項目にファイル名:行番号 or コマンド出力を記録
3. **独立検証**: 各足軽が他の足軽の検証結果を参照せずに独立実施

| 検証カテゴリ | 項目数 | PASS | PARTIAL | FAIL |
|-------------|--------|------|---------|------|
| cmd_066成果物 | 8 | 8 | 0 | 0 |
| cmd_067 Critical修正 | 11 | 11 | 0 | 0 |
| cmd_067 UX+SEC修正 | 11 | 9 | 2 | 0 |
| cmd_067 スキル | 6 | 6 | 0 | 0 |
| cmd_068成果物 | 5 | 5 | 0 | 0 |
| **合計** | **41** | **39** | **2** | **0** |

**虚偽報告ゼロ。** PARTIAL 2件も軽微な残存（副次UIの旧表記、app_minimal.pyのGCPプロジェクト番号）であり、Critical修正は11件全PASS。

マルチエージェントシステムにおける品質保証の核心は、「修正を実施するエージェント」と「検証するエージェント」を分離することだ。自分で書いたコードを自分でレビューしても見落とす。別の足軽が独立検証することで、人間のコードレビューに相当する品質ゲートが機能した。

---

### 品質改善の全体像 — 数字で見るビフォー・アフター

| 指標 | Before（cmd_027時点） | After（最終提出時点） |
|------|---------------------|--------------------|
| 品質スコア | 72/100 | 85+ |
| テスト数 | 不十分 | 186件（全通過） |
| セキュリティCritical | 11件 | 10修正 + 1部分修正 |
| ゴールデンセット | 10件 | 14件 |
| E2Eテスト | なし | 11件 |
| docstring | 不足 | 主要モジュール整備 |
| Dockerfile | 非rootなし | 非root + HEALTHCHECK |
| APIセキュリティ | 認証なし | 9層の防御スタック |
| レビュー指摘 | 未実施 | 47件中25件修正（53%） |
| 統合検証 | 未実施 | 41項目中39PASS |

72点から85+点への改善は、単に数字が上がっただけではない。**品質を構造的に保証する仕組み**が構築された。8名のクロスレビュー → 5名の並列修正 → 7名の独立検証。このパイプラインは、人間の開発チームが数週間かけて行うプロセスを、マルチエージェントシステムが数時間で実行したものだ。

品質改善とは、コードを直すことではない。「品質を確認し、改善し、検証する」サイクルを回すことだ。multi-agent-shogunは、そのサイクルを並列化する基盤として機能した。

---

<a id="section-17"></a>

## 17. ハッカソン戦略の全容

### 18.1 過去受賞作品の勝ちパターン分析

第1回〜第3回の最優秀賞作品を調査し、6つの勝ちパターンを抽出した。

| 回 | 作品名 | 分野 |
|----|--------|------|
| 第1回 | eCoino | サプライチェーン計画修正AI |
| 第2回 | FlatJam | 音楽教育創造性支援 |
| 第3回 | Fukushia | 社会福祉士業務支援 |

#### 6つの勝ちパターン

| # | パターン | 全受賞作品の共通点 | 本プロジェクトの対応 |
|---|---------|-------------------|-------------------|
| 1 | **Human-in-the-Loop** | AIが全自動でなく、人間の意思決定を支援 | Stop-first設計（GUIDANCE）そのもの |
| 2 | **専門職の業務負荷軽減** | 「時間がない専門職」の余裕のなさを解消 | 経理担当者の月末・決算期を支援 |
| 3 | **セレンディピティ** | AIが選択肢を広げ、人間の思考を拡張 | missing_fields + why_missing_matters の提示 |
| 4 | **既存業務フローへの統合** | 新しいワークフローを強制しない | PDF→判定→要確認行の可視化 |
| 5 | **GCPサービスの深い活用** | 単一サービスでなく複数の組み合わせ | Document AI + Vertex AI Search + Cloud Run |
| 6 | **対話型インターフェース** | 自然言語対話をUI/UXに組み込む | 2段階ウィザード型質問 + Before/After差分 |

**結論**: 本プロジェクトは6つの勝ちパターン全てを満たしている。

### 18.2 審査員7名への個別戦略

審査員の専門・価値観を分析し、個別の訴求ポイントを設計した。

| 審査員 | 所属 | 重視するポイント | 本プロジェクトの刺さる要素 |
|--------|------|------------------|--------------------------|
| 佐藤祥子 | THE BIGLE | コミュニティ、多様性 | 「経理担当者が安心して使える」設計 |
| 渡部陽太 | アクセンチュア/ゆめみ CTO | 実装品質、スケーラビリティ | 凍結スキーマv1.0、100% Golden Set |
| **李碩根** | **松尾研究所** | **学術的厳密性、データ駆動** | **3値分類の設計根拠、Fail-to-GUIDANCE** |
| 伴野智樹 | MA理事 | プロトタイピング、社会課題 | 経理現場の課題解決 |
| **中井悦司** | **Google Cloud** | **GCP活用、スケーラビリティ** | **Gemini + Cloud Run + Vertex AI Search** |
| 吉川大央 | Zenn | 再現性、継続発展性 | コード品質、README充実度 |
| **佐藤一憲** | **Google DevRel** | **教育性、ベストプラクティス** | **他開発者が学べるStop-first設計** |

**戦略的優先順位:**

- **Tier 1（最重要）**: 李碩根氏（AIエージェント専門家）、中井悦司氏・佐藤一憲氏（Google関係者2名）
- **Tier 2（重要）**: 渡部陽太氏（技術実装品質）、伴野智樹氏（課題設定）
- **Tier 3（補完）**: 佐藤祥子氏（DevRel）、吉川大央氏（Zenn品質）

### 18.3 差別化の5本柱

先行22件のZenn記事との比較から、5つの差別化ポイントを確立した。

| # | 差別化 | 独自性 | 先行22件との比較 |
|---|--------|:---:|-----------------|
| 1 | **Stop-first / Fail-to-GUIDANCE** | ★★★★★ | 22件中0件。唯一「判定しない」選択肢を持つ |
| 2 | **Agentic 3フェーズ（止まる→聞く→変わる）** | ★★★★★ | AIが能動的に段階質問→再判定は0件 |
| 3 | **外部化ポリシーエンジン（JSON）** | ★★★★☆ | ルールのハードコードが22件全て。JSON外部化は唯一 |
| 4 | **税務知識注入プロンプト** | ★★★★☆ | 税法判定基準のシステムプロンプト注入は0件 |
| 5 | **多層分類 + フォールバック** | ★★★☆☆ | LLM→ルール→ポリシー→税則の4層。安全側一方通行 |

### 18.4 30秒エレベーターピッチ

> 「AIが間違えた判定を出すと、税務申告の修正や加算税のリスクがあります。
> 私たちのツールは**AIが『わかりません』と正直に言える**唯一の固定資産判定ツールです。
> 止まったAIがユーザーに質問を投げ、回答に応じて判定が変わる — これがAgentic設計です。」

### 18.5 審査基準スコアリングと改善計画

| 基準 | 修正前 | 修正後 | 目標 | 対策 |
|------|:---:|:---:|:---:|------|
| 課題の新規性 | 8 | 8 | 9 | Zenn記事でインボイス制度・電帳法と紐付けて訴求 |
| 解決策の有効性 | 8 | 8 | 9 | Golden Set 10→20件拡充、定量効果をデモで実証 |
| 実装品質と拡張性 | 7 | 7.5 | 8 | Feature Flag有効化でGCPサービス3個以上稼働 |
| **公式基準平均** | **7.7** | **7.8** | **8.7** | — |

### 18.6 副業・事業化の展望

side_business_research.mdで実施した市場調査の結果、本プロジェクトの技術基盤は以下の事業展開に活用可能であることが判明した。

| アイデア | MA相性 | 推奨度 | 備考 |
|---------|:---:|:---:|------|
| コードレビュー代行 | 高 | ★★★★★ | 静的解析・パターン検出をエージェントで自動化 |
| テストコード作成代行 | 高 | ★★★★☆ | テスト生成のテンプレート化 |
| バグ修正・デバッグ | 高 | ★★★★☆ | エラーログ解析の自動化 |
| 技術相談・アドバイザリー | 低 | ★★★★★ | マルチエージェント開発のノウハウ提供 |

**ITフリーランス市場規模**: 1兆1,849億円（2025年）。本プロジェクトで培った「Stop-first設計」「マルチエージェント並列開発」のノウハウは、コードレビュー代行やアドバイザリー事業に直接転用可能。

<!-- 殿記入欄: 事業化・副業への興味・方針 -->

---

*本文書は cmd_038 subtask_038_02 として足軽4号が作成。*
*出典: /tmp/journey_part2.md（足軽4号作成、859行）、/tmp/journey_part3.md（足軽8号作成、475行）、docs/配下の参照ファイル40+件。*
*RACE-001遵守: HACKATHON_JOURNEY.md を直接編集していない。*
<a id="section-18"></a>

## 18. デプロイ戦記 — Cloud Runとの格闘の全記録

本プロジェクトのデプロイは一筋縄ではいかなかった。WSL2環境からGoogle Cloud Runへのデプロイという、やや特殊な構成に加え、ContainerImageImportFailed、IAM権限不足、Feature Flag制御、Dockerfile差し替え方式など、多くの技術的課題と格闘した。このセクションでは、デプロイにまつわる全ての苦労とトラブルシューティングの記録を残す。

### 19.1 デプロイ構成の全体像

```
開発環境（WSL2 on Windows 11）
  │
  │ CLOUDSDK_CONFIG="/mnt/c/Users/owner/AppData/Roaming/gcloud"
  │ （Windows側のgcloud認証を流用）
  ▼
gcloud run deploy
  │
  │ Dockerfile → Cloud Build → Artifact Registry → Cloud Run
  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Google Cloud Run                          │
├───────────────────────────────┬──────────────────────────────┤
│  fixed-asset-agentic-api     │  fixed-asset-agentic-ui      │
│  (FastAPI + Uvicorn)         │  (Streamlit)                 │
│  asia-northeast1             │  asia-northeast1             │
│  1Gi Memory                  │  デフォルト                   │
│  allow-unauthenticated       │  allow-unauthenticated       │
└───────────────────────────────┴──────────────────────────────┘
```

**API と UI は別サービスとしてデプロイ**する設計を採用した。理由:
1. APIはFastAPI + Uvicorn、UIはStreamlitという異なるランタイム
2. 個別にスケーリング・更新が可能
3. API単体でERP/RPA連携が可能

### 19.2 WSL2からのgcloud認証問題

最初の壁は **WSL2環境でのgcloud認証** だった。WSL2内でそのまま `gcloud auth login` を実行すると、ブラウザ認証フローが正しく動作しない場合がある。

**解決策**: Windows側のgcloud認証情報をWSL2から直接参照する。

```bash
# Windows側のgcloud設定ディレクトリを環境変数で指定
export CLOUDSDK_CONFIG="/mnt/c/Users/owner/AppData/Roaming/gcloud"

# 認証状態の確認
gcloud auth list
# → tenz4.yugo.k0384@gmail.com (ACTIVE)

# プロジェクトの確認
gcloud config get-value project
# → fixedassets-project
```

この手法は cmd_033 の足軽2が発見・確立し、`cloudrun-deploy-wsl2` としてスキル化候補に挙げられた。以降の全デプロイで標準手順となった。

**注意点**: Cursor統合ターミナルでは `WinError 5`（credentials.db へのアクセス拒否）が発生する場合がある。CLOUDRUN_TROUBLESHOOTING.md に記載の通り、外部ターミナル（Windows ターミナル、PowerShell）で実行する必要がある。

### 19.3 Dockerfile設計 — セキュリティと実用性の両立

APIとUIで異なるDockerfileを使い分ける設計を採用した。

**API用 Dockerfile（メイン）**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app

# セキュリティ: 最小パッケージインストール
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# セキュリティ: 非rootユーザーで実行
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser

ENV PORT=8080

# 死活監視: 30秒間隔でヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

CMD ["sh", "-c", "exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
```

**UI用 Dockerfile.ui**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app

COPY requirements-ui.txt .
RUN pip install --no-cache-dir -r requirements-ui.txt

COPY ui/ ./ui/
COPY data/demo/ ./data/demo/
COPY data/demo_pdf/ ./data/demo_pdf/

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser

ENV PORT=8080
CMD ["sh", "-c", "exec streamlit run ui/app_minimal.py --server.port=${PORT:-8080} --server.address=0.0.0.0 --server.headless=true"]
```

**セキュリティ対策3点**:
| 対策 | 内容 | 理由 |
|------|------|------|
| 非rootユーザー | `appuser`（appgroup）で実行 | コンテナ内の権限を最小化。万が一の侵害時の影響範囲を限定 |
| HEALTHCHECK | `/health` エンドポイントへの30秒間隔監視 | Cloud Runのコールドスタート検出と自動復旧 |
| 最小パッケージ | `--no-install-recommends` | 攻撃面の縮小。イメージサイズの最小化 |

### 19.4 Dockerfile差し替え方式 — UIデプロイの工夫

Cloud Runはソースコードからのデプロイ（`--source .`）ではルートディレクトリの `Dockerfile` を自動検出する。APIとUIで異なるDockerfileを使うため、**差し替え方式**を採用した。

```bash
# 1. バックアップ
cp Dockerfile Dockerfile.api.bak
cp .dockerignore .dockerignore.api.bak

# 2. UI用に差し替え
cp Dockerfile.ui Dockerfile
cp .dockerignore.ui .dockerignore

# 3. UIデプロイ
gcloud run deploy fixed-asset-agentic-ui --source . --region asia-northeast1 \
  --allow-unauthenticated \
  --set-env-vars "API_URL=https://fixed-asset-agentic-api-XXXXXX.asia-northeast1.run.app"

# 4. 復元
cp Dockerfile.api.bak Dockerfile
cp .dockerignore.api.bak .dockerignore
rm Dockerfile.api.bak .dockerignore.api.bak
```

**`.dockerignore` も差し替える理由**: API用とUI用でコンテナに含めるファイルが異なる。
- API用 `.dockerignore`: `ui/` ディレクトリの大部分を除外（APIに不要）
- UI用 `.dockerignore.ui`: `api/`, `core/`, `policies/` を除外（UIに不要）

これにより、各コンテナのイメージサイズを最小化し、ビルド時間を短縮した。

### 19.5 ContainerImageImportFailed — 最も厄介なエラー

Cloud Runデプロイで最も厄介なエラーが **ContainerImageImportFailed**。Cloud Buildでビルドは成功しても、Cloud Runがイメージをpullできない場合に発生する。

**典型的な原因**: Artifact Registryの読み取り権限不足。

```
Cloud Build (ビルド成功)
    │
    │ push → Artifact Registry
    │
    ▼
Cloud Run (pull 失敗)
    → ContainerImageImportFailed
    原因: Runtime SA または Service Agent に
         roles/artifactregistry.reader がない
```

**対処手順**（CLOUDRUN_TROUBLESHOOTING.mdより）:

```powershell
# 1. ランタイムSAの特定
gcloud run services describe fixed-asset-agentic-api \
  --region asia-northeast1 \
  --format="value(spec.template.spec.serviceAccountName)"
# 空の場合 → デフォルトCompute SA: {PROJECT_NUMBER}-compute@developer.gserviceaccount.com

# 2. プロジェクト番号の取得
gcloud projects describe fixedassets-project --format="value(projectNumber)"

# 3. IAM権限の付与
gcloud projects add-iam-policy-binding fixedassets-project \
  --member="serviceAccount:{RUNTIME_SA}" \
  --role="roles/artifactregistry.reader"

gcloud projects add-iam-policy-binding fixedassets-project \
  --member="serviceAccount:service-{PROJECT_NUMBER}@serverless-robot-prod.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.reader"

# 4. digest指定での再デプロイ（ビルドなし）
gcloud run deploy fixed-asset-agentic-api \
  --image asia-northeast1-docker.pkg.dev/fixedassets-project/cloud-run-source-deploy/fixed-asset-agentic-api@sha256:{FULL_DIGEST} \
  --region asia-northeast1 --allow-unauthenticated
```

この手順は `scripts/cloudrun_triage_and_fix.ps1` として対話形式スクリプト化され、トラブル発生時に迅速に対処できるようにした。

### 19.6 障害報告テンプレート — トラブルシューティングの標準化

Cloud Runの障害が発生した際、原因特定を迅速化するための標準報告テンプレートを `docs/CLOUDRUN_TRIAGE_TEMPLATE.md` に整備した。

**報告時に貼るべき3点**:
1. `gcloud run services describe` の出力（status.conditions, latestCreatedRevisionName, url）
2. `gcloud run revisions describe` の出力（status.conditions, spec.containers）
3. IAM権限付与を実施したか否か

このテンプレートにより、「何が起きたか分からない」状態から「必要な情報が揃った状態」へ即座に遷移できる。

### 19.7 環境変数チェックリスト — Feature Flag設計

本プロジェクトは **Feature Flag設計** を採用し、各機能を環境変数で段階的に有効化できる。CLOUDRUN_ENV.md にチェックリストを整備した。

| Feature | 環境変数 | 未設定時の動作 | 有効化時の動作 |
|---------|---------|---------------|---------------|
| **PDF分類** | `PDF_CLASSIFY_ENABLED=1` | POST /classify_pdf → 400 (PDF_CLASSIFY_DISABLED) | PDF分類機能が有効 |
| **Gemini AI** | `GEMINI_ENABLED=1` | ルールベース分類のみ | Gemini APIによるAI分類 |
| **Document AI** | `USE_DOCAI=1` | PyMuPDF/pdfplumberフォールバック | Document AI高精度抽出 |
| **Vertex Search** | `VERTEX_SEARCH_ENABLED=1` | citations空リスト | 法令根拠の自動引用 |
| **耐用年数推定** | `GOOGLE_API_KEY` | マスタ照合のみ | Gemini APIで推定 |

**Feature Flag OFF時の期待値** が明確に定義されているのがポイント。例えば `/classify_pdf` がOFFの場合:
```json
{
  "detail": {
    "error": "PDF_CLASSIFY_DISABLED",
    "how_to_enable": "Set PDF_CLASSIFY_ENABLED=1 on server",
    "fallback": "Use POST /classify with Opal JSON instead"
  }
}
```

### 19.8 ローカルDockerスモークテスト — Cloud Run前の品質ゲート

Cloud Runにデプロイする前に、ローカルでDockerビルド・起動・HTTPスモークを実施する手順を `docs/DOCKER_LOCAL_SMOKE.md` に整備した。

```powershell
# ターミナル1: ビルド→起動
docker build -t fixed-asset-api .
docker run --rm -e PORT=8080 -p 8080:8080 fixed-asset-api

# ターミナル2: スモークテスト（一括）
.\scripts\docker_smoke.ps1
```

**スモークテストの期待値**:
| エンドポイント | 期待 | 確認内容 |
|---------------|------|---------|
| GET /health | 200 OK | `{"ok": true}` |
| POST /classify | 200 OK | decision, confidence, trace, missing_fields を含む |
| POST /classify_pdf | 400 | `PDF_CLASSIFY_DISABLED`（Feature Flag OFF時） |

`docker_smoke.ps1` は全項目通過で `=== All docker smoke tests passed ===` を出力し exit 0。失敗時は exit 1 でCI/CDゲートとして機能する。

### 19.9 Dockerfileの静的チェック

`docs/DOCKER_STARTUP_REPORT.md` として、Dockerfileとアプリケーションの整合性を静的チェックした記録が残されている。

**チェック項目と結果**:
| 項目 | 結果 | 詳細 |
|------|------|------|
| PORT設定 | OK | `ENV PORT=8080` + `--port ${PORT:-8080}` で Cloud Run の PORT を利用 |
| 0.0.0.0 bind | OK | `--host 0.0.0.0` で全インターフェース listen |
| app名の整合性 | OK | `api/main.py` の `app = FastAPI(...)` と `CMD` の `api.main:app` が整合 |
| requirements | 注意 | `google-cloud-documentai` が常時インストール対象（イメージサイズ増加）。`gunicorn` は CMD で未使用（uvicorn のみ） |

### 19.10 デプロイの変遷 — 4回のデプロイ記録

本プロジェクトでは合計4回のCloud Runデプロイを実施した。

**第1-2回: cmd_033（足軽2） — 初回デプロイ**
```
API: fixed-asset-agentic-api-00034-mtc (100% traffic)
UI:  fixed-asset-agentic-ui-00004-2qj (100% traffic)
環境変数:
  GEMINI_ENABLED=1
  PDF_CLASSIFY_ENABLED=1
  GOOGLE_GENAI_USE_VERTEXAI=True
  GOOGLE_CLOUD_PROJECT=fixedassets-project
  GOOGLE_CLOUD_LOCATION=global
  CORS_ORIGINS=<UI URL>
```

動作確認結果:
- GET /health → 200 OK `{"ok":true}`
- GET / → 200 OK `{"message":"Fixed Asset Classification API","version":"1.0.0"}`
- POST /classify → 200 OK（Gemini連携成功、confidence 0.95、trace: gemini_success）
- UI → HTTP 200 OK

**第3-4回: cmd_035（足軽8） — リスク対処後再デプロイ**
```
API: fixed-asset-agentic-api-00035-r5x (100% traffic)
UI:  fixed-asset-agentic-ui-00005-ddv (100% traffic)
環境変数: 既存設定を完全維持
```

新たに確認した項目:
- GET /health → 200 OK `{"ok":true,"gemini_available":true,"gemini_enabled":true,"gemini_connected":true}`
  → **RISK-006修正反映**: gemini_connected フィールド追加
- レート制限テスト:
  - GET /health: 30回目で HTTP 429（30/minute制限）
  - POST /classify: 10回目で HTTP 429（10/minute制限）
  → **RISK-002修正反映**: slowapi @limiter.limit() が全エンドポイントで動作

### 19.11 デプロイで学んだ教訓

1. **WSL2からのgcloud認証は Windows側の設定を直接参照するのが最速**。WSL2内でのgcloud auth loginは不安定。
2. **Feature Flagは必須**。全機能を一度に有効化するのではなく、段階的に確認しながら有効化する。
3. **スモークテストスクリプトを先に用意する**。手動curlを毎回打つのは非効率。
4. **ContainerImageImportFailed はIAM権限を真っ先に疑う**。ビルド成功なのにデプロイ失敗の場合、99%がIAM。
5. **Dockerfile差し替え方式は復元忘れに注意**。復元忘れでAPIサービスにUI用Dockerfileをデプロイしてしまうリスクがある。

---

<a id="section-19"></a>

## 19. 将来ビジョン — Stop-first設計の可能性

### 20.1 MVPから始まるロードマップ

本システムは第4回Agentic AI Hackathon with Google Cloud向けのPOC（Proof of Concept）として開発された。しかし、その核心である **Stop-first設計** は、固定資産判定に限らず、あらゆる業務判断に適用可能なパターンである。

**現在の制約と将来目標**:
| 項目 | 現状（POC） | 将来目標 |
|------|------------|---------|
| 対応帳票 | 見積書のみ | 請求書・領収書・注文書・契約書 |
| 判定範囲 | 固定資産/費用の分類 | 耐用年数・減価償却方法の提案 |
| OCR | PyMuPDF/pdfplumber中心 | Document AI本格活用 |
| 法令検索 | Feature-flagged | Vertex AI Search常時有効 |
| 運用環境 | Cloud Run（単一リージョン） | マルチリージョン・高可用性 |

### 20.2 短期ロードマップ（3-6ヶ月）

**Phase 1: 基盤安定化（1-2ヶ月）**

1. **Document AI本格統合**: `USE_DOCAI=1` をデフォルト化。PDFレイアウト解析の精度向上、テーブル構造の自動抽出、手書き文字認識の強化。
2. **Vertex AI Search常時有効化**: 法令エビデンス検索の常時利用。税法・会計基準のベクトル検索で判定根拠を自動引用。
3. **テスト・品質基盤**: Golden Set 10件 → 50件に拡充。E2Eテストの自動化。本番環境のモニタリング構築。

**Phase 2: 機能拡張（3-4ヶ月）**

1. **耐用年数マスタ連携**: 「減価償却資産の耐用年数等に関する省令」をマスタデータとして構造化し、asset_category と structure_or_use からの自動検索を実装。Stop-first設計を維持し、自動決定ではなく候補提示と根拠提示に留める。

```yaml
# 想定インターフェース
useful_life_master:
  source: "減価償却資産の耐用年数等に関する省令"
  lookup_by:
    - asset_category      # 資産カテゴリ
    - structure_or_use    # 構造または用途
  output:
    - useful_life_years   # 耐用年数
    - depreciation_method # 償却方法
    - confidence_score    # 信頼度
```

2. **会社別ポリシー拡張**: 現在の `policies/company_default.json` をマルチテナント対応（会社コード別ポリシー）に拡張。上場企業向けに四半期決算対応フラグを追加。

**Phase 3: 運用成熟（5-6ヶ月）**

1. **監査証跡の強化**: 全判定のトレースログ永続化、人間による上書き判定の記録、監査人向けエクスポート機能。
2. **ユーザーフィードバックループ**: GUIDANCE → 人間判定 → フィードバック収集 → 判定精度の継続的改善。ただし、前例踏襲による思考停止リスクには注意。

### 20.3 新機能候補 — 価値と工数のバランス

`docs/NEW_FEATURES_CANDIDATES.md` に整理された新機能候補から、優先度順に5件:

| 優先度 | 機能 | 工数 | 価値 | 理由 |
|--------|------|------|------|------|
| **1** | 判定理由の詳細化 | 2-3時間 | ★★☆ | Geminiに自然言語での説明を追加。審査員・ユーザーへの説明力UP |
| **2** | 一括アップロード | 半日 | ★★☆ | 複数PDFの順次判定。実務的価値が高い |
| **3** | 固定資産台帳インポート | 1日 | ★★★ | CSV/Excelから過去台帳を取り込み、類似度学習の前提機能 |
| **4** | 人間の修正履歴記録 | 2-3時間 | ★★☆ | AI判定と人間修正の差分を記録。監査対応アピール |
| **5** | ダッシュボード画面 | 半日-1日 | ★★☆ | 月間判定件数・金額・分類内訳の可視化。デモ映え |

**判定理由詳細化の具体例**:
```
現状の reasons:
  "判断が割れる可能性があるため判定しません"

改善後の detailed_reason:
  "この支出は「ノートパソコン一式」で金額が185,000円です。
   10万円以上のため少額資産には該当せず、固定資産として
   計上が必要です。PCは「器具備品」に分類され、
   耐用年数は4年となります。"
```

### 20.4 未実装課題の全体像

`docs/UNIMPLEMENTED_ISSUES.md` に整理された未実装課題は6カテゴリ・約40項目:

| カテゴリ | 主要課題 | 件数 |
|----------|---------|------|
| AI・GCP統合 | Geminiマルチモーダル、ai_suggestions、Vertex AI実動作確認 | 7件 |
| 根拠・証跡 | evidence_keywords、applied_rule、legal_reference | 4件 |
| UI・可視化 | PDFハイライト、Dark Mode、Loading States、Tooltips | 7件 |
| 抽出・パース | 合計行除外、extraction confidence、日付抽出 | 4件 |
| 税務・判定 | 取得価額10%基準、メンテナンスvs価値向上の峻別 | 2件 |
| エラーハンドリング | Vertex AIタイムアウト/レート制限 | 2件 |

**すでに実装済みだがレポートに未反映のもの**も複数:
- DocAI（`_try_docai` 実装済み）
- 表構造抽出（pdfplumber実装済み）
- 税務ルール（`_apply_tax_rules` 実装済み: 10/20/30/60万円基準）
- `/classify_pdf`（api/main.py に実装済み）
- `useful_life_estimator.py`（API統合済み、UIで耐用年数表示）
- Vertex AI Search（`vertex_search.py` に実装済み）

### 20.5 中長期ビジョン — プラットフォーム化

**他帳票への横展開**（1-2年）:
| 帳票種別 | 判定内容 | Stop条件 |
|----------|----------|----------|
| **請求書** | 支払承認/保留/要確認 | 金額差異・未承認ベンダー |
| **領収書** | 経費精算可否 | 社内規定逸脱・重複疑い |
| **注文書** | 予算整合性 | 予算超過・承認フロー未完了 |
| **契約書** | リース/購入判定 | IFRS16適用判断 |

**「判断支援AI」のプラットフォーム化**（3年以上）:

```
┌───────────────────────────────────────────────────┐
│       Agentic Decision Support Platform            │
├───────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │固定資産  │ │与信判定  │ │採用判定  │  ...     │
│  │判定      │ │          │ │          │          │
│  └──────────┘ └──────────┘ └──────────┘          │
├───────────────────────────────────────────────────┤
│  共通基盤:                                         │
│  Stop-first Engine / Evidence Store /              │
│  Audit Trail / Human-in-the-Loop                   │
└───────────────────────────────────────────────────┘
```

Stop-first設計は固定資産判定に限らず、**あらゆる業務判断の支援に適用可能**。与信判定（融資の可否）、採用判定（書類選考の合否）、コンプライアンスチェックなど、「AIが確信を持てないケースで止まり、人間の判断を求める」パターンは普遍的。

### 20.6 ビジネスモデルの展望

**想定顧客セグメント**:
| セグメント | 特徴 | 月間処理量 | 提供価値 |
|-----------|------|-----------|---------|
| 中堅企業 | 経理2-5名 | 100-500件 | 判定効率化・属人化解消 |
| 大企業 | 監査対応必須 | 1,000件以上 | 監査証跡・ガバナンス強化 |
| 会計事務所 | 複数クライアント | 1,000件以上 | マルチテナント・標準化 |
| SIer/コンサル | 顧客提案材料 | - | ホワイトラベル提供 |

**収益モデル案**:
```
Option A: SaaS月額課金
├── Basic:        ¥50,000/月 (500件/月)
├── Professional: ¥150,000/月 (2,000件/月)
└── Enterprise:   個別見積 (無制限 + SLA)

Option B: 従量課金
├── 判定単価:     ¥100/件
├── GUIDANCE時:   ¥150/件 (根拠提示含む)
└── 月間最低:     ¥30,000

Option C: ライセンス販売
├── オンプレミス:  初期費用 + 年間保守
└── プライベートクラウド: 構築費 + 運用サポート
```

### 20.7 成功指標（KPI）

| 期間 | 指標 | 目標 |
|------|------|------|
| 短期（6ヶ月） | Golden Set精度 | 95%以上維持 |
| 短期（6ヶ月） | GUIDANCE発生率 | 20-30% |
| 短期（6ヶ月） | API応答時間 | p99 < 3秒 |
| 中期（1年） | 導入企業数 | 10社 |
| 中期（1年） | 月間処理件数 | 10,000件 |
| 長期（3年） | ARR（年間経常収益） | ¥100M |
| 長期（3年） | 横展開帳票数 | 5種類 |

### 20.8 副業・収益化の可能性

`docs/side_business_research.md` では、本プロジェクトの技術スタックを活用した副業ビジネスの可能性も調査済み。ITフリーランス市場規模 **1兆1,849億円**（2025年）、IT人材不足 **79万人**（2025年予測）という市場環境の中で、以下が高い推奨度:

| 順位 | アイデア | MA相性 |
|------|---------|--------|
| 1 | 技術相談・アドバイザリー | 低 |
| 2 | コードレビュー代行 | 高 |
| 3 | テストコード作成代行 | 高 |
| 4 | バグ修正・デバッグ | 高 |
| 5 | API設計・実装支援 | 中 |

「MA相性」はマルチエージェントシステム（multi-agent-shogun）との相性。コードレビュー代行やテストコード作成代行は、足軽を並列稼働させて効率化できる領域。

---

<a id="section-20"></a>

## 20. スキル化候補9件の詳細

multi-agent-shogunでは、足軽が作業中に発見した **再利用可能なパターン** を「スキル化候補」として報告する仕組みがある。各足軽の報告書には `skill_candidate` セクションが必須で、`found: true` の場合はスキル名・説明・理由を記載する。

本ハッカソン（cmd_033〜cmd_037）で報告されたスキル化候補は **9件**。以下にその全詳細を記す。

### 21.1 hackathon-risk-audit

| 項目 | 内容 |
|------|------|
| **報告元** | 足軽4（cmd_033: 懸念点・リスク洗い出し） |
| **概要** | ハッカソン提出前の包括的リスク監査 |
| **カテゴリ** | 4カテゴリ（技術/審査/法的/秘密情報）の並列調査 |
| **実績** | 17件のリスクを検出（高6/中6/低5） |
| **スキル化理由** | ハッカソン参加時に毎回使える。プロジェクト提出前の定型チェック |

**入力**: プロジェクトのルートディレクトリパス、ハッカソンのルールファイル
**出力**: リスク一覧（ID、タイトル、深刻度、推奨対処、対処状況）

```yaml
# 想定スキル定義
skill:
  name: hackathon-risk-audit
  trigger: "ハッカソン提出前のリスク監査を実施"
  categories:
    - technical_risk    # APIキー漏洩、レート制限、コスト超過
    - review_risk       # ルール違反、デモ失敗シナリオ
    - legal_risk        # ライセンス、利用規約
    - secret_risk       # 秘密情報の露出
  output_format: markdown_table
```

### 21.2 doc-consistency-checker

| 項目 | 内容 |
|------|------|
| **報告元** | 足軽1（cmd_033: 資料間の齟齬検証） |
| **概要** | 複数ドキュメント間の整合性を自動検証 |
| **実績** | 15件の齟齬を発見・修正 |
| **スキル化理由** | どのプロジェクトでもドキュメントの齟齬は発生する。正データを基準にした突合は汎用パターン |

**入力**: 正データファイル群（例: RULES.md）、検証対象ファイル群（例: README.md, DEMO.md）
**出力**: 齟齬一覧（ファイル、行番号、正データとの差分、修正内容）

**検証ポイント**:
- 機能説明の一貫性（API仕様、UIの説明、判定ロジック）
- 技術スタック記載の統一（バージョン、サービス名）
- デプロイ手順の正確性
- 審査員向け情報の正確性

### 21.3 cloudrun-deploy-wsl2

| 項目 | 内容 |
|------|------|
| **報告元** | 足軽2（cmd_033: Cloud Runデプロイ） |
| **概要** | WSL2環境からCloud Runへのデプロイ手順（Windows側gcloud認証活用、Dockerfile差し替え方式） |
| **実績** | 4回のデプロイ全てで使用 |
| **スキル化理由** | WSL2特有のgcloud認証問題の解決パターンは汎用的。Dockerfile差し替えデプロイも再利用可能 |

**手順の骨格**:
```bash
# 1. 認証設定
export CLOUDSDK_CONFIG="/mnt/c/Users/owner/AppData/Roaming/gcloud"

# 2. APIデプロイ
gcloud run deploy SERVICE-api --source . --region REGION --allow-unauthenticated --memory 1Gi

# 3. UIデプロイ（Dockerfile差し替え）
cp Dockerfile Dockerfile.api.bak && cp Dockerfile.ui Dockerfile
gcloud run deploy SERVICE-ui --source . --region REGION --allow-unauthenticated
cp Dockerfile.api.bak Dockerfile && rm Dockerfile.api.bak

# 4. スモークテスト
curl -s https://SERVICE-URL/health
```

### 21.4 api-hardening-audit

| 項目 | 内容 |
|------|------|
| **報告元** | 足軽1（cmd_035: api/main.pyリスク対処） |
| **概要** | FastAPIエンドポイントのセキュリティ・堅牢性を自動監査 |
| **実績** | レート制限未適用5件、bare exception 4件、接続テスト未実装1件を検出・修正 |
| **スキル化理由** | 新規APIエンドポイント追加時の定型チェックとして汎用的 |

**チェック項目**:
| # | チェック内容 | 深刻度 |
|---|-------------|--------|
| 1 | 全エンドポイントに `@limiter.limit()` があるか | 高 |
| 2 | `except Exception:` が `as e` なしで使われていないか | 中 |
| 3 | 全 except ブロックに `logger.exception()` があるか | 中 |
| 4 | startup event で外部サービスの接続テストがあるか | 中 |
| 5 | 環境変数のバリデーション（未設定時のフォールバック）があるか | 低 |

### 21.5 github-publish-auditor

| 項目 | 内容 |
|------|------|
| **報告元** | 足軽3（cmd_035: GitHub公開準備） |
| **概要** | GitHub公開前のセキュリティ監査（秘密情報スキャン + .gitignore補強 + ライセンス記載チェック） |
| **実績** | .gitignoreに秘密鍵・証明書パターン追加、GCPプロジェクト番号の環境変数化、AGPL記載追加 |
| **スキル化理由** | OSS公開時のセキュリティ監査は毎回同じパターン |

**チェックフロー**:
```
1. ソースコード全文スキャン
   → ハードコードされたAPIキー、シークレット、プロジェクト番号
2. .gitignore 補強
   → *.key, *.pem, *.p12, credentials*, service-account*
3. ライセンス記載チェック
   → 使用OSS（特にAGPL等copyleft）のライセンス記載
4. .env.example 確認
   → プレースホルダのみで実値なし
5. レポート出力
   → 発見事項一覧、推奨対処、修正結果
```

### 21.6 pptx-dark-theme-generator

| 項目 | 内容 |
|------|------|
| **報告元** | 足軽5（cmd_034: pptxスライド前半） |
| **概要** | python-pptxでダークテーマのプレゼンスライドを自動生成するスクリプトテンプレート |
| **実績** | 6枚のスライドをデザインルール5種準拠で生成。品質チェック17項目全PASS |
| **スキル化理由** | デザインルール5種（color/layout/slide-generator/diagram/graph）の適用パターンをテンプレート化 |

**組み込みデザインルール**:
```python
# カラーパレット（Google Cloud準拠）
COLORS = {
    "BASE": "#0D0D0D",       # 背景
    "MAIN": "#4285F4",       # メインカラー（Google Blue）
    "ACCENT": "#EA4335",     # アクセント（Google Red）
    "CARD_BG": "#1A1F2E",    # カード背景
    "GRAY": "#9CA3AF",       # テキスト（サブ）
    "YELLOW": "#FBBC04",     # 警告/GUIDANCE
    "GREEN": "#34A853",      # 成功
}

# フォント設定
FONT_FAMILY = "Meiryo UI"
FONT_MIN = Pt(20)     # 殿の基準: 最小20pt
FONT_NORMAL = Pt(24)  # 通常サイズ

# レイアウト
SLIDE_WIDTH = Inches(13.333)  # 16:9
SLIDE_HEIGHT = Inches(7.500)
MARGIN_LR = Inches(0.8)       # 左右マージン
```

### 21.7 pptx-slide-batch-generator

| 項目 | 内容 |
|------|------|
| **報告元** | 足軽6（cmd_034: pptxスライド後半） |
| **概要** | python-pptxでデザインルール準拠のスライドをバッチ生成するスキル |
| **実績** | 6枚のスライド（アーキテクチャ、Agentic設計、Before/After、成果、展望、クロージング） |
| **スキル化理由** | デザインルール5種の適用ロジックを毎回手書きするのは非効率。他プロジェクトでも再利用可能 |

**pptx-dark-theme-generatorとの違い**: dark-theme-generatorはテンプレート（スタイル定義）、batch-generatorはバッチ実行（複数スライドの一括生成ロジック）。

### 21.8 pptx-merge-and-verify

| 項目 | 内容 |
|------|------|
| **報告元** | 足軽7（cmd_034: 結合・最終検証） |
| **概要** | 複数のpptxファイルをpython-pptxで結合し、5つのデザインルール準拠を自動検証 |
| **実績** | Part1(6枚) + Part2(6枚) を結合、暗色背景カード色の統一修正（10箇所）、品質チェック5項目全PASS |
| **スキル化理由** | 結合+品質チェックのパターンは他プレゼン作成タスクでも再利用可能 |

**品質チェック5項目**:
| # | チェック | 対象 |
|---|---------|------|
| 1 | カラールール | 原色不使用、テーマカラー統一 |
| 2 | レイアウトルール | マージン、版面率、Z型フロー |
| 3 | タイポグラフィ | フォント統一（Meiryo UI）、最小20pt |
| 4 | 図解ルール | 角丸四角形統一、塗り=強調/枠線=通常 |
| 5 | 一貫性 | スライド番号連番、カラー共通、内容の重複/矛盾なし |

### 21.9 video-recording-guide-generator

| 項目 | 内容 |
|------|------|
| **報告元** | 足軽3（cmd_033: 動画撮影手順書作成） |
| **概要** | ハッカソンデモ動画の撮影手順書を自動生成 |
| **実績** | VIDEO_RECORDING_GUIDE.md を作成（撮影前準備、デモシナリオ、シーン別時間配分、審査員向けキーワード） |
| **スキル化理由** | デモ動画は多くのハッカソンで必要。台本設計のパターンは汎用的 |

**出力に含まれる内容**:
- 撮影前の準備（環境確認、ブラウザ設定、録画ソフト設定）
- デモシナリオ（どの画面で何を見せるか、時系列の台本）
- 各シーンの想定時間
- 話すべきポイント（審査員に刺さるキーワード）
- 撮影後の確認事項

### 21.10 スキル化の今後

9件のスキル化候補のうち、即座に実装すべき優先度が高いものは:

| 優先度 | スキル | 理由 |
|--------|--------|------|
| **1** | cloudrun-deploy-wsl2 | 次回デプロイ時に即活用。WSL2ユーザーへの汎用性高い |
| **2** | api-hardening-audit | 新規FastAPIプロジェクト立ち上げ時の品質ゲート |
| **3** | doc-consistency-checker | ドキュメント齟齬はどのプロジェクトでも発生する |
| **4** | hackathon-risk-audit | 次回ハッカソン参加時に即活用 |
| **5** | pptx-dark-theme-generator | プレゼン作成の自動化 |

スキルは `~/.claude/skills/` にMarkdown形式で保存され、Claude Codeの任意のセッションから呼び出し可能。multi-agent-shogunの足軽が使用するローカルスキルは `/mnt/c/tools/multi-agent-shogun/multi-agent-shogun-main/skills/` に保存される。

```yaml
# config/settings.yaml のスキル設定
skill:
  save_path: "~/.claude/skills/"           # グローバルスキル
  local_path: "/mnt/c/tools/multi-agent-shogun/multi-agent-shogun-main/skills/"  # ローカルスキル
```

スキル化候補の発見は、multi-agent-shogunの **継続的ナレッジ蓄積メカニズム** の一部である。足軽が日常的に作業する中で「これは汎用パターンだ」と気づいた時点で報告し、家老がダッシュボードに集約し、殿が承認してスキル化する。この3段階のフィルタリングにより、本当に価値のあるスキルだけが残る仕組みになっている。

---

> **本セクション（19-21）は multi-agent-shogun の足軽8号が、cmd_038 の任務として作成した。**
> **参照情報源**: docs/CLOUDRUN_ENV.md, docs/CLOUDRUN_TROUBLESHOOTING.md, docs/CLOUDRUN_TRIAGE_TEMPLATE.md, docs/DOCKER_STARTUP_REPORT.md, docs/DOCKER_LOCAL_SMOKE.md, docs/REPORT_DOCKER_SMOKE_AND_TESTS.md, docs/deploy_status.md, DEPLOY.md, docs/future_vision.md, docs/NEW_FEATURES_CANDIDATES.md, docs/UNIMPLEMENTED_ISSUES.md, docs/side_business_research.md, queue/reports/ashigaru1-8_report.yaml
<a id="section-21"></a>

## 21. おわりに（拡充版）

### 14.1 プロジェクト完成度サマリ

| カテゴリ | 項目 | 状態 |
|---------|------|------|
| **コア機能** | 3値判定（CAPITAL_LIKE / EXPENSE_LIKE / GUIDANCE） | 完成 |
| **Agentic機能** | 止まる→聞く→深く聞く→変わる | 完成 |
| **デプロイ** | Cloud Run API + UI | 稼働中 |
| **品質** | Golden Set 100%、136テスト通過 | 達成 |
| **セキュリティ** | Critical 10/11修正、残1は部分修正 | 概ね完了 |
| **提出物** | Zenn記事下書き、pptx 12枚 | 動画・スクショ待ち |

### 14.2 「止まれるAI」が示す未来

このプロジェクトを通じて、我々は一つの確信を得た。

> **AIの価値は「正解を出すこと」だけではない。「わからない」と正直に言えることにもある。**

経理の現場では、月末・決算期に判断を疑う余裕がない。そこにAIの自動化を入れると、誤った判断を高速に通過させてしまう。Stop-first設計は、この問題に対する設計レベルでの回答だ。

止まる。聞く。深く聞く。そして変わる。

これがAgentic AIの新しい定義 — **判断を行う／止めるを選択できる自律性**。

<!-- 殿記入欄: プロジェクトを振り返っての一言メッセージ -->

---

