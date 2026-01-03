# System Restructuring and Deduplication Plan

This plan addresses the "Single Source of Truth" violation by merging and removing redundant directories and files.

## User Review Required

> [!WARNING]
> **Deletions and Moves**: This plan involves moving files and deleting redundant wrappers.
> - `core/` directory will be deleted.
> - `tools/` directory will be merged into `scripts/` and `tests/`.
> - `docs/context/ARCHITECTURAL_CONTEXT.md` will be removed in favor of `docs/ARCHITECTURAL_CONTEXT.md`.

## Proposed Changes

### 1. Test Consolidation
- **Source**: `tools/tests/`
- **Destination**: `tests/`
- **Action**: Move all files. Delete `tools/tests/`.

### 2. Scripts Consolidation
- **Source**: `tools/scripts/`
- **Destination**: `scripts/`
- **Action**: Move all files. Delete `tools/scripts/`.

### 3. Core Cleanup
- **Target**: `core/` (root directory)
- **Action**: Delete `core/` directory.
- **Replacement**: Create `scripts/run_engine_demo.py` containing the logic from `core/engine.py` (updated imports).

### 4. Documentation Deduplication
- **Todo**:
    - Overwrite `docs/mithaly_todo.md` with content from `docs/mithaly_todo_updated.md`.
    - Delete `docs/mithaly_todo_updated.md` and `docs/mithaly_todo.md.bak`.
- **Context**:
    - Delete `docs/context/ARCHITECTURAL_CONTEXT.md` (Redundant copy).
    - Source of Truth: `docs/ARCHITECTURAL_CONTEXT.md`.

## Verification Plan

### Automated
- Run `find . -maxdepth 2` to verify directory structure cleanup.
- Run `python3 scripts/run_engine_demo.py` to ensure the moved runner still works.
- Run `python3 tests/test_policy_constitution.py` to ensure tests still run.

### Manual
- Check that `docs/mithaly_todo.md` contains the latest tasks.
