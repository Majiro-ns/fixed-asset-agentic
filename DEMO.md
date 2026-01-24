# Fixed Asset Classification Demo Script (3-4 minutes)

## Overview
Demonstrate the agentic fixed-asset classification service with evidence-first outputs and GUIDANCE Q&A loop.

**This demo follows the Agentic 5-step process defined in README.md:**
1. **止まる（GUIDANCE）**: 判断が割れる可能性がある場合、自動判定を停止
2. **根拠提示**: 判定根拠（Evidence）と不足情報（Missing Fields）を明示
3. **質問**: 不足情報について「なぜ必要か（Why Missing Matters）」を説明し、ユーザーに質問
4. **再実行**: ユーザーの回答を受け取り、再分類を実行
5. **差分保存**: 再実行前後の変化（Decision/Confidence/Trace/Citations）を明確に表示

## Setup (0:00-0:10)
**Canonical launch command (ONLY use this):**
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\demo_ui.ps1
```

**Manual fallback (only if demo_ui.ps1 fails):**
```bash
streamlit run ui/app_minimal.py
```

**Before starting:**
- Show Cloud Run URL in sidebar: `https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app`
- Mention: "Rule-first, evidence-first classification with agentic assistance for ambiguous cases"
- **Note:** Legal Citations feature is OFF by default (UI shows "Legal Citations: OFF"). To enable, set `VERTEX_SEARCH_ENABLED=1` (see "Enable Legal Citations" section below).

**デモデータについて:**
- 本デモで使用するすべてのデータ（`data/demo/*.json`）は**架空データ（ダミーデータ）**です。
- 実在の企業名、請求書、見積書は一切含まれていません。

## Demo Timeline

### 0:10-0:40 — CAPITAL_LIKE Case (30 seconds)
**Actions:**
1. Load `demo01_capital_server.json` from dropdown
2. Click "Classify"

**Point to (10-second comprehension):**
- **Decision:** `[CAPITAL_LIKE]` (prominent at top)
- **Confidence:** ~0.8
- **Valid Document:** Yes
- **Trace:** `extract -> parse -> rules -> format` (4 steps)

**Evidence-first display:**
- Evidence panel (expandable, shows Line 1, description, confidence, source text)
- Reasons: "サーバー新設工事" contains "新設" keyword

**Say:** "Clear classification with evidence. Keywords trigger rule-based decision. This demonstrates step 1-2 of the Agentic process: the system makes a decision and shows evidence."

### 0:40-1:10 — EXPENSE_LIKE Case (30 seconds)
**Actions:**
1. Load `demo03_expense_maintenance.json` from dropdown
2. Click "Classify"

**Point to:**
- Decision: `[EXPENSE_LIKE]`
- Evidence panel: Line 1 details
- Reasons: "設備調整" contains "調整" keyword

**Say:** "Different classification based on expense keywords. Rule-based system handles common cases."

### 1:10-3:10 — GUIDANCE Case with Agentic Loop (2 minutes)
**Actions:**
1. Load `demo04_guidance_ambiguous.json` from dropdown
2. Click "Classify"

**Point to (Agentic 5-step demonstration):**

**Step 1: 止まる（GUIDANCE）**
- Decision: `[GUIDANCE]` (yellow)
- **"Agent Needs Information" panel** (prominent at top):
  - Missing fields checklist
  - "Why This Matters" (1-3 bullets, prominent)
  - "What You Should Answer" (guidance text)

**Step 2: 根拠提示**
- Evidence panel (shows source text, confidence)
- Missing fields list
- Why missing matters (explanation)

**Step 3: 質問**
- Quick-pick buttons: "Repair/Maintenance", "Upgrade/New Asset", "Clear All Answers"
- Form fields for missing_fields (with help text)

**Say:** "Ambiguous case triggers GUIDANCE. System identifies missing information and explains why it matters. This is step 1-3 of the Agentic process: stop, show evidence, ask questions."

**Step 4: 再実行**
- Fill in answers (use quick-pick OR form fields)
- Click "Re-run Classification with Answers"

**Step 5: 差分保存**
- **DIFF card appears at top:**
  - Decision: `GUIDANCE → CAPITAL_LIKE` (or similar)
  - Confidence: `0.70 → 0.85`
  - Trace: `extract → parse → rules → format` → `extract → parse → rules → rerun_with_answers → format`
  - Citations: `0 → 0` (or `0 → 3` if VERTEX_SEARCH_ENABLED=1)

**Say:** "Agentic loop shows exactly what changed. The system re-evaluates with your context and provides a clear before/after comparison. This completes steps 4-5: rerun and show diff."

**Legal Citations (if enabled):**
- If `VERTEX_SEARCH_ENABLED=1` is set, show "Legal Citations (Google Cloud Search)" section with citations
- If not set, show "Legal Citations: OFF (set VERTEX_SEARCH_ENABLED=1 to enable)"

### 3:10-3:40 — API Integration (30 seconds)
**Show:**
- Sidebar Service URL
- Mention: "UI calls Cloud Run API via POST /classify"
- Show "Full Result JSON" expander to show API response structure
- Mention: WIN+1 fields (is_valid_document, confidence, trace, missing_fields, why_missing_matters, citations)

### 3:40-3:50 — Closing (10 seconds)
**Summary:**
- Rule-first classification with evidence
- Agentic loop for GUIDANCE cases (5-step process: stop → evidence → question → rerun → diff)
- Evaluation metrics: 100% accuracy on golden set (10/10 pass)
- Cloud Run deployment ready

**Prove evaluation:**
```bash
python scripts/eval_golden.py
```

## Cloud Run デプロイ後スモーク（最小）

デプロイ後の確認は次の 3 段階。PowerShell は 1 コマンドずつ（`&&` 禁止）。

1. **/health** — `curl.exe -s https://SERVICE_URL/health` → `{"ok":true}`
2. **/classify** — JSON で POST（Opal 形式）。`decision` / `trace` 等が返ること。
3. **/classify_pdf OFF** — 既定 OFF のため 400。`detail.error == "PDF_CLASSIFY_DISABLED"` かつ `detail.how_to_enable` / `detail.fallback` が含まれること（UI表示用）。

一括実行: `.\scripts\smoke_cloudrun.ps1`（上記 3 段階をすべて検証）。`$env:CLOUD_RUN_URL` 未設定時は既定 URL を使用。

## PDF Upload Demo (Optional)

**Feature Flag:** `PDF_CLASSIFY_ENABLED` (default: OFF)

To enable PDF upload functionality:

1. Set environment variable:
   ```powershell
   $env:PDF_CLASSIFY_ENABLED="1"
   ```

2. Restart the API service (Cloud Run or local).

3. In UI:
   - Sidebar shows "PDF classification: ON" (or "OFF" if disabled)
   - Upload PDF file via "PDF Upload (Optional)" section
   - Click "Classify PDF" button
   - Results display same as Opal JSON flow (Decision/Confidence/Evidence/GUIDANCE loop)

**UI Behavior (Server Truth-Based):**
- **PDF Upload UI:** Always visible in Input section. UI does NOT check local environment variables. Users can always see and use the PDF upload option.
- **Server Status Detection:** When PDF is uploaded and "Classify PDF" is clicked, UI calls `/classify_pdf` and detects server-side feature flag status from API response:
  - **If server is OFF (400/503 with "disabled"):** UI shows clear error: "Server-side PDF_CLASSIFY_ENABLED=1 is required (feature is OFF on server)" with server response details. This prevents demo accidents where Cloud Run has the feature ON but UI shows OFF due to local env mismatch.
  - **If server is ON:** Normal classification proceeds with same evidence-first display, GUIDANCE loop, DIFF card as Opal JSON flow
- **Results:** Same evidence-first display, GUIDANCE loop, DIFF card as Opal JSON flow

**Note:** Default is OFF on server. The demo works perfectly with Opal JSON input. PDF upload is an optional enhancement. **UI always shows PDF upload option; server status is determined by actual API response (server truth), not local environment variables.**

## Enable Legal Citations (Optional)

**Feature Flag:** `VERTEX_SEARCH_ENABLED` (default: OFF)

To enable Vertex AI Search (Discovery Engine) for legal/regulation citations:

1. Set environment variables:
   ```powershell
   $env:VERTEX_SEARCH_ENABLED="1"
   $env:GOOGLE_CLOUD_PROJECT="your-project-id"
   $env:DISCOVERY_ENGINE_DATA_STORE_ID="your-datastore-id"
   ```

2. Install optional dependency (if not already installed):
   ```powershell
   pip install google-cloud-discoveryengine>=0.11.0
   ```

3. Restart the API service (Cloud Run or local).

**UI Behavior:**
- **When OFF (default):** UI shows "Legal Citations: OFF (set VERTEX_SEARCH_ENABLED=1 to enable)"
- **When ON:** UI shows "Legal Citations (Google Cloud Search)" section with citation cards (title, snippet, URI, relevance_score)
- **In DIFF card:** Citations count shows `0 → 0` (OFF) or `0 → 3` (ON, if citations found)

**Note:** Default is OFF. Tests and golden set evaluation do not require this feature. The demo works perfectly without this feature enabled.

## Timing Breakdown (Timeline Format)
- **0:00-0:10** Setup (10s)
- **0:10-0:40** Case 1 (CAPITAL): 30s
- **0:40-1:10** Case 2 (EXPENSE): 30s
- **1:10-3:10** Case 3 (GUIDANCE + Agentic Loop): 120s
- **3:10-3:40** API Integration: 30s
- **3:40-3:50** Closing: 10s
- **Total: ~3 minutes 50 seconds**

## Notes
- Keep it fast-paced
- Focus on evidence and traceability
- Emphasize the agentic loop as the "WIN+1" feature
- Show both UI and API capabilities
- No emojis/special symbols (cp932 safety)
