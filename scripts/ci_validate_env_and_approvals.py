#!/usr/bin/env python3
"""CI helper: disallow enabling sensitive agent env vars unless approval files exist.

Exits with non-zero code to fail CI when unapproved variables are set.
"""
import os
import sys

ROOT = os.path.abspath(os.path.dirname(__file__) + "/..")
RESTRICTED_VARS = [
    "ENABLE_CONTINUE_MITHALY_SOT",
    "ENABLE_CURSORRULES",
]

def has_approval(var):
    # Accept either a specific approval file or a global APPROVALS.md
    approval_paths = [
        os.path.join(ROOT, 'docs', 'approvals', f'APPROVAL_{var}.md'),
        os.path.join(ROOT, 'docs', 'approvals', 'APPROVALS.md'),
        os.path.join(ROOT, 'docs', 'approvals', f'{var}.approved'),
    ]
    for p in approval_paths:
        if os.path.exists(p):
            return True, p
    return False, None

def is_enabled(val):
    if val is None:
        return False
    return str(val).strip().lower() in ('1','true','yes','on')

def main():
    offending = []
    for v in RESTRICTED_VARS:
        val = os.environ.get(v)
        if is_enabled(val):
            ok, path = has_approval(v)
            if not ok:
                offending.append(v)
            else:
                print(f'Approval found for {v}: {path}')

    if offending:
        print('ERROR: Restricted agent environment variables enabled without approval:')
        for o in offending:
            print(' -', o)
        print('\nTo approve enabling these, add one of:')
        print(' - docs/approvals/APPROVAL_<ENV_VAR>.md')
        print(' - docs/approvals/APPROVALS.md (global approvals)')
        print(' - docs/approvals/<ENV_VAR>.approved')
        sys.exit(1)

    print('No unapproved restricted env vars enabled.')

if __name__ == '__main__':
    main()
