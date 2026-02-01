# 01_commands: Single Source of Truth

Environment
- Python 3.11+ recommended. Run in repo root (PowerShell).

Setup
- `python -m pip install --upgrade pip`
- `python -m pip install -r requirements.txt`

Quality gate (local & CI)
- `python -m pytest`
- Rule: scripts/dev_run_checks.ps1 must pass before PR; CI must pass. If CI fails 3 times in a row, escalate to a human.

Manual runs
- Adapter only: `python scripts/run_adapter.py --in data/opal_outputs/01_opal.json --out data/results/01_normalized.json`
- Full pipeline: `python scripts/run_pipeline.py --in data/opal_outputs/01_opal.json --out data/results/01_final.json`
- PDF end-to-end: `python scripts/run_pdf.py --pdf tests/fixtures/sample_text.pdf --out data/results`
- UI (optional): `python -m pip install -r requirements-ui.txt` then `streamlit run ui/app.py` (JSON tab + PDF tab)
- Agent run (GitHub Actions): add label `agent:run` to an Issue (or trigger workflow_dispatch). Agent will branch, run checks, push, and open a PR. It will never auto-merge.

Notes
- scripts/dev_run_checks.ps1 executes the quality gate above and must pass before any PR.
- CI workflow (.github/workflows/ci.yml) calls the same commands to keep parity.
- PDFs: see below for PDF classification runbook.

PDF classification (PowerShell)
- `python scripts/run_pdf.py --pdf tests/fixtures/sample_text.pdf --out data/results`
- Streamlit UI: `streamlit run ui/app.py` then use the **PDF Upload** tab; files land in `data/uploads/*` and `data/results/*`.
- Environment toggles: `USE_DOCAI=true|false` (default false), `USE_LOCAL_OCR=true|false` (default false), `OCR_TEXT_THRESHOLD=<int>` (default 50). OCR is optional; if not installed, the extractor will log/flag and continue with text-only results.

Optional OCR enablement (not required for CI)
- Install pytesseract + Tesseract OCR binary for your OS; set `USE_LOCAL_OCR=true` when needed.
- Keep it off in CI; local-only feature.
