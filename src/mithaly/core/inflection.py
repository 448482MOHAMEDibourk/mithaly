from typing import Dict, Any
import os
import json


def check_inflection(state: Dict[str, Any]) -> str:
    """Inflection decision logic extracted for testing.

    Mirrors the logic used by `engine.check_inflection`:
    - persists `docs/context/current_context.json` when inflection triggered
    - returns 'end' for non_interactive or when no approval
    - returns 'planning' if approved
    """
    inflection = state.get('inflection') or {}
    if not inflection.get('triggered'):
        return "planning"

    # Ensure current context is persisted for snapshotting
    try:
        ctx_dir = os.path.join('docs', 'context')
        os.makedirs(ctx_dir, exist_ok=True)
        ctx_path = os.path.join(ctx_dir, 'current_context.json')
        with open(ctx_path, 'w', encoding='utf-8') as cf:
            json.dump({k: v for k, v in state.items() if k != '__internal__'}, cf, ensure_ascii=False, indent=2)
    except Exception:
        pass

    if state.get('non_interactive'):
        return "end"

    # Check on-disk approvals by transition id if available
    tid = inflection.get('transition_id')
    if not inflection.get('approved_by') and tid:
        try:
            appr = os.path.join('docs', 'context', 'approvals', f'approval_{tid}.json')
            if os.path.exists(appr):
                try:
                    with open(appr, 'r', encoding='utf-8') as af:
                        aobj = json.load(af)
                        approved_by = aobj.get('approved_by')
                        if approved_by:
                            inflection['approved_by'] = approved_by
                except Exception:
                    pass
        except Exception:
            pass

    if inflection.get('approved_by'):
        return "planning"

    return "end"
