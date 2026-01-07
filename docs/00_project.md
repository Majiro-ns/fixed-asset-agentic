# 00_project: Purpose and Scope

Purpose
- Convert Opal OCR/output into a frozen schema, classify line items into CAPITAL_LIKE / EXPENSE_LIKE / GUIDANCE with a stop-first bias.
- Provide a minimal agent-friendly workflow (adapter + classifier + policy hook) with clear quality gates for issue-driven development.

Scope
- Python core: core/adapter.py, classifier.py, policy.py, pipeline.py, schema.py.
- CLI helpers: scripts/run_adapter.py, scripts/run_pipeline.py.
- Policy extension: policies/company_default.json or custom policy via POLICY_PATH.
- Sample data: data/opal_outputs/*.json and derived results.
- UI demo: ui/app.py (Streamlit) for interactive review.

Non-goals
- No production accounting/tax advice; classifications stay stop-first and require human review.
- No external services, paid APIs, or credentials.
- No changes to OCR (Opal output is treated as input).
