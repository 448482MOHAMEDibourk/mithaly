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
