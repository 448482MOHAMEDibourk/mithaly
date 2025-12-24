"""
Shim module to make `from project_management.agents import protocol` work.

This file attempts to load the real `protocol.py` implementation from the
`project_management/context/protocol/` folder first (preferred), and falls
back to `project_management/archive/agents/protocol.py` if necessary.

The shim loads the target module by file path using importlib and then
injects its attributes into this module's globals so callers can access
the same symbols via `project_management.agents.protocol`.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_candidates = [
    _ROOT / "context" / "protocol" / "protocol.py",
    _ROOT / "archive" / "agents" / "protocol.py",
]

_loaded = None
for _p in _candidates:
    if _p.exists():
        spec = importlib.util.spec_from_file_location("project_management.agents.protocol", str(_p))
        module = importlib.util.module_from_spec(spec)
        # Register under the expected name so other imports find the same module
        sys.modules["project_management.agents.protocol"] = module
        try:
            spec.loader.exec_module(module)  # type: ignore[attr-defined]
        except Exception:
            # If loading fails, clean up and continue to next candidate
            sys.modules.pop("project_management.agents.protocol", None)
            continue
        # copy public attributes into this shim module
        for _name in dir(module):
            if not _name.startswith("__"):
                globals()[_name] = getattr(module, _name)
        _loaded = str(_p)
        break

if _loaded is None:
    raise ImportError(
        "Could not locate protocol implementation in project_management/context/protocol or archive/agents"
    )

# Expose a small helper to indicate where we loaded the implementation from
__protocol_impl_path__ = _loaded
