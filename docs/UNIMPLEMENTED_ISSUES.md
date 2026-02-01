# 未実装・未対応 課題一覧

> **作成日**: 2026-02-01  
> **対象**: 第4回 Agentic AI Hackathon with Google Cloud  
> **目的**: 全未実装課題の洗い出しと優先度整理

---

## 1. 提出物・手続き（ハッカソン必須）

| 課題 | ソース | 優先度 |
|------|--------|--------|
| Zenn記事作成・公開 | submission_checklist | 必須 |
| Zennトピック「gch4」設定 | submission_checklist | 必須 |
| Zennカテゴリ「Idea」設定 | submission_checklist | 必須 |
| デモ動画（3分）撮影・埋め込み | submission_checklist | 必須 |
| 参加登録フォーム提出（締切2/13） | LORD_INSTRUCTIONS | 必須 |
| GitHub公開確認 | submission_checklist | 必須 |
| Cloud Run再デプロイ（PDF_CLASSIFY_ENABLED=1） | LORD_INSTRUCTIONS | 必須 |
| commit & push（未pushの可能性） | LORD_INSTRUCTIONS | 必須 |
| LICENSEファイル確認 | github_checklist | 中 |
| .gcloud_config 機密情報確認 | submission_checklist | 中 |

---

## 2. 技術・機能（コードベース）

### 2.1 AI・GCP統合

| 課題 | ソース | 詳細 |
|------|--------|------|
| Gemini 1.5 Pro マルチモーダル | IMPLEMENTATION_AUDIT | PDFを画像として送信しレイアウト・表構造を解析 |
| Vertex AI Gemini（classifier内統合） | IMPLEMENTATION_STATUS | GUIDANCE時の候補案生成・補助判断 |
| ai_suggestions 出力（2026-FA-03） | IMPLEMENTATION_AUDIT, specs | 勘定科目候補リスト（account_category, confidence, reason） |
| useful_life の API 統合 | integration_test_report | estimate_useful_life は存在するが api/main.py から未呼び出し |
| useful_life_candidates（2026-FA-04）full schema | specs | 法定耐用年数候補の完全仕様（legal_basis, historical_support 等） |
| Vertex AI Search 実動作確認 | integration_test_report | 環境変数設定による本番確認が必要 |
| Gemini API 実動作確認 | integration_test_report | APIキーが必要、本番環境で確認 |

### 2.2 根拠・証跡

| 課題 | ソース | 詳細 |
|------|--------|------|
| evidence_keywords | IMPLEMENTATION_AUDIT | どのキーワードが検出されたかを明示 |
| applied_rule / rules_applied | IMPLEMENTATION_AUDIT, 2026-FA-02 | evidence に税務ルールIDを追加 |
| legal_reference / regulation_citation | IMPLEMENTATION_AUDIT | 「国税庁基本通達 第X条」などの条文参照 |
| trace_log 詳細化 | IMPLEMENTATION_AUDIT | キーワード検出・ルール適用の記録 |

### 2.3 UI・可視化

| 課題 | ソース | 詳細 |
|------|--------|------|
| PDF該当箇所ハイライト | IMPLEMENTATION_AUDIT | position_hint に座標・矩形情報、UIでハイライト表示 |
| position_hint 座標情報 | IMPLEMENTATION_AUDIT | PDF内の矩形情報を記録 |
| Dark Mode Support | ui_improvements | ライト/ダークテーマ切替 |
| Print Stylesheet | ui_improvements | 結果の印刷用最適化 |
| Keyboard Shortcuts | ui_improvements | よく使う操作のショートカット |
| Loading States | ui_improvements | API呼び出し中のスケルトン表示 |
| Tooltips | ui_improvements | 専門用語の説明ツールチップ |

### 2.4 抽出・パース（PDF関連）

| 課題 | ソース | 詳細 |
|------|--------|------|
| 合計・小計行の除外 | 設計提案 | 表パースで「合計」「小計」行を明細から除外 |
| extraction confidence 付与 | 設計提案 | 表/テキスト/フォールバックの信頼度を付与 |
| 日付・ベンダー抽出 | 設計提案 | PDFから invoice_date, vendor を抽出 |
| 2026-FA-01 extraction スキーマ | specs | fields, evidence_refs, confidence の形式準拠 |

### 2.5 税務・判定

| 課題 | ソース | 詳細 |
|------|--------|------|
| 取得価額10%基準 | IMPLEMENTATION_STATUS | 修繕費判定の「取得価額の10%以下」ロジック |
| 継続的メンテナンス vs 価値向上の峻別 | IMPLEMENTATION_AUDIT | 金額・文脈を考慮した判定の強化 |

### 2.6 エラーハンドリング・運用

| 課題 | ソース | 詳細 |
|------|--------|------|
| Vertex AI 呼び出しのタイムアウト処理 | IMPLEMENTATION_AUDIT | - |
| Vertex AI 呼び出しのレート制限処理 | IMPLEMENTATION_AUDIT | - |

---

## 3. 開発・CI/CD

| 課題 | ソース | 詳細 |
|------|--------|------|
| Lint（ruff/black/mypy） | dev_run_checks.ps1 | `# Lint placeholder: add ruff/black/mypy here` |
| Vertex AI 統合後の CI テスト | IMPLEMENTATION_AUDIT | .github/workflows/ci.yml の拡張 |

---

## 4. ドキュメント・仕様との不整合

| 課題 | ソース | 詳細 |
|------|--------|------|
| IMPLEMENTATION_STATUS_REPORT 更新 | - | DocAI・表構造・税務ルール等が実装済みなのに未実装記載 |
| IMPLEMENTATION_AUDIT_REPORT 更新 | - | 同上 |
| integration_test_report 更新 | - | useful_life_estimator.py 存在の反映 |
| final_procedure の core/normalizer.py | final_procedure | 存在しない。adapter の誤記の可能性 |

---

## 5. 将来ビジョン（future_vision.md 記載）

| 課題 | フェーズ | 詳細 |
|------|----------|------|
| 請求書・領収書・注文書対応 | 中期 | 他帳票への横展開 |
| 耐用年数マスタ本格連携 | 短期 | 候補提示と根拠提示 |
| 監査証跡の強化 | 短期 | トレースログ永続化、人間上書き記録 |
| マルチテナント対応 | 短期 | 会社コード別ポリシー |
| 写真・音声・図面/CAD 入力 | 中期 | マルチモーダル対応 |

---

## 6. 優先度別サマリ

### 必須（提出ブロッカー）

1. Zenn記事 + デモ動画 + 参加登録
2. GitHub公開 + Cloud Run再デプロイ
3. commit & push

### 高（優勝・審査に直結）

4. ai_suggestions（勘定科目候補）の実装
5. useful_life の API 統合
6. Vertex AI Search / Gemini の本番動作確認

### 中（差別化・品質向上）

7. evidence_keywords / applied_rule
8. 合計・小計行の除外
9. extraction confidence
10. PDF該当箇所ハイライト

### 低（将来対応）

11. Geminiマルチモーダル
12. 2026-FA-01 スキーマ準拠
13. Lint 整備
14. レポート類の更新
15. UI Future Improvements（Dark Mode, Print, 等）

---

## 7. 実装済みだがレポート未反映のもの

| 項目 | 現状 |
|------|------|
| DocAI | _try_docai 実装済み（IMPLEMENTATION_STATUS は placeholder と誤記載） |
| 表構造抽出 | pdfplumber で実装済み |
| 行単位パース | extraction_to_opal で実装済み |
| 税務ルール（10/20/30/60万） | classifier に _apply_tax_rules 実装済み |
| /classify_pdf | api/main.py に実装済み |
| useful_life_estimator.py | ファイル存在、API 統合のみ未実施 |
| Vertex AI Search | vertex_search.py に実装済み |

---

## 8. 参照ドキュメント

- [submission_checklist.md](./submission_checklist.md)
- [LORD_INSTRUCTIONSハッカソン残タスク.md](./LORD_INSTRUCTIONSハッカソン残タスク.md)
- [IMPLEMENTATION_AUDIT_REPORT.md](./IMPLEMENTATION_AUDIT_REPORT.md)
- [IMPLEMENTATION_STATUS_REPORT.md](./IMPLEMENTATION_STATUS_REPORT.md)
- [integration_test_report.md](./integration_test_report.md)
- [future_vision.md](./future_vision.md)
- [ui_improvements.md](./ui_improvements.md)
- [specs/](./specs/)
