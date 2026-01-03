#!/usr/bin/env python3
"""Continue.dev custom context provider: Mithaly Source-of-Truth

This provider returns a small context dict containing the contents of the
file pointed to by the `MITHALY_SOURCE_OF_TRUTH` environment variable.

Safe-by-default: provider only returns content when `ENABLE_CONTINUE_MITHALY_SOT=1`.
"""
import os
from typing import Optional, Dict


def provide_context() -> Optional[Dict[str, str]]:
    if os.environ.get("ENABLE_CONTINUE_MITHALY_SOT", "0") != "1":
        return None
    path = os.environ.get("MITHALY_SOURCE_OF_TRUTH")
    if not path:
        return None
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return None
    return {"mithaly_source_of_truth": content}


if __name__ == "__main__":
    # Simple CLI for debugging
    import json
    print(json.dumps(provide_context() or {}))
