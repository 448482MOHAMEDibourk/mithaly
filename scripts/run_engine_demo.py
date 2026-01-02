#!/usr/bin/env python3
"""Simple runner that demonstrates calling `BuildEngine` from the package.

This is a lightweight demo script replacing the root `core/` runner.
"""
import json
from mithaly.core.engine import BuildEngine


def main():
    e = BuildEngine()
    payload = {"text": "demo run", "non_interactive": True}
    try:
        res = e.run_lifecycle(payload)
    except Exception as exc:
        print("Runner error:", exc)
        return
    print(json.dumps(res if isinstance(res, dict) else {}, indent=2, ensure_ascii=False)[:4000])


if __name__ == '__main__':
    main()
