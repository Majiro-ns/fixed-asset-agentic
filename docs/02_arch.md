# 02_arch: Structure and Responsibilities

Directories
- core/: adapter (normalize Opal), classifier (rule-based labels), policy (safe loading), schema (frozen v1.0), pipeline (adapter+classifier wiring), pdf_extract (PDF extraction with DocAI/PyMuPDF fallback), pdf_splitter, ledger_import.
- api/: main.py (FastAPI endpoints on Cloud Run), gemini_classifier.py (Gemini 3 Pro classification with thinking_level=HIGH), gemini_splitter.py (Gemini 2.0 Flash PDF splitting), vertex_search.py (legal citation search), useful_life_estimator.py, history_search.py, similarity_search.py, embedding_store.py.
- scripts/: run_adapter.py, run_pipeline.py (CLI entry points).
- data/: demo/ samples, golden/ evaluation set, results/ outputs.
- policies/: company_default.json (optional policy hook; fallback is empty policy).
- ui/: app_minimal.py (Streamlit main UI), app_classic.py (legacy), components/ (hero, input, result_card, guidance_panel, diff_display).

Data flow
1) Opal JSON -> adapt_opal_to_v1 (core/adapter.py) -> normalized schema v1.0.
2) load_policy (core/policy.py) -> safe defaults if missing/invalid.
3) classify_document (core/classifier.py) -> line_items marked CAPITAL_LIKE/EXPENSE_LIKE/GUIDANCE with flags/rationale.
4) pipeline (core/pipeline.py) orchestrates adapter + classifier; scripts/run_pipeline.py wraps it.

Boundaries
- Adapter does pure field shaping; no business rules.
- Classifier is stop-first: ambiguity routes to GUIDANCE; policies can only add guidance/flags, not relax safety.
- Policy loader must never fail the pipeline; malformed policy reverts to empty defaults.
- UI is best-effort visualization; it should not change core logic.
