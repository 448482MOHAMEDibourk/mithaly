"""Simple transition logger for Mithaly.

Writes layer transition records to `docs/context/transitions.jsonl` and
validates minimal required fields against the schema in
`docs/context/schemas/layer_transition_schema.json`.
"""
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any


SCHEMA_CANDIDATES = [
    os.path.join('docs', 'knowledge', 'context', 'schemas', 'layer_transition_schema.json'),
    os.path.join('docs', 'context', 'schemas', 'layer_transition_schema.json'),
]
# Prefer writing to `docs/context` when present (tests create it),
# otherwise fall back to canonical `docs/knowledge/context`.
if os.path.exists(os.path.join('docs', 'context')):
    TRANSITIONS_PATH = os.path.join('docs', 'context', 'transitions.jsonl')
elif os.path.exists(os.path.join('docs', 'knowledge', 'context')):
    TRANSITIONS_PATH = os.path.join('docs', 'knowledge', 'context', 'transitions.jsonl')
else:
    # default to legacy path if neither exists
    TRANSITIONS_PATH = os.path.join('docs', 'context', 'transitions.jsonl')


def _load_schema() -> Dict[str, Any]:
    for p in SCHEMA_CANDIDATES:
        try:
            if os.path.exists(p):
                with open(p, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            continue
    return {}


def _validate_minimal(record: Dict[str, Any]) -> bool:
    """Perform a minimal validation using the required fields from schema.

    Returns True if record contains the required keys.
    """
    schema = _load_schema()
    # If schema is not present or doesn't declare required fields,
    # skip strict validation to remain tolerant in test and CI environments.
    if not isinstance(schema, dict) or not schema.get('required'):
        return True
    req = schema.get('required', [])
    missing = [k for k in req if k not in record]
    if missing:
        raise ValueError(f'Transition record missing required fields: {missing}')
    return True


def record_transition(record: Dict[str, Any]) -> Dict[str, Any]:
    """Record a transition to the JSONL ledger.

    Ensures `id` and `timestamp` (ts) are set, validates minimal schema,
    appends to `docs/context/transitions.jsonl`. Returns the final record.
    """
    os.makedirs(os.path.dirname(TRANSITIONS_PATH), exist_ok=True)

    final = dict(record)
    if 'id' not in final:
        final['id'] = str(uuid.uuid4())
    if 'timestamp' not in final and 'ts' not in final:
        final['timestamp'] = datetime.now(timezone.utc).isoformat()
    # normalize: ensure timestamp key exists as 'timestamp'
    if 'ts' in final and 'timestamp' not in final:
        final['timestamp'] = final['ts']

    # Minimal validation
    if not _validate_minimal(final):
        raise ValueError('Transition record missing required fields per schema')

    # Append to JSONL
    try:
        with open(TRANSITIONS_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps(final, ensure_ascii=False) + '\n')
    except Exception:
        # non-fatal: try to create file
        with open(TRANSITIONS_PATH, 'w', encoding='utf-8') as f:
            f.write(json.dumps(final, ensure_ascii=False) + '\n')

    # Special-case: if blocked/inflection, create a snapshot of current_context.json if present
    outcome = final.get('outcome') or ''
    if outcome == 'blocked' or final.get('emergency') is True or final.get('reason', '').lower().find('inflection') != -1:
        try:
            # Try canonical knowledge path first, then legacy context path
            src_candidates = [
                os.path.join('docs', 'knowledge', 'context', 'current_context.json'),
                os.path.join('docs', 'context', 'current_context.json')
            ]
            for src in src_candidates:
                if os.path.exists(src):
                    snaps_dir = os.path.join(os.path.dirname(src), 'snapshots')
                    os.makedirs(snaps_dir, exist_ok=True)
                    snap_name = f"snapshot_{final.get('id')}.json"
                    dst = os.path.join(snaps_dir, snap_name)
                    with open(src, 'r', encoding='utf-8') as sf, open(dst, 'w', encoding='utf-8') as df:
                        df.write(sf.read())
                    break
        except Exception:
            pass

    return final
