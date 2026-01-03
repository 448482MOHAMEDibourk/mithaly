"""Approve an inflection transition by id.

Usage: PYTHONPATH=./src python3 scripts/approve_inflection.py <transition_id> --approver NAME

This writes `docs/context/approvals/approval_<transition_id>.json` containing approver and timestamp.
"""
import sys
import os
import json
from datetime import datetime


def main(argv):
    if len(argv) < 2:
        print("Usage: approve_inflection.py <transition_id> --approver NAME")
        return 2
    transition_id = argv[0]
    approver = None
    if '--approver' in argv:
        idx = argv.index('--approver')
        if idx + 1 < len(argv):
            approver = argv[idx + 1]

    if not approver:
        print("Error: provide --approver NAME")
        return 2

    out_dir = os.path.join('docs', 'context', 'approvals')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"approval_{transition_id}.json")
    record = {
        'transition_id': transition_id,
        'approved_by': approver,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    print(f"Approved transition {transition_id} by {approver}. Wrote: {out_path}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
