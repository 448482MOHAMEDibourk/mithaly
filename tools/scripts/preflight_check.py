#!/usr/bin/env python3
"""Preflight checks to enforce repository rules before merge.

Checks performed:
- existence of required docs and architecture directories/files
- presence of `docs/context/current_context.json` and parsable JSON
- `docs/mithaly_todo.md` exists and is non-empty

Exit code 1 on any failure.
"""
import json
import os
import sys


print("This script has been moved to scripts/preflight_check.py — use that path instead.")
sys.exit(0)
