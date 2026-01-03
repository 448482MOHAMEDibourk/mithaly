#!/usr/bin/env python3
"""Simple runner that demonstrates calling `BuildEngine` from the package.

This is a lightweight demo script replacing the root `core/` runner.
"""
#!/usr/bin/env python3
"""Simple runner that demonstrates calling `BuildEngine` from the package.

This runner also probes optional integrations (LangGraph, MCP) and logs availability.
"""
import json
import sys

from mithaly.core.engine import BuildEngine

try:
    from mithaly.core.adapter.langgraph_adapter import LangGraphAdapter
except Exception:
    LangGraphAdapter = None

try:
    import chromadb  # type: ignore
    _HAS_CHROMA = True
except Exception:
    _HAS_CHROMA = False

try:
    from mithaly.core.adapter.ollama_client import OllamaClient
    _HAS_OLLAMA = True
except Exception:
    OllamaClient = None
    _HAS_OLLAMA = False


def main():
    lg = LangGraphAdapter() if LangGraphAdapter else None
    print("Integration status:")
    if lg is None:
        print(" - LangGraph adapter not present in package (use src/mithaly/core/adapter/langgraph_adapter.py)")
    else:
        print(f" - LangGraph available: {lg.is_available()}")
    print(f" - ChromaDB available: {_HAS_CHROMA}")
    print(f" - Ollama adapter present: {_HAS_OLLAMA}")

    e = BuildEngine()
    payload = {"text": "demo run", "non_interactive": True}
    try:
        res = e.run_lifecycle(payload)
    except Exception as exc:
        print("Runner error:", exc)
        sys.exit(1)
    print(json.dumps(res if isinstance(res, dict) else {}, indent=2, ensure_ascii=False)[:4000])


if __name__ == '__main__':
    main()
