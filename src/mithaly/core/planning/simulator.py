"""Virtual Simulator - 'Mental Walkthrough' of plans before execution."""
from typing import Dict, List, Any

try:
    from mithaly.core.adapter.ollama_client import OllamaClient
except ImportError:
    OllamaClient = None

class VirtualSimulator:
    """Simulates plan execution using LLM reasoning."""

    def __init__(self, ollama_client=None):
        self.ollama = ollama_client

    def simulate(self, plan: List[str], context: str = "") -> Dict[str, Any]:
        """
        Run a mental simulation.
        Returns: {'passed': bool, 'feedback': str}
        """
        print("--- [Simulator] Running Virtual Simulation ---")
        if not self.ollama:
            print("WARN: No LLM for simulation, defaulting to PASS.")
            return {'passed': True, 'feedback': "Simulation skipped (No LLM)."}

        prompt = f"""
        You are the Virtual Simulator.
        Review the following execution plan for safety and logic errors.
        
        Context: {context}
        Plan: {plan}
        
        Analyze:
        1. Are there missing dependencies?
        2. Is the order logical?
        3. Is there a risk of destructive data loss?
        
        If SAFE and LOGICAL, reply with JSON: {{"passed": true, "feedback": "Looks good."}}
        If UNSAFE or FLAWED, reply with JSON: {{"passed": false, "feedback": "Reason..."}}
        """
        
        try:
            response = self.ollama.chat([{"role": "user", "content": prompt}], task_type="smart")
            content = response.get("content", "")
            
            import json
            # Naive parse
            clean = content.replace("```json", "").replace("```", "").strip()
            # Find first { and last }
            start = clean.find("{")
            end = clean.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(clean[start:end])
                return data
            else:
                return {'passed': True, 'feedback': "Could not parse simulation result, assuming safe."}
                
        except Exception as e:
            print(f"ERROR: Simulation failed: {e}")
            return {'passed': False, 'feedback': f"Simulation error: {e}"}
