# Fixed Asset Classification - Demo Runbook

> **Purpose**: Demo script for Agentic AI Hackathon with Google Cloud (3-4 minutes)
> **Target Audience**: Hackathon judges, technical evaluators
> **Format**: Operation steps + Narration scripts + Emphasis points

---

## Timeline Overview

| Time | Section | Duration | Focus |
|------|---------|----------|-------|
| 0:00-0:30 | Problem Statement | 30s | Why this matters |
| 0:30-1:00 | Case 1: CAPITAL_LIKE | 30s | Clear classification |
| 1:00-1:30 | Case 2: EXPENSE_LIKE | 30s | Rule-based decision |
| 1:30-3:00 | Case 3: GUIDANCE + Agentic Loop | 90s | Stop-first design |
| 3:00-3:30 | Technical Highlights | 30s | Architecture |
| 3:30-4:00 | Summary | 30s | Key takeaways |

---

## Demo Data Notice

All demo data in `data/demo/*.json` is **fictional sample data** created for this hackathon. No real company names, invoices, or estimates are included.

---

## Setup (Before Recording)

### Launch Command (Canonical)
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\demo_ui.ps1
```

### Manual Fallback (if demo_ui.ps1 fails)
```bash
streamlit run ui/app_minimal.py
```

### Pre-Demo Checklist
- [ ] Cloud Run URL visible in sidebar: `https://fixed-asset-agentic-api-986547623556.asia-northeast1.run.app`
- [ ] Browser: Chrome, full screen mode, 1920x1080
- [ ] Demo JSON files loaded in dropdown
- [ ] Legal Citations: OFF by default (shown in sidebar)

### Recording Setup
- **Resolution**: 1920x1080 recommended
- **Pacing**: Moderate (150 words/min), pause when showing results
- **Audio**: Clear narration, let visual changes settle before speaking

---

## Section 1: Problem Statement (0:00-0:30)

### Screen Direction
- **0:00-0:10**: Title card or Streamlit UI welcome screen
- **0:10-0:30**: Point to architecture diagram or UI

### Narration Script

> **[0:00-0:05]**
> "Fixed Asset Classification - an Agentic AI that knows when to stop."

> **[0:05-0:15]**
> "In accounting departments, classifying expenses as fixed assets or operating costs is critical for tax compliance. But AI systems that blindly automate this process create a dangerous problem: when the AI is wrong, there's no time to catch the error before month-end close."

> **[0:15-0:25]**
> "Our solution takes a different approach. Instead of forcing a decision on ambiguous cases, the system autonomously recognizes uncertainty and stops - asking for human judgment exactly when it's needed."

> **[0:25-0:30]**
> "Let me show you how it works."

### Emphasis Points
- **Key phrase**: "knows when to stop"
- **Problem**: Blind automation + time pressure = undetected errors
- **Solution**: Autonomous stop decision

---

## Section 2: Case 1 - CAPITAL_LIKE (0:30-1:00)

### Actions
1. Load `demo01_capital_server.json` from dropdown
2. Click "Classify"

### Screen Direction
1. Show Streamlit UI (browser)
2. Highlight: Decision badge, Confidence score, Evidence panel

### Narration Script

> **[0:30-0:35]**
> "First, a straightforward case. This invoice is for a new server installation."

> **[0:35-0:50]**
> "The system immediately returns CAPITAL_LIKE with high confidence. Notice the evidence panel - it shows exactly which keywords triggered this classification and the source text."

> **[0:50-1:00]**
> "Clear cases are handled automatically with full traceability."

### Point to (Visual Highlights)
- **Decision**: `[CAPITAL_LIKE]` (green, prominent at top)
- **Confidence**: ~0.8
- **Valid Document**: Yes
- **Trace**: `extract -> parse -> rules -> format` (4 steps)
- **Evidence panel**: Line 1, description, confidence, source text
- **Reasons**: "contains keyword triggering capital classification"

### Emphasis Points
- **Visual**: Green "CAPITAL_LIKE" badge
- **Key message**: Automatic + traceable

---

## Section 3: Case 2 - EXPENSE_LIKE (1:00-1:30)

### Actions
1. Load `demo03_expense_maintenance.json` from dropdown
2. Click "Classify"

### Narration Script

> **[1:00-1:05]**
> "Now a maintenance case. Equipment adjustment - clearly operational."

> **[1:05-1:20]**
> "EXPENSE_LIKE classification. The keyword 'adjustment' triggered this. Rule-based decisions handle 80% of cases instantly."

> **[1:20-1:30]**
> "Speed and consistency - the system applies the same rules every time."

### Point to (Visual Highlights)
- **Decision**: `[EXPENSE_LIKE]` (blue)
- **Evidence panel**: Line 1 details
- **Reasons**: keyword-triggered classification

### Emphasis Points
- **Visual**: Blue "EXPENSE_LIKE" badge
- **Speed**: Near-instant response
- **Key message**: Rule-first design

---

## Section 4: Case 3 - GUIDANCE + Agentic Loop (1:30-3:00)

This is the core demonstration of the **Agentic 5-step process**:

1. **Stop (GUIDANCE)**: Detect ambiguity, halt automatic classification
2. **Evidence**: Show reasoning and missing information
3. **Question**: Explain why missing info matters, prompt user
4. **Re-run**: Process with additional context
5. **Diff**: Display before/after comparison with full trace

### Actions
1. Load `demo04_guidance_ambiguous.json` from dropdown
2. Click "Classify"
3. Observe GUIDANCE result
4. Fill in answers (use quick-pick OR form fields)
5. Click "Re-run Classification with Answers"
6. Show DIFF card

### Narration Script

> **[1:30-1:40]**
> "Now the interesting part. This invoice has ambiguous wording - it could be a repair or an upgrade. Watch what happens."

> **[1:40-1:55]**
> "GUIDANCE. The system stopped itself. It detected ambiguity and autonomously decided not to guess. This is the core of our Agentic design."

> **[1:55-2:10]**
> "Look at this panel. The system explains exactly what information is missing and why it matters for classification. It's not just saying 'I don't know' - it's telling you what to check."

> **[2:10-2:25]**
> "I'll provide the context using these quick-pick options. This simulates asking the vendor or checking the contract."

> **[2:25-2:40]**
> "Re-run... and now we get a confident decision."

> **[2:40-3:00]**
> "The DIFF card shows exactly what changed - decision, confidence, and the reasoning trace. Full audit trail for compliance."

### Point to (Visual Highlights)

**Step 1-2: Stop and Evidence**
- **Decision**: `[GUIDANCE]` (yellow badge)
- **"Agent Needs Information" panel** (prominent at top):
  - Missing fields checklist
  - "Why This Matters" (1-3 bullets)
  - "What You Should Answer"

**Step 3: Question**
- Quick-pick buttons: "Repair/Maintenance", "Upgrade/New Asset", "Clear All Answers"
- Form fields for missing_fields (with help text)

**Step 4-5: Re-run and Diff**
- **DIFF card** (appears at top after re-run):
  - Decision: `GUIDANCE -> CAPITAL_LIKE` (or similar)
  - Confidence: `0.70 -> 0.85`
  - Trace: shows `rerun_with_answers` step added
  - Citations: `0 -> 0` (or `0 -> 3` if VERTEX_SEARCH_ENABLED=1)

### Emphasis Points
- **Critical visual**: Yellow "GUIDANCE" badge
- **Agentic moment**: System autonomously stops
- **Resolution**: DIFF card showing before/after
- **Audit**: Complete trace of decision change

---

## Section 5: Technical Highlights (3:00-3:30)

### Screen Direction
- Show sidebar with Cloud Run URL
- Or show architecture diagram (from README.md mermaid)

### Narration Script

> **[3:00-3:10]**
> "Under the hood, this runs on Google Cloud. Cloud Run hosts the API. Document AI handles PDF extraction. Optionally, Vertex AI Search provides legal regulation citations."

> **[3:10-3:20]**
> "The classifier uses a rule-first design with frozen schema. This means reproducible, testable decisions - not black-box AI."

> **[3:20-3:30]**
> "Golden set evaluation shows 100% accuracy on 10 test cases. The system is ready for production deployment."

### Point to
- Sidebar Service URL: `https://fixed-asset-agentic-api-...`
- Mention: "UI calls Cloud Run API via POST /classify"
- Show "Full Result JSON" expander (optional)

### Emphasis Points
- **Google Cloud stack**: Cloud Run, Document AI, Vertex AI Search
- **Design principle**: Rule-first, frozen schema
- **Quality**: 100% golden set accuracy (10/10 pass)

---

## Section 6: Summary (3:30-4:00)

### Narration Script

> **[3:30-3:40]**
> "To summarize: this is an Agentic AI that classifies fixed assets with evidence and stops when uncertain. It doesn't replace human judgment - it supports it by knowing when to ask."

> **[3:40-3:50]**
> "Future extensions include integration with accounting systems and historical decision comparison - always maintaining the stop-first design."

> **[3:50-4:00]**
> "Fixed Asset Agentic - AI that's smart enough to know when not to decide. Thank you."

### Emphasis Points
- **Tagline**: "Smart enough to know when not to decide"
- **Future**: Extensible while maintaining core design

### Prove Evaluation (Optional)
```bash
python scripts/eval_golden.py
```

---

## Appendix A: Cloud Run Smoke Test

Post-deployment verification (PowerShell, one command at a time):

1. **/health**
   ```powershell
   curl.exe -s https://SERVICE_URL/health
   ```
   Expected: `{"ok":true}`

2. **/classify** - POST with Opal JSON format
   Expected: `decision`, `trace`, `evidence` in response

3. **/classify_pdf OFF** - Default OFF, expect 400
   Expected: `detail.error == "PDF_CLASSIFY_DISABLED"` with `how_to_enable` and `fallback`

One-shot verification:
```powershell
.\scripts\smoke_cloudrun.ps1
```

---

## Appendix B: Optional Features

### PDF Upload (Feature-Flagged)

**Flag**: `PDF_CLASSIFY_ENABLED` (default: OFF)

To enable:
```powershell
$env:PDF_CLASSIFY_ENABLED="1"
```

**UI Behavior (Server Truth-Based)**:
- PDF Upload UI is always visible
- Server status detected from actual API response
- If server OFF: Clear error message shown
- If server ON: Normal classification with same evidence-first display

### Legal Citations / Vertex AI Search (Feature-Flagged)

**Flag**: `VERTEX_SEARCH_ENABLED` (default: OFF)

To enable:
```powershell
$env:VERTEX_SEARCH_ENABLED="1"
$env:GOOGLE_CLOUD_PROJECT="your-project-id"
$env:DISCOVERY_ENGINE_DATA_STORE_ID="your-datastore-id"
pip install google-cloud-discoveryengine>=0.11.0
```

**UI Behavior**:
- When OFF: "Legal Citations: OFF" shown
- When ON: Citations cards with title, snippet, URI, relevance_score
- DIFF card shows Citations count change

### Document AI (Cloud AI)

**Flag**: `USE_DOCAI=1` enables Document AI for PDF extraction. Falls back to PyMuPDF/pdfplumber when unset.

---

## Appendix C: Quick Reference

### Agentic 5-Step Process
1. **Stop (GUIDANCE)**: Detect ambiguity, halt automatic classification
2. **Evidence**: Show reasoning and missing information
3. **Question**: Explain why missing info matters, prompt user
4. **Re-run**: Process with additional context
5. **Diff**: Display before/after comparison with full trace

### Key Differentiators
- **Stop-first design**: Unlike typical automation that forces decisions
- **Evidence transparency**: Every decision has traceable reasoning
- **Human-AI collaboration**: AI handles clear cases, humans handle edge cases
- **Audit-ready**: Complete trace for compliance requirements

### Key Moments to Emphasize (Recording)
1. **0:20** - "knows when to stop" (lean into this phrase)
2. **1:45** - GUIDANCE result appears (pause for effect)
3. **2:40** - DIFF card appears (highlight the comparison)
4. **3:55** - Closing tagline

---

## Notes

- Keep it fast-paced
- Focus on evidence and traceability
- Emphasize the agentic loop as the "WIN+1" feature
- Show both UI and API capabilities
- No emojis/special symbols (cp932 safety)
