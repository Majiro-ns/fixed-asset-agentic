# Cloud Run が Ready でないときのデモ代替（Docker 一本道）

[DEMO_RUNBOOK.md](DEMO_RUNBOOK.md) の Cloud Run ルートが使えないときに、Docker のみでデモする手順。概要は Runbook、詳細はここ。

---

## いつ使うか

- Cloud Run が **ContainerImageImportFailed** やその他で **Ready にならない** とき。
- 審査やデモの時間内に Cloud Run を直せないとき。
- **→ Docker だけで同じ価値を示す。**

---

## やること（一本道）

**分岐はひとつだけ**: Cloud Run が Ready でない → Docker で実施。

1. リポジトリルートに `cd` する。
2. `docker build -t fixed-asset-api .` を実行する。
3. `docker run --rm -e PORT=8080 -p 8080:8080 fixed-asset-api` を**ターミナル 1**で起動する。
4. **ターミナル 2**で `.\scripts\docker_smoke.ps1` を実行する。
5. 成功なら `=== All docker smoke tests passed ===`。ここまでで /health・/classify・/classify_pdf OFF の期待値は満たす。
6. デモで話す内容（目的・Stop-first・evidence・税務閾値・/classify_pdf の安全設計）は [DEMO_RUNBOOK.md](DEMO_RUNBOOK.md) の 1・3・5 に沿う。

---

## コピペ用（ターミナル 1 / 2）

**ターミナル 1（コンテナ起動）:**

```powershell
cd c:\Users\owner\Desktop\fixed-asset-agentic-repo
docker build -t fixed-asset-api .
docker run --rm -e PORT=8080 -p 8080:8080 fixed-asset-api
```

**ターミナル 2（スモーク、起動後に実行）:**

```powershell
cd c:\Users\owner\Desktop\fixed-asset-agentic-repo
.\scripts\docker_smoke.ps1
```

- パスは環境に合わせて読み替える。`DOCKER_SMOKE_URL` 未設定時は `http://localhost:8080`。

---

## 詳細・Cloud Run 復旧

- Docker のくわしい手順・期待値: [DOCKER_LOCAL_SMOKE.md](DOCKER_LOCAL_SMOKE.md)
- デモの話し方・QA: [DEMO_RUNBOOK.md](DEMO_RUNBOOK.md)
- Cloud Run の切り分け・IAM・再デプロイ: [CLOUDRUN_TROUBLESHOOTING.md](CLOUDRUN_TROUBLESHOOTING.md)、`scripts/cloudrun_triage_and_fix.ps1`
- 貼り付け用テンプレ: [CLOUDRUN_TRIAGE_TEMPLATE.md](CLOUDRUN_TRIAGE_TEMPLATE.md)
