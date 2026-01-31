# 審査員向け価値訴求ドキュメント

> **第4回 Agentic AI Hackathon with Google Cloud**
> 見積書 固定資産判定システム ― Stop-first Agentic AI

---

## 審査基準への対応マトリクス

| 審査基準 | 本プロジェクトの対応 |
|----------|----------------------|
| **課題の新規性** | 「止まる」ことを価値とするAgentic設計 |
| **解決策の有効性** | Stop-first + GUIDANCE + 再実行ループ |
| **実装品質と拡張性** | Docker/Cloud Run対応、Policy Hook、Golden Set評価 |

---

## 審査員別 価値訴求ポイント

### 1. 佐藤祥子 氏（THE BIGLE代表）
**専門**: DevRel、技術コミュニティ支援

**訴求ポイント**:
- **開発者体験の重視**: README.md、DEMO_RUNBOOK.md、INDEX.mdで段階的な理解を支援
- **再現性の確保**: `docker_smoke.ps1`で3分以内にローカル動作確認可能
- **コミュニティ貢献可能性**: Stop-first設計パターンは他ドメインにも適用可能（医療診断、法務レビュー等）

---

### 2. 渡部陽太 氏（アクセンチュア/ゆめみCTO）
**専門**: 生成AI技術開発、Flutter著書

**訴求ポイント**:
- **生成AIの適切な活用**: LLMの「断定癖」を設計で制御（3値判定: CAPITAL_LIKE / EXPENSE_LIKE / GUIDANCE）
- **実装品質**:
  - 凍結スキーマv1.0によるAdapter正規化
  - 100% Golden Set Accuracy（10/10ケース）
- **技術的誠実さ**: 意図的に実装しなかったもの（自動仕訳、耐用年数判定）を明示

---

### 3. 李碩根 氏（松尾研究所/SozoWorks代表）
**専門**: AIエージェント特化、需要予測・因果探索

**訴求ポイント（最重要審査員）**:
- **Agenticの再定義**:
  > 「自律」とは、すべてを自動で処理することではなく、**判断を行う／止めるを選択できること**
- **5ステップのAgenticループ**:
  1. **止まる（GUIDANCE）**: 判断が割れる可能性がある場合、自動判定を停止
  2. **根拠提示**: Evidence + Missing Fields を明示
  3. **質問**: `why_missing_matters` でなぜその情報が必要かを説明
  4. **再実行**: `answers`フィールドで不足情報を補完し再分類
  5. **差分保存**: Before → After の Decision/Confidence/Trace を表示
- **Stop-first設計の思想**: 「誤った自動化を防ぐ」ことが最大の価値
- **因果的思考**: 判断停止の理由（flags）を証跡として保存 → 後から「なぜ止まったか」を追跡可能

---

### 4. 伴野智樹 氏（一般社団法人MA理事）
**専門**: ハッカソン運営、アイディエーション

**訴求ポイント**:
- **課題設定のユニークさ**:
  > 「AIが賢くなる」ではなく「AIが止まる」ことを価値とする逆転の発想
- **現場の痛みに根ざした設計**:
  - 月末・決算期の時間的余裕のなさ
  - 人員不足による確認工程の圧縮
  - 「人が判断したから大丈夫」「AIが出した結果だから正しい」という思考停止
- **実用性**: 経理担当者は「要確認（GUIDANCE）の行だけを優先的に確認」すればよくなる

---

### 5. 中井悦司 氏（Google Cloud Japan）
**専門**: AI Solutions Architect、機械学習・生成AI著書

**訴求ポイント**:
- **Google Cloud AIの深い活用**:
  | サービス | 用途 | 実装箇所 |
  |----------|------|----------|
  | **Document AI** | PDF抽出（`USE_DOCAI=1`） | `core/pdf_extract.py` |
  | **Vertex AI Search** | 法令エビデンス検索（feature-flagged） | `api/vertex_search.py` |
  | **Cloud Run** | APIデプロイ | `Dockerfile`, `api/main.py` |
- **アーキテクチャのベストプラクティス**:
  - Feature Flag による段階的機能有効化
  - `/health`エンドポイントによるCloud Run準拠
  - 環境変数ベースの設定（`PDF_CLASSIFY_ENABLED`等）
- **Stop-first設計とGCP**: 抽出が不十分な場合は`GUIDANCE`として返す → AIの不確実性をシステム設計で吸収

---

### 6. 吉川大央 氏（クラスメソッド Zennチーム）
**専門**: AIスパム検知、Zenn機能開発

**訴求ポイント**:
- **コード品質**:
  - `scripts/dev_run_checks.ps1`による単一品質ゲート
  - CI/CD整備（GitHub Actions）
  - 100% Golden Set Accuracy
- **技術記事としての説明力**: README.mdの構成
  - 審査員向け3点セット（Agentic / Google Cloud AI / Repro）を冒頭に
  - Mermaidによるシステム構成図
  - 意図的に実装しなかったものの明示
- **AIとの協働設計**: 「疑えない状況」での誤判定リスクを明示 → Zennの技術記事としても価値あり

---

### 7. 佐藤一憲 氏（Google Developer Advocate）
**専門**: AI/ML担当、デモ開発

**訴求ポイント**:
- **デモの分かりやすさ**:
  - `docs/DEMO_RUNBOOK.md`: 3-4分のデモ台本
  - `docs/DEMO_FALLBACK_DOCKER.md`: Cloud Run障害時のフォールバック
- **GCP活用の実践**:
  - Document AI + Vertex AI Search の組み合わせ
  - Cloud Run へのワンコマンドデプロイ
- **Agenticの可視化**: Before → After の差分表示（Decision/Confidence/Trace）

---

## 戦略的優先順位

### Tier 1（最重要）
1. **李碩根 氏**: AIエージェント専門家 → Agentic設計の質が評価の核心
2. **中井悦司 氏 / 佐藤一憲 氏**: Google関係者2名 → GCP活用の深さを示す

### Tier 2（重要）
3. **渡部陽太 氏**: 生成AI技術 → 技術的実装品質
4. **伴野智樹 氏**: ハッカソン運営 → 課題設定のユニークさ

### Tier 3（補完）
5. **佐藤祥子 氏**: DevRel → 開発者体験
6. **吉川大央 氏**: Zenn → コード品質と説明力

---

## キーメッセージ（30秒ピッチ用）

> 「AIが賢くなる」ではなく「AIが止まる」ことを価値とする。
>
> 経理現場では、月末・決算期に判断を疑う余裕がない。
> そこにAIの自動化を入れると、誤った判断を高速に通過させてしまう。
>
> 本システムは、判断が割れる場面で**自律的に停止**し、
> 人間に確認すべきポイントを明示する。
>
> これが「Agentic AI」の新しい定義 ―
> **判断を行う／止めるを選択できる自律性**。

---

## 補足資料へのリンク

| 資料 | 用途 |
|------|------|
| [README.md](../README.md) | プロジェクト全体像 |
| [DEMO_RUNBOOK.md](./DEMO_RUNBOOK.md) | デモ手順（3-4分） |
| [COMPLIANCE_CHECKLIST.md](./COMPLIANCE_CHECKLIST.md) | 規約準拠チェックリスト |
| [DOCKER_LOCAL_SMOKE.md](./DOCKER_LOCAL_SMOKE.md) | ローカル動作確認 |
| [CLOUDRUN_ENV.md](./CLOUDRUN_ENV.md) | Cloud Run環境設定 |

---

*Last Updated: 2026-01-30*
