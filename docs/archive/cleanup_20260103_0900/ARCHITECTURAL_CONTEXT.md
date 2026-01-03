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
----------------------
- See `docs/MITHALY_CONSTITUTION.md` for immutable principles.
- See `docs/mithaly_todo.md` for planned enhancements and design work.

Where to look for more details
------------------------------
- Layer implementations: `src/mithaly/core/gaps`, `src/mithaly/core/planning`, `src/mithaly/core/execution`, `src/mithaly/core/feedback`.
- Engine runner: `src/mithaly/core/engine.py` (canonical).
- **Workflow & Diagrams**: `docs/architecture/workflow.md` (Visual flow of LangGraph & Memory).
- Policy enforcement: `src/mithaly/core/policy.py` and `src/mithaly/core/registry.py`.

Recommended next steps for contributors
-------------------------------------
1. Read `docs/MITHALY_CONSTITUTION.md` to understand immutable constraints.
2. Follow `CONTRIBUTING.md` before adding new files — add a header comment describing intended scope if adding a second file with similar name.
3. Use `PYTHONPATH=src` when running tests locally.

Minimal header template (copy into new files when scope may overlap):
```
# Purpose: short description of what this file does
# Scope: describe the precise responsibility and what it explicitly does NOT do
# Related: reference to other files (example: "see src/mithaly/core/utils/context_updater.py")
```

---

Last updated: 2026-01-03

## Recent changes (snapshot)

- 2026-01-02: Added file-organization rule to constitution and docs; added `generator_adapter` task to TODO; created `docs/ARCHITECTURAL_CONTEXT.md` snapshot.
- 2026-01-03: Integrated optional integrations and moved enforcement tooling:
	- Added optional adapters and probes for LangGraph (`src/mithaly/core/adapter/langgraph_adapter.py`) and MCP (`src/mithaly/core/adapter/mcp_client.py`).
	- Added ChromaDB vector-store adapter (`src/mithaly/core/memory/vector_store.py`) support and Ollama adapter (`src/mithaly/core/adapter/ollama_client.py`).
	- Moved enforcement scripts to `scripts/` and tests to `tests/`; stubs left in `tools/` during transition.
	- Added `requirements-integrations.txt` and `docs/INTEGRATIONS.md` describing optional packages and configuration.

See `docs/mithaly_todo.md` for tasks and `docs/MITHALY_CONSTITUTION.md` for governance.

## Layered Flow Rules
- The layered transition rules and failure scenarios are specified in `docs/rules/layered_flow.md`.
- A machine-readable JSON Schema for recording transitions is available at `docs/context/schemas/layer_transition_schema.json`.
- All transitions should be recorded with provenance into `docs/context/` according to the schema.

```
