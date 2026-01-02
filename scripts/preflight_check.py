#!/usr/bin/env python3
"""Preflight checks to enforce repository rules before merge.

This is the moved copy from tools/scripts with ROOT adjusted for new location.
"""
import json
import os
import sys


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def fail(msg: str):
    print("ERROR:", msg)
    sys.exit(1)


def check_paths():
    required = [
        os.path.join(ROOT, "docs"),
        os.path.join(ROOT, "docs", "architecture"),
        os.path.join(ROOT, "docs", "MITHALY_CONSTITUTION.md"),
        os.path.join(ROOT, "docs", "ARCHITECTURAL_CONTEXT.md"),
        os.path.join(ROOT, "docs", "PLANS.md"),
        os.path.join(ROOT, "docs", "mithaly_todo.md"),
        os.path.join(ROOT, "docs", "context", "current_context.json"),
    ]
    missing = [p for p in required if not os.path.exists(p)]
    if missing:
        fail("Missing required documentation paths/files: " + ", ".join(missing))
    print("OK: required doc paths exist")


def check_current_context():
    path = os.path.join(ROOT, "docs", "context", "current_context.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        fail(f"Failed to parse current_context.json: {e}")
    if not isinstance(data, dict) or "last_updated" not in data:
        fail("current_context.json must be a JSON object with at least a 'last_updated' field")
    print("OK: current_context.json parsed and contains last_updated")


def check_todo():
    path = os.path.join(ROOT, "docs", "mithaly_todo.md")
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
    except Exception as e:
        fail(f"Failed to read mithaly_todo.md: {e}")
    if not content or len(content) < 10:
        fail("mithaly_todo.md appears empty or too small; ensure tasks are recorded there before changes")
    print("OK: mithaly_todo.md present and non-empty")


def main():
    check_paths()
    check_current_context()
    check_todo()
    print("Preflight checks passed")


if __name__ == "__main__":
    main()
