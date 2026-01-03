"""OllamaClient - Adapter for Local LLM (Ollama).

This adapter handles connection to the local Ollama instance and provides
a unified interface for chat completions, including model routing and
performance tracking.
"""
import time
import json
import os
import httpx
from typing import List, Dict, Any, Optional

class OllamaClient:
    """Client for interacting with local Ollama instance."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.routing_table = {}
        self.metrics_file = None
        self._load_config()

    def _load_config(self):
        """Load routing table and metrics file path."""
        # Defaults
        self.routing_table = {
            "fast": "qwen2.5-coder:3b",
            "standard": "qwen2.5-coder:7b-instruct-q4_K_M",
            "smart": "deepseek-coder-v2:16b-lite-instruct-q3_K_S"
        }
        
        # Try to load from file
        try:
            base = os.getcwd()
            path = os.path.join(base, 'docs', 'knowledge', 'routing_table.json')
            if os.path.exists(path):
                with open(path, 'r') as f:
                    self.routing_table = json.load(f)
            
            # Setup metrics path
            metrics_dir = os.path.join(base, 'docs', 'knowledge', 'metrics')
            if not os.path.exists(metrics_dir):
                os.makedirs(metrics_dir, exist_ok=True)
            self.metrics_file = os.path.join(metrics_dir, 'model_metrics.jsonl')
        except Exception as e:
            print(f"WARN: Failed to load LLM config: {e}")

    def route(self, task_type: str) -> str:
        """Select the best model for the task type."""
        # Fallback to standard if unknown
        model = self.routing_table.get(task_type, self.routing_table.get("standard"))
        # Fallback to hardcoded string if config is empty
        return model or "qwen2.5-coder:7b"

    def chat(self, messages: List[Dict[str, str]], task_type: str = "standard") -> Dict[str, Any]:
        """Send chat request to Ollama with automatic routing and tracking."""
        model = self.route(task_type)
        print(f"--- [LLM] Asking {model} (Task: {task_type}) ---")
        
        start_time = time.time()
        success = False
        response_content = ""
        
        try:
            payload = {
                "model": model,
                "messages": messages,
                "stream": False
            }
            
            # Use httpx for sync call (can be async'd later)
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(f"{self.base_url}/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()
                
                response_content = data.get("message", {}).get("content", "")
                success = True
                return {"content": response_content, "raw": data}
                
        except Exception as e:
            print(f"ERROR: LLM Call failed ({model}): {e}")
            return {"content": f"Error: {str(e)}", "error": True}
            
        finally:
            duration = time.time() - start_time
            self._track_metrics(model, task_type, duration, success)

    def _track_metrics(self, model: str, task_type: str, duration: float, success: bool):
        """Log performance metrics."""
        if not self.metrics_file:
            return
            
        entry = {
            "timestamp": time.time(),
            "model": model,
            "task_type": task_type,
            "duration": duration,
            "success": success
        }
        
        try:
            with open(self.metrics_file, 'a') as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass # Don't crash on logging
