#!/usr/bin/env python3
"""Probe-driven PolicyEnforcer tests.

Simple smoke tests that call `PolicyEnforcer.process()` with crafted `probes`
to verify probe->policy mappings (container runtime and sensitive/inflection).
"""
import sys
import json

from mithaly.core.policy import PolicyEnforcer


def test_requires_container_runtime():
    pe = PolicyEnforcer()
    payload = {
        'probes': {
            'execution': {
                'layer': 'execution',
                'requirements': {'requires_container_runtime': 'yes'},
                'attributes': {'estimated_time_seconds': 10, 'sensitive': False},
            }
        }
    }
    out = pe.process(payload)
    pc = out.get('policy_constraints', {})
    ok = bool(pc.get('requires_container_runtime'))
    print('requires_container_runtime ->', ok, json.dumps(pc, indent=2))
    return ok


def test_sensitive_inflection():
    pe = PolicyEnforcer()
    payload = {
        'probes': {
            'gaps': {
                'layer': 'gaps',
                'requirements': {'requires_db': 'maybe'},
                'attributes': {'sensitive': True},
            }
        }
    }
    out = pe.process(payload)
    pc = out.get('policy_constraints', {})
    ok = bool(pc.get('inflection_point') or pc.get('inflection') or pc.get('sensitive_project_review'))
    print('sensitive ->', ok, json.dumps(pc, indent=2))
    return ok


def main():
    a = test_requires_container_runtime()
    b = test_sensitive_inflection()
    if a and b:
        print('ALL TESTS PASSED')
        sys.exit(0)
    else:
        print('TESTS FAILED')
        sys.exit(2)


if __name__ == '__main__':
    main()
