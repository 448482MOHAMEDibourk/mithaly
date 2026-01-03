"""LangGraph adapter shim for optional integration.

This module provides a lightweight wrapper so the codebase can probe for
LangGraph availability without hard-failing at import time.
"""
from typing import Optional

try:
    from langgraph.graph import StateGraph
    from langgraph.checkpoint.memory import MemorySaver
    _HAS_LANGGRAPH = True
except Exception:
    StateGraph = None
    MemorySaver = None
    _HAS_LANGGRAPH = False


class LangGraphAdapter:
    """Adapter to hide LangGraph as an optional dependency.

    Usage:
      adapter = LangGraphAdapter()
      if adapter.is_available():
          g = adapter.create_state_graph()
    """

    def __init__(self):
        self.available = _HAS_LANGGRAPH

    def is_available(self) -> bool:
        return self.available

    def create_state_graph(self, *args, **kwargs) -> Optional[object]:
        """Create a StateGraph instance when LangGraph is installed.

        Returns None if LangGraph is not available.
        """
        if not self.available or StateGraph is None:
            return None
        # Keep construction light here; callers can configure nodes/actions.
        try:
            saver = MemorySaver()
            graph = StateGraph(checkpoint=saver, *args, **kwargs)
            return graph
        except Exception:
            return None
