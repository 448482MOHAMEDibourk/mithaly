#!/usr/bin/env python3
"""Check that `docs/mithaly_todo.md` was updated when source files change in the PR/branch.

This script is intended to run inside CI after checkout. It compares the current branch
against `origin/main` and ensures that if files under `src/` (or similar) were modified,
then `docs/mithaly_todo.md` was also modified in the same set of changes.

Exit with non-zero status if the rule is violated.
"""
import os
import subprocess
import sys


def run(cmd):
    return subprocess.check_output(cmd, shell=True, text=True).strip()


def main():
    try:
        run("git fetch origin main --depth=1")
    except Exception:
        # best-effort; continue
        pass

    try:
        diff = run("git diff --name-only origin/main...HEAD || git diff --name-only HEAD~1 HEAD")
    except Exception as e:
        print("WARN: could not compute diff:", e)
        diff = ""

    changed = [line for line in diff.splitlines() if line]
    print("Changed files:", changed)

    src_changed = any(p.startswith("src/") or p.startswith("core/") or p.startswith("src/") for p in changed)
    todo_changed = any(p == "docs/mithaly_todo.md" for p in changed)

    if src_changed and not todo_changed:
        print("ERROR: Source files changed but docs/mithaly_todo.md was not updated in this branch/PR.")
        print("Please add/update the corresponding task entry before merging.")
        sys.exit(1)

    print("OK: todo update check passed (or no source changes detected)")


if __name__ == '__main__':
    main()
