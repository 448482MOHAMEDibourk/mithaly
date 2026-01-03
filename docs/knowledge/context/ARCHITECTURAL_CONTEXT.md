```markdown
Mithaly — Architectural Context
=================================

Purpose
-------
This file captures the high-level architectural context and decisions for Mithaly so contributors can quickly understand the canonical layout, layer responsibilities, and key governance rules.

Canonical layout
----------------
- Package source: `src/mithaly` (single source-of-truth for runtime code)
- Docs/staging: `docs/` (snapshots, tickets, drafts)
- Archive/legacy: `Raw_Artifact/` (reference only)

Core concepts
-------------
- Layers: `Gaps` → `Planning` → `Execution` → `Feedback` (each has a `process()` API-contract).
- Generator: keeps responsibility for content generation; does not own administrative policies.
- LayerRegistry: central registry for layers and probes (used by `PolicyEnforcer`).
- INFLECTION_POINT: policy-driven stop/human-review hook — snapshot context before halting.

Key governance rules (summary)
------------------------------
- File-organization rule: do not create two files that implement the exact same functional task unless the scope difference is explicitly documented in the file header and referenced in `CONTRIBUTING.md`.
- Trusted-persistence: only records marked `trusted: True` are allowed to be written into the canonical KB via `FeedbackLoop.persist_to_kb()`.

Decision log (pointer)
This file was a duplicate of the canonical architectural context.

Primary copy: [docs/ARCHITECTURAL_CONTEXT.md](docs/ARCHITECTURAL_CONTEXT.md#L1)

Backup: [docs/context/backup/ARCHITECTURAL_CONTEXT.md](docs/context/backup/ARCHITECTURAL_CONTEXT.md#L1)

Action: content removed here to avoid duplication; refer to the primary copy above.

Last modified: 2026-01-02

