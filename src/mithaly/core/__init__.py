# Core package initializer: import known layer modules to trigger registration

# Import order: keep lightweight to avoid heavy side-effects at import time.
from .gaps import gap_analyzer  # registers 'gaps'
from .planning import execution_planner  # registers 'planning'
from .execution import safe_executor  # registers 'execution'
from .feedback import feedback_loop  # registers 'feedback'

# Optionally perform autodiscovery as fallback (non-destructive)
try:
    from .registry import LayerRegistry
    # perform autodiscovery to catch any additional modules
    LayerRegistry.autodiscover('mithaly.core')
except Exception:
    pass
