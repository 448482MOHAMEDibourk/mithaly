"""Generator Adapter - The Sovereign Embassy for the Generator.

This component provides a stable interface for the Project Generator (and other
external tools) to interact with the Mithaly Core layers (Gaps, Planning,
Execution, Feedback). It solves the "Floating Generator" gap by anchoring
the generator's identity within the core architecture.
"""
from typing import Dict, Any, Optional
from mithaly.core.registry import LayerRegistry

class GeneratorAdapter:
    """The embassy class for the Generator."""

    def __init__(self, generator_id: str = "default_generator"):
        self.generator_id = generator_id
        # Ensure we can see the layers
        LayerRegistry.autodiscover()

    def request_gap_analysis(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to the GapAnalyzer layer."""
        return self._delegate_to_layer('Gaps', 'gap_analyzer', payload)

    def request_planning(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to the ExecutionPlanner layer."""
        return self._delegate_to_layer('Planning', 'execution_planner', payload)

    def request_execution(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to the SafeExecutor layer."""
        return self._delegate_to_layer('Execution', 'safe_executor', payload)

    def request_feedback(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to the FeedbackLoop layer."""
        return self._delegate_to_layer('Feedback', 'feedback_loop', payload)

    def _delegate_to_layer(self, layer_category: str, layer_hint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generic delegation logic with error handling."""
        # Try to find by name, or use registry keys if known
        # Current registry logic relies on manual registration or auto-discovery.
        # We'll assume the standard names are registered or we try to find them.
        
        # Simple lookup: try to find a class named similarly to layer_hint
        # in the registry keys (case-insensitive search for robustness)
        target_cls = None
        for name in LayerRegistry.list():
            if layer_hint.lower() in name.lower():
                target_cls = LayerRegistry.get(name)
                break
        
        if not target_cls:
             # Fallback: try to instantiate directly if we know the path (shortcuts)
             # This is a bit "floating" but helpful if registry is empty
             return {"error": f"Layer {layer_hint} not found in registry", "status": "failed"}

        try:
            instance = target_cls()
            if hasattr(instance, 'process'):
                return instance.process(payload)
            else:
                return {"error": f"Layer {layer_hint} does not have process() method", "status": "failed"}
        except Exception as e:
            return {"error": f"Exception calling layer {layer_hint}: {str(e)}", "status": "failed"}

    def get_status(self):
        """Return the status of the embassy."""
        return {
            "id": self.generator_id,
            "connected_layers": LayerRegistry.list(),
            "status": "active"
        }
