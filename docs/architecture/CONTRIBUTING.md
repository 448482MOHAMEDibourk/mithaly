Contribution guidelines
=======================

Project structure and developer notes:

- `src/mithaly`: canonical source code. All active development should target this package.
- `docs/`: temporary staging area for snapshots, analysis tickets, policy drafts, and other administrative artifacts. Do not treat files in `docs/` as authoritative source code.
- `Raw_Artifact/`: archive of past experiments, demos, and legacy projects. Use for reference only; do not import from or run tests inside this folder.

Testing and CI:

- The test suite is configured to ignore `docs/` and `Raw_Artifact/` to avoid collecting legacy examples. Use `PYTHONPATH=src` when running tests locally so the package imports correctly.

If you need to promote an artifact from `docs/` into the canonical KB, use the established workflow (analysis ticket → mark `trusted: True` → `FeedbackLoop.persist_to_kb()`).

File organization rule:

- Avoid duplicate files for the same functional task. If you must create a second file that touches similar functionality, document the difference in the file header and in `docs/` (example: "configurator vs executor — configurator prepares environment, executor runs tasks"). This keeps `src/mithaly` as the single source-of-truth and reduces maintenance overhead.

Allowed exceptions (policy)

The project allows a small set of intentional duplicates where scope is clearly different and documented. When adding or keeping such copies, the file header must explain the scope difference and reference the canonical location.

- `Raw_Artifact/` — archival copies of older projects or experiments. These are reference-only and must be clearly marked as archival (see example in `Raw_Artifact/mithaly_v1/core/engine.py`).
- `docs/context/` — snapshot copies of documentation and context for historical tracing. These files are generated; edit the source under `docs/` and use the snapshot tooling to update copies.
- `.<tool>` folders (e.g., `.ccp/`) — developer sandbox helpers or tool-specific scripts. Mark these as developer-only and avoid importing them in production code.

Any other duplicate must be approved and documented in `docs/mithaly_todo.md` prior to merging.

Respect Constitution and Source of Truth
----------------------------------------

Important: the project constitution (`MITHALY_CONSTITUTION.md`) and the Source of Truth are the legal/operational constraints for this repository and take precedence over local contribution convenience.

- Any promotion, update, or automatic generation that would modify files under `docs/architecture/` that are declared as sacred (for example `docs/architecture/MITHALY_SOURCE_OF_TRUTH_CANONICAL.md`) is explicitly prohibited without a recorded manual approval from the user/owner. Such attempts must trigger an `INFLECTION_POINT` and be blocked from automatic merge.
- Contributors MUST use the `MITHALY_SOURCE_OF_TRUTH` environment variable to point to the canonical Source of Truth file when running tools or scripts that need to reference it. Example: `export MITHALY_SOURCE_OF_TRUTH=/path/to/docs/architecture/MITHALY_SOURCE_OF_TRUTH_CANONICAL.md`.
- Tools that create snapshots (e.g., snapshot tooling which writes to `docs/knowledge/context/snapshots/`) may generate copies only; they must never modify the canonical files under `docs/architecture/` automatically.
- The workflow to promote artifacts from `docs/` into canonical locations must include a manual approval step and an approval record saved in `docs/approvals/` (e.g., `docs/approvals/<pr-number>.approved`) before calling `FeedbackLoop.persist_to_kb()` or merging changes that touch protected documents.
- CI or pre-commit checks should reject pushes/PRs that attempt to modify `docs/architecture/MITHALY_SOURCE_OF_TRUTH` or `MITHALY_CONSTITUTION.md` unless an approval file is present or a maintainer has explicitly granted permission in the PR comments.

Follow these rules to keep the repository consistent with the project constitution.
