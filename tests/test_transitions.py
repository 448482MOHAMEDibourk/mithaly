import json
import os
import shutil
import uuid
from pathlib import Path

import pytest

from mithaly.core.transition_logger import record_transition


DOCSPATH = Path('docs') / 'context'
TRANS_PATH = DOCSPATH / 'transitions.jsonl'
CURRENT = DOCSPATH / 'current_context.json'
SNAP_DIR = DOCSPATH / 'snapshots'


def setup_module(module):
    DOCSPATH.mkdir(parents=True, exist_ok=True)
    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    # ensure current context exists
    with open(CURRENT, 'w', encoding='utf-8') as f:
        json.dump({'state': 'test-context'}, f)


def teardown_module(module):
    # cleanup created artifacts by the test
    try:
        if TRANS_PATH.exists():
            TRANS_PATH.unlink()
        if CURRENT.exists():
            CURRENT.unlink()
        if SNAP_DIR.exists():
            shutil.rmtree(SNAP_DIR)
    except Exception:
        pass


def test_record_blocked_triggers_snapshot(tmp_path):
    rec = {
        'id': str(uuid.uuid4()),
        'from_layer': 'policy',
        'to_layer': 'inflection',
        'timestamp': '2026-01-01T00:00:00Z',
        'actor': 'pytest',
        'outcome': 'blocked',
        'reason': 'sensitive data',
    }

    # call the logger
    record_transition(rec)

    # assert record appended
    assert TRANS_PATH.exists()
    with open(TRANS_PATH, 'r', encoding='utf-8') as f:
        lines = [json.loads(l) for l in f]
    assert any(l.get('id') == rec['id'] for l in lines)

    # assert snapshot created
    snaps = list(SNAP_DIR.glob('snapshot_*.json'))
    assert len(snaps) >= 1
