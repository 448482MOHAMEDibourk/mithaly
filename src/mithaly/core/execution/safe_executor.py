# -*- coding: utf-8 -*-
from mithaly.core.registry import register_layer


@register_layer('execution')
class SafeExecutor:
    """Simple SafeExecutor stub for mithaly.core.execution."""

    def __init__(self):
        pass

    def process(self, data):
        """Execute a plan or step and indicate the execution layer is running.

        Enforces 'Awareness before Will' — require `probe_results` in the
        incoming payload unless running in `non_interactive` mode, in which
        case a fallback warning is logged and execution proceeds.
        """
        print("[execution] SafeExecutor تعمل الآن. المدخل:", data)

        probe_results = data.get('probe_results') if isinstance(data, dict) else None
        if not probe_results:
            # If non-interactive, log warning and proceed; otherwise raise
            if isinstance(data, dict) and data.get('non_interactive'):
                print("WARN: Missing probe_results in non-interactive mode; proceeding with caution.")
            else:
                raise RuntimeError('SafeExecutor: missing probe_results — Awareness required before execution')

        return {
            'layer': 'execution',
            'status': 'ok',
            'result': {},
            'input': data,
            'probe': {
                'layer': 'execution',
                'capabilities': ['run_steps', 'sandbox'],
                'requirements': {'requires_container_runtime': 'maybe'},
                'attributes': {'estimated_time_seconds': 60, 'sensitive': False},
            }
        }

    def probe(self, data=None):
        return {
            'layer': 'execution',
            'capabilities': ['run_steps', 'sandbox'],
            'requirements': {'requires_container_runtime': 'maybe'},
            'attributes': {'estimated_time_seconds': 60, 'sensitive': False},
        }
