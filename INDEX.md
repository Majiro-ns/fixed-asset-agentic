Autonomous Development Rules（Fixed Asset Domain）
Purpose

This repository is developed using issue-driven autonomous development.
The goal is to improve fixed-asset related systems safely and incrementally by letting an AI agent implement only what is explicitly specified, while humans retain final decision authority.

AI is responsible for:

Drafting implementations

Adding/adjusting tests

Opening pull requests

Humans are responsible for:

Defining specifications

Approving plans

Reviewing and merging changes

Making all tax/accounting decisions

Trigger

Autonomous development starts only when:

A human creates a GitHub Issue and

The Issue references a SPEC file under docs/specs/ and

The Issue is explicitly approved to run (e.g. via agent:run label or by saying
“read INDEX.md and do autonomous dev for this issue”)

No trigger → no autonomous work.

Core Principle (Non-Negotiable)

SPEC is the single source of truth

If it is not written, it must not be implemented

When in doubt, stop

Loop (Issue-Driven Development)

Read context

docs/00_project.md

docs/02_arch.md

This INDEX.md

Referenced docs/specs/<task>.md

Propose a plan

Post a short, concrete plan as an Issue comment

Include:

What will change

What will NOT change

Which files/modules are touched

Do not write code yet

Wait for human approval

Coding starts only after explicit approval

e.g. “Approved”, “LGTM”, “Proceed”

No approval → stop and wait

Create an issue branch

Use scripts/dev_take_issue.ps1

Branch naming: ai/issue-<id>

Never work on main

Implement narrowly

Follow the approved plan only

No scope expansion

No spec reinterpretation

If new requirements appear → stop and propose

Run the single quality gate

Execute scripts/dev_run_checks.ps1

Fix failures before proceeding

Open a Pull Request

Reference the Issue

Wait for CI to pass

Address review comments

Merge via PR only

Human decides when to merge

Then move to the next Issue

Plan Approval (Mandatory)

Plans must be written as Issue comments

Coding must not begin without explicit human approval

Silence ≠ approval

If approval is unclear → stop

Ambiguity Handling (Stop-First Rule)

If any of the following occurs:

SPEC is ambiguous

SPEC conflicts with existing rules

Tax/accounting meaning is unclear

Output requirements are underspecified

Then:

Do NOT guess

Do NOT implement

Ask for clarification with concrete options

Default action is NO CHANGE

Quality & Policy Gates
Branch & CI Rules

Direct push to main is forbidden

All changes via PR

CI must pass before merge

Branch protection on main is required

Single Source of Truth for Checks

Defined in docs/01_commands.md

scripts/dev_run_checks.ps1 runs exactly those commands

CI runs the same gate

Escalation Rule

If CI fails 3 consecutive times, stop and escalate to a human

Secrets

Never create, commit, or output secrets

Use only existing environment variables

No new tokens, vaults, or credentials

Execution Lane (Operational Rules)

Unit of work = Issue

Always use issue-scoped branches

Preferred automation:

scripts/dev_take_issue.ps1 -IssueNumber <n>


If automation fails, follow the same steps manually using:

docs/01_commands.md

Forbidden Changes / Stop List

The following require explicit human approval before any implementation:

Tax or accounting decision logic

Fixed asset classification meaning

Useful life / depreciation logic

Evidence or rationale requirements

Silent exception handling

Paid or external SaaS / APIs

Major dependency version bumps

If encountered:

Stop

Propose

Wait for approval

Definition of Done (DoD)

A task is considered DONE only if all of the following are true:

All Acceptance Criteria in the referenced SPEC are satisfied

Evidence and rationale outputs (warnings, evidence) are preserved or expanded — never reduced

scripts/dev_run_checks.ps1 succeeds locally

CI is green

Changes are merged via PR

Current Focus (Updateable)

A1: Quality gate parity (local vs CI)

A2: Policy safety (stop-first, evidence required)

A3: Developer ergonomics (issue automation)

A4: UI review flow (Streamlit demo, secondary)

Working Notes

Prefer adding tests over changing behavior

Keep diffs small and reviewable

Always optimize for explainability, not cleverness

Fixed asset systems must support post-hoc explanation

Final Rule (If You Remember One Thing)

When unsure, stop and ask.
Silence, guessing, or assumption is failure.