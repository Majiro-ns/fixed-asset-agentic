# 03_rules: Fixed-Asset Domain Safety

Principles
- Always include rationale and evidence fields when classifying line items; stop-first bias toward GUIDANCE.
- Do not swallow exceptions; bubble with context so humans can intervene.
- Ambiguity (mixed keywords, missing signals) must land in GUIDANCE with flags.
- Large amounts (threshold-based) can force GUIDANCE via policy; never auto-approve.

Forbidden
- Changing tax/accounting decision rules without explicit approval (propose in PR description first).
- Removing or downgrading evidence/rationale requirements.
- Adding unapproved paid/external services or credentials without explicit approval. (Approved: Gemini API, Document AI, Vertex AI Search, Cloud Run.)
- Major version bumps of dependencies without approval; propose instead.
- Silently ignoring malformed input/policy; prefer safe defaults plus visible flags.

Process
- Work per issue on branches issue/<id>; no direct main pushes. Enable branch protection (PR + CI required).
- Run scripts/dev_run_checks.ps1 before PR; CI runs the same commands.
- Keep policy additions additive and reviewable; default behavior must remain safe if a policy file is missing or invalid.
