"""PolicyEnforcer for Mithaly.

Provides a small, testable policy-enforcement component that evaluates a
payload (usually produced by `GapAnalyzer`) and returns `policy_constraints`.
By default it attempts to load a policy file from the workspace
`docs/knowledge/policies/policies.yaml` (or `policies.json`) unless
explicit `policies` are provided to the constructor.
"""
import os
import json
from typing import Dict, Any, Optional


def _load_policies_from_file(path: str) -> Optional[Dict[str, Any]]:
    """Try to load policies from YAML (if PyYAML is installed) or JSON.

    Returns a dict or None if file not found or parsing failed.
    """
    if not os.path.exists(path):
        return None
    # Prefer YAML if available
    try:
        import yaml  # type: ignore
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception:
        # Fallback to JSON
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None


class PolicyEnforcer:
    def __init__(self, policies: Dict[str, Any] = None, policy_path: str = None):
        # If policies explicitly provided, use them.
        if policies is not None:
            self.policies = policies
            return

        # Allow overriding policy file path via env var or constructor
        candidate = policy_path or os.environ.get('MITHALY_POLICY_PATH')
        if candidate:
            loaded = _load_policies_from_file(candidate)
            self.policies = loaded or {}
            return

        # Default locations under docs/knowledge/policies
        base = os.getcwd()
        defaults = [
            os.path.join(base, 'docs', 'knowledge', 'policies', 'policies.yaml'),
            os.path.join(base, 'docs', 'knowledge', 'policies', 'policies.yml'),
            os.path.join(base, 'docs', 'knowledge', 'policies', 'policies.json'),
        ]
        loaded = None
        for p in defaults:
            loaded = _load_policies_from_file(p)
            if loaded is not None:
                break

        self.policies = loaded or {}

    def _load_constitution_core(self) -> Optional[str]:
        """Load the 'Immutable Core' section from the constitution."""
        try:
            # Try to locate MITHALY_CONSTITUTION.md
            candidates = [
                os.path.join(os.getcwd(), 'docs', 'MITHALY_CONSTITUTION.md'),
                os.path.join(os.getcwd(), 'MITHALY_CONSTITUTION.md'),
            ]
            path = None
            for c in candidates:
                if os.path.exists(c):
                    path = c
                    break
            
            if not path:
                return None

            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract 'Mithaly — ميثاق الثوابت' or relevant core section
            # For now, we take the whole file or a significant chunk if markers exist.
            # The gaps analysis requested "full text" or "summary" as hard constraint.
            # We will return the whole text to be safe as the "Core".
            return content
        except Exception:
            return None


    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate payload and return a dict with `policy_constraints`.

        This implementation is intentionally small and rule-based. It looks
        for common technical gap indicators and returns simple constraints.
        The returned constraints are merged with loaded policies (policies as base,
        detected constraints override when present).
        """
        constraints: Dict[str, Any] = {}

        # Start from configured policies as defaults
        if isinstance(self.policies, dict):
            constraints.update(self.policies)

        # Inspect gap analysis for indicators
        gap = payload.get('gap_analysis') if isinstance(payload, dict) else None
        techs = None
        try:
            techs = gap.get('technical_gaps') if isinstance(gap, dict) else None
        except Exception:
            techs = None

        if techs:
            combined = ' '.join(map(str, techs)).lower()
            if 'db' in combined or 'database' in combined or 'postgres' in combined or 'mysql' in combined:
                constraints['requires_db'] = True
            if 'docker' in combined or 'container' in combined:
                constraints['requires_container_runtime'] = True

        text = payload.get('text') if isinstance(payload, dict) else None
        if isinstance(text, str):
            t = text.lower()
            if 'third-party api' in t or 'external api' in t or 'oauth' in t:
                constraints['requires_network_access'] = True

        # Inspect probes (if any) and derive constraints from reported requirements
        probes = None
        try:
            probes = payload.get('probes') if isinstance(payload, dict) else None
        except Exception:
            probes = None

        if isinstance(probes, dict):
            for pname, probe in probes.items():
                if not isinstance(probe, dict):
                    continue
                reqs = probe.get('requirements') or {}
                # normalize string values
                for k, v in reqs.items():
                    sval = v
                    if isinstance(v, str):
                        sval = v.lower()
                    # map common requirement keys to policy flags
                    if k in ('requires_db',) and sval in (True, 'yes', 'true'):
                        constraints['requires_db'] = True
                    if k in ('requires_container_runtime',) and sval in (True, 'yes', 'true'):
                        constraints['requires_container_runtime'] = True
                    if k in ('requires_network',) and sval in (True, 'yes', 'true'):
                        constraints['requires_network_access'] = True

                attrs = probe.get('attributes') or {}
                if attrs.get('sensitive') is True:
                    # flag for human review and potential inflection
                    constraints['sensitive_project_review'] = True
                    constraints['inflection_point'] = True
                    # Record transition: Policy -> INFLECTION_POINT (blocked)
                    try:
                        from mithaly.core.transition_logger import record_transition
                    except Exception:
                        try:
                            from src.mithaly.core.transition_logger import record_transition
                        except Exception:
                            record_transition = None
                    if record_transition is not None:
                        try:
                            rec = {
                                'from_layer': 'Policy',
                                'to_layer': 'INFLECTION',
                                'reason': 'Probe marked sensitive',
                                'metrics': {'probe': pname},
                                'actor': 'PolicyEnforcer',
                                'outcome': 'blocked',
                                'emergency': False,
                                'provenance': 'policy.process'
                            }
                            record_transition(rec)
                        except Exception:
                            pass

        # Inject Constitutional Hard Constraints
        constitution = self._load_constitution_core()
        if constitution:
            constraints['constitutional_constraints'] = {
                'source': 'MITHALY_CONSTITUTION.md',
                'type': 'HARD_CONSTRAINT',
                'content': constitution
            }

        return {'policy_constraints': constraints}

    def report_error(self, error_report: Dict[str, Any]) -> Dict[str, Any]:
        """Receive an error report and convert it into an analysis request.

        Behavior:
        - Persist the report non-destructively under `docs/context/errors_pending.json`.
        - Attempt to dispatch the report to registered layers that implement
          `analyze_error(report) -> dict` and collect their analysis outputs.
        - Return an `analysis_ticket` describing the dispatched analyses and a
          recommended action: `defer`, `requires_admin`, or `auto_resolve`.

        This method deliberately does NOT write to the Knowledge Base. callers
        should honor the returned recommendation.
        """
        # ensure docs/context exists and append the pending error
        import pathlib
        base = pathlib.Path('docs') / 'context'
        base.mkdir(parents=True, exist_ok=True)
        pending = base / 'errors_pending.json'

        entry = {
            'timestamp': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
            'report': error_report,
        }

        # Append to pending list (safe, non-destructive)
        try:
            if pending.exists():
                try:
                    with open(pending, 'r', encoding='utf-8') as f:
                        existing = json.load(f) or []
                except Exception:
                    existing = []
            else:
                existing = []
            existing.append(entry)
            with open(pending, 'w', encoding='utf-8') as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)
        except Exception:
            # non-fatal: continue even if writing the pending file fails
            pass

        # Dispatch to layers that expose `analyze_error`
        analyses = {}
        try:
            from mithaly.core.registry import LayerRegistry as _LR
        except Exception:
            try:
                from src.mithaly.core.registry import LayerRegistry as _LR
            except Exception:
                _LR = None

        if _LR is not None:
            for name in _LR.list():
                try:
                    layer_cls = _LR.get(name)
                    inst = layer_cls()
                    if hasattr(inst, 'analyze_error'):
                        try:
                            res = inst.analyze_error(error_report)
                            analyses[name] = res
                        except Exception as e:
                            analyses[name] = {'error': str(e)}
                except Exception:
                    analyses[name] = {'error': 'failed to instantiate layer'}

        # Simple heuristics to decide recommendation
        recommendation = 'defer'
        try:
            # if any analysis marks as 'confident' or 'actionable', escalate
            for a in analyses.values():
                if isinstance(a, dict) and a.get('action') == 'auto_resolve':
                    recommendation = 'auto_resolve'
                    break
                if isinstance(a, dict) and a.get('action') == 'requires_admin':
                    recommendation = 'requires_admin'
                    break
        except Exception:
            recommendation = 'defer'

        ticket = {
            'ticket_id': f"err-{int(__import__('time').time())}",
            'timestamp': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
            'recommendation': recommendation,
            'analyses': analyses,
            'trusted': False,
        }

        # write ticket record for audit
        try:
            tickets = base / 'analysis_tickets.json'
            if tickets.exists():
                try:
                    with open(tickets, 'r', encoding='utf-8') as f:
                        tlist = json.load(f) or []
                except Exception:
                    tlist = []
            else:
                tlist = []
            tlist.append(ticket)
            with open(tickets, 'w', encoding='utf-8') as f:
                json.dump(tlist, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        # If recommendation suggests auto-resolve, prefer to persist via FeedbackLoop
        try:
            from mithaly.core.utils.context_updater import deliver_record as _deliver
        except Exception:
            try:
                from src.mithaly.core.utils.context_updater import deliver_record as _deliver
            except Exception:
                _deliver = None

        if _deliver is not None and ticket.get('recommendation') == 'auto_resolve':
            try:
                deliver_res = _deliver(ticket, prefer_feedback=True)
                ticket['delivered'] = deliver_res
            except Exception:
                ticket['delivered'] = {'delivered': False, 'via': 'error', 'error': 'deliver_failed'}

        return ticket
