# -*- coding: utf-8 -*-
from mithaly.core.registry import register_layer
from datetime import datetime, timezone
import json
import pathlib


@register_layer('feedback')
class FeedbackLoop:
    """Simple FeedbackLoop stub for mithaly.core.feedback."""

    def __init__(self):
        pass

    def process(self, data):
        """Record results and indicate the feedback layer is running."""
        print("[feedback] FeedbackLoop تعمل الآن. المدخل:", data)
        return {
            'layer': 'feedback',
            'status': 'ok',
            'recorded': True,
            'input': data,
            'probe': {
                'layer': 'feedback',
                'capabilities': ['record_result', 'detect_risks'],
                'requirements': {'requires_network': 'no'},
                'attributes': {'estimated_time_seconds': 2, 'sensitive': False},
            }
        }

    def probe(self, data=None):
        return {
            'layer': 'feedback',
            'capabilities': ['record_result', 'detect_risks'],
            'requirements': {'requires_network': 'no'},
            'attributes': {'estimated_time_seconds': 2, 'sensitive': False},
        }

    def persist_to_kb(self, record: dict) -> bool:
        """Persist a trusted record into a simple on-disk KB under `docs/knowledge/kb.json`.

        Returns True on success, False otherwise.
        """
        try:
            # Enforce trusted filter: only persist records explicitly marked trusted
            if not bool(record.get('trusted')):
                # Reject untrusted records; caller should handle audit tickets
                return False
            kb_dir = pathlib.Path('docs') / 'knowledge'
            kb_dir.mkdir(parents=True, exist_ok=True)
            kb_file = kb_dir / 'kb.json'
            if kb_file.exists():
                try:
                    with open(kb_file, 'r', encoding='utf-8') as f:
                        existing = json.load(f) or []
                except Exception:
                    existing = []
            else:
                existing = []
            existing.append({'timestamp': datetime.now(timezone.utc).isoformat(), 'record': record})
            with open(kb_file, 'w', encoding='utf-8') as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
