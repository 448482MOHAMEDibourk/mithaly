#!/usr/bin/env python3
"""Log outcome patterns (success/failure) into docs/knowledge/outcomes.json

Moved from tools/scripts; adjusted ROOT.
"""
import json
import os
import argparse
from datetime import datetime, timezone


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, "docs", "knowledge", "outcomes.json")


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


if __name__ == '__main__':
    main()
