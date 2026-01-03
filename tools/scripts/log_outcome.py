#!/usr/bin/env python3
"""Log outcome patterns (success/failure) into docs/knowledge/outcomes.json

Usage:
  python tools/scripts/log_outcome.py --status success --pattern "unit-test failure: ..."
"""
import json
import os
import argparse
from datetime import datetime, timezone


print("This script has been moved to scripts/log_outcome.py — use that path instead.")
import sys
sys.exit(0)


def load():
    if os.path.exists(OUT):
        with open(OUT, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return []
    return []


def save(data):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--status", choices=["success", "failure"], required=True)
    p.add_argument("--pattern", required=True)
    args = p.parse_args()

    items = load()
    items.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": args.status,
        "pattern": args.pattern,
    })
    save(items)
    print("Logged outcome")


# original implementation moved; stubbed here
