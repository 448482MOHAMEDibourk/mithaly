import json
import os
import uuid
from pathlib import Path

from mithaly.core.transition_logger import record_transition


def test_inflection_approval_flow(tmp_path):
    # prepare current_context
    ctx_dir = Path('docs') / 'context'
    ctx_dir.mkdir(parents=True, exist_ok=True)
    with open(ctx_dir / 'current_context.json', 'w', encoding='utf-8') as f:
        json.dump({'state': 'test'}, f)

    # create a blocked transition via record_transition
    rec = {
        'from_layer': 'Policy',
        'to_layer': 'INFLECTION',
        'timestamp': '2026-01-03T00:00:00Z',
        'actor': 'pytest',
        'outcome': 'blocked',
        'reason': 'sensitive data',
    }
    saved = record_transition(rec)
    tid = saved.get('id')
    assert tid

    # ensure snapshot written
    snaps = list((ctx_dir / 'snapshots').glob(f'snapshot_{tid}.json'))
    assert snaps, 'Snapshot not created'

    # No approval yet: check_inflection should not find approval (we simulate by calling function)
    from mithaly.core.inflection import check_inflection
    state = {'inflection': {'triggered': True, 'transition_id': tid}, 'non_interactive': False}
    res = check_inflection(state)
    assert res == 'end'

    # create approval file
    apr_dir = ctx_dir / 'approvals'
    apr_dir.mkdir(exist_ok=True)
    with open(apr_dir / f'approval_{tid}.json', 'w', encoding='utf-8') as f:
        json.dump({'transition_id': tid, 'approved_by': 'unittest'}, f)

    # Now check_inflection should allow planning
    res2 = check_inflection({'inflection': {'triggered': True, 'transition_id': tid}, 'non_interactive': False})
    assert res2 == 'planning'
