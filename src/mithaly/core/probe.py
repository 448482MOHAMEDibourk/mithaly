"""Semantic probe utilities for Mithaly.

Provides a lightweight `semantic_probe` function that aggregates probes
from registered layers in `LayerRegistry` if available, and yields a
compact `probe_results` dict consumed by policy/engine.
"""
from typing import Dict, Any
import traceback


def semantic_probe(state: Dict[str, Any]) -> Dict[str, Any]:
    """Collect probes and produce a consolidated probe_results object.

    This is intentionally lightweight: it looks for `LayerRegistry` and
    calls each layer's `probe` method if available. If LayerRegistry
    isn't available, returns a minimal probe indicating unknown.
    """
    results = {
        'collected': [],
        'sensitive': False,
        'summary': ''
    }
    try:
        from mithaly.core.registry import LayerRegistry
    except Exception:
        LayerRegistry = None

    try:
        if LayerRegistry:
            try:
                probes = LayerRegistry.collect_probes(state)
            except Exception:
                probes = None
            if probes:
                # probes is expected to be a dict mapping layer -> probe
                for layer, p in (probes.items() if isinstance(probes, dict) else []):
                    results['collected'].append({'layer': layer, 'probe': p})
                    attrs = p.get('attributes', {}) if isinstance(p, dict) else {}
                    if attrs.get('sensitive'):
                        results['sensitive'] = True
        else:
            # Fallback: try calling state-provided probes
            sp = state.get('probes')
            if sp:
                for layer, p in (sp.items() if isinstance(sp, dict) else []):
                    results['collected'].append({'layer': layer, 'probe': p})
                    attrs = p.get('attributes', {}) if isinstance(p, dict) else {}
                    if attrs.get('sensitive'):
                        results['sensitive'] = True
    except Exception:
        traceback.print_exc()

    # Build a short summary
    try:
        if results['sensitive']:
            results['summary'] = 'sensitive content present in probes'
        elif results['collected']:
            results['summary'] = f"collected {len(results['collected'])} probes"
        else:
            results['summary'] = 'no probes collected'
    except Exception:
        results['summary'] = 'probe error'

    return results
