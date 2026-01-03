Hybrid registration and INFLECTION_POINT
=========================================

This repository uses a hybrid registration approach for layers in `mithaly.core`:

- Explicit registration: layers use the `@register_layer('<name>')` decorator on the class definition. This is the preferred, explicit method.
- Central import: `src/mithaly/core/__init__.py` imports known layer modules to trigger registration when the package is imported.
- Autodiscover fallback: `LayerRegistry.autodiscover()` can scan `mithaly.core` submodules and import them as a fallback when explicit registration is missing.

INFLECTION_POINT handling
-------------------------

When `PolicyEnforcer` evaluates probes + policies it may set the `inflection_point` flag (or `inflection`) in `policy_constraints` for sensitive cases. The `BuildEngine` reacts as follows:

- If `inflection_point` is present and `initial_data` contains `non_interactive: True`, the engine returns early with `inflection.triggered = True` and does not proceed to planning/execution.
- If running interactively, the engine prompts the user: "Policy flagged an INFLECTION_POINT. Proceed automatically? (yes/no)" — a negative response halts the lifecycle and returns the payload with `inflection` metadata.

This behavior makes policy-driven human review and stop/gate actions explicit and testable.

Recommendations
---------------

- Keep module-level imports in layer modules lightweight to avoid side-effects on import.
- Prefer explicit `@register_layer` for clarity and testability; autodiscover is a safety net.
- Add probe-driven tests (examples under `tools/tests/`) to ensure policy->engine behavior remains stable.
