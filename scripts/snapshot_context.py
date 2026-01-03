#!/usr/bin/env python3
"""Snapshot the ARCHITECTURAL_CONTEXT into `docs/context/` and update current_context.json and history.md.

Moved from tools/scripts with ROOT adjusted.
"""
import json
import os
from datetime import datetime, timezone


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def write_snapshot():
    src = os.path.join(ROOT, "docs", "ARCHITECTURAL_CONTEXT.md")
    dst_dir = os.path.join(ROOT, "docs", "context")
    dst = os.path.join(dst_dir, "ARCHITECTURAL_CONTEXT.md")
    os.makedirs(dst_dir, exist_ok=True)
    with open(src, "r", encoding="utf-8") as f:
        content = f.read()
    with open(dst, "w", encoding="utf-8") as f:
        f.write(content)

    cc_path = os.path.join(dst_dir, "current_context.json")
    now = datetime.now(timezone.utc).isoformat()
    current = {
        "last_updated": now,
        "summary": "Architectural context snapshot",
        "files": ["docs/ARCHITECTURAL_CONTEXT.md", "docs/context/ARCHITECTURAL_CONTEXT.md"],
    }
    with open(cc_path, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2, ensure_ascii=False)

    hist = os.path.join(dst_dir, "history.md")
    with open(hist, "a", encoding="utf-8") as f:
        f.write(f"\n## {now}\n\n- Snapshot: ARCHITECTURAL_CONTEXT.md copied to docs/context.\n")
    print("Snapshot written")


if __name__ == "__main__":
    write_snapshot()
