"""Preflight helper: validate transition records against minimal schema.

Usage: PYTHONPATH=./src python3 scripts/check_transitions.py
"""
import json
import os
import sys

SCHEMA = os.path.join('docs', 'context', 'schemas', 'layer_transition_schema.json')
TRANS = os.path.join('docs', 'context', 'transitions.jsonl')


def load_schema():
    try:
        with open(SCHEMA, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print('WARN: Could not load schema:', e)
        return {}


def check():
    schema = load_schema()
    req = schema.get('required', []) if isinstance(schema, dict) else []
    if not os.path.exists(TRANS):
        print('OK: No transition records found.')
        return 0

    bad = 0
    total = 0
    with open(TRANS, 'r', encoding='utf-8') as f:
        for line in f:
            total += 1
            try:
                rec = json.loads(line)
                for k in req:
                    if k not in rec:
                        print(f'BAD: record {rec.get("id","<no-id>")} missing {k}')
                        bad += 1
                        break
            except Exception as e:
                print('BAD: failed to parse line:', e)
                bad += 1

    if bad:
        print(f'FAILED: {bad}/{total} records invalid')
        return 2
    print(f'OK: All {total} transition records look valid (minimal checks).')
    return 0


if __name__ == '__main__':
    sys.exit(check())
