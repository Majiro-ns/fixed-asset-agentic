# Fixed Asset Classification Demo Script (3-4 minutes)

## Overview
Demonstrate the agentic fixed-asset classification service with evidence-first outputs and GUIDANCE Q&A loop.

## Setup (10 seconds)
- **Launch UI (canonical):**
  ```powershell
  powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\demo_ui.ps1
  ```
- **Manual fallback (if demo_ui.ps1 fails):**
  ```bash
  streamlit run ui/app_minimal.py
  ```
- Show Cloud Run URL in sidebar: `https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app`
- Mention: "Rule-first, evidence-first classification with agentic assistance for ambiguous cases"

## Demo Flow

### 1. CAPITAL_LIKE Case (30 seconds)
- **Load:** `demo01_capital_server.json` from dropdown
- **Click:** "Classify"
- **Point to:**
  - Decision: `[CAPITAL_LIKE]` (green)
  - Confidence: ~0.8
  - Reasons: "サーバー新設工事" contains "新設" keyword
  - Evidence table: Line 1, description, confidence, source text
  - Trace: `extract -> parse -> rules -> format`
- **Say:** "Clear classification with evidence. Keywords trigger rule-based decision."

### 2. EXPENSE_LIKE Case (30 seconds)
- **Load:** `demo03_expense_maintenance.json` from dropdown
- **Click:** "Classify"
- **Point to:**
  - Decision: `[EXPENSE_LIKE]` (blue)
  - Reasons: "設備調整" contains "調整" keyword
  - Evidence table: Line 1 details
- **Say:** "Different classification based on expense keywords. Rule-based system handles common cases."

### 3. GUIDANCE Case with Agentic Loop (2 minutes)
- **Load:** `demo04_guidance_ambiguous.json` from dropdown
- **Click:** "Classify"
- **Point to:**
  - Decision: `[GUIDANCE]` (yellow)
  - Missing Fields panel: What's missing and why it matters
  - Questions: Generated from flags
- **Say:** "Ambiguous case triggers GUIDANCE. System identifies missing information."
- **Agentic Loop:**
  - Fill in answers to questions (e.g., "This is a capital expense for new equipment")
  - **Click:** "Re-run Classification with Answers"
  - **Point to:**
    - Updated trace: includes `rerun_with_answers`
    - Potentially updated decision (if answers resolve ambiguity)
    - Updated confidence
- **Say:** "Agentic loop allows user to provide context. System re-evaluates with additional information."

### 4. API Integration (30 seconds)
- **Show:** Sidebar Service URL
- **Mention:** "UI calls Cloud Run API via POST /classify"
- **Show:** "Full Result JSON" expander to show API response structure
- **Mention:** WIN+1 fields (is_valid_document, confidence, trace, missing_fields, why_missing_matters)

## Closing (10 seconds)
- **Summary:**
  - Rule-first classification with evidence
  - Agentic loop for GUIDANCE cases
  - Evaluation metrics: 100% accuracy on golden set (10/10 pass)
  - Cloud Run deployment ready
- **Prove evaluation:**
  ```bash
  python scripts/eval_golden.py
  ```
- **Next steps:** Vertex AI integration for advanced GUIDANCE assistance

## Timing Breakdown
- Setup: 10s
- Case 1 (CAPITAL): 30s
- Case 2 (EXPENSE): 30s
- Case 3 (GUIDANCE + Loop): 120s
- API Integration: 30s
- Closing: 10s
- **Total: ~3.5 minutes**

## Notes
- Keep it fast-paced
- Focus on evidence and traceability
- Emphasize the agentic loop as the "WIN+1" feature
- Show both UI and API capabilities
- No emojis/special symbols (cp932 safety)
