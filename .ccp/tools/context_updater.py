#!/usr/bin/env python3
"""
Developer-tool copy: .ccp/tools/context_updater.py

This script is a developer-side helper that maintains a local `.ccp/context`
state used by developer-sandbox workflows. It is NOT the canonical
`src/mithaly/core/utils/context_updater.py` implementation. Keep scope
limited to local sandboxing and document any behavior differences here.
"""

import json
import sys
import os
from datetime import datetime


def update_context(change):
    root = os.getcwd()
    cpath = os.path.join(root, '.ccp', 'context')
    os.makedirs(cpath, exist_ok=True)
    state_path = os.path.join(cpath, 'state.json')
    if os.path.exists(state_path):
        with open(state_path, 'r', encoding='utf-8') as f:
            try:
                st = json.load(f)
            except Exception:
                st = {}
    else:
        st = {"project": {"name": "mithaly"}}
    st['last_change'] = change
    st['last_updated'] = datetime.now().isoformat()
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(st, f, ensure_ascii=False, indent=2)
    print(f"Updated {state_path} with change: {change}")

if __name__ == '__main__':
    change = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else 'manual'
    update_context(change)
