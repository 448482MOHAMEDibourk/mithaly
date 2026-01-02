#!/usr/bin/env python3
import json
import sys

from mithaly.core.engine import BuildEngine


def find_policy(obj):
    if isinstance(obj, dict):
        if 'policy_constraints' in obj:
            return obj['policy_constraints']
        for v in obj.values():
            r = find_policy(v)
            if r:
                return r
    if isinstance(obj, list):
        for item in obj:
            r = find_policy(item)
            if r:
                return r
    return None


def main():
    e = BuildEngine()
    payload = {
        'text': 'This project will call an external API and needs Postgres and Docker',
        'non_interactive': True,
    }
    res = e.run_lifecycle(payload)
    pc = find_policy(res)
    print('--- Lifecycle result (truncated) ---')
    print(json.dumps(res if isinstance(res, dict) else {}, indent=2, ensure_ascii=False)[:4000])
    print('\n--- policy_constraints found ---')
    print(json.dumps(pc, indent=2, ensure_ascii=False))

    if not pc:
        print('ERROR: no policy_constraints found', file=sys.stderr)
        sys.exit(2)

    if pc.get('sensitive_project_review') is True:
        print('OK: policy effect detected')
        sys.exit(0)
    else:
        print('WARN: policy loaded but expected sensitive_project_review:true', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
