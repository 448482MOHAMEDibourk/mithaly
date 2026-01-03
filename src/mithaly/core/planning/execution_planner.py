# -*- coding: utf-8 -*-
from mithaly.core.registry import register_layer


@register_layer('planning')
class ExecutionPlanner:
    """Simple ExecutionPlanner stub for mithaly.core.planning."""

    def __init__(self):
        pass

    def process(self, data):
        """Process input data and indicate the planning layer is running."""
        print("[planning] ExecutionPlanner تعمل الآن. المدخل:", data)
        return {
            'layer': 'planning',
            'status': 'ok',
            'plan': {'steps': []},
            'input': data,
            'probe': {
                'layer': 'planning',
                'capabilities': ['create_plan', 'estimate_time'],
                'requirements': {'requires_network': 'maybe'},
                'attributes': {'estimated_time_seconds': 10, 'sensitive': False},
            }
        }

    def probe(self, data=None):
        return {
            'layer': 'planning',
            'capabilities': ['create_plan', 'estimate_time'],
            'requirements': {'requires_network': 'maybe'},
            'attributes': {'estimated_time_seconds': 10, 'sensitive': False},
        }
