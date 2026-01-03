**LangGraph & MCP Integrations**

- **Purpose**: describe how to enable optional integrations used by Mithaly.

- **Install (optional)**:

```bash
pip install -r requirements-integrations.txt
```

- **LangGraph**:
  - Package: `langgraph` (and `langchain-core` as required by newer LangGraph versions).
  - Usage: Mithaly includes a safe adapter at `src/mithaly/core/adapter/langgraph_adapter.py`.
  - The demo runner `scripts/run_engine_demo.py` will report availability.

- **MCP (Model Context Protocol)**:
  - Package: `mcp`
  - Mithaly includes an MCP adapter at `src/mithaly/core/adapter/mcp_client.py`.
  - Configure MCP servers by adding `docs/knowledge/mcp_config.json` with server definitions.

- **Behavior**:
  - Integrations are optional — Mithaly falls back gracefully when packages are missing.
  - CI should only enable integration tests when the environment is configured.

- **ChromaDB (Semantic Memory / Vector Store)**:
  - Package: `chromadb`
  - Usage: Mithaly's vector store adapter is implemented in `src/mithaly/core/memory/vector_store.py` and will print a warning if `chromadb` is not installed.
  - Persistence: default path `docs/knowledge/chroma_db` (configurable in the adapter).

- **Ollama (Local LLM runtime)**:
  - Package / runtime: `ollama` (binary and/or Python client).
  - Usage: Mithaly provides `src/mithaly/core/adapter/ollama_client.py` to interact with a local Ollama instance; configuration keys like `OLLAMA_HOST`/`OLLAMA_API_BASE` and `MODEL_NAME` are expected in environment or config files.
  - Notes: prefer using the official `ollama` binary for serving models (`ollama serve`) and the adapter will fall back to HTTP/CLI if a Python client is unavailable.

